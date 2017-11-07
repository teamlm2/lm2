__author__ = 'anna'

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class DocumentsTableWidget(QTableWidget):

    def __init__(self,  parent=None):

        super(DocumentsTableWidget,  self).__init__(parent)
        self.setColumnCount(6)
        self.setGeometry(QRect(20, 100, 701, 192))
        self.horizontalHeader().setDefaultSectionSize(120)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        header = [self.tr("Provided"), self.tr("Type"), self.tr("Name"),
                  self.tr("Open"), self.tr("Remove"), self.tr("View")]

        self.setup_header(header)

    def setup_header(self, header_labels):

        self.setColumnCount(len(header_labels))
        count = 0

        for label in header_labels:
            item = QTableWidgetItem(label)
            self.setHorizontalHeaderItem(count, item)
            count += 1

    def dropEvent(self, event):
        event.acceptProposedAction()
        self.itemDropped.emit()