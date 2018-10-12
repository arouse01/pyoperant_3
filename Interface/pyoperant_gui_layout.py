# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'untitled_2.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

# Much of the core code (of creating each of the sections) could probably made more dynamic to allow the user to
# specify the desired number of boxes

from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
import math

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


class UiMainWindow(object):
    def setup_ui(self, main_window):

        self.startBoxList = []
        self.stopBoxList = []
        self.paramFileButtonBoxList = []
        self.checkActiveBoxList = []
        self.statusTextBoxList = []
        self.paramFileBoxList = []
        self.graphicBoxList = []
        self.birdEntryBoxList = []
        self.paramFileLabelBoxList = []
        self.birdEntryLabelBoxList = []
        self.gridLayoutBoxList = []
        self.labelBoxList = []
        self.checkActiveLabelBoxList = []
        self.optionButtonBoxList = []
        self.lineList = []

        self.greenIcon = QPixmap("green_circle.svg")
        self.redIcon = QPixmap("red_stop.svg")
        self.wrenchIcon = QIcon()
        self.wrenchIcon.addPixmap(QtGui.QPixmap(_fromUtf8("icons/wrench.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        # Object location-specific variables
        self.numberOfBoxes = 6

        # Calculate box arrangement in window
        # rowCount = math.floor(math.sqrt(self.numberOfBoxes))
        rowCount = 3
        columnCount = self.numberOfBoxes / rowCount
        numHorizontalLines = self.numberOfBoxes
        numVerticalLines = columnCount - 1

        # Make main window
        main_window.setObjectName(_fromUtf8("main_window"))

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        main_window.setSizePolicy(sizePolicy)
        # main_window.setMaximumSize(QtCore.QSize(1200, 1000))
        self.centralwidget = QtGui.QWidget(main_window)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.centralwidget.setSizePolicy(sizePolicy)
        # self.centralwidget.setMaximumSize(QtCore.QSize(2000, 2000))
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))

        self.gridLayoutWidget = QtGui.QWidget(self.centralwidget)
        self.gridLayoutWidget.setObjectName(_fromUtf8("gridLayoutWidget"))
        self.mainGrid = QtGui.QGridLayout(self.gridLayoutWidget)
        self.mainGrid.setObjectName(_fromUtf8("mainGrid"))

        # Menu at bottom of screen
        self.menuGrid = QtGui.QGridLayout()
        self.menuGrid.setObjectName(_fromUtf8("menuGrid"))
        self.stopAllButton = QtGui.QPushButton(self.gridLayoutWidget)
        self.stopAllButton.setObjectName(_fromUtf8("stopAllButton"))
        self.startAllButton = QtGui.QPushButton(self.gridLayoutWidget)
        self.startAllButton.setObjectName(_fromUtf8("startAllButton"))
        self.menuGrid.addWidget(self.stopAllButton, 0, 0, 1, 1)
        self.menuGrid.addWidget(self.startAllButton, 0, 1, 1, 1)
        self.behaviorField = QtGui.QComboBox(self.gridLayoutWidget)
        self.behaviorField.setMinimumSize(QtCore.QSize(200, 0))
        self.behaviorField.setMaximumSize(QtCore.QSize(300, 30))
        self.behaviorField.setObjectName(_fromUtf8("behaviorField"))
        self.behaviorField.addItem(_fromUtf8(""))
        self.menuGrid.addWidget(self.behaviorField, 0, 4, 1, 1)
        self.behaviorLabel = QtGui.QLabel(self.gridLayoutWidget)
        self.behaviorLabel.setMinimumSize(QtCore.QSize(70, 0))
        self.behaviorLabel.setMaximumSize(QtCore.QSize(80, 80))
        self.behaviorLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.behaviorLabel.setObjectName(_fromUtf8("behaviorLabel"))
        self.menuGrid.addWidget(self.behaviorLabel, 0, 3, 1, 1)
        self.menuGrid.addItem(QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 0, 2,
                              1, 1)
        self.mainGrid.addLayout(self.menuGrid, 2*rowCount, 0, 1, 2*columnCount-1)

        ### Layout dividing lines
        for i in range(0, numHorizontalLines):  # Horizontal lines
            self.lineList.append(QtGui.QFrame(self.gridLayoutWidget))
            self.lineList[i].setFrameShape(QtGui.QFrame.HLine)
            self.lineList[i].setFrameShadow(QtGui.QFrame.Sunken)
            self.lineList[i].setObjectName(_fromUtf8("hline_%d" % i))
            self.mainGrid.addWidget(self.lineList[i], 2 * math.floor(i / columnCount) + 1, 2 * (i % columnCount), 1,
                                    1)

        for i in range(numHorizontalLines, self.numberOfBoxes + int(numVerticalLines)):  # Vertical lines
            self.lineList.append(QtGui.QFrame(self.gridLayoutWidget))
            self.lineList[i].setFrameShadow(QtGui.QFrame.Plain)
            self.lineList[i].setLineWidth(2)
            self.lineList[i].setMidLineWidth(0)
            self.lineList[i].setFrameShape(QtGui.QFrame.VLine)
            self.lineList[i].setObjectName(_fromUtf8("vline_%d" % i))
            self.mainGrid.addWidget(self.lineList[i], 0, (i - numHorizontalLines) * 2 + 1, 2 * rowCount, 1)

        ### Individual section elements
        for box in range(0, self.numberOfBoxes):
            # Object placement
            self.gridLayoutBoxList.append(QtGui.QGridLayout())
            self.birdEntryLabelBoxList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.birdEntryBoxList.append(QtGui.QPlainTextEdit(self.gridLayoutWidget))
            self.checkActiveBoxList.append(QtGui.QCheckBox(self.gridLayoutWidget))
            self.checkActiveLabelBoxList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.graphicBoxList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.labelBoxList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.paramFileLabelBoxList.append(QtGui.QLabel(self.gridLayoutWidget))
            self.paramFileButtonBoxList.append(QtGui.QPushButton(self.gridLayoutWidget))
            self.paramFileBoxList.append(QtGui.QTextEdit(self.gridLayoutWidget))
            self.optionButtonBoxList.append(QtGui.QToolButton(self.gridLayoutWidget))
            self.startBoxList.append(QtGui.QPushButton(self.gridLayoutWidget))
            self.statusTextBoxList.append(QtGui.QTextBrowser(self.gridLayoutWidget))
            self.stopBoxList.append(QtGui.QPushButton(self.gridLayoutWidget))
            self.mainGrid.addLayout(self.gridLayoutBoxList[box], 2 * (box % rowCount), 2 * math.floor(box / rowCount),
                                    1, 1)

            # Formatting
            self.stopBoxList[box].setEnabled(False)
            sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Maximum)
            sizePolicy.setHorizontalStretch(1)
            sizePolicy.setVerticalStretch(1)
            font = QtGui.QFont()
            font.setPointSize(11)
            self.birdEntryBoxList[box].setFont(font)
            self.birdEntryBoxList[box].setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.birdEntryBoxList[box].setMaximumSize(QtCore.QSize(200, 26))
            self.birdEntryBoxList[box].setObjectName(_fromUtf8("birdEntry_Box%d" % box))
            self.birdEntryBoxList[box].setPlainText(_fromUtf8(""))
            self.birdEntryBoxList[box].setSizePolicy(sizePolicy)
            self.birdEntryBoxList[box].setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.birdEntryLabelBoxList[box].setAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
            self.birdEntryLabelBoxList[box].setMaximumSize(QtCore.QSize(500, 26))
            self.birdEntryLabelBoxList[box].setObjectName(_fromUtf8("birdEntryLabel_Box%d" % box))
            self.birdEntryLabelBoxList[box].setSizePolicy(sizePolicy)
            self.checkActiveBoxList[box].setIconSize(QtCore.QSize(20, 20))
            self.checkActiveBoxList[box].setMaximumSize(QtCore.QSize(22, 22))
            self.checkActiveBoxList[box].setObjectName(_fromUtf8("checkActive_Box%d" % box))
            self.checkActiveBoxList[box].setText(_fromUtf8(""))
            self.checkActiveLabelBoxList[box].setAlignment(QtCore.Qt.AlignCenter)
            self.checkActiveLabelBoxList[box].setObjectName(_fromUtf8("checkActiveLabel_Box%d" % box))
            self.graphicBoxList[box].setAlignment(QtCore.Qt.AlignCenter)
            self.graphicBoxList[box].setFrameShadow(QtGui.QFrame.Sunken)
            self.graphicBoxList[box].setFrameShape(QtGui.QFrame.Panel)
            self.graphicBoxList[box].setMargin(2)
            self.graphicBoxList[box].setMaximumSize(QtCore.QSize(35, 35))
            self.graphicBoxList[box].setObjectName(_fromUtf8("graphicLabel_Box%d" % box))
            self.graphicBoxList[box].setPixmap(self.redIcon)
            self.graphicBoxList[box].setScaledContents(True)
            self.graphicBoxList[box].setText(_fromUtf8(""))
            self.graphicBoxList[box].setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
            self.gridLayoutBoxList[box].addItem(
                QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 1, 1, 1, 1)
            self.gridLayoutBoxList[box].addItem(
                QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 3, 1, 1, 1)
            self.gridLayoutBoxList[box].addItem(
                QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 6, 1, 1, 1)
            self.gridLayoutBoxList[box].addWidget(self.labelBoxList[box], 0, 1, 1, 1, QtCore.Qt.AlignHCenter)
            self.gridLayoutBoxList[box].addWidget(self.statusTextBoxList[box], 0, 2, 7, 3)
            self.gridLayoutBoxList[box].addWidget(self.graphicBoxList[box], 2, 1, 1, 1, QtCore.Qt.AlignHCenter)
            self.gridLayoutBoxList[box].addWidget(self.checkActiveBoxList[box], 4, 1, 1, 1, QtCore.Qt.AlignHCenter)
            self.gridLayoutBoxList[box].addWidget(self.checkActiveLabelBoxList[box], 5, 1, 1, 1, QtCore.Qt.AlignHCenter)
            self.gridLayoutBoxList[box].addWidget(self.paramFileBoxList[box], 7, 2, 1, 2)
            self.gridLayoutBoxList[box].addWidget(self.paramFileButtonBoxList[box], 7, 4, 1, 1)
            self.gridLayoutBoxList[box].addWidget(self.paramFileLabelBoxList[box], 7, 1, 1, 1)
            self.gridLayoutBoxList[box].addWidget(self.birdEntryBoxList[box], 8, 2, 1, 2)
            self.gridLayoutBoxList[box].addWidget(self.birdEntryLabelBoxList[box], 8, 1, 1, 1)
            self.gridLayoutBoxList[box].addWidget(self.startBoxList[box], 9, 3, 1, 1,
                                                  QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            self.gridLayoutBoxList[box].addWidget(self.stopBoxList[box], 9, 2, 1, 1,
                                                  QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            self.gridLayoutBoxList[box].addWidget(self.optionButtonBoxList[box], 9, 4, 1, 1,
                                                  QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            self.gridLayoutBoxList[box].setObjectName(_fromUtf8("gridLayout_Box%d" % box))
            self.gridLayoutBoxList[box].setSpacing(6)
            self.labelBoxList[box].setObjectName(_fromUtf8("label_Box%d" % box))
            self.paramFileBoxList[box].setFont(font)
            self.paramFileBoxList[box].setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.paramFileBoxList[box].setMaximumSize(QtCore.QSize(200, 26))
            self.paramFileBoxList[box].setObjectName(_fromUtf8("paramFile_Box%d" % box))
            self.paramFileBoxList[box].setSizePolicy(sizePolicy)
            self.paramFileBoxList[box].setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.paramFileButtonBoxList[box].setMaximumSize(QtCore.QSize(26, 26))
            self.paramFileButtonBoxList[box].setObjectName(_fromUtf8("paramFileButton_Box%d" % box))
            self.paramFileButtonBoxList[box].setSizePolicy(sizePolicy)
            self.optionButtonBoxList[box].setMaximumSize(QtCore.QSize(26, 26))
            self.optionButtonBoxList[box].setObjectName(_fromUtf8("optionButton_Box%d" % box))
            self.optionButtonBoxList[box].setSizePolicy(sizePolicy)
            self.optionButtonBoxList[box].setIcon(self.wrenchIcon)
            self.optionButtonBoxList[box].setMinimumSize(QtCore.QSize(26, 26))
            self.optionButtonBoxList[box].setMaximumSize(QtCore.QSize(26, 26))
            self.optionButtonBoxList[box].setPopupMode(2)
            self.optionButtonBoxList[box].setArrowType(0)
            self.optionButtonBoxList[box].setText(_fromUtf8(""))
            self.paramFileLabelBoxList[box].setAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
            self.paramFileLabelBoxList[box].setMaximumSize(QtCore.QSize(500, 26))
            self.paramFileLabelBoxList[box].setObjectName(_fromUtf8("paramFileLabel_Box%d" % box))
            self.paramFileLabelBoxList[box].setSizePolicy(sizePolicy)
            self.startBoxList[box].setMaximumSize(QtCore.QSize(100, 16777215))
            self.startBoxList[box].setObjectName(_fromUtf8("start_Box1"))
            self.statusTextBoxList[box].setMaximumSize(QtCore.QSize(230, 250))
            self.statusTextBoxList[box].setObjectName(_fromUtf8("statusText_Box%d" % box))
            self.stopBoxList[box].setMaximumSize(QtCore.QSize(100, 16777215))
            self.stopBoxList[box].setObjectName(_fromUtf8("stop_Box%d" % box))

        main_window.setCentralWidget(self.centralwidget)

        # Set window and grid size based on content
        mainGridWidth = math.floor(self.gridLayoutWidget.sizeHint().width()*1.0375)
        mainGridHeight = self.gridLayoutWidget.sizeHint().height()

        # horizWindow = 300 * columnCount
        # vertWindow = 300 * rowCount + 100
        main_window.setFixedSize(mainGridWidth, mainGridHeight)

        self.retranslate_ui(main_window)
        QtCore.QMetaObject.connectSlotsByName(main_window)

    def retranslate_ui(self, mainwindow):
        mainwindow.setWindowTitle(_translate("MainWindow", "pyoperant Interface", None))
        self.startAllButton.setText(_translate("MainWindow", "Start All", None))
        self.stopAllButton.setText(_translate("MainWindow", "Stop All", None))
        self.behaviorField.setItemText(0, _translate("MainWindow", "GoNoGoInterruptExp", None))
        self.behaviorLabel.setText(_translate("MainWindow", "Paradigm", None))

        for box in range(0, self.numberOfBoxes):
            self.birdEntryLabelBoxList[box].setText(_translate("MainWindow", "Bird", None))
            self.checkActiveLabelBoxList[box].setText(_translate("MainWindow", "Active", None))
            self.labelBoxList[box].setText(_translate("MainWindow", _fromUtf8("Box %s" % str(box + 1)), None))
            self.paramFileButtonBoxList[box].setText(_translate("MainWindow", "...", None))
            self.paramFileLabelBoxList[box].setText(_translate("MainWindow", "File", None))
            self.startBoxList[box].setText(_translate("MainWindow", "Start", None))
            self.stopBoxList[box].setText(_translate("MainWindow", "Stop", None))
