# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'solenoid_control.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

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


class UiSolenoidControl(object):
    def setup_ui(self, solenoid_control):
        solenoid_control.setObjectName(_fromUtf8("solenoid_control"))
        solenoid_control.resize(300, 185)
        sizePolicy_fixed = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy_fixed.setHorizontalStretch(0)
        sizePolicy_fixed.setVerticalStretch(0)
        sizePolicy_max = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        sizePolicy_max.setHorizontalStretch(0)
        sizePolicy_max.setVerticalStretch(0)

        solenoid_control.setSizePolicy(sizePolicy_fixed)
        solenoid_control.setMaximumSize(QtCore.QSize(300, 200))

        self.gridLayout = QtGui.QGridLayout(solenoid_control)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))

        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))

        self.box_name = QtGui.QLabel(solenoid_control)
        self.box_name.setSizePolicy(sizePolicy_max)
        self.box_name.setMaximumSize(QtCore.QSize(280, 24))
        self.box_name.setBaseSize(QtCore.QSize(50, 18))
        font = QtGui.QFont()
        font.setPointSize(13)
        self.box_name.setFont(font)
        self.box_name.setAlignment(QtCore.Qt.AlignCenter)
        self.box_name.setObjectName(_fromUtf8("box_name"))

        self.solenoid_text = QtGui.QLabel(solenoid_control)
        self.solenoid_text.setSizePolicy(sizePolicy_fixed)
        self.solenoid_text.setMaximumSize(QtCore.QSize(280, 24))
        self.solenoid_text.setAlignment(QtCore.Qt.AlignCenter)
        self.solenoid_text.setObjectName(_fromUtf8("solenoid_text"))

        self.solenoid_Status_Text = QtGui.QLabel(solenoid_control)
        self.solenoid_Status_Text.setSizePolicy(sizePolicy_fixed)
        self.solenoid_Status_Text.setMinimumSize(QtCore.QSize(0, 17))
        self.solenoid_Status_Text.setMaximumSize(QtCore.QSize(280, 24))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.solenoid_Status_Text.setFont(font)
        self.solenoid_Status_Text.setAlignment(QtCore.Qt.AlignCenter)
        self.solenoid_Status_Text.setObjectName(_fromUtf8("solenoid_Status_Text"))
        spacerItem = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)

        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))

        self.open_Button = QtGui.QPushButton(solenoid_control)
        self.open_Button.setMinimumSize(QtCore.QSize(0, 27))
        self.open_Button.setMaximumSize(QtCore.QSize(136, 27))
        self.open_Button.setObjectName(_fromUtf8("open_Button"))

        self.close_Button = QtGui.QPushButton(solenoid_control)
        self.close_Button.setEnabled(False)
        self.close_Button.setMinimumSize(QtCore.QSize(0, 27))
        self.close_Button.setMaximumSize(QtCore.QSize(136, 27))
        self.close_Button.setObjectName(_fromUtf8("close_Button"))

        self.line = QtGui.QFrame(solenoid_control)
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.done_Button = QtGui.QPushButton(solenoid_control)
        self.done_Button.setSizePolicy(sizePolicy_fixed)
        self.done_Button.setMaximumSize(QtCore.QSize(270, 27))
        self.done_Button.setObjectName(_fromUtf8("done_Button"))

        self.horizontalLayout.addWidget(self.open_Button)
        self.horizontalLayout.addWidget(self.close_Button)

        self.verticalLayout.addWidget(self.box_name)
        self.verticalLayout.addWidget(self.solenoid_text)
        self.verticalLayout.addWidget(self.solenoid_Status_Text)
        self.verticalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.line)
        self.verticalLayout.addWidget(self.done_Button)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 2, 2)

        self.retranslate_ui(solenoid_control)
        QtCore.QMetaObject.connectSlotsByName(solenoid_control)

    def retranslate_ui(self, solenoid_control):
        solenoid_control.setWindowTitle(_translate("solenoid_control", "Solenoid Control", None))
        self.box_name.setText(_translate("solenoid_control", "Box ", None))
        self.solenoid_text.setText(_translate("solenoid_control", "Solenoid is ", None))
        self.solenoid_Status_Text.setText(_translate("solenoid_control", "CLOSED", None))
        self.open_Button.setText(_translate("solenoid_control", "Open Solenoid", None))
        self.close_Button.setText(_translate("solenoid_control", "Close Solenoid", None))
        self.done_Button.setText(_translate("solenoid_control", "Done", None))

