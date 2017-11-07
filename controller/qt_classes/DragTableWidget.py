__author__ = 'anna'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ...model import Constants
from ...utils.PluginUtils import PluginUtils


class DragTableWidget(QTableWidget):

    itemDropped = pyqtSignal()

    def __init__(self, drop_type,  x, y, width, height, parent):
        super(DragTableWidget,  self).__init__(parent)
        self.setGeometry(QRect(x, y, width, height))
        self.horizontalHeader().setDefaultSectionSize(180)
        self.drop_type = drop_type
        self.parent = parent

        self.setDragEnabled(True)
        self.setDragDropOverwriteMode(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.CopyAction)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

    def setup_header(self, header_labels):

        self.setColumnCount(len(header_labels))
        count = 0

        for label in header_labels:
            item = QTableWidgetItem(label)
            self.setHorizontalHeaderItem(count, item)
            count += 1
        try:

            default_section_size = int(self.width()/count)

        except ValueError:
            default_section_size = Constants.DEFAULT_HEADER_WIDTH

        self.horizontalHeader().setDefaultSectionSize(default_section_size)

    def dropEvent(self, event):

        widget = event.source()

        if widget is not None:
            object_name = widget.objectName()
            if self.drop_type in object_name:
                event.acceptProposedAction()
                self.itemDropped.emit()

            else:
                PluginUtils.show_error(self.parent, self.tr("Type mismatch"),
                                    self.tr("An instance of the type {0} has to be added. ").format(self.drop_type))