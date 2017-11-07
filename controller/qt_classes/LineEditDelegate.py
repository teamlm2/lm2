__author__ = 'anna'
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class LineEditDelegate(QStyledItemDelegate):

    def __init__(self, column, completer_value_list, parent):

        super(LineEditDelegate, self).__init__(parent)
        self.line_edit_column = column
        self.completer_model = QStringListModel(completer_value_list)
        self.completer_proxy_model = QSortFilterProxyModel()
        self.completer_proxy_model.setSourceModel(self.completer_model)
        self.completer = QCompleter(self.completer_proxy_model, self, activated=self.on_completer_activated)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.parent = parent

    def createEditor(self, widget, item, index):

        if not index is None:
            if index.isValid():
                if index.column() == self.line_edit_column:
                    editor = QLineEdit(widget)
                    editor.setCompleter(self.completer)
                    editor.textEdited.connect(self.completer_proxy_model.setFilterFixedString)
                    return editor

    @pyqtSlot(str)
    def on_completer_activated(self, text):

        if not text:
            return
        self.completer.activated[str].emit(text)