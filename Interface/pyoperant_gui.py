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
import logging
import datetime as dt  # For auto sleep

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

    def __init__(self):

        super(self.__class__, self).__init__()
        self.setup_ui(self)  # Sets up layout and widgets that are defined

        self.debug = False

        # Number of boxes declared in pyoperant_gui_layout.py

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refreshall)
        self.timer.start(5000)

        self.log_config()

        # Monitor when USB devices are connected/disconnected
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='tty')
        observer = pyudev.MonitorObserver(monitor, self.usb_monitor, name='usb-observer')
        observer.daemon = True
        observer.start()

        self.teensy_emit.connect(
            (lambda triggered_boxnumber, parameter: self.teensy_control(triggered_boxnumber, parameter)))

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
        self.experimentPath = ""

        # Option var init
        self.optionMenuList = []
        self.solenoidMenuList = []
        self.primeActionList = []
        self.purgeActionList = []
        self.solenoidManualList = []
        self.jsonMenuList = []
        self.openFolderActionList = []
        self.openSettingsActionList = []
        self.createNewJsonList = []
        self.newBirdActionList = []
        self.statsActionList = []
        self.useNRList = []
        self.autoSleepList = []

        self.sleepScheduleList = []  # schedule is none if box not active, set when box started
        self.defaultSleepSchedule = [["08:30", "22:30"]]

        # region Option menu setup
        ## To add an item to the option menu:
        # - Add a blank list var to the "option var init" section for the action to be stored for each box
        # - Figure out whether the new option should be in the main option menu or in a submenu
        # - in the "Option Menu Setup" section, add two lines:
        #       self.{list var}.append(QtGui.QAction({action name as str}, self)   # or QtGui.QMenu({menu name as str})
        #       self.{parent menu}[boxnumber].addAction(self.{list var}[boxnumber])  # or addMenu
        # - If adding an action, go to the "Connect functions to buttons/objects" section and add a line to connect
        # the actual QAction object with the function for each box:
        #       self.{list var}[boxNumber].triggered.connect(lambda _, b=i: self.{function}(boxnumber=b, {other vars}))

        for boxnumber in self.boxList:
            # Create necessary objects for each box
            self.optionMenuList.append(QtGui.QMenu())
            self.solenoidMenuList.append(QtGui.QMenu("Water Control"))
            self.primeActionList.append(QtGui.QAction("Prime (5s)", self))
            self.purgeActionList.append(QtGui.QAction("Purge (20s)", self))
            self.solenoidManualList.append(QtGui.QAction("Manual Control", self))
            self.jsonMenuList.append(QtGui.QMenu("JSON File"))
            self.openFolderActionList.append(QtGui.QAction("Open data folder", self))
            self.openSettingsActionList.append(QtGui.QAction("Edit", self))
            self.createNewJsonList.append(QtGui.QAction("New from template", self))
            self.newBirdActionList.append(QtGui.QAction("Change bird", self))
            self.statsActionList.append(QtGui.QAction("Performance", self))
            self.useNRList.append(QtGui.QAction("Use NR Trials", self))
            self.useNRList[boxnumber].setCheckable(True)
            self.autoSleepList.append(QtGui.QAction("Autosleep", self))
            self.autoSleepList[boxnumber].setCheckable(True)
            self.autoSleepList[boxnumber].setChecked(True)

            # Reorder to change order in menu
            self.optionMenuList[boxnumber].addMenu(self.solenoidMenuList[boxnumber])
            self.optionMenuList[boxnumber].addSeparator()
            self.optionMenuList[boxnumber].addMenu(self.jsonMenuList[boxnumber])
            self.optionMenuList[boxnumber].addSeparator()
            self.optionMenuList[boxnumber].addAction(self.openFolderActionList[boxnumber])
            self.optionMenuList[boxnumber].addAction(self.newBirdActionList[boxnumber])
            self.optionMenuList[boxnumber].addSeparator()
            self.optionMenuList[boxnumber].addAction(self.useNRList[boxnumber])
            self.optionMenuList[boxnumber].addSeparator()
            self.optionMenuList[boxnumber].addAction(self.autoSleepList[boxnumber])

            # JSON submenu
            self.jsonMenuList[boxnumber].addAction(self.openSettingsActionList[boxnumber])
            self.jsonMenuList[boxnumber].addAction(self.createNewJsonList[boxnumber])

            # Solenoid submenu
            self.solenoidMenuList[boxnumber].addAction(self.primeActionList[boxnumber])
            self.solenoidMenuList[boxnumber].addAction(self.purgeActionList[boxnumber])
            self.solenoidMenuList[boxnumber].addAction(self.solenoidManualList[boxnumber])
        # endregion

        # region Other box-specific var setup
        for boxnumber in self.boxList:
            # Fill sleep schedule var with None to start, and fill later when box is started
            self.sleepScheduleList.append(None)

            # Queue for running subprocesses and pulling outputs without blocking main script
            self.qList[boxnumber] = Queue.Queue()

            ## The following lines are only if we want to implement the ability for a running pyoperant subprocess to
            #  accept external input from the GUI

            # self.qReadList[boxnumber] = Queue.Queue()  # Queue for running log-read subprocesses without blocking
            # # main script
            #
            # self.tReadList[boxnumber] = threading.Thread(target=self.read_output_box,
            #                                             args=(self.logProcessBox[boxnumber].stdout,
            #                                                   self.qReadList[boxnumber]))
            # self.tReadList[boxnumber].daemon = True
        # endregion

        # region Connect functions to buttons/objects
        for boxnumber in self.boxList:
            self.paramFileButtonBoxList[boxnumber].clicked.connect(
                lambda _, b=boxnumber: self.param_file_select(boxnumber=b))
            self.performanceBoxList[boxnumber].clicked.connect(
                lambda _, b=boxnumber: self.analyze_performance(boxnumber=b))
            self.startBoxList[boxnumber].clicked.connect(lambda _, b=boxnumber: self.start_box(boxnumber=b))
            self.stopBoxList[boxnumber].clicked.connect(lambda _, b=boxnumber: self.stop_box(boxnumber=b))

            # Option menu
            self.purgeActionList[boxnumber].triggered.connect(
                lambda _, b=boxnumber: self.water_control(boxnumber=b, parameter='purge', purge_time=20))
            self.primeActionList[boxnumber].triggered.connect(
                lambda _, b=boxnumber: self.water_control(boxnumber=b, parameter='purge', purge_time=5))
            self.solenoidManualList[boxnumber].triggered.connect(
                lambda _, b=boxnumber: self.water_control(boxnumber=b, parameter='dialog'))
            self.openFolderActionList[boxnumber].triggered.connect(
                lambda _, b=boxnumber: self.open_box_folder(boxnumber=b))
            self.openSettingsActionList[boxnumber].triggered.connect(
                lambda _, b=boxnumber: self.open_json_file(boxnumber=b))
            self.createNewJsonList[boxnumber].triggered.connect(
                lambda _, b=boxnumber: self.create_json_file(boxnumber=b))
            self.newBirdActionList[boxnumber].triggered.connect(
                lambda _, b=boxnumber: self.create_new_bird(boxnumber=b))
            self.useNRList[boxnumber].triggered.connect(
                lambda _, b=boxnumber: self.use_nr_trials(boxnumber=b))
            self.autoSleepList[boxnumber].triggered.connect(
                lambda _, b=boxnumber: self.auto_sleep_set(boxnumber=b))

            # Attach menu to physical option button
            self.optionButtonBoxList[boxnumber].setMenu(self.optionMenuList[boxnumber])
        # endregion

        self.closeEvent = self.close_application

        for boxnumber in self.boxList:
            actualboxnumber = boxnumber + 1
            if not os.path.exists("/dev/teensy{:02d}".format(actualboxnumber)):  # check if Teensy is detected:
                self.box_button_control(boxnumber, 'disable')
            # else:
            #     self.log.error("Error: Teensy {:02d} not detected.".format(actualboxnumber))

        self.open_application()

    # region GUI button/object handling
    def param_file_select(self, boxnumber):

        existingFile = self.paramFileBoxList[boxnumber].toPlainText()
        if os.path.isfile(existingFile):  # If param file is already specified, start in that folder
            existingPathFile = os.path.split(str(existingFile))
            currentPath = existingPathFile[0]
        else:  # Otherwise just start in working directory
            currentPath = os.path.dirname(os.path.realpath(__file__))
        paramFile = QtGui.QFileDialog.getOpenFileName(self, "Select Preferences File", currentPath,
                                                      "JSON Files (*.json)")
        # execute getOpenFileName dialog and set the directory variable to be equal to the user selected directory

        if paramFile:  # if user didn't pick a file don't replace existing path

            self.paramFileBoxList[boxnumber].setPlainText(paramFile)  # add file to the listWidget

    def box_button_control(self, boxnumber, parameter):
        if parameter == 'stop' or parameter == 'enable':
            # Enable objects when box is not running
            self.paramFileButtonBoxList[boxnumber].setEnabled(True)
            self.birdEntryBoxList[boxnumber].setReadOnly(False)
            self.startBoxList[boxnumber].setEnabled(True)
            self.stopBoxList[boxnumber].setEnabled(False)
            # self.graphicBoxList[boxnumber].setPixmap(self.redIcon)
            self.log.debug("Setting status icon to 'stop'")
            self.status_icon(boxnumber, 'stop')

        elif parameter == "start":
            # Hide and/or disable objects while box is running
            self.paramFileButtonBoxList[boxnumber].setEnabled(False)
            self.birdEntryBoxList[boxnumber].setReadOnly(True)
            self.startBoxList[boxnumber].setEnabled(False)
            self.stopBoxList[boxnumber].setEnabled(True)
            # self.graphicBoxList[boxnumber].setPixmap(self.greenIcon)
            self.log.debug("Setting status icon to 'start'")
            self.status_icon(boxnumber, 'start')

        elif parameter == "disable":
            # For when Teensy isn't connected
            self.paramFileButtonBoxList[boxnumber].setEnabled(True)
            self.birdEntryBoxList[boxnumber].setReadOnly(False)
            self.startBoxList[boxnumber].setEnabled(False)
            self.stopBoxList[boxnumber].setEnabled(False)
            # self.graphicBoxList[boxnumber].setPixmap(self.emptyIcon)
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

    def open_json_file(self, boxnumber):
        jsonPath = str(self.paramFileBoxList[boxnumber].toPlainText())
        if os.path.exists(jsonPath):
            subprocess.Popen(["geany", jsonPath])
        else:
            msg = QtGui.QMessageBox()
            msg.setIcon(2)
            msg.setText('Warning: File not found')
            msg.setStandardButtons(QtGui.QMessageBox.Ok)
            msg.exec_()
            self.log.error('Warning: Settings file not found: ({})'.format(jsonPath))

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
        else:
            self.subprocessBox[boxnumber] = 0
            self.sleepScheduleList[boxnumber] = None

        self.box_button_control(boxnumber, 'stop')
        self.refreshfile(boxnumber)  # one last time to display any errors sent to the summaryDAT file

        # set icon
        if error_mode:
            self.log.debug("Setting status icon to 'error'")
            self.status_icon(boxnumber, 'error')
        elif sleep_mode:
            self.log.debug("Setting status icon to 'sleep'")
            self.status_icon(boxnumber, 'sleep')
        else:
            self.log.debug("Setting status icon to 'stop'")
            self.status_icon(boxnumber, 'stop')

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

                self.tList[boxnumber] = threading.Thread(target=self.read_output_box,
                                                         args=(boxnumber, self.subprocessBox[boxnumber].stderr,
                                                               self.qList[boxnumber]))
                self.tList[boxnumber].daemon = True

                self.tList[boxnumber].start()

                # while True:  # Loop through error codes generated, if any
                #    error = ""
                #    try:
                #        error = '{0}\n{1}'.format(error, self.qList[boxnumber].get(False))
                #    except Queue.Empty:
                #        break

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
        if action == 'add':
            # print 'Connected'
            self.log.debug('USB device connected')
            deviceString = device.device_links.next()
            self.check_teensy(deviceString, True)
        elif action == 'remove':
            # print 'Removed'
            self.log.debug('USB device disconnected')
            deviceString = device.device_links.next()
            self.check_teensy(deviceString, False)

    def check_teensy(self, device_path, connect=False):
        # device_path is result from device_paths of device that was connected/disconnected
        # It needs to be parsed to get the actual box number
        if device_path[0:4] == '/dev':  # Only pass if device path is valid
            devicePathSplit = os.path.split(device_path)
            try:
                boxLink = devicePathSplit[1]
                # print boxLink
                # self.log.info(boxLink)
                match = re.split('Board(\\d*)', boxLink)
                boxnumber = int(
                    match[1]) - 1  # Box number as index is indexed from 0, but Teensy numbers are indexed from 1
                # print boxnumber
                # self.log.info(boxnumber)
            except IndexError:
                boxnumber = None
                print 'Error: board not recognized'
                self.log.error('Error: board not recognized')

            if boxnumber is not None:
                if connect:
                    # self.box_button_control(boxnumber, 'enable')
                    parameter = 'enable'
                else:
                    # self.box_button_control(boxnumber, 'disable')
                    parameter = 'disable'
                self.log.debug("Teensy {:02d} recognized, status set to {}".format(boxnumber, parameter))
                self.teensy_emit.emit(boxnumber, parameter)
            else:
                pass

    def teensy_control(self, boxnumber, parameter):
        # quick method to enable or disable gui buttons and stop pyoperant if teensy is disconnected
        self.stop_box(boxnumber)
        self.box_button_control(boxnumber, parameter)

    # endregion

    # region Water system functions
    def water_control(self, boxnumber, parameter='purge', purge_time=20):

        if self.subprocessBox[boxnumber] == 0:  # If box is not running
            boxnumber = boxnumber + 1  # boxnumber is index, but device name is not
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

    # def solenoid_dialog(self, boxnumber):
    #     if self.subprocessBox[boxnumber] == 0:  # If box is not running
    #         boxnumber = boxnumber + 1  # boxnumber is index, but device name is not
    #         # print("Opening solenoid control for box {:d}".format(boxnumber))
    #         # self.log.info("Opening solenoid control for box {:d}".format(boxnumber))
    #         dialog = SolenoidGui(boxnumber)
    #         dialog.exec_()
    #     else:
    #         print "Cannot open solenoid: Box {0} is currently running".format(str(boxnumber))
    #         self.log.error("Water error: Cannot open solenoid: Box {0} is currently running".format(str(boxnumber)))
    # endregion

    # region Box updating functions
    def refreshall(self):
        # refresh each box, checking for run status, checking if box should sleep

        # print "timer fired"
        # self.log.info("timer fired")
        # print mem_top()
        for boxnumber in self.boxList:
            if self.debug:
                self.refreshfile(boxnumber)

            # If box is still running, check
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

                # Check if subprocess is still running
                if self.subprocessBox[boxnumber] != 1:  # subprocessBox set to 1 when sleeping, so don't check that
                    # it's still running
                    poll = self.subprocessBox[boxnumber].poll()
                    if poll is None:  # or self.args['debug'] is not False:  # poll() == 0 means the subprocess is still
                        # running
                        self.refreshfile(boxnumber)

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
                    logTotalsMessage = "Training Trials: {trials}   Probe trials: {probe_trials}\n" \
                                       "Rf'd responses: {feeds}".format(**logData)
                    logTotalsMessage.encode('utf8')
                    self.display_message(boxnumber, logTotalsMessage, target='status')

                    self.logRawCounts = QtGui.QStandardItemModel(self)
                    self.logRawCounts.setHorizontalHeaderLabels(["S+", "S-", "Prb+", "Prb-"])
                    self.logRawCounts.setVerticalHeaderLabels(["RespSw", "TrlSw"])

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
                        logStats = "d' (NR): {dprime_NR:1.2f}      β (NR): {bias_NR:1.2f} {bias_description_NR}".format(
                            **logData)
                    else:
                        logStats = "d': {dprime:1.2f}      β: {bias:1.2f} {bias_description}".format(**logData)
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
        self.useNRList[boxnumber].setChecked(self.useNRList[boxnumber].isChecked())

    def auto_sleep_set(self, boxnumber):
        self.autoSleepList[boxnumber].setChecked(self.autoSleepList[boxnumber].isChecked())

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
                self.display_message(boxnumber, error)
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
                self.display_message(boxnumber, error)
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
        errorHandler = logging.FileHandler(self.error_file, mode='w')
        errorHandler.setLevel(logging.ERROR)
        errorHandler.setFormatter(logging.Formatter('"%(asctime)s",\n%(message)s'))

        self.log.addHandler(errorHandler)

    # endregion

    # region data analysis
    def analyze_performance(self, boxnumber):
        dataFolder = os.path.dirname(str(self.paramFileBoxList[boxnumber].toPlainText()))
        bird_name = self.birdEntryBoxList[boxnumber].toPlainText()
        dialog = StatsGui(dataFolder, bird_name)
        dialog.exec_()

    # endregion

    # region GUI application functions
    def open_application(self):
        # Command line argument parsing
        # message = u'β123'#.decode('utf8')
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
        self.setup_ui(self)  # This is defined in design.py file automatically
        # It sets up layout and widgets that are defined
        self.open_Button.clicked.connect(lambda _, b=box_number: self.open_solenoid(b))
        self.close_Button.clicked.connect(lambda _, b=box_number: self.close_solenoid(b))
        self.done_Button.clicked.connect(self.accept)

        self.box_name.setText(str("Box {:02d}".format(box_number)))

    def open_solenoid(self, boxnumber):
        self.log.info("Opening water system in box {:d}".format(boxnumber))
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
            self.log.debug("Successfully opened device {}".format(device_name))
            # solenoid = channel 16
            device.write("".join([chr(16), chr(3)]))  # set channel 16 as output
            # device.write("".join([chr(16), chr(2)]))  # close solenoid, just in case
            device.write("".join([chr(16), chr(1)]))  # open solenoid

            self.solenoid_Status_Text.setText(str("OPEN"))
            self.open_Button.setEnabled(False)
            self.close_Button.setEnabled(True)

    def close_solenoid(self, boxnumber):
        self.log.info("Closing water system in box {:d}".format(boxnumber))
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
            # solenoid = channel 16
            device.write("".join([chr(16), chr(3)]))  # set channel 16 as output
            # device.write("".join([chr(16), chr(2)]))  # close solenoid, just in case

            device.write("".join([chr(16), chr(2)]))  # close solenoid
            device.close()  # close connection
            print "Closed water system in box {0}".format(str(boxnumber))

            self.solenoid_Status_Text.setText(str("CLOSED"))
            self.close_Button.setEnabled(False)
            self.open_Button.setEnabled(True)


class StatsGui(QtGui.QDialog, pyoperant_gui_layout.StatsWindow):
    """
    Code for creating and managing dialog that displays bird's performance stats
    Added 11/30/18 by AR
    """

    def __init__(self, data_folder, bird_name):
        super(self.__class__, self).__init__()
        self.setup_ui(self)  # This is defined in pyoperant_gui_layout.py file

        self.export_Button.clicked.connect(lambda _, b=data_folder: self.export(b))
        self.done_Button.clicked.connect(self.accept)
        self.noResponse_Checkbox.stateChanged.connect(lambda _, b=data_folder: self.recalculate(b))
        self.probe_Checkbox.stateChanged.connect(lambda _, b=data_folder: self.recalculate(b))
        self.raw_Checkbox.stateChanged.connect(lambda _, b=data_folder: self.recalculate(b))

        self.setWindowTitle(str("Performance for {}".format(bird_name)))

        self.recalculate(data_folder)

    def export(self, output_folder):
        output_path = QtGui.QFileDialog.getSaveFileName(self, "Save As...", output_folder, "CSV Files (*.csv)")
        if output_path:
            self.outputData.to_csv(str(output_path))
            print 'saved to {}'.format(output_path)

    def recalculate(self, data_folder):
        include_NR = self.noResponse_Checkbox.isChecked()
        include_Probe = self.probe_Checkbox.isChecked()
        include_raw = self.raw_Checkbox.isChecked()
        perform = analysis.Performance(data_folder)
        perform.summarize('raw')
        self.outputData = perform.analyze(perform.summaryData, groupBy='day', NRTrials=include_NR,
                                          probeTrials=include_Probe, rawTrials=include_raw)
        # self.outputData = perform.analyze(perform.summaryData, groupBy='day')
        outputFile = 'performanceSummary.csv'
        output_path = os.path.join(data_folder, outputFile)
        self.outputData.to_csv(str(output_path), encoding='utf-8')
        self.refresh_table(output_path)

    def refresh_table(self, output_path):
        # reimport the data from csv because moving directly from dataframe is a pain
        self.model = QtGui.QStandardItemModel(self)

        with open(output_path, 'rb') as inputFile:
            i = 1
            for row in csv.reader(inputFile):
                if i == 1:  # set headers of table
                    for column in range(len(row)):
                        # reencode each item in header list as utf-8 so beta can be displayed properly
                        row[column] = row[column].decode('utf-8')
                    self.model.setHorizontalHeaderLabels(row)

                else:  # set items in rows of table
                    items = [QtGui.QStandardItem(field)
                             for field in row]
                    self.model.appendRow(items)
                i += 1

        self.performance_Table.setModel(self.model)  # apply constructed model to tableview object

        self.performance_Table.resizeColumnsToContents()


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
