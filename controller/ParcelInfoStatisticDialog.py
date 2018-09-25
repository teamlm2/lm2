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

    @pyqtSlot()
    def on_print_button_clicked(self):

        default_path = r'D:/TM_LM2/reports'

        # path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/" + "parcel_info_statistic.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_row(3, 20)
        # worksheet.set_landscape()
        # worksheet.set_paper(9)
        worksheet.set_margins(left=0.3, right=0.3)

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(14)
        format_header.set_bold()

        format_normal = workbook.add_format()
        format_normal.set_text_wrap()
        format_normal.set_border(1)
        format_normal.set_font_name('Times New Roman')
        format_normal.set_font_size(12)
        # format_normal.set_bold()

        worksheet.merge_range('D2:L2', u'Мэдээллийн сангийн өгөгдөл засварлаж буй тайлан', format_header)

        row_count = range(self.result_twidget.rowCount())

        x_row = 5
        for row in row_count:
            worksheet.write(x_row, 0, row+1, format_normal)
            worksheet.write(x_row, 1, self.result_twidget.item(row, 0).text(), format_normal)
            worksheet.write(x_row, 2, self.result_twidget.item(row, 1).text(), format_normal)
            worksheet.write(x_row, 3, self.result_twidget.item(row, 2).text(), format_normal)
            worksheet.write(x_row, 4, self.result_twidget.item(row, 3).text(), format_normal)
            worksheet.write(x_row, 5, self.result_twidget.item(row, 4).text(), format_normal)
            worksheet.write(x_row, 6, self.result_twidget.item(row, 5).text(), format_normal)
            worksheet.write(x_row, 7, self.result_twidget.item(row, 6).text(), format_normal)

            x_row += 1

        # try:
        workbook.close()
        QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/" + "parcel_info_statistic.xlsx"))
        # except IOError, e:
        #     PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

