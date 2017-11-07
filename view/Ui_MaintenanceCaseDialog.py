# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'MaintenanceCaseDialog.ui'
#
# Created: Tue Dec  2 16:46:54 2014
#      by: PyQt4 UI code generator 4.11.1
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

class Ui_MaintenanceCaseDialog(object):
    def setupUi(self, MaintenanceCaseDialog):
        MaintenanceCaseDialog.setObjectName(_fromUtf8("MaintenanceCaseDialog"))
        MaintenanceCaseDialog.resize(700, 450)
        MaintenanceCaseDialog.setMinimumSize(QtCore.QSize(700, 450))
        MaintenanceCaseDialog.setMaximumSize(QtCore.QSize(700, 450))
        self.label = QtGui.QLabel(MaintenanceCaseDialog)
        self.label.setGeometry(QtCore.QRect(21, 40, 91, 20))
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(MaintenanceCaseDialog)
        self.label_2.setGeometry(QtCore.QRect(20, 70, 121, 20))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.label_3 = QtGui.QLabel(MaintenanceCaseDialog)
        self.label_3.setGeometry(QtCore.QRect(360, 40, 121, 20))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.label_4 = QtGui.QLabel(MaintenanceCaseDialog)
        self.label_4.setGeometry(QtCore.QRect(20, 126, 121, 20))
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.label_5 = QtGui.QLabel(MaintenanceCaseDialog)
        self.label_5.setGeometry(QtCore.QRect(360, 72, 161, 20))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.label_6 = QtGui.QLabel(MaintenanceCaseDialog)
        self.label_6.setGeometry(QtCore.QRect(20, 96, 121, 20))
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.creation_date_edit = QtGui.QLineEdit(MaintenanceCaseDialog)
        self.creation_date_edit.setEnabled(False)
        self.creation_date_edit.setGeometry(QtCore.QRect(190, 40, 161, 21))
        self.creation_date_edit.setObjectName(_fromUtf8("creation_date_edit"))
        self.completion_date_edit = QtGui.QLineEdit(MaintenanceCaseDialog)
        self.completion_date_edit.setEnabled(False)
        self.completion_date_edit.setGeometry(QtCore.QRect(190, 68, 161, 21))
        self.completion_date_edit.setObjectName(_fromUtf8("completion_date_edit"))
        self.survey_date_edit = QtGui.QLineEdit(MaintenanceCaseDialog)
        self.survey_date_edit.setEnabled(False)
        self.survey_date_edit.setGeometry(QtCore.QRect(530, 42, 161, 21))
        self.survey_date_edit.setObjectName(_fromUtf8("survey_date_edit"))
        self.created_by_edit = QtGui.QLineEdit(MaintenanceCaseDialog)
        self.created_by_edit.setEnabled(False)
        self.created_by_edit.setGeometry(QtCore.QRect(190, 126, 161, 21))
        self.created_by_edit.setObjectName(_fromUtf8("created_by_edit"))
        self.surveyed_by_land_office_edit = QtGui.QLineEdit(MaintenanceCaseDialog)
        self.surveyed_by_land_office_edit.setEnabled(False)
        self.surveyed_by_land_office_edit.setGeometry(QtCore.QRect(530, 74, 161, 21))
        self.surveyed_by_land_office_edit.setObjectName(_fromUtf8("surveyed_by_land_office_edit"))
        self.completed_by_edit = QtGui.QLineEdit(MaintenanceCaseDialog)
        self.completed_by_edit.setEnabled(False)
        self.completed_by_edit.setGeometry(QtCore.QRect(190, 96, 161, 21))
        self.completed_by_edit.setObjectName(_fromUtf8("completed_by_edit"))
        self.maintenance_objects_twidget = QtGui.QTreeWidget(MaintenanceCaseDialog)
        self.maintenance_objects_twidget.setGeometry(QtCore.QRect(20, 180, 331, 221))
        self.maintenance_objects_twidget.setObjectName(_fromUtf8("maintenance_objects_twidget"))
        self.close_button = QtGui.QPushButton(MaintenanceCaseDialog)
        self.close_button.setGeometry(QtCore.QRect(580, 418, 114, 32))
        self.close_button.setObjectName(_fromUtf8("close_button"))
        self.label_8 = QtGui.QLabel(MaintenanceCaseDialog)
        self.label_8.setGeometry(QtCore.QRect(360, 101, 141, 20))
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.surveyed_by_surveyor_edit = QtGui.QLineEdit(MaintenanceCaseDialog)
        self.surveyed_by_surveyor_edit.setEnabled(False)
        self.surveyed_by_surveyor_edit.setGeometry(QtCore.QRect(530, 100, 161, 21))
        self.surveyed_by_surveyor_edit.setObjectName(_fromUtf8("surveyed_by_surveyor_edit"))
        self.application_twidget = QtGui.QTableWidget(MaintenanceCaseDialog)
        self.application_twidget.setGeometry(QtCore.QRect(360, 180, 330, 221))
        self.application_twidget.setObjectName(_fromUtf8("application_twidget"))
        self.application_twidget.setColumnCount(1)
        self.application_twidget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.application_twidget.setHorizontalHeaderItem(0, item)
        self.line = QtGui.QFrame(MaintenanceCaseDialog)
        self.line.setGeometry(QtCore.QRect(-10, 407, 801, 16))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.line_2 = QtGui.QFrame(MaintenanceCaseDialog)
        self.line_2.setGeometry(QtCore.QRect(-4, 23, 801, 16))
        self.line_2.setFrameShape(QtGui.QFrame.HLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName(_fromUtf8("line_2"))
        self.label_7 = QtGui.QLabel(MaintenanceCaseDialog)
        self.label_7.setGeometry(QtCore.QRect(21, 7, 151, 20))
        self.label_7.setObjectName(_fromUtf8("label_7"))

        self.retranslateUi(MaintenanceCaseDialog)
        QtCore.QMetaObject.connectSlotsByName(MaintenanceCaseDialog)

    def retranslateUi(self, MaintenanceCaseDialog):
        MaintenanceCaseDialog.setWindowTitle(_translate("MaintenanceCaseDialog", "Maintenance Case Dialog", None))
        self.label.setText(_translate("MaintenanceCaseDialog", "Creation date:", None))
        self.label_2.setText(_translate("MaintenanceCaseDialog", "Completion date:", None))
        self.label_3.setText(_translate("MaintenanceCaseDialog", "Survey date:", None))
        self.label_4.setText(_translate("MaintenanceCaseDialog", "Created by:", None))
        self.label_5.setText(_translate("MaintenanceCaseDialog", "Surveyed by land office:", None))
        self.label_6.setText(_translate("MaintenanceCaseDialog", "Completed by:", None))
        self.maintenance_objects_twidget.headerItem().setText(0, _translate("MaintenanceCaseDialog", "Maintenance Objects", None))
        self.close_button.setText(_translate("MaintenanceCaseDialog", "Close", None))
        self.label_8.setText(_translate("MaintenanceCaseDialog", "Surveyed by surveyor:", None))
        item = self.application_twidget.horizontalHeaderItem(0)
        item.setText(_translate("MaintenanceCaseDialog", "Applications", None))
        self.label_7.setText(_translate("MaintenanceCaseDialog", "Maintenance Case", None))

