from PyQt4 import QtCore, QtGui  # Import the PyQt4 module we'll need
import sys  # We need sys so that we can pass argv to QApplication
import os
import subprocess
import serial
import time
import threading
import Queue
import numpy

try:
    import simplejson as json

except ImportError:
    import json

import ui_layout
import pyoperant


# it also keeps events etc that we defined in Qt Designer

class pyoperantGui(QtGui.QMainWindow, ui_layout.Ui_MainWindow):
    def __init__(self):

        super(self.__class__, self).__init__()
        self.setupUi(self)  # This is defined in design.py file automatically
        # It sets up layout and widgets that are defined



        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refreshall)
        self.timer.start(5000)

        # arrays for queues and threads
        self.qList = [0] * self.numberOfBoxes
        self.tList = [0] * self.numberOfBoxes
        self.qReadList = [0] * self.numberOfBoxes
        self.tReadList = [0] * self.numberOfBoxes

        self.startAllButton.clicked.connect(lambda: self.start_all())
        self.stopAllButton.clicked.connect(lambda: self.stop_all())

        self.optionMenuList = []

        self.subprocessBox = [0] * self.numberOfBoxes   # stores subprocesses for pyoperant for each box
        self.logProcessBox = [0] * self.numberOfBoxes  # stores subprocesses for log reading for each box
        self.logpathList = [0] * self.numberOfBoxes     # stores log file path for each box

        boxList = range(0,self.numberOfBoxes)

        # Option menu setup
        for boxnumber in boxList:
            self.optionMenuList.append(QtGui.QMenu())
            # Duplicate the following two lines to add additional menu items, modifying names as needed
            self.purgeActionList.append(QtGui.QAction("Purge", self))
            self.optionMenuList[boxnumber].addAction(self.purgeActionList[boxnumber])

        for boxnumber in boxList:
            # This is only in a separate for loop to visually isolate it from the option menu setup above
            self.qList[boxnumber] = Queue.Queue()  # Queue for running subprocesses and pulling outputs without blocking main script
            #self.qReadList[boxnumber] = Queue.Queue()  # Queue for running log read subprocesses without blocking main script



            #self.tReadList[boxnumber] = threading.Thread(target=self.read_output,
            #                                             args=(self.logProcessBox[boxnumber].stdout,
            #                                                   self.qReadList[boxnumber]))
            #self.tReadList[boxnumber].daemon = True

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
        i = 0
        # Duplicate this for each menu item, changing names and functions to match
        for action in self.purgeActionList:
            action.triggered.connect(lambda _, b=i: self.purge_water(boxnumber=b))
            i += 1

        for boxnumber in boxList:  # Attach menus to option buttons
            self.optionButtonBoxList[boxnumber].setMenu(self.optionMenuList[boxnumber])

        self.closeEvent = self.close_application

        self.open_application()

    def param_file_select(self, boxnumber):

        self.paramFileBoxList[boxnumber].clear()  # In case there are any existing elements in the list
        paramFile = QtGui.QFileDialog.getOpenFileName(self, "Select Preferences File")
        # execute getOpenFileName dialog and set the directory variable to be equal
        # to the user selected directory

        if paramFile:  # if user didn't pick a file don't continue

            self.paramFileBoxList[boxnumber].setPlainText(paramFile)  # add file to the listWidget

    def stop_box(self, boxnumber):
        # stop selected box

        if not self.subprocessBox[boxnumber] == 0:  # Only operate if box is running
            self.subprocessBox[boxnumber].kill
            self.subprocessBox[boxnumber] = 0
            self.box_enable(boxnumber)
            self.graphicBoxList[boxnumber].setPixmap(self.redIcon)
        return

    def start_box(self, boxnumber):
        # start selected box
        actualboxnumber = boxnumber + 1
        if self.checkActiveBoxList[boxnumber].checkState():
            if os.path.exists("/dev/teensy%02i" % actualboxnumber):  # check if Teensy is detected
                jsonPath = self.paramFileBoxList[boxnumber].toPlainText()
                if os.path.isfile(jsonPath):  # Make sure param file is specified
                    try:
                        from pyoperant.local import DATAPATH
                    except ImportError:
                        DATAPATH = '/home/rouse/bird/data'
                    self.experimentPath = DATAPATH
                    birdName = self.birdEntryBoxList[boxnumber].toPlainText()
                    if not birdName == "":  # Make sure bird is specified too
                        if self.subprocessBox[boxnumber] == 0:  # Make sure box isn't already running
                            self.subprocessBox[boxnumber] = subprocess.Popen(
                                ['python', '/home/rouse/Desktop/pyoperant/pyoperant/scripts/behave', '-P',
                                 str(boxnumber + 1), '-S', '%s' % birdName, '%s' % self.behaviorField.currentText(),
                                 '-c', '%s' % jsonPath], stderr=subprocess.PIPE)

                            self.tList[boxnumber] = threading.Thread(target=self.read_output,
                                                                     args=(self.subprocessBox[boxnumber].stderr,
                                                                           self.qList[boxnumber]))
                            self.tList[boxnumber].daemon = True

                            self.tList[boxnumber].start()

                            try:
                                error = self.qList[boxnumber].get(False)
                                if error and not error[0:4] == "ALSA":
                                    msg = QtGui.QMessageBox("Warning", error, QtGui.QMessageBox.Warning,
                                                            QtGui.QMessageBox.Ok, 0, 0)
                                    msg.exec_()
                                    self.subprocessBox[boxnumber].kill
                                    self.subprocessBox[boxnumber] = 0
                                    self.graphicBoxList[boxnumber].setPixmap(self.redIcon)
                            except Queue.Empty:
                                self.box_disable(boxnumber)  # UI modifications while box is running
                                self.graphicBoxList[boxnumber].setPixmap(self.greenIcon)

                            # if error and not error[0:4] == "ALSA":
                            #     msg = QtGui.QMessageBox("Warning", error, QtGui.QMessageBox.Warning,
                            #                             QtGui.QMessageBox.Ok, 0, 0)
                            #     msg.exec_()
                            #     self.subprocessBox[boxnumber].kill
                            #     self.subprocessBox[boxnumber] = 0
                            #     self.graphicBoxList[boxnumber].setPixmap(self.redIcon)
                            # else:
                            #     self.box_disable(boxnumber)  # UI modifications while box is running
                            #     self.graphicBoxList[boxnumber].setPixmap(self.greenIcon)

                    else:
                        msg = QtGui.QMessageBox("Warning", "Bird name must be entered.", QtGui.QMessageBox.Warning,
                                                QtGui.QMessageBox.Ok, 0, 0)
                        msg.exec_()
                else:
                    msg = QtGui.QMessageBox("Warning", "No parameter file selected.", QtGui.QMessageBox.Warning,
                                            QtGui.QMessageBox.Ok, 0, 0)
                    msg.exec_()
            else:
                msg = QtGui.QMessageBox("Warning", "Teensy not detected.", QtGui.QMessageBox.Warning,
                                        QtGui.QMessageBox.Ok, 0, 0)
                msg.exec_()
        else:
            msg = QtGui.QMessageBox("Warning", "Box not checked.", QtGui.QMessageBox.Warning,
                                    QtGui.QMessageBox.Ok, 0, 0)
            msg.exec_()
        return

    def read_output(self, pipe, q):

        while True:
            output = pipe.readline()
            q.put(output)

    def read_input(self, write_pipe, in_pipe_name):
        """reads input from a pipe with name `read_pipe_name`,
        writing this input straight into `write_pipe`"""
        while True:
            with open(in_pipe_name, "r") as f:
                write_pipe.write(f.read())

    def start_all(self):
        # start all checked boxes
        for boxnumber in range(0, 12):
            if self.subprocessBox[boxnumber] == 0 and self.checkActiveBoxList[boxnumber].checkState():
                self.start_box(boxnumber)
        return

    def stop_all(self):
        # stop all running boxes
        for boxnumber in range(0, 12):
            if not self.subprocessBox[boxnumber] == 0:
                self.stop_box(boxnumber)
        return

    def box_disable(self, boxnumber):
        # Hide and/or disable objects while box is running
        self.paramFileButtonBoxList[boxnumber].setEnabled(False)
        self.birdEntryBoxList[boxnumber].setReadOnly(True)
        self.startBoxList[boxnumber].setEnabled(False)
        self.stopBoxList[boxnumber].setEnabled(True)

    def box_enable(self, boxnumber):
        # Enable objects when box is not running
        self.paramFileButtonBoxList[boxnumber].setEnabled(True)
        self.birdEntryBoxList[boxnumber].setReadOnly(False)
        self.startBoxList[boxnumber].setEnabled(True)
        self.stopBoxList[boxnumber].setEnabled(False)

    def purge_water(self, boxnumber):
        return
        boxnumber = boxnumber + 1   # boxnumber is index, but device name is not
        print("Purging water system in box %d" % boxnumber)
        device_name = '/dev/teensy%02i' % boxnumber
        self.device = serial.Serial(port=device_name,
                                    baudrate=19200,
                                    timeout=5)
        if self.device is None:
            raise 'Could not open serial device %s' % self.device_name

        #print("Waiting for device to open")
        self.device.readline()
        self.device.flushInput()
        print("Successfully opened device %s" % self.device_name)
        # solenoid = channel 16
        self.device.write("".join([chr(16), chr(3)]))   # set channel 16 as output
        # self.device.write("".join([chr(16), chr(2)]))  # close solenoid, just in case
        self.device.write("".join([chr(16), chr(1)]))  # open solenoid
        startTime = time.time()
        purgeTime = 5

        while True:
            elapsedTime = time.time() - startTime
            if purgeTime <= elapsedTime:
                break

        self.device.write("".join([chr(16), chr(2)]))   # close solenoid
        self.device.close()    # close connection
        print 'Purged box ' + str(boxnumber)

    def refreshall(self):
        # print "timer fired"
        for box in range(0, 12):
            if not self.subprocessBox[box] == 0:  # If box is running
                self.refreshfile(box)

    def refreshfile(self, boxnumber):
        birdName = str(self.birdEntryBoxList[boxnumber].toPlainText())
        # experiment_path = str(self.logpathList[boxnumber]+"/")
        dataPath = os.path.join(self.experimentPath,birdName,birdName + ".log")
        print "opening file for box %d (%s)" % (boxnumber+1, birdName)
        f = open(dataPath, 'r')
        if f:
            logData = f.readlines()
            self.statusTextBoxList[boxnumber].setPlainText('\n'.join(logData[-10:]))
            f.close()
        else:
            print "Unable to open file for %s" % birdName

    def open_application(self):
        settingsFile = 'settings.json'
        if os.path.isfile(settingsFile):  # Make sure param file is specified
            print 'Settings detected'
            with open(settingsFile, 'r') as f:
                dictLoaded = json.load(f)
                if dictLoaded['birds']:
                    for i, birdName in dictLoaded['birds']:
                        if birdName:
                            self.birdEntryBoxList[i].setPlainText(birdName)

                if dictLoaded['paramFiles']:
                    for i, paramFile in dictLoaded['paramFiles']:
                        if paramFile:
                            self.paramFileBoxList[i].setPlainText(paramFile)

    def close_application(self, event):
        # Save settings to file to reload for next time
        # choice = QtGui.QMessageBox.question(self, "Save?", "Save all settings?", QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)

        # if choice == QtGui.QMessageBox.Yes:
        # build dictionary to save
        boxlist = range(0, self.numberOfBoxes)
        paramFileList = []
        birdListTemp = []
        for boxnumber in boxlist:
            # Get plain text of both param file path and bird name, then join in a list for each
            paramSingle = str(self.paramFileBoxList[boxnumber].toPlainText())
            paramFileList.append(paramSingle)
            birdSingle = str(self.birdEntryBoxList[boxnumber].toPlainText())
            birdListTemp.append(birdSingle)
        paramFiles = zip(boxlist, paramFileList)
        birds = zip(boxlist, birdListTemp)

        d = {}
        d['paramFiles'] = paramFiles
        d['birds'] = birds

        with open('settings.json', 'w') as outfile:
            json.dump(d, outfile, ensure_ascii=False)

        event.accept()


def main():
    app = QtGui.QApplication(sys.argv)  # A new instance of QApplication

    form = pyoperantGui()  # We set the form to be our ExampleApp (design)
    form.show()  # Show the form
    sys.exit(app.exec_())  # and execute the app


if __name__ == '__main__':  # if we're running file directly and not importing it
    main()  # run the main function
