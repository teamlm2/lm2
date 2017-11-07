# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\AboutDialog.ui'
#
# Created: Fri Dec 05 21:18:43 2014
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

class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        AboutDialog.setObjectName(_fromUtf8("AboutDialog"))
        AboutDialog.resize(390, 400)
        AboutDialog.setMinimumSize(QtCore.QSize(390, 400))
        AboutDialog.setMaximumSize(QtCore.QSize(390, 400))
        self.label = QtGui.QLabel(AboutDialog)
        self.label.setGeometry(QtCore.QRect(40, 51, 91, 21))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Helvetica"))
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.version_label = QtGui.QLabel(AboutDialog)
        self.version_label.setGeometry(QtCore.QRect(160, 53, 71, 16))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Helvetica"))
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.version_label.setFont(font)
        self.version_label.setObjectName(_fromUtf8("version_label"))
        self.label_2 = QtGui.QLabel(AboutDialog)
        self.label_2.setGeometry(QtCore.QRect(40, 30, 271, 20))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Helvetica"))
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.label_3 = QtGui.QLabel(AboutDialog)
        self.label_3.setGeometry(QtCore.QRect(40, 334, 111, 21))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.version_label_2 = QtGui.QLabel(AboutDialog)
        self.version_label_2.setGeometry(QtCore.QRect(150, 337, 221, 16))
        self.version_label_2.setObjectName(_fromUtf8("version_label_2"))
        self.close_button = QtGui.QPushButton(AboutDialog)
        self.close_button.setGeometry(QtCore.QRect(300, 360, 75, 23))
        self.close_button.setObjectName(_fromUtf8("close_button"))
        self.officer_twidget = QtGui.QTableWidget(AboutDialog)
        self.officer_twidget.setGeometry(QtCore.QRect(40, 120, 320, 192))
        self.officer_twidget.setObjectName(_fromUtf8("officer_twidget"))
        self.officer_twidget.setColumnCount(2)
        self.officer_twidget.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.officer_twidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.officer_twidget.setHorizontalHeaderItem(1, item)
        self.label_4 = QtGui.QLabel(AboutDialog)
        self.label_4.setGeometry(QtCore.QRect(40, 90, 321, 21))
        self.label_4.setObjectName(_fromUtf8("label_4"))

        self.retranslateUi(AboutDialog)
        QtCore.QMetaObject.connectSlotsByName(AboutDialog)

    def retranslateUi(self, AboutDialog):
        AboutDialog.setWindowTitle(_translate("AboutDialog", "About Dialog", None))
        self.label.setText(_translate("AboutDialog", "Version:", None))
        self.version_label.setText(_translate("AboutDialog", "version", None))
        self.label_2.setText(_translate("AboutDialog", "Land Manager II", None))
        self.label_3.setText(_translate("AboutDialog", "Developed by:", None))
        self.version_label_2.setText(_translate("AboutDialog", "Topmap, allspatial, GCI", None))
        self.close_button.setText(_translate("AboutDialog", "Close", None))
        item = self.officer_twidget.horizontalHeaderItem(0)
        item.setText(_translate("AboutDialog", "Name", None))
        item = self.officer_twidget.horizontalHeaderItem(1)
        item.setText(_translate("AboutDialog", "Logged Actions", None))
        self.label_4.setText(_translate("AboutDialog", "Land officer of the month:", None))

