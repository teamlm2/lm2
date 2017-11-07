__author__ = 'anna'
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sqlalchemy.exc import SQLAlchemyError

from ...model.SetOfficialDocument import SetOfficialDocument
from ...utils.FileUtils import FileUtils
from ...utils.PluginUtils import PluginUtils
from ...utils.SessionHandler import SessionHandler
from ...utils.DatabaseUtils import *
from ...utils.FilePath import *
import shutil

VISIBLE_COLUMN = 0
NAME_COLUMN = 1
DESCRIPTION_COLUMN = 2
OPEN_FILE_COLUMN = 3
VIEW_COLUMN = 4


class OfficialDocumentDelegate(QStyledItemDelegate):

    def __init__(self, widget, parent):

        super(OfficialDocumentDelegate, self).__init__(parent)
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
        elif index.column() == VIEW_COLUMN:
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
                if index.column() == OPEN_FILE_COLUMN:

                    file_dialog = QFileDialog()
                    file_dialog.setModal(True)
                    file_dialog.setFileMode(QFileDialog.ExistingFile)
                    if file_dialog.exec_():

                        selected_file = file_dialog.selectedFiles()[0]
                        file_info = QFileInfo(selected_file)
                        if QFileInfo(file_info).size()/(1024*1024) > 21:
                            PluginUtils.show_error(self.parent, self.tr("File size exceeds limit!"), self.tr("The maximum size of documents to be attached is 5 MB."))
                            return False

                        num = []
                        working_soum = DatabaseUtils.working_l2_code()
                        if self.widget.rowCount() == 0:
                            file_name = working_soum +'-doc-'+ '01.pdf'
                            num.append(int(file_name[-6]+file_name[-5]))
                        else:
                            for i in range(self.widget.rowCount()):
                                doc_name_item = self.widget.item(i, NAME_COLUMN)
                                doc_name_no = doc_name_item.text()
                                num.append(int(doc_name_no[-6]+doc_name_no[-5]))

                            max_num = max(num)
                            max_num = str(max_num+1)
                            if len((max_num)) == 1:
                                max_num = '0'+(max_num)
                            file_name = working_soum +'-doc-'+ (max_num)+'.pdf'

                        self.widget.item(index.row(), NAME_COLUMN).setText(file_name)
                        self.widget.item(index.row(), OPEN_FILE_COLUMN).setData(Qt.UserRole, file_info.filePath())
                        shutil.copy2(selected_file, archive_legaldocuments_path+'/'+file_name)

                elif index.column() == VIEW_COLUMN:

                    try:
                        file_name = self.widget.item(index.row(), NAME_COLUMN).text()
                        if file_name != '':
                            shutil.copy2(archive_legaldocuments_path + '/'+file_name, FilePath.view_file_path())
                            QDesktopServices.openUrl(QUrl.fromLocalFile(FilePath.view_file_path()))
                    except SQLAlchemyError, e:
                            PluginUtils.show_error(self.parent, self.tr("File Error"), self.tr("Could not execute: {0}").format(e.message))
                            return True

                elif index.column() == VISIBLE_COLUMN:
                    if index.data(Qt.CheckStateRole) == Qt.Unchecked:
                        item = self.widget.item(index.row(), VISIBLE_COLUMN)
                        item.setCheckState(Qt.Checked)
                    else:
                        item = self.widget.item(index.row(), VISIBLE_COLUMN)
                        item.setCheckState(Qt.Unchecked)

                elif index.column() == DESCRIPTION_COLUMN or index.column() == NAME_COLUMN:
                    return True

                else:
                    index.model().setData(index, 0, Qt.EditRole)
        return False
