# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\ConnectionToMainDatabaseDialog.ui'
#
# Created: Wed May 11 15:50:18 2016
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

class Ui_ConnectionToMainDatabaseDialog(object):
    def setupUi(self, ConnectionToMainDatabaseDialog):
        ConnectionToMainDatabaseDialog.setObjectName(_fromUtf8("ConnectionToMainDatabaseDialog"))
        ConnectionToMainDatabaseDialog.resize(320, 310)
        ConnectionToMainDatabaseDialog.setMinimumSize(QtCore.QSize(320, 310))
        ConnectionToMainDatabaseDialog.setMaximumSize(QtCore.QSize(320, 310))
        ConnectionToMainDatabaseDialog.setBaseSize(QtCore.QSize(320, 310))
        self.server_name_edit = QtGui.QLineEdit(ConnectionToMainDatabaseDialog)
        self.server_name_edit.setGeometry(QtCore.QRect(60, 56, 200, 20))
        self.server_name_edit.setObjectName(_fromUtf8("server_name_edit"))
        self.port_edit = QtGui.QLineEdit(ConnectionToMainDatabaseDialog)
        self.port_edit.setGeometry(QtCore.QRect(60, 96, 200, 20))
        self.port_edit.setObjectName(_fromUtf8("port_edit"))
        self.database_edit = QtGui.QLineEdit(ConnectionToMainDatabaseDialog)
        self.database_edit.setGeometry(QtCore.QRect(60, 136, 200, 20))
        self.database_edit.setObjectName(_fromUtf8("database_edit"))
        self.user_name_edit = QtGui.QLineEdit(ConnectionToMainDatabaseDialog)
        self.user_name_edit.setGeometry(QtCore.QRect(60, 176, 200, 20))
        self.user_name_edit.setObjectName(_fromUtf8("user_name_edit"))
        self.label = QtGui.QLabel(ConnectionToMainDatabaseDialog)
        self.label.setGeometry(QtCore.QRect(60, 36, 200, 17))
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(ConnectionToMainDatabaseDialog)
        self.label_2.setGeometry(QtCore.QRect(60, 76, 200, 17))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.label_3 = QtGui.QLabel(ConnectionToMainDatabaseDialog)
        self.label_3.setGeometry(QtCore.QRect(60, 116, 200, 17))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.label_4 = QtGui.QLabel(ConnectionToMainDatabaseDialog)
        self.label_4.setGeometry(QtCore.QRect(60, 156, 200, 17))
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.ok_button = QtGui.QPushButton(ConnectionToMainDatabaseDialog)
        self.ok_button.setGeometry(QtCore.QRect(153, 265, 70, 23))
        self.ok_button.setObjectName(_fromUtf8("ok_button"))
        self.cancel_button = QtGui.QPushButton(ConnectionToMainDatabaseDialog)
        self.cancel_button.setGeometry(QtCore.QRect(230, 265, 70, 23))
        self.cancel_button.setObjectName(_fromUtf8("cancel_button"))
        self.line = QtGui.QFrame(ConnectionToMainDatabaseDialog)
        self.line.setGeometry(QtCore.QRect(0, 20, 321, 20))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.line_2 = QtGui.QFrame(ConnectionToMainDatabaseDialog)
        self.line_2.setGeometry(QtCore.QRect(0, 290, 321, 16))
        self.line_2.setFrameShape(QtGui.QFrame.HLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName(_fromUtf8("line_2"))
        self.label_5 = QtGui.QLabel(ConnectionToMainDatabaseDialog)
        self.label_5.setGeometry(QtCore.QRect(10, 10, 371, 17))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.help_button = QtGui.QPushButton(ConnectionToMainDatabaseDialog)
        self.help_button.setGeometry(QtCore.QRect(110, 265, 30, 23))
        self.help_button.setText(_fromUtf8(""))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/lm2/help_button.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.help_button.setIcon(icon)
        self.help_button.setObjectName(_fromUtf8("help_button"))
        self.password_edit = QtGui.QLineEdit(ConnectionToMainDatabaseDialog)
        self.password_edit.setGeometry(QtCore.QRect(60, 216, 200, 20))
        self.password_edit.setEchoMode(QtGui.QLineEdit.Password)
        self.password_edit.setObjectName(_fromUtf8("password_edit"))
        self.label_6 = QtGui.QLabel(ConnectionToMainDatabaseDialog)
        self.label_6.setGeometry(QtCore.QRect(60, 196, 200, 16))
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.error_label = QtGui.QLabel(ConnectionToMainDatabaseDialog)
        self.error_label.setGeometry(QtCore.QRect(20, 240, 291, 16))
        self.error_label.setText(_fromUtf8(""))
        self.error_label.setObjectName(_fromUtf8("error_label"))
        self.connect_label = QtGui.QLabel(ConnectionToMainDatabaseDialog)
        self.connect_label.setGeometry(QtCore.QRect(60, 240, 241, 16))
        self.connect_label.setText(_fromUtf8(""))
        self.connect_label.setObjectName(_fromUtf8("connect_label"))

        self.retranslateUi(ConnectionToMainDatabaseDialog)
        QtCore.QMetaObject.connectSlotsByName(ConnectionToMainDatabaseDialog)
        ConnectionToMainDatabaseDialog.setTabOrder(self.server_name_edit, self.port_edit)
        ConnectionToMainDatabaseDialog.setTabOrder(self.port_edit, self.database_edit)
        ConnectionToMainDatabaseDialog.setTabOrder(self.database_edit, self.user_name_edit)
        ConnectionToMainDatabaseDialog.setTabOrder(self.user_name_edit, self.password_edit)
        ConnectionToMainDatabaseDialog.setTabOrder(self.password_edit, self.ok_button)
        ConnectionToMainDatabaseDialog.setTabOrder(self.ok_button, self.help_button)
        ConnectionToMainDatabaseDialog.setTabOrder(self.help_button, self.cancel_button)

    def retranslateUi(self, ConnectionToMainDatabaseDialog):
        ConnectionToMainDatabaseDialog.setWindowTitle(_translate("ConnectionToMainDatabaseDialog", "Dialog", None))
        self.label.setText(_translate("ConnectionToMainDatabaseDialog", "Server Name / IP Address", None))
        self.label_2.setText(_translate("ConnectionToMainDatabaseDialog", "Port", None))
        self.label_3.setText(_translate("ConnectionToMainDatabaseDialog", "Database", None))
        self.label_4.setText(_translate("ConnectionToMainDatabaseDialog", "User Name", None))
        self.ok_button.setText(_translate("ConnectionToMainDatabaseDialog", "Ok", None))
        self.cancel_button.setText(_translate("ConnectionToMainDatabaseDialog", "Cancel", None))
        self.label_5.setText(_translate("ConnectionToMainDatabaseDialog", "Connection To Main Database (Working DB)", None))
        self.label_6.setText(_translate("ConnectionToMainDatabaseDialog", "Password", None))

import resources_rc
