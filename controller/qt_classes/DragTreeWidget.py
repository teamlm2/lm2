__author__ = 'B.Ankhbold'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ...model import Constants
from ...utils.PluginUtils import PluginUtils


class DragTreeWidget(QTreeWidget):

    itemDropped = pyqtSignal()

    def __init__(self, drop_type,  x, y, width, height, parent):
        super(DragTreeWidget, self).__init__(parent)
        self.setGeometry(QRect(x, y, width, height))
        self.drop_type = drop_type
        self.parent = parent

        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def setup_header(self, header_labels):

        self.setColumnCount(len(header_labels))
        self.setHeaderLabels(header_labels)

        for i in range(self.columnCount()):
            self.headerItem().setTextAlignment(i,Qt.AlignHCenter)
        self.header().setResizeMode(QHeaderView.ResizeToContents)
        # self.header().setStretchLastSection(False)
        # self.setIndentation(60)
        # self.setColumnWidth(0, 200)

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