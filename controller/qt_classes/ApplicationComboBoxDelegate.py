__author__ = 'anna'
from PyQt4.QtGui import *
from PyQt4.Qt import *

class ApplicationComboBoxDelegate(QStyledItemDelegate):

    def __init__(self, column, value_list, parent):

        super(ApplicationComboBoxDelegate, self).__init__(parent)
        self.cbox_column = column
        self.value_list = value_list
        self.parent = parent

    def createEditor(self, widget, item, index):

        if not index is None:
            if index.isValid():
                if index.column() == self.cbox_column:
                    editor = QComboBox(widget)
                    editor.setEditable(True)
                    curr_idx = -1
                    count = 0
                    for txt in self.value_list:
                        exists = self.parent.findItems(txt[0], Qt.MatchExactly)
                        if len(exists) == 0:
                            editor.addItem(txt[0])
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