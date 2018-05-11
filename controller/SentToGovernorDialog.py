__author__ = 'B.Ankhbold'
# coding=utf8
import os
import xlsxwriter
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *
from qgis.core import *
from qgis.gui import *
from inspect import currentframe
from datetime import timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_, and_, desc
from xlrd import open_workbook
from ..view.Ui_SentToGovernorDialog import *
from ..utils.SessionHandler import SessionHandler
from ..model.CtApplicationStatus import *
from ..model.CtDecision import *
from ..model.DatabaseHelper import *
from ..utils.PluginUtils import PluginUtils
from ..model.ApplicationSearch import *
from ..model.ContractSearch import *
from ..model.BsPerson import *
from ..model.ClDecisionLevel import *
from ..model.ClDecision import *
from ..model.ClCountryList import *
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.AuLevel3 import *
from ..model.SetTaxAndPriceZone import *
from ..model.SetBaseTaxAndPrice import *
from ..model.Enumerations import ApplicationType, UserRight
from ..utils.DatabaseUtils import *
from .qt_classes.ComboBoxDelegate import *
from .qt_classes.DropLabel import DropLabel
from .qt_classes.IntegerSpinBoxDelegate import *
from .qt_classes.ObjectAppDocumentDelegate import ObjectAppDocumentDelegate
from .qt_classes.ContractDocumentDelegate import ContractDocumentDelegate
from docxtpl import DocxTemplate, RichText

class SentToGovernorDialog(QDialog, Ui_SentToGovernorDialog, DatabaseHelper):

    def __init__(self, parent=None):

        super(SentToGovernorDialog,  self).__init__(parent)
        DatabaseHelper.__init__(self)
        self.setupUi(self)

        self.setWindowTitle(self.tr("Sent and prepare governor decision Dialog"))
        self.session = SessionHandler().session_instance()
        self.__setup_validators()
        self.__app_status_count()
        self.close_button.clicked.connect(self.reject)
        self.__setup_combo_boxes()
        self.begin_date.setDateTime(QDateTime().currentDateTime())

        begin_qt_date = self.begin_date.date().toString(Constants.DATABASE_DATE_FORMAT)
        p_begin_date = datetime.strptime(str(begin_qt_date), Constants.PYTHON_DATE_FORMAT)
        p_begin_date = p_begin_date  - timedelta(days=1)
        self.begin_date.setDateTime(p_begin_date)

        self.end_date.setDateTime(QDateTime().currentDateTime())
        self.draft_date.setDateTime(QDateTime().currentDateTime())
        self.decision_date.setDateTime(QDateTime().currentDateTime())
        self.__set_up_draft_detail_twidget()
        self.select_app_count.setText(str(0)+'/')
        self.tabWidget.currentChanged.connect(self.onChangetab)
        self.is_tmp_parcel = False
        self.app_no = None

    def __setup_validators(self):

        self.int_validator = QRegExpValidator(QRegExp("[0-9]+"), None)
        self.draft_no_edit.setValidator(self.int_validator)

    def __setup_twidget(self, table_widget):

        table_widget.setAlternatingRowColors(True)
        table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        table_widget.setSelectionMode(QTableWidget.SingleSelection)

    def __set_up_draft_detail_twidget(self):

        self.drafts_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.drafts_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.drafts_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.drafts_twidget.setSortingEnabled(True)

    def __app_status_count(self):

        app_count = ""
        try:
            app_count = self.session.query(CtApplicationStatus.application, func.max(CtApplicationStatus.status_date))\
                .group_by(CtApplicationStatus.application)\
                .having(func.max(CtApplicationStatus.status) == Constants.APP_STATUS_WAITING).distinct().count()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self.iface.mainWindow(), QApplication.translate("Plugin", "Error executing"), e.message)

        self.app_count_lbl.setText(str(app_count))

    def __setup_combo_boxes(self):

        soum_code = ''
        au_level2 = DatabaseUtils.current_working_soum_schema()
        soum_code = str(au_level2)[3:]
        try:
            user = DatabaseUtils.current_user()
            officers = self.session.query(SetRole) \
                .filter(SetRole.user_name == user.user_name) \
                .filter(SetRole.is_active == True).one()

            application_types = self.session.query(ClApplicationType).all()

            set_roles = self.session.query(SetRole).all()
            set_role = self.session.query(SetRole).filter(SetRole.user_name_real == officers.user_name_real).one()
            aimag_code = set_role.working_au_level1
            aimag_code = aimag_code[:2]
        except SQLAlchemyError, e:
            PluginUtils.show_error(self.iface.mainWindow(), QApplication.translate("Plugin", "Error executing"), e.message)

        self.officer_cbox.addItem("*", -1)
        self.decision_level_cbox.clear()
        try:
            for item in application_types:
                self.app_type_cbox.addItem(item.description, item.code)
            # if aimag_code == '01' or aimag_code == '12':
            #     decision_level = self.session.query(ClDecisionLevel).filter(or_(ClDecisionLevel.code == 10, ClDecisionLevel.code == 20)).all()
            #     for item in decision_level:
            #         self.decision_level_cbox.addItem(item.description, item.code)
            # else:
            #     if soum_code == '01':
            #         decision_level = self.session.query(ClDecisionLevel).filter(or_(ClDecisionLevel.code == 30, ClDecisionLevel.code == 40, ClDecisionLevel.code == 50, ClDecisionLevel.code == 60)).all()
            #         for item in decision_level:
            #             self.decision_level_cbox.addItem(item.description, item.code)
            #         # self.decision_level_cbox.setCurrentIndex(2)
            #     else:
            #         decision_level = self.session.query(ClDecisionLevel).filter(or_(ClDecisionLevel.code == 40, ClDecisionLevel.code == 50, ClDecisionLevel.code == 60)).all()
            #         for item in decision_level:
            #             self.decision_level_cbox.addItem(item.description, item.code)
            #         # self.decision_level_cbox.setCurrentIndex(3)
            soum_code = DatabaseUtils.working_l2_code()
            if set_roles is not None:
                for role in set_roles:
                    l2_code_list = role.restriction_au_level2.split(',')
                    if soum_code in l2_code_list:
                    # if role.user_name_real.find(restrictions[1:]) != -1:
                        self.officer_cbox.addItem(role.surname + ", " + role.first_name, role)
        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))


    def __remove_application_items(self):

        self.draft_detail_twidget.setRowCount(0)

    @pyqtSlot()
    def on_search_button_clicked(self):

        self.draft_no_edit.setText('')
        self.draft_detail_twidget.setRowCount(0)
        begin_qt_date = self.begin_date.date().toString(Constants.DATABASE_DATE_FORMAT)
        p_begin_date = datetime.strptime(str(begin_qt_date), Constants.PYTHON_DATE_FORMAT)

        end_qt_date = self.end_date.date().toString(Constants.DATABASE_DATE_FORMAT)
        p_end_date = datetime.strptime(str(end_qt_date), Constants.PYTHON_DATE_FORMAT)
        p_end_date = p_end_date  + timedelta(days=1)

        application_type = self.app_type_cbox.itemData(self.app_type_cbox.currentIndex())
        try:
            applications = self.session.query(ApplicationSearch)
            sub = self.session.query(ApplicationSearch, func.row_number().over(partition_by = ApplicationSearch.app_no, order_by = (desc(ApplicationSearch.status_date), desc(ApplicationSearch.status))).label("row_number")).subquery()
            applications = applications.select_entity_from(sub).filter(sub.c.row_number == 1)
            status = 5

            applications = applications.filter(ApplicationSearch.status == status)
            if not self.officer_cbox.itemData(self.officer_cbox.currentIndex()) == -1:
                officer = "%" + self.officer_cbox.itemData(self.officer_cbox.currentIndex()).user_name_real + "%"

                applications = applications.filter(ApplicationSearch.next_officer_in_charge.ilike(officer))

            decision_result = self.session.query(ClDecision).filter(ClDecision.code == 20).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self.iface.mainWindow(), QApplication.translate("Plugin", "Error executing"), e.message)

        self.__remove_application_items()
        count = 0

        for app in applications:

            application = app.app_no
            streetname = ''
            khashaa = ''
            bag_name = ''
            application_instance = self.session.query(CtApplication).filter(CtApplication.app_no == application).one()

            if int(application[6:-9]) == (self.app_type_cbox.itemData(self.app_type_cbox.currentIndex())) and application_instance.app_timestamp >= p_begin_date and application_instance.app_timestamp <= p_end_date:

                app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == application).\
                    filter(CtApplicationPersonRole.role == 70).count()
                if app_person > 0:
                    app_person = self.session.query(CtApplicationPersonRole).filter(
                        CtApplicationPersonRole.application == application).filter(CtApplicationPersonRole.role == 70).all()
                else:
                    app_person = self.session.query(CtApplicationPersonRole).filter(
                        CtApplicationPersonRole.application == application).all()
                landuse_type = self.session.query(ClLanduseType).filter(ClLanduseType.code == application_instance.requested_landuse).one()
                parcel_count = self.session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == application_instance.tmp_parcel).count()
                if parcel_count == 0:
                    parcel_count = self.session.query(CaParcel).filter(CaParcel.parcel_id == application_instance.parcel).count()
                    if parcel_count != 0:
                        parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == application_instance.parcel).one()
                    else:
                        PluginUtils.show_message(self, self.tr("parcel none"), self.tr("None Parcel!!!"))
                        return
                else:
                    parcel = self.session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == application_instance.tmp_parcel).one()
                if parcel_count != 0:
                    bag_count = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(parcel.geometry)).count()
                    if bag_count == 1:
                        bag = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(parcel.geometry)).one()
                        if bag.name != None:
                            bag_name = bag.name


                    if parcel.address_streetname != None:
                        streetname = parcel.address_streetname
                    if parcel.address_khashaa != None:
                        khashaa = parcel.address_khashaa
                    parcel_address = bag_name +', '+ streetname +', '+ khashaa
                for p in app_person:
                    if p.main_applicant == True:
                        person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()

                self.draft_detail_twidget.insertRow(count)

                item = QTableWidgetItem(person.name)
                item.setData(Qt.UserRole, person.name)
                self.draft_detail_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(person.first_name)
                item.setData(Qt.UserRole, person.first_name)
                self.draft_detail_twidget.setItem(count, 1, item)

                item = QTableWidgetItem(person.person_id)
                item.setData(Qt.UserRole, person.person_id)
                self.draft_detail_twidget.setItem(count, 2, item)

                item = QTableWidgetItem(application_instance.app_no)
                item.setData(Qt.UserRole, application_instance.app_no)
                self.draft_detail_twidget.setItem(count, 3, item)

                item = QTableWidgetItem(parcel.parcel_id)
                item.setData(Qt.UserRole, parcel.parcel_id)
                self.draft_detail_twidget.setItem(count, 4, item)

                item = QTableWidgetItem(parcel_address)
                item.setData(Qt.UserRole, parcel_address)
                self.draft_detail_twidget.setItem(count, 5, item)

                item = QTableWidgetItem(str(parcel.area_m2))
                item.setData(Qt.UserRole, parcel.area_m2)
                self.draft_detail_twidget.setItem(count, 6, item)

                item = QTableWidgetItem(landuse_type.description)
                item.setData(Qt.UserRole, landuse_type.code)
                self.draft_detail_twidget.setItem(count, 7, item)

                item = QTableWidgetItem(self.draft_no_edit.text())
                item.setData(Qt.UserRole, self.draft_no_edit.text())
                self.draft_detail_twidget.setItem(count, 8, item)

                item = QTableWidgetItem(self.draft_date.text())
                item.setData(Qt.UserRole, self.draft_date.text())
                self.draft_detail_twidget.setItem(count, 9, item)

                item = QTableWidgetItem(self.decision_level_cbox.itemText(self.decision_level_cbox.currentIndex()))
                item.setData(Qt.UserRole, self.decision_level_cbox.itemData(self.decision_level_cbox.currentIndex()))
                self.draft_detail_twidget.setItem(count, 10, item)

                item = QTableWidgetItem(decision_result.description)
                item.setData(Qt.UserRole, decision_result.code)
                self.draft_detail_twidget.setItem(count, 11, item)

                item = QTableWidgetItem(str(application_instance.requested_duration))
                item.setData(Qt.UserRole, application_instance.requested_duration)
                self.draft_detail_twidget.setItem(count, 12, item)

                count += 1
        self.select_app_count.setText(str(count) + '/')
        if count != 0:
            self.sent_to_governor_button.setEnabled(True)
        else:
            self.sent_to_governor_button.setEnabled(False)

    def __drafts_twidget(self):

        if self.drafts_edit.text() == "":
            PluginUtils.show_message(self,self.tr("no dir"),self.tr("no dir"))
            return
        self.drafts_twidget.setRowCount(0)
        count = 0
        for file in os.listdir(self.drafts_edit.text()):
            if file.endswith(".xlsx") and str(file)[:5] == "draft":
                item_name = QTableWidgetItem(str(file))
                item_name.setData(Qt.UserRole,file)

                self.drafts_twidget.insertRow(count)
                self.drafts_twidget.setItem(count,0,item_name)
                count +=1
    @pyqtSlot()
    def on_drafts_path_button_clicked(self):

        default_path = r'D:/TM_LM2/decision_draft'
        default_parent_path = r'D:/TM_LM2'
        if not os.path.exists(default_parent_path):
            os.makedirs('D:/TM_LM2')
            os.makedirs('D:/TM_LM2/application_response')
            os.makedirs('D:/TM_LM2/application_list')
            os.makedirs('D:/TM_LM2/approved_decision')
            os.makedirs('D:/TM_LM2/cad_maintenance')
            os.makedirs('D:/TM_LM2/cad_maps')
            os.makedirs('D:/TM_LM2/contracts')
            os.makedirs('D:/TM_LM2/decision_draft')
            os.makedirs('D:/TM_LM2/dumps')
            os.makedirs('D:/TM_LM2/q_data')
            os.makedirs('D:/TM_LM2/refused_decision')
            os.makedirs('D:/TM_LM2/reports')
            os.makedirs('D:/TM_LM2/training')
        if not os.path.exists(default_path):
            os.makedirs(default_path)
        workbook = xlsxwriter.Workbook(default_path+'/'+'default.xlsx')
        worksheet = workbook.add_worksheet()
        file_dialog = QFileDialog()
        file_dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        file_dialog.setModal(True)
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setDirectory(default_path)
        if file_dialog.exec_():

            selected_file = file_dialog.selectedFiles()[0]
            file_path = QFileInfo(selected_file).path()
            file_name = QFileInfo(selected_file).fileName()
            self.drafts_edit.setText(file_path)
            self.__drafts_twidget()
            self.__drafts_twidget_2()

    @pyqtSlot()
    def on_sent_to_governor_button_clicked(self):

        row_num = self.drafts_twidget.rowCount()

        for row in range(row_num):
            item = self.drafts_twidget.item(row, 0)
            draft_id = item.data(Qt.UserRole)
            draft_id = draft_id[15:-5]
            if draft_id == self.draft_no_edit.text():
                PluginUtils.show_message(self, self.tr("File operation"), self.tr("Duplicated draft number!!!."))
                return

        select_app_count = self.draft_detail_twidget.rowCount()
        if select_app_count == 0:
            PluginUtils.show_message(self, self.tr("draft info"), self.tr("No select application!!!"))
            return

        if self.draft_no_edit.text() == "":
            PluginUtils.show_message(self, self.tr("draft info"), self.tr("None Decision Draft No!!!"))
            return
        if self.drafts_edit.text() == "":
            PluginUtils.show_message(self, self.tr("draft info"), self.tr("None Decision Draft Path No!!!"))
            return
        app_count = ""
        begin_qt_date = self.begin_date.date().toString(Constants.DATABASE_DATE_FORMAT)
        p_begin_date = datetime.strptime(str(begin_qt_date), Constants.PYTHON_DATE_FORMAT)

        end_qt_date = self.end_date.date().toString(Constants.DATABASE_DATE_FORMAT)
        p_end_date = datetime.strptime(str(end_qt_date), Constants.PYTHON_DATE_FORMAT)
        p_end_date = p_end_date  + timedelta(days=1)
        try:
            applications = self.session.query(ApplicationSearch)

            sub = self.session.query(ApplicationSearch, func.row_number().over(partition_by = ApplicationSearch.app_no, order_by = (desc(ApplicationSearch.status_date), desc(ApplicationSearch.status))).label("row_number")).subquery()
            applications = applications.select_entity_from(sub).filter(sub.c.row_number == 1)
            status = 5

            applications = applications.filter(ApplicationSearch.status == status)
            if not self.officer_cbox.itemData(self.officer_cbox.currentIndex()) == -1:
                officer = "%" + self.officer_cbox.itemData(self.officer_cbox.currentIndex()).user_name_real + "%"

                applications = applications.filter(ApplicationSearch.officer_in_charge.ilike(officer))

            stati = self.session.query(CtApplicationStatus.application, func.max(CtApplicationStatus.status_date))\
                .group_by(CtApplicationStatus.application)\
                .having(func.max(CtApplicationStatus.status) == Constants.APP_STATUS_WAITING).distinct()


            decision_result = self.session.query(ClDecision).filter(ClDecision.code == 20).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self.iface.mainWindow(), QApplication.translate("Plugin", "Error executing"), e.message)
        au_level2 = DatabaseUtils.current_working_soum_schema()

        current_user = DatabaseUtils.current_user()
        year_filter = str(QDate().currentDate().toString("yyyy"))
        month_filter = str(QDate().currentDate().toString("MM"))
        day_filter = str(QDate().currentDate().toString("dd"))

        file_name = 'draft_'+ year_filter + month_filter + day_filter + '_' + self.draft_no_edit.text()+'.xlsx'
        workbook = xlsxwriter.Workbook(self.drafts_edit.text()+'/'+file_name)
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 12)
        worksheet.set_column('D:D', 12)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 16)
        worksheet.set_column('G:G', 10)
        worksheet.set_column('H:H', 15)
        worksheet.set_column('I:I', 12)
        worksheet.set_column('J:J', 10)
        worksheet.set_column('K:K', 15)
        worksheet.set_column('L:L', 15)
        worksheet.set_column('M:M', 11)

        bold = workbook.add_format({'bold': True})

        worksheet.write('A1',u"Овог", bold)
        worksheet.write('B1',u"Нэр", bold)
        worksheet.write('C1',u"Регистрийн дугаар", bold)
        worksheet.write('D1',u"Өргөдлийн дугаар", bold)
        worksheet.write('E1',u"Нэгж талбарын дугаар", bold)

        worksheet.write('F1',u"Нэгж талбарын хаяг", bold)
        worksheet.write('G1',u"Талбайн хэмжээ", bold)

        worksheet.write('H1',u"Газар ашиглалтын зориулалт", bold)
        worksheet.write('I1',u"Төсөлийн дугаар", bold)
        worksheet.write('J1',u"Огноо", bold)
        worksheet.write('K1',u"Захирамжийн түвшин", bold)
        worksheet.write('L1',u"Төлөв", bold)
        worksheet.write('M1',u"Хүсэлт гаргасан хугацаа", bold)
        row = 1
        col = 0
        app_no_without_parcel = []
        count = 0
        for rw in range(self.draft_detail_twidget.rowCount()):
            app_no = self.draft_detail_twidget.item(rw,3)
            application = app_no.text()

            application_instance = self.session.query(CtApplication).filter(CtApplication.app_no == application).one()
            app_person = self.session.query(CtApplicationPersonRole).filter(
                CtApplicationPersonRole.application == application). \
                filter(CtApplicationPersonRole.role == 70).count()
            if app_person > 0:
                app_person = self.session.query(CtApplicationPersonRole).filter(
                    CtApplicationPersonRole.application == application).filter(CtApplicationPersonRole.role == 70).all()
            else:
                app_person = self.session.query(CtApplicationPersonRole).filter(
                    CtApplicationPersonRole.application == application).all()
            landuse_type = self.session.query(ClLanduseType).filter(ClLanduseType.code == application_instance.requested_landuse).one()
            for p in app_person:
                if p.main_applicant == True:
                    person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()
            if person.type == 10 or person.type == 20 or person == 50:
                first_name = person.first_name
            else:
                first_name = u"ААН"

            address_item = self.draft_detail_twidget.item(rw,5)
            parcel_address = address_item.text()

            parcel_id_item = self.draft_detail_twidget.item(rw,4)
            parcel_id = parcel_id_item.text()
            worksheet.write(row, col,person.name)
            worksheet.write(row, col+1,first_name)
            worksheet.write(row, col+2,person.person_id)
            worksheet.write(row, col+3,application)
            worksheet.write(row, col+4,parcel_id)

            worksheet.write(row, col+5,parcel_address)

            area_item = self.draft_detail_twidget.item(rw,6)
            parcel_area = area_item.text()

            worksheet.write(row, col+6,parcel_area)

            worksheet.write(row, col+7,landuse_type.description)
            worksheet.write(row, col+8,self.draft_no_edit.text())
            worksheet.write(row, col+9,self.draft_date.text())
            worksheet.write(row, col+10,self.decision_level_cbox.itemText(self.decision_level_cbox.currentIndex()))
            worksheet.write(row, col+11,decision_result.description)
            worksheet.write(row, col+12,str(application_instance.requested_duration))

            user = DatabaseUtils.current_user()
            officers = self.session.query(SetRole) \
                .filter(SetRole.user_name == user.user_name) \
                .filter(SetRole.is_active == True).one()

            new_status = CtApplicationStatus()
            new_status.application = application
            new_status.next_officer_in_charge = officers.user_name_real
            new_status.officer_in_charge = officers.user_name_real
            new_status.status = Constants.APP_STATUS_SEND
            new_status.status_date = datetime.now().strftime(Constants.PYTHON_DATE_FORMAT)
            self.session.add(new_status)
            row += 1

        self.session.commit()

        if len(app_no_without_parcel) > 0:
            app_no_string = ", ".join(app_no_without_parcel)
            QMessageBox.information(None, QApplication.translate("LM2", "Mark Applications"),
                                        QApplication.translate("LM2", "The following applications have no parcels assigned and could not be updated: {0} ".format(app_no_string)))

        workbook.close()
        self.__drafts_twidget()
        self.__drafts_twidget_2()
        self.draft_detail_twidget.setRowCount(0)
        self.__app_status_count()
        QMessageBox.information(self,self.tr("Sent To Governor"), self.tr("Successful"))
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.drafts_edit.text()+file_name))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    @pyqtSlot(QTableWidgetItem)
    def on_drafts_twidget_itemClicked(self, item):

        self.sent_to_governor_button.setDisabled(True)

        num_rows = self.draft_detail_twidget.rowCount()

        session = SessionHandler().session_instance()
        current_column = self.drafts_twidget.currentColumn()
        current_row = self.drafts_twidget.currentRow()
        item = self.drafts_twidget.item(current_row,0)
        draft_id = item.data(Qt.UserRole)
        file_name = self.drafts_edit.text() + '/' +draft_id

        self.__read_xls_file(file_name)

        self.draft_no_edit.setText(draft_id[15:-5])

    def __read_xls_file(self, file_name):

        if file_name == "":
            PluginUtils.show_message(self, self.tr("File operation"), self.tr("Please select a file."))
            return

        if not QFileInfo(file_name).exists():
            PluginUtils.show_message(self, self.tr("File operation"), self.tr("Invalid file."))
            return
        workbook = open_workbook(file_name)
        worksheet = workbook.sheet_by_name('Sheet1')
        # num_rows = worksheet.nrows - 1
        # num_cells = worksheet.ncols - 1
        # curr_row = -1
        self.draft_detail_twidget.setRowCount(0)
        count = 0

        for curr_row in range(worksheet.nrows-1):

            curr_row = curr_row + 1
            row = worksheet.row(curr_row)
            surname = worksheet.cell_value(curr_row, 0)

            first_name = worksheet.cell_value(curr_row, 1)
            person_id = worksheet.cell_value(curr_row, 2)

            app_no = worksheet.cell_value(curr_row, 3)
            self.app_no = app_no
            parcel_id = (worksheet.cell_value(curr_row, 4))

            parcel_address = worksheet.cell_value(curr_row, 5)
            parcel_area = worksheet.cell_value(curr_row, 6)

            landuse_type = worksheet.cell_value(curr_row, 7)
            draft_no = worksheet.cell_value(curr_row, 8)
            draft_date = worksheet.cell_value(curr_row, 9)
            decision_level = worksheet.cell_value(curr_row, 10)
            decision_result = worksheet.cell_value(curr_row, 11)
            request_duration = worksheet.cell_value(curr_row, 12)

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

            item = QTableWidgetItem(str(parcel_area))
            item.setData(Qt.UserRole, parcel_area)
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 6, item)

            item = QTableWidgetItem(landuse_type)
            item.setData(Qt.UserRole, landuse_type)
            if self.tabWidget.currentIndex() == 0:
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

            if self.tabWidget.currentIndex() == 1:
                descriptions = self.session.query(ClDecision).filter(ClDecision.code == 10).one()
                item = QTableWidgetItem(descriptions.description)
                item.setData(Qt.UserRole, descriptions.code)
                if self.tabWidget.currentIndex() == 0:
                    item.setFlags(QtCore.Qt.ItemIsEnabled)
                self.draft_detail_twidget.setItem(count, 11, item)
            else:
                item = QTableWidgetItem(decision_result)
                item.setData(Qt.UserRole, 20)
                if self.tabWidget.currentIndex() == 0:
                    item.setFlags(QtCore.Qt.ItemIsEnabled)
                self.draft_detail_twidget.setItem(count, 11, item)

            item = QTableWidgetItem(request_duration)
            item.setData(Qt.UserRole, request_duration)
            if self.tabWidget.currentIndex() == 0:
                item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.draft_detail_twidget.setItem(count, 12, item)

            count += 1

    @pyqtSlot()
    def on_doc_print_button_clicked(self):

        if self.draft_detail_twidget.rowCount() == 0:
            PluginUtils.show_message(self,self.tr("List None"),self.tr("Draft list null!!!"))
            return
        if self.drafts_twidget.rowCount() == 0:
            PluginUtils.show_message(self,self.tr("List None"),self.tr("Drafts list null!!!"))
            return
        if self.draft_no_edit.text() == "":
            PluginUtils.show_message(self,self.tr("Draft No None"),self.tr("Draft No null!!!"))
            return

        select_item = self.drafts_twidget.selectedItems()
        name_item = select_item[0]
        file_name = name_item.data(Qt.UserRole)
        num_rows = self.draft_detail_twidget.rowCount()
        for row in range(num_rows):
            date = self.draft_detail_twidget.item(row, 9)
            draft_date = date.text()

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to print for draft doc of governor decision"))

        yes_button = message_box.addButton(self.tr("Yes"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("No"), QMessageBox.ActionRole)
        message_box.exec_()

        if message_box.clickedButton() == yes_button:
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.drafts_edit.text()+"/"+file_name))
            except IOError, e:
                PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    @pyqtSlot()
    def on_change_button_clicked(self):

        if len(self.drafts_twidget_2.selectedItems()) == 0:
            PluginUtils.show_message(self, self.tr("Draft path"), self.tr("Select draft list!"))
            return
        if len(self.drafts_twidget_2.selectedItems()) > 1:
            PluginUtils.show_message(self, self.tr("Draft path"), self.tr("2 tusul songoh bolomjhui"))
            return

        if self.drafts_edit.text() == "":
            PluginUtils.show_message(self, self.tr("Draft path"), self.tr("Choose the draft path first!"))
            return

        if self.draft_detail_twidget.rowCount() == 0:
            PluginUtils.show_message(self, self.tr("Decision list"), self.tr("Application list is empty. Choose the draft decision!"))
            return

        if self.decision_number_edit.text() == "":
            PluginUtils.show_message(self, self.tr("Decision No"), self.tr("Please enter decision number!"))
            return
        au_level2 = DatabaseUtils.current_working_soum_schema()
        year_filter = str(QDate().currentDate().toString("yyyy"))
        num_rows, num_cols = self.draft_detail_twidget.rowCount(), self.draft_detail_twidget.columnCount()

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to insert the decision number?"))

        yes_button = message_box.addButton(self.tr("Yes"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("No"), QMessageBox.ActionRole)
        message_box.exec_()

        if message_box.clickedButton() == yes_button:

            for row in range(num_rows):
                try:
                    item = self.draft_detail_twidget.item(row, 3)
                    app_no = item.data(Qt.UserRole)
                    application_count = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).count()
                    if application_count == 0:
                        PluginUtils.show_message(self, self.tr("Decision date"), self.tr("no this application: "+ app_no))
                        return
                    application = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
                    if self.decision_date.date() < application.app_timestamp:
                        PluginUtils.show_message(self, self.tr("Decision date"), self.tr("This application date "+ app_no + " must be before decision date"))
                        return
                except (DatabaseError, SQLAlchemyError), e:
                    PluginUtils.show_error(self,  self.tr("Database Error"), e.message)
                decision_no = au_level2 + '-' + self.decision_number_edit.text() + '/' + year_filter
                item = QTableWidgetItem(decision_no)
                item.setData(Qt.UserRole, self.decision_number_edit.text())
                self.draft_detail_twidget.setItem(row, 8, item)

                item = QTableWidgetItem(self.decision_date.text())
                item.setData(Qt.UserRole, self.decision_date.text())
                self.draft_detail_twidget.setItem(row, 9, item)


    @pyqtSlot()
    def on_decision_save_button_clicked(self):

        if self.decision_number_edit.text() == "" or self.decision_number_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Decision No"), self.tr("Please enter decision number!"))
            return
        au_level2 = DatabaseUtils.current_working_soum_schema()
        year_filter = str(QDate().currentDate().toString("yyyy"))
        decision_no = 'decision_'+au_level2 + '_' + self.decision_number_edit.text() + '_' + year_filter
        path = QSettings().value(SettingsConstants.LAST_FILE_PATH, QDir.homePath())

        # default_path = path + QDir.separator()
        default_path = r'D:/TM_LM2/approved_decision'
        default_parent_path = r'D:/TM_LM2'
        if not os.path.exists(default_parent_path):
            os.makedirs('D:/TM_LM2')
            os.makedirs('D:/TM_LM2/application_response')
            os.makedirs('D:/TM_LM2/application_list')
            os.makedirs('D:/TM_LM2/approved_decision')
            os.makedirs('D:/TM_LM2/cad_maintenance')
            os.makedirs('D:/TM_LM2/cad_maps')
            os.makedirs('D:/TM_LM2/contracts')
            os.makedirs('D:/TM_LM2/decision_draft')
            os.makedirs('D:/TM_LM2/dumps')
            os.makedirs('D:/TM_LM2/q_data')
            os.makedirs('D:/TM_LM2/refused_decision')
            os.makedirs('D:/TM_LM2/reports')
            os.makedirs('D:/TM_LM2/training')
        if not os.path.exists(default_path):
            os.makedirs(default_path)

        file_dialog = QFileDialog(self, Qt.WindowStaysOnTopHint)
        file_dialog.setFilter('XLSX (*.xlsx)')
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setDirectory(default_path)
        file_dialog.selectFile(decision_no + ".xlsx")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            if file_path is None or type(file_path) == QPyNullVariant:
                return
            f_info = QFileInfo(file_path)

            QSettings().setValue(SettingsConstants.LAST_FILE_PATH, f_info.dir().path())

            self.decision_save_edit.setText(file_path)
        else:
            return

        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 18)
        worksheet.set_column('B:B', 18)
        worksheet.set_column('C:C', 18)
        worksheet.set_column('D:D', 18)
        worksheet.set_column('E:E', 18)
        worksheet.set_column('F:F', 18)
        worksheet.set_column('G:G', 20)

        bold = workbook.add_format({'bold': True})

        worksheet.write('A1',u"Өргөдлийн дугаар", bold)
        worksheet.write('B1',u"Захирамж дугаар", bold)
        worksheet.write('C1',u"Захирамж огноо", bold)
        worksheet.write('D1',u"Захирамж түвшин", bold)
        worksheet.write('E1',u"Захирамж гарсан эсэх", bold)
        worksheet.write('F1',u"Хугацаа", bold)
        worksheet.write('G1',u"Газар ашиглалтын зориулалт", bold)
        xrow = 1
        xcol = 0
        num_rows = self.draft_detail_twidget.rowCount()
        for row in range(num_rows):

            app_no = self.draft_detail_twidget.item(row, 3)
            decision_no = self.draft_detail_twidget.item(row, 8)
            decision_date = self.draft_detail_twidget.item(row, 9)
            # decision_level = self.draft_detail_twidget.item(row, 8)
            # decision_result = self.draft_detail_twidget.item(row, 9)
            approved_diratoin = self.draft_detail_twidget.item(row, 12)

            landsue_type_desc = self.draft_detail_twidget.item(row, 7).text()
            landuse_type = self.session.query(ClLanduseType). \
                filter(ClLanduseType.description == landsue_type_desc).one()

            decision_level_desc = self.draft_detail_twidget.item(row, 10).text()
            decision_level = self.session.query(ClDecisionLevel). \
                filter(ClDecisionLevel.description == decision_level_desc).one()

            decision_result_desc = self.draft_detail_twidget.item(row, 11).text()
            decision_result = self.session.query(ClDecision). \
                filter(ClDecision.description == decision_result_desc).one()

            worksheet.write(xrow, xcol,app_no.text())
            worksheet.write(xrow, xcol+1,decision_no.text())
            worksheet.write(xrow, xcol+2,decision_date.text())
            worksheet.write(xrow, xcol+3,str(decision_level.code))
            worksheet.write(xrow, xcol+4,str(decision_result.code))
            worksheet.write(xrow, xcol+5,approved_diratoin.text())
            worksheet.write(xrow, xcol+6,str(landuse_type.code))
            xrow = xrow + 1

        workbook.close()
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    @pyqtSlot()
    def on_draft_print_button_clicked(self):

        if self.draft_detail_twidget.rowCount() == 0:
            PluginUtils.show_message(self,self.tr("List None"),self.tr("Draft list null!!!"))
            return
        if self.draft_no_edit.text() == "":
            PluginUtils.show_message(self,self.tr("Draft No None"),self.tr("Draft No null!!!"))
            return
        au_level2 = DatabaseUtils.current_working_soum_schema()
        au_level1 = au_level2[:3]

        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == au_level2).one()
            aimag = self.session.query(AuLevel1).filter(AuLevel1.code == au_level1).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"),
                                   self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        path = os.path.join(os.path.dirname(__file__), "../view/map/decision/")
        num_rows = self.draft_detail_twidget.rowCount()
        parcel_id = ''
        for row in range(num_rows):
            parcel = self.draft_detail_twidget.item(row, 4)
            parcel_id = parcel.text()
            app = self.draft_detail_twidget.item(row, 3)
            app_no = app.text()

            app_type_code = app_no[6:-9]

            person = self.draft_detail_twidget.item(row, 2)
            person_id = person.text()

            date = self.draft_detail_twidget.item(row, 9)
            draft_date = date.text()

            landsue_type_desc = self.draft_detail_twidget.item(row, 7).text()
        # try:
        long_old_name = ''
        short_old_name = ''
        old_person_id = ''
        old_decision_level = ''
        old_decision_no = ''
        old_decision_year = ''
        old_decision_month = ''
        old_decision_day = ''
        old_cert_no = ''
        parcel_price = ''
        landuse_type = self.session.query(ClLanduseType). \
            filter(ClLanduseType.description == landsue_type_desc).one()
        if app_type_code == "07" or app_type_code == "10":
            app_person = self.session.query(CtApplicationPersonRole).\
                filter(CtApplicationPersonRole.application == app_no).\
                filter(CtApplicationPersonRole.main_applicant == True).\
                filter(CtApplicationPersonRole.role == 10).one()
        if app_type_code == "02":
            app_person = self.session.query(CtApplicationPersonRole). \
                filter(CtApplicationPersonRole.application == app_no). \
                filter(CtApplicationPersonRole.role == 30).one()
        if app_type_code == "07" or app_type_code == "10" or app_type_code == "02":
            old_person = self.session.query(BsPerson).filter(BsPerson.person_id == app_person.person).one()
            if old_person.type == 10 or old_person.type == 20 or old_person.type == 50:
                long_old_name = old_person.name + u' овогтой ' + old_person.first_name
                short_old_name = old_person.name[:2] + '.' + old_person.first_name
                old_person_id = old_person.person_id
            elif old_person.type == 30 or old_person.type == 40 or old_person.type == 60:
                long_old_name = old_person.name
                short_old_name = old_person.name
                old_person_id = old_person.person_id
            old_person_app = self.session.query(func.max(ApplicationSearch.app_timestamp).label("date"), ApplicationSearch.decision_no, ApplicationSearch.app_no).\
                filter(ApplicationSearch.person_id == old_person_id).\
                filter(ApplicationSearch.status >= 7).\
                filter(ApplicationSearch.parcel_id == parcel_id).group_by(ApplicationSearch.decision_no, ApplicationSearch.app_no).all()
            for i in old_person_app:
                app_date =  i.date
                dec_no = i.decision_no
                app_no = i.app_no
            if app_type_code == "07" or app_type_code == "10":
                old_contract_search = self.session.query(ContractSearch).filter(ContractSearch.app_no == app_no).one()
                if old_contract_search.certificate_no:
                    old_cert_no = old_contract_search.certificate_no
            if app_type_code == "02":
                parcel_c = self.session.query(CaParcel).filter(CaParcel.parcel_id == parcel_id).count()
                if parcel_c != 0:
                    parcel  = self.session.query(CaParcel).filter(CaParcel.parcel_id == parcel_id).one()
                    tax_zone_c = self.session.query(SetTaxAndPriceZone).filter(
                        parcel.geometry.ST_Within(SetTaxAndPriceZone.geometry)).count()
                    if tax_zone_c != 0:
                        tax_zone = self.session.query(SetTaxAndPriceZone).filter(parcel.geometry.ST_Within(SetTaxAndPriceZone.geometry)).first()
                        base_tax_price_c = self.session.query(SetBaseTaxAndPrice). \
                            filter(SetBaseTaxAndPrice.landuse == landuse_type.code). \
                            filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id).count()
                        if base_tax_price_c != 0:
                            base_tax_price = self.session.query(SetBaseTaxAndPrice).\
                                filter(SetBaseTaxAndPrice.landuse == landuse_type.code).\
                                filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id).one()
                            parcel_price = str(float(base_tax_price.base_value_per_m2)*parcel.area_m2)
            decision = self.session.query(CtDecision).filter(CtDecision.decision_no == dec_no).one()
            qt_date = PluginUtils.convert_python_date_to_qt(decision.decision_date)
            old_decision_no = dec_no

            if qt_date is not None:
                old_decision_year = qt_date.year()
                old_decision_month = qt_date.month()
                old_decision_day = qt_date.day()
            if decision.decision_level == 10:
                old_decision_level = u' Нийслэлийн '
            elif decision.decision_level == 20:
                old_decision_level = aimag.name + u' аймгийн '
            elif decision.decision_level == 30:
                old_decision_level = aimag.name + u' аймгийн ' + soum.name + u' сумын '
        person_c = self.session.query(BsPerson).filter(BsPerson.person_id == person_id).count()
        if person_c == 0:
            PluginUtils.show_message(self, self.tr("Person None"), self.tr("Person no information"))
            return
        person = self.session.query(BsPerson).filter(BsPerson.person_id == person_id).one()

        # except SQLAlchemyError, e:
        #     PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
        #     return

        if app_type_code == "05" and self.draft_detail_twidget.rowCount() == 1 and (person.type == 10 or person.type == 20)\
                and (landuse_type.code == 2204 or landuse_type.code == 2205 or landuse_type.code == 1302 or landuse_type.code == 1303 \
                        or landuse_type.code == 1304 or landuse_type.code == 1305 or landuse_type.code == 1306 or landuse_type.code == 1402\
                        or landuse_type.code == 1403 or landuse_type.code == 1404 or landuse_type.code == 1405 or landuse_type.code == 1406):
            tpl = DocxTemplate(path + 'draft_3_6_1.docx')
        elif app_type_code == "05" and self.draft_detail_twidget.rowCount() > 1:
            tpl = DocxTemplate(path + 'draft_3_6_2.docx')
        elif app_type_code == "06" and self.draft_detail_twidget.rowCount() == 1:
            tpl = DocxTemplate(path + 'draft_5_16_1.docx')
        elif app_type_code == "05" and person.type == 40 and self.draft_detail_twidget.rowCount() == 1:
            tpl = DocxTemplate(path + 'draft_3_7_1.docx')
        elif app_type_code == "05" and person.type == 40 and self.draft_detail_twidget.rowCount() > 1:
            tpl = DocxTemplate(path + 'draft_3_7_2.docx')
        elif app_type_code == "23" and self.draft_detail_twidget.rowCount() == 1:
            tpl = DocxTemplate(path + 'draft_3_6_1.docx')
        elif app_type_code == "24" and self.draft_detail_twidget.rowCount() == 1:
            tpl = DocxTemplate(path + 'draft_3_8_1.docx')
        elif app_type_code == "24" and self.draft_detail_twidget.rowCount() > 1:
            tpl = DocxTemplate(path + 'draft_3_8_2.docx')
        elif app_type_code == "07" and self.draft_detail_twidget.rowCount() == 1:
            tpl = DocxTemplate(path + 'draft_4_9_1.docx')
        elif app_type_code == "07" and self.draft_detail_twidget.rowCount() > 1:
            tpl = DocxTemplate(path + 'draft_4_9_2.docx')
        elif app_type_code == "10" and self.draft_detail_twidget.rowCount() == 1:
            tpl = DocxTemplate(path + 'draft_4_13_1.docx')
        elif app_type_code == "10" and self.draft_detail_twidget.rowCount() > 1:
            tpl = DocxTemplate(path + 'draft_4_13_2.docx')
        elif app_type_code == "01" or app_type_code == "03":
            tpl = DocxTemplate(path + 'draft_6_1.docx')
        elif app_type_code == "02" and self.draft_detail_twidget.rowCount() == 1:
            tpl = DocxTemplate(path + 'draft_6_2.docx')
        else:
            tpl = DocxTemplate(path + 'draft_3_6_1.docx')

        num_rows = self.draft_detail_twidget.rowCount()
        for row in range(num_rows):
            sur_name = self.draft_detail_twidget.item(row, 0)
            first_name = self.draft_detail_twidget.item(row, 1)

        long_name = ''
        short_name = ''
        register_id = ''

        if person.type == 10 or person.type == 20 or person.type == 50:
            long_name = sur_name.text() + u' овогтой ' + first_name.text()
            short_name = sur_name.text()[:2] + '.' + first_name.text()
            register_id = person_id
        elif person.type == 30 or person.type == 40 or person.type == 60:
            long_name = sur_name.text()
            short_name = sur_name.text()
            register_id = person_id

        total_area_m2 = 0
        num_rows = self.draft_detail_twidget.rowCount()
        for row in range(num_rows):

            requested_duration = self.draft_detail_twidget.item(row, 10)
            app_no = self.draft_detail_twidget.item(row, 3).text()
            decision_level_dec = self.draft_detail_twidget.item(row, 10).data(Qt.UserRole)
            decision_level = 20
            if decision_level_dec == u'Нийслэлийн Засаг даргын захирамж':
                decision_level = 10
            elif decision_level_dec == u'Дүүргийн Засаг даргын захирамж':
                decision_level = 20
            elif decision_level_dec == u'Аймгийн Засаг даргын захирамж':
                decision_level = 30
            elif decision_level_dec == u'Сумын Засаг даргын захирамж':
                decision_level = 40
            elif decision_level_dec == u'Чөлөөт бүсийн захирагч':
                decision_level = 50
            elif decision_level_dec == u'Тосгоны захирагч':
                decision_level = 60
            elif decision_level_dec == u'Нотариатч':
                decision_level = 70
            elif decision_level_dec == u'Байгаль орчны яамны сайдын тушаал':
                decision_level = 80

            try:
                application = self.session.query(CtApplication).\
                    filter(CtApplication.app_no == app_no).one()
                tmp_parcel_count = self.session.query(CaTmpParcel).\
                    filter(CaTmpParcel.parcel_id == application.tmp_parcel).count()
                if tmp_parcel_count != 0:
                    parcel = self.session.query(CaTmpParcel). \
                        filter(CaTmpParcel.parcel_id == application.tmp_parcel).one()
                else:
                    parcel = self.session.query(CaParcel).\
                        filter(CaParcel.parcel_id == application.parcel).one()

                bag = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(parcel.geometry)).one()
                country_c = self.session.query(ClCountryList).filter(ClCountryList.code == person.country).count()
                country_name = ''
                if country_c > 0:
                    country = self.session.query(ClCountryList).filter(ClCountryList.code == person.country).one()
                    country_name = country.description
                total_area_m2 = total_area_m2 + parcel.area_m2
            except SQLAlchemyError, e:
                self.rollback()
                PluginUtils.show_error(self, self.tr("Query Error"),
                                       self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

        user_name = QSettings().value(SettingsConstants.USER)
        user_rights = DatabaseUtils.userright_by_name(user_name)

        try:
            user = self.session.query(SetRole).filter(SetRole.user_name == user_name).filter(SetRole.is_active == True).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"),
                                   self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        sum_officer = ''
        if decision_level == 20 or decision_level == 40:
            sum_name_dec = soum.name + u'cум /дүүрэг/-ийн '
            sum_officer = soum.name + u'cум /дүүрэг/-ийн газрын даамал '
        elif decision_level == 10 or decision_level == 30:
            sum_officer = u'ГХБХБГазрын газрын асуудал эрхэлсэн албан тушаалтан '

        is_person = ''
        if person.type == 50:
            is_person = u'иргэн'
        elif person.type == 60:
            is_person = u'байгууллага'
        o_surname = user.surname
        o_firstname = user.first_name
        sum_name = soum.name
        bag_name = bag.name
        address_streetname = ''
        address_khashaa = ''
        if parcel.address_streetname:
            address_streetname = parcel.address_streetname + u' гудамж '
        if parcel.address_khashaa:
            address_khashaa = parcel.address_khashaa
        address_neighbourhood =  address_streetname + address_khashaa
        area_ga = str(parcel.area_m2/10000)
        area_m2 = str(parcel.area_m2)
        requested_duration = application.requested_duration
        person_count = self.draft_detail_twidget.rowCount()
        total_area_ga = str(total_area_m2 / 10000)
        total_area_m2 = str(total_area_m2)

        context = {
            'long_name': long_name,
            'short_name': short_name,
            'person_id': register_id,
            'landuse': landuse_type.description,
            'sum_name': sum_name,
            'bag_name': bag_name,
            'address_neighbourhood': address_neighbourhood,
            'parcel_id': parcel_id,
            'area_ga': area_ga,
            'area_m2': area_m2,
            'request_duration': requested_duration,
            'o_surname': o_surname,
            'o_firstname': o_firstname,
            'sum_officer': sum_officer,
            'country': country_name,
            'is_person': is_person,
            'count': person_count,
            't_area_ga': total_area_ga,
            't_area_m2': total_area_m2,
            'long_old_name': long_old_name,
            'short_old_name': short_old_name,
            'old_person_id': old_person_id,
            'aimag_sum': old_decision_level,
            'old_decision_year': old_decision_year,
            'old_decision_no': old_decision_no,
            'old_cert_no': old_cert_no,
            'streetname': address_streetname,
            'khashaa': address_khashaa,
            'parcel_price': parcel_price
        }

        tpl.render(context)
        default_path = r'D:/TM_LM2/approved_decision'

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to print for draft of governor decision"))

        yes_button = message_box.addButton(self.tr("Yes"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("No"), QMessageBox.ActionRole)
        message_box.exec_()
        if message_box.clickedButton() == yes_button:
            try:
                tpl.save(default_path + "/draft" + ".docx")
                QDesktopServices.openUrl(
                    QUrl.fromLocalFile(default_path + "/draft" + ".docx"))
            except IOError, e:
                PluginUtils.show_error(self, self.tr("Out error"),
                                       self.tr("This file is already opened. Please close re-run"))

    def __add_person_count(self,map_composition):

        num_rows = self.draft_detail_twidget.rowCount()

        item = map_composition.getComposerItemById("p_count")
        item.setText(str(num_rows))
        item.adjustSizeToText()
        area_m2 = 0
        for row in range(num_rows):
            p = self.draft_detail_twidget.item(row, 4)
            parcel_id = p.text()
            parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == parcel_id).one()
            area_m2 = area_m2 + parcel.area_m2

        item = map_composition.getComposerItemById("area_sum")
        item.setText(str(area_m2))
        item.adjustSizeToText()

    def __wrap(self,text, width):
        """
        A word-wrap function that preserves existing line breaks
        and most spaces in the text. Expects that existing line
        breaks are posix newlines (\n).
        """
        return reduce(lambda line, word, width=width: '%s%s%s' %
                      (line,
                       ' \n'[(len(line)-line.rfind('\n')-1
                             + len(word.split('\n',1)[0]
                                  ) >= width)],
                       word),
                      text.split(' ')
                     )
    def __add_use_text(self, map_composition):

        num_rows = self.draft_detail_twidget.rowCount()
        for row in range(num_rows):
            sur_name = self.draft_detail_twidget.item(row, 0)
            first_name = self.draft_detail_twidget.item(row, 1)
            register_id = self.draft_detail_twidget.item(row, 2)
            landusetype = self.draft_detail_twidget.item(row, 5).text()
            requested_duration = self.draft_detail_twidget.item(row, 10).text()
            parcel = self.draft_detail_twidget.item(row, 4)
            parcel_id = parcel.text()
        try:
            person = self.session.query(BsPerson).filter(BsPerson.person_id == register_id.text()).one()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        au_level2 = DatabaseUtils.current_working_soum_schema()
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == au_level2).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        num_rows = self.draft_detail_twidget.rowCount()

        try:
            parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == parcel_id).one()
            bag = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(parcel.geometry)).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        if parcel.address_streetname == None:
            streetname = ""
        else:
            streetname = parcel.address_streetname
        if parcel.address_khashaa == None:
            khashaa = ""
        else:
            khashaa = parcel.address_khashaa
        parcel_address =  streetname + ', ' + khashaa
        parcel_id = parcel.parcel_id[1:-9]+parcel.parcel_id[4:]
        if person.type == 50:

            full_name =  u'          1. ..................улсын иргэн "'+sur_name.text() + u'" овогтой ' + first_name.text()+ u' -ын '+ register_id.text()+u'/регистрийн дугаар/-д ' + \
                landusetype + u' зориулалтаар ' + soum.name + u' сумын ' + bag.name + u' багийн нутаг дэвсгэр ' + parcel_address + \
                u' байрлалтай ' + parcel_id + u' нэгж талбарын дугаартай, ' + str(parcel.area_m2/10000) + u' га  /' + str(parcel.area_m2) + u' м2/ газар эзэмших эрхийн хугацааг ' +\
                (requested_duration) + u' жилийн хугацаатайгаар ашиглуулсугай. '
            item = map_composition.getComposerItemById("full_name")
            item.setText(self.__wrap(full_name, 160))
            # item.adjustSizeToText()
            name = sur_name.text()[:1]+'.'+first_name.text()
            item = map_composition.getComposerItemById("company_name")
            item.setText(name)
            item.adjustSizeToText()

        elif person.type == 60:

            full_name =  u'          1. .................. улсын"' + sur_name.text() + u'" байгууллага '+ register_id.text()+u'/регистрийн дугаар/-д ' + \
                landusetype + u' зориулалтаар ' + soum.name + u' сумын ' + bag.name + u' багийн нутаг дэвсгэр ' + parcel_address + \
                u' байрлалтай ' + parcel_id + u' нэгж талбарын дугаартай, ' + str(parcel.area_m2/10000) + u' га  /' + str(parcel.area_m2) + u' м2/ газар эзэмших эрхийн хугацааг ' +\
                (requested_duration) + u' жилийн хугацаатайгаар ашиглуулсугай. '
            item = map_composition.getComposerItemById("full_name")
            item.setText(self.__wrap(full_name,170))
            # item.adjustSizeToText()
            name = sur_name.text()
            item = map_composition.getComposerItemById("company_name")
            item.setText(name)
            item.adjustSizeToText()

    def __add_extension_date(self, map_composition):

        num_rows = self.draft_detail_twidget.rowCount()
        for row in range(num_rows):
            sur_name = self.draft_detail_twidget.item(row, 0)
            first_name = self.draft_detail_twidget.item(row, 1)
            register_id = self.draft_detail_twidget.item(row, 2)
            landusetype = self.draft_detail_twidget.item(row, 5).text()
            requested_duration = self.draft_detail_twidget.item(row, 10).text()
            parcel = self.draft_detail_twidget.item(row, 4)
            parcel_id = parcel.text()
        try:
            person = self.session.query(BsPerson).filter(BsPerson.person_id == register_id.text()).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        au_level2 = DatabaseUtils.current_working_soum_schema()
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == au_level2).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        num_rows = self.draft_detail_twidget.rowCount()

        try:
            parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == parcel_id).one()
            bag = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(parcel.geometry)).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        if parcel.address_streetname == None:
            streetname = ""
        else:
            streetname = parcel.address_streetname
        if parcel.address_khashaa == None:
            khashaa = ""
        else:
            khashaa = parcel.address_khashaa
        parcel_address =  streetname + ', ' + khashaa
        parcel_id = parcel.parcel_id[1:-9]+parcel.parcel_id[4:]
        if person.type == 10 or person.type == 20 or person.type == 50:

            full_name =  u'          1. Иргэн "'+sur_name.text() + u'" овогтой ' + first_name.text()+ u' -ын '+ register_id.text()+u'/регистрийн дугаар/-д ' + \
                landusetype + u' зориулалтаар үнэ төлбөргүйгээр ' + soum.name + u' сумын ' + bag.name + u' багийн нутаг дэвсгэр ' + parcel_address + \
                u' байрлалтай ' + parcel_id + u' нэгж талбарын дугаартай, ' + str(parcel.area_m2/10000) + u' га  /' + str(parcel.area_m2) + u' м2/ газар эзэмших эрхийн хугацааг ' +\
                requested_duration + u' жилээр сунгасугай. '
            item = map_composition.getComposerItemById("full_name")
            item.setText(self.__wrap(full_name, 160))
            # item.adjustSizeToText()
            name = sur_name.text()[1:]+'.'+first_name.text()
            item = map_composition.getComposerItemById("company_name")
            item.setText(name)
            item.adjustSizeToText()

        elif person.type == 30 or person.type == 40 or person.type == 60:

            full_name =  u'          1. "' + sur_name.text() + u'" байгууллага '+ register_id.text()+u'/регистрийн дугаар/-д ' + \
                landusetype + u' зориулалтаар үнэ төлбөргүйгээр ' + soum.name + u' сумын ' + bag.name + u' багийн нутаг дэвсгэр ' + parcel_address + \
                u' байрлалтай ' + parcel_id + u' нэгж талбарын дугаартай, ' + str(parcel.area_m2/10000) + u' га  /' + str(parcel.area_m2) + u' м2/ газар эзэмших эрхийн хугацааг ' +\
                (requested_duration) + u' жилээр сунгасугай. '
            item = map_composition.getComposerItemById("full_name")
            item.setText(self.__wrap(full_name,170))
            # item.adjustSizeToText()
            name = sur_name.text()
            item = map_composition.getComposerItemById("company_name")
            item.setText(name)
            item.adjustSizeToText()

    def __add_agr_name(self, map_composition):

        num_rows = self.draft_detail_twidget.rowCount()
        for row in range(num_rows):
            sur_name = self.draft_detail_twidget.item(row, 0)
            first_name = self.draft_detail_twidget.item(row, 1)
            register_id = self.draft_detail_twidget.item(row, 2)
            landusetype = self.draft_detail_twidget.item(row, 5).text()
            requested_duration = self.draft_detail_twidget.item(row, 10).text()
            parcel = self.draft_detail_twidget.item(row, 4)
            parcel_id = parcel.text()
        try:
            person = self.session.query(BsPerson).filter(BsPerson.person_id == register_id.text()).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        au_level2 = DatabaseUtils.current_working_soum_schema()
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == au_level2).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        num_rows = self.draft_detail_twidget.rowCount()

        try:
            parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == parcel_id).one()
            bag = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(parcel.geometry)).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        if parcel.address_streetname == None:
            streetname = ""
        else:
            streetname = parcel.address_streetname
        if parcel.address_khashaa == None:
            khashaa = ""
        else:
            khashaa = parcel.address_khashaa
        parcel_address =  streetname + ', ' + khashaa
        parcel_id = parcel.parcel_id[1:-9]+parcel.parcel_id[4:]
        if person.type == 10 or person.type == 20 or person.type == 50:

            full_name =  u'          1. Иргэн "'+sur_name.text() + u'" овогтой ' + first_name.text()+ u' -ын '+ register_id.text()+u'/регистрийн дугаар/-д гэр бүлийнх нь хамтын хэрэгцээнд давуу эрхээр' + \
                landusetype + u' зориулалтаар үнэ төлбөргүйгээр ' + soum.name + u' сумын ' + bag.name + u' багийн нутаг дэвсгэр ' + parcel_address + \
                u' байрлалтай ' + parcel_id + u' нэгж талбарын дугаартай, ' + str(parcel.area_m2/10000) + u' га  /' + str(parcel.area_m2) + u' м2/ газрыг ' +\
                (requested_duration) + u' жилийн хугацаатайгаар эзэмшүүлсүгэй. '
            item = map_composition.getComposerItemById("full_name")
            item.setText(self.__wrap(full_name, 160))
            # item.adjustSizeToText()
            name = sur_name.text()[:1]+'.'+first_name.text()
            item = map_composition.getComposerItemById("company_name")
            item.setText(name)
            item.adjustSizeToText()

        elif person.type == 30 or person.type == 40 or person.type == 60:

            full_name =  u'          1. "' + sur_name.text() + u'" байгууллага '+ register_id.text()+u'/регистрийн дугаар/-д гэр бүлийнх нь хамтын хэрэгцээнд давуу эрхээр' + \
                landusetype + u' зориулалтаар үнэ төлбөргүйгээр ' + soum.name + u' сумын ' + bag.name + u' багийн нутаг дэвсгэр ' + parcel_address + \
                u' байрлалтай ' + parcel_id + u' нэгж талбарын дугаартай, ' + str(parcel.area_m2/10000) + u' га  /' + str(parcel.area_m2) + u' м2/ газрыг ' +\
                (requested_duration) + u' жилийн хугацаатайгаар эзэмшүүлсүгэй. '
            item = map_composition.getComposerItemById("full_name")
            item.setText(self.__wrap(full_name,170))
            # item.adjustSizeToText()
            name = sur_name.text()
            item = map_composition.getComposerItemById("company_name")
            item.setText(name)
            item.adjustSizeToText()

    def __add_full_name(self, map_composition):

        num_rows = self.draft_detail_twidget.rowCount()
        for row in range(num_rows):
            sur_name = self.draft_detail_twidget.item(row, 0)
            first_name = self.draft_detail_twidget.item(row, 1)
            register_id = self.draft_detail_twidget.item(row, 2)
            landusetype = self.draft_detail_twidget.item(row, 5).text()
            requested_duration = self.draft_detail_twidget.item(row, 10).text()
            parcel = self.draft_detail_twidget.item(row, 4)
            parcel_id = parcel.text()
        try:
            person = self.session.query(BsPerson).filter(BsPerson.person_id == register_id.text()).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        au_level2 = DatabaseUtils.current_working_soum_schema()
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == au_level2).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        num_rows = self.draft_detail_twidget.rowCount()

        try:
            parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == parcel_id).one()
            bag = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(parcel.geometry)).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        if parcel.address_streetname == None:
            streetname = ""
        else:
            streetname = parcel.address_streetname
        if parcel.address_khashaa == None:
            khashaa = ""
        else:
            khashaa = parcel.address_khashaa
        parcel_address =  streetname + ', ' + khashaa
        parcel_id = parcel.parcel_id[1:-9]+parcel.parcel_id[4:]
        if person.type == 10 or person.type == 20 or person.type == 50:

            full_name =  u'          1. Иргэн "'+sur_name.text() + u'" овогтой ' + first_name.text()+ u' -ын '+ register_id.text()+u'/регистрийн дугаар/-д ' + \
                landusetype + u' зориулалтаар ' + soum.name + u' сумын ' + bag.name + u' багийн нутаг дэвсгэр ' + parcel_address + \
                u' байрлалтай ' + parcel_id + u' нэгж талбарын дугаартай, ' + str(parcel.area_m2/10000) + u' га  /' + str(parcel.area_m2) + u' м2/ газрыг ' +\
                (requested_duration) + u' жилийн хугацаатайгаар эзэмшүүлсүгэй. '
            item = map_composition.getComposerItemById("full_name")
            item.setText(self.__wrap(full_name, 160))
            # item.adjustSizeToText()
            name = sur_name.text()[:1]+'.'+first_name.text()
            item = map_composition.getComposerItemById("company_name")
            item.setText(name)
            item.adjustSizeToText()

        elif person.type == 30 or person.type == 40 or person.type == 60:

            full_name =  u'          1. "' + sur_name.text() + u'" байгууллага '+ register_id.text()+u'/регистрийн дугаар/-д ' + \
                landusetype + u' зориулалтаар ' + soum.name + u' сумын ' + bag.name + u' багийн нутаг дэвсгэр ' + parcel_address + \
                u' байрлалтай ' + parcel_id + u' нэгж талбарын дугаартай, ' + str(parcel.area_m2/10000) + u' га  /' + str(parcel.area_m2) + u' м2/ газрыг ' +\
                (requested_duration) + u' жилийн хугацаатайгаар эзэмшүүлсүгэй. '
            item = map_composition.getComposerItemById("full_name")
            item.setText(self.__wrap(full_name,170))
            # item.adjustSizeToText()
            name = sur_name.text()
            item = map_composition.getComposerItemById("company_name")
            item.setText(name)
            item.adjustSizeToText()

    def __add_person(self, map_composition):

        num_rows = self.draft_detail_twidget.rowCount()
        for row in range(num_rows):
            sur_name = self.draft_detail_twidget.item(row, 0)
            first_name = self.draft_detail_twidget.item(row, 1)
            register_id = self.draft_detail_twidget.item(row, 2)

        try:
            person = self.session.query(BsPerson).filter(BsPerson.person_id == register_id.text()).one()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return


        if person.type == 10 or person.type == 20 or person.type == 50:
            surname = sur_name.text()
            firstname = first_name.text()
            short_name =  sur_name.text()[:1] + '.' + first_name.text()
            item = map_composition.getComposerItemById("surname")
            item.setText(sur_name.text())
            item.adjustSizeToText()

            item = map_composition.getComposerItemById("first_name")
            item.setText(first_name.text())
            item.adjustSizeToText()
        elif person.type == 30 or person.type == 40 or person.type == 60:
            short_name =  sur_name.text()

        item = map_composition.getComposerItemById("register_id")
        item.setText(register_id.text())
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("short_name")
        item.setText(short_name)
        item.adjustSizeToText()

    def __add_officer(self,map_composition):

        user_name = QSettings().value(SettingsConstants.USER)
        user_rights = DatabaseUtils.userright_by_name(user_name)

        try:
            user = self.session.query(SetRole).filter(SetRole.user_name == user_name).filter(SetRole.is_active == True).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        item = map_composition.getComposerItemById("officer_name")
        item.setText(user.surname[:1] +"."+ user.first_name)
        item.adjustSizeToText()

    def __add_soum1(self,map_composition):

        au_level2 = DatabaseUtils.current_working_soum_schema()
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == au_level2).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        item = map_composition.getComposerItemById("soum_name1")
        item.setText(soum.name)
        item.adjustSizeToText()

    def __add_soum(self,map_composition):

        au_level2 = DatabaseUtils.current_working_soum_schema()
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == au_level2).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        item = map_composition.getComposerItemById("soum_name")
        item.setText(soum.name)
        item.adjustSizeToText()

    def __add_bag(self, map_composition):

        num_rows = self.draft_detail_twidget.rowCount()
        for row in range(num_rows):
            parcel = self.draft_detail_twidget.item(row, 4)
            parcel_id = parcel.text()
            requested_duration = self.draft_detail_twidget.item(row, 10)
        try:
            parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == parcel_id).one()
            bag = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(parcel.geometry)).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        item = map_composition.getComposerItemById("bag_name")
        item.setText(bag.name)
        item.adjustSizeToText()

    def __add_parcel_info(self, map_composition):

        num_rows = self.draft_detail_twidget.rowCount()
        for row in range(num_rows):
            parcel = self.draft_detail_twidget.item(row, 4)
            parcel_id = parcel.text()
            requested_duration = self.draft_detail_twidget.item(row, 10)
            app_no = self.draft_detail_twidget.item(row, 3).text()
        try:
            parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == parcel_id).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        if parcel.address_streetname == None:
            streetname = ""
        else:
            streetname = parcel.address_streetname
        if parcel.address_khashaa == None:
            khashaa = ""
        else:
            khashaa = parcel.address_khashaa
        parcel_address =  streetname + ', ' + khashaa

        item = map_composition.getComposerItemById("parcel_address")
        item.setText(parcel_address)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("parcel_id")
        item.setText(parcel.parcel_id)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("area_ga")
        item.setText(str(parcel.area_m2/10000))
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("area_m2")
        item.setText(str(parcel.area_m2))
        item.adjustSizeToText()

        app_type = app_no[6:-9]
        if app_type != "02":
            item = map_composition.getComposerItemById("year_count")
            item.setText(str(requested_duration.text()))
            item.adjustSizeToText()

    def __add_trasfer_count(self, map_composition):

        num_rows = self.draft_detail_twidget.rowCount()

        count = 0
        try:
            for row in range(num_rows):
                app_no = self.draft_detail_twidget.item(row, 3).text()
                applicants_new = self.session.query(CtApplicationPersonRole).filter(
                CtApplicationPersonRole.role == Constants.NEW_RIGHT_HOLDER_CODE).\
                filter(CtApplicationPersonRole.application == app_no).all()
                for applicant_new in applicants_new:
                    applicant = applicant_new

                    count = count + 1
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        item = map_composition.getComposerItemById("transfer_count")
        item.setText(str(count))
        item.adjustSizeToText()


    def __add_transfer(self, map_composition):

        num_rows = self.draft_detail_twidget.rowCount()
        for row in range(num_rows):
            sur_name = self.draft_detail_twidget.item(row, 0)
            first_name = self.draft_detail_twidget.item(row, 1)
            register_id = self.draft_detail_twidget.item(row, 2)
            app_no = self.draft_detail_twidget.item(row, 3).text()
            landusetype = self.draft_detail_twidget.item(row, 7).text()
            requested_duration = self.draft_detail_twidget.item(row, 10).text()
            parcel = self.draft_detail_twidget.item(row, 4)
            parcel_id = parcel.text()
        try:
            person = self.session.query(BsPerson).filter(BsPerson.person_id == register_id.text()).one()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        au_level2 = DatabaseUtils.current_working_soum_schema()
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == au_level2).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        num_rows = self.draft_detail_twidget.rowCount()

        try:
            parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == parcel_id).one()
            bag = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(parcel.geometry)).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        try:
            applicants_new = self.session.query(CtApplicationPersonRole).filter(
                CtApplicationPersonRole.role == Constants.NEW_RIGHT_HOLDER_CODE).\
                filter(CtApplicationPersonRole.application == app_no).all()
            # applicants_old = self.session.query(CtApplicationPersonRole).filter(
            #     CtApplicationPersonRole.role == Constants.OLD_RIGHT_HOLDER_CODE).all()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        for applicant_new in applicants_new:
            applicant = applicant_new
        if parcel.address_streetname == None:
            streetname = ""
        else:
            streetname = parcel.address_streetname
        if parcel.address_khashaa == None:
            khashaa = ""
        else:
            khashaa = parcel.address_khashaa
        parcel_address =  streetname + ', ' + khashaa
        parcel_id = parcel.parcel_id[1:-9]+parcel.parcel_id[4:]
        if person.type == 10 or person.type == 20:
            if applicant.person_ref.type == 10:
                full_name =  u'          1. Иргэн '+sur_name.text() + u' овогтой ' + first_name.text()+ u' -ын '+ register_id.text()+u'/регистрийн дугаар/-д ' + \
                    landusetype + u' зориулалтаар ' + soum.name + u' сумын ' + bag.name + u' багийн нутаг дэвсгэр ' + parcel_address + \
                    u' байрлалтай ' + parcel_id + u' нэгж талбарын дугаартай, ' + str(parcel.area_m2/10000) + u' га  /' + str(parcel.area_m2) + u' м2/ газар эзэмших эрхийг иргэн ' +\
                    (applicant.person_ref.name) + u' овогтой ' + (applicant.person_ref.first_name) + u' -ны ' + (applicant.person_ref.person_id) + u'/регистрийн дугаар/-д ' + (requested_duration) + u' жилийн хугацаатайгаар шилжүүлэн эзэмшүүлсүгэй. '
                item = map_composition.getComposerItemById("full_name")
                item.setText(self.__wrap(full_name, 160))
                # item.adjustSizeToText()

            elif applicant.person_ref.type == 30 or applicant.person_ref.type == 40:
                full_name =  u'          1. Иргэн '+sur_name.text() + u' овогтой ' + first_name.text()+ u' -ын '+ register_id.text()+u'/регистрийн дугаар/-д ' + \
                    landusetype + u' зориулалтаар ' + soum.name + u' сумын ' + bag.name + u' багийн нутаг дэвсгэр ' + parcel_address + \
                    u' байрлалтай ' + parcel_id + u' нэгж талбарын дугаартай, ' + str(parcel.area_m2/10000) + u' га  /' + str(parcel.area_m2) + u' м2/ газар эзэмших эрхийг иргэн ' +\
                    (applicant.person_ref.name) + u' байгууллага ' + (applicant.person_ref.person_id) + u'/регистрийн дугаар/-д ' + str(requested_duration) + u' жилийн хугацаатайгаар шилжүүлэн эзэмшүүлсүгэй. '
                item = map_composition.getComposerItemById("full_name")
                item.setText(self.__wrap(full_name, 160))
            name = applicant.person_ref.name[:1]+'.'+applicant.person_ref.first_name
            item = map_composition.getComposerItemById("company_name")
            item.setText(name)
            item.adjustSizeToText()

        elif person.type == 30 or person.type == 40:
            if applicant.person_ref.type == 10:
                full_name =  u'          1. "' + sur_name.text() + u'" байгууллага '+ register_id.text()+u'/регистрийн дугаар/-д ' + \
                    landusetype + u' зориулалтаар ' + soum.name + u' сумын ' + bag.name + u' багийн нутаг дэвсгэр ' + parcel_address + \
                    u' байрлалтай ' + parcel_id + u' нэгж талбарын дугаартай, ' + str(parcel.area_m2/10000) + u' га  /' + str(parcel.area_m2) + u' м2/ газар эзэмших эрхийг иргэн ' +\
                    (applicant.person_ref.name) + u' овогтой ' + (applicant.person_ref.first_name) + u' -ны ' + (applicant.person_ref.person_id) + u'/регистрийн дугаар/-д ' + str(requested_duration) + u' жилийн хугацаатайгаар шилжүүлэн эзэмшүүлсүгэй. '
                item = map_composition.getComposerItemById("full_name")
                item.setText(self.__wrap(full_name,170))
                # item.adjustSizeToText()
            if applicant.person_ref.type == 30 or applicant.person_ref.type == 40:
                full_name =  u'          1. "' + sur_name.text() + u'" байгууллага '+ register_id.text()+u'/регистрийн дугаар/-д ' + \
                    landusetype + u' зориулалтаар ' + soum.name + u' сумын ' + bag.name + u' багийн нутаг дэвсгэр ' + parcel_address + \
                    u' байрлалтай ' + parcel_id + u' нэгж талбарын дугаартай, ' + str(parcel.area_m2/10000) + u' га  /' + str(parcel.area_m2) + u' м2/ газар эзэмших эрхийг иргэн ' +\
                    (applicant.person_ref.name) + u' байгууллага ' + (applicant.person_ref.person_id) + u'/регистрийн дугаар/-д ' + (requested_duration) + u' жилийн хугацаатайгаар шилжүүлэн эзэмшүүлсүгэй. '
                item = map_composition.getComposerItemById("full_name")
                item.setText(self.__wrap(full_name,165))
                # item.adjustSizeToText()
            name = sur_name.text()
            item = map_composition.getComposerItemById("company_name")
            item.setText(name)
            item.adjustSizeToText()

    def __add_suh_use(self, map_composition):

        num_rows = self.draft_detail_twidget.rowCount()
        for row in range(num_rows):
            sur_name = self.draft_detail_twidget.item(row, 0)
            first_name = self.draft_detail_twidget.item(row, 1)
            register_id = self.draft_detail_twidget.item(row, 2)
            landusetype = self.draft_detail_twidget.item(row, 5).text()
            requested_duration = self.draft_detail_twidget.item(row, 10).text()
            parcel = self.draft_detail_twidget.item(row, 4)
            parcel_id = parcel.text()
        try:
            person = self.session.query(BsPerson).filter(BsPerson.person_id == register_id.text()).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        au_level2 = DatabaseUtils.current_working_soum_schema()
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == au_level2).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        num_rows = self.draft_detail_twidget.rowCount()

        try:
            parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == parcel_id).one()
            bag = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(parcel.geometry)).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        if parcel.address_streetname == None:
            streetname = ""
        else:
            streetname = parcel.address_streetname
        if parcel.address_khashaa == None:
            khashaa = ""
        else:
            khashaa = parcel.address_khashaa
        parcel_address =  streetname + ', ' + khashaa
        parcel_id = parcel.parcel_id[1:-9]+parcel.parcel_id[4:]

        if person.type == 30:

            full_name =  u'          1. "' + sur_name.text() + u'" /'+ register_id.text()+u'/ сууц өмчлөгчдийн холбоонд' + \
                landusetype + u' зориулалтаар ' + soum.name + u' сумын ' + bag.name + u' багийн нутаг дэвсгэр ' + parcel_address + \
                u' байрлалтай ' + parcel_id + u' нэгж талбарын дугаартай, ' + str(parcel.area_m2/10000) + u' га  /' + str(parcel.area_m2) + u' м2/ газрыг ' +\
                str(requested_duration) + u' жилийн хугацаатайгаар ашиглуулсугай. '
            item = map_composition.getComposerItemById("full_name")
            item.setText(self.__wrap(full_name,170))
            # item.adjustSizeToText()
            name = sur_name.text()
            item = map_composition.getComposerItemById("company_name")
            item.setText(name)
            item.adjustSizeToText()

    def __drafts_twidget_2(self):

        if self.drafts_edit.text() == "":
            PluginUtils.show_message(self,self.tr("no dir"),self.tr("no dir"))
            return
        self.drafts_twidget_2.setRowCount(0)
        count = 0
        for file in os.listdir(self.drafts_edit.text()):
            if file.endswith(".xlsx") and str(file)[:5] == "draft":
                item_name = QTableWidgetItem(str(file))
                item_name.setData(Qt.UserRole,file)

                self.drafts_twidget_2.insertRow(count)
                self.drafts_twidget_2.setItem(count,0,item_name)
                count +=1

    @pyqtSlot(QTableWidgetItem)
    def on_drafts_twidget_2_itemClicked(self, item):

        num_rows = self.draft_detail_twidget.rowCount()

        session = SessionHandler().session_instance()
        current_column = self.drafts_twidget_2.currentColumn()
        current_row = self.drafts_twidget_2.currentRow()
        item = self.drafts_twidget_2.item(current_row,0)
        draft_id = item.data(Qt.UserRole)
        file_name = self.drafts_edit.text() + '/' +draft_id

        self.__read_xls_file(file_name)


    def onChangetab(self, i):

        if i == 1:
            # self.draft_detail_twidget.setRowCount(0)
            # self.new_group_box.setEnabled(False)
            # self.draft_group_box.setEnabled(True)
            # self.decision_save_edit.setEnabled(True)
            # self.decision_save_button.setEnabled(True)
            # self.draft_rbutton.setEnabled(False)
            # self.new_rbutton.setEnabled(False)
            self.__setup_twidget(self.draft_detail_twidget)

            code_list = list()
            descriptions = self.session.query(ClDecision.description).order_by((ClDecision.description))
            for description in descriptions:
                code_list.append(description[0])

            landuse = list()
            landuse_type = self.session.query(ClLanduseType.description).order_by(ClLanduseType.description)
            for description in landuse_type:
                landuse.append(description[0])

            delegate = ComboBoxDelegate(7, landuse, self.draft_detail_twidget)
            self.draft_detail_twidget.setItemDelegateForColumn(7, delegate)

            delegate = IntegerSpinBoxDelegate(12, 0, 120, 0, 5, self.draft_detail_twidget)
            self.draft_detail_twidget.setItemDelegateForColumn(12, delegate)

            delegate = ComboBoxDelegate(11, code_list, self.draft_detail_twidget)
            self.draft_detail_twidget.setItemDelegateForColumn(11, delegate)

    @pyqtSlot(int)
    def on_app_type_cbox_currentIndexChanged(self, index):

        self.decision_level_cbox.clear()
        app_type = self.app_type_cbox.itemData(index)
        if app_type == ApplicationType.special_use:
            decision_level = self.session.query(ClDecisionLevel).filter(ClDecisionLevel.code == 80).all()
            for item in decision_level:
                self.decision_level_cbox.addItem(item.description, item.code)
        else:
            soum_code = ''
            au_level2 = DatabaseUtils.current_working_soum_schema()
            soum_code = str(au_level2)[3:]
            set_roles = self.session.query(SetRole).all()
            set_role = self.session.query(SetRole).filter(
                SetRole.user_name == DatabaseUtils.current_user().user_name).filter(SetRole.is_active == True).one()
            aimag_code = set_role.working_au_level1
            aimag_code = aimag_code[:2]
            if aimag_code == '01' or aimag_code == '12':
                decision_level = self.session.query(ClDecisionLevel).filter(
                    or_(ClDecisionLevel.code == 10, ClDecisionLevel.code == 20)).all()
                for item in decision_level:
                    self.decision_level_cbox.addItem(item.description, item.code)
            else:
                if soum_code == '01':
                    decision_level = self.session.query(ClDecisionLevel).filter(
                        or_(ClDecisionLevel.code == 30, ClDecisionLevel.code == 40, ClDecisionLevel.code == 50, ClDecisionLevel.code == 60)).all()
                    for item in decision_level:
                        self.decision_level_cbox.addItem(item.description, item.code)
                        # self.decision_level_cbox.setCurrentIndex(2)
                else:
                    decision_level = self.session.query(ClDecisionLevel).filter(or_(ClDecisionLevel.code == 40, ClDecisionLevel.code == 50, ClDecisionLevel.code == 60)).all()
                    for item in decision_level:
                        self.decision_level_cbox.addItem(item.description, item.code)
                        # self.decision_level_cbox.setCurrentIndex(3)

    @pyqtSlot()
    def on_help_button_clicked(self):
        os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                  :-10]) + "help\output\help_lm2.chm::/html/sent_to_the_governor_decision.htm")