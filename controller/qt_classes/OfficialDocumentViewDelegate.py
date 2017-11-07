__author__ = 'anna'
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sqlalchemy.exc import SQLAlchemyError
from ...model import SettingsConstants
from ...model.SetOfficialDocument import SetOfficialDocument
from ...utils.FileUtils import FileUtils
from ...utils.PluginUtils import PluginUtils
from ...utils.SessionHandler import SessionHandler
from ...utils.DatabaseUtils import *
from ...utils.FilePath import *
import shutil
NAME_COLUMN = 0
DESCRIPTION_COLUMN = 1
VIEW_COLUMN = 2


class OfficialDocumentDelegate(QStyledItemDelegate):

    def __init__(self, widget, parent):

        super(OfficialDocumentDelegate, self).__init__(parent)
        self.widget = widget
        self.parent = parent
        self.session = SessionHandler().session_instance()
        self.button = QPushButton("", parent)
        self.button.hide()

        self.viewIcon = QIcon(":/plugins/lm2/file.png")

    def paint(self, painter, option, index):

        if index.column() == VIEW_COLUMN:
            self.button.setIcon(self.viewIcon)
        else:
            super(OfficialDocumentDelegate, self).paint(painter, option, index)
            return

        self.button.setGeometry(option.rect)
        button_picture = QPixmap.grabWidget(self.button)
        painter.drawPixmap(option.rect.x(), option.rect.y(), button_picture)

    def editorEvent(self, event, model, option, index):

        if index is not None:

            if index.isValid() and event.type() == QEvent.MouseButtonRelease:

                working_aimag = DatabaseUtils.working_l1_code()
                working_soum = DatabaseUtils.working_l2_code()
                archive_legaldocuments_path = FilePath.legaldocuments_file_path()
                if not os.path.exists(archive_legaldocuments_path):
                    os.makedirs(archive_legaldocuments_path)

                if event.button() == Qt.RightButton:
                    return False

                if index.column() == VIEW_COLUMN:

                    try:
                        file_name = self.widget.item(index.row(), NAME_COLUMN).text()
                        if file_name != '':
                            shutil.copy2(archive_legaldocuments_path + '/'+file_name, FilePath.view_file_path())
                            QDesktopServices.openUrl(QUrl.fromLocalFile(FilePath.view_file_path()))
                    except SQLAlchemyError, e:
                            PluginUtils.show_error(self.parent, self.tr("File Error"), self.tr("Could not execute: {0}").format(e.message))
                            return True

                elif index.column() == DESCRIPTION_COLUMN or index.column() == NAME_COLUMN:
                    return True

                else:
                    index.model().setData(index, 0, Qt.EditRole)
        return False
