__author__ = 'anna'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ...utils.PluginUtils import PluginUtils


class DropLabel(QLabel):

    itemDropped = pyqtSignal()

    def __init__(self, drop_type, parent):

        super(DropLabel,  self).__init__(parent)
        self.drop_type = drop_type
        self.parent = parent
        self.setGeometry(QRect(450, 28, 270, 81))
        self.setPixmap(QPixmap(":/plugins/lm2/drag_drop.png"))
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):

        event.acceptProposedAction()

    def dropEvent(self, event):

        widget = event.source()

        if widget is not None:

            object_name = widget.objectName()
            print object_name
            print self.drop_type
            # if self.drop_type in object_name:

            event.acceptProposedAction()
            self.itemDropped.emit()

            # else:
            #     PluginUtils.show_error(self.parent, self.tr("Type mismatch"),
            #                            self.tr("An instance of the type {0} has to be added. ").format(self.drop_type))
