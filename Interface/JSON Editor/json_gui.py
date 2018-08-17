from PyQt4 import QtCore, QtGui  # Import the PyQt4 module we'll need
import sys  # We need sys so that we can pass argv to QApplication
import os
import subprocess
from subprocess import PIPE

try:
    import simplejson as json

except ImportError:
    import json

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

import json_layout
import pyoperant


# it also keeps events etc that we defined in Qt Designer

class jsonGui(QtGui.QMainWindow, json_layout.Ui_jsonStim):
    def __init__(self):
        # Explaining super is out of the scope of this article
        # So please google it if you're not familar with it
        # Simple reason why we use it here is that it allows us to
        # access variables, methods etc in the design.py file
        super(self.__class__, self).__init__()
        self.setupUi(self)  # This is defined in design.py file automatically
        # It sets up layout and widgets that are defined
        self.paramFile_Button.clicked.connect(lambda: self.param_file_select())
        self.stimDir_Button.clicked.connect(lambda: self.stim_file_select())
        # self.stimRefresh_Button.clicked.connect(lambda: self.stimRefresh_window())
        self.saveButton.clicked.connect(lambda: self.save_window())
        self.saveAs_Button.clicked.connect(lambda: self.saveAs_window())
        self.cancelButton.clicked.connect(self.close)
        self.trialTypeApply_Button.clicked.connect(lambda: self.apply_categories())
        self.refresh_Button.clicked.connect(lambda: self.rearrangetree())
        self.columnOrder = [0, 0, 0, 0, 0, 0, 0]
        # self.item = QtGui.QTreeWidgetItem(self.treeWidget)
        #
        # self.item.setText(0, "test")
        # self.item.setFlags(self.item.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsTristate)
        # self.item.setText(1, "alphabet")
        # self.item.setText(2, "plumbing")
        # self.item.setText(3, "quatro")
        # child = QtGui.QTreeWidgetItem(self.item)
        # child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
        # child.setText(0, "test two")
        # child.setCheckState(0, QtCore.Qt.Unchecked)
        #item = QtGui.QTreeWidgetItem(self.treeWidget,1,"test32, 1234"))
        #item = QtGui.QTreeWidgetItem(self.treeWidget, ("", "test", "test32, 1234"))

    def param_file_select(self):
        paramFile = QtGui.QFileDialog.getOpenFileName(self, "Select Preferences File")
        # execute getOpenFileName dialog and set the directory variable to be equal
        # to the user selected directory

        if paramFile:  # if user didn't pick a file don't continue
            print("success")
            self.paramFile_Box.setPlainText(paramFile)  # add file to the listWidget
            jsonFile = open(paramFile)
            parameters = json.load(jsonFile)
            self.stimDir = parameters["stim_path"]
            self.stimList = parameters["stims"]
            self.condList = parameters["block_design"]["blocks"]["default"]["conditions"]
            self.populate()

            self.stimDir_Box.setPlainText(str(self.stimDir))

            self.trainSMinus_Box.setPlainText(str(parameters["classes"]["sMinus"]["ratio"]))
            self.trainSPlus_Box.setPlainText(str(parameters["classes"]["sPlus"]["ratio"]))
            self.probeSMinus_Box.setPlainText(str(parameters["classes"]["probeMinus"]["ratio"]))
            self.probeSPlus_Box.setPlainText(str(parameters["classes"]["probePlus"]["ratio"]))

    def populate(self):
        # Populate table from scratch
        # self.treeWidget.setRowCount(0)   # Clear table
        # self.treeWidget.setRowCount(len(self.condList))
        condition = []
        stimulus = []
        tempo = []
        baseTempo = []
        stimPattern = []
        bird = []
        soundType = []

        for i in range(0, len(self.stimList)):
            # Get data
            condition.append(str(self.condList.__getitem__(i).get('class')))
            stimulus.append(str(self.stimList.get(self.condList.__getitem__(i).get('stim_name'))))
            tempo.append(int(stimulus[i][5:8]))
            if 97 < tempo[i] < 103:
                baseTempo.append(100)
            elif 110 < tempo[i] < 116:
                baseTempo.append(112.5)
            elif 122 < tempo[i] < 128:
                baseTempo.append(125)
            elif 135 < tempo[i] < 141:
                baseTempo.append(137.5)
            elif 147 < tempo[i] < 153:
                baseTempo.append(150)
            #stimPattern = stimulus[i][11]
            if stimulus[i][11].isdigit:  # Change ir1, ir2, etc. to irr
                stimPattern.append("irr")
            else:
                stimPattern.append(stimulus[i][9:12])
            bird.append(str(stimulus[i][0:2]))
            soundType.append(str(stimulus[i][2:4]))

            # Add data to dict
            # self.data[stimulus] = [baseTempo,tempo,condition,soundType,bird]

        self.dataStruct = []
        # add row
        # self.dataStruct.append(QtGui.QTreeWidgetItem())
        self.dataStruct = zip(baseTempo, tempo, condition, stimPattern, soundType, bird, stimulus)
        # self.dataStruct.append([baseTempo, tempo, condition, stimPattern, soundType, bird, stimulus])

        # print self.dataStruct
            # print self.dataStruct[0][0][0]
            # self.dataStruct[i].setFlags(self.dataStruct[i].flags() | QtCore.Qt.ItemIsUserCheckable)
            # self.dataStruct[i].setCheckState(0, QtCore.Qt.Unchecked)
            # self.dataStruct[stimulus] = [baseTempo, tempo, condition, soundType, bird, stimulus]
            # self.dataStruct[i].setText(0, str(baseTempo))
            # self.dataStruct[i].setText(1, str(tempo))
            # self.dataStruct[i].setText(2, condition)  # Defining the string that way converts the value into one that QtTable likes
            # self.dataStruct[i].setText(3, soundType)
            # self.dataStruct[i].setText(4, bird)
            # self.dataStruct[i].setText(5, stimulus)
            # self.add_row
                # add fields/buttons
            # Create dictionary


        # Get unique values for each column
        # make temporary list variables for each column
        baseTempoList = []
        tempoList = []
        conditionList = []
        stimPatternList = []
        soundTypeList = []
        birdList = []
        stimulusList = []
        # populate list variables
        # print len(self.stimList)
        for row in range(0, len(self.stimList), 1):
            #print row

            baseTempoList.append(self.dataStruct[row][0])
            tempoList.append(self.dataStruct[row][1])
            conditionList.append(self.dataStruct[row][2])
            stimPatternList.append(self.dataStruct[row][3])
            soundTypeList.append(self.dataStruct[row][4])
            birdList.append(self.dataStruct[row][5])
            stimulusList.append(self.dataStruct[row][6])

        # Convert lists to sets to obtain unique values
        self.baseTempoSet = set(baseTempoList)
        self.tempoSet = set(tempoList)
        self.conditionSet = set(conditionList)
        self.stimPatternSet = set(stimPatternList)
        self.soundTypeSet = set(soundTypeList)
        self.birdSet = set(birdList)
        self.stimulusSet = set(stimulusList)

        self.uniqueValues = [self.baseTempoSet, self.tempoSet, self.conditionSet, self.stimPatternSet, self.soundTypeSet, self.birdSet, self.stimulusSet]

        # Reorganize list data based on grouping
        headerCount = self.treeWidget.columnCount()
        for i in range(0, headerCount):
            headerName = str(self.treeWidget.headerItem().text(i))
            if headerName == 'Base Tempo':
                self.baseTempoColumn = i
                self.columnOrder[i] = 0
            elif headerName == 'Tempo':
                self.tempoColumn = i
                self.columnOrder[i] = 1
            elif headerName == 'Trial Type':
                self.conditionColumn = i
                self.columnOrder[i] = 2
            elif headerName == 'Pattern':
                self.stimPatternColumn = i
                self.columnOrder[i] = 3
            elif headerName == 'Sound Type':
                self.soundTypeColumn = i
                print 'soundType'
                print self.soundTypeColumn
                self.columnOrder[i] = 4
            elif headerName == 'Bird':
                self.birdColumn = i
                self.columnOrder[i] = 5
            elif headerName == 'Stimulus':
                self.stimulusColumn = i
                self.columnOrder[i] = 6
            else:
                pass

        # Create first column groups
        currentColumn = 0
        i = 0
        # for i in range(0,len(self.uniqueValues[self.columnOrder[currentColumn]])-1):
        for groupName in self.uniqueValues[self.columnOrder[currentColumn]]:
            # groupName = self.uniqueValues[0][i]
            item = QtGui.QTreeWidgetItem(self.treeWidget, i)
            item.setText(0, str(groupName))
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsTristate)

            for j in range(0, len(self.stimList)):
                if self.dataStruct[j][self.columnOrder[currentColumn]] == groupName:
                    child = QtGui.QTreeWidgetItem(item)
                    child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                    child.setCheckState(0, QtCore.Qt.Unchecked)
                    child.setText(currentColumn, str(self.dataStruct[j][self.columnOrder[currentColumn]]))
                    child.setText(self.tempoColumn, str(self.dataStruct[j][1]))
                    child.setText(self.conditionColumn, self.dataStruct[j][
                        2])  # Defining the string that way converts the value into one that QtTable likes
                    child.setText(self.stimPatternColumn, self.dataStruct[j][3])
                    child.setText(self.soundTypeColumn, self.dataStruct[j][4])
                    child.setText(self.birdColumn, self.dataStruct[j][5])
                    child.setText(self.stimulusColumn, self.dataStruct[j][6])
            i = i + 1

        # self.rearrangetree()

    def rearrangetree(self):

        # headerCount = self.treeWidget.columnCount()
        # for i in range(0,headerCount):
        #     headerName = str(self.treeWidget.headerItem().text(i))
        #     if headerName == 'Base Tempo':
        #         self.baseTempoColumn = i
        #         self.columnOrder[i] = 0
        #     elif headerName == 'Tempo':
        #         self.tempoColumn = i
        #         self.columnOrder[i] = 1
        #     elif headerName == 'Trial Type':
        #         self.conditionColumn = i
        #         self.columnOrder[i] = 2
        #     elif headerName == 'Pattern':
        #         self.stimPatternColumn = i
        #         self.columnOrder[i] = 3
        #     elif headerName == 'Sound Type':
        #         self.soundTypeColumn = i
        #         self.columnOrder[i] = 4
        #     elif headerName == 'Bird':
        #         self.birdColumn = i
        #         self.columnOrder[i] = 5
        #     elif headerName == 'Stimulus':
        #         self.stimulusColumn = i
        #         self.columnOrder[i] = 6
        #     else:
        #         pass

        # Create first column groups
        currentColumn = 0
        i = 0
        #for i in range(0,len(self.uniqueValues[self.columnOrder[currentColumn]])-1):
        for groupName in self.uniqueValues[self.columnOrder[currentColumn]]:
            #groupName = self.uniqueValues[0][i]
            item = QtGui.QTreeWidgetItem(self.treeWidget, i)
            item.setText(0, str(groupName))
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsTristate)

            for j in range(0, len(self.stimList)):
                if self.dataStruct[j][self.columnOrder[currentColumn]] == groupName:
                    child = QtGui.QTreeWidgetItem(item)
                    child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                    child.setCheckState(0, QtCore.Qt.Unchecked)
                    child.setText(currentColumn, str(self.dataStruct[j][self.columnOrder[currentColumn]]))
                    child.setText(self.tempoColumn, str(self.dataStruct[j][1]))
                    child.setText(self.conditionColumn, self.dataStruct[j][2])  # Defining the string that way converts the value into one that QtTable likes
                    child.setText(self.stimPatternColumn, self.dataStruct[j][3])
                    child.setText(self.birdColumn, self.dataStruct[j][5])
                    child.setText(self.stimulusColumn, self.dataStruct[j][6])
            i = i+1

    def stim_file_select(self):
        stimFile = QtGui.QFileDialog.getOpenFileName(self, "Select Stimuli Folder")
        # execute getOpenFileName dialog and set the directory variable to be equal
        # to the user selected directory

        if stimFile:  # if user didn't pick a file don't continue
            self.stimDir_Box.setPlainText(stimFile)  # add file to the listWidget

    def save_window(self):
        return

    def saveAs_window(self):
        return

    def apply_categories(self):
        return

    def stimRefresh_window(self):
        return

    def add_row(self):
        # Add row to end of table
        self.treeWidget.setRowCount(self.treeWidget.rowCount()+1)
        newRowIndex = self.treeWidget.rowCount()

        # Add fields to row
        self.row_fields(newRowIndex)

        self.enableCheck = QtGui.QTableWidgetItem()
        self.enableCheck.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        self.enableCheck.setCheckState(QtCore.Qt.Unchecked)
        self.enableCheck.setObjectName(_fromUtf8("enableCheck"))
        self.treeWidget.setItem(newRowIndex, 0, self.enableCheck)

    def row_fields(self, rowIndex):
        # Enable checkbox
        self.enableCheck = QtGui.QTableWidgetItem()
        self.enableCheck.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        self.enableCheck.setCheckState(QtCore.Qt.Unchecked)
        self.enableCheck.setObjectName(_fromUtf8("enableCheck"))
        self.treeWidget.setItem(rowIndex, 0, self.enableCheck)










    def cancel_window(self):
        return

    def cancel_window(self):
        return


def main():
    app = QtGui.QApplication(sys.argv)  # A new instance of QApplication
    form = jsonGui()  # We set the form to be our ExampleApp (design)
    form.show()  # Show the form

    app.exec_()  # and execute the app


if __name__ == '__main__':  # if we're running file directly and not importing it
    main()  # run the main function
