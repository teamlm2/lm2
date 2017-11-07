__author__ = 'topmap'
# coding=utf8
import os
import xlsxwriter
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *
from qgis.core import *
from qgis.gui import *
from inspect import currentframe
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from xlrd import open_workbook
from ..view.Ui_DraftDecisionDialog import *
from ..utils.SessionHandler import SessionHandler
from ..model.CtApplicationStatus import *
from ..model import Constants
from ..model.DatabaseHelper import *
from ..utils.PluginUtils import PluginUtils
from ..model.CtApplication import *
from ..model.BsPerson import *
from ..model.ClDecisionLevel import *
from ..model.ClDecision import *
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.AuLevel3 import *
from ..utils.DatabaseUtils import *
from .qt_classes.ComboBoxDelegate import *
from .qt_classes.DropLabel import DropLabel
from .qt_classes.IntegerSpinBoxDelegate import *
from .qt_classes.ObjectAppDocumentDelegate import ObjectAppDocumentDelegate
from .qt_classes.ContractDocumentDelegate import ContractDocumentDelegate
from .qt_classes.ApplicantDocumentDelegate import ApplicationDocumentDelegate
from .qt_classes.DocumentsTableWidget import DocumentsTableWidget
from .qt_classes.DragTableWidget import DragTableWidget
from .qt_classes.DoubleSpinBoxDelegate import DoubleSpinBoxDelegate
from .qt_classes.DropLabel import DropLabel

class DraftDecisionPrintDialog(QDialog, Ui_DraftDecisionPrintDialog, DatabaseHelper):

    def __init__(self, type, parent=None):

        super(DraftDecisionPrintDialog,  self).__init__(parent)
        DatabaseHelper.__init__(self)
        self.setupUi(self)

        self.type = type
        self.setWindowTitle(self.tr("Print Decision Draft Dialog"))
        self.session = SessionHandler().session_instance()
        self.close_button.clicked.connect(self.reject)

    def __drafts_twidget(self):

        if self.drafts_edit.text() == "":
            PluginUtils.show_message(self,self.tr("no dir"),self.tr("no dir"))
            return
        self.drafts_twidget.setRowCount(0)
        count = 0
        if self.type == 0:
            for file in os.listdir(self.drafts_edit.text()):
                if file.endswith(".xlsx") and str(file)[:5] == "draft":
                    item_name = QTableWidgetItem(str(file))
                    item_name.setCheckState(Qt.Unchecked)
                    item_name.setData(Qt.UserRole,file)
                    item_name.setFlags(QtCore.Qt.ItemIsEnabled)
                    self.drafts_twidget.insertRow(count)
                    self.drafts_twidget.setItem(count,0,item_name)
                    count +=1
        elif self.type == 1:
            for file in os.listdir(self.drafts_edit.text()):
                if file.endswith(".xlsx") and str(file)[:8] == "decision":
                    item_name = QTableWidgetItem(str(file))
                    item_name.setCheckState(Qt.Unchecked)
                    item_name.setData(Qt.UserRole,file)
                    item_name.setFlags(QtCore.Qt.ItemIsEnabled)
                    self.drafts_twidget.insertRow(count)
                    self.drafts_twidget.setItem(count,0,item_name)
                    count +=1

    @pyqtSlot()
    def on_drafts_path_button_clicked(self):

        file_dialog = QFileDialog()
        file_dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        file_dialog.setModal(True)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        if file_dialog.exec_():

            selected_file = file_dialog.selectedFiles()[0]
            file_path = QFileInfo(selected_file).path()
            self.drafts_edit.setText(file_path)
            self.draft_detail_twidget.setRowCount(0)
            self.__drafts_twidget()

    @pyqtSlot(QTableWidgetItem)
    def on_drafts_twidget_itemClicked(self, item):

        current_row = self.drafts_twidget.currentRow()
        item = self.drafts_twidget.item(current_row,0)
        draft_id = item.data(Qt.UserRole)
        file_name = self.drafts_edit.text() + '/' +draft_id
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
            self.__remove_xls_file(file_name)
        else:
            item.setCheckState(Qt.Checked)
            self.__read_xls_file(file_name)

    def __remove_xls_file(self, file_name):

        if file_name == "":
            PluginUtils.show_message(self, self.tr("File operation"), self.tr("Please select a file."))
            return

        if not QFileInfo(file_name).exists():
            PluginUtils.show_message(self, self.tr("File operation"), self.tr("Invalid file."))
            return
        workbook = open_workbook(file_name)
        worksheet = workbook.sheet_by_name('Sheet1')
        if self.type == 0:
            for curr_row in range(worksheet.nrows-1):
                curr_row = curr_row + 1
                draft_no = worksheet.cell_value(curr_row, 8)
                for i in reversed(range(self.draft_detail_twidget.rowCount())):
                    draft = self.draft_detail_twidget.item(i, 8)
                    draft_number = draft.text()
                    if draft_no == draft_number:
                        self.draft_detail_twidget.removeRow(i)
        elif self.type == 1:
            for curr_row in range(worksheet.nrows-1):
                curr_row = curr_row + 1
                draft_no = worksheet.cell_value(curr_row, 1)
                for i in reversed(range(self.draft_detail_twidget.rowCount())):
                    draft = self.draft_detail_twidget.item(i, 8)
                    draft_number = draft.text()
                    if draft_no == draft_number:
                        self.draft_detail_twidget.removeRow(i)
    def __read_xls_file(self, file_name):

        if file_name == "":
            PluginUtils.show_message(self, self.tr("File operation"), self.tr("Please select a file."))
            return

        if not QFileInfo(file_name).exists():
            PluginUtils.show_message(self, self.tr("File operation"), self.tr("Invalid file."))
            return
        workbook = open_workbook(file_name)
        worksheet = workbook.sheet_by_name('Sheet1')
        count = 0
        app_no = ''
        surname = ''
        first_name = ''
        person_id = ''
        parcel_id = ''
        parcel_address = ''
        parcel_area = ''
        landuse_type = ''
        draft_no = ''
        draft_date = ''
        decision_level = ''
        decision_result = ''
        request_duration = ''
        bag_name = ''
        streetname = ''
        khashaa = ''

        for curr_row in range(worksheet.nrows-1):
            curr_row = curr_row + 1
            if self.type == 0:
                surname = worksheet.cell_value(curr_row, 0)
                first_name = worksheet.cell_value(curr_row, 1)
                person_id = worksheet.cell_value(curr_row, 2)
                app_no = worksheet.cell_value(curr_row, 3)
                parcel_id = worksheet.cell_value(curr_row, 4)

                parcel_address = worksheet.cell_value(curr_row, 5)
                parcel_area = worksheet.cell_value(curr_row, 6)

                landuse_type = worksheet.cell_value(curr_row, 7)
                draft_no = worksheet.cell_value(curr_row, 8)
                draft_date = worksheet.cell_value(curr_row, 9)
                decision_level = worksheet.cell_value(curr_row, 10)
                decision_result = worksheet.cell_value(curr_row, 11)
                request_duration = worksheet.cell_value(curr_row, 12)
            elif self.type == 1:
                app_no = worksheet.cell_value(curr_row, 0)
                application_count = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).count()
                if application_count == 1:
                    application = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
                    parcel_id = application.parcel
                    parcel_area = str(application.parcel_ref.area_m2)
                    bag = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(application.parcel_ref.geometry)).one()
                    if bag.name != None:
                        bag_name = bag.name
                    if application.parcel_ref.address_streetname != None:
                        streetname = application.parcel_ref.address_streetname
                    if application.parcel_ref.address_khashaa != None:
                        khashaa = application.parcel_ref.address_khashaa
                    parcel_address = bag_name +', '+ streetname +', '+ khashaa
                app_person_count = self.session.query(CtApplicationPersonRole)\
                            .filter(CtApplicationPersonRole.application == app_no)\
                            .filter(CtApplicationPersonRole.main_applicant == True).count()
                if app_person_count == 1:
                    app_person = self.session.query(CtApplicationPersonRole)\
                            .filter(CtApplicationPersonRole.application == app_no)\
                            .filter(CtApplicationPersonRole.main_applicant == True).one()
                    if app_person.person_ref.type == 10 or app_person.person_ref.type == 20 or app_person.person_ref.type == 50:
                        surname = app_person.person_ref.name
                        first_name = app_person.person_ref.first_name
                    elif app_person.person_ref.type == 30 or app_person.person_ref.type == 40 or app_person.person_ref.type == 60:
                        surname = u'Хуулийн этгээд'
                        first_name = app_person.person_ref.name
                    person_id = app_person.person_ref.person_id
                landuse_count = self.session.query(ClLanduseType).filter(ClLanduseType.code == int(worksheet.cell_value(curr_row, 6))).count()
                if landuse_count == 1:
                    landuse = self.session.query(ClLanduseType).filter(ClLanduseType.code == int(worksheet.cell_value(curr_row, 6))).one()
                    landuse_type = landuse.description
                level_count = self.session.query(ClDecisionLevel).filter(ClDecisionLevel.code == int(worksheet.cell_value(curr_row, 3))).count()
                if level_count == 1:
                    level = self.session.query(ClDecisionLevel).filter(ClDecisionLevel.code == int(worksheet.cell_value(curr_row, 3))).one()
                    decision_level = level.description
                result_count = self.session.query(ClDecision).filter(ClDecision.code == int(worksheet.cell_value(curr_row, 4))).count()
                if result_count == 1:
                    result = self.session.query(ClDecision).filter(ClDecision.code == int(worksheet.cell_value(curr_row, 4))).one()
                    decision_result = result.description
                draft_no = worksheet.cell_value(curr_row, 1)
                draft_date = worksheet.cell_value(curr_row, 2)
                request_duration = worksheet.cell_value(curr_row, 5)

            self.draft_detail_twidget.insertRow(count)

            item = QTableWidgetItem(surname)
            item.setData(Qt.UserRole, surname)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(first_name)
            item.setData(Qt.UserRole, first_name)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(person_id)
            item.setData(Qt.UserRole, person_id)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 2, item)

            item = QTableWidgetItem(app_no)
            item.setData(Qt.UserRole, app_no)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 3, item)

            item = QTableWidgetItem(parcel_id)
            item.setData(Qt.UserRole, parcel_id)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 4, item)

            item = QTableWidgetItem(parcel_address)
            item.setData(Qt.UserRole, parcel_address)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 5, item)

            item = QTableWidgetItem(parcel_area)
            item.setData(Qt.UserRole, parcel_area)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 6, item)

            item = QTableWidgetItem(landuse_type)
            item.setData(Qt.UserRole, landuse_type)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 7, item)

            item = QTableWidgetItem(draft_no)
            item.setData(Qt.UserRole, draft_no)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 8, item)

            item = QTableWidgetItem(draft_date)
            item.setData(Qt.UserRole, draft_date)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 9, item)

            item = QTableWidgetItem(decision_level)
            item.setData(Qt.UserRole, decision_level)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 10, item)

            item = QTableWidgetItem(decision_result)
            item.setData(Qt.UserRole, 20)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 11, item)

            item = QTableWidgetItem(request_duration)
            item.setData(Qt.UserRole, request_duration)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 12, item)

            count += 1

    @pyqtSlot()
    def on_doc_print_button_clicked(self):

        # path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        path = r"D:\ankhaa_d\TM_LM2\decision_draft/"
        workbook = xlsxwriter.Workbook(path + "SentToGovernor.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 12)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 18)
        worksheet.set_column('G:G', 9)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 12)
        worksheet.set_column('K:K', 15)
        worksheet.set_column('L:L', 15)
        worksheet.set_column('M:M', 10)

        worksheet.set_row(3,50)
        worksheet.set_landscape()
        worksheet.set_paper(8)
        worksheet.set_margins(left=0.3,right=0.3)

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(9)
        format.set_border(1)

        format1 = workbook.add_format()
        format1.set_text_wrap()
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_font_name('Times New Roman')
        format1.set_rotation(90)
        format1.set_font_size(9)
        format1.set_border(1)

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(14)
        format_header.set_bold()

        worksheet.write('A4',u'Овог', format)
        worksheet.write('B4',u'Нэр', format)
        worksheet.write('C4',u'Регистрийн дугаар', format)
        worksheet.write('D4',u'Өргөдлийн дугаар', format)
        worksheet.write('E4',u'Нэгж талбарын дугаар', format)
        worksheet.write('F4',u'Нэгж талбарын хаяг', format)
        worksheet.write('G4',u'Талбайн хэмжээ', format)
        worksheet.write('H4',u'Газар ашиглалтын зориулалт', format)
        if self.type == 0:
            worksheet.write('I4',u'Төслийн дугаар', format)
            worksheet.merge_range('A2:M2', u'Засаг даргын захирамжийн төсөлд явуулсан өргөдлийн жагсаалт',format_header)
        if self.type == 1:
            worksheet.write('I4',u'Захирамжийн дугаар', format)
            worksheet.merge_range('A2:M2', u'Засаг даргын захирамж гарсан өргөдлийн жагсаалт',format_header)
        worksheet.write('J4',u'Огноо', format)
        worksheet.write('K4',u'Захирамжийн түвшин', format)
        worksheet.write('L4',u'Төлөв', format)
        worksheet.write('M4',u'Хүсэлт гаргасан хугацаа', format)
        row = 4
        col = 0
        row_number = 1
        khashaa = ''
        streetname = ''
        bag_name = ''
        for i in reversed(range(self.draft_detail_twidget.rowCount())):

            item = self.draft_detail_twidget.item(i, 0)
            surname = item.text()

            item = self.draft_detail_twidget.item(i, 1)
            first_name = item.text()

            item = self.draft_detail_twidget.item(i, 2)
            person_id = item.text()

            item = self.draft_detail_twidget.item(i, 3)
            app_no = item.text()

            item = self.draft_detail_twidget.item(i, 4)
            parcel_id = item.text()

            item = self.draft_detail_twidget.item(i, 5)
            parcel_address = item.text()

            item = self.draft_detail_twidget.item(i, 6)
            parcel_area = item.text()

            item = self.draft_detail_twidget.item(i, 7)
            landuse = item.text()

            item = self.draft_detail_twidget.item(i, 8)
            draft_id = item.text()

            item = self.draft_detail_twidget.item(i, 9)
            draft_date = item.text()

            item = self.draft_detail_twidget.item(i, 10)
            decision_level = item.text()

            item = self.draft_detail_twidget.item(i, 11)
            decision_result = item.text()

            item = self.draft_detail_twidget.item(i, 12)
            duration = item.text()

            worksheet.write(row, col, surname, format)
            worksheet.write(row, col+1, first_name, format)
            worksheet.write(row, col+2, person_id, format)
            worksheet.write(row, col+3, app_no, format)
            worksheet.write(row, col+4, parcel_id, format)
            worksheet.write(row, col+5, parcel_address, format)
            worksheet.write(row, col+6, parcel_area, format)
            worksheet.write(row, col+7, landuse, format)
            worksheet.write(row, col+8, draft_id, format)
            worksheet.write(row, col+9, draft_date, format)
            worksheet.write(row, col+10, decision_level, format)
            worksheet.write(row, col+11, decision_result, format)
            worksheet.write(row, col+12, duration, format)

            row += 1
            row_number += 1

        workbook.close()
        QDesktopServices.openUrl(QUrl.fromLocalFile(path+"SentToGovernor.xlsx"))