__author__ = 'anna'
from PyQt4.QtGui import *

class ComboBoxDelegate(QStyledItemDelegate):

    def __init__(self, column, value_list, parent):

        super(ComboBoxDelegate, self).__init__(parent)
        self.cbox_column = column
        self.value_list = value_list
        self.parent = parent

    def createEditor(self, widget, item, index):

        if not index is None:
            if index.isValid():
                if index.column() == self.cbox_column:
                    editor = QComboBox(widget)
                    curr_idx = -1
                    count = 0
                    for txt in self.value_list:
                        editor.addItem(txt)
                        if txt == self.parent.item(index.row(), index.column()).text():
                            curr_idx = count
                        count += 1

                    if curr_idx != -1:
                        editor.setCurrentIndex(curr_idx)
                    return editor