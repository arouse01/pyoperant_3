# -*- coding: utf-8 -*-

# Much of the core code (of creating each of the sections) could probably made more dynamic to allow the user to
# specify the desired number of boxes

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (QWidget, QGridLayout, QPushButton, QSizePolicy, QLabel, QComboBox, QFrame,
                             QVBoxLayout, QPlainTextEdit, QCheckBox, QTextEdit, QTextBrowser, QTableView,
                             QAbstractItemView, QLayout, QHBoxLayout, QSpinBox, QToolBox, QFormLayout, QScrollArea,
                             QTreeView, QSpacerItem)
from PyQt5.QtGui import QPixmap, QIcon
# from PyQt5.QtGui import *
import math
import collections


class UiMainWindow(object):

    def __init__(self):
        self.behaviorLabel = None
        self.behaviorField = None
        self.startAllButton = None
        self.stopAllButton = None
        self.menuGrid = None
        self.mainGrid = None
        self.gridLayoutWidget = None
        self.centralwidget = None
        self.numberOfBoxes = None
        self.waterIcon = None
        self.wrenchIcon = None
        self.sleepIcon = None
        self.emptyIcon = None
        self.errorIcon = None
        self.redIcon = None
        self.greenIcon = None
        self.lineList = []  # Array for window dividng lines
        self.stopBoxList = []  # Array for "stop box" button
        self.startBoxList = []  # Array for "start box" button
        self.performanceBoxList = []  # Array for "Performance" button
        self.waterOptionButtonBoxList = []  # Array for water option button
        self.optionButtonBoxList = []  # Array for option button
        self.statusLayoutBoxList = []  # Array for the grid layout for each box
        self.gridLayoutBoxList = []  # Array for the grid layout for each box
        self.birdEntryBoxList = []  # Array for bird name text box
        self.birdEntryLabelBoxList = []  # Array for label for parameter file
        self.paramFileButtonBoxList = []  # Array for parameter file selection button
        self.paramFileBoxList = []  # Array for parameter file text box
        self.paramFileLabelBoxList = []  # Array for label for parameter file
        self.lastTrialLabelList = []  # Array for last trial text box
        self.statusStatsBoxList = []  # Array for status text box
        self.statusTableBoxList = []  # Array for status text box
        self.statusTotalsBoxList = []  # Array for status text box
        self.boardVerBoxList = []  # Array for board version dropdown
        self.checkActiveBoxList = []  # Array for "active" checkbox
        self.checkActiveLabelBoxList = []  # Array for label for Active checkbox
        self.graphicBoxList = []  # Array for status graphic box
        self.phaseBoxList = []  # Array for the current phase
        self.phaseLabelList = []  # Array for the current phase label
        self.labelBoxList = []  # Array for the box name label

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

    def setup_ui(self, main_window, window_dim=[], box_count=6, box_coords=[]):

        # region Variable init
        # endregion

        # region Icons
        # region Status icons
        self.greenIcon = QPixmap("icons/green_circle.svg")
        self.redIcon = QPixmap("icons/red_stop.svg")
        self.errorIcon = QPixmap("icons/error_x.png")
        self.emptyIcon = QPixmap("icons/not_detected.png")
        self.sleepIcon = QPixmap("icons/sleep.png")
        # endregion

        # region Button icons
        self.wrenchIcon = QIcon()
        self.wrenchIcon.addPixmap(QtGui.QPixmap("icons/wrench.svg"), QIcon.Normal, QIcon.Off)
        self.waterIcon = QIcon()
        self.waterIcon.addPixmap(QtGui.QPixmap("icons/water.png"), QIcon.Normal, QIcon.Off)
        # endregion Button icons

        # region Other vars

        # endregion Other vars
        # endregion

        # region Layout vars
        # Object location-specific variables
        self.numberOfBoxes = int(box_count)
        if self.numberOfBoxes > 30:
            raise ValueError('Too many boxes indicated, probably a typo: %i' % self.numberOfBoxes)
        elif self.numberOfBoxes < 1:
            raise ValueError('Too few boxes indicated, probably a typo: %i' % self.numberOfBoxes)

        # Calculate box arrangement in window

        if len(window_dim) == 2 and all(isinstance(x, int) for x in window_dim):
            # if window grid dimensions specified (as row, column) and values are integers (as they should be)
            rowCount = window_dim[0]
            columnCount = window_dim[1]
        else:
            rowCount = 3
            columnCount = math.ceil(float(self.numberOfBoxes) / rowCount)

        numHorizontalLines = self.numberOfBoxes
        numVerticalLines = columnCount - 1

        lineHeightBuffer = 10  # Padding around text to ensure it will fit in a text box (so text box size will be
        # buffer + (textLnHgt * lineCount)
        # Validate custom location selections
        coordsValid = False
        if box_coords and len(box_coords) == self.numberOfBoxes:  # make sure all coordinates are specified
            # for each coord tuple
            for i in range(len(box_coords)):
                if 2 != len(box_coords[i]):
                    # ensure tuple is two values
                    coordsValid = False
                    break
                elif not all(isinstance(x, int) for x in box_coords[i]):
                    # check that both values are int
                    coordsValid = False
                    break
                elif box_coords[i][0] >= rowCount and box_coords[i][1] >= columnCount:
                    # make sure coords actually exist within grid dimensions
                    coordsValid = False
                    break
                else:
                    coordsValid = True

        if not coordsValid:
            # default box coordinates
            for i in range(self.numberOfBoxes):
                box_coords.append((i % rowCount, math.floor(i / rowCount)))

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
        sizePolicy_Fixed = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy_Fixed.setHorizontalStretch(0)
        sizePolicy_Fixed.setVerticalStretch(0)

        sizePolicy_minEx_max = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
        sizePolicy_minEx_max.setHorizontalStretch(0)
        sizePolicy_minEx_max.setVerticalStretch(0)

        sizePolicy_max = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy_max.setHorizontalStretch(0)
        sizePolicy_max.setVerticalStretch(0)
        # endregion Formatting templates

        # region Main window setup
        main_window.setObjectName("main_window")
        main_window.setSizePolicy(sizePolicy_Fixed)
        # main_window.setMaximumSize(QtCore.QSize(1200, 1000))
        self.centralwidget = QWidget(main_window)
        self.centralwidget.setSizePolicy(sizePolicy_Fixed)
        # self.centralwidget.setContentsMargins(0, 0, 0, 0)
        # self.centralwidget.setMaximumSize(QtCore.QSize(2000, 2000))
        self.centralwidget.setObjectName("centralwidget")

        self.gridLayoutWidget = QWidget(self.centralwidget)
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayoutWidget.setSizePolicy(sizePolicy_Fixed)
        self.mainGrid = QGridLayout(self.gridLayoutWidget)
        self.mainGrid.setObjectName("mainGrid")
        self.gridLayoutWidget.setLayout(self.mainGrid)

        # Menu at bottom of screen
        self.menuGrid = QGridLayout()
        self.menuGrid.setObjectName("menuGrid")
        self.stopAllButton = QPushButton(self.gridLayoutWidget)
        self.stopAllButton.setObjectName("stopAllButton")
        self.stopAllButton.setSizePolicy(sizePolicy_minEx_max)
        self.startAllButton = QPushButton(self.gridLayoutWidget)
        self.startAllButton.setObjectName("startAllButton")
        self.startAllButton.setSizePolicy(sizePolicy_minEx_max)
        self.menuGrid.addWidget(self.stopAllButton, 0, 0, 1, 1)
        self.menuGrid.addWidget(self.startAllButton, 0, 1, 1, 1)
        self.behaviorField = QComboBox(self.gridLayoutWidget)
        self.behaviorField.setMinimumSize(QtCore.QSize(200, 0))
        self.behaviorField.setMaximumSize(QtCore.QSize(300, 30))
        self.behaviorField.setObjectName("behaviorField")
        self.behaviorField.addItem("")
        self.menuGrid.addWidget(self.behaviorField, 0, 4, 1, 1)
        self.behaviorLabel = QLabel(self.gridLayoutWidget)
        self.behaviorLabel.setMinimumSize(QtCore.QSize(70, 0))
        self.behaviorLabel.setMaximumSize(QtCore.QSize(80, 30))
        # self.behaviorLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTrailing | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.behaviorLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.behaviorLabel.setObjectName("behaviorLabel")
        self.menuGrid.addWidget(self.behaviorLabel, 0, 3, 1, 1)
        self.menuGrid.addItem(add_spacer(20, policy='min'), 0, 2, 1, 1)
        self.mainGrid.addLayout(self.menuGrid, 2 * rowCount, 0, 1, 2 * columnCount - 1)
        # endregion

        # region Layout dividing lines
        for i in range(0, numHorizontalLines):  # Horizontal lines
            self.lineList.append(QFrame(self.gridLayoutWidget))
            self.lineList[i].setFrameShape(QFrame.HLine)
            self.lineList[i].setFrameShadow(QFrame.Sunken)
            self.lineList[i].setObjectName(("hline_%d" % i))
            self.mainGrid.addWidget(self.lineList[i], 2 * math.floor(i / columnCount) + 1, 2 * (i % columnCount), 1,
                                    1)

        for i in range(numHorizontalLines, self.numberOfBoxes + int(numVerticalLines)):  # Vertical lines
            self.lineList.append(QFrame(self.gridLayoutWidget))
            self.lineList[i].setFrameShadow(QFrame.Plain)
            self.lineList[i].setLineWidth(2)
            self.lineList[i].setMidLineWidth(0)
            self.lineList[i].setFrameShape(QFrame.VLine)
            self.lineList[i].setObjectName(("vline_%d" % i))
            self.mainGrid.addWidget(self.lineList[i], 0, (i - numHorizontalLines) * 2 + 1, 2 * rowCount, 1)

        # endregion

        # region Individual section elements
        for box in range(0, self.numberOfBoxes):
            # region Object creation
            self.gridLayoutBoxList.append(QGridLayout())
            self.statusLayoutBoxList.append(QVBoxLayout())
            self.birdEntryLabelBoxList.append(QLabel(self.gridLayoutWidget))
            self.birdEntryBoxList.append(QPlainTextEdit(self.gridLayoutWidget))
            self.checkActiveBoxList.append(QCheckBox(self.gridLayoutWidget))
            self.checkActiveLabelBoxList.append(QLabel(self.gridLayoutWidget))
            self.boardVerBoxList.append(QComboBox(self.gridLayoutWidget))
            self.graphicBoxList.append(QLabel(self.gridLayoutWidget))
            self.labelBoxList.append(QLabel(self.gridLayoutWidget))
            self.paramFileLabelBoxList.append(QLabel(self.gridLayoutWidget))
            self.paramFileButtonBoxList.append(QPushButton(self.gridLayoutWidget))
            self.paramFileBoxList.append(QTextEdit(self.gridLayoutWidget))
            self.phaseLabelList.append(QLabel(self.gridLayoutWidget))
            self.phaseBoxList.append(QLabel(self.gridLayoutWidget))
            self.optionButtonBoxList.append(QPushButton(self.gridLayoutWidget))
            self.waterOptionButtonBoxList.append(QPushButton(self.gridLayoutWidget))
            self.startBoxList.append(QPushButton(self.gridLayoutWidget))
            self.performanceBoxList.append(QPushButton(self.gridLayoutWidget))
            self.statusTotalsBoxList.append(QTextBrowser(self.gridLayoutWidget))
            self.statusTableBoxList.append(QTableView(self.gridLayoutWidget))
            self.statusStatsBoxList.append(QLabel(self.gridLayoutWidget))
            self.stopBoxList.append(QPushButton(self.gridLayoutWidget))
            self.lastTrialLabelList.append(QLabel(self.gridLayoutWidget))

            # TODO: dynamic box placement within self.mainGrid
            boxRow = 2 * box_coords[box][0]
            boxCol = 2 * box_coords[box][1]
            self.mainGrid.addLayout(self.gridLayoutBoxList[box], boxRow, boxCol, 1, 1)
            # endregion

            # region Object placement

            # region Debugging gridlines

            drawBorders = False
            if drawBorders:
                boxGrid = [10, 5]
                for row in range(boxGrid[0]):
                    line = QFrame(self.gridLayoutWidget)
                    line.setFrameShape(QFrame.HLine)
                    line.setStyleSheet("color: red;")
                    self.gridLayoutBoxList[box].addWidget(line, row, 0, boxGrid[0] + 1, 0, QtCore.Qt.AlignmentFlag.AlignTop |
                                                          QtCore.Qt.AlignmentFlag.AlignVCenter)
                for column in range(boxGrid[1]):
                    line = QFrame(self.gridLayoutWidget)
                    line.setFrameShape(QFrame.VLine)
                    line.setMidLineWidth(0)
                    line.setStyleSheet("color: red;")
                    self.gridLayoutBoxList[box].addWidget(line, 0, column, 0, boxGrid[1] + 1, QtCore.Qt.AlignmentFlag.AlignLeft |
                                                          QtCore.Qt.AlignmentFlag.AlignLeft)
                # region End lines
                line = QFrame(self.gridLayoutWidget)
                line.setFrameShape(QFrame.HLine)
                line.setStyleSheet("color: red;")
                self.gridLayoutBoxList[box].addWidget(line, boxGrid[0], 0, boxGrid[0] + 1, 0, QtCore.Qt.AlignmentFlag.AlignBottom |
                                                      QtCore.Qt.AlignmentFlag.AlignVCenter)

                line = QFrame(self.gridLayoutWidget)
                line.setFrameShape(QFrame.VLine)
                line.setStyleSheet("color: red;")
                self.gridLayoutBoxList[box].addWidget(line, 0, boxGrid[1], 0, boxGrid[1] + 1, QtCore.Qt.AlignmentFlag.AlignLeft |
                                                      QtCore.Qt.AlignmentFlag.AlignLeft)

                # endregion End lines
            # endregion Debugging gridlines

            """
            # Per-box layout schematic
             
                 0	        1	        2	        3	        4
             ┌──────────┬───────────┬───────────────────────┬─────────┐
            0│boxLbl   	│phaseLbl	│phase	          	    │phaseChk │
             ├──────────╔═══════════╧═══════════════════════╗─────────┤
            1│          ║statusTop	        (statusLayout)  ║         │
             ├──────────╢                                   ╟─────────┤
            2│graphic	║          	          	          	║         │
             ├──────────╫───────────────────────────────────╫─────────┤
            3│		    ║statusMain                         ║waterOpt │
             ├──────────╢                                   ╟─────────┤
            4│chkAct	║          	         	          	║         │
             ├──────────╫───────────────────────────────────╫─────────┤
            5│chkLbl	║statusStats                        ║         │
             ├──────────╚═══════════╤═══════════════════════╝─────────┤
            6│		    │lastTrial	                     	│         │
             ├──────────┼───────────┴───────────────────────┼─────────┤
            7│parmLbl	│parmEntry	                        │parmBtn  │
             ├──────────┼───────────────────────────────────┼─────────┤
            8│birdLbl	│birdEntry	                        │         │
             ├──────────┴───────────┬───────────┬───────────┼─────────┤
            9│       pfrmBtn	    │start      │stop	    │optionBtn│
             └──────────────────────┴───────────┴───────────┴─────────┘
            """
            self.gridLayoutBoxList[box].addWidget(self.labelBoxList[box], 0, 0, 1, 1)
            self.gridLayoutBoxList[box].addWidget(self.phaseLabelList[box], 0, 1, 1, 1, QtCore.Qt.AlignmentFlag.AlignRight)
            self.gridLayoutBoxList[box].addWidget(self.phaseBoxList[box], 0, 2, 1, 2)

            self.gridLayoutBoxList[box].addWidget(self.waterOptionButtonBoxList[box], 0, 4, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
            self.gridLayoutBoxList[box].addLayout(self.statusLayoutBoxList[box], 1, 1, 5, 3)

            self.gridLayoutBoxList[box].addWidget(self.graphicBoxList[box], 2, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)

            self.gridLayoutBoxList[box].addWidget(self.boardVerBoxList[box], 1, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)

            self.gridLayoutBoxList[box].addWidget(self.checkActiveBoxList[box], 4, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)

            self.gridLayoutBoxList[box].addWidget(self.checkActiveLabelBoxList[box], 5, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)

            self.gridLayoutBoxList[box].addWidget(self.lastTrialLabelList[box], 6, 1, 1, 3, QtCore.Qt.AlignmentFlag.AlignLeft)
            # self.gridLayoutBoxList[box].addWidget(self.lastTrialBoxList[box], 6, 2, 1, 2)

            self.gridLayoutBoxList[box].addWidget(self.paramFileBoxList[box], 7, 1, 1, 3)
            self.gridLayoutBoxList[box].addWidget(self.paramFileButtonBoxList[box], 7, 4, 1, 1)
            self.gridLayoutBoxList[box].addWidget(self.paramFileLabelBoxList[box], 7, 0, 1, 1)

            self.gridLayoutBoxList[box].addWidget(self.birdEntryBoxList[box], 8, 1, 1, 3)
            self.gridLayoutBoxList[box].addWidget(self.birdEntryLabelBoxList[box], 8, 0, 1, 1)

            self.gridLayoutBoxList[box].addWidget(self.performanceBoxList[box], 9, 0, 1, 2, QtCore.Qt.AlignmentFlag.AlignLeft)
            self.gridLayoutBoxList[box].addWidget(self.startBoxList[box], 9, 2, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
            self.gridLayoutBoxList[box].addWidget(self.stopBoxList[box], 9, 3, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
            self.gridLayoutBoxList[box].addWidget(self.optionButtonBoxList[box], 9, 4, 1, 1, QtCore.Qt.AlignmentFlag.AlignCenter)
            self.gridLayoutBoxList[box].setObjectName(("gridLayout_Box%d" % box))
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
            self.statusTotalsBoxList[box].setObjectName(("statusTotalsText_Box%d" % box))
            self.statusTotalsBoxList[box].setSizePolicy(sizePolicy_Fixed)
            self.statusTotalsBoxList[box].setStyleSheet("border: 0px;")
            self.statusTotalsBoxList[box].setTabStopWidth(60)

            self.statusTableBoxList[box].setFont(font11)
            self.statusTableBoxList[box].setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.statusTableBoxList[box].setSelectionMode(QAbstractItemView.NoSelection)
            self.statusTableBoxList[box].setMinimumSize(QtCore.QSize(280, lineHeightBuffer + (textLnHgt * 4)))
            self.statusTableBoxList[box].setMaximumSize(QtCore.QSize(340, lineHeightBuffer + (textLnHgt * 4)))
            self.statusTableBoxList[box].setObjectName(("statusTable_Box%d" % box))
            self.statusTableBoxList[box].setSizePolicy(sizePolicy_Fixed)
            self.statusTableBoxList[box].setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.statusTableBoxList[box].setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.statusTableBoxList[box].setStyleSheet("border: 0px;")
            self.statusTableBoxList[box].horizontalHeader().setMinimumSectionSize(50)

            self.statusStatsBoxList[box].setFont(font11)
            self.statusStatsBoxList[box].setMinimumSize(QtCore.QSize(280, lineHeightBuffer + textLnHgt))
            self.statusStatsBoxList[box].setMaximumSize(QtCore.QSize(340, lineHeightBuffer + textLnHgt))
            self.statusStatsBoxList[box].setObjectName(("statusStatsText_Box%d" % box))
            self.statusStatsBoxList[box].setSizePolicy(sizePolicy_Fixed)
            self.statusStatsBoxList[box].setStyleSheet("border: 0px; background: white; text-align: center;")
            # self.statusStatsBoxList[box].setTabStopWidth(60)
            self.statusStatsBoxList[box].setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

            self.birdEntryBoxList[box].setFont(font11)
            self.birdEntryBoxList[box].setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.birdEntryBoxList[box].setMaximumSize(QtCore.QSize(280, 10 + textLnHgt))
            self.birdEntryBoxList[box].setObjectName(("birdEntry_Box%d" % box))
            self.birdEntryBoxList[box].setPlainText("")
            self.birdEntryBoxList[box].setSizePolicy(sizePolicy_minEx_max)
            self.birdEntryBoxList[box].setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            self.paramFileBoxList[box].setFont(font11)
            self.paramFileBoxList[box].setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.paramFileBoxList[box].setMaximumSize(QtCore.QSize(280, 10 + textLnHgt))
            self.paramFileBoxList[box].setObjectName(("paramFile_Box%d" % box))
            self.paramFileBoxList[box].setSizePolicy(sizePolicy_minEx_max)
            self.paramFileBoxList[box].setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            # endregion Text boxes

            # region Labels
            self.labelBoxList[box].setFont(font12Bold)
            self.labelBoxList[box].setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
            self.labelBoxList[box].setLineWidth(2)
            self.labelBoxList[box].setFrameShape(QFrame.StyledPanel)
            self.labelBoxList[box].setFrameShadow(QFrame.Raised)
            self.labelBoxList[box].setStyleSheet("padding: 1px 1px 1px 1px;")
            self.labelBoxList[box].setObjectName(("label_Box%d" % box))

            self.phaseLabelList[box].setFont(font10)
            self.phaseLabelList[box].setObjectName(("phaseLabel_Box%d" % box))

            self.phaseBoxList[box].setFont(font11Under)
            self.phaseBoxList[box].setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
            self.phaseBoxList[box].setObjectName(("phase_Box%d" % box))

            self.lastTrialLabelList[box].setFont(font11)
            self.lastTrialLabelList[box].setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
            self.lastTrialLabelList[box].setObjectName(("lastTrialLabel_Box%d" % box))

            # self.lastTrialBoxList[box].setFont(font11Under)
            # self.lastTrialBoxList[box].setObjectName(_from_utf8("lastTrial_Box%d" % box))

            self.checkActiveLabelBoxList[box].setFont(font11)
            self.checkActiveLabelBoxList[box].setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.checkActiveLabelBoxList[box].setObjectName(("checkActiveLabel_Box%d" % box))
            self.checkActiveLabelBoxList[box].setSizePolicy(sizePolicy_minEx_max)

            self.paramFileLabelBoxList[box].setFont(font11)
            self.paramFileLabelBoxList[box].setAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTrailing | QtCore.Qt.AlignmentFlag.AlignVCenter)
            self.paramFileLabelBoxList[box].setMaximumSize(QtCore.QSize(500, 26))
            self.paramFileLabelBoxList[box].setObjectName(("paramFileLabel_Box%d" % box))
            self.paramFileLabelBoxList[box].setSizePolicy(sizePolicy_minEx_max)

            self.birdEntryLabelBoxList[box].setFont(font11)
            self.birdEntryLabelBoxList[box].setAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTrailing | QtCore.Qt.AlignmentFlag.AlignVCenter)
            self.birdEntryLabelBoxList[box].setMaximumSize(QtCore.QSize(500, 26))
            self.birdEntryLabelBoxList[box].setObjectName(("birdEntryLabel_Box%d" % box))
            self.birdEntryLabelBoxList[box].setSizePolicy(sizePolicy_minEx_max)

            # endregion Labels

            # region Buttons
            self.waterOptionButtonBoxList[box].setFont(font11)
            self.waterOptionButtonBoxList[box].setMinimumSize(QtCore.QSize(27, 27))
            self.waterOptionButtonBoxList[box].setMaximumSize(QtCore.QSize(27, 27))
            self.waterOptionButtonBoxList[box].setObjectName(("waterOptionButton_Box%d" % box))
            self.waterOptionButtonBoxList[box].setSizePolicy(sizePolicy_max)
            self.waterOptionButtonBoxList[box].setIcon(self.waterIcon)
            self.waterOptionButtonBoxList[box].setText("")
            self.waterOptionButtonBoxList[box].setStyleSheet("QPushButton::menu-indicator { image: none; }")

            self.paramFileButtonBoxList[box].setFont(font11)
            self.paramFileButtonBoxList[box].setMaximumSize(QtCore.QSize(27, 27))
            self.paramFileButtonBoxList[box].setObjectName(("paramFileButton_Box%d" % box))
            self.paramFileButtonBoxList[box].setSizePolicy(sizePolicy_max)
            self.paramFileButtonBoxList[box].setText("...")
            self.paramFileButtonBoxList[box].setStyleSheet("QPushButton::menu-indicator { image: none; width: 0px; }")

            self.startBoxList[box].setFont(font11)
            self.startBoxList[box].setMaximumSize(QtCore.QSize(100, 27))
            self.startBoxList[box].setObjectName("start_Box1")
            self.startBoxList[box].setSizePolicy(sizePolicy_minEx_max)

            self.performanceBoxList[box].setFont(font11)
            self.performanceBoxList[box].setMaximumSize(QtCore.QSize(100, 27))
            self.performanceBoxList[box].setObjectName("start_Box1")
            self.performanceBoxList[box].setSizePolicy(sizePolicy_minEx_max)

            self.stopBoxList[box].setFont(font11)
            self.stopBoxList[box].setMaximumSize(QtCore.QSize(100, 27))
            self.stopBoxList[box].setObjectName(("stop_Box%d" % box))
            self.stopBoxList[box].setEnabled(False)
            self.stopBoxList[box].setSizePolicy(sizePolicy_minEx_max)

            self.optionButtonBoxList[box].setFont(font11)
            self.optionButtonBoxList[box].setMinimumSize(QtCore.QSize(27, 27))
            self.optionButtonBoxList[box].setMaximumSize(QtCore.QSize(27, 27))
            self.optionButtonBoxList[box].setObjectName(("optionButton_Box%d" % box))
            self.optionButtonBoxList[box].setSizePolicy(sizePolicy_max)
            self.optionButtonBoxList[box].setIcon(self.wrenchIcon)
            self.optionButtonBoxList[box].setText("")
            self.optionButtonBoxList[box].setStyleSheet("QPushButton::menu-indicator { image: none; }")

            # endregion Buttons

            # region Checkboxes
            self.checkActiveBoxList[box].setFont(font11)
            self.checkActiveBoxList[box].setIconSize(QtCore.QSize(20, 20))
            self.checkActiveBoxList[box].setMaximumSize(QtCore.QSize(22, 22))
            self.checkActiveBoxList[box].setObjectName(("checkActive_Box%d" % box))
            self.checkActiveBoxList[box].setText("")

            # endregion Checkboxes

            # region Dropdowns
            self.boardVerBoxList[box].setFont(font11)
            self.boardVerBoxList[box].setMaximumSize(QtCore.QSize(100, 22))
            self.boardVerBoxList[box].setObjectName(("boardVer_Box%d" % box))
            self.boardVerBoxList[box].addItems(["v1.3","v1.4","v2.0","v4.0"])
            self.boardVerBoxList[box].setCurrentIndex(0)

            # endregion Checkboxes

            # region Graphics
            self.graphicBoxList[box].setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.graphicBoxList[box].setFrameShadow(QFrame.Sunken)
            self.graphicBoxList[box].setFrameShape(QFrame.Panel)
            self.graphicBoxList[box].setMargin(2)
            self.graphicBoxList[box].setMaximumSize(QtCore.QSize(35, 35))
            self.graphicBoxList[box].setObjectName(("graphicLabel_Box%d" % box))
            self.graphicBoxList[box].setPixmap(self.redIcon)
            self.graphicBoxList[box].setScaledContents(True)
            self.graphicBoxList[box].setText("")
            self.graphicBoxList[box].setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.NoTextInteraction)

            # endregion Graphics

            # region Alignments
            # self.gridLayoutBoxList[box].setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            # endregion Alignments

            # endregion Formatting

        # endregion

        main_window.setCentralWidget(self.centralwidget)

        # region Window sizing
        # Set window and grid size based on content
        # extra space due to padding:
        #   layoutSpacing * (number of columns + number of vertical lines + 1 [for whole layout])
        spacingWidthTotal = (columnCount + numVerticalLines + -3) * self.mainGrid.getContentsMargins()[0]
        mainGridWidth = math.ceil(self.gridLayoutWidget.sizeHint().width() + spacingWidthTotal)
        mainGridHeight = self.gridLayoutWidget.sizeHint().height()

        main_window.setFixedSize(mainGridWidth, mainGridHeight)
        # endregion Window sizing

        self.retranslate_ui(main_window)
        # QtCore.QMetaObject.connectSlotsByName(main_window)

    def retranslate_ui(self, mainwindow):
        mainwindow.setWindowTitle("MainWindow", "pyoperant Interface", None)
        self.startAllButton.setText("MainWindow", "Start All", None)
        self.stopAllButton.setText("MainWindow", "Stop All", None)
        self.behaviorField.setItemText(0, "MainWindow", "GoNoGoInterruptExp", None)
        self.behaviorLabel.setText("MainWindow", "Paradigm", None)

        for box in range(0, self.numberOfBoxes):
            self.birdEntryLabelBoxList[box].setText("MainWindow", "Bird", None)
            self.checkActiveLabelBoxList[box].setText("MainWindow", "Active", None)
            self.labelBoxList[box].setText("MainWindow", (" Box %s " % str(box + 1)), None)
            self.phaseLabelList[box].setText("MainWindow", "Phase: ", None)
            self.lastTrialLabelList[box].setText("MainWindow", "Last Trial: ", None)
            self.paramFileButtonBoxList[box].setText("MainWindow", "...", None)
            self.paramFileLabelBoxList[box].setText("MainWindow", "File", None)
            self.performanceBoxList[box].setText("MainWindow", "Performance", None)
            self.startBoxList[box].setText("MainWindow", "Start", None)
            self.stopBoxList[box].setText("MainWindow", "Stop", None)


class UiSolenoidControl(object):
    def __init__(self):
        self.verticalLayout = None
        self.gridLayout = None
        self.line = None
        self.done_Button = None
        self.test_Button = None
        self.close_Button = None
        self.open_Button = None
        self.test_Times = None
        self.times_Label = None
        self.test_Amount = None
        self.amount_Label = None
        self.test_Label = None
        self.solenoid_Status_Text = None
        self.solenoid_text = None
        self.box_name = None
        self.testLayout = None
        self.horizontalLayout = None

    def setup_ui(self, solenoid_control):
        # region Presets
        sizePolicy_fixed = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy_fixed.setHorizontalStretch(0)
        sizePolicy_fixed.setVerticalStretch(0)
        sizePolicy_max = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy_max.setHorizontalStretch(0)
        sizePolicy_max.setVerticalStretch(0)

        font13 = QtGui.QFont()
        font13.setPointSize(13)

        font16 = QtGui.QFont()
        font16.setPointSize(16)
        # endregion Presets

        solenoid_control.setObjectName("solenoid_control")
        solenoid_control.resize(300, 185)
        solenoid_control.setSizePolicy(sizePolicy_fixed)
        solenoid_control.setMaximumSize(QtCore.QSize(300, 200))

        # region Layouts
        self.gridLayout = QGridLayout(solenoid_control)
        self.gridLayout.setObjectName("gridLayout")

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QLayout.SetFixedSize)
        self.verticalLayout.setObjectName("verticalLayout")

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.testLayout = QGridLayout()
        self.testLayout.setObjectName("testLayout")
        # endregion Layouts

        # region Labels and text
        self.box_name = QLabel(solenoid_control)
        self.box_name.setSizePolicy(sizePolicy_max)
        self.box_name.setMaximumSize(QtCore.QSize(280, 24))
        self.box_name.setBaseSize(QtCore.QSize(50, 18))
        self.box_name.setFont(font13)
        self.box_name.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.box_name.setObjectName("box_name")

        self.solenoid_text = QLabel(solenoid_control)
        self.solenoid_text.setSizePolicy(sizePolicy_fixed)
        self.solenoid_text.setMaximumSize(QtCore.QSize(280, 24))
        self.solenoid_text.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.solenoid_text.setObjectName("solenoid_text")

        self.solenoid_Status_Text = QLabel(solenoid_control)
        self.solenoid_Status_Text.setSizePolicy(sizePolicy_fixed)
        self.solenoid_Status_Text.setMinimumSize(QtCore.QSize(0, 17))
        self.solenoid_Status_Text.setMaximumSize(QtCore.QSize(280, 24))

        self.solenoid_Status_Text.setFont(font16)
        self.solenoid_Status_Text.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.solenoid_Status_Text.setObjectName("solenoid_Status_Text")

        self.test_Label = QLabel(solenoid_control)
        self.test_Label.setSizePolicy(sizePolicy_fixed)
        self.test_Label.setMaximumSize(QtCore.QSize(280, 24))
        self.test_Label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.test_Label.setObjectName("test_Label")

        self.amount_Label = QLabel(solenoid_control)
        self.amount_Label.setSizePolicy(sizePolicy_fixed)
        self.amount_Label.setMaximumSize(QtCore.QSize(280, 24))
        self.amount_Label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.amount_Label.setObjectName("amount_Label")

        self.test_Amount = QSpinBox(solenoid_control)
        self.test_Amount.setFixedHeight(27)
        self.test_Amount.setMaximumWidth(300)
        self.test_Amount.setSuffix(' ms')
        self.test_Amount.setMinimum(0)
        self.test_Amount.setMaximum(1000)
        self.test_Amount.setSingleStep(5)
        self.test_Amount.setValue(75)

        self.times_Label = QLabel(solenoid_control)
        self.times_Label.setSizePolicy(sizePolicy_fixed)
        self.times_Label.setMaximumSize(QtCore.QSize(280, 24))
        self.times_Label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.times_Label.setObjectName("times_Label")

        self.test_Times = QSpinBox(solenoid_control)
        self.test_Times.setFixedHeight(27)
        self.test_Times.setMaximumWidth(300)
        self.test_Times.setMinimum(0)
        self.test_Times.setMaximum(1000)
        self.test_Times.setSingleStep(1)
        self.test_Times.setValue(1)

        # endregion Labels and text

        # region Buttons
        self.open_Button = QPushButton(solenoid_control)
        self.open_Button.setMinimumSize(QtCore.QSize(0, 27))
        self.open_Button.setMaximumSize(QtCore.QSize(136, 27))
        self.open_Button.setObjectName("open_Button")

        self.close_Button = QPushButton(solenoid_control)
        self.close_Button.setEnabled(False)
        self.close_Button.setMinimumSize(QtCore.QSize(0, 27))
        self.close_Button.setMaximumSize(QtCore.QSize(136, 27))
        self.close_Button.setObjectName("close_Button")

        self.test_Button = QPushButton(solenoid_control)
        self.test_Button.setMinimumSize(QtCore.QSize(0, 27))
        self.test_Button.setMaximumSize(QtCore.QSize(136, 27))
        self.test_Button.setObjectName("test_Button")

        self.done_Button = QPushButton(solenoid_control)
        self.done_Button.setSizePolicy(sizePolicy_fixed)
        self.done_Button.setMaximumSize(QtCore.QSize(270, 27))
        self.done_Button.setObjectName("done_Button")
        # endregion Buttons

        # region Other objects
        self.line = QFrame(solenoid_control)
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.line.setObjectName("line")

        self.horizontalLayout.addWidget(self.open_Button)
        self.horizontalLayout.addWidget(self.close_Button)

        self.testLayout.addWidget(self.amount_Label, 0, 0, 1, 1)
        self.testLayout.addWidget(self.times_Label, 0, 1, 1, 1)
        self.testLayout.addWidget(self.test_Amount, 1, 0, 1, 1)
        self.testLayout.addWidget(self.test_Times, 1, 1, 1, 1)
        self.testLayout.addWidget(self.test_Button, 1, 2, 1, 1)
        # endregion Other objects

        # region Object placement
        self.verticalLayout.addWidget(self.box_name)
        self.verticalLayout.addWidget(self.solenoid_text)
        self.verticalLayout.addWidget(self.solenoid_Status_Text)
        self.verticalLayout.addItem(add_spacer(20, policy='min'))
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.line)
        self.verticalLayout.addWidget(self.test_Label)
        self.verticalLayout.addLayout(self.testLayout)
        self.verticalLayout.addWidget(self.line)
        self.verticalLayout.addWidget(self.done_Button)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 2, 2)
        # endregion Object placement

        self.retranslate_ui(solenoid_control)
        # QtCore.QMetaObject.connectSlotsByName(solenoid_control)

    def retranslate_ui(self, solenoid_control):
        solenoid_control.setWindowTitle("solenoid_control", "Solenoid Control", None)
        self.solenoid_text.setText("solenoid_control", "Solenoid is ", None)
        self.open_Button.setText("solenoid_control", "Open Solenoid", None)
        self.close_Button.setText("solenoid_control", "Close Solenoid", None)
        self.test_Label.setText("solenoid_control", "Solenoid Testing", None)
        self.amount_Label.setText("solenoid_control", "Amount", None)
        self.times_Label.setText("solenoid_control", "Times", None)
        self.test_Button.setText("solenoid_control", "Test Solenoid", None)
        self.done_Button.setText("solenoid_control", "Done", None)


class StatsWindow(object):
    def __init__(self):
        self.done_Button = None
        self.export_Button = None
        self.hold_Checkbox = None
        self.recalculate_Button = None
        self.folder_Button = None
        self.menuGrid = None
        self.presetsWidget = None
        self.raw_Checkbox = None
        self.probe_Checkbox = None
        self.noResponse_Checkbox = None
        self.presetsGrid = None
        self.fieldSelectWidget = None
        self.fieldListSelectNone = None
        self.fieldListSelectAll = None
        self.fieldWidget = None
        self.fieldList = None
        self.fieldScroll = None
        self.fieldGrid = None
        self.filterByWidget = None
        self.filterGrid = None
        self.groupByFields = None
        self.groupByDisable_Checkbox = None
        self.groupByDisable = None
        self.groupDisableWidget = None
        self.groupGrid = None
        self.groupGridWidget = None
        self.groupByWidget = None
        self.optionWidth = None
        self.optionToolbox = None
        self.performance_Table = None
        self.tableStatsBar = None
        self.gridLayout = None

    def setup_ui(self, stats_window):
        stats_window.setObjectName("stats_window")
        stats_window.resize(1000, 600)
        sizePolicy_fixed = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy_fixed.setHorizontalStretch(0)
        sizePolicy_fixed.setVerticalStretch(0)
        sizePolicy_exp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy_exp.setHorizontalStretch(0)
        sizePolicy_exp.setVerticalStretch(0)
        sizePolicy_minEx = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        sizePolicy_minEx.setHorizontalStretch(0)
        sizePolicy_minEx.setVerticalStretch(0)
        sizePolicy_min = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy_min.setHorizontalStretch(0)
        sizePolicy_min.setVerticalStretch(0)

        stats_window.setSizePolicy(sizePolicy_exp)
        font = QtGui.QFont()
        font.setPointSize(11)

        self.gridLayout = QGridLayout(stats_window)
        self.gridLayout.setObjectName("gridLayout")

        self.tableStatsBar = QLabel()
        self.tableStatsBar.setStyleSheet("QLabel {border-bottom: 1px solid #CCCCCC; border-top: 0px solid #CCCCCC; "
                                         "qproperty-alignment: AlignRight; padding: 0px 2px 2px 2px; font: 10pt; }")

        # region grid lines for debugging
        drawBorders = False
        if drawBorders:
            boxGrid = [4, 3]
            for row in range(boxGrid[0]):  # Horizontal lines
                line = QFrame(stats_window)
                line.setFrameShape(QFrame.HLine)
                line.setStyleSheet("color: red;")
                self.gridLayout.addWidget(line, row, 0, boxGrid[0], 0, QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignVCenter)
            for column in range(boxGrid[1]):  # Vertical lines
                line = QFrame(stats_window)
                line.setFrameShape(QFrame.VLine)
                line.setMidLineWidth(0)
                line.setStyleSheet("color: red;")
                self.gridLayout.addWidget(line, 0, column, 0, boxGrid[1], QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignLeft)
            # Grid lines at right and bottom
            line = QFrame(stats_window)
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("color: red;")
            self.gridLayout.addWidget(line, boxGrid[0], 0, boxGrid[0], 0,
                                      QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignVCenter)

            line = QFrame(stats_window)
            line.setFrameShape(QFrame.VLine)
            line.setStyleSheet("color: red;")
            self.gridLayout.addWidget(line, 0, boxGrid[1], 0, boxGrid[1], QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignLeft)

        # endregion

        self.performance_Table = QTableView(stats_window)
        self.performance_Table.setSizePolicy(sizePolicy_exp)
        self.performance_Table.setMinimumSize(QtCore.QSize(800, 700))
        self.performance_Table.setFont(font)
        self.performance_Table.setObjectName("performance_Table")
        self.performance_Table.setSelectionMode(4)
        self.performance_Table.installEventFilter(self)  # to capture keyboard commands to allow ctrl+c functionality

        # Analysis Settings
        self.optionToolbox = QToolBox()
        self.optionToolbox.setFrameShape(1)
        self.optionWidth = 290
        self.optionToolbox.setMinimumWidth(self.optionWidth)
        self.optionToolbox.setMaximumWidth(self.optionWidth)

        # region Grouping section
        # Two widgets, one (top) for all of the regular grouping checkboxes, and one (bottom) for the 'show raw 
        # trials' checkbox
        self.groupByWidget = QWidget()
        self.groupByWidget.setSizePolicy(sizePolicy_exp)
        groupByWidgetLayout = QVBoxLayout(self.groupByWidget)
        groupByWidgetLayout.setMargin(0)

        # top widget that holds all regular grouping checkboxes
        self.groupGridWidget = QWidget()
        self.groupGrid = QFormLayout(self.groupGridWidget)
        self.groupGrid.setObjectName("groupGrid")
        self.groupGrid.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.groupGrid.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.groupGrid.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # raw trial checkbox that will disable all grouping checkboxes
        self.groupDisableWidget = QWidget()
        self.groupByDisable = QFormLayout(self.groupDisableWidget)
        self.groupByDisable.setObjectName("groupByDisable")
        self.groupByDisable.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.groupByDisable.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.groupByDisable.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        # actual checkbox
        self.groupByDisable_Checkbox = QCheckBox(stats_window)
        self.groupByDisable_Checkbox.setSizePolicy(sizePolicy_fixed)
        self.groupByDisable_Checkbox.setFixedHeight(27)
        self.groupByDisable_Checkbox.setMaximumWidth(300)
        self.groupByDisable_Checkbox.setObjectName("groupByDisable_Checkbox")
        self.groupByDisable_Checkbox.setText('Show raw trial data')
        self.groupByDisable.addRow(self.groupByDisable_Checkbox)

        groupByWidgetLayout.addWidget(self.groupGridWidget)
        groupByWidgetLayout.addSpacerItem(add_spacer(20, direction='vert'))
        groupByWidgetLayout.addWidget(self.groupDisableWidget)

        # variable to store actual checkbox objects for the groupby. orderedDict so grouping can be in order
        self.groupByFields = collections.OrderedDict()

        # endregion Grouping section

        # region filtering section
        self.filterGrid = QFormLayout()
        self.filterGrid.setObjectName("filterGrid")
        self.filterGrid.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.filterGrid.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.filterGrid.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        # self.filterGrid.setSizeConstraint(QLayout.SetFixedSize)

        self.filterByWidget = QWidget()
        self.filterByWidget.setLayout(self.filterGrid)
        self.filterByWidget.setSizePolicy(sizePolicy_minEx)
        # endregion filtering section

        # region Field selection section
        self.fieldGrid = QGridLayout()
        self.fieldGrid.setObjectName("fieldGrid")
        self.fieldGrid.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.fieldScroll = QScrollArea()
        self.fieldScroll.setSizePolicy(sizePolicy_exp)
        self.fieldScroll.setMinimumSize(QtCore.QSize(100, 150))
        self.fieldScroll.setMaximumSize(QtCore.QSize(self.optionWidth, 500))
        self.fieldScroll.setWidgetResizable(True)

        self.fieldList = QVBoxLayout()
        self.fieldList.setObjectName("fieldList")
        self.fieldList.setSpacing(0)

        self.fieldWidget = QWidget()
        self.fieldWidget.setSizePolicy(sizePolicy_exp)
        self.fieldWidget.setMaximumWidth(self.optionWidth)

        self.fieldWidget.setLayout(self.fieldList)
        self.fieldScroll.setWidget(self.fieldWidget)

        # region Select All/None buttons
        self.fieldListSelectAll = QPushButton(stats_window)
        self.fieldListSelectAll.setMinimumSize(QtCore.QSize(50, 27))
        self.fieldListSelectAll.setMaximumSize(QtCore.QSize(self.optionWidth, 27))
        self.fieldListSelectAll.setSizePolicy(sizePolicy_exp)
        self.fieldListSelectNone = QPushButton(stats_window)
        self.fieldListSelectNone.setMinimumSize(QtCore.QSize(50, 27))
        self.fieldListSelectNone.setMaximumSize(QtCore.QSize(self.optionWidth, 27))
        self.fieldListSelectNone.setSizePolicy(sizePolicy_exp)
        # endregion Select All/None buttons

        self.fieldSelectWidget = QWidget()
        self.fieldSelectWidget.setLayout(self.fieldGrid)
        # endregion Field selection section

        # region Preset Options
        self.presetsGrid = QFormLayout()
        self.presetsGrid.setObjectName("presetsGrid")
        self.presetsGrid.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.presetsGrid.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)

        # region Specific presets
        # Use only trials where subject responded, or include all trials?
        self.noResponse_Checkbox = QCheckBox(stats_window)
        self.noResponse_Checkbox.setSizePolicy(sizePolicy_fixed)
        self.noResponse_Checkbox.setMaximumSize(QtCore.QSize(27, 27))
        self.noResponse_Checkbox.setObjectName("noResponse_Checkbox")
        self.noResponse_Checkbox.setCheckState(2)

        # Analyze probe trials as well?
        self.probe_Checkbox = QCheckBox(stats_window)
        self.probe_Checkbox.setSizePolicy(sizePolicy_fixed)
        self.probe_Checkbox.setMaximumSize(QtCore.QSize(27, 27))
        self.probe_Checkbox.setObjectName("probe_Checkbox")
        self.probe_Checkbox.setCheckState(2)  # default to on

        # Include raw counts
        self.raw_Checkbox = QCheckBox(stats_window)
        self.raw_Checkbox.setSizePolicy(sizePolicy_fixed)
        self.raw_Checkbox.setMaximumSize(QtCore.QSize(27, 27))
        self.raw_Checkbox.setObjectName("raw_Checkbox")
        # endregion

        self.presetsGrid.addRow(QLabel("Include NR Trials"), self.noResponse_Checkbox)
        self.presetsGrid.addRow(QLabel("Include Probe Trials"), self.probe_Checkbox)
        self.presetsGrid.addRow(QLabel("Include Raw Trial Counts"), self.raw_Checkbox)
        self.presetsWidget = QWidget()
        self.presetsWidget.setLayout(self.presetsGrid)
        # endregion Preset Options

        # region Menu buttons at bottom
        self.menuGrid = QHBoxLayout()
        self.menuGrid.setObjectName("menuGrid")

        self.folder_Button = QPushButton(stats_window)
        self.folder_Button.setSizePolicy(sizePolicy_fixed)
        self.folder_Button.setMinimumSize(QtCore.QSize(150, 27))
        self.folder_Button.setMaximumSize(QtCore.QSize(300, 27))
        self.folder_Button.setObjectName("folder_Button")

        # button to force a recalculation
        self.recalculate_Button = QPushButton(stats_window)
        self.recalculate_Button.setSizePolicy(sizePolicy_fixed)
        self.recalculate_Button.setMinimumSize(QtCore.QSize(150, 27))
        self.recalculate_Button.setMaximumSize(QtCore.QSize(300, 27))
        self.recalculate_Button.setObjectName("recalculate_Button")

        # if hold checkbox is on, changing field/grouping/filters won't force a recalculate, so multiple things can
        # be changed without needing to wait after each click
        self.hold_Checkbox = QCheckBox(stats_window)
        self.hold_Checkbox.setSizePolicy(sizePolicy_fixed)
        self.hold_Checkbox.setText('Automatically recalculate')
        self.hold_Checkbox.setFixedHeight(27)
        self.hold_Checkbox.setMaximumWidth(300)
        self.hold_Checkbox.setObjectName("hold_Checkbox")

        self.export_Button = QPushButton(stats_window)
        self.export_Button.setSizePolicy(sizePolicy_fixed)
        self.export_Button.setMinimumSize(QtCore.QSize(150, 27))
        self.export_Button.setMaximumSize(QtCore.QSize(300, 27))
        self.export_Button.setObjectName("export_Button")

        self.done_Button = QPushButton(stats_window)
        self.done_Button.setSizePolicy(sizePolicy_fixed)
        self.done_Button.setMinimumSize(QtCore.QSize(150, 27))
        self.done_Button.setMaximumSize(QtCore.QSize(300, 27))
        self.done_Button.setObjectName("done_Button")

        self.menuGrid.addWidget(self.folder_Button)

        self.menuGrid.addSpacerItem(add_spacer(100))

        self.menuGrid.addWidget(self.recalculate_Button)
        self.menuGrid.addWidget(self.hold_Checkbox)

        self.menuGrid.addSpacerItem(add_spacer(100))

        self.menuGrid.addWidget(self.export_Button)
        self.menuGrid.addWidget(self.done_Button)
        # endregion Menu buttons at bottom

        """
            # Layout schematic

                            0                  	     1	    
             ┌──────────────────────────╔═══════════════════════════╗
            0│performance_table    	    ║groupGrid  (optionToolbox) ║
             │                          ╟───────────────────────────╢
             │                          ║filterGrid                 ║
             │──────────────────────────╟───────────────────────────╢
            1│tableStatsBar                 ║fieldGrid                  ║
             ├──────────────────────────╚═══════════════════════════╝
            2│menuGrid                                              │
             └──────────────────────────────────────────────────────┘
             
             ┬┴├┤─│┼┌┐└┘  ╔╗╚╝╟╢╧╤╫╪═║
             row, column
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
        self.gridLayout.addWidget(self.optionToolbox, 0, 1, 2, 1)
        self.gridLayout.addLayout(self.menuGrid, 2, 0, 1, 2)

        self.gridLayout.addWidget(self.tableStatsBar, 1, 0, 1, 1)
        # endregion Object placement

        self.retranslate_ui(stats_window)
        # QtCore.QMetaObject.connectSlotsByName(stats_window)

    def retranslate_ui(self, stats_window):
        stats_window.setWindowTitle("stats_window", "Performance", None)
        self.folder_Button.setText("stats_window", "Select...", None)
        self.recalculate_Button.setText("stats_window", "Recalculate", None)
        self.export_Button.setText("stats_window", "Export", None)
        self.done_Button.setText("stats_window", "Done", None)
        self.noResponse_Checkbox.setText("stats_window", "", None)
        self.probe_Checkbox.setText("stats_window", "", None)
        self.raw_Checkbox.setText("stats_window", "", None)
        self.fieldListSelectAll.setText("stats_window", "Select All", None)
        self.fieldListSelectNone.setText("stats_window", "Select None", None)


class FolderSelectWindow(object):
    def __init__(self):
        self.done_button = None
        self.cancel_button = None
        self.change_folder_button = None
        self.menuBar = None
        self.folder_view = None
        self.gridLayout = None

    def setup_ui(self, folder_window):
        folder_window.setObjectName("folder_select_window")
        folder_window.resize(500, 400)
        sizePolicy_fixed = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy_fixed.setHorizontalStretch(0)
        sizePolicy_fixed.setVerticalStretch(0)
        sizePolicy_exp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy_exp.setHorizontalStretch(0)
        sizePolicy_exp.setVerticalStretch(0)

        folder_window.setSizePolicy(sizePolicy_exp)
        font = QtGui.QFont()
        font.setPointSize(11)

        self.gridLayout = QGridLayout(folder_window)
        self.gridLayout.setObjectName("gridLayout")

        self.folder_view = QTreeView(folder_window)
        self.folder_view.setSizePolicy(sizePolicy_exp)
        self.folder_view.setMinimumSize(QtCore.QSize(500, 300))
        self.folder_view.setFont(font)
        self.folder_view.setAnimated(False)
        self.folder_view.setObjectName("folder_view")

        # region Menu buttons at bottom
        self.menuBar = QHBoxLayout()
        self.menuBar.setObjectName("menuBar")

        self.change_folder_button = QPushButton(folder_window)
        self.change_folder_button.setSizePolicy(sizePolicy_fixed)
        self.change_folder_button.setMaximumSize(QtCore.QSize(300, 27))
        self.change_folder_button.setObjectName("change_folder_button")

        self.cancel_button = QPushButton(folder_window)
        self.cancel_button.setSizePolicy(sizePolicy_fixed)
        self.cancel_button.setMaximumSize(QtCore.QSize(300, 27))
        self.cancel_button.setObjectName("cancel_button")

        self.done_button = QPushButton(folder_window)
        self.done_button.setSizePolicy(sizePolicy_fixed)
        self.done_button.setMaximumSize(QtCore.QSize(300, 27))
        self.done_button.setObjectName("done_button")

        self.menuBar.addWidget(self.change_folder_button)
        self.menuBar.addSpacerItem(add_spacer(40, policy='min'))
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
        stats_window.setWindowTitle("stats_window", "Select Folder", None)
        self.done_button.setText("stats_window", "Done", None)
        self.cancel_button.setText("stats_window", "Cancel", None)
        self.change_folder_button.setText("stats_window", "Select Base Folder", None)


def add_spacer(pref_width, pref_height=20, direction='horiz', policy='exp'):
    """
    Simple method for creating a spacer item that doesn't need to be referred to later

    :param direction: horiz or vert
    :param pref_width: Preferred width of spacer item
    :param pref_height: Preferred height of spacer item. Default is 20
    :param policy: Size policy. 'exp' for MinimumExpanding (default), 'min' for Minimum
    :return: QSpacerItem
    """
    size_minExp = QSizePolicy.MinimumExpanding
    size_min = QSizePolicy.Minimum

    if policy == 'exp':
        if direction == 'vert':
            spacer = QSpacerItem(pref_width, pref_height, size_min, size_minExp)
        else:
            spacer = QSpacerItem(pref_width, pref_height, size_minExp, size_min)
    else:
        # minimum, direction only specified in given dimensions
        spacer = QSpacerItem(pref_width, pref_height, size_min, size_min)
    return spacer
