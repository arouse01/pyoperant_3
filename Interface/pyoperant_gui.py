#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui  # Import the PyQt4 module we'll need
import sys  # We need sys so that we can pass argv to QApplication
import os
import subprocess  # So pyoperant can run for each box without blocking the rest of the GUI
import serial  # To connect directly to Teensys for water control
import time
import threading  # Support subprocess, allow error messages to be passed out of the subprocess
import Queue  # Support subprocess, allow error messages to be passed out of the subprocess
import pyudev  # device monitoring to identify connected Teensys
import re  # Regex, for parsing device names returned from pyudev to identify connected Teensys
import argparse  # Parse command line arguments for GUI, primarily to enable debug mode
from shutil import copyfile  # For creating new json file by copying another
import logging, traceback
import datetime as dt  # For auto sleep
import string  # for modifying strings from the data
import collections  # allows use of ordered dictionaries
import io  # for copying cells from analysis table

from pyoperant import analysis  # Analysis creates the data summary tables
import pandas as pd  # Dataframes for data summary tables
import csv  # For exporting data summaries as csv files

try:
    import simplejson as json

except ImportError:
    import json

try:  # Allows proper formatting of UTF-8 characters from summaryDAT file
    _from_utf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _from_utf8(s):
        return s

import pyoperant_gui_layout


def _log_except_hook(*exc_info):  # How uncaught errors are handled
    text = "".join(traceback.format_exception(*exc_info))
    logging.error("Unhandled exception: {}".format(text))


class PyoperantGui(QtGui.QMainWindow, pyoperant_gui_layout.UiMainWindow):
    teensy_emit = QtCore.pyqtSignal(int, str)

    class DeviceInfo:
        # Extracts device info from pyudev output: box number, device ID, USB device number
        def __init__(self, device):
            deviceString = device.device_links.next()
            try:
                # Get box number
                deviceStringSplit = os.path.split(deviceString)
                boxLink = deviceStringSplit[1]
                boxLinkSplit = re.split('Board(\\d*)', boxLink)
                self.boxNumber = int(boxLinkSplit[1])
                self.boxIndex = self.boxNumber - 1  # Teensy numbers are indexed from 1, but box array indexed from 0

            except IndexError:
                self.boxNumber = None
                self.boxIndex = None
                self.log.error('Error: board not recognized')

            if self.boxIndex is not None:
                # Get device ID (e.g. "tty...")
                self.device_path = os.path.split(device.device_path)
                self.deviceID = self.device_path[1]

                # Get USB port info
                usbPath = device.parent.parent.device_node
                usbSplit = re.split('/', usbPath)
                self.usbBus = int(usbSplit[-2])
                self.usbDevice = int(usbSplit[-1])
                self.usbString = 'Bus {:02d}, Device {:02d}'.format(int(self.usbBus), int(self.usbDevice))
            else:
                self.device_path = None
                self.deviceID = None
                self.usbBus = None
                self.usbDevice = None
                self.usbString = None

    def __init__(self):

        super(self.__class__, self).__init__()
        self.setup_ui(self)  # Sets up layout and widgets that are defined

        self.debug = False

        # Number of boxes declared in pyoperant_gui_layout.py

        # region Menu bar
        mainMenu = QtGui.QMenuBar()
        fileMenu = mainMenu.addMenu('&File')

        analyzeGuiAction = QtGui.QAction("&Analyze", self)
        analyzeGuiAction.triggered.connect(lambda _, b=1: self.analyze_performance(b))
        quitGuiAction = QtGui.QAction("&Quit", self)
        quitGuiAction.triggered.connect(self.close)
        fileMenu.addAction(quitGuiAction)

        globalOptionsMenu = mainMenu.addMenu('Options')
        autosleepMenu = QtGui.QMenu('Autosleep', self)
        nrTrialMenu = QtGui.QMenu('NR Trials', self)

        # global options for GUI
        self.ui_options = {}

        viewGuiLogAction = QtGui.QAction("View GUI Log", self)
        viewGuiLogAction.triggered.connect(lambda _, b='guilog': self.open_text_file(0, whichfile=b))
        viewGuiErrorAction = QtGui.QAction("View GUI Error Log", self)
        viewGuiErrorAction.triggered.connect(lambda _, b='guierror': self.open_text_file(0, whichfile=b))
        self.ui_options['use_nr_all'] = QtGui.QAction("Include NR trials (all)", self)
        self.ui_options['use_nr_all'].setCheckable(True)
        self.ui_options['use_nr_all'].triggered.connect(self.use_nr_trials_all)
        self.ui_options['autosleep_all'] = QtGui.QAction("Enable autosleep (all)", self)
        self.ui_options['autosleep_all'].setCheckable(True)
        self.ui_options['autosleep_all'].setChecked(True)
        self.ui_options['autosleep_all'].triggered.connect(self.auto_sleep_set_all)

        globalOptionsMenu.addAction(viewGuiLogAction)
        globalOptionsMenu.addAction(viewGuiErrorAction)

        globalOptionsMenu.addSeparator()
        globalOptionsMenu.addMenu(autosleepMenu)
        globalOptionsMenu.addMenu(nrTrialMenu)
        nrTrialMenu.addAction(self.ui_options['use_nr_all'])
        nrTrialMenu.addSeparator()

        autosleepMenu.addAction(self.ui_options['autosleep_all'])
        autosleepMenu.addSeparator()

        self.setMenuBar(mainMenu)
        # endregion

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refreshall)
        self.timer.start(5000)

        self.idleTime = 1.5  # max idle time before restarting pyoperant process

        self.log_config()

        # region Monitor when USB devices are connected/disconnected
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='tty')
        observer = pyudev.MonitorObserver(monitor, self.usb_monitor, name='usb-observer')
        observer.daemon = True
        observer.start()

        self.teensy_emit.connect(
            (lambda triggered_boxnumber, parameter: self.teensy_control(triggered_boxnumber, parameter)))
        # endregion

        # arrays for queues and threads
        self.qList = [0] * self.numberOfBoxes
        self.tList = [0] * self.numberOfBoxes
        # self.qReadList = [0] * self.numberOfBoxes  # list of queues for inputs to subprocesses
        # self.tReadList = [0] * self.numberOfBoxes  # list of queues for inputs to subprocesses

        # Connect 'global' buttons to functions
        self.startAllButton.clicked.connect(lambda: self.start_all())
        self.stopAllButton.clicked.connect(lambda: self.stop_all())

        self.subprocessBox = [0] * self.numberOfBoxes  # stores subprocesses for pyoperant for each box
        self.logProcessBox = [0] * self.numberOfBoxes  # stores subprocesses for log reading for each box
        self.logpathList = [0] * self.numberOfBoxes  # stores log file path for each box

        # Variable initiation
        self.boxList = range(0, self.numberOfBoxes)
        self.deviceIDList = []
        self.deviceLocationList = []
        self.experimentPath = ""

        # Option var init
        self.boxMenuList = []
        self.solenoidMenuList = []
        self.primeActionList = []
        self.purgeActionList = []
        self.solenoidManualList = []
        self.optionsMenuList = []
        self.openFolderActionList = []
        self.openSettingsActionList = []
        self.createNewJsonList = []
        self.newBirdActionList = []
        self.statsActionList = []
        self.rawTrialActionList = []
        self.useNRList = []
        self.autoSleepList = []
        self.openBoxLogActionList = []
        self.lastStartList = []
        self.lastTrialList = []
        self.sleepScheduleList = []  # schedule is none if box not active, set when box started
        self.defaultSleepSchedule = [["08:30", "22:30"]]

        # region Individual option menu setup
        ## To add an item to the option menu:
        # - Add a blank list var to the "option var init" section for the action to be stored for each box
        # - Figure out whether the new option should be in the main option menu or in a submenu
        # - in the "Option Menu Setup" section, add two lines:
        #       self.{list var}.append(QtGui.QAction({action name as str}, self)   # or QtGui.QMenu({menu name as str})
        #       self.{parent menu}[boxIndex].addAction(self.{list var}[boxIndex])  # or addMenu
        # - If adding an action, go to the "Connect functions to buttons/objects" section and add a line to connect
        # the actual QAction object with the function for each box:
        #       self.{list var}[boxNumber].triggered.connect(lambda _, b=i: self.{function}(boxIndex=b, {other vars}))

        for boxIndex in self.boxList:
            # Create necessary objects for each box
            self.statsActionList.append(QtGui.QAction("Performance", self))

            # menu-specific
            self.boxMenuList.append(QtGui.QMenu())
            self.solenoidMenuList.append(QtGui.QMenu("Water Control"))
            self.primeActionList.append(QtGui.QAction("Prime (5s)", self))
            self.purgeActionList.append(QtGui.QAction("Purge (20s)", self))
            self.solenoidManualList.append(QtGui.QAction("Manual Control", self))
            self.optionsMenuList.append(QtGui.QMenu("Options"))
            self.rawTrialActionList.append(QtGui.QAction("Get Raw Trial Data", self))
            self.openFolderActionList.append(QtGui.QAction("Open &Data folder", self))
            self.openSettingsActionList.append(QtGui.QAction("Open &Settings file", self))
            self.openBoxLogActionList.append(QtGui.QAction("Open &Log file", self))
            self.createNewJsonList.append(QtGui.QAction("New &Settings file", self))
            self.newBirdActionList.append(QtGui.QAction("New &Bird", self))
            self.useNRList.append(QtGui.QAction("Use &NR Trials", self))
            self.autoSleepList.append(QtGui.QAction("&Autosleep", self))

            self.useNRList[boxIndex].setCheckable(True)
            self.autoSleepList[boxIndex].setCheckable(True)
            self.autoSleepList[boxIndex].setChecked(self.ui_options['autosleep_all'].isChecked())

            # Reorder to change order in menu
            """
            Current order:
            Open data folder
            Open log file
            Open Settings file 
            Get raw trial data
            ---
            Water Control:
                Prime
                Purge
                Manual
            ---
            Options:
                Autosleep
                Use NR
                ---
                New settings file
                New bird
            
            
            """
            self.boxMenuList[boxIndex].addAction(self.openFolderActionList[boxIndex])
            self.boxMenuList[boxIndex].addAction(self.openSettingsActionList[boxIndex])
            self.boxMenuList[boxIndex].addAction(self.openBoxLogActionList[boxIndex])
            self.boxMenuList[boxIndex].addAction(self.rawTrialActionList[boxIndex])
            self.boxMenuList[boxIndex].addSeparator()
            self.boxMenuList[boxIndex].addMenu(self.solenoidMenuList[boxIndex])
            self.boxMenuList[boxIndex].addSeparator()
            self.boxMenuList[boxIndex].addMenu(self.optionsMenuList[boxIndex])

            # option submenu

            self.optionsMenuList[boxIndex].addAction(self.autoSleepList[boxIndex])
            self.optionsMenuList[boxIndex].addAction(self.useNRList[boxIndex])
            self.optionsMenuList[boxIndex].addSeparator()
            self.optionsMenuList[boxIndex].addAction(self.createNewJsonList[boxIndex])
            self.optionsMenuList[boxIndex].addAction(self.newBirdActionList[boxIndex])

            # Solenoid submenu
            self.solenoidMenuList[boxIndex].addAction(self.primeActionList[boxIndex])
            self.solenoidMenuList[boxIndex].addAction(self.purgeActionList[boxIndex])
            self.solenoidMenuList[boxIndex].addAction(self.solenoidManualList[boxIndex])
        # endregion
            self.autoSleepList[boxIndex].setText('Autosleep (Box {:02d})'.format(boxIndex + 1))
            autosleepMenu.addAction(self.autoSleepList[boxIndex])
            self.useNRList[boxIndex].setText('Use NR Trials (Box {:02d})'.format(boxIndex + 1))
            nrTrialMenu.addAction(self.useNRList[boxIndex])

        # region Other box-specific var setup
        for boxIndex in self.boxList:
            # Fill sleep schedule var with None to start, and fill later when box is started
            self.sleepScheduleList.append(None)
            self.lastStartList.append(None)
            self.lastTrialList.append(None)

            # Queue for running subprocesses and pulling outputs without blocking main script
            self.qList[boxIndex] = Queue.Queue()

            # Device-specific vars
            self.deviceIDList.append(None)
            self.deviceLocationList.append(None)

            ## The following lines are only if we want to implement the ability for a running pyoperant subprocess to
            #  accept external input from the GUI

            # self.qReadList[boxIndex] = Queue.Queue()  # Queue for running log-read subprocesses without blocking
            # # main script
            #
            # self.tReadList[boxIndex] = threading.Thread(target=self.read_output_box,
            #                                             args=(self.logProcessBox[boxIndex].stdout,
            #                                                   self.qReadList[boxIndex]))
            # self.tReadList[boxIndex].daemon = True
        # endregion

        # region Connect functions to buttons/objects
        for boxIndex in self.boxList:
            self.paramFileButtonBoxList[boxIndex].clicked.connect(
                lambda _, b=boxIndex: self.param_file_select(boxindex=b))
            self.performanceBoxList[boxIndex].clicked.connect(
                lambda _, b=boxIndex: self.analyze_performance(boxnumber=b))
            self.startBoxList[boxIndex].clicked.connect(lambda _, b=boxIndex: self.start_box(boxnumber=b))
            self.stopBoxList[boxIndex].clicked.connect(lambda _, b=boxIndex: self.stop_box(boxnumber=b))

            # Option menu
            self.purgeActionList[boxIndex].triggered.connect(
                lambda _, b=boxIndex: self.water_control(boxindex=b, parameter='purge', purge_time=20))
            self.primeActionList[boxIndex].triggered.connect(
                lambda _, b=boxIndex: self.water_control(boxindex=b, parameter='purge', purge_time=5))
            self.solenoidManualList[boxIndex].triggered.connect(
                lambda _, b=boxIndex: self.water_control(boxindex=b, parameter='dialog'))
            self.openFolderActionList[boxIndex].triggered.connect(
                lambda _, b=boxIndex: self.open_box_folder(boxnumber=b))
            self.openSettingsActionList[boxIndex].triggered.connect(
                lambda _, b=boxIndex: self.open_text_file(boxnumber=b, whichfile='json'))
            self.openBoxLogActionList[boxIndex].triggered.connect(
                lambda _, b=boxIndex: self.open_text_file(boxnumber=b, whichfile='boxlog'))
            self.rawTrialActionList[boxIndex].triggered.connect(
                lambda _, b=boxIndex: self.get_raw_trial_data(boxnumber=b))
            self.createNewJsonList[boxIndex].triggered.connect(
                lambda _, b=boxIndex: self.create_json_file(boxnumber=b))
            self.newBirdActionList[boxIndex].triggered.connect(
                lambda _, b=boxIndex: self.create_new_bird(boxnumber=b))
            self.useNRList[boxIndex].triggered.connect(
                lambda _, b=boxIndex: self.use_nr_trials(boxnumber=b))
            self.autoSleepList[boxIndex].triggered.connect(
                lambda _, b=boxIndex: self.auto_sleep_set(boxnumber=b))

            # Attach menu to physical option button
            self.optionButtonBoxList[boxIndex].setMenu(self.boxMenuList[boxIndex])
        # endregion

        self.closeEvent = self.close_application

        # check if each box is connected
        # tempContext = pyudev.Context()
        for device in context.list_devices(subsystem='tty'):
            try:
                deviceString = device.device_links.next()
                self.usb_monitor('add', device)
            except StopIteration:
                pass

        self.open_application()

    # region GUI button/object handling
    def param_file_select(self, boxindex):

        existingFile = self.paramFileBoxList[boxindex].toPlainText()
        if os.path.isfile(existingFile):  # If param file is already specified, start in that folder
            existingPathFile = os.path.split(str(existingFile))
            currentPath = existingPathFile[0]
        else:  # Otherwise just start in working directory
            currentPath = os.path.dirname(os.path.realpath(__file__))
        paramFile = QtGui.QFileDialog.getOpenFileName(self, "Select Preferences File", currentPath,
                                                      "JSON Files (*.json)")
        # execute getOpenFileName dialog and set the directory variable to be equal to the user selected directory

        if paramFile:  # if user didn't pick a file don't replace existing path

            self.paramFileBoxList[boxindex].setPlainText(paramFile)  # add file to the listWidget

    def box_button_control(self, boxnumber, parameter):
        if parameter == 'stop' or parameter == 'enable':
            # Enable objects when box is not running
            self.paramFileButtonBoxList[boxnumber].setEnabled(True)
            self.birdEntryBoxList[boxnumber].setReadOnly(False)
            self.startBoxList[boxnumber].setEnabled(True)
            self.stopBoxList[boxnumber].setEnabled(False)
            self.log.debug("Setting status icon to 'stop'")
            self.status_icon(boxnumber, 'stop')

        elif parameter == 'sleep':
            # Enable objects when box is not running
            self.paramFileButtonBoxList[boxnumber].setEnabled(True)
            self.birdEntryBoxList[boxnumber].setReadOnly(False)
            self.startBoxList[boxnumber].setEnabled(False)
            self.stopBoxList[boxnumber].setEnabled(True)
            self.log.debug("Setting status icon to 'sleep'")
            self.status_icon(boxnumber, 'sleep')

        elif parameter == 'start':
            # Hide and/or disable objects while box is running
            self.paramFileButtonBoxList[boxnumber].setEnabled(False)
            self.birdEntryBoxList[boxnumber].setReadOnly(True)
            self.startBoxList[boxnumber].setEnabled(False)
            self.stopBoxList[boxnumber].setEnabled(True)
            self.log.debug("Setting status icon to 'start'")
            self.status_icon(boxnumber, 'start')

        elif parameter == 'disable':
            # For when Teensy isn't connected
            self.paramFileButtonBoxList[boxnumber].setEnabled(True)
            self.birdEntryBoxList[boxnumber].setReadOnly(False)
            self.startBoxList[boxnumber].setEnabled(False)
            self.stopBoxList[boxnumber].setEnabled(False)
            self.log.debug("Setting status icon to 'blank'")
            self.status_icon(boxnumber, 'blank')

    def open_box_folder(self, boxnumber):
        settingsPath = str(self.paramFileBoxList[boxnumber].toPlainText())
        folderPath = os.path.split(settingsPath)
        if os.path.exists(folderPath[0]):
            # print folderPath[0]
            # self.log.info(folderPath[0])
            subprocess.Popen(["xdg-open", folderPath[0]])
        else:
            msg = QtGui.QMessageBox()
            msg.setIcon(2)
            msg.setText('Warning: Folder not found')
            msg.setStandardButtons(QtGui.QMessageBox.Ok)
            msg.exec_()
            self.log.error('Warning: Data folder not found: ({})'.format(folderPath[0]))

    def open_text_file(self, boxnumber, whichfile='json'):
        filePath = ''  # default
        if whichfile == 'boxlog':
            settingsPath = str(self.paramFileBoxList[boxnumber].toPlainText())
            birdName = str(self.birdEntryBoxList[boxnumber].toPlainText())
            folderPath = os.path.split(settingsPath)
            filePath = os.path.join(folderPath[0], birdName + '.log')
        elif whichfile == 'guierror':
            filePath = self.error_file
        elif whichfile == 'guilog':
            filePath = self.log_file
        elif whichfile == 'json':
            filePath = str(self.paramFileBoxList[boxnumber].toPlainText())

        if not len(filePath) > 0:  # value of whichfile doesn't match any of the options
            pass
        elif os.path.exists(filePath):
            subprocess.Popen(["geany", filePath])
        else:
            msg = QtGui.QMessageBox()
            msg.setIcon(2)
            msg.setText('Warning: File not found')
            msg.setStandardButtons(QtGui.QMessageBox.Ok)
            msg.exec_()
            self.log.error('Warning: Selected file not found: ({})'.format(filePath))

    def create_json_file(self, boxnumber, birdname=''):
        currentPath = os.path.dirname('/home/rouse/Desktop/pyoperant/pyoperant/pyoperant/behavior/')
        paramFile = QtGui.QFileDialog.getOpenFileName(self, "Select Template for Settings", currentPath,
                                                      "JSON Files (*.json)")
        if paramFile:  # if user didn't pick a file don't replace existing path
            # build new data folder path
            if not birdname:
                birdname = str(self.birdEntryBoxList[boxnumber].toPlainText())
            else:
                birdname = str(birdname)

            try:
                from pyoperant.local import DATAPATH
            except ImportError:
                DATAPATH = '/home/rouse/bird/data'
            data_dir = os.path.join(DATAPATH, birdname)

            if not os.path.exists(data_dir):
                os.mkdir(data_dir)

            newParamFile = birdname + "_config.json"
            newParamPath = os.path.join(data_dir, newParamFile)

            # Copy template file to new data directory
            copyfile(paramFile, newParamPath)
            self.paramFileBoxList[boxnumber].setPlainText(newParamPath)
            return True
        return False

    def create_new_bird(self, boxnumber):
        newBird, ok = QtGui.QInputDialog.getText(self, 'Change Bird', 'Bird ID:', QtGui.QLineEdit.Normal, "")
        if newBird and ok:  # User entered bird name and clicked OK
            jsonSuccess = self.create_json_file(boxnumber, newBird)
            if jsonSuccess:
                self.birdEntryBoxList[boxnumber].setPlainText(newBird)

    # endregion

    # region Pyoperant stop/start functions
    def stop_box(self, boxnumber, error_mode=False, sleep_mode=False):
        # stop selected box
        if not self.subprocessBox[boxnumber] == 0:  # Only operate if box is running
            while True:  # Empty queue so process can end gracefully
                try:
                    # error = '{0}\n{1}'.format(error, self.qList[boxnumber].get(False))
                    self.qList[boxnumber].get(False)
                except Queue.Empty:
                    break
        # self.tList[boxnumber].terminate()
        # self.subprocessBox[boxnumber].stderr.close()
        # self.subprocessBox[boxnumber].stdout.close()
        try:
            self.subprocessBox[boxnumber].terminate()
        except OSError:
            pass  # OSError is probably that the process is already terminated
        except AttributeError:
            pass  # Subprocess is stopped and already set to 0

        if sleep_mode:
            self.subprocessBox[boxnumber] = 1
            self.sleep_box(boxnumber)
            self.box_button_control(boxnumber, 'sleep')
        else:
            self.subprocessBox[boxnumber] = 0
            self.sleepScheduleList[boxnumber] = None
            self.box_button_control(boxnumber, 'stop')

        self.refreshfile(boxnumber)  # one last time to display any errors sent to the summaryDAT file

        # set icon if error
        if error_mode:
            self.log.debug("Setting status icon to 'error'")
            self.status_icon(boxnumber, 'error')
        # elif sleep_mode:
        #     self.log.debug("Setting status icon to 'sleep'")
        #     self.status_icon(boxnumber, 'sleep')
        # else:
        #     self.log.debug("Setting status icon to 'stop'")
        #     self.status_icon(boxnumber, 'stop')

    def start_box(self, boxnumber):
        # start selected box
        actualboxnumber = boxnumber + 1  # Boxnumber is index, but actual box number starts from 1

        # Error checking: make sure all relevant boxes are filled and files are found:
        birdName = self.birdEntryBoxList[boxnumber].toPlainText()
        jsonPath = self.paramFileBoxList[boxnumber].toPlainText()
        if not self.checkActiveBoxList[boxnumber].checkState():  # Box needs to be marked as active
            error = "Error: Box not set as Active."
            self.display_message(boxnumber, error, target='status')
        elif birdName == "":  # Need a bird specified
            error = "Error: Bird name must be entered."
            self.display_message(boxnumber, error, target='status')
        elif not os.path.isfile(jsonPath):  # Make sure param file is specified
            error = "Error: No parameter file selected."
            self.display_message(boxnumber, error, target='status')
        elif not os.path.exists("/dev/teensy{:02d}".format(actualboxnumber)):  # check if Teensy is detected:
            error = "Error: Teensy {:02d} not detected.".format(actualboxnumber)
            self.display_message(boxnumber, error, target='status')
        else:
            try:
                from pyoperant.local import DATAPATH
            except ImportError:
                DATAPATH = '/home/rouse/bird/data'
            self.experimentPath = DATAPATH

            if self.subprocessBox[boxnumber] == 0 or self.subprocessBox[boxnumber] == 1:  # Make sure box isn't already
                # running or sleeping
                self.subprocessBox[boxnumber] = subprocess.Popen(
                    ['python', '/home/rouse/Desktop/pyoperant/pyoperant/scripts/behave', '-P',
                     str(boxnumber + 1), '-S', '{0}'.format(birdName), '{0}'.format(self.behaviorField.currentText()),
                     '-c', '{0}'.format(jsonPath)], stdin=open(os.devnull), stderr=subprocess.PIPE,
                    stdout=open(os.devnull))

                # Thread for reading error messages
                self.tList[boxnumber] = threading.Thread(target=self.read_output_box,
                                                         args=(boxnumber, self.subprocessBox[boxnumber].stderr,
                                                               self.qList[boxnumber]))
                self.tList[boxnumber].daemon = True

                self.tList[boxnumber].start()

                error = self.get_error(boxnumber)

                if error and not error[0:4] == "ALSA" and not error[0:5] == 'pydev' and not error[0:5] == 'debug':
                    print error
                    self.log.info(error)
                    self.display_message(boxnumber, error, target='status')
                    self.stop_box(boxnumber, error_mode=True)
                    # self.subprocessBox[boxnumber].terminate
                    # self.subprocessBox[boxnumber].wait
                    # self.subprocessBox[boxnumber] = 0
                    # self.graphicBoxList[boxnumber].setPixmap(self.redIcon)
                else:  # Successfully started
                    self.box_button_control(boxnumber, "start")  # UI modifications while box is running
                    # self.graphicBoxList[boxnumber].setPixmap(self.greenIcon)
                    self.log.debug("Setting status icon to 'start'")
                    self.status_icon(boxnumber, 'start')
                    self.lastStartList[boxnumber] = dt.datetime.now()
                    self.sleepScheduleList[boxnumber] = self.defaultSleepSchedule
                    # with open(jsonPath, 'r') as f:
                    #     jsonLoaded = json.load(f)
                    #     self.sleepScheduleList[boxnumber] = {jsonLoaded["session_schedule"],
                    #                                          jsonLoaded["light_schedule"]}

    def start_all(self):
        # start all checked boxes
        for boxnumber in self.boxList:
            if self.subprocessBox[boxnumber] == 0 and self.checkActiveBoxList[boxnumber].checkState():
                self.start_box(boxnumber)
                time.sleep(1)

    def stop_all(self):
        # stop all running boxes
        for boxnumber in self.boxList:
            if not self.subprocessBox[boxnumber] == 0:
                self.stop_box(boxnumber)

    def read_output_box(self, boxnumber, pipe, q):

        while True:
            output = pipe.readline()
            q.put(output)

            # Added the following so that the queue stops when the parent thread stops
            # (so it doesn't take off and inflate memory usage)
            try:
                running = self.subprocessBox[boxnumber].poll()  # Tried this on 10/22/18
            except AttributeError:
                # If subprocess was already stopped, and the subprocessBox value was already cleared,
                # then poll() will throw an error
                running = 1
            # running = self.subprocessBox[boxnumber]
            if running is not None:
                break

    def sleep_box(self, boxnumber):
        # Turn off house light
        boxnumber = boxnumber + 1
        print("Box {:d} going to sleep".format(boxnumber))
        self.log.info("Box {:d} going to sleep".format(boxnumber))
        device_name = '/dev/teensy{:02d}'.format(boxnumber)
        device = serial.Serial(port=device_name, baudrate=19200, timeout=5)
        if device is None:
            print 'Could not open serial device {}'.format(device_name)
            self.log.info('Could not open serial device {}'.format(device_name))
            raise 'Could not open serial device {}'.format(device_name)
        else:
            device.readline()
            device.flushInput()
            device.write("".join([chr(3), chr(3)]))  # set channel 3 (house light) as output
            device.write("".join([chr(3), chr(1)]))  # turn off house lights
            device.close()  # close connection

    def wake_box(self, boxnumber):
        print("Box {:d} waking up".format(boxnumber))
        self.log.info("Box {:d} waking up".format(boxnumber))
        device_name = '/dev/teensy{:02d}'.format(boxnumber)
        device = serial.Serial(port=device_name,
                               baudrate=19200,
                               timeout=5)
        if device is None:
            self.log.error('Could not open serial device {}'.format(device_name))
            raise 'Could not open serial device {}'.format(device_name)
        else:
            device.readline()
            device.flushInput()
            device.write("".join([chr(3), chr(3)]))  # set channel 3 (house light) as output
            device.write("".join([chr(3), chr(2)]))  # turn on house lights
            device.close()  # close connection

    # endregion

    # region Unused function
    def read_input(self, write_pipe, in_pipe_name):
        """reads input from a pipe with name `read_pipe_name`,
        writing this input straight into `write_pipe`"""
        while True:
            with open(in_pipe_name, "r") as f:
                write_pipe.write(f.read())

    # endregion

    # region Physical device monitoring

    def usb_monitor(self, action, device):
        # deviceString = device.device_node
        # print deviceString
        if str(device.parent.subsystem) == 'usb':
            # deviceString[0:4] == '/dev':  # Only pass if device path is valid
            devInfo = self.DeviceInfo(device)
            boxIndex = devInfo.boxIndex
            # try:
            #     # Get box number
            #     deviceStringSplit = os.path.split(deviceString)
            #     boxLink = deviceStringSplit[1]
            #     boxLinkSplit = re.split('Board(\\d*)', boxLink)
            #     devInfo.boxNumber = int(boxLinkSplit[1])
            #     boxIndex = devInfo.boxNumber - 1  # Teensy numbers are indexed from 1, but box array indexed from 0
            #
            # except IndexError:
            #     devInfo.boxNumber = None
            #     boxIndex = None
            #     self.log.error('Error: board not recognized')
            #
            # if boxIndex is not None:
            #     # Get device ID (e.g. "tty...")
            #     device_path = os.path.split(device.device_path)
            #     deviceID = device_path[1]
            #
            #     # Get USB port info
            #     usbPath = device.parent.parent.device_node
            #     usbSplit = re.split('/', usbPath)
            #     usbString = 'Bus {:02d}:{:02d}'.format(int(usbSplit[-2]), int(usbSplit[-1]))

            # enable or disable
            if action == 'add':
                self.log.debug('USB device connected: Teensy {:02d}, device {:s}, USB: {:s}'.format(
                    devInfo.boxNumber, devInfo.deviceID, devInfo.usbString))
                self.deviceIDList[boxIndex] = devInfo.deviceID
                self.deviceLocationList[boxIndex] = devInfo.usbString
                self.check_teensy(boxIndex, True)
            elif action == 'remove':
                self.log.debug('USB device disconnected: Teensy {:02d}, device {:s}, USB: {:s}'.format(
                    devInfo.boxNumber, devInfo.deviceID, devInfo.usbString))
                self.deviceLocationList[boxIndex] = None
                self.deviceIDList[boxIndex] = None
                self.check_teensy(boxIndex, False)

    def check_teensy(self, boxindex=None, connect=False):
        # device_path is result from device_paths of device that was connected/disconnected
        # It needs to be parsed to get the actual box number
        # if device_path[0:4] == '/dev':  # Only pass if device path is valid
        #     devicePathSplit = os.path.split(device_path)
        #     try:
        #         boxLink = devicePathSplit[1]
        #         # print boxLink
        #         # self.log.info(boxLink)
        #         match = re.split('Board(\\d*)', boxLink)
        #         boxnumber = int(
        #             match[1]) - 1  # Box number as index is indexed from 0, but Teensy numbers are indexed from 1
        #         # print boxnumber
        #         # self.log.info(boxnumber)
        #     except IndexError:
        #         boxnumber = None
        #         print 'Error: board not recognized'
        #         self.log.error('Error: board not recognized')

        if boxindex is not None:
            if connect:
                parameter = 'enable'
            else:
                parameter = 'disable'
            self.log.info("Teensy {:02d} recognized, status set to {}".format(boxindex, parameter))
            usbToolTip = 'System ID: ' + self.deviceIDList[boxindex] + '\n' + self.deviceLocationList[boxindex]
            self.labelBoxList[boxindex].setToolTip(usbToolTip)
            # self.usbInfoBoxList[boxindex].setText(self.deviceIDList[boxindex])
            self.box_button_control(boxindex, parameter)
        else:
            pass

    def teensy_control(self, boxindex, parameter):
        # quick method to enable or disable gui buttons and stop pyoperant if teensy is disconnected
        self.stop_box(boxindex)
        self.box_button_control(boxindex, parameter)

    # endregion

    # region Water system functions
    def water_control(self, boxindex, parameter='purge', purge_time=20):

        boxnumber = boxindex + 1  # boxindex is device number - 1
        if self.subprocessBox[boxindex] == 0:  # If box is not running
            if parameter == 'dialog':
                dialog = SolenoidGui(boxnumber)
                dialog.exec_()
            elif parameter == 'purge':
                self.log.info("Purging water system in box {:d} for {:d} s".format(boxnumber, purge_time))
                device_name = '/dev/teensy{:02d}'.format(boxnumber)
                device = serial.Serial(port=device_name, baudrate=19200, timeout=5)
                if device is None:
                    self.log.error('Water error: Could not open serial device {}'.format(device_name))
                    raise 'Could not open serial device {}'.format(device_name)

                device.readline()
                device.flushInput()
                self.log.debug("Successfully opened device {}".format(device_name))
                device.write("".join([chr(16), chr(3)]))  # set channel 16 (solenoid) as output
                # device.write("".join([chr(16), chr(2)]))  # close solenoid, just in case
                device.write("".join([chr(16), chr(1)]))  # open solenoid
                startTime = time.time()

                while True:
                    elapsedTime = time.time() - startTime
                    if purge_time <= elapsedTime:
                        break

                device.write("".join([chr(16), chr(2)]))  # close solenoid
                device.close()  # close connection
                print "Purged box {:02d}".format(boxnumber)
                self.log.info("Purged box {:02d}".format(boxnumber))
        else:
            print "Cannot open solenoid: Box {0} is currently running".format(str(boxnumber))
            self.log.error("Water error: Cannot open solenoid: Box {0} is currently running".format(str(boxnumber)))

    # endregion

    # region Box updating functions
    def refreshall(self):
        # refresh each box, checking for run status, checking if box should sleep

        for boxnumber in self.boxList:
            if self.debug:
                self.refreshfile(boxnumber)

            # If box is currently running, check sleep schedule
            if not self.subprocessBox[boxnumber] == 0:  # If box is supposed to be running or sleeping
                # Check sleep first
                if self.autoSleepList[boxnumber].isChecked() and self.sleepScheduleList[boxnumber] is not None:
                    schedule = self.sleepScheduleList[boxnumber]
                    if self.check_time(schedule):  # box should be awake
                        if self.subprocessBox[boxnumber] == 1:  # subprocessBox set to 1 when sleeping
                            # Box not awake, make it awake
                            self.start_box(boxnumber)
                    else:  # box should be asleep
                        if not self.subprocessBox[boxnumber] == 1:  # subprocessBox set to 1 when sleeping
                            # Box not asleep, make it sleep
                            self.stop_box(boxnumber, sleep_mode=True)

                # Check if subprocess is still running, not sleeping
                if self.subprocessBox[boxnumber] != 1:  # subprocessBox set to 1 when sleeping, so don't check that
                    # Box should be active, not sleeping
                    poll = self.subprocessBox[boxnumber].poll()  # poll() == 0 means the subprocess is still running
                    if poll is None:  # or self.args['debug'] is not False:
                        self.refreshfile(boxnumber)

                        # Restart if last trial was more than 2 hours ago
                        try:
                            timeDeltaSinceTrial = (dt.datetime.now() - self.lastTrialList[boxnumber])
                            timeSinceTrial = timeDeltaSinceTrial.total_seconds() / 3600
                        except TypeError:
                            timeSinceTrial = 10  # if last trial time isn't available, then assume it's very large

                        timeDeltaSinceStart = dt.datetime.now() - self.lastStartList[boxnumber]  # also ensure box has
                        # been running for at least two hours
                        timeSinceStart = timeDeltaSinceStart.total_seconds() / 3600

                        if timeSinceStart > self.idleTime and timeSinceTrial > self.idleTime:
                            # restart box
                            self.stop_box(boxnumber, error_mode=False)  # stop box
                            self.log.info('Restarting box {:02d}'.format(boxnumber + 1))
                            time.sleep(2)  # wait a second
                            self.start_box(boxnumber)  # restart box
                    else:
                        self.stop_box(boxnumber, error_mode=True)

    def refreshfile(self, boxnumber):

        if self.debug:
            self.experimentPath = '/home/rouse/bird/data'
        birdName = str(self.birdEntryBoxList[boxnumber].toPlainText())
        # experiment_path = str(self.logpathList[boxnumber]+"/")
        summary_file = os.path.join(self.experimentPath, birdName, "{0}{1}".format(birdName, '.summaryDAT'))
        error_log = os.path.join(self.experimentPath, birdName, 'error.log')
        errorData = []  # Initialize to prevent the code from getting tripped up when checking for error text

        try:
            f = open(summary_file, 'r')
        except IOError:
            f = False

        try:
            g = open(error_log, 'r')
        except IOError:
            g = False

        if f:
            logData = f.readlines()
            f.close()
            if isinstance(logData, list):
                messageFormatted = ''.join(logData)
                messageFormatted = _from_utf8(messageFormatted)
                if len(logData[0]) > 50:
                    logData = json.loads(str(messageFormatted))
                    logFull = True  # full summary loaded, not just single message
                else:
                    logData = messageFormatted
                    logFull = False
            else:
                logData = _from_utf8(logData)
                logFull = False
                # logData = f.readlines()
                # f.close()

            if g:
                errorData = g.readlines()
                g.close()
                errorSuccess = True
            else:
                errorSuccess = False

            if errorSuccess and len(errorData) > 1:  # If error file correctly opened and there is an error
                # print "error log"
                # self.log.info("error log")
                self.display_message(boxnumber, errorData, target='status')
            else:
                if logFull:
                    # self.display_message(boxnumber, logData)
                    self.display_message(boxnumber, logData['phase'], target='phase')
                    self.display_message(boxnumber, 'Last Trial: ' + logData['last_trial_time'], target='time')

                    try:
                        self.lastTrialList[boxnumber] = dt.datetime.strptime(str(logData['last_trial_time']), '%c')
                    except ValueError:
                        try:
                            self.lastTrialList[boxnumber] = dt.datetime.strptime(str(logData['last_trial_time']),
                                                                                 '%a %b %d %H:%M:%S %Y')
                        except ValueError:
                            self.log.error('Last Trial datetime not parsed properly')

                    logTotalsMessage = "Training Trials: {trials}   Probe trials: {probe_trials}\n" \
                                       "Rf'd responses: {feeds}".format(**logData)
                    logTotalsMessage.encode('utf8')
                    self.display_message(boxnumber, logTotalsMessage, target='status')

                    self.logRawCounts = QtGui.QStandardItemModel(self)
                    self.logRawCounts.setHorizontalHeaderLabels(["S+", "S-", "Prb+", "Prb-"])
                    self.logRawCounts.setVerticalHeaderLabels(["RspSw", "TrlSw"])

                    rawCounts = [
                        [
                            str(logData["correct_responses"]),
                            str(logData["false_alarms"]),
                            str(logData["probe_hit"]),
                            str(logData["probe_FA"])
                        ],
                        [
                            ("{0} ({1})".format(logData["misses"], logData["splus_nr"])),
                            ("{0} ({1})".format(logData["correct_rejections"], logData["sminus_nr"])),
                            ("{0} ({1})".format(logData["probe_miss"], logData["probe_miss_nr"])),
                            ("{0} ({1})".format(logData["probe_CR"], logData["probe_CR_nr"]))
                        ]
                    ]
                    for row in range(len(rawCounts)):
                        for column in range(len(rawCounts[row])):
                            self.logRawCounts.setItem(row, column, QtGui.QStandardItem(rawCounts[row][column]))

                    self.statusTableBoxList[boxnumber].setModel(self.logRawCounts)
                    self.statusTableBoxList[boxnumber].horizontalHeader().setResizeMode(
                        QtGui.QHeaderView.ResizeToContents)
                    self.statusTableBoxList[boxnumber].horizontalHeader().setStretchLastSection(True)
                    self.statusTableBoxList[boxnumber].verticalHeader().setResizeMode(
                        QtGui.QHeaderView.Stretch)

                    # logRawCounts = "\tS+\tS-\tPrb+\tPrb-\n" \
                    #                "RespSw\t{correct_responses}\t{false_alarms}\t{probe_hit}\t{probe_FA}\n" \
                    #                "TrlSw\t{misses}({splus_nr})\t{correct_rejections}({sminus_nr})\t" \
                    #                "{probe_miss}({probe_miss_nr})\t{probe_CR}({probe_CR_nr})".format(**logData)
                    # logTotalsMessage.encode('utf8')
                    # self.display_message(boxnumber, logTotalsMessage, target='statusRaw')

                    if self.useNRList[boxnumber].isChecked():
                        logStats = "d' (NR): {dprime_NR:1.2f}      " + \
                                   "Beta (NR): {bias_NR:1.2f} {bias_description_NR}".format(**logData)
                    else:
                        logStats = "d': {dprime:1.2f}      Beta: {bias:1.2f} {bias_description}".format(**logData)
                    logStats.decode('utf8')
                    self.display_message(boxnumber, logStats, target='statusStats')

                else:
                    self.display_message(boxnumber, logData, target='status')
        else:
            print "{0}{1}".format("Unable to open file for ", birdName)
            self.log.info("{0}{1}".format("Unable to open file for ", birdName))

        # with open(summary_file, 'r') as f:
        # logData = f.readlines()
        # self.statusTotalsBoxList[boxnumber].setPlainText('\n'.join(logData[-10:]))
        # f.close()

    # endregion

    # region Utility functions
    def check_time(self, schedule, fmt="%H:%M", **kwargs):
        """ Determine whether current time is within $schedule
        Primary use: determine whether trials should be done given the current time and light schedule or
        session schedule

        returns Boolean if current time meets schedule

        schedule='sun' will change lights according to local sunrise and sunset

        schedule=[('07:00','17:00')] will have lights on between 7am and 5pm
        schedule=[('06:00','12:00'),('18:00','24:00')] will have lights on between

        """

        if schedule == 'sun':
            if is_day(kwargs):
                return True
        else:
            for epoch in schedule:
                assert len(epoch) is 2
                now = dt.datetime.time(dt.datetime.now())
                start = dt.datetime.time(dt.datetime.strptime(epoch[0], fmt))
                end = dt.datetime.time(dt.datetime.strptime(epoch[1], fmt))
                if self.time_in_range(start, end, now):
                    return True
        return False

    def time_in_range(self, start, end, x):
        """Return true if x is in the range [start, end]"""
        if start <= end:
            return start <= x <= end
        else:
            return start <= x or x <= end

    def use_nr_trials(self, boxnumber):
        # single box: invert selection of whether to use NR trials
        self.useNRList[boxnumber].setChecked(self.useNRList[boxnumber].isChecked())

    def auto_sleep_set(self, boxnumber):
        # single box: invert selection of whether to auto sleep
        self.autoSleepList[boxnumber].setChecked(self.autoSleepList[boxnumber].isChecked())

    def use_nr_trials_all(self):
        self.ui_options['use_nr_all'].setChecked(self.ui_options['use_nr_all'].isChecked())
        for boxnumber in self.boxList:
            self.useNRList[boxnumber].setChecked(self.ui_options['use_nr_all'].isChecked())

    def auto_sleep_set_all(self):
        print 'autosleep'
        self.ui_options['autosleep_all'].setChecked(self.ui_options['autosleep_all'].isChecked())
        for boxnumber in self.boxList:
            self.autoSleepList[boxnumber].setChecked(self.ui_options['autosleep_all'].isChecked())
    # endregion

    # region Error handling
    def get_error(self, boxnumber):
        # Check output for any errors
        while True:  # Loop through error codes generated, if any
            error = ""
            try:
                error = '{0}\n{1}'.format(error, self.qList[boxnumber].get(False))
            except Queue.Empty:
                break
        return error

    def error_handler(self, boxnumber):
        # Take any errors and stop box, if necessary
        error = self.get_error(boxnumber)
        if error:
            if error[0:4] == "ALSA":
                # Ignore ALSA errors; they've always occurred and don't interfere (have to do with the sound chip not
                # liking some channels as written)
                self.display_message(boxnumber, error, target='status')
                print error
                self.log.error(error)
            elif error[0:5] == 'pydev':
                # Ignore pydev errors - thrown automatically during PyCharm debugging
                pass
            elif error[0:5] == 'debug':  #
                pass
            # elif error[0:5] == 'pydev':  # Add additional exceptions here
            #     pass
            else:
                self.display_message(boxnumber, error, target='status')
                print error
                self.log.error(error)
                self.stop_box(boxnumber, error_mode=True)
                return True
        else:
            return False

    def display_message(self, boxnumber, message, target='status'):  # quick method for redirecting messages to status
        # box
        if isinstance(message, list):
            messageFormatted = ''.join(message)
            messageFormatted = _from_utf8(messageFormatted)
        else:
            messageFormatted = _from_utf8(message)

        if target == 'status':
            self.statusTotalsBoxList[boxnumber].setText(messageFormatted)
        elif target == 'statusRaw':
            self.statusTableBoxList[boxnumber].setText(messageFormatted)
        elif target == 'statusStats':
            self.statusStatsBoxList[boxnumber].setText(messageFormatted)
        elif target == 'phase':
            self.phaseBoxList[boxnumber].setText(messageFormatted)
        elif target == 'time':
            self.lastTrialLabelList[boxnumber].setText(messageFormatted)

    def log_config(self):
        # capture all terminal output and send to log file instead
        self.log_file = os.path.join(os.getcwd(), 'GUI_log.log')
        self.error_file = os.path.join(os.getcwd(), 'GUI_error.log')
        log_path = os.path.join(os.getcwd())
        if not os.path.exists(log_path):  # Add path if it doesn't exist
            os.makedirs(log_path)

        if self.debug:
            self.log_level = logging.DEBUG
        else:
            self.log_level = logging.INFO

        sys.excepthook = _log_except_hook  # send uncaught exceptions to log file

        logging.basicConfig(filename=self.log_file,
                            level=self.log_level,
                            format='"%(asctime)s","%(levelname)s","%(message)s"')
        self.log = logging.getLogger()
        errorHandler = logging.FileHandler(self.error_file, mode='a')
        errorHandler.setLevel(logging.ERROR)
        errorHandler.setFormatter(logging.Formatter('"%(asctime)s","%(message)s'))

        self.log.addHandler(errorHandler)

    # endregion

    # region data analysis
    def analyze_performance(self, boxnumber):
        dataFolder = os.path.dirname(str(self.paramFileBoxList[boxnumber].toPlainText()))
        bird_name = self.birdEntryBoxList[boxnumber].toPlainText()
        dialog = StatsGui(dataFolder, bird_name)
        dialog.exec_()

    def get_raw_trial_data(self, boxnumber):
        bird_name = str(self.birdEntryBoxList[boxnumber].toPlainText())
        dataFolder = os.path.join(self.experimentPath, bird_name)
        performance = analysis.Performance(dataFolder)
        output_path = QtGui.QFileDialog.getSaveFileName(self, "Save As...", dataFolder, "CSV Files (*.csv)")
        if output_path:
            performance.raw_trial_data.to_csv(str(output_path))
    # endregion

    # region GUI application functions
    def open_application(self):
        # Command line argument parsing
        # message = u'Beta123'#.decode('utf8')
        # self.statusTotalsBoxList[1].setPlainText(message)
        self.args = self.parse_commandline()

        shutdownPrev = True  # Define first then settings file overwrites, if present

        settingsFile = 'settings.json'
        if os.path.isfile(settingsFile):  # Make sure param file is specified
            self.log.info('settings.json file detected, loading settings')
            with open(settingsFile, 'r') as f:
                dictLoaded = json.load(f)
                if 'birds' in dictLoaded:
                    for i, birdName in dictLoaded['birds']:
                        if birdName:
                            self.birdEntryBoxList[i].setPlainText(birdName)

                if 'paramFiles' in dictLoaded:
                    for i, paramFile in dictLoaded['paramFiles']:
                        if paramFile:
                            self.paramFileBoxList[i].setPlainText(paramFile)

                if 'active' in dictLoaded:
                    for i, check in dictLoaded['active']:
                        if check:
                            self.checkActiveBoxList[i].setChecked(True)
                # Whether last shutdown was done properly
                if 'shutdownProper' in dictLoaded:
                    shutdownPrev = dictLoaded['shutdownProper']

            ## Power outage handling ##
            # Set shutdownProper to False when GUI is opened, set it to true when it's properly closed.
            # That way if it doesn't get closed properly, shutdownProper still reads False and the GUI will
            # automatically start all checked boxes on startup (in case of power outage)

            # Write False to shutdownProper in the settings file
            dictLoaded['shutdownProper'] = False
            with open('settings.json', 'w') as outfile:
                json.dump(dictLoaded, outfile, ensure_ascii=False)

            # If last shutdown was improper, start all checked boxes
            if not shutdownPrev:
                if self.args['debug'] is False:
                    self.start_all()

        try:
            from pyoperant.local import DATAPATH
        except ImportError:
            DATAPATH = '/home/rouse/bird/data'
        self.experimentPath = DATAPATH

    def close_application(self, event):
        ## Save settings to file to reload for next time
        # build dictionary to save
        paramFileList = []
        birdListTemp = []
        activeListTemp = []
        for boxnumber in self.boxList:
            # Get plain text of both param file path and bird name, then join in a list for each
            paramSingle = str(self.paramFileBoxList[boxnumber].toPlainText())
            paramFileList.append(paramSingle)
            birdSingle = str(self.birdEntryBoxList[boxnumber].toPlainText())
            birdListTemp.append(birdSingle)
            activeListTemp.append(self.checkActiveBoxList[boxnumber].isChecked())
        paramFiles = zip(self.boxList, paramFileList)
        birds = zip(self.boxList, birdListTemp)
        active = zip(self.boxList, activeListTemp)
        shutdownProper = True

        d = {'paramFiles': paramFiles, 'birds': birds, 'active': active, 'shutdownProper': shutdownProper}
        # d = {}
        # d['paramFiles'] = paramFiles
        # d['birds'] = birds
        # d['active'] = active

        with open('settings.json', 'w') as outfile:
            json.dump(d, outfile, ensure_ascii=False, indent=4, separators=(',', ': '))

        ## Box-specific closing operations
        # Close all serial ports, if available
        for boxnumber in self.boxList:
            device_name = "{0}{1}".format('/dev/teensy', int(boxnumber + 1))
            try:
                device = serial.Serial(port=device_name,
                                       baudrate=19200,
                                       timeout=5)

                if device.isOpen():
                    device.close()
                    # print "Closed device {:d}".format(int(boxnumber + 1))
                    self.log.debug("Closed device {:d}".format(int(boxnumber + 1)))
            except serial.SerialException:
                pass

            # print "Checked device {:d}".format(int(boxnumber + 1))
            self.log.debug("Checked device {:d}".format(int(boxnumber + 1)))
        # Stop running sessions
        self.stop_all()

        event.accept()  # Accept GUI closing

    def parse_commandline(self, arg_str=sys.argv[1:]):
        parser = argparse.ArgumentParser(description='Start the Pyoperant GUI')

        parser.add_argument('-d', '--debug',
                            action='store_true',
                            default=False,
                            help='Turn on debug mode'
                            )
        args = parser.parse_args(arg_str)
        return vars(args)
    # endregion


class SolenoidGui(QtGui.QDialog, pyoperant_gui_layout.UiSolenoidControl):
    """
    Code for creating and managing dialog that can open and close the solenoid for a given box manually
    Primarily to aid in water system cleaning process
    Added 10/20/18 by AR
    """

    def __init__(self, box_number):
        super(self.__class__, self).__init__()

        self.setup_ui(self)  # from pyoperant_gui_layout.py

        self.open_Button.clicked.connect(lambda _, b=box_number: self.solenoid_control('open', b))
        self.close_Button.clicked.connect(lambda _, b=box_number: self.solenoid_control('close', b))
        self.done_Button.clicked.connect(self.close_window)
        self.log = logging.getLogger(__name__)
        self.box_name.setText(str("Box {:02d}".format(box_number)))
        self.solenoid_Status_Text.setText(_translate("solenoid_control", "CLOSED", None))

        self.solenoidChannel = 16

        self.device = None

    def serial_connect(self, boxnumber):
        """Connect to solenoid of boxnumber, return error if connection cannot be established"""
        if self.device is None:
            self.device_name = '/dev/teensy{:02d}'.format(boxnumber)

            try:
                self.device = serial.Serial(port=self.device_name,
                                            baudrate=19200,
                                            timeout=5)
            except serial.SerialException:
                self.log.error('Could not open serial device {}'.format(self.device_name))
                raise serial.SerialException('Could not open serial device {}'.format(self.device_name))
            else:
                self.device.readline()
                self.device.flushInput()
                self.log.debug("Successfully opened device {}".format(self.device_name))

                # set labels
                self.box_name.setText(str("Box {:02d}".format(box_number)))

                # set self.solenoidChannel as output
                self.device.write("".join([chr(self.solenoidChannel), chr(3)]))

    def solenoid_control(self, action, boxnumber):
        if action == 'open':
            self.log.info("Opening water system in box {:d}".format(boxnumber))
        elif action == 'close':
            self.log.info("Closing water system in box {:d}".format(boxnumber))

        try:
            # attempt to connect to Teensy
            self.serial_connect(boxnumber)
        except serial.SerialException:
            # if Teensy connection fails, set status text to indicate error
            self.solenoid_Status_Text.setText(str("Not Accessible (SerialException)"))
        else:
            # send signals and update layout
            if action == 'open':
                self.device.write("".join([chr(self.solenoidChannel), chr(1)]))  # open solenoid

                self.solenoid_Status_Text.setText(str("OPEN"))
                self.open_Button.setEnabled(False)
                self.close_Button.setEnabled(True)
            elif action == 'close':
                self.device.write("".join([chr(self.solenoidChannel), chr(2)]))  # close solenoid

                print "Closed water system in box {0}".format(str(boxnumber))

                self.solenoid_Status_Text.setText(str("CLOSED"))
                self.close_Button.setEnabled(False)
                self.open_Button.setEnabled(True)

    def close_window(self):
        """Make sure serial connection is closed before exiting window."""
        if self.device is not None:
            self.device.close()  # close connection
        self.accept()


class StatsGui(QtGui.QDialog, pyoperant_gui_layout.StatsWindow):
    """
    Code for creating and managing dialog that displays bird's performance stats
    Added 11/30/18 by AR
    This is probably done all very very wrong:
        - Pyqt can't easily display a DataFrame with multiple indices per axis, so the whole
        DataFrame is exported to a csv and that file is then imported directly into the QTableView.
        - Importing the data from the CSV uses hard-coded column numbers, because dynamically assigning them was
        drastically slower than hardcoded values (2 seconds vs 15 seconds). God help you if the pyoperant output csv
        changes column order at any point (although adding new columns at the end shouldn't affect existing column
        indices)
        - It was frustratingly hard to get in-place filtering of the csv data (without completely removing or
        adding new columns), because QTableView uses a model, so all columns have to be referenced by index rather
        than name. Therefore all filtering, grouping, and column selection is done within pandas in the analysis.py
        file, and the table is regenerated each time a change is made to the filters/groups/columns.
        - Filters and grouping variables are also rebuilt each time the table is recalculated rather than maintaining a
        modifiable list
        - Filter vars keep all old values since they repopulate based on currently available columns (so if a column
        was filtered out, it would no longer appear in the filter list, leaving no way to restore it without removing
        all filters)
        - The column/field list is static, stored in analysis.py, so adding any additional columns or calculations
        might require modifying that list
        - Originally, the beta column was simply the character β, but that's a unicode character and converting back
        and forth between ascii and utf-8 was a nightmare to keep straight
        - For the table itself, NR columns have a line break added so the name isn't too long in the table. Therefore,
        any place that reads directly from the underlying model (like build_filter_value_lists) needs to have
        the line break removed from all column names so the name can be used properly as a key for various dicts.
    """
    def __init__(self, data_folder, bird_name):
        super(self.__class__, self).__init__()
        self.setup_ui(self)  # This is defined in pyoperant_gui_layout.py file

        # Ensure that pyqt can delete objects properly before python garbage collector goes to work
        # (prevents "QObject::startTimer: QTimer can only be used with threads started with QThread" error)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.data_folder = data_folder

        self.folder_Button.clicked.connect(self.select_bird)
        self.export_Button.clicked.connect(lambda _, b=self.data_folder: self.export(b))
        self.done_Button.clicked.connect(self.accept)

        self.performance_Table.installEventFilter(self)  # to capture keyboard commands so data can be copied directly

        self.noResponse_Checkbox.stateChanged.connect(lambda _, b='nr': self.field_preset_select(pattern=b))
        self.probe_Checkbox.stateChanged.connect(lambda _, b='probe': self.field_preset_select(pattern=b))
        self.raw_Checkbox.stateChanged.connect(lambda _, b='raw': self.field_preset_select(pattern=b))
        self.fieldListSelectNone.clicked.connect(lambda _, b='none': self.field_preset_select(pattern=b))
        self.fieldListSelectAll.clicked.connect(lambda _, b='all': self.field_preset_select(pattern=b))

        self.create_grouping_checkbox('Subject')
        self.create_grouping_checkbox('Date')
        self.create_grouping_checkbox('Block')
        self.create_grouping_checkbox('Stimulus')
        self.create_grouping_checkbox('Class')
        self.create_grouping_checkbox('Response Type')
        self.create_grouping_checkbox('Response')
        self.groupByCheckboxes['Subject'].setChecked(True)
        self.groupByCheckboxes['Date'].setChecked(True)
        self.groupByCheckboxes['Block'].setChecked(True)

        # Filter creation
        for checkbox in self.groupByCheckboxes:
            self.groupByCheckboxes[checkbox].stateChanged.connect(self.recalculate)

        self.setWindowTitle(str("Performance for {}".format(bird_name)))
        self.log = logging.getLogger(__name__)
        self.dataGroups = []
        self.filters = []
        self.create_field_list()
        self.create_filter_objects()

        self.build_field_checkboxes()
        self.group_by()

        self.get_raw_data()

        self.field_preset_select('nr')
        self.recalculate()

    def select_bird(self):
        # select new data_folder(s)

        dialog = FolderSelect()
        return_code = dialog.exec_()
        if return_code:
            output_path = dialog.checkedPaths

            if output_path:
                self.data_folder = output_path

                # refresh data
                self.get_raw_data()

                self.field_preset_select('nr')
                self.recalculate()

    # region Field selection

    def create_field_list(self):
        # Create dictionary of fields, then create checkboxes for all fields for the "Select Columns" pane

        self.fieldManagement = collections.OrderedDict()
        allColumns = analysis.field_list()
        for column in allColumns:
            # column = column.decode('utf-8')
            self.fieldManagement[column] = {}
            self.fieldManagement[column]['visible'] = True
            self.fieldManagement[column]['filter'] = {}

            self.fieldManagement[column]['name'] = column.replace('\n(NR)', ' (NR)')
            columnSafe = self.fieldManagement[column]['name']
            if columnSafe in ['Subject', 'Block', 'Response Type', 'Stimulus', 'Class', 'Response']:
                self.fieldManagement[column]['filter']['type'] = 'list'
            elif columnSafe in ['Date']:
                self.fieldManagement[column]['filter']['type'] = 'range'
            else:
                self.fieldManagement[column]['filter']['type'] = 'None'

            # give each field a type to indicate what functions can be performed
            if columnSafe in ['File', 'Session', 'File Count', 'Index', 'Time']:
                self.fieldManagement[column]['type'] = 'raw'
            elif columnSafe in ['Subject', 'Block', 'Date', 'Response Type', 'Stimulus', 'Class', 'Response']:
                self.fieldManagement[column]['type'] = 'index'  # groupby enabled
            elif columnSafe == 'RT':
                self.fieldManagement[column]['type'] = 'math'
            elif columnSafe in ['Reward', 'Punish', 'Hit', 'FA', 'Miss', 'CR', 'Miss (NR)', 'CR (NR)',
                                'Probe Hit', 'Probe FA', 'Probe Miss', 'Probe CR', 'Probe Miss (NR)',
                                'Probe CR (NR)']:
                self.fieldManagement[column]['type'] = 'sum'
            elif columnSafe in ["d'", "d' (NR)", 'Beta', 'Beta (NR)', 'S+', 'S+ (NR)',
                                'S-', 'S- (NR)', 'Total Corr', 'Total Corr (NR)', 'Trials',
                                "Probe d'", "Probe d' (NR)", 'Probe Beta', 'Probe Beta (NR)',
                                'Probe S+', 'Probe S+ (NR)', 'Probe S-', 'Probe S- (NR)',
                                'Probe Tot Corr', 'Probe Tot Corr (NR)', 'Probe Trials']:
                self.fieldManagement[column]['type'] = 'group'

    def build_field_checkboxes(self):
        # build checkbox items for every field from fieldManangement dict
        for key in self.fieldManagement:

            columnName = self.fieldManagement[key]['name']

            item = QtGui.QCheckBox()
            item.setMinimumSize(QtCore.QSize(27, 27))
            item.setMaximumSize(QtCore.QSize(300, 27))
            item.setText(columnName)
            item.setTristate(False)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.fieldManagement[key]['itemWidget'] = item

            self.fieldList.addWidget(self.fieldManagement[key]['itemWidget'])
            self.fieldManagement[key]['itemWidget'].stateChanged.connect(self.recalculate)

    # region Functions
    def silent_checkbox_change(self, checkbox, newstate=False):
        checkbox.blockSignals(True)
        if newstate:
            checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            checkbox.setCheckState(QtCore.Qt.Unchecked)
        checkbox.blockSignals(False)

    def recheck_fields(self):
        # Make sure all displayed fields are checked in Select Column pane
        existingHeaders = []  # Get list of headers, since they can't be pulled out of model as list (AFAIK)
        for j in xrange(self.model.columnCount()):  # for all fields available in model
            columnName = unicode(self.model.headerData(j, QtCore.Qt.Horizontal).toString()).replace('\n(NR)', ' (NR)')
            self.silent_checkbox_change(self.fieldManagement[columnName]['itemWidget'], True)
            existingHeaders.append(columnName)

        # Mark remaining fields as not visible
        # remainingHeaders = list(filter(lambda a: a not in analysis.field_list(), existingHeaders))
        for columnName in self.fieldManagement:
            if columnName in existingHeaders:
                self.fieldManagement[columnName]['visible'] = True
            else:
                self.fieldManagement[columnName]['visible'] = False

    def field_preset_select(self, pattern=None):
        for columnName in self.fieldManagement:
            if pattern == 'all':
                self.silent_checkbox_change(self.fieldManagement[columnName]['itemWidget'], True)

            elif pattern == 'none':
                self.silent_checkbox_change(self.fieldManagement[columnName]['itemWidget'], False)

            else:
                # fieldName = unicode(self.fieldList.item(x).text())
                columnNameF = self.fieldManagement[columnName]['name']
                if pattern == 'nr':
                    self.silent_checkbox_change(self.fieldManagement['Trials']['itemWidget'], True)
                checkstate = self.noResponse_Checkbox.isChecked()
                if columnNameF in ["d'", 'Beta', 'S+', 'S-', 'Total Corr', "Probe d'", 'Probe Beta', 'Probe S+',
                                   'Probe S-', 'Probe Tot Corr']:
                    self.silent_checkbox_change(self.fieldManagement[columnName]['itemWidget'], not checkstate)

                    # self.fieldManagement[columnName]['itemWidget'].setCheckState(not checkstate)
                elif columnNameF in ["d' (NR)", 'Beta (NR)', 'S+ (NR)', 'S- (NR)', 'Total Corr (NR)',
                                     "Probe d' (NR)", 'Probe Beta (NR)', 'Probe S+ (NR)', 'Probe S- (NR)',
                                     'Probe Tot Corr (NR)']:
                    self.silent_checkbox_change(self.fieldManagement[columnName]['itemWidget'], checkstate)

                    # self.fieldManagement[columnName]['itemWidget'].setCheckState(checkstate)

                # elif pattern == 'probe':
                checkstate = self.probe_Checkbox.isChecked()
                if columnNameF in ["Probe d'", "Probe d' (NR)", 'Probe Beta', 'Probe Beta (NR)', 'Probe Trials',
                                   'Probe Hit', 'Probe Miss', 'Probe Miss (NR)', 'Probe FA', 'Probe CR',
                                   'Probe CR (NR)', 'Probe S+', 'Probe S+ (NR)', 'Probe S-', 'Probe S- (NR)',
                                   'Probe Tot Corr', 'Probe Tot Corr (NR)']:
                    self.silent_checkbox_change(self.fieldManagement[columnName]['itemWidget'], checkstate)
                    # self.fieldManagement[columnName]['itemWidget'].setCheckState(checkstate)

                # elif pattern == 'raw':
                checkstate = self.raw_Checkbox.isChecked()
                if columnNameF in ['Hit', 'Miss', 'Miss (NR)', 'FA', 'CR', 'CR (NR)', 'Probe Hit', 'Probe Miss',
                                   'Probe Miss (NR)', 'Probe FA', 'Probe CR', 'Probe CR (NR)']:
                    self.silent_checkbox_change(self.fieldManagement[columnName]['itemWidget'], checkstate)
                    # self.fieldManagement[columnName]['itemWidget'].setCheckState(checkstate)

        self.recalculate()

    # endregion
    # endregion

    # region Field grouping

    def create_grouping_checkbox(self, group_name):
        sizePolicy_fixed = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy_fixed.setHorizontalStretch(0)
        sizePolicy_fixed.setVerticalStretch(0)
        self.groupByCheckboxes[group_name] = QtGui.QCheckBox(self)
        self.groupByCheckboxes[group_name].setSizePolicy(sizePolicy_fixed)
        self.groupByCheckboxes[group_name].setMaximumSize(QtCore.QSize(27, 27))
        self.groupByCheckboxes[group_name].setObjectName(_from_utf8("groupBy{}_Checkbox".format(group_name)))
        self.groupGrid.addRow(QtGui.QLabel(group_name), self.groupByCheckboxes[group_name])

    def group_by(self):
        # construct groupby parameter for pd.groupby - there may be a better way to do this:
        # Currently rebuilds the self.dataGroups var each time a box is checked or unchecked, which requires adding a
        # new checkbox for each column that could be grouped
        self.dataGroups = []
        for checkbox in self.groupByCheckboxes:
            if self.groupByCheckboxes[checkbox].isChecked():
                self.dataGroups.append(checkbox)

        # enable/disable raw field checkboxes depending on group state
        for field in (rawFields for rawFields in self.fieldManagement
                      if self.fieldManagement[rawFields]['type'] == 'raw'):
            if len(self.dataGroups) > 0:
                self.fieldManagement[field]['itemWidget'].setEnabled(False)
            else:
                self.fieldManagement[field]['itemWidget'].setEnabled(True)

        # enable/disable raw field checkboxes depending on group state
        for field in (rawFields for rawFields in self.fieldManagement if self.fieldManagement[rawFields][
                                                                             'type'] == 'group'):
            if len(self.dataGroups) > 0:
                self.fieldManagement[field]['itemWidget'].setEnabled(True)
            else:
                self.fieldManagement[field]['itemWidget'].setEnabled(False)
        # self.recalculate()

    # endregion

    # region Filters

    def create_filter_objects(self):
        # add field info to filter

        for columnName in self.fieldManagement:
            if self.fieldManagement[columnName]['filter']['type'] == 'list':
                # create widget for both select all/none and field list
                parentGroupBox = QtGui.QGroupBox()

                # Stylesheet so the groupbox can have a border without giving borders to all child components
                parentGroupBox.setStyleSheet(
                    'QGroupBox {border: 1px solid gray;margin-top: 0.5em} ' +
                    'QGroupBox::title {subcontrol-origin: margin; left: 3px; padding: 0 3px 0 3px;}')

                parentGroupBox.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,
                                                               QtGui.QSizePolicy.MinimumExpanding))
                parentGroupBox.setMaximumHeight(180)
                parentGroupBox.setContentsMargins(3, 3, 3, 3)
                # Set title of groupbox
                parentGroupBox.setTitle(columnName)
                self.fieldManagement[columnName]['filter']['widget'] = parentGroupBox
                # Add sublayout for both all/none buttons and value list
                layout = QtGui.QVBoxLayout()
                layout.setSpacing(0)
                # Add widget for value list (that gets filled later)
                scrollArea = QtGui.QScrollArea()
                scrollArea.setMinimumHeight(40)
                scrollArea.setMaximumHeight(150)
                # scrollArea.setWidgetResizable(True)
                scrollArea.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                                           QtGui.QSizePolicy.MinimumExpanding))
                scrollArea.setContentsMargins(0, 0, 0, 0)
                self.fieldManagement[columnName]['filter']['CheckBoxList'] = scrollArea
                # Add widget for select all/none
                self.fieldManagement[columnName]['filter']['selectAllNoneMenu'] = QtGui.QWidget()
                selectLayout = QtGui.QHBoxLayout()
                actionAll = QtGui.QPushButton("Select All", self)
                actionAll.clicked.connect(lambda _, b=columnName: self.apply_filter(
                    column_name=b, filter_value='all'))
                actionNone = QtGui.QPushButton("Select None", self)
                actionNone.clicked.connect(lambda _, b=columnName: self.apply_filter(
                    column_name=b, filter_value='none'))
                selectLayout.addWidget(actionAll)
                selectLayout.addWidget(actionNone)

                self.fieldManagement[columnName]['filter']['selectAllNoneMenu'].setLayout(selectLayout)
                layout.addWidget(self.fieldManagement[columnName]['filter']['selectAllNoneMenu'])
                layout.addWidget(self.fieldManagement[columnName]['filter']['CheckBoxList'])
                self.fieldManagement[columnName]['filter']['widget'].setLayout(layout)
                # self.fieldManagement[columnName]['filter']['CheckBoxList'].addSeparator()

                self.filterGrid.addWidget(self.fieldManagement[columnName]['filter']['widget'])
            elif self.fieldManagement[columnName]['filter']['type'] == 'range':
                # create widget for both select all/none and field list
                parentGroupBox = QtGui.QGroupBox()

                # Stylesheet so the groupbox can have a border without giving borders to all child components
                parentGroupBox.setStyleSheet(
                    'QGroupBox {border: 1px solid gray;margin-top: 0.5em} ' +
                    'QGroupBox::title {subcontrol-origin: margin; left: 3px; padding: 0 3px 0 3px;}')

                parentGroupBox.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,
                                                               QtGui.QSizePolicy.MinimumExpanding))
                parentGroupBox.setMaximumHeight(180)
                parentGroupBox.setContentsMargins(3, 3, 3, 3)
                # Set title of groupbox
                parentGroupBox.setTitle(columnName)
                self.fieldManagement[columnName]['filter']['widget'] = parentGroupBox
                # Add sublayout for both all/none buttons and value list
                layout = QtGui.QHBoxLayout()
                # layout.setSpacing(0)

                # Widget for equality selection
                compareBox = QtGui.QComboBox()
                compareBox.addItems(['<', '<=', '>', '>=', '==', '!='])
                compareBox.setMaximumWidth(50)
                compareBox.currentIndexChanged.connect(self.apply_filter)

                # Add widget for date
                dateBox = QtGui.QDateEdit()
                dateBox.setCalendarPopup(True)
                dateBox.setDate(QtCore.QDate.currentDate())
                dateBox.setDisplayFormat('yyyy/MM/dd')
                dateBox.dateChanged.connect(self.apply_filter)

                layout.addWidget(compareBox)
                layout.addWidget(dateBox)

                self.fieldManagement[columnName]['filter']['widget'].setLayout(layout)
                # self.fieldManagement[columnName]['filter']['CheckBoxList'].addSeparator()

                self.filterGrid.addWidget(self.fieldManagement[columnName]['filter']['widget'])

    def build_filter_value_lists(self):
        # For each displayed field, create a value list of unique values from the extant data
        # Get values from model rather than table because table might be filtered and we want to see all available
        # fields
        for column in xrange(self.model.columnCount()):
            columnName = unicode(self.model.headerData(column, QtCore.Qt.Horizontal).toString()).replace('\n(NR)',
                                                                                                         ' (NR)')
            if self.fieldManagement[columnName]['filter']['type'] == 'list':
                valueList = []
                for row in xrange(self.model.rowCount()):
                    valueIndex = self.model.index(row, column)
                    valueList.append(str(self.model.data(valueIndex).toString()))
                valueList = list(set(valueList))
                if 'valueList' in self.fieldManagement[columnName]:
                    valueList = valueList + self.fieldManagement[columnName]['valueList']
                self.fieldManagement[columnName]['valueList'] = list(set(valueList))

    def refresh_filters(self):
        for columnName in self.fieldManagement:
            if self.fieldManagement[columnName]['visible']:  # only if column is actually present
                if self.fieldManagement[columnName]['filter']['type'] == 'list':
                    # Signal mapper for all of the values, so each one
                    # self.fieldManagement[columnName]['filter']['signalMapper'] = QtCore.QSignalMapper(self)

                    valueWidget = QtGui.QWidget()
                    valueWidget.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,
                                                                QtGui.QSizePolicy.MinimumExpanding))

                    valueLayout = QtGui.QVBoxLayout()
                    valueLayout.setSpacing(2)
                    valueLayout.setContentsMargins(0, 3, 0, 3)
                    # valueLayout.addStretch()

                    for valueNumber, valueName in enumerate(sorted(self.fieldManagement[columnName]['valueList'])):
                        action = QtGui.QCheckBox(valueName)

                        if len(self.filters) == 0:
                            action.setCheckState(QtCore.Qt.Checked)
                        elif columnName in self.filters and valueName in self.filters[columnName]:
                            action.setCheckState(QtCore.Qt.Checked)
                        action.setMaximumHeight(27)
                        action.stateChanged.connect(lambda _, b=valueName: self.apply_filter(filter_value=b))
                        # self.fieldManagement[columnName]['filter']['signalMapper'].setMapping(action, valueName)
                        # action.stateChanged.connect(self.fieldManagement[columnName]['filter']['signalMapper'].map)
                        valueLayout.addWidget(action)

                    # self.fieldManagement[columnName]['filter']['signalMapper'].mapped.connect(self.apply_filter)
                    # self.fieldManagement[columnName]['filter']['widget'] = QtGui.QWidget()

                    valueWidget.setLayout(valueLayout)
                    # Delete existing layout in CheckBoxList

                    oldLayout = self.fieldManagement[columnName]['filter']['CheckBoxList'].widget()

                    if oldLayout is not None:
                        oldLayout.deleteLater()

                    self.fieldManagement[columnName]['filter']['CheckBoxList'].setWidget(valueWidget)

                    # remove old valueLayout from widget
                    mainChildren = self.fieldManagement[columnName]['filter']['widget'].children()

                    mainChildren[2].setParent(None)
                    self.fieldManagement[columnName]['filter']['widget'].layout().addWidget(
                        self.fieldManagement[columnName]['filter']['CheckBoxList']
                    )

                    self.fieldManagement[columnName]['filter']['widget'].setVisible(True)

                # elif self.fieldManagement[columnName]['filter']['type'] == 'range':
                #     # for date or time field:
                #
                #     pass
            else:
                if self.fieldManagement[columnName]['filter']['type'] is not 'none':
                    if 'widget' in self.fieldManagement[columnName]['filter']:
                        # Hide filter
                        self.fieldManagement[columnName]['filter']['widget'].setVisible(False)

    def apply_filter(self, column_name=None, filter_value=None):
        # Clear existing filter, if any
        # if len(self.currentFilter) > 0:
        #     self.currentFilter

        filterData = {}
        # build new filter
        for columnName in self.fieldManagement:
            comparison = ''
            selectedDate = ''
            if self.fieldManagement[columnName]['visible']:  # only if column is actually present
                if self.fieldManagement[columnName]['filter']['type'] == 'list':

                    filterData[columnName] = []
                    # Get individual values
                    valueWidget = self.fieldManagement[columnName]['filter']['CheckBoxList'].widget().children()
                    for child in valueWidget:
                        if type(child).__name__ == 'QCheckBox':
                            if filter_value == 'all' and column_name == columnName:
                                child.blockSignals(True)
                                child.setCheckState(QtCore.Qt.Checked)
                                child.blockSignals(False)

                            elif filter_value == 'none' and column_name == columnName:
                                child.blockSignals(True)
                                child.setCheckState(QtCore.Qt.Unchecked)
                                child.blockSignals(False)

                            if child.isChecked():
                                filterData[columnName].append(str(child.text()))
                elif self.fieldManagement[columnName]['filter']['type'] == 'range':
                    # range passes two parameters, an equality and a value
                    filterData[columnName] = []
                    # Get individual values
                    valueWidget = self.fieldManagement[columnName]['filter']['widget'].children()
                    for child in valueWidget:
                        if type(child).__name__ == 'QComboBox':
                            comparison = child.currentText()
                        elif type(child).__name__ == 'QDateEdit':
                            selectedDate = child.date()
                    filterData[columnName].append(str(comparison))
                    filterData[columnName].append(selectedDate.toPyDate())
        self.filters = filterData
        self.recalculate()

    # endregion

    # region Analysis methods

    def get_raw_data(self):
        perform = analysis.Performance(self.data_folder)
        self.rawTrialData = perform.raw_trial_data
        return perform

    def recalculate(self):
        dropCols = []
        for x in self.fieldManagement:
            if not self.fieldManagement[x]['itemWidget'].checkState():
                dropCols.append(x)
        # dropCols = [col.replace(' (NR)', '\n(NR)') for col in dropCols]
        self.group_by()
        perform = analysis.Performance(self.data_folder)
        perform.filter_data(filters=self.filters)
        perform.summarize('filt')
        self.outputData = perform.analyze(perform.summaryData, groupBy=self.dataGroups, dropCols=dropCols)

        outputFile = 'performanceSummary.csv'
        if isinstance(self.data_folder, list):
            output_path = os.path.join(self.data_folder[0], outputFile)
        else:
            output_path = os.path.join(self.data_folder, outputFile)
        self.outputData.to_csv(str(output_path), encoding='utf-8')
        self.refresh_table(output_path)

    # endregion

    # region Data manipulation

    def export(self, output_folder):
        output_path = QtGui.QFileDialog.getSaveFileName(self, "Save As...", output_folder, "CSV Files (*.csv)")
        if output_path:
            self.outputData.to_csv(str(output_path))
            print 'saved to {}'.format(output_path)

    def refresh_table(self, output_path):
        # Refresh the data table with new values
        # reimport the data from csv because moving directly from dataframe is a pain and doesn't support multiple
        # headers
        self.model = QtGui.QStandardItemModel(self)

        with open(output_path, 'rb') as inputFile:
            i = 1
            for row in csv.reader(inputFile):
                if i == 1:  # set headers of table
                    for column in range(len(row)):
                        # reencode each item in header list as utf-8 so beta can be displayed properly
                        row[column] = row[column].decode('utf-8')
                        row[column] = row[column].replace(' (NR)', '\n(NR)')

                    self.model.setHorizontalHeaderLabels(row)

                else:  # set items in rows of table
                    items = [QtGui.QStandardItem(field) for field in row]
                    self.model.appendRow(items)
                i += 1

        self.proxyModel = QtGui.QSortFilterProxyModel()
        self.proxyModel.setSourceModel(self.model)
        # # get column
        # self.modelColumns = []
        # for j in xrange(self.proxyModel.columnCount()):  # for all fields available in model
        #     self.modelColumns.append(unicode(self.model.headerData(j, QtCore.Qt.Horizontal).toString()))
        self.performance_Table.setModel(self.proxyModel)  # apply constructed model to tableview object
        self.performance_Table.setSortingEnabled(True)

        self.recheck_fields()
        self.build_filter_value_lists()
        self.refresh_filters()

        self.performance_Table.resizeColumnsToContents()

    def eventFilter(self, source, event):
        # Reimplementation of eventFilter, this one to capture ctrl+C to copy data from table
        # https://stackoverflow.com/questions/40469607

        if (event.type() == QtCore.QEvent.KeyPress and
                event.matches(QtGui.QKeySequence.Copy)):
            self.copy_table_selection()
            return True
        return super(self.__class__, self).eventFilter(source, event)

    def copy_table_selection(self):
        # actual copy method for copying cells from tableview

        selection = self.performance_Table.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            rowcount = rows[-1] - rows[0] + 1
            colcount = columns[-1] - columns[0] + 1
            table = [[''] * colcount for _ in range(rowcount)]
            for index in selection:
                row = index.row() - rows[0]
                column = index.column() - columns[0]
                table[row][column] = index.data().toString()
            stream = io.BytesIO()
            csv.writer(stream, delimiter='\t').writerows(table)
            QtGui.qApp.clipboard().setText(stream.getvalue())

    # endregion


class CheckableDirModel(QtGui.QFileSystemModel):
    def __init__(self, parent=None):
        QtGui.QFileSystemModel.__init__(self, None)
        self.checks = {}

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.CheckStateRole:
            return QtGui.QFileSystemModel.data(self, index, role)
        else:
            if index.column() == 0:
                return self.checkbox_state(index)

    def flags(self, index):
        return QtGui.QFileSystemModel.flags(self, index) | QtCore.Qt.ItemIsUserCheckable

    def checkbox_state(self, index):
        if index in self.checks:
            return self.checks[index]
        else:
            return QtCore.Qt.Unchecked

    def setData(self, index, value, role):
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            self.checks[index] = value
            self.emit(QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index)
            return True
        return QtGui.QFileSystemModel.setData(self, index, value, role)

    def export_checked(self):
        selection = []
        for c in self.checks.keys():
            if self.checks[c] == QtCore.Qt.Checked:
                try:

                    selection.append(str(self.filePath(c).toUtf8()))
                except:
                    pass
        return selection


class FolderSelect(QtGui.QDialog, pyoperant_gui_layout.FolderSelectWindow):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setup_ui(self)  # This is defined in pyoperant_gui_layout.py file

        self.data_folder = '/home/rouse/bird/data'

        self.model = CheckableDirModel()
        self.model.setRootPath(self.data_folder)
        # folders only
        self.model.setFilter(QtCore.QDir.Dirs | QtCore.QDir.NoDotAndDotDot)

        self.folder_view.setModel(self.model)
        self.folder_view.setRootIndex(self.model.index(self.data_folder))
        self.folder_view.hideColumn(1)
        self.folder_view.hideColumn(2)
        self.folder_view.hideColumn(3)

        self.done_button.clicked.connect(self.select)
        self.cancel_button.clicked.connect(self.cancel)
        self.change_folder_button.clicked.connect(self.change_folder)

    def cancel(self):
        self.close()

    def select(self):
        self.checkedPaths = self.model.export_checked()
        self.accept()

    def change_folder(self):
        newPath = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory", self.data_folder)
        if newPath:
            self.data_folder = newPath
            self.model.setRootPath(self.data_folder)
            self.folder_view.setModel(self.model)
            self.folder_view.setRootIndex(self.model.index(self.data_folder))


def main():
    app = QtGui.QApplication(sys.argv)  # A new instance of QApplication

    form = PyoperantGui()  # We set the form to be our ExampleApp (design)
    form.show()  # Show the form
    sys.exit(app.exec_())  # and execute the app


if __name__ == '__main__':  # if we're running file directly and not importing it
    main()  # run the main function

# subprocessBox is a variable that tracks the subprocess ID of a subprocess. In this case specifically, it tracks the
# pyoperant subprocess. It is set to 0 when the subprocess has been stopped and should not be running (i.e. if user
# clicked "stop box" or pyoperant crashed, which was caught by the GUI.
# Alternatively it gets set to 1 if the box should be set to 'sleep' mode, meaning pyoperant should be stopped
# temporarily and restarted in the morning. This was added to help combat the intermittent and unexplained instances
# of Teensys ceasing to respond to computer input
