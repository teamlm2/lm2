__author__ = 'B.Ankhbold'
# -*- encoding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ...utils.PluginUtils import *

class DateFormatDelegate(QStyledItemDelegate):
    def __init__(self, date_format):
        QStyledItemDelegate.__init__(self)
        self.date_format = date_format

    def displayText(self, value, locale):
        return value.toDate().toString(self.date_format)
