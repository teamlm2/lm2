# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'DecisionErrorDialog.ui'
#
# Created: Fri Sep 26 15:22:40 2014
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

class Ui_DecisionErrorDialog(object):
    def setupUi(self, DecisionErrorDialog):
        DecisionErrorDialog.setObjectName(_fromUtf8("DecisionErrorDialog"))
        DecisionErrorDialog.resize(599, 391)
        DecisionErrorDialog.setMinimumSize(QtCore.QSize(599, 391))
        DecisionErrorDialog.setMaximumSize(QtCore.QSize(599, 391))
        self.error_twidget = QtGui.QTableWidget(DecisionErrorDialog)
        self.error_twidget.setGeometry(QtCore.QRect(10, 10, 581, 331))
        self.error_twidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.error_twidget.setObjectName(_fromUtf8("error_twidget"))
        self.error_twidget.setColumnCount(2)
        self.error_twidget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.error_twidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.error_twidget.setHorizontalHeaderItem(1, item)
        self.error_twidget.horizontalHeader().setCascadingSectionResizes(True)
        self.error_twidget.horizontalHeader().setDefaultSectionSize(100)
        self.error_twidget.horizontalHeader().setMinimumSectionSize(100)
        self.error_twidget.verticalHeader().setCascadingSectionResizes(False)
        self.error_twidget.verticalHeader().setDefaultSectionSize(17)
        self.error_twidget.verticalHeader().setHighlightSections(False)
        self.error_twidget.verticalHeader().setMinimumSectionSize(17)
        self.close_button = QtGui.QPushButton(DecisionErrorDialog)
        self.close_button.setGeometry(QtCore.QRect(480, 350, 114, 32))
        self.close_button.setObjectName(_fromUtf8("close_button"))

        self.retranslateUi(DecisionErrorDialog)
        QtCore.QMetaObject.connectSlotsByName(DecisionErrorDialog)

    def retranslateUi(self, DecisionErrorDialog):
        DecisionErrorDialog.setWindowTitle(_translate("DecisionErrorDialog", "Decision Error Dialog", None))
        item = self.error_twidget.horizontalHeaderItem(0)
        item.setText(_translate("DecisionErrorDialog", "Application", None))
        item = self.error_twidget.horizontalHeaderItem(1)
        item.setText(_translate("DecisionErrorDialog", "Error", None))
        self.close_button.setText(_translate("DecisionErrorDialog", "Close", None))

