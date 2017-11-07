__author__ = 'anna'
from PyQt4.QtGui import *


class ApplicationCmbBoxDelegate(QStyledItemDelegate):

    def __init__(self, column, value_list, parent):

        super(ApplicationCmbBoxDelegate, self).__init__(parent)
        self.cbox_column = column
        self.value_list = value_list
        self.parent = parent

    def createEditor(self, widget, item, index):

        if not index is None:
            if index.isValid():
                if index.column() == self.cbox_column:
                    editor = QComboBox(widget)
                    used_codes = self.excluded_codes(index.row())
                    curr_idx = -1
                    count = 0
                    for txt in self.value_list:
                        if txt not in used_codes:
                            editor.addItem(txt)
                            if txt == self.parent.item(index.row(), 0).text():
                                curr_idx = count
                            count += 1

                    if curr_idx != -1:
                        editor.setCurrentIndex(curr_idx)
                    return editor

    def setModelData(self, editor, model, index):

        if index is None:
            return

        item = self.parent.item(index.row(), self.cbox_column)
        if item is None:
            return
        item.setText(editor.currentText())
        return


    def excluded_codes(self, current_row):

        used_codes = list()
        for row in range(self.parent.rowCount()):
            landuse_code = self.parent.item(row, 0).text()
            if row != current_row:
                used_codes.append(landuse_code)
        return used_codes