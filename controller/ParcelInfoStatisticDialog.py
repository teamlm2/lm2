__author__ = 'B.Ankhbold'
# -*- encoding: utf-8 -*-
from PyQt4.QtXml import *
from geoalchemy2.elements import WKTElement
from PyQt4.QtXml import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import *
from qgis.core import *
from qgis.gui import *
from sqlalchemy import exc, or_
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_, extract
from datetime import date, datetime, timedelta
from ..view.Ui_ParcelInfoStatisticDialog import *
from inspect import currentframe
from ..utils.FileUtils import FileUtils
from ..utils.LayerUtils import LayerUtils
from ..model.DatabaseHelper import *
from .qt_classes.DoubleSpinBoxDelegate import *
import os
import locale
from collections import defaultdict
import collections
from xlsxwriter.utility import xl_rowcol_to_cell, xl_col_to_name
import xlsxwriter


class ParcelInfoStatisticDialog(QDialog, Ui_ParcelInfoStatisticDialog, DatabaseHelper):
    def __init__(self, plugin, parent=None):

        super(ParcelInfoStatisticDialog, self).__init__(parent)
        DatabaseHelper.__init__(self)

        self.setupUi(self)
        self.time_counter = None
        self.setWindowTitle(self.tr("Parcel info statistic"))
        self.close_button.clicked.connect(self.reject)
        self.session = SessionHandler().session_instance()
        self.plugin = plugin

        self.__setup_table_widget()

    def __setup_table_widget(self):

        self.result_twidget.setAlternatingRowColors(True)
        self.result_twidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_twidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_twidget.setSelectionMode(QTableWidget.SingleSelection)
        self.result_twidget.setSortingEnabled(True)

    @pyqtSlot()
    def on_find_button_clicked(self):

        self.result_twidget.setRowCount(0)
        sql = "select * from webgis.view_ub_statistic_all  "

        result = self.session.execute(sql)
        row = 0
        for item_row in result:

            self.result_twidget.insertRow(row)

            item = QTableWidgetItem()
            item.setText(unicode(item_row[1]))
            item.setData(Qt.UserRole, item_row[1])
            self.result_twidget.setItem(row, 0, item)

            item = QTableWidgetItem()
            item.setText(unicode(item_row[3]))
            item.setData(Qt.UserRole, item_row[3])
            self.result_twidget.setItem(row, 1, item)

            item = QTableWidgetItem()
            item.setText(str(item_row[4]) if item_row[4] else '0')
            item.setData(Qt.UserRole, item_row[4])
            self.result_twidget.setItem(row, 2, item)

            item = QTableWidgetItem()
            item.setText(str(item_row[8]) if item_row[8] else '0')
            item.setData(Qt.UserRole, item_row[8])
            self.result_twidget.setItem(row, 3, item)

            item = QTableWidgetItem()
            item.setText(str(item_row[6]) if item_row[6] else '0')
            item.setData(Qt.UserRole, item_row[6])
            self.result_twidget.setItem(row, 4, item)

            item = QTableWidgetItem()
            item.setText(str(item_row[5]) if item_row[5] else '0')
            item.setData(Qt.UserRole, item_row[5])
            self.result_twidget.setItem(row, 5, item)

            item = QTableWidgetItem()
            item.setText(str(item_row[7]) if item_row[7] else '0')
            item.setData(Qt.UserRole, item_row[7])
            self.result_twidget.setItem(row, 6, item)

            row = + 1

        self.result_twidget.resizeColumnsToContents()