# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\ReportDialog.ui'
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

class Ui_ReportDialog(object):
    def setupUi(self, ReportDialog):
        ReportDialog.setObjectName(_fromUtf8("ReportDialog"))
        ReportDialog.resize(378, 476)
        self.listWidget = QtGui.QListWidget(ReportDialog)
        self.listWidget.setGeometry(QtCore.QRect(4, 90, 371, 160))
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        item = QtGui.QListWidgetItem()
        self.listWidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.listWidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.listWidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.listWidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.listWidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.listWidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.listWidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.listWidget.addItem(item)
        item = QtGui.QListWidgetItem()
        self.listWidget.addItem(item)
        self.line = QtGui.QFrame(ReportDialog)
        self.line.setGeometry(QtCore.QRect(0, 20, 378, 16))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.label = QtGui.QLabel(ReportDialog)
        self.label.setGeometry(QtCore.QRect(10, 10, 46, 13))
        self.label.setObjectName(_fromUtf8("label"))
        self.begin_year_sbox = QtGui.QSpinBox(ReportDialog)
        self.begin_year_sbox.setGeometry(QtCore.QRect(20, 276, 91, 22))
        self.begin_year_sbox.setObjectName(_fromUtf8("begin_year_sbox"))
        self.label_2 = QtGui.QLabel(ReportDialog)
        self.label_2.setGeometry(QtCore.QRect(20, 256, 71, 16))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.label_4 = QtGui.QLabel(ReportDialog)
        self.label_4.setGeometry(QtCore.QRect(20, 306, 46, 13))
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.aimag_cbox = QtGui.QComboBox(ReportDialog)
        self.aimag_cbox.setGeometry(QtCore.QRect(20, 326, 201, 22))
        self.aimag_cbox.setObjectName(_fromUtf8("aimag_cbox"))
        self.line_2 = QtGui.QFrame(ReportDialog)
        self.line_2.setGeometry(QtCore.QRect(0, 450, 378, 16))
        self.line_2.setFrameShape(QtGui.QFrame.HLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName(_fromUtf8("line_2"))
        self.print_button = QtGui.QPushButton(ReportDialog)
        self.print_button.setGeometry(QtCore.QRect(210, 420, 75, 23))
        self.print_button.setObjectName(_fromUtf8("print_button"))
        self.close_button = QtGui.QPushButton(ReportDialog)
        self.close_button.setGeometry(QtCore.QRect(300, 420, 75, 23))
        self.close_button.setObjectName(_fromUtf8("close_button"))
        self.progressBar = QtGui.QProgressBar(ReportDialog)
        self.progressBar.setEnabled(True)
        self.progressBar.setGeometry(QtCore.QRect(20, 420, 181, 22))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(True)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.label_5 = QtGui.QLabel(ReportDialog)
        self.label_5.setGeometry(QtCore.QRect(10, 40, 91, 16))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.work_level_lbl = QtGui.QLabel(ReportDialog)
        self.work_level_lbl.setGeometry(QtCore.QRect(110, 40, 241, 16))
        self.work_level_lbl.setObjectName(_fromUtf8("work_level_lbl"))
        self.layer_view_button = QtGui.QPushButton(ReportDialog)
        self.layer_view_button.setGeometry(QtCore.QRect(20, 370, 201, 23))
        self.layer_view_button.setObjectName(_fromUtf8("layer_view_button"))

        self.retranslateUi(ReportDialog)
        QtCore.QMetaObject.connectSlotsByName(ReportDialog)

    def retranslateUi(self, ReportDialog):
        ReportDialog.setWindowTitle(_translate("ReportDialog", "Dialog", None))
        __sortingEnabled = self.listWidget.isSortingEnabled()
        self.listWidget.setSortingEnabled(False)
        item = self.listWidget.item(0)
        item.setText(_translate("ReportDialog", "01.GT-1 Land unified report", None))
        item = self.listWidget.item(1)
        item.setText(_translate("ReportDialog", "02.GT-2 Report on the legal status of the unified", None))
        item = self.listWidget.item(2)
        item.setText(_translate("ReportDialog", "03.GT-3 Land registry report", None))
        item = self.listWidget.item(3)
        item.setText(_translate("ReportDialog", "04.GT-4 Land for state special need report", None))
        item = self.listWidget.item(4)
        item.setText(_translate("ReportDialog", "05.GT-5 Change of land transaction report", None))
        item = self.listWidget.item(5)
        item.setText(_translate("ReportDialog", "06.GT-6 Land pollution report", None))
        item = self.listWidget.item(6)
        item.setText(_translate("ReportDialog", "07.GT-7 Land conservation report", None))
        item = self.listWidget.item(7)
        item.setText(_translate("ReportDialog", "08.GT-8 Land fee yearly report", None))
        item = self.listWidget.item(8)
        item.setText(_translate("ReportDialog", "09.GT-9 Land privatization report", None))
        self.listWidget.setSortingEnabled(__sortingEnabled)
        self.label.setText(_translate("ReportDialog", "Report ", None))
        self.label_2.setText(_translate("ReportDialog", "Report Year", None))
        self.label_4.setText(_translate("ReportDialog", "Aimag", None))
        self.print_button.setText(_translate("ReportDialog", "Print", None))
        self.close_button.setText(_translate("ReportDialog", "Close", None))
        self.label_5.setText(_translate("ReportDialog", "Work level:", None))
        self.work_level_lbl.setText(_translate("ReportDialog", "TextLabel", None))
        self.layer_view_button.setText(_translate("ReportDialog", "Layer view", None))

