# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\LogOnDialog.ui'
#
# Created: Tue Apr 19 10:46:17 2016
#      by: PyQt4 UI code generator 4.10.4
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

class Ui_LogOnDialog(object):
    def setupUi(self, LogOnDialog):
        LogOnDialog.setObjectName(_fromUtf8("LogOnDialog"))
        LogOnDialog.resize(300, 360)
        LogOnDialog.setMinimumSize(QtCore.QSize(300, 360))
        LogOnDialog.setMaximumSize(QtCore.QSize(300, 360))
        self.label = QtGui.QLabel(LogOnDialog)
        self.label.setGeometry(QtCore.QRect(10, 1, 191, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.line = QtGui.QFrame(LogOnDialog)
        self.line.setGeometry(QtCore.QRect(0, 20, 300, 3))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.label_2 = QtGui.QLabel(LogOnDialog)
        self.label_2.setGeometry(QtCore.QRect(40, 43, 200, 16))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.server_edit = QtGui.QLineEdit(LogOnDialog)
        self.server_edit.setGeometry(QtCore.QRect(40, 63, 200, 20))
        self.server_edit.setObjectName(_fromUtf8("server_edit"))
        self.label_3 = QtGui.QLabel(LogOnDialog)
        self.label_3.setGeometry(QtCore.QRect(40, 93, 200, 16))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.port_edit = QtGui.QLineEdit(LogOnDialog)
        self.port_edit.setGeometry(QtCore.QRect(40, 113, 200, 20))
        self.port_edit.setObjectName(_fromUtf8("port_edit"))
        self.database_edit = QtGui.QLineEdit(LogOnDialog)
        self.database_edit.setGeometry(QtCore.QRect(40, 163, 200, 20))
        self.database_edit.setObjectName(_fromUtf8("database_edit"))
        self.label_4 = QtGui.QLabel(LogOnDialog)
        self.label_4.setGeometry(QtCore.QRect(40, 143, 200, 16))
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.label_5 = QtGui.QLabel(LogOnDialog)
        self.label_5.setGeometry(QtCore.QRect(40, 193, 200, 16))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.user_edit = QtGui.QLineEdit(LogOnDialog)
        self.user_edit.setGeometry(QtCore.QRect(40, 213, 200, 20))
        self.user_edit.setObjectName(_fromUtf8("user_edit"))
        self.password_edit = QtGui.QLineEdit(LogOnDialog)
        self.password_edit.setGeometry(QtCore.QRect(40, 263, 200, 20))
        self.password_edit.setEchoMode(QtGui.QLineEdit.Password)
        self.password_edit.setObjectName(_fromUtf8("password_edit"))
        self.label_6 = QtGui.QLabel(LogOnDialog)
        self.label_6.setGeometry(QtCore.QRect(40, 243, 200, 16))
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.logon_button = QtGui.QPushButton(LogOnDialog)
        self.logon_button.setGeometry(QtCore.QRect(110, 313, 75, 23))
        self.logon_button.setObjectName(_fromUtf8("logon_button"))
        self.close_button = QtGui.QPushButton(LogOnDialog)
        self.close_button.setGeometry(QtCore.QRect(195, 313, 75, 23))
        self.close_button.setObjectName(_fromUtf8("close_button"))
        self.help_button = QtGui.QPushButton(LogOnDialog)
        self.help_button.setGeometry(QtCore.QRect(22, 313, 81, 23))
        self.help_button.setText(_fromUtf8(""))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/lm2/help_button.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.help_button.setIcon(icon)
        self.help_button.setObjectName(_fromUtf8("help_button"))
        self.line_2 = QtGui.QFrame(LogOnDialog)
        self.line_2.setGeometry(QtCore.QRect(0, 343, 300, 3))
        self.line_2.setFrameShape(QtGui.QFrame.HLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName(_fromUtf8("line_2"))

        self.retranslateUi(LogOnDialog)
        QtCore.QMetaObject.connectSlotsByName(LogOnDialog)
        LogOnDialog.setTabOrder(self.server_edit, self.port_edit)
        LogOnDialog.setTabOrder(self.port_edit, self.database_edit)
        LogOnDialog.setTabOrder(self.database_edit, self.user_edit)
        LogOnDialog.setTabOrder(self.user_edit, self.password_edit)
        LogOnDialog.setTabOrder(self.password_edit, self.logon_button)
        LogOnDialog.setTabOrder(self.logon_button, self.help_button)
        LogOnDialog.setTabOrder(self.help_button, self.close_button)

    def retranslateUi(self, LogOnDialog):
        LogOnDialog.setWindowTitle(_translate("LogOnDialog", "Log On To Database", None))
        self.label.setText(_translate("LogOnDialog", "Log On", None))
        self.label_2.setText(_translate("LogOnDialog", "Server Name / IP Address", None))
        self.label_3.setText(_translate("LogOnDialog", "Port", None))
        self.label_4.setText(_translate("LogOnDialog", "Database", None))
        self.label_5.setText(_translate("LogOnDialog", "User Name", None))
        self.label_6.setText(_translate("LogOnDialog", "Password", None))
        self.logon_button.setText(_translate("LogOnDialog", "Log On", None))
        self.close_button.setText(_translate("LogOnDialog", "Close", None))

import resources_rc
