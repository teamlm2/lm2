# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\ParcelInfoStatisticDialog.ui'
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

class Ui_ParcelInfoStatisticDialog(object):
    def setupUi(self, ParcelInfoStatisticDialog):
        ParcelInfoStatisticDialog.setObjectName(_fromUtf8("ParcelInfoStatisticDialog"))
        ParcelInfoStatisticDialog.resize(783, 428)
        self.line = QtGui.QFrame(ParcelInfoStatisticDialog)
        self.line.setGeometry(QtCore.QRect(0, 12, 781, 16))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.line_2 = QtGui.QFrame(ParcelInfoStatisticDialog)
        self.line_2.setGeometry(QtCore.QRect(1, 400, 781, 16))
        self.line_2.setFrameShape(QtGui.QFrame.HLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName(_fromUtf8("line_2"))
        self.close_button = QtGui.QPushButton(ParcelInfoStatisticDialog)
        self.close_button.setGeometry(QtCore.QRect(700, 380, 75, 23))
        self.close_button.setObjectName(_fromUtf8("close_button"))
        self.print_button = QtGui.QPushButton(ParcelInfoStatisticDialog)
        self.print_button.setGeometry(QtCore.QRect(610, 380, 75, 23))
        self.print_button.setObjectName(_fromUtf8("print_button"))
        self.result_twidget = QtGui.QTableWidget(ParcelInfoStatisticDialog)
        self.result_twidget.setGeometry(QtCore.QRect(10, 100, 761, 271))
        self.result_twidget.setObjectName(_fromUtf8("result_twidget"))
        self.result_twidget.setColumnCount(7)
        self.result_twidget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.result_twidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.result_twidget.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.result_twidget.setHorizontalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.result_twidget.setHorizontalHeaderItem(3, item)
        item = QtGui.QTableWidgetItem()
        self.result_twidget.setHorizontalHeaderItem(4, item)
        item = QtGui.QTableWidgetItem()
        self.result_twidget.setHorizontalHeaderItem(5, item)
        item = QtGui.QTableWidgetItem()
        self.result_twidget.setHorizontalHeaderItem(6, item)
        self.organization_type_cbox = QtGui.QComboBox(ParcelInfoStatisticDialog)
        self.organization_type_cbox.setGeometry(QtCore.QRect(10, 50, 201, 22))
        self.organization_type_cbox.setObjectName(_fromUtf8("organization_type_cbox"))
        self.label_4 = QtGui.QLabel(ParcelInfoStatisticDialog)
        self.label_4.setGeometry(QtCore.QRect(10, 30, 201, 16))
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.organization_cbox = QtGui.QComboBox(ParcelInfoStatisticDialog)
        self.organization_cbox.setGeometry(QtCore.QRect(240, 50, 201, 22))
        self.organization_cbox.setObjectName(_fromUtf8("organization_cbox"))
        self.label_5 = QtGui.QLabel(ParcelInfoStatisticDialog)
        self.label_5.setGeometry(QtCore.QRect(240, 30, 201, 16))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.department_cbox = QtGui.QComboBox(ParcelInfoStatisticDialog)
        self.department_cbox.setGeometry(QtCore.QRect(470, 50, 201, 22))
        self.department_cbox.setObjectName(_fromUtf8("department_cbox"))
        self.label_6 = QtGui.QLabel(ParcelInfoStatisticDialog)
        self.label_6.setGeometry(QtCore.QRect(470, 30, 201, 16))
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.checkBox = QtGui.QCheckBox(ParcelInfoStatisticDialog)
        self.checkBox.setGeometry(QtCore.QRect(20, 80, 191, 17))
        self.checkBox.setObjectName(_fromUtf8("checkBox"))
        self.checkBox_2 = QtGui.QCheckBox(ParcelInfoStatisticDialog)
        self.checkBox_2.setGeometry(QtCore.QRect(230, 80, 191, 17))
        self.checkBox_2.setObjectName(_fromUtf8("checkBox_2"))
        self.find_button = QtGui.QPushButton(ParcelInfoStatisticDialog)
        self.find_button.setGeometry(QtCore.QRect(690, 50, 75, 23))
        self.find_button.setObjectName(_fromUtf8("find_button"))

        self.retranslateUi(ParcelInfoStatisticDialog)
        QtCore.QMetaObject.connectSlotsByName(ParcelInfoStatisticDialog)

    def retranslateUi(self, ParcelInfoStatisticDialog):
        ParcelInfoStatisticDialog.setWindowTitle(_translate("ParcelInfoStatisticDialog", "Dialog", None))
        self.close_button.setText(_translate("ParcelInfoStatisticDialog", "Close", None))
        self.print_button.setText(_translate("ParcelInfoStatisticDialog", "print", None))
        item = self.result_twidget.horizontalHeaderItem(0)
        item.setText(_translate("ParcelInfoStatisticDialog", "Duureg", None))
        item = self.result_twidget.horizontalHeaderItem(1)
        item.setText(_translate("ParcelInfoStatisticDialog", "Department", None))
        item = self.result_twidget.horizontalHeaderItem(2)
        item.setText(_translate("ParcelInfoStatisticDialog", "Parcel Count", None))
        item = self.result_twidget.horizontalHeaderItem(3)
        item.setText(_translate("ParcelInfoStatisticDialog", "Not Fixed", None))
        item = self.result_twidget.horizontalHeaderItem(4)
        item.setText(_translate("ParcelInfoStatisticDialog", "In process", None))
        item = self.result_twidget.horizontalHeaderItem(5)
        item.setText(_translate("ParcelInfoStatisticDialog", "Finished", None))
        item = self.result_twidget.horizontalHeaderItem(6)
        item.setText(_translate("ParcelInfoStatisticDialog", "Done", None))
        self.label_4.setText(_translate("ParcelInfoStatisticDialog", "Organization Type", None))
        self.label_5.setText(_translate("ParcelInfoStatisticDialog", "Organization", None))
        self.label_6.setText(_translate("ParcelInfoStatisticDialog", "Department", None))
        self.checkBox.setText(_translate("ParcelInfoStatisticDialog", "sort by duureg", None))
        self.checkBox_2.setText(_translate("ParcelInfoStatisticDialog", "sort by department", None))
        self.find_button.setText(_translate("ParcelInfoStatisticDialog", "Find", None))

