# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'OfficialDocumentsDialog.ui'
#
# Created: Mon Dec  1 15:12:01 2014
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

class Ui_OfficialDocumentsDialog(object):
    def setupUi(self, OfficialDocumentsDialog):
        OfficialDocumentsDialog.setObjectName(_fromUtf8("OfficialDocumentsDialog"))
        OfficialDocumentsDialog.resize(740, 390)
        OfficialDocumentsDialog.setMinimumSize(QtCore.QSize(740, 390))
        OfficialDocumentsDialog.setMaximumSize(QtCore.QSize(740, 390))
        self.doc_twidget = QtGui.QTableWidget(OfficialDocumentsDialog)
        self.doc_twidget.setGeometry(QtCore.QRect(14, 41, 711, 301))
        self.doc_twidget.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked)
        self.doc_twidget.setObjectName(_fromUtf8("doc_twidget"))
        self.doc_twidget.setColumnCount(3)
        self.doc_twidget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.doc_twidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.doc_twidget.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.doc_twidget.setHorizontalHeaderItem(2, item)
        self.doc_twidget.horizontalHeader().setCascadingSectionResizes(False)
        self.doc_twidget.horizontalHeader().setDefaultSectionSize(120)
        self.doc_twidget.horizontalHeader().setHighlightSections(False)
        self.doc_twidget.verticalHeader().setCascadingSectionResizes(False)
        self.line_2 = QtGui.QFrame(OfficialDocumentsDialog)
        self.line_2.setGeometry(QtCore.QRect(0, 370, 801, 16))
        self.line_2.setFrameShape(QtGui.QFrame.HLine)
        self.line_2.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_2.setObjectName(_fromUtf8("line_2"))
        self.line_3 = QtGui.QFrame(OfficialDocumentsDialog)
        self.line_3.setGeometry(QtCore.QRect(0, 18, 801, 16))
        self.line_3.setFrameShape(QtGui.QFrame.HLine)
        self.line_3.setFrameShadow(QtGui.QFrame.Sunken)
        self.line_3.setObjectName(_fromUtf8("line_3"))
        self.label = QtGui.QLabel(OfficialDocumentsDialog)
        self.label.setGeometry(QtCore.QRect(10, 8, 151, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.close_button = QtGui.QPushButton(OfficialDocumentsDialog)
        self.close_button.setGeometry(QtCore.QRect(652, 347, 75, 23))
        self.close_button.setObjectName(_fromUtf8("close_button"))

        self.retranslateUi(OfficialDocumentsDialog)
        QtCore.QMetaObject.connectSlotsByName(OfficialDocumentsDialog)

    def retranslateUi(self, OfficialDocumentsDialog):
        OfficialDocumentsDialog.setWindowTitle(_translate("OfficialDocumentsDialog", "Dialog", None))
        item = self.doc_twidget.horizontalHeaderItem(0)
        item.setText(_translate("OfficialDocumentsDialog", "Name", None))
        item = self.doc_twidget.horizontalHeaderItem(1)
        item.setText(_translate("OfficialDocumentsDialog", "Description", None))
        item = self.doc_twidget.horizontalHeaderItem(2)
        item.setText(_translate("OfficialDocumentsDialog", "View", None))
        self.label.setText(_translate("OfficialDocumentsDialog", "Official documents", None))
        self.close_button.setText(_translate("OfficialDocumentsDialog", "Close", None))

