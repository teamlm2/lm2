__author__ = 'anna'
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sqlalchemy.exc import SQLAlchemyError
from inspect import currentframe
from ...model import SettingsConstants
from ...model.LM2Exception import LM2Exception
from ...model.CtRecordDocument import CtRecordDocument
from ...model.CtDocument import CtDocument
from ...utils.FileUtils import FileUtils
from ...utils.PluginUtils import PluginUtils
from ...utils.DatabaseUtils import DatabaseUtils
from ...utils.SessionHandler import SessionHandler
from ...utils.FilePath import *
import shutil

PROVIDED_COLUMN = 0
FILE_TYPE_COLUMN = 1
FILE_NAME_COLUMN = 2
OPEN_FILE_COLUMN = 3
DELETE_COLUMN = 4
VIEW_COLUMN = 5


class RecordDocumentDelegate(QStyledItemDelegate):

    def __init__(self, widget, parent):

        super(RecordDocumentDelegate, self).__init__(parent)
        self.widget = widget
        self.parent = parent
        self.session = SessionHandler().session_instance()
        self.button = QPushButton("", parent)
        self.button.hide()

        self.remove = QIcon(":/plugins/lm2/remove.png")
        self.openIcon = QIcon(":/plugins/lm2/open.png")
        self.viewIcon = QIcon(":/plugins/lm2/file.png")

    def paint(self, painter, option, index):

        if index.column() == OPEN_FILE_COLUMN:
            self.button.setIcon(self.openIcon)
        elif index.column() == DELETE_COLUMN:
            self.button.setIcon(self.remove)
        elif index.column() == VIEW_COLUMN:
            self.button.setIcon(self.viewIcon)
        else:
            super(RecordDocumentDelegate, self).paint(painter, option, index)
            return

        self.button.setGeometry(option.rect)
        button_picture = QPixmap.grabWidget(self.button)
        painter.drawPixmap(option.rect.x(), option.rect.y(), button_picture)

    def editorEvent(self, event, model, option, index):

        if not index is None:

            if index.isValid()\
                    and event.type() == QEvent.MouseButtonRelease:
                record_no = self.parent.current_parent_object_no()
                record_no = record_no.replace("/", "-")
                default_path = FilePath.ownership_file_path() + '/' + record_no

                if not os.path.exists(default_path):
                    os.makedirs(default_path)

                if event.button() == Qt.RightButton:
                    return False

                if index.column() == OPEN_FILE_COLUMN:

                    file_dialog = QFileDialog()
                    file_dialog.setFilter('PDF (*.pdf)')
                    file_dialog.setModal(True)
                    file_dialog.setFileMode(QFileDialog.ExistingFile)
                    if file_dialog.exec_():
                        selected_file = file_dialog.selectedFiles()[0]

                        file_info = QFileInfo(selected_file)

                        if QFileInfo(file_info).size()/(1024*1024) > 5:
                            PluginUtils.show_error(self.parent, self.tr("File size exceeds limit!"), self.tr("The maximum size of documents to be attached is 5 MB."))
                            return False

                        role = self.widget.item(index.row(), FILE_TYPE_COLUMN).data(Qt.UserRole)
                        try:
                            file_name = record_no + "-" + str(role) + "." + file_info.suffix()
                            self.widget.item(index.row(), FILE_NAME_COLUMN).setText(file_name)
                            shutil.copy2(selected_file, default_path+'/'+file_name)

                            check_item = self.widget.item(index.row(), PROVIDED_COLUMN)
                            check_item.setCheckState(True)

                        except SQLAlchemyError, e:
                            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Could not execute: {0}").format(e.message))
                            return True

                elif index.column() == VIEW_COLUMN:

                    try:
                        file_name = self.widget.item(index.row(), FILE_NAME_COLUMN).text()
                        if file_name != '':
                            shutil.copy2(default_path + '/'+file_name, FilePath.view_file_path())
                            QDesktopServices.openUrl(QUrl.fromLocalFile(FilePath.view_file_path()))

                    except SQLAlchemyError, e:
                            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Could not execute: {0}").format(e.message))
                            return True

                elif index.column() == DELETE_COLUMN:

                    message_box = QMessageBox()
                    message_box.setText(self.tr("Do you want to delete the selected document?"))

                    delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
                    message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
                    message_box.exec_()

                    if message_box.clickedButton() == delete_button:
                        try:
                            check_item = self.widget.item(index.row(), PROVIDED_COLUMN)
                            check_item.setCheckState(False)
                            self.widget.item(index.row(), FILE_NAME_COLUMN).setText("")
                        except SQLAlchemyError, e:
                            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Could not execute: {0}").format(e.message))
                            return True

                elif index.column() == PROVIDED_COLUMN:
                    if index.data(Qt.CheckStateRole) == Qt.Unchecked:
                        item = self.widget.item(index.row(), PROVIDED_COLUMN)
                        item.setCheckState(Qt.Checked)
                    else:
                        item = self.widget.item(index.row(), PROVIDED_COLUMN)
                        item.setCheckState(Qt.Unchecked)

                elif index.column() == FILE_TYPE_COLUMN or index.column() == FILE_NAME_COLUMN:
                    return False

                else:
                    index.model().setData(index, 0, Qt.EditRole)
        return False
