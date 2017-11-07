__author__ = 'B.Ankhbold'
# -*- encoding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ...utils.PluginUtils import *

class DateDelegate(QStyledItemDelegate):

    def __init__(self, parent):

        super(DateDelegate, self).__init__(parent)
        self.parent = parent

    def createEditor(self, widget, item, index):

        if not index is None:
            if index.isValid():
                now = QDate.currentDate()
                editor = QDateEdit(now, widget)
                editor.setMouseTracking(True)
                editor.setCalendarPopup(True)
                editor.setDisplayFormat("yyyy-MM-dd")
                return editor

    # def displayText(self, value, locale):
    #
    #     return value
