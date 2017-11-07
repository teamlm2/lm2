import os

__author__ = 'anna'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ..view.Ui_DecisionErrorDialog import *


class DecisionErrorDialog(QDialog, Ui_DecisionErrorDialog):

    def __init__(self, error_list, parent=None):

        super(DecisionErrorDialog, self).__init__(parent)
        self.setupUi(self)
        self.error_list = error_list

        for application, error in self.error_list.iteritems():

            app_item = QTableWidgetItem(application)
            error_item = QTableWidgetItem(error)
            count = self.error_twidget.rowCount()
            self.error_twidget.insertRow(count)
            self.error_twidget.setItem(count, 0, app_item)
            self.error_twidget.setItem(count, 1, error_item)

        self.error_twidget.resizeColumnsToContents()

    @pyqtSlot()
    def on_close_button_clicked(self):

        self.reject()

    @pyqtSlot()
    def on_help_button_clicked(self):

        os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/decision.htm")