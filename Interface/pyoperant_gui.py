from PyQt4 import QtCore, QtGui  # Import the PyQt4 module we'll need
import sys  # We need sys so that we can pass argv to QApplication
import os
import subprocess
import serial
import time
import threading
import Queue
import pyudev
import re

# import watchdog

try:
    import simplejson as json

except ImportError:
    import json

import pyoperant_gui_layout


class PyoperantGui(QtGui.QMainWindow, pyoperant_gui_layout.UiMainWindow):
    teensy_emit = QtCore.pyqtSignal(int, str)

    def __init__(self):

        super(self.__class__, self).__init__()
        self.setup_ui(self)  # This is defined in design.py file automatically
        # It sets up layout and widgets that are defined

        # Number of boxes declared in pyoperant_gui_layout.py

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refreshall)
        self.timer.start(5000)

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
        self.qReadList = [0] * self.numberOfBoxes  # list of queues for inputs to subprocesses
        self.tReadList = [0] * self.numberOfBoxes  # list of queues for inputs to subprocesses

        self.startAllButton.clicked.connect(lambda: self.start_all())
        self.stopAllButton.clicked.connect(lambda: self.stop_all())

        self.optionMenuList = []

        self.subprocessBox = [0] * self.numberOfBoxes  # stores subprocesses for pyoperant for each box
        self.logProcessBox = [0] * self.numberOfBoxes  # stores subprocesses for log reading for each box
        self.logpathList = [0] * self.numberOfBoxes  # stores log file path for each box

        self.boxList = range(0, self.numberOfBoxes)

        # Variable initiation
        self.experimentPath = ""
        self.purgeActionList = []
        self.primeActionList = []
        # self.logModList = []  # Last modification date of log file
        self.solenoidControlList = []

        # Option menu setup
        for boxnumber in self.boxList:
            self.optionMenuList.append(QtGui.QMenu())
            # Duplicate the following two lines to add additional menu items, modifying names as needed
            self.purgeActionList.append(QtGui.QAction("Purge (20s)", self))
            self.optionMenuList[boxnumber].addAction(self.purgeActionList[boxnumber])

            self.primeActionList.append(QtGui.QAction("Prime (5s)", self))
            self.optionMenuList[boxnumber].addAction(self.primeActionList[boxnumber])

            self.solenoidControlList.append(QtGui.QAction("Solenoid Control", self))
            self.optionMenuList[boxnumber].addAction(self.solenoidControlList[boxnumber])

        for boxnumber in self.boxList:
            # This is only in a separate for loop to visually isolate it from the option menu setup above
            self.qList[
                boxnumber] = Queue.Queue()  # Queue for running subprocesses and pulling outputs without blocking main script
            # self.qReadList[boxnumber] = Queue.Queue()  # Queue for running log read subprocesses without blocking main script

            # self.tReadList[boxnumber] = threading.Thread(target=self.read_output_box,
            #                                             args=(self.logProcessBox[boxnumber].stdout,
            #                                                   self.qReadList[boxnumber]))
            # self.tReadList[boxnumber].daemon = True

        i = 0
        for button in self.paramFileButtonBoxList:
            button.clicked.connect(lambda _, b=i: self.param_file_select(boxnumber=b))
            i += 1
        i = 0
        for button in self.startBoxList:
            button.clicked.connect(lambda _, b=i: self.start_box(boxnumber=b))
            i += 1
        i = 0
        for button in self.stopBoxList:
            button.clicked.connect(lambda _, b=i: self.stop_box(boxnumber=b))
            i += 1

        # Duplicate this for each menu item, changing names and functions to match
        i = 0
        for action in self.purgeActionList:
            action.triggered.connect(lambda _, b=i: self.purge_water(boxnumber=b, purge_time=20))
            i += 1

        i = 0
        for action in self.primeActionList:
            action.triggered.connect(lambda _, b=i: self.purge_water(boxnumber=b, purge_time=5))
            i += 1

        i = 0
        for action in self.solenoidControlList:
            action.triggered.connect(lambda _, b=i: self.solenoid_dialog(boxnumber=b))
            i += 1

        for boxnumber in self.boxList:  # Attach menus to option buttons
            self.optionButtonBoxList[boxnumber].setMenu(self.optionMenuList[boxnumber])

        self.closeEvent = self.close_application

        for boxnumber in self.boxList:
            actualboxnumber = boxnumber + 1
            if not os.path.exists("/dev/teensy%02i" % actualboxnumber):  # check if Teensy is detected:
                self.box_button_control(boxnumber, 'disable')
        # error = "Error: Teensy %d not detected." % actualboxnumber
        # self.display_message(boxnumber, error)

        self.open_application()

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
            if error[
               0:4] == "ALSA":  # Ignore ALSA errors; they've always occurred and don't interfere (have to do with the sound chip not liking some channels as written)
                pass
            elif error[0:5] == 'pydev':  # Ignore pydev errors - thrown automatically during PyCharm debugging
                pass
            # elif error[0:5] == 'pydev':  # Add additional exceptions here
            #     pass
            else:
                self.display_message(boxnumber, error)
                print error
                self.stop_box(boxnumber, error_mode=True)
                return True
        else:
            return False

    def display_message(self, boxnumber, message):  # quick method for redirecting messages to status box
        self.statusTextBoxList[boxnumber].setPlainText(''.join(message))

    def stop_box(self, boxnumber, error_mode=False):
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
        self.subprocessBox[boxnumber] = 0
        self.box_button_control(boxnumber, "stop")
        self.refreshfile(boxnumber)  # one last time to display any errors sent to the summaryDAT file
        if error_mode:
            # self.graphicBoxList[boxnumber].setPixmap(self.errorIcon)
            self.status_icon(boxnumber, 'error')
        else:
            # self.graphicBoxList[boxnumber].setPixmap(self.redIcon)
            self.status_icon(boxnumber, 'stop')

    def start_box(self, boxnumber):
        # start selected box
        actualboxnumber = boxnumber + 1

        # Error checking: make sure all relevant boxes are filled and files are found:
        birdName = self.birdEntryBoxList[boxnumber].toPlainText()
        jsonPath = self.paramFileBoxList[boxnumber].toPlainText()

        if not self.checkActiveBoxList[boxnumber].checkState():
            error = "Error: Box not set as Active."
            self.display_message(boxnumber, error)
        elif not os.path.exists("/dev/teensy%02i" % actualboxnumber):  # check if Teensy is detected:
            error = "Error: Teensy %d not detected." % actualboxnumber
            self.display_message(boxnumber, error)
        elif birdName == "":
            error = "Error: Bird name must be entered."
            self.display_message(boxnumber, error)
        elif not os.path.isfile(jsonPath):  # Make sure param file is specified
            error = "Error: No parameter file selected."
            self.display_message(boxnumber, error)
        else:
            try:
                from pyoperant.local import DATAPATH
            except ImportError:
                DATAPATH = '/home/rouse/bird/data'
            self.experimentPath = DATAPATH

            if self.subprocessBox[boxnumber] == 0:  # Make sure box isn't already running
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

                if error and not error[0:4] == "ALSA" and not error[0:5] == 'pydev':
                    self.display_message(boxnumber, error)
                    self.stop_box(boxnumber, error_mode=True)
                    # self.subprocessBox[boxnumber].terminate
                    # self.subprocessBox[boxnumber].wait
                    # self.subprocessBox[boxnumber] = 0
                    # self.graphicBoxList[boxnumber].setPixmap(self.redIcon)
                else:
                    self.box_button_control(boxnumber, "start")  # UI modifications while box is running
                    # self.graphicBoxList[boxnumber].setPixmap(self.greenIcon)
                    self.status_icon(boxnumber, 'start')

    def read_output_box(self, boxnumber, pipe, q):

        while True:
            output = pipe.readline()
            q.put(output)

            # Added the following so that the queue stops when the parent thread stops (so it doesn't take off and inflate memory usage)
            try:
                running = self.subprocessBox[boxnumber].poll()  # Tried this on 10/22/18
            except AttributeError:  # If subprocess was already stopped, and the subprocessBox value was already cleared, then poll() will throw an error
                running = 1
            # running = self.subprocessBox[boxnumber]
            if running is not None:
                break

    def read_input(self, write_pipe, in_pipe_name):
        """reads input from a pipe with name `read_pipe_name`,
        writing this input straight into `write_pipe`"""
        while True:
            with open(in_pipe_name, "r") as f:
                write_pipe.write(f.read())

    def usb_monitor(self, action, device):
        if action == 'add':
            # print 'Connected'
            deviceString = device.device_links.next()
            self.check_teensy(deviceString, True)
        elif action == 'remove':
            # print 'Removed'
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
                match = re.split('Board(\d*)', boxLink)
                boxnumber = int(
                    match[1]) - 1  # Box number as index is indexed from 0, but Teensy numbers are indexed from 1
                # print boxnumber
            except:
                boxnumber = None
                print 'Error: board not recognized'

            if boxnumber is not None:
                if connect:
                    # self.box_button_control(boxnumber, 'enable')
                    parameter = 'enable'
                else:
                    # self.box_button_control(boxnumber, 'disable')
                    parameter = 'disable'
                self.teensy_emit.emit(boxnumber, parameter)
            else:
                pass

    def teensy_control(self, boxnumber, parameter):
        # quick method to enable or disable gui buttons and stop pyoperant if teensy is disconnected
        self.stop_box(boxnumber)
        # self.checkActiveBoxList[boxnumber].setChecked(False)
        self.box_button_control(boxnumber, parameter)

    def start_all(self):
        # start all checked boxes
        for boxnumber in self.boxList:
            if self.subprocessBox[boxnumber] == 0 and self.checkActiveBoxList[boxnumber].checkState():
                self.start_box(boxnumber)

    def stop_all(self):
        # stop all running boxes
        for boxnumber in self.boxList:
            if not self.subprocessBox[boxnumber] == 0:
                self.stop_box(boxnumber)

    def box_button_control(self, boxnumber, parameter):
        if parameter == 'stop' or parameter == 'enable':
            # Enable objects when box is not running
            self.paramFileButtonBoxList[boxnumber].setEnabled(True)
            self.birdEntryBoxList[boxnumber].setReadOnly(False)
            self.startBoxList[boxnumber].setEnabled(True)
            self.stopBoxList[boxnumber].setEnabled(False)
            # self.graphicBoxList[boxnumber].setPixmap(self.redIcon)
            self.status_icon(boxnumber, 'stop')

        elif parameter == "start":
            # Hide and/or disable objects while box is running
            self.paramFileButtonBoxList[boxnumber].setEnabled(False)
            self.birdEntryBoxList[boxnumber].setReadOnly(True)
            self.startBoxList[boxnumber].setEnabled(False)
            self.stopBoxList[boxnumber].setEnabled(True)
            # self.graphicBoxList[boxnumber].setPixmap(self.greenIcon)
            self.status_icon(boxnumber, 'start')

        elif parameter == "disable":
            # For when Teensy isn't connected
            self.paramFileButtonBoxList[boxnumber].setEnabled(True)
            self.birdEntryBoxList[boxnumber].setReadOnly(False)
            self.startBoxList[boxnumber].setEnabled(False)
            self.stopBoxList[boxnumber].setEnabled(False)
            # self.graphicBoxList[boxnumber].setPixmap(self.emptyIcon)
            self.status_icon(boxnumber, 'blank')

    def purge_water(self, boxnumber, purge_time=20):
        boxnumber = boxnumber + 1  # boxnumber is index, but device name is not
        print("Purging water system in box %d" % boxnumber)
        device_name = '/dev/teensy%02i' % boxnumber
        device = serial.Serial(port=device_name,
                               baudrate=19200,
                               timeout=5)
        if device is None:
            raise 'Could not open serial device %s' % device_name

        device.readline()
        device.flushInput()
        print("Successfully opened device %s" % device_name)
        # solenoid = channel 16
        device.write("".join([chr(16), chr(3)]))  # set channel 16 as output
        # device.write("".join([chr(16), chr(2)]))  # close solenoid, just in case
        device.write("".join([chr(16), chr(1)]))  # open solenoid
        startTime = time.time()

        while True:
            elapsedTime = time.time() - startTime
            if purge_time <= elapsedTime:
                break

        device.write("".join([chr(16), chr(2)]))  # close solenoid
        device.close()  # close connection
        print "Purged box {0}".format(str(boxnumber))

    def solenoid_dialog(self, boxnumber):
        boxnumber = boxnumber + 1  # boxnumber is index, but device name is not
        print("Opening solenoid control for box %d" % boxnumber)
        dialog = SolenoidGui(boxnumber)
        dialog.exec_()

    def refreshall(self):
        # print "timer fired"
        # print mem_top()
        for boxnumber in self.boxList:

            # Check for errors and read summary file
            if not self.subprocessBox[boxnumber] == 0:  # If box is running
                # Check if subprocess is still running
                poll = self.subprocessBox[boxnumber].poll()
                if poll is None:  # poll() == 0 means the subprocess is still running
                    self.refreshfile(boxnumber)
                else:
                    self.stop_box(boxnumber, error_mode=True)

    def refreshfile(self, boxnumber):
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

            if g:
                errorData = g.readlines()
                g.close()
            else:
                g = 0

            if not g == 0 and len(errorData) > 1:
                # print "error log"
                self.display_message(boxnumber, errorData)
                # self.statusTextBoxList[boxnumber].setPlainText(''.join(errorData[-10:]))
            else:
                # print 'reg summary'
                self.display_message(boxnumber, logData)
                # self.statusTextBoxList[boxnumber].setPlainText(''.join(logData[-10:]))
        else:
            print "{0}{1}".format("Unable to open file for ", birdName)

        # with open(summary_file, 'r') as f:
        # logData = f.readlines()
        # self.statusTextBoxList[boxnumber].setPlainText('\n'.join(logData[-10:]))
        # f.close()

    def open_application(self):
        settingsFile = 'settings.json'
        if os.path.isfile(settingsFile):  # Make sure param file is specified
            print 'settings.json file detected, loading settings'
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

        d = {'paramFiles': paramFiles, 'birds': birds, 'active': active}
        # d = {}
        # d['paramFiles'] = paramFiles
        # d['birds'] = birds
        # d['active'] = active

        with open('settings.json', 'w') as outfile:
            json.dump(d, outfile, ensure_ascii=False)

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
                    # print "Closed device %d" % int(boxnumber + 1)
            except serial.SerialException:
                pass

            # print "Checked device %d" % int(boxnumber + 1)
        # Stop running sessions
        self.stop_all()

        event.accept()  # Accept GUI closing


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

        self.box_name.setText(str("Box %02i" % box_number))

    def open_solenoid(self, boxnumber):
        print("Opening water system in box %d" % boxnumber)
        device_name = '/dev/teensy%02i' % boxnumber
        device = serial.Serial(port=device_name,
                               baudrate=19200,
                               timeout=5)
        if device is None:
            print 'Could not open serial device %s' % device_name
            raise 'Could not open serial device %s' % device_name
        else:
            device.readline()
            device.flushInput()
            # print("Successfully opened device %s" % device_name)
            # solenoid = channel 16
            device.write("".join([chr(16), chr(3)]))  # set channel 16 as output
            # device.write("".join([chr(16), chr(2)]))  # close solenoid, just in case
            device.write("".join([chr(16), chr(1)]))  # open solenoid

            self.solenoid_Status_Text.setText(str("OPEN"))
            self.open_Button.setEnabled(False)
            self.close_Button.setEnabled(True)

    def close_solenoid(self, boxnumber):
        print("Closing water system in box %d" % boxnumber)
        device_name = '/dev/teensy%02i' % boxnumber
        device = serial.Serial(port=device_name,
                               baudrate=19200,
                               timeout=5)
        if device is None:
            print 'Could not open serial device %s' % device_name
            raise 'Could not open serial device %s' % device_name
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


def main():
    app = QtGui.QApplication(sys.argv)  # A new instance of QApplication

    form = PyoperantGui()  # We set the form to be our ExampleApp (design)
    form.show()  # Show the form
    sys.exit(app.exec_())  # and execute the app


if __name__ == '__main__':  # if we're running file directly and not importing it
    main()  # run the main function
