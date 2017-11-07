# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\work\LAND_MANAGER\lm2\view\CadastrePageReportDialog.ui.'
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

class Ui_CadastrePageReportDialog(object):
    def setupUi(self, CadastrePageReportDialog):
        CadastrePageReportDialog.setObjectName(_fromUtf8("CadastrePageReportDialog"))
        CadastrePageReportDialog.resize(732, 453)
        self.close_button = QtGui.QPushButton(CadastrePageReportDialog)
        self.close_button.setGeometry(QtCore.QRect(650, 410, 75, 23))
        self.close_button.setObjectName(_fromUtf8("close_button"))
        self.find_button = QtGui.QPushButton(CadastrePageReportDialog)
        self.find_button.setGeometry(QtCore.QRect(450, 59, 75, 23))
        self.find_button.setObjectName(_fromUtf8("find_button"))
        self.cpage_twidget = QtGui.QTableWidget(CadastrePageReportDialog)
        self.cpage_twidget.setGeometry(QtCore.QRect(10, 110, 718, 292))
        self.cpage_twidget.setObjectName(_fromUtf8("cpage_twidget"))
        self.cpage_twidget.setColumnCount(7)
        self.cpage_twidget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.cpage_twidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.cpage_twidget.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.cpage_twidget.setHorizontalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.cpage_twidget.setHorizontalHeaderItem(3, item)
        item = QtGui.QTableWidgetItem()
        self.cpage_twidget.setHorizontalHeaderItem(4, item)
        item = QtGui.QTableWidgetItem()
        self.cpage_twidget.setHorizontalHeaderItem(5, item)
        item = QtGui.QTableWidgetItem()
        self.cpage_twidget.setHorizontalHeaderItem(6, item)
        self.results_label = QtGui.QLabel(CadastrePageReportDialog)
        self.results_label.setGeometry(QtCore.QRect(10, 90, 201, 16))
        self.results_label.setText(_fromUtf8(""))
        self.results_label.setObjectName(_fromUtf8("results_label"))
        self.print_button = QtGui.QPushButton(CadastrePageReportDialog)
        self.print_button.setGeometry(QtCore.QRect(550, 410, 75, 23))
        self.print_button.setObjectName(_fromUtf8("print_button"))
        self.line = QtGui.QFrame(CadastrePageReportDialog)
        self.line.setGeometry(QtCore.QRect(0, 20, 731, 16))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.line_2 = QtGui.QFrame(CadastrePageReportDialog)
        self.line_2.setGeometry(QtCore.QRect(0, 430, 731, 16))
        self.line_2.setFrameShape(QtGui.QFrame.HLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName(_fromUtf8("line_2"))
        self.label_2 = QtGui.QLabel(CadastrePageReportDialog)
        self.label_2.setGeometry(QtCore.QRect(10, 10, 281, 16))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.print_year_chbox = QtGui.QCheckBox(CadastrePageReportDialog)
        self.print_year_chbox.setGeometry(QtCore.QRect(330, 40, 101, 17))
        self.print_year_chbox.setObjectName(_fromUtf8("print_year_chbox"))
        self.print_year_sbox = QtGui.QSpinBox(CadastrePageReportDialog)
        self.print_year_sbox.setEnabled(False)
        self.print_year_sbox.setGeometry(QtCore.QRect(330, 59, 91, 22))
        self.print_year_sbox.setMinimum(2000)
        self.print_year_sbox.setMaximum(2100)
        self.print_year_sbox.setProperty("value", 2017)
        self.print_year_sbox.setObjectName(_fromUtf8("print_year_sbox"))
        self.label_3 = QtGui.QLabel(CadastrePageReportDialog)
        self.label_3.setGeometry(QtCore.QRect(10, 40, 171, 16))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.person_id_edit = QtGui.QLineEdit(CadastrePageReportDialog)
        self.person_id_edit.setGeometry(QtCore.QRect(10, 60, 150, 20))
        self.person_id_edit.setObjectName(_fromUtf8("person_id_edit"))
        self.parcel_id_edit = QtGui.QLineEdit(CadastrePageReportDialog)
        self.parcel_id_edit.setGeometry(QtCore.QRect(170, 60, 150, 20))
        self.parcel_id_edit.setObjectName(_fromUtf8("parcel_id_edit"))
        self.label_4 = QtGui.QLabel(CadastrePageReportDialog)
        self.label_4.setGeometry(QtCore.QRect(170, 40, 151, 16))
        self.label_4.setObjectName(_fromUtf8("label_4"))

        self.retranslateUi(CadastrePageReportDialog)
        QtCore.QMetaObject.connectSlotsByName(CadastrePageReportDialog)

    def retranslateUi(self, CadastrePageReportDialog):
        CadastrePageReportDialog.setWindowTitle(_translate("CadastrePageReportDialog", "Dialog", None))
        self.close_button.setText(_translate("CadastrePageReportDialog", "close", None))
        self.find_button.setText(_translate("CadastrePageReportDialog", "Find", None))
        item = self.cpage_twidget.horizontalHeaderItem(0)
        item.setText(_translate("CadastrePageReportDialog", "ID", None))
        item = self.cpage_twidget.horizontalHeaderItem(1)
        item.setText(_translate("CadastrePageReportDialog", "PrintDate", None))
        item = self.cpage_twidget.horizontalHeaderItem(2)
        item.setText(_translate("CadastrePageReportDialog", "Page Number", None))
        item = self.cpage_twidget.horizontalHeaderItem(3)
        item.setText(_translate("CadastrePageReportDialog", "Person ID", None))
        item = self.cpage_twidget.horizontalHeaderItem(4)
        item.setText(_translate("CadastrePageReportDialog", "Right Holder", None))
        item = self.cpage_twidget.horizontalHeaderItem(5)
        item.setText(_translate("CadastrePageReportDialog", "Parcel ID", None))
        item = self.cpage_twidget.horizontalHeaderItem(6)
        item.setText(_translate("CadastrePageReportDialog", "Streetname-Khashaa", None))
        self.print_button.setText(_translate("CadastrePageReportDialog", "Print", None))
        self.label_2.setText(_translate("CadastrePageReportDialog", "Cadastre page report", None))
        self.print_year_chbox.setText(_translate("CadastrePageReportDialog", "Year Print", None))
        self.label_3.setText(_translate("CadastrePageReportDialog", "Person ID", None))
        self.label_4.setText(_translate("CadastrePageReportDialog", "Parcel ID", None))

