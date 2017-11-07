__author__ = 'anna'
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sqlalchemy.exc import SQLAlchemyError
from ...model import SettingsConstants
from ...model.LM2Exception import LM2Exception
from ...model.CtApplicationDocument import CtApplicationDocument
from ...model.CtDocument import CtDocument
from ...utils.FileUtils import FileUtils
from ...utils.PluginUtils import PluginUtils
from ...utils.DatabaseUtils import DatabaseUtils
from ...utils.SessionHandler import SessionHandler
from ...utils.FilePath import *
import shutil

APP_DOC_PROVIDED_COLUMN = 0
APP_DOC_TYPE_COLUMN = 1
APP_DOC_NAME_COLUMN = 2
APP_DOC_VIEW_COLUMN = 3


class ObjectAppDocumentDelegate(QStyledItemDelegate):

    def __init__(self, widget, parent):

        super(ObjectAppDocumentDelegate, self).__init__(parent)
        self.widget = widget
        self.parent = parent
        self.session = SessionHandler().session_instance()
        self.button = QPushButton("", parent)
        self.button.hide()

        self.viewIcon = QIcon(":/plugins/lm2/file.png")

    def paint(self, painter, option, index):

        if index.column() == APP_DOC_VIEW_COLUMN:
            self.button.setIcon(self.viewIcon)
        else:
            super(ObjectAppDocumentDelegate, self).paint(painter, option, index)
            return

        self.button.setGeometry(option.rect)
        button_picture = QPixmap.grabWidget(self.button)
        painter.drawPixmap(option.rect.x(), option.rect.y(), button_picture)

    def editorEvent(self, event, model, option, index):

        if not index is None:

            if index.isValid() and event.type() == QEvent.MouseButtonRelease:

                if event.button() == Qt.RightButton:
                    return False

                if index.column() == APP_DOC_VIEW_COLUMN:

                    try:
                        file_name = self.widget.item(index.row(), APP_DOC_NAME_COLUMN).text()
                        app_no = self.widget.item(index.row(), APP_DOC_NAME_COLUMN).data(Qt.UserRole)
                        default_path = FilePath.app_file_path()
                        if file_name != '':
                            shutil.copy2(default_path+ '/'+ app_no + '/'+file_name, FilePath.view_file_path())
                            QDesktopServices.openUrl(QUrl.fromLocalFile(FilePath.view_file_path()))

                    except IOError, e:
                        QMessageBox.information(None, QApplication.translate("LM2", "No parcel"),
                                                QApplication.translate("LM2", "This file is already opened. Please close re-run"))
                        return True

                elif index.column() == APP_DOC_TYPE_COLUMN or index.column() == APP_DOC_NAME_COLUMN or index.column() == APP_DOC_PROVIDED_COLUMN:
                    return False

                else:
                    index.model().setData(index, 0, Qt.EditRole)
        return False
