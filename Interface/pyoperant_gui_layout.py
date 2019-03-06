# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'untitled_2.ui'
#
# Created by: PyQt4 UI code generator 4.11.4


# Much of the core code (of creating each of the sections) could probably made more dynamic to allow the user to
# specify the desired number of boxes

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
import math
import collections

try:
    _from_utf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _from_utf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class UiMainWindow(object):

    def status_icon(self, boxnumber, icon):
        # Function for changing status icon to keep image changes within the layout file
        if icon == "start":
            self.graphicBoxList[boxnumber].setPixmap(self.greenIcon)
        elif icon == "stop":
            self.graphicBoxList[boxnumber].setPixmap(self.redIcon)
        elif icon == "error":
            self.graphicBoxList[boxnumber].setPixmap(self.errorIcon)
        elif icon == "blank":
            self.graphicBoxList[boxnumber].setPixmap(self.emptyIcon)
        elif icon == "sleep":
            self.graphicBoxList[boxnumber].setPixmap(self.sleepIcon)
        else:
            pass

    def setup_ui(self, main_window):

        # region Variable init
        self.labelBoxList = []  # Array for the box name label
        self.phaseLabelList = []  # Array for the current phase label
        self.phaseBoxList = []  # Array for the current phase
        self.graphicBoxList = []  # Array for status graphic box
        self.checkActiveLabelBoxList = []  # Array for label for Active checkbox
        self.checkActiveBoxList = []  # Array for "active" checkbox
        self.statusTotalsBoxList = []  # Array for status text box
        self.statusTableBoxList = []  # Array for status text box
        self.statusStatsBoxList = []  # Array for status text box
        self.lastTrialLabelList = []  # Array for last trial text box
        self.lastTrialBoxList = []  # Array for last trial text box
        self.paramFileLabelBoxList = []  # Array for label for parameter file
        self.paramFileBoxList = []  # Array for parameter file text box
        self.paramFileButtonBoxList = []  # Array for parameter file selection button
        self.birdEntryLabelBoxList = []  # Array for label for parameter file
        self.birdEntryBoxList = []  # Array for bird name text box
        self.gridLayoutBoxList = []  # Array for the grid layout for each box
        self.statusLayoutBoxList = []  # Array for the grid layout for each box
        self.optionButtonBoxList = []  # Array for option button
        self.performanceBoxList = []  # Array for "Performance" button
        self.startBoxList = []  # Array for "start box" button
        self.stopBoxList = []  # Array for "stop box" button
        self.lineList = []  # Array for window dividng lines
        # endregion

        # region Icons
        # region Status icons
        self.greenIcon = QPixmap("icons/green_circle.svg")
        self.redIcon = QPixmap("icons/red_stop.svg")
        self.errorIcon = QPixmap("icons/error_x.png")
        self.emptyIcon = QPixmap("icons/not_detected.png")
        self.sleepIcon = QPixmap("icons/sleep.png")
        # endregion

        self.wrenchIcon = QIcon()
        self.wrenchIcon.addPixmap(QtGui.QPixmap(_from_utf8("icons/wrench.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        # endregion

        # region Layout vars
        # Object location-specific variables
        self.numberOfBoxes = 6

        # Calculate box arrangement in window
        # self.rowCount = math.floor(math.sqrt(self.numberOfBoxes))
        rowCount = 3
        columnCount = self.numberOfBoxes / rowCount

        numHorizontalLines = self.numberOfBoxes
        numVerticalLines = columnCount - 1

        lineHeightBuffer = 10  # Padding around text to ensure it will fit in a text box (so text box size will be
        # buffer + (textLnHgt * lineCount)
        # endregion

        # region Formatting templates
        # Text formatting
        font10 = QtGui.QFont()
        font10.setPointSizeF(10.9)
        font11 = QtGui.QFont()
        font11.setPointSize(11)
        font11Bold = QtGui.QFont()
        font11Bold.setPointSize(11)
        font11Bold.setBold(True)
        font12Bold = QtGui.QFont()
        font12Bold.setPointSize(12)
        font12Bold.setBold(True)
        font11Under = QtGui.QFont()
        font11Under.setPointSize(11)
        font11Under.setUnderline(True)

        # Size policies
        sizePolicy_Fixed = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy_Fixed.setHorizontalStretch(0)
        sizePolicy_Fixed.setVerticalStretch(0)

        sizePolicy_minEx_max = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Maximum)
        sizePolicy_minEx_max.setHorizontalStretch(0)
        sizePolicy_minEx_max.setVerticalStretch(0)

        sizePolicy_max = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        sizePolicy_max.setHorizontalStretch(0)
        sizePolicy_max.setVerticalStretch(0)
        # endregion

        # region Main window setup
        main_window.setObjectName(_from_utf8("main_window"))
        main_window.setSizePolicy(sizePolicy_Fixed)
        # main_window.setMaximumSize(QtCore.QSize(1200, 1000))
        self.centralwidget = QtGui.QWidget(main_window)
        self.centralwidget.setSizePolicy(sizePolicy_Fixed)
        # self.centralwidget.setMaximumSize(QtCore.QSize(2000, 2000))
        self.centralwidget.setObjectName(_from_utf8("centralwidget"))

        self.gridLayoutWidget = QtGui.QWidget(self.centralwidget)
        self.gridLayoutWidget.setObjectName(_from_utf8("gridLayoutWidget"))
        self.mainGrid = QtGui.QGridLayout(self.gridLayoutWidget)
        self.mainGrid.setObjectName(_from_utf8("mainGrid"))

        # Menu at bottom of screen
        self.menuGrid = QtGui.QGridLayout()
        self.menuGrid.setObjectName(_from_utf8("menuGrid"))
        self.stopAllButton = QtGui.QPushButton(self.gridLayoutWidget)
        self.stopAllButton.setObjectName(_from_utf8("stopAllButton"))
        self.stopAllButton.setSizePolicy(sizePolicy_minEx_max)
        self.startAllButton = QtGui.QPushButton(self.gridLayoutWidget)
        self.startAllButton.setObjectName(_from_utf8("startAllButton"))
        self.startAllButton.setSizePolicy(sizePolicy_minEx_max)
        self.menuGrid.addWidget(self.stopAllButton, 0, 0, 1, 1)
        self.menuGrid.addWidget(self.startAllButton, 0, 1, 1, 1)
        self.behaviorField = QtGui.QComboBox(self.gridLayoutWidget)
        self.behaviorField.setMinimumSize(QtCore.QSize(200, 0))
        self.behaviorField.setMaximumSize(QtCore.QSize(300, 30))
        self.behaviorField.setObjectName(_from_utf8("behaviorField"))
        self.behaviorField.addItem(_from_utf8(""))
        self.menuGrid.addWidget(self.behaviorField, 0, 4, 1, 1)
        self.behaviorLabel = QtGui.QLabel(self.gridLayoutWidget)
        self.behaviorLabel.setMinimumSize(QtCore.QSize(70, 0))
        self.behaviorLabel.setMaximumSize(QtCore.QSize(80, 30))
        # self.behaviorLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.behaviorLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.behaviorLabel.setObjectName(_from_utf8("behaviorLabel"))
        self.menuGrid.addWidget(self.behaviorLabel, 0, 3, 1, 1)
        self.menuGrid.addItem(QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 0, 2,
                              1, 1)
        self.mainGrid.addLayout(self.menuGrid, 2*rowCount, 0, 1, 2*columnCount-1)
        # endregion

        # region Layout dividing lines
        for i in range(0, numHorizontalLines):  # Horizontal lines
            self.lineList.append(QtGui.QFrame(self.gridLayoutWidget))
            self.lineList[i].setFrameShape(QtGui.QFrame.HLine)
            self.lineList[i].setFrameShadow(QtGui.QFrame.Sunken)
            self.lineList[i].setObjectName(_from_utf8("hline_%d" % i))
            self.mainGrid.addWidget(self.lineList[i], 2 * math.floor(i / columnCount) + 1, 2 * (i % columnCount), 1,
                                    1)

        for i in range(numHorizontalLines, self.numberOfBoxes + int(numVerticalLines)):  # Vertical lines
            self.lineList.append(QtGui.QFrame(self.gridLayoutWidget))
            self.lineList[i].setFrameShadow(QtGui.QFrame.Plain)
            self.lineList[i].setLineWidth(2)
            self.lineList[i].setMidLineWidth(0)
            self.lineList[i].setFrameShape(QtGui.QFrame.VLine)
            self.lineList[i].setObjectName(_from_utf8("vline_%d" % i))
            self.mainGrid.addWidget(self.lineList[i], 0, (i - numHorizontalLines) * 2 + 1, 2 * rowCount, 1)

        # endregion

        # region Individual section elements
        for box in range(0, self.numberOfBoxes):
            # region Object creation
            self.gridLayoutBoxList.append(QtGui.QGridLayout())
            self.statusLayoutBoxList.append(QtGui.QVBoxLayout())
            self.birdEntryLabelBoxList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.birdEntryBoxList.append(QtGui.QPlainTextEdit(self.gridLayoutWidget))
            self.checkActiveBoxList.append(QtGui.QCheckBox(self.gridLayoutWidget))
            self.checkActiveLabelBoxList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.graphicBoxList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.labelBoxList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.paramFileLabelBoxList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.paramFileButtonBoxList.append(QtGui.QPushButton(self.gridLayoutWidget))
            self.paramFileBoxList.append(QtGui.QTextEdit(self.gridLayoutWidget))
            self.phaseLabelList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.phaseBoxList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.optionButtonBoxList.append(QtGui.QPushButton(self.gridLayoutWidget))
            self.startBoxList.append(QtGui.QPushButton(self.gridLayoutWidget))
            self.performanceBoxList.append(QtGui.QPushButton(self.gridLayoutWidget))
            self.statusTotalsBoxList.append(QtGui.QTextBrowser(self.gridLayoutWidget))
            self.statusTableBoxList.append(QtGui.QTableView(self.gridLayoutWidget))
            self.statusStatsBoxList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.stopBoxList.append(QtGui.QPushButton(self.gridLayoutWidget))
            self.lastTrialLabelList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.lastTrialBoxList.append(QtGui.QLabel(self.gridLayoutWidget))

            self.mainGrid.addLayout(self.gridLayoutBoxList[box], 2 * (box % rowCount), 2 * math.floor(box / rowCount),
                                    1, 1)
            # endregion

            # region Object placement
            boxGrid = [10, 5]

            # region Debugging gridlines
            drawBorders = False
            if drawBorders:
                for row in range(boxGrid[0]):
                    line = QtGui.QFrame(self.gridLayoutWidget)
                    line.setFrameShape(QtGui.QFrame.HLine)
                    line.setStyleSheet("color: red;")
                    self.gridLayoutBoxList[box].addWidget(line, row, 0, boxGrid[0] + 1, 0, QtCore.Qt.AlignTop |
                                                          QtCore.Qt.AlignVCenter)
                for column in range(boxGrid[1]):
                    line = QtGui.QFrame(self.gridLayoutWidget)
                    line.setFrameShape(QtGui.QFrame.VLine)
                    line.setMidLineWidth(0)
                    line.setStyleSheet("color: red;")
                    self.gridLayoutBoxList[box].addWidget(line, 0, column, 0, boxGrid[1] + 1, QtCore.Qt.AlignLeft |
                                                          QtCore.Qt.AlignLeft)
                # region End lines
                line = QtGui.QFrame(self.gridLayoutWidget)
                line.setFrameShape(QtGui.QFrame.HLine)
                line.setStyleSheet("color: red;")
                self.gridLayoutBoxList[box].addWidget(line, boxGrid[0], 0, boxGrid[0] + 1, 0, QtCore.Qt.AlignBottom |
                                                      QtCore.Qt.AlignVCenter)

                line = QtGui.QFrame(self.gridLayoutWidget)
                line.setFrameShape(QtGui.QFrame.VLine)
                line.setStyleSheet("color: red;")
                self.gridLayoutBoxList[box].addWidget(line, 0, boxGrid[1], 0, boxGrid[1] + 1, QtCore.Qt.AlignLeft |
                                                      QtCore.Qt.AlignLeft)

                # endregion End lines
            # endregion Debugging gridlines

            """
            # Layout schematic
             
                 0	        1	        2	        3	        4
             ┌──────────┬───────────┬───────────────────────┬─────────┐
            0│boxLbl   	│phaseLbl	│phase	          	    │         │
             ├──────────╔═══════════╧═══════════════════════╗─────────┤
            1│          ║statusTop	        (statusLayout)  ║         │
             ├──────────╢                                   ╟─────────┤
            2│graphic	║          	          	          	║         │
             ├──────────╫───────────────────────────────────╫─────────┤
            3│		    ║statusMain                         ║         │
             ├──────────╢                                   ╟─────────┤
            4│chkAct	║          	         	          	║         │
             ├──────────╫───────────────────────────────────╫─────────┤
            5│chkLbl	║statusStats                        ║         │
             ├──────────╚═══════════╤═══════════════════════╝─────────┤
            6│		    │lastTrlLbl	│lastTrial	        	│         │
             ├──────────┼───────────┴───────────────────────┼─────────┤
            7│parmLbl	│parmEntry	                        │parmBtn  │
             ├──────────┼───────────────────────────────────┼─────────┤
            8│birdLbl	│birdEntry	                        │         │
             ├──────────┴───────────┬───────────┬───────────┼─────────┤
            9│       pfrmBtn	    │start      │stop	    │optionBtn│
             └──────────────────────┴───────────┴───────────┴─────────┘
            """
            self.gridLayoutBoxList[box].addWidget(self.labelBoxList[box], 0, 0, 1, 1)
            self.gridLayoutBoxList[box].addWidget(self.phaseLabelList[box], 0, 1, 1, 1, QtCore.Qt.AlignRight)
            self.gridLayoutBoxList[box].addWidget(self.phaseBoxList[box], 0, 2, 1, 2)
            self.gridLayoutBoxList[box].addLayout(self.statusLayoutBoxList[box], 1, 1, 5, 3)
            self.gridLayoutBoxList[box].addWidget(self.graphicBoxList[box], 2, 0, 1, 1, QtCore.Qt.AlignCenter)
            self.gridLayoutBoxList[box].addWidget(self.checkActiveBoxList[box], 4, 0, 1, 1, QtCore.Qt.AlignCenter)
            self.gridLayoutBoxList[box].addWidget(self.checkActiveLabelBoxList[box], 5, 0, 1, 1, QtCore.Qt.AlignCenter)
            self.gridLayoutBoxList[box].addWidget(self.lastTrialLabelList[box], 6, 1, 1, 3, QtCore.Qt.AlignLeft)
            self.gridLayoutBoxList[box].addWidget(self.lastTrialBoxList[box], 6, 2, 1, 2)
            self.gridLayoutBoxList[box].addWidget(self.paramFileBoxList[box], 7, 1, 1, 3)
            self.gridLayoutBoxList[box].addWidget(self.paramFileButtonBoxList[box], 7, 4, 1, 1)
            self.gridLayoutBoxList[box].addWidget(self.paramFileLabelBoxList[box], 7, 0, 1, 1)
            self.gridLayoutBoxList[box].addWidget(self.birdEntryBoxList[box], 8, 1, 1, 3)
            self.gridLayoutBoxList[box].addWidget(self.birdEntryLabelBoxList[box], 8, 0, 1, 1)
            self.gridLayoutBoxList[box].addWidget(self.startBoxList[box], 9, 2, 1, 1, QtCore.Qt.AlignCenter)
            self.gridLayoutBoxList[box].addWidget(self.performanceBoxList[box], 9, 0, 1, 2, QtCore.Qt.AlignLeft)
            self.gridLayoutBoxList[box].addWidget(self.stopBoxList[box], 9, 3, 1, 1, QtCore.Qt.AlignCenter)
            self.gridLayoutBoxList[box].addWidget(self.optionButtonBoxList[box], 9, 4, 1, 1, QtCore.Qt.AlignCenter)
            self.gridLayoutBoxList[box].setObjectName(_from_utf8("gridLayout_Box%d" % box))
            self.gridLayoutBoxList[box].setSpacing(4)

            self.statusLayoutBoxList[box].addWidget(self.statusTotalsBoxList[box], 0)
            self.statusLayoutBoxList[box].addWidget(self.statusTableBoxList[box], 1)
            self.statusLayoutBoxList[box].addWidget(self.statusStatsBoxList[box], 2)
            self.statusLayoutBoxList[box].setSpacing(0)

            # endregion Object placement

            # region Formatting
            # region Text boxes
            textLnHgt = self.statusTotalsBoxList[box].fontMetrics().height()

            self.statusTotalsBoxList[box].setFont(font11)
            self.statusTotalsBoxList[box].setMinimumSize(QtCore.QSize(280, lineHeightBuffer + (textLnHgt * 2)))
            self.statusTotalsBoxList[box].setMaximumSize(QtCore.QSize(340, lineHeightBuffer + (textLnHgt * 2)))
            self.statusTotalsBoxList[box].setObjectName(_from_utf8("statusTotalsText_Box%d" % box))
            self.statusTotalsBoxList[box].setSizePolicy(sizePolicy_Fixed)
            self.statusTotalsBoxList[box].setStyleSheet("border: 0px;")
            self.statusTotalsBoxList[box].setTabStopWidth(60)

            self.statusTableBoxList[box].setFont(font11)
            self.statusTableBoxList[box].setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
            self.statusTableBoxList[box].setSelectionMode(QtGui.QAbstractItemView.NoSelection)
            self.statusTableBoxList[box].setMinimumSize(QtCore.QSize(280, lineHeightBuffer + (textLnHgt * 4)))
            self.statusTableBoxList[box].setMaximumSize(QtCore.QSize(340, lineHeightBuffer + (textLnHgt * 4)))
            self.statusTableBoxList[box].setObjectName(_from_utf8("statusTable_Box%d" % box))
            self.statusTableBoxList[box].setSizePolicy(sizePolicy_Fixed)
            self.statusTableBoxList[box].setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.statusTableBoxList[box].setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.statusTableBoxList[box].setStyleSheet("border: 0px;")
            self.statusTableBoxList[box].horizontalHeader().setMinimumSectionSize(50)

            self.statusStatsBoxList[box].setFont(font11)
            self.statusStatsBoxList[box].setMinimumSize(QtCore.QSize(280, lineHeightBuffer + textLnHgt))
            self.statusStatsBoxList[box].setMaximumSize(QtCore.QSize(340, lineHeightBuffer + textLnHgt))
            self.statusStatsBoxList[box].setObjectName(_from_utf8("statusStatsText_Box%d" % box))
            self.statusStatsBoxList[box].setSizePolicy(sizePolicy_Fixed)
            self.statusStatsBoxList[box].setStyleSheet("border: 0px; background: white; text-align: center;")
            # self.statusStatsBoxList[box].setTabStopWidth(60)
            self.statusStatsBoxList[box].setAlignment(QtCore.Qt.AlignCenter)

            self.birdEntryBoxList[box].setFont(font11)
            self.birdEntryBoxList[box].setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.birdEntryBoxList[box].setMaximumSize(QtCore.QSize(280, 10 + textLnHgt))
            self.birdEntryBoxList[box].setObjectName(_from_utf8("birdEntry_Box%d" % box))
            self.birdEntryBoxList[box].setPlainText(_from_utf8(""))
            self.birdEntryBoxList[box].setSizePolicy(sizePolicy_minEx_max)
            self.birdEntryBoxList[box].setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

            self.paramFileBoxList[box].setFont(font11)
            self.paramFileBoxList[box].setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.paramFileBoxList[box].setMaximumSize(QtCore.QSize(280, 10 + textLnHgt))
            self.paramFileBoxList[box].setObjectName(_from_utf8("paramFile_Box%d" % box))
            self.paramFileBoxList[box].setSizePolicy(sizePolicy_minEx_max)
            self.paramFileBoxList[box].setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

            # endregion Text boxes

            # region Labels
            self.labelBoxList[box].setFont(font12Bold)
            self.labelBoxList[box].setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            self.labelBoxList[box].setFrameShape(QFrame.Panel)
            self.labelBoxList[box].setObjectName(_from_utf8("label_Box%d" % box))

            self.phaseLabelList[box].setFont(font10)
            self.phaseLabelList[box].setObjectName(_from_utf8("phaseLabel_Box%d" % box))

            self.phaseBoxList[box].setFont(font11Under)
            self.phaseBoxList[box].setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self.phaseBoxList[box].setObjectName(_from_utf8("phase_Box%d" % box))

            self.lastTrialLabelList[box].setFont(font11)
            self.lastTrialLabelList[box].setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self.lastTrialLabelList[box].setObjectName(_from_utf8("lastTrialLabel_Box%d" % box))

            self.lastTrialBoxList[box].setFont(font11Under)
            self.lastTrialBoxList[box].setObjectName(_from_utf8("lastTrial_Box%d" % box))

            self.checkActiveLabelBoxList[box].setFont(font11)
            self.checkActiveLabelBoxList[box].setAlignment(QtCore.Qt.AlignCenter)
            self.checkActiveLabelBoxList[box].setObjectName(_from_utf8("checkActiveLabel_Box%d" % box))
            self.checkActiveLabelBoxList[box].setSizePolicy(sizePolicy_minEx_max)

            self.paramFileLabelBoxList[box].setFont(font11)
            self.paramFileLabelBoxList[box].setAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
            self.paramFileLabelBoxList[box].setMaximumSize(QtCore.QSize(500, 26))
            self.paramFileLabelBoxList[box].setObjectName(_from_utf8("paramFileLabel_Box%d" % box))
            self.paramFileLabelBoxList[box].setSizePolicy(sizePolicy_minEx_max)

            self.birdEntryLabelBoxList[box].setFont(font11)
            self.birdEntryLabelBoxList[box].setAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
            self.birdEntryLabelBoxList[box].setMaximumSize(QtCore.QSize(500, 26))
            self.birdEntryLabelBoxList[box].setObjectName(_from_utf8("birdEntryLabel_Box%d" % box))
            self.birdEntryLabelBoxList[box].setSizePolicy(sizePolicy_minEx_max)

            # endregion Labels

            # region Buttons
            self.paramFileButtonBoxList[box].setFont(font11)
            self.paramFileButtonBoxList[box].setMaximumSize(QtCore.QSize(27, 27))
            self.paramFileButtonBoxList[box].setObjectName(_from_utf8("paramFileButton_Box%d" % box))
            self.paramFileButtonBoxList[box].setSizePolicy(sizePolicy_max)

            self.startBoxList[box].setFont(font11)
            self.startBoxList[box].setMaximumSize(QtCore.QSize(100, 27))
            self.startBoxList[box].setObjectName(_from_utf8("start_Box1"))
            self.startBoxList[box].setSizePolicy(sizePolicy_minEx_max)

            self.performanceBoxList[box].setFont(font11)
            self.performanceBoxList[box].setMaximumSize(QtCore.QSize(100, 27))
            self.performanceBoxList[box].setObjectName(_from_utf8("start_Box1"))
            self.performanceBoxList[box].setSizePolicy(sizePolicy_minEx_max)

            self.stopBoxList[box].setFont(font11)
            self.stopBoxList[box].setMaximumSize(QtCore.QSize(100, 27))
            self.stopBoxList[box].setObjectName(_from_utf8("stop_Box%d" % box))
            self.stopBoxList[box].setEnabled(False)
            self.stopBoxList[box].setSizePolicy(sizePolicy_minEx_max)

            self.optionButtonBoxList[box].setFont(font11)
            self.optionButtonBoxList[box].setMaximumSize(QtCore.QSize(27, 27))
            self.optionButtonBoxList[box].setObjectName(_from_utf8("optionButton_Box%d" % box))
            self.optionButtonBoxList[box].setSizePolicy(sizePolicy_max)
            self.optionButtonBoxList[box].setIcon(self.wrenchIcon)
            self.optionButtonBoxList[box].setMinimumSize(QtCore.QSize(27, 27))
            self.optionButtonBoxList[box].setMaximumSize(QtCore.QSize(27, 27))
            self.optionButtonBoxList[box].setText(_from_utf8(""))

            # endregion Buttons

            # region Checkboxes
            self.checkActiveBoxList[box].setFont(font11)
            self.checkActiveBoxList[box].setIconSize(QtCore.QSize(20, 20))
            self.checkActiveBoxList[box].setMaximumSize(QtCore.QSize(22, 22))
            self.checkActiveBoxList[box].setObjectName(_from_utf8("checkActive_Box%d" % box))
            self.checkActiveBoxList[box].setText(_from_utf8(""))

            # endregion Checkboxes

            # region Graphics
            self.graphicBoxList[box].setAlignment(QtCore.Qt.AlignCenter)
            self.graphicBoxList[box].setFrameShadow(QtGui.QFrame.Sunken)
            self.graphicBoxList[box].setFrameShape(QtGui.QFrame.Panel)
            self.graphicBoxList[box].setMargin(2)
            self.graphicBoxList[box].setMaximumSize(QtCore.QSize(35, 35))
            self.graphicBoxList[box].setObjectName(_from_utf8("graphicLabel_Box%d" % box))
            self.graphicBoxList[box].setPixmap(self.redIcon)
            self.graphicBoxList[box].setScaledContents(True)
            self.graphicBoxList[box].setText(_from_utf8(""))
            self.graphicBoxList[box].setTextInteractionFlags(QtCore.Qt.NoTextInteraction)

            # endregion Graphics

            # region Alignments
            # self.gridLayoutBoxList[box].setAlignment(QtCore.Qt.AlignCenter)
            # endregion Alignments

            # endregion Formatting

        # endregion

        main_window.setCentralWidget(self.centralwidget)

        # region Window sizing
        # Set window and grid size based on content
        widthRatio = 1.05  # 1.05 seems to be the right propotion to prevent things from being cut off or too much space
        mainGridWidth = math.ceil(self.gridLayoutWidget.sizeHint().width() * widthRatio)
        mainGridHeight = self.gridLayoutWidget.sizeHint().height()

        # horizWindow = 300 * columnCount
        # vertWindow = 300 * rowCount + 100
        main_window.setFixedSize(mainGridWidth, mainGridHeight)

        # endregion Window sizing

        self.retranslate_ui(main_window)
        # QtCore.QMetaObject.connectSlotsByName(main_window)

    def retranslate_ui(self, mainwindow):
        mainwindow.setWindowTitle(_translate("MainWindow", "pyoperant Interface", None))
        self.startAllButton.setText(_translate("MainWindow", "Start All", None))
        self.stopAllButton.setText(_translate("MainWindow", "Stop All", None))
        self.behaviorField.setItemText(0, _translate("MainWindow", "GoNoGoInterruptExp", None))
        self.behaviorLabel.setText(_translate("MainWindow", "Paradigm", None))

        for box in range(0, self.numberOfBoxes):
            self.birdEntryLabelBoxList[box].setText(_translate("MainWindow", "Bird", None))
            self.checkActiveLabelBoxList[box].setText(_translate("MainWindow", "Active", None))
            self.labelBoxList[box].setText(_translate("MainWindow", _from_utf8(" Box %s " % str(box + 1)), None))
            self.phaseLabelList[box].setText(_translate("MainWindow", _from_utf8("Phase: "), None))
            self.lastTrialLabelList[box].setText(_translate("MainWindow", _from_utf8("Last Trial: "), None))
            self.paramFileButtonBoxList[box].setText(_translate("MainWindow", "...", None))
            self.paramFileLabelBoxList[box].setText(_translate("MainWindow", "File", None))
            self.performanceBoxList[box].setText(_translate("MainWindow", "Performance", None))
            self.startBoxList[box].setText(_translate("MainWindow", "Start", None))
            self.stopBoxList[box].setText(_translate("MainWindow", "Stop", None))


class UiSolenoidControl(object):
    def setup_ui(self, solenoid_control):
        # region Presets
        solenoid_control.setObjectName(_from_utf8("solenoid_control"))
        solenoid_control.resize(300, 185)
        sizePolicy_fixed = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy_fixed.setHorizontalStretch(0)
        sizePolicy_fixed.setVerticalStretch(0)
        sizePolicy_max = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        sizePolicy_max.setHorizontalStretch(0)
        sizePolicy_max.setVerticalStretch(0)

        font13 = QtGui.QFont()
        font13.setPointSize(13)

        font16 = QtGui.QFont()
        font16.setPointSize(16)
        # endregion Presets

        solenoid_control.setSizePolicy(sizePolicy_fixed)
        solenoid_control.setMaximumSize(QtCore.QSize(300, 200))

        # region Layouts
        self.gridLayout = QtGui.QGridLayout(solenoid_control)
        self.gridLayout.setObjectName(_from_utf8("gridLayout"))

        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.verticalLayout.setObjectName(_from_utf8("verticalLayout"))

        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_from_utf8("horizontalLayout"))
        # endregion Layouts

        # region Labels and text
        self.box_name = QtGui.QLabel(solenoid_control)
        self.box_name.setSizePolicy(sizePolicy_max)
        self.box_name.setMaximumSize(QtCore.QSize(280, 24))
        self.box_name.setBaseSize(QtCore.QSize(50, 18))
        self.box_name.setFont(font13)
        self.box_name.setAlignment(QtCore.Qt.AlignCenter)
        self.box_name.setObjectName(_from_utf8("box_name"))

        self.solenoid_text = QtGui.QLabel(solenoid_control)
        self.solenoid_text.setSizePolicy(sizePolicy_fixed)
        self.solenoid_text.setMaximumSize(QtCore.QSize(280, 24))
        self.solenoid_text.setAlignment(QtCore.Qt.AlignCenter)
        self.solenoid_text.setObjectName(_from_utf8("solenoid_text"))

        self.solenoid_Status_Text = QtGui.QLabel(solenoid_control)
        self.solenoid_Status_Text.setSizePolicy(sizePolicy_fixed)
        self.solenoid_Status_Text.setMinimumSize(QtCore.QSize(0, 17))
        self.solenoid_Status_Text.setMaximumSize(QtCore.QSize(280, 24))

        self.solenoid_Status_Text.setFont(font16)
        self.solenoid_Status_Text.setAlignment(QtCore.Qt.AlignCenter)
        self.solenoid_Status_Text.setObjectName(_from_utf8("solenoid_Status_Text"))
        # endregion Labels and text

        # region Buttons
        self.open_Button = QtGui.QPushButton(solenoid_control)
        self.open_Button.setMinimumSize(QtCore.QSize(0, 27))
        self.open_Button.setMaximumSize(QtCore.QSize(136, 27))
        self.open_Button.setObjectName(_from_utf8("open_Button"))

        self.close_Button = QtGui.QPushButton(solenoid_control)
        self.close_Button.setEnabled(False)
        self.close_Button.setMinimumSize(QtCore.QSize(0, 27))
        self.close_Button.setMaximumSize(QtCore.QSize(136, 27))
        self.close_Button.setObjectName(_from_utf8("close_Button"))

        self.done_Button = QtGui.QPushButton(solenoid_control)
        self.done_Button.setSizePolicy(sizePolicy_fixed)
        self.done_Button.setMaximumSize(QtCore.QSize(270, 27))
        self.done_Button.setObjectName(_from_utf8("done_Button"))
        # endregion Buttons

        # region Other objects
        spacerItem = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)

        self.line = QtGui.QFrame(solenoid_control)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_from_utf8("line"))

        self.horizontalLayout.addWidget(self.open_Button)
        self.horizontalLayout.addWidget(self.close_Button)
        # endregion Other objects

        # region Object placement
        self.verticalLayout.addWidget(self.box_name)
        self.verticalLayout.addWidget(self.solenoid_text)
        self.verticalLayout.addWidget(self.solenoid_Status_Text)
        self.verticalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.line)
        self.verticalLayout.addWidget(self.done_Button)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 2, 2)
        # endregion Object placement

        self.retranslate_ui(solenoid_control)
        # QtCore.QMetaObject.connectSlotsByName(solenoid_control)

    def retranslate_ui(self, solenoid_control):
        solenoid_control.setWindowTitle(_translate("solenoid_control", "Solenoid Control", None))
        self.box_name.setText(_translate("solenoid_control", "Box ", None))
        self.solenoid_text.setText(_translate("solenoid_control", "Solenoid is ", None))
        self.solenoid_Status_Text.setText(_translate("solenoid_control", "CLOSED", None))
        self.open_Button.setText(_translate("solenoid_control", "Open Solenoid", None))
        self.close_Button.setText(_translate("solenoid_control", "Close Solenoid", None))
        self.done_Button.setText(_translate("solenoid_control", "Done", None))


class StatsWindow(object):
    def setup_ui(self, stats_window):
        stats_window.setObjectName(_from_utf8("stats_window"))
        stats_window.resize(1000, 600)
        sizePolicy_fixed = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy_fixed.setHorizontalStretch(0)
        sizePolicy_fixed.setVerticalStretch(0)
        sizePolicy_exp = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy_exp.setHorizontalStretch(0)
        sizePolicy_exp.setVerticalStretch(0)
        sizePolicy_minEx = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy_minEx.setHorizontalStretch(0)
        sizePolicy_minEx.setVerticalStretch(0)
        sizePolicy_min = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy_min.setHorizontalStretch(0)
        sizePolicy_min.setVerticalStretch(0)

        stats_window.setSizePolicy(sizePolicy_exp)
        font = QtGui.QFont()
        font.setPointSize(11)

        self.gridLayout = QtGui.QGridLayout(stats_window)
        self.gridLayout.setObjectName(_from_utf8("gridLayout"))

        # region grid lines for debugging
        boxGrid = [4, 3]
        drawBorders = False
        if drawBorders:
            for row in range(boxGrid[0]):  # Horizontal lines
                line = QtGui.QFrame(stats_window)
                line.setFrameShape(QtGui.QFrame.HLine)
                line.setStyleSheet("color: red;")
                self.gridLayout.addWidget(line, row, 0, boxGrid[0], 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignVCenter)
            for column in range(boxGrid[1]):  # Vertical lines
                line = QtGui.QFrame(stats_window)
                line.setFrameShape(QtGui.QFrame.VLine)
                line.setMidLineWidth(0)
                line.setStyleSheet("color: red;")
                self.gridLayout.addWidget(line, 0, column, 0, boxGrid[1], QtCore.Qt.AlignLeft | QtCore.Qt.AlignLeft)
            # End grid lines
            line = QtGui.QFrame(stats_window)
            line.setFrameShape(QtGui.QFrame.HLine)
            line.setStyleSheet("color: red;")
            self.gridLayout.addWidget(line, boxGrid[0], 0, boxGrid[0], 0,
                                      QtCore.Qt.AlignBottom | QtCore.Qt.AlignVCenter)

            line = QtGui.QFrame(stats_window)
            line.setFrameShape(QtGui.QFrame.VLine)
            line.setStyleSheet("color: red;")
            self.gridLayout.addWidget(line, 0, boxGrid[1], 0, boxGrid[1], QtCore.Qt.AlignLeft | QtCore.Qt.AlignLeft)

        # endregion

        self.performance_Table = QtGui.QTableView(stats_window)
        self.performance_Table.setSizePolicy(sizePolicy_exp)
        self.performance_Table.setMinimumSize(QtCore.QSize(800, 700))
        self.performance_Table.setFont(font)
        self.performance_Table.setObjectName(_from_utf8("performance_Table"))
        self.performance_Table.setSelectionMode(4)
        self.performance_Table.installEventFilter(self)  # to capture keyboard commands to allow ctrl+c functionality

        # Analysis Settings
        self.optionToolbox = QtGui.QToolBox()
        self.optionToolbox.setFrameShape(1)
        self.optionToolbox.setMinimumWidth(260)
        self.optionToolbox.setMaximumWidth(260)

        # region Grouping section
        self.groupGrid = QtGui.QFormLayout()
        self.groupGrid.setObjectName(_from_utf8("groupGrid"))
        self.groupGrid.setLabelAlignment(QtCore.Qt.AlignRight)
        self.groupGrid.setFormAlignment(QtCore.Qt.AlignHCenter)
        self.groupGrid.setAlignment(QtCore.Qt.AlignCenter)

        # region specific groupbys
        self.groupByCheckboxes = collections.OrderedDict()  # orderedDict so grouping can be in order
        self.groupByWidget = QtGui.QWidget()
        self.groupByWidget.setLayout(self.groupGrid)
        self.groupByWidget.setSizePolicy(sizePolicy_exp)
        # endregion
        # endregion Grouping section

        # region filtering section
        self.filterGrid = QtGui.QFormLayout()
        self.filterGrid.setObjectName(_from_utf8("filterGrid"))
        self.filterGrid.setLabelAlignment(QtCore.Qt.AlignRight)
        self.filterGrid.setAlignment(QtCore.Qt.AlignCenter)
        self.filterGrid.setFormAlignment(QtCore.Qt.AlignHCenter)
        self.filterGrid.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        self.filterByWidget = QtGui.QWidget()
        self.filterByWidget.setLayout(self.filterGrid)
        # endregion filtering section

        # region Field selection section
        self.fieldGrid = QtGui.QGridLayout()
        self.fieldGrid.setObjectName(_from_utf8("fieldGrid"))
        self.fieldGrid.setAlignment(QtCore.Qt.AlignCenter)

        self.fieldScroll = QtGui.QScrollArea()
        self.fieldScroll.setMinimumSize(QtCore.QSize(100, 150))
        self.fieldScroll.setMaximumSize(QtCore.QSize(300, 500))
        self.fieldScroll.setWidgetResizable(True)

        self.fieldList = QtGui.QVBoxLayout()
        self.fieldList.setObjectName(_from_utf8("fieldList"))
        self.fieldList.setSpacing(0)

        self.fieldWidget = QtGui.QWidget()

        self.fieldWidget.setLayout(self.fieldList)
        self.fieldScroll.setWidget(self.fieldWidget)

        self.fieldListSelectAll = QtGui.QPushButton(stats_window)
        self.fieldListSelectAll.setMinimumSize(QtCore.QSize(50, 27))
        self.fieldListSelectAll.setMaximumSize(QtCore.QSize(90, 27))
        self.fieldListSelectAll.setSizePolicy(sizePolicy_min)
        self.fieldListSelectNone = QtGui.QPushButton(stats_window)
        self.fieldListSelectNone.setMinimumSize(QtCore.QSize(50, 27))
        self.fieldListSelectNone.setMaximumSize(QtCore.QSize(90, 27))
        self.fieldListSelectNone.setSizePolicy(sizePolicy_min)

        self.fieldSelectWidget = QtGui.QWidget()
        self.fieldSelectWidget.setLayout(self.fieldGrid)
        # endregion Field selection section

        # region Preset Options
        self.presetsGrid = QtGui.QFormLayout()
        self.presetsGrid.setObjectName(_from_utf8("presetsGrid"))
        self.presetsGrid.setLabelAlignment(QtCore.Qt.AlignRight)
        self.presetsGrid.setFormAlignment(QtCore.Qt.AlignHCenter)

        # region Specific presets
        # Use only trials where subject responded, or include all trials?
        self.noResponse_Checkbox = QtGui.QCheckBox(stats_window)
        self.noResponse_Checkbox.setSizePolicy(sizePolicy_fixed)
        self.noResponse_Checkbox.setMaximumSize(QtCore.QSize(27, 27))
        self.noResponse_Checkbox.setObjectName(_from_utf8("noResponse_Checkbox"))
        self.noResponse_Checkbox.setCheckState(2)

        # Analyze probe trials as well?
        self.probe_Checkbox = QtGui.QCheckBox(stats_window)
        self.probe_Checkbox.setSizePolicy(sizePolicy_fixed)
        self.probe_Checkbox.setMaximumSize(QtCore.QSize(27, 27))
        self.probe_Checkbox.setObjectName(_from_utf8("probe_Checkbox"))

        # Include raw counts
        self.raw_Checkbox = QtGui.QCheckBox(stats_window)
        self.raw_Checkbox.setSizePolicy(sizePolicy_fixed)
        self.raw_Checkbox.setMaximumSize(QtCore.QSize(27, 27))
        self.raw_Checkbox.setObjectName(_from_utf8("raw_Checkbox"))
        # endregion

        self.presetsGrid.addRow(QLabel("Include NR Trials"), self.noResponse_Checkbox)
        self.presetsGrid.addRow(QLabel("Include Probe Trials"), self.probe_Checkbox)
        self.presetsGrid.addRow(QLabel("Include Raw Trial Counts"), self.raw_Checkbox)
        self.presetsWidget = QtGui.QWidget()
        self.presetsWidget.setLayout(self.presetsGrid)
        # endregion Preset Options

        # region Menu buttons at bottom
        self.menuGrid = QtGui.QHBoxLayout()
        self.menuGrid.setObjectName(_from_utf8("menuGrid"))

        self.folder_Button = QtGui.QPushButton(stats_window)
        self.folder_Button.setSizePolicy(sizePolicy_fixed)
        self.folder_Button.setMinimumSize(QtCore.QSize(0, 27))
        self.folder_Button.setMaximumSize(QtCore.QSize(300, 27))
        self.folder_Button.setObjectName(_from_utf8("folder_Button"))
        
        self.export_Button = QtGui.QPushButton(stats_window)
        self.export_Button.setSizePolicy(sizePolicy_fixed)
        self.export_Button.setMinimumSize(QtCore.QSize(0, 27))
        self.export_Button.setMaximumSize(QtCore.QSize(300, 27))
        self.export_Button.setObjectName(_from_utf8("export_Button"))

        self.done_Button = QtGui.QPushButton(stats_window)
        self.done_Button.setSizePolicy(sizePolicy_fixed)
        self.done_Button.setMaximumSize(QtCore.QSize(300, 27))
        self.done_Button.setObjectName(_from_utf8("done_Button"))

        self.menuGrid.addWidget(self.folder_Button)
        spacerItem = QtGui.QSpacerItem(200, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.menuGrid.addSpacerItem(spacerItem)
        self.menuGrid.addWidget(self.export_Button)
        self.menuGrid.addWidget(self.done_Button)
        # endregion Menu buttons at bottom

        """
            # Layout schematic

                        0	        	     1	    
             ┌──────────────────────╔═══════════════════════╗
            0│performance_table    	║filterBy    (groupGrid)║
             │                      ╟───────────────────────╢
             │                      ║fieldSelect            ║
             │                      ╟───────────────────────╢
             │                      ║presetsGrid            ║
             ├──────────────────────╚═══════════════════════╝
            1│menuGrid                                      │
             └──────────────────────────────────────────────┘
             ┬┴├┤─│┼┌┐└┘  ╔╗╚╝╟╢╫═║
        """

        # region Object placement
        self.optionToolbox.addItem(self.groupByWidget, 'Group by:')
        self.optionToolbox.addItem(self.filterByWidget, 'Filter by:')
        self.optionToolbox.addItem(self.fieldSelectWidget, 'Select columns:')

        self.fieldGrid.addWidget(self.fieldScroll, 0, 0, 1, 2)
        self.fieldGrid.addWidget(self.fieldListSelectAll, 1, 0, 1, 1)
        self.fieldGrid.addWidget(self.fieldListSelectNone, 1, 1, 1, 1)
        self.fieldGrid.addWidget(self.presetsWidget, 2, 0, 1, 2)

        self.gridLayout.addWidget(self.performance_Table, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.optionToolbox, 0, 1, 1, 1)
        self.gridLayout.addLayout(self.menuGrid, 1, 0, 1, 2)
        # endregion Object placement

        self.retranslate_ui(stats_window)
        # QtCore.QMetaObject.connectSlotsByName(stats_window)

    def retranslate_ui(self, stats_window):
        stats_window.setWindowTitle(_translate("stats_window", "Performance", None))
        self.folder_Button.setText(_translate("stats_window", "Select...", None))
        self.export_Button.setText(_translate("stats_window", "Export", None))
        self.done_Button.setText(_translate("stats_window", "Done", None))
        self.noResponse_Checkbox.setText(_translate("stats_window", "", None))
        self.probe_Checkbox.setText(_translate("stats_window", "", None))
        self.raw_Checkbox.setText(_translate("stats_window", "", None))
        self.fieldListSelectAll.setText(_translate("stats_window", "Select All", None))
        self.fieldListSelectNone.setText(_translate("stats_window", "Select None", None))


class FolderSelectWindow(object):
    def setup_ui(self, folder_window):
        folder_window.setObjectName(_from_utf8("folder_select_window"))
        folder_window.resize(500, 400)
        sizePolicy_fixed = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy_fixed.setHorizontalStretch(0)
        sizePolicy_fixed.setVerticalStretch(0)
        sizePolicy_exp = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy_exp.setHorizontalStretch(0)
        sizePolicy_exp.setVerticalStretch(0)

        folder_window.setSizePolicy(sizePolicy_exp)
        font = QtGui.QFont()
        font.setPointSize(11)

        self.gridLayout = QtGui.QGridLayout(folder_window)
        self.gridLayout.setObjectName(_from_utf8("gridLayout"))

        self.folder_view = QtGui.QTreeView(folder_window)
        self.folder_view.setSizePolicy(sizePolicy_exp)
        self.folder_view.setMinimumSize(QtCore.QSize(500, 300))
        self.folder_view.setFont(font)
        self.folder_view.setAnimated(False)
        self.folder_view.setObjectName(_from_utf8("folder_view"))

        # region Menu buttons at bottom
        self.menuBar = QtGui.QHBoxLayout()
        self.menuBar.setObjectName(_from_utf8("menuBar"))

        self.change_folder_button = QtGui.QPushButton(folder_window)
        self.change_folder_button.setSizePolicy(sizePolicy_fixed)
        self.change_folder_button.setMaximumSize(QtCore.QSize(300, 27))
        self.change_folder_button.setObjectName(_from_utf8("change_folder_button"))

        self.cancel_button = QtGui.QPushButton(folder_window)
        self.cancel_button.setSizePolicy(sizePolicy_fixed)
        self.cancel_button.setMaximumSize(QtCore.QSize(300, 27))
        self.cancel_button.setObjectName(_from_utf8("cancel_button"))

        self.done_button = QtGui.QPushButton(folder_window)
        self.done_button.setSizePolicy(sizePolicy_fixed)
        self.done_button.setMaximumSize(QtCore.QSize(300, 27))
        self.done_button.setObjectName(_from_utf8("done_button"))

        self.menuBar.addWidget(self.change_folder_button)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.menuBar.addSpacerItem(spacerItem)
        self.menuBar.addWidget(self.cancel_button)
        self.menuBar.addWidget(self.done_button)
        # endregion

        """
            # Layout schematic

                        0
             ┌──────────────────────┐
            0│folder_view          	│
             │                      │
             │                      │
             │                      │
             │                      │
             │                      │
             │                      │
             ├──────────────────────┤
            1│menuBar               │
             └──────────────────────┘
             ┬┴├┤─│┼┌┐└┘  ╔╗╚╝╟╢╫═║
        """

        self.gridLayout.addWidget(self.folder_view, 0, 0, 1, 1)
        self.gridLayout.addLayout(self.menuBar, 1, 0, 1, 0)

        self.retranslate_ui(folder_window)
        # QtCore.QMetaObject.connectSlotsByName(folder_window)

    def retranslate_ui(self, stats_window):
        stats_window.setWindowTitle(_translate("stats_window", "Select Folder", None))
        self.done_button.setText(_translate("stats_window", "Done", None))
        self.cancel_button.setText(_translate("stats_window", "Cancel", None))
        self.change_folder_button.setText(_translate("stats_window", "Select Base Folder", None))
