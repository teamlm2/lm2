__author__ = 'anna'
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class IntegerSpinBoxDelegate(QStyledItemDelegate):

    def __init__(self, column, min_val, max_val, cur_val, step, parent):

        super(IntegerSpinBoxDelegate, self).__init__(parent)
        self.spinbox_column = column
        self.min_val = min_val
        self.max_val = max_val
        self.cur_val = cur_val
        self.step = step
        self.parent = parent

    def createEditor(self, widget, item, index):

        if not index is None:
            if index.isValid():
                if index.column() == self.spinbox_column:
                    editor = QSpinBox(widget)
                    editor.setMaximum(self.max_val)
                    editor.setValue(self.cur_val)
                    editor.setMinimum(self.min_val)
                    editor.setSingleStep(self.step)
                    return editor
