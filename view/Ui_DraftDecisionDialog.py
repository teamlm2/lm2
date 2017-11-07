# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\DraftDecisionPrintDialog.ui'
#
# Created: Tue Mar 24 05:33:57 2015
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

class Ui_DraftDecisionPrintDialog(object):
    def setupUi(self, DraftDecisionPrintDialog):
        DraftDecisionPrintDialog.setObjectName(_fromUtf8("DraftDecisionPrintDialog"))
        DraftDecisionPrintDialog.resize(731, 560)
        self.line = QtGui.QFrame(DraftDecisionPrintDialog)
        self.line.setGeometry(QtCore.QRect(0, 540, 730, 3))
        self.line.setFrameShape(QtGui.QFrame.HLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.line_2 = QtGui.QFrame(DraftDecisionPrintDialog)
        self.line_2.setGeometry(QtCore.QRect(0, 20, 730, 3))
        self.line_2.setFrameShape(QtGui.QFrame.HLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName(_fromUtf8("line_2"))
        self.close_button = QtGui.QPushButton(DraftDecisionPrintDialog)
        self.close_button.setGeometry(QtCore.QRect(650, 510, 75, 23))
        self.close_button.setObjectName(_fromUtf8("close_button"))
        self.doc_print_button = QtGui.QPushButton(DraftDecisionPrintDialog)
        self.doc_print_button.setGeometry(QtCore.QRect(560, 510, 75, 23))
        self.doc_print_button.setObjectName(_fromUtf8("doc_print_button"))
        self.drafts_edit = QtGui.QLineEdit(DraftDecisionPrintDialog)
        self.drafts_edit.setGeometry(QtCore.QRect(10, 42, 401, 20))
        self.drafts_edit.setObjectName(_fromUtf8("drafts_edit"))
        self.drafts_path_button = QtGui.QPushButton(DraftDecisionPrintDialog)
        self.drafts_path_button.setGeometry(QtCore.QRect(420, 40, 75, 23))
        self.drafts_path_button.setObjectName(_fromUtf8("drafts_path_button"))
        self.label = QtGui.QLabel(DraftDecisionPrintDialog)
        self.label.setGeometry(QtCore.QRect(10, 22, 431, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.drafts_twidget = QtGui.QTableWidget(DraftDecisionPrintDialog)
        self.drafts_twidget.setGeometry(QtCore.QRect(10, 70, 401, 171))
        self.drafts_twidget.setObjectName(_fromUtf8("drafts_twidget"))
        self.drafts_twidget.setColumnCount(1)
        self.drafts_twidget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.drafts_twidget.setHorizontalHeaderItem(0, item)
        self.drafts_twidget.horizontalHeader().setDefaultSectionSize(400)
        self.draft_detail_twidget = QtGui.QTableWidget(DraftDecisionPrintDialog)
        self.draft_detail_twidget.setGeometry(QtCore.QRect(0, 250, 731, 251))
        self.draft_detail_twidget.setObjectName(_fromUtf8("draft_detail_twidget"))
        self.draft_detail_twidget.setColumnCount(13)
        self.draft_detail_twidget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.draft_detail_twidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.draft_detail_twidget.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.draft_detail_twidget.setHorizontalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.draft_detail_twidget.setHorizontalHeaderItem(3, item)
        item = QtGui.QTableWidgetItem()
        self.draft_detail_twidget.setHorizontalHeaderItem(4, item)
        item = QtGui.QTableWidgetItem()
        self.draft_detail_twidget.setHorizontalHeaderItem(5, item)
        item = QtGui.QTableWidgetItem()
        self.draft_detail_twidget.setHorizontalHeaderItem(6, item)
        item = QtGui.QTableWidgetItem()
        self.draft_detail_twidget.setHorizontalHeaderItem(7, item)
        item = QtGui.QTableWidgetItem()
        self.draft_detail_twidget.setHorizontalHeaderItem(8, item)
        item = QtGui.QTableWidgetItem()
        self.draft_detail_twidget.setHorizontalHeaderItem(9, item)
        item = QtGui.QTableWidgetItem()
        self.draft_detail_twidget.setHorizontalHeaderItem(10, item)
        item = QtGui.QTableWidgetItem()
        self.draft_detail_twidget.setHorizontalHeaderItem(11, item)
        item = QtGui.QTableWidgetItem()
        self.draft_detail_twidget.setHorizontalHeaderItem(12, item)

        self.retranslateUi(DraftDecisionPrintDialog)
        QtCore.QMetaObject.connectSlotsByName(DraftDecisionPrintDialog)

    def retranslateUi(self, DraftDecisionPrintDialog):
        DraftDecisionPrintDialog.setWindowTitle(_translate("DraftDecisionPrintDialog", "Dialog", None))
        self.close_button.setText(_translate("DraftDecisionPrintDialog", "Close", None))
        self.doc_print_button.setText(_translate("DraftDecisionPrintDialog", "Print", None))
        self.drafts_path_button.setText(_translate("DraftDecisionPrintDialog", "Path", None))
        self.label.setText(_translate("DraftDecisionPrintDialog", "Drafts and Decisions Path", None))
        item = self.drafts_twidget.horizontalHeaderItem(0)
        item.setText(_translate("DraftDecisionPrintDialog", "File Name", None))
        item = self.draft_detail_twidget.horizontalHeaderItem(0)
        item.setText(_translate("DraftDecisionPrintDialog", "Surname/Company Name", None))
        item = self.draft_detail_twidget.horizontalHeaderItem(1)
        item.setText(_translate("DraftDecisionPrintDialog", "First Name", None))
        item = self.draft_detail_twidget.horizontalHeaderItem(2)
        item.setText(_translate("DraftDecisionPrintDialog", "Person Id", None))
        item = self.draft_detail_twidget.horizontalHeaderItem(3)
        item.setText(_translate("DraftDecisionPrintDialog", "Application No", None))
        item = self.draft_detail_twidget.horizontalHeaderItem(4)
        item.setText(_translate("DraftDecisionPrintDialog", "Parcel No", None))
        item = self.draft_detail_twidget.horizontalHeaderItem(5)
        item.setText(_translate("DraftDecisionPrintDialog", "Address", None))
        item = self.draft_detail_twidget.horizontalHeaderItem(6)
        item.setText(_translate("DraftDecisionPrintDialog", "Area [m2]", None))
        item = self.draft_detail_twidget.horizontalHeaderItem(7)
        item.setText(_translate("DraftDecisionPrintDialog", "Land Use Type", None))
        item = self.draft_detail_twidget.horizontalHeaderItem(8)
        item.setText(_translate("DraftDecisionPrintDialog", "Draft/Decision No", None))
        item = self.draft_detail_twidget.horizontalHeaderItem(9)
        item.setText(_translate("DraftDecisionPrintDialog", "Draft/Decision Date", None))
        item = self.draft_detail_twidget.horizontalHeaderItem(10)
        item.setText(_translate("DraftDecisionPrintDialog", "Level", None))
        item = self.draft_detail_twidget.horizontalHeaderItem(11)
        item.setText(_translate("DraftDecisionPrintDialog", "Result", None))
        item = self.draft_detail_twidget.horizontalHeaderItem(12)
        item.setText(_translate("DraftDecisionPrintDialog", "Duration", None))

