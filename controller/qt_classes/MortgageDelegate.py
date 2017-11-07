__author__ = 'anna'
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ...model.LM2Exception import LM2Exception
from ...utils.DatabaseUtils import DatabaseUtils

SHARE_COLUMN = 0
PERSON_ID_COLUMN = 1
NAME_COLUMN = 2
SURNAME_COLUMN = 3
START_COLUMN = 4
END_COLUMN = 5
TYPE_COLUMN = 6


class MortgageDelegate(QStyledItemDelegate):

    def __init__(self, widget, parent):

        super(MortgageDelegate, self).__init__(parent)
        self.widget = widget
        self.parent = parent

        self.mortgageTypes = DatabaseUtils.codelist_by_name("codelists", "cl_mortage_type", "code", "description")

    def paint(self, painter, option, index):
        #if index.column() == TYPE_COLUMN:
            #item = self.widget.item(index.row(), TYPE_COLUMN)
            #if item is not None:
                #if item.data(Qt.UserRole) in self.mortgageTypes.keys():
                    #return self.mortgageTypes[item.data(Qt.UserRole)]

        return super(MortgageDelegate, self).paint(painter, option, index)

    def createEditor(self, widget, item, index):

        if not index is None:
            if index.isValid():
                if index.column() == TYPE_COLUMN:
                    combo_box = QComboBox(widget)
                    for mortgage_type in self.mortgageTypes.keys():
                        combo_box.addItem(self.mortgageTypes[mortgage_type], mortgage_type)
                    return combo_box

                elif index.column() == START_COLUMN:
                    date = QDateEdit(QDate.currentDate(), widget)
                    return date

                elif index.column() == END_COLUMN:
                    date = QDateEdit(QDate.currentDate(), widget)
                    return date

        return False

    def __file_data(self, file_path):

        currentFile = QFile(file_path)
        if not currentFile.open(QIODevice.ReadOnly):
            raise LM2Exception(self.tr("File Error"), self.tr("Could not open/read File: {0}").format(file_path))

        byteArray = currentFile.readAll()
        return byteArray
