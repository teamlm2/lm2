__author__ = 'B.Ankhbold'
# coding=utf8
from sqlalchemy import exc, or_
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_, and_, desc,extract
from inspect import currentframe
from qgis.core import *
from qgis.gui import *
import qgis.utils
from ..view.Ui_LandOfficeAdministrativeSettingsDialog import *
from ..utils.PluginUtils import *
from ..model import Constants
from ..model.DatabaseHelper import *
from ..model.ClApplicationStatus import *
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.ClBank import *
from ..model.ClContractCancellationReason import *
from ..model.ClContractCondition import *
from ..model.ClContractStatus import *
from ..model.ClPositionType import *
from ..model.ClDecisionLevel import *
from ..model.ClDocumentRole import *
from ..model.ClGender import *
from ..model.ClGrudType import *
from ..model.ClPastureType import *
from ..model.ClEmployeeType import *
from ..model.ClPollutionType import *
from ..model.ClMemberRole import *
from ..model.SetCertificate import *
from ..model.ClPersonRole import *
from ..model.ClPersonType import *
from ..model.ClRecordCancellationReason import *
from ..model.ClRecordRightType import *
from ..model.ClRecordStatus import *
from ..model.ClRightType import *
from ..model.ClEquipmentList import *
from ..model.ClCertificateType import *
from ..model.ClMortgageStatus import *
from ..model.SetFeeZone import *
from ..model.SetBaseFee import *
from ..model.SetTaxAndPriceZone import *
from ..model.SetBaseTaxAndPrice import *
from ..model.SetSurveyCompany import *
from ..model.SetOfficialDocument import *
from ..model.CtContractApplicationRole import *
from ..model.SetFeeDocument import *
from ..model.CtArchivedFee import *
from ..model.CtArchivedTaxAndPrice import *
from ..model.VaTypeParcel import *
from ..model.VaTypeAgriculture import *
from ..model.VaTypeDesign import *
from ..model.VaTypeHeat import *
from ..model.VaTypeLanduseBuilding import *
from ..model.VaTypeMaterial import *
from ..model.VaTypePurchaseOrLease import *
from ..model.VaTypeSource import *
from ..model.VaTypeStatusBuilding import *
from ..model.VaTypeStove import *
from ..model.VaTypeSideFence import *
from ..model.SetEquipment import *
from ..model.SetEquipmentDocument import *
from ..model.SetDocument import *
from ..model.SetTraining import *
from ..model.SetCertificatePerson import *
from ..model.SetTrainingPerson import *
from ..model.ClTrainingLevel import *
from ..model.SetCadastrePage import *
from ..utils.FileUtils import FileUtils
from ..utils.LayerUtils import LayerUtils
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.SessionHandler import SessionHandler
from ..utils.FilePath import *
from .qt_classes.CertificateDocumentDelegate import *
from xlsxwriter.utility import xl_rowcol_to_cell, xl_col_to_name
import xlsxwriter
import shutil
import win32netcon,win32wnet
import os
import os.path
import shutil
import sys
import win32wnet

from .qt_classes.OfficialDocumentDelegate import OfficialDocumentDelegate
from .qt_classes.DoubleSpinBoxDelegate import DoubleSpinBoxDelegate
from .qt_classes.IntegerSpinBoxDelegate import IntegerSpinBoxDelegate
from .qt_classes.LandUseComboBoxDelegate import LandUseComboBoxDelegate
from .qt_classes.DateDelegate import DateDelegate
from .qt_classes.DateFormatDelegate import DateFormatDelegate
from .qt_classes.LineEditDelegate import LineEditDelegate

FEE_LAND_USE = 0
FEE_BASE_FEE_PER_M2 = 1
FEE_SUBSIDIZED_AREA = 2
FEE_SUBSIDIZED_FEE_RATE = 3

TAX_LAND_USE = 0
TAX_BASE_VALUE_PER_M2 = 1
TAX_BASE_TAX_RATE = 2
TAX_SUBSIDIZED_AREA = 3
TAX_SUBSIDIZED_TAX_RATE = 4

CODELIST_CODE = 0
CODELIST_DESC = 1

COMPANY_NAME = 0
COMPANY_ADDRESS = 1

SURVEYOR_SURNAME = 0
SURVEYOR_FIRST_NAME = 1
SURVEYOR_PHONE = 2

DOC_VISIBLE_COLUMN = 0
DOC_NAME_COLUMN = 1
DOC_DESCRIPTION_COLUMN = 2
DOC_OPEN_FILE_COLUMN = 3
DOC_VIEW_COLUMN = 4


class LandOfficeAdministrativeSettingsDialog(QDialog, Ui_LandOfficeAdministrativeSettingsDialog, DatabaseHelper):

    def __init__(self, parent=None):

        super(LandOfficeAdministrativeSettingsDialog, self).__init__(parent)
        DatabaseHelper.__init__(self)
        self.setupUi(self)

        self.time_counter = None
        self.old_codelist_index = -1
        self.company_search_str = ''
        self.surveyor_search_str = ''
        self.zone_fid = None

        self.session = SessionHandler().session_instance()
        self.__set_schema()
        self.__setup_combo_boxes()
        self.__load_settings()
        self.__setup_codelist_table_widget()

        self.close_button.clicked.connect(self.reject)
        self.apply_button.setDefault(True)
        self.status_label.clear()
        self.initial_date.setDate(QDate().currentDate())
        self.given_date.setDate(QDate().currentDate())
        self.duration_date.setDate(QDate().currentDate())
        # self.change_begin_date.setDate(QDate().currentDate())
        self.change_end_date.setDate(QDate().currentDate())

        self.landuse_code_list = list()
        self.__set_up_land_fee_tab()
        self.__setup_certificate_person()
        self.__set_up_land_tax_tab()
        self.__set_up_company_tab()
        self.__set_up_surveyor_tab()
        self.__setup_doc_twidget()
        self.__set_up_equipment_tab()

        self.doc_add_button.setEnabled(False)
        self.doc_delete_button.setEnabled(False)
        self.doc_view_button.setEnabled(False)

        self.add_equip_doc_button.setEnabled(False)
        self.delete_equip_doc_button.setEnabled(False)
        self.view_equip_doc_button.setEnabled(False)
        self.add_document_button.setEnabled(False)
        self.remove_document_button.setEnabled(False)
        self.add_document_button.setEnabled(False)
        self.remove_document_button.setEnabled(False)

    def __setup_codelist_table_widget(self):

        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setSelectionMode(QTableWidget.SingleSelection)
        delegate = IntegerSpinBoxDelegate(CODELIST_CODE, 1, 10000, 1000, 10, self.table_widget)
        self.table_widget.setItemDelegateForColumn(CODELIST_CODE, delegate)

    def __setup_combo_boxes(self):

        bank_list = DatabaseUtils.codelist_by_name("codelists", "cl_bank", "code", "description")
        for key, value in bank_list.iteritems():
            self.bank_cbox.addItem(value, key)

        code_lists = self.__codelist_names()
        for key, value in code_lists.iteritems():
            self.select_codelist_cbox.addItem(value, key)

        l1_codes = DatabaseUtils.l1_restriction_array()
        l2_codes = DatabaseUtils.l2_restriction_array()

        self.__set_up_feezone_cbox(l1_codes, l2_codes)
        self.__set_up_taxzone_cbox(l1_codes, l2_codes)

        self.__set_equipment_cbox()
        self.__cpage_cbox()

    def __set_equipment_cbox(self):

        equipment_list = []
        users_list = []

        try:
            equipment_list = self.session.query(ClEquipmentList).all()
            users_list = self.session.query(SetRole).all()
            aimag_list = self.session.query(AuLevel1.name, AuLevel1.code).\
                filter(AuLevel1.code != '013').filter(AuLevel1.code != '012').order_by(AuLevel1.name.desc()).all()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        self.equipment_list_cbox.addItem("*", -1)
        self.users_list_cbox.addItem("*", -1)
        self.aimags_cbox.addItem("*", -1)
        for item in equipment_list:
            self.equipment_list_cbox.addItem(item.description, item.code)
        for item in users_list:
            display_name = item.user_name + u": "+ item.surname[:1] + u"."+ item.first_name
            self.users_list_cbox.addItem(display_name, item.user_name_real)
        for auLevel1 in aimag_list:
            self.aimags_cbox.addItem(auLevel1.name, auLevel1.code)

        working_aimag = DatabaseUtils.working_l1_code()
        working_soum = DatabaseUtils.working_l2_code()
        self.aimags_cbox.setCurrentIndex(self.aimags_cbox.findData(working_aimag))
        self.soums_cbox.setCurrentIndex(self.soums_cbox.findData(working_soum))

    @pyqtSlot(int)
    def on_aimags_cbox_currentIndexChanged(self, index):

        aimag = self.aimags_cbox.itemData(index)
        self.soums_cbox.clear()

        self.soums_cbox.addItem("*", -1)

        soum_list = []

        if aimag == -1:
            soum_list = self.session.query(AuLevel2).all()
            for au_level2 in soum_list:
                if au_level2.code[:2] == '01':
                    self.soums_cbox.addItem(au_level2.name, au_level2.code)

        else:
            try:
                if not aimag:
                    aimag = ''
                soum_list = self.session.query(AuLevel2.name, AuLevel2.code).filter(
                    AuLevel2.code.like(aimag + "%")).all()

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
                self.reject()

            for au_level2 in soum_list:
                self.soums_cbox.addItem(au_level2.name, au_level2.code)

    @pyqtSlot(int)
    def on_register_search_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.add_equipment_button.setDisabled(True)
            self.edit_equipment_button.setDisabled(True)
            self.delete_equipment_button.setDisabled(True)
            self.add_equip_doc_button.setDisabled(True)
            self.view_equip_doc_button.setDisabled(True)
            self.delete_equip_doc_button.setDisabled(True)
            self.equipment_find_button.setDisabled(False)
        else:
            self.add_equipment_button.setDisabled(False)
            self.edit_equipment_button.setDisabled(False)
            self.delete_equipment_button.setDisabled(False)
            self.add_equip_doc_button.setDisabled(False)
            self.view_equip_doc_button.setDisabled(False)
            self.delete_equip_doc_button.setDisabled(False)
            self.equipment_find_button.setDisabled(True)

    def __set_up_feezone_cbox(self, l1_codes, l2_codes):

        locations1 = self.session.query(SetFeeZone.location, SetFeeZone.code).distinct(). \
            filter(SetFeeZone.geometry.ST_Within(AuLevel1.geometry)). \
            filter(AuLevel1.code.in_(l1_codes)). \
            filter(or_(AuLevel1.code.startswith('01'), AuLevel1.code.startswith('1'))). \
            order_by(SetFeeZone.location)
        locations2 = self.session.query(SetFeeZone.location, SetFeeZone.code).distinct(). \
            filter(SetFeeZone.geometry.ST_Within(AuLevel2.geometry)). \
            filter(AuLevel2.code.in_(l2_codes)). \
            order_by(SetFeeZone.location)
        locations3 = self.session.query(SetFeeZone.location, SetFeeZone.code).distinct(). \
            filter(SetFeeZone.geometry.ST_Contains(AuLevel2.geometry)). \
            filter(AuLevel2.code.in_(l2_codes)). \
            order_by(SetFeeZone.location)
        locations4 = self.session.query(SetFeeZone.location, SetFeeZone.code).distinct(). \
            filter(SetFeeZone.geometry.ST_Intersects(AuLevel2.geometry)). \
            filter(AuLevel2.code.in_(l2_codes)). \
            order_by(SetFeeZone.location)

        for location in locations1:
            self.zone_location_cbox.addItem(location[0], location[1])
        # for location in locations2:
        #     self.zone_location_cbox.addItem(location[0], location[1])
        for location in locations3:
            self.zone_location_cbox.addItem(location[0], location[1])
        for location in locations4:
            if location[0]!= self.zone_location_cbox.itemText(self.zone_location_cbox.currentIndex()):
                self.zone_location_cbox.addItem(location[0], location[1])

    def __set_up_taxzone_cbox(self, l1_codes, l2_codes):

        locations1 = self.session.query(SetTaxAndPriceZone.location, SetTaxAndPriceZone.code).distinct(). \
            filter(SetTaxAndPriceZone.geometry.ST_Within(AuLevel1.geometry)). \
            filter(AuLevel1.code.in_(l1_codes)). \
            filter(or_(AuLevel1.code.startswith('01'), AuLevel1.code.startswith('1'))). \
            order_by(SetTaxAndPriceZone.location)
        locations2 = self.session.query(SetTaxAndPriceZone.location, SetTaxAndPriceZone.code).distinct(). \
            filter(SetTaxAndPriceZone.geometry.ST_Within(AuLevel2.geometry)). \
            filter(AuLevel2.code.in_(l2_codes)). \
            order_by(SetTaxAndPriceZone.location)
        locations3 = self.session.query(SetTaxAndPriceZone.location, SetTaxAndPriceZone.code).distinct(). \
            filter(SetTaxAndPriceZone.geometry.ST_Contains(AuLevel2.geometry)). \
            filter(AuLevel2.code.in_(l2_codes)). \
            order_by(SetTaxAndPriceZone.location)
        locations4 = self.session.query(SetTaxAndPriceZone.location, SetTaxAndPriceZone.code).distinct(). \
            filter(SetTaxAndPriceZone.geometry.ST_Intersects(AuLevel2.geometry)). \
            filter(AuLevel2.code.in_(l2_codes)). \
            order_by(SetTaxAndPriceZone.location)

        for location in locations1:
            self.zone_location_tax_cbox.addItem(location[0], location[1])
        # for location in locations2:
        #     self.zone_location_tax_cbox.addItem(location[0], location[1])
        for location in locations3:
            self.zone_location_tax_cbox.addItem(location[0], location[1])
        for location in locations4:
            if location[0] != self.zone_location_tax_cbox.itemText(self.zone_location_tax_cbox.currentIndex()):
                self.zone_location_tax_cbox.addItem(location[0], location[1])

    def __load_settings(self):

        self.__load_report_settings()
        self.__load_certificate_settings()
        self.__load_payment_settings()
        self.__load_logging_settings()

    def __load_report_settings(self):

        self.doc_path_edit.setText(QSettings().value(SettingsConstants.DOCUMENT_PATH))
        self.webgis_ip_edit.setText(QSettings().value(SettingsConstants.WEBGIS_IP))

        report_settings = self.__admin_settings("set_report_parameter")
        if len(report_settings) == 0:
            return

        self.land_office_name_edit.setText(report_settings[Constants.REPORT_LAND_OFFICE_NAME])
        self.phone_edit.setText(report_settings[Constants.REPORT_PHONE])
        self.fax_edit.setText(report_settings[Constants.REPORT_FAX])
        self.email_address_edit.setText(report_settings[Constants.REPORT_EMAIL])
        self.web_site_edit.setText(report_settings[Constants.REPORT_WEBSITE])
        self.bank_account_num_edit.setText(report_settings[Constants.REPORT_BANK_ACCOUNT])
        self.address_edit.setText(report_settings[Constants.REPORT_ADDRESS])
        self.bank_account_num_edit.setText(report_settings[Constants.REPORT_BANK_ACCOUNT])
        self.bank_cbox.setCurrentIndex(self.bank_cbox.findText(report_settings[Constants.REPORT_BANK]))

    def __load_certificate_settings(self):

        certificate_type = []

        try:
            certificate_type = self.session.query(ClCertificateType).all()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr('File Error'), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        for item in certificate_type:
            self.certificate_type_cbox.addItem(item.description, item.code)

        self.certificate_range_twidget.sortItems(0, Qt.AscendingOrder)
        self.certificate_range_twidget.resizeColumnToContents(0)
        self.certificate_range_twidget.resizeColumnToContents(1)
        self.certificate_range_twidget.resizeColumnToContents(2)
        self.certificate_range_twidget.resizeColumnToContents(3)
        self.certificate_range_twidget.resizeColumnToContents(4)
        self.certificate_range_twidget.resizeColumnToContents(5)
        self.certificate_range_twidget.resizeColumnToContents(6)

        self.certificate_range_twidget.setColumnWidth(0, 50)
        self.certificate_range_twidget.setColumnWidth(1, 100)
        self.certificate_range_twidget.setColumnWidth(2, 100)
        self.certificate_range_twidget.setColumnWidth(3, 100)
        self.certificate_range_twidget.setColumnWidth(4, 100)
        self.certificate_range_twidget.setColumnWidth(5, 100)
        self.certificate_range_twidget.setColumnWidth(5, 200)
        # self.training_twidget.horizontalHeader().setResizeMode(3, QHeaderView.Stretch)

        self.certificate_range_twidget.setAlternatingRowColors(True)
        self.certificate_range_twidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.certificate_range_twidget.setSelectionMode(QTableWidget.SingleSelection)

        delegate = DateDelegate(self.certificate_range_twidget)
        self.certificate_range_twidget.setItemDelegateForColumn(1, delegate)

        delegate = DateDelegate(self.certificate_range_twidget)
        self.certificate_range_twidget.setItemDelegateForColumn(2, delegate)

        delegate = IntegerSpinBoxDelegate(3, 1, 10000000, 1000, 10, self.certificate_range_twidget)
        self.certificate_range_twidget.setItemDelegateForColumn(3, delegate)

        delegate = IntegerSpinBoxDelegate(4, 1, 10000000, 1000, 10, self.certificate_range_twidget)
        self.certificate_range_twidget.setItemDelegateForColumn(4, delegate)

        # certificate_settings = self.__certificate_range(1)
        # self.mn_citizen_first_number_spinbox.setValue(certificate_settings[Constants.CERTIFICATE_FIRST_NUMBER])
        # self.mn_citizen_last_number_spinbox.setValue(certificate_settings[Constants.CERTIFICATE_LAST_NUMBER])
        # self.mn_citizen_current_number_ledit.setText(str(certificate_settings[Constants.CERTIFICATE_CURRENT_NUMBER]))
        #
        # certificate_settings = self.__certificate_range(2)
        # self.mn_business_first_number_spinbox.setValue(certificate_settings[Constants.CERTIFICATE_FIRST_NUMBER])
        # self.mn_business_last_number_spinbox.setValue(certificate_settings[Constants.CERTIFICATE_LAST_NUMBER])
        # self.mn_business_current_number_ledit.setText(str(certificate_settings[Constants.CERTIFICATE_CURRENT_NUMBER]))
        #
        # certificate_settings = self.__certificate_range(3)
        # self.foreign_first_number_spinbox.setValue(certificate_settings[Constants.CERTIFICATE_FIRST_NUMBER])
        # self.foreign_last_number_spinbox.setValue(certificate_settings[Constants.CERTIFICATE_LAST_NUMBER])
        # self.foreign_current_number_ledit.setText(str(certificate_settings[Constants.CERTIFICATE_CURRENT_NUMBER]))
        #
        # certificate_settings = self.__certificate_range(4)
        # self.mn_org_first_number_spinbox.setValue(certificate_settings[Constants.CERTIFICATE_FIRST_NUMBER])
        # self.mn_org_last_number_spinbox.setValue(certificate_settings[Constants.CERTIFICATE_LAST_NUMBER])
        # self.mn_org_current_number_ledit.setText(str(certificate_settings[Constants.CERTIFICATE_CURRENT_NUMBER]))

    def __load_payment_settings(self):

        payment_settings = self.__payment_settings()
        if len(payment_settings) == 0 and payment_settings == None:
            return
        if payment_settings[Constants.PAYMENT_LANDTAX_RATE] == None:
            self.fee_finerate_spinbox.setValue(0)
            self.tax_finerate_spinbox.setValue(0)
        else:
            self.fee_finerate_spinbox.setValue(payment_settings[Constants.PAYMENT_LANDFEE_RATE])
            self.tax_finerate_spinbox.setValue(payment_settings[Constants.PAYMENT_LANDTAX_RATE])

    def __load_logging_settings(self):

        logging_settings = self.__logging_settings()
        if logging_settings:
            self.logging_chk_box.setChecked(True)

    def __save_settings(self):

        # try:
            self.__save_report_settings()
            self.__save_certificate_settings()
            self.__save_payment_settings()
            self.__save_logging_settings()
            self.__save_fees()
            self.__save_taxes()
            self.__save_companies()
            self.__save_surveyors()
            self.__save_codelist_entries()
            # self.__save_documents()
            self.__save_equipments()
            self.__save_training()
            self.__save_certificate_person()
            self.__save_training_person()

            return True
        # except exc.SQLAlchemyError,  e:
        #     PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
        #     return False
        #
        # except LM2Exception, e:
        #     return False

    def __save_equipments(self):

        num_rows = self.equipment_twidget.rowCount()
        try:
            for row in range(num_rows):
                item = self.equipment_twidget.item(row,0)
                id = item.data(Qt.UserRole)
                equipment = self.session.query(SetEquipment).filter(SetEquipment.id == id).one()
                item = self.equipment_twidget.item(row,1)
                equipment.type = item.data(Qt.UserRole)
                item = self.equipment_twidget.item(row,2)
                equipment.officer_user = item.data(Qt.UserRole)
                item = self.equipment_twidget.item(row,3)
                equipment.purchase_date = item.data(Qt.UserRole)
                item = self.equipment_twidget.item(row,4)
                equipment.given_date = item.data(Qt.UserRole)
                item = self.equipment_twidget.item(row,5)
                equipment.duration_date = item.data(Qt.UserRole)
                item = self.equipment_twidget.item(row,6)
                equipment.description = item.data(Qt.UserRole)
                item = self.equipment_twidget.item(row,7)
                equipment.mac_address = item.data(Qt.UserRole)
                item = self.equipment_twidget.item(row,8)
                equipment.seller_name = item.data(Qt.UserRole)
                item = self.equipment_twidget.item(row,9)
                equipment.aimag = item.data(Qt.UserRole)
                item = self.equipment_twidget.item(row,10)
                equipment.soum = item.data(Qt.UserRole)

                self.session.add(equipment)

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
            raise
        self.__equipment_clear()

    @pyqtSlot()
    def on_clear_button_clicked(self):

        self.mac_address_edit.clear()
        self.seller_name_edit.clear()
        self.id_equipment_edit.clear()
        self.equipment_desc_text.clear()
        self.equipment_doc_twidget.clear()
        self.initial_date.setDate(QDate.currentDate())
        self.given_date.setDate(QDate.currentDate())
        self.duration_date.setDate(QDate.currentDate())

        self.equipment_list_cbox.setCurrentIndex(self.equipment_list_cbox.findData(-1))
        self.users_list_cbox.setCurrentIndex(self.users_list_cbox.findData(-1))

        self.equipment_twidget.setRowCount(0)
        # self.equipment_results_label.setText("")
        self.add_equip_doc_button.setEnabled(False)
        self.view_equip_doc_button.setEnabled(False)
        self.delete_equip_doc_button.setEnabled(False)

    @pyqtSlot()
    def on_find_button_clicked(self):

        self.__search_equipment()

    def __search_equipment(self):
        try:
            equipments = self.session.query(SetEquipment)
            filter_is_set = False

            if self.equipment_desc_text.toPlainText():
                filter_is_set = True
                desc = "%" + self.equipment_desc_text.toPlainText() + "%"
                equipments = equipments.filter(SetEquipment.description.ilike(desc))

            if self.seller_name_edit.text():
                filter_is_set = True
                seller_name = "%" + self.seller_name_edit.text() + "%"
                equipments = equipments.filter(SetEquipment.seller_name.ilike(seller_name))

            if self.equipment_list_cbox.currentIndex() != -1:
                if not self.equipment_list_cbox.itemData(self.equipment_list_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    equipment_type = self.equipment_list_cbox.itemData(self.equipment_list_cbox.currentIndex())
                    equipments = equipments.filter(SetEquipment.type == equipment_type)

            if self.users_list_cbox.currentIndex() != -1:
                if not self.users_list_cbox.itemData(self.users_list_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    officer = self.users_list_cbox.itemData(self.users_list_cbox.currentIndex())
                    equipments = equipments.filter(SetEquipment.officer_user == officer)

            count = 0

            self.__remove_equipment_items()

            # if equipments.distinct(SetEquipment.id).count() == 0:
            #     self.error_label.setText(self.tr("No equipments found for this search filter."))
            #     return

            # elif filter_is_set is False:
            #     self.error_label.setText(self.tr("Please specify a search filter."))
            #     return

            for equipment in equipments.distinct(SetEquipment.id).all():
                id_item = QTableWidgetItem(str(equipment.id))
                # item.setIcon(QIcon(QPixmap(":/plugins/lm2/application.png")))
                id_item.setData(Qt.UserRole, equipment.id)

                equipment_type = equipment.type
                equipment_type_text = equipment.type_ref.description
                equipment_type_item = QTableWidgetItem(equipment_type_text)
                equipment_type_item.setData(Qt.UserRole, equipment_type)

                officer_user = equipment.officer_user
                officer_user_text = equipment.officer_user_ref.surname[:1] + u"." + equipment.officer_user_ref.first_name
                officer_user_item = QTableWidgetItem(officer_user_text)
                officer_user_item.setData(Qt.UserRole, officer_user)

                decsription = equipment.description
                decsription_item = QTableWidgetItem(decsription)
                decsription_item.setData(Qt.UserRole, decsription)

                purchase_date = equipment.purchase_date
                given_date = equipment.given_date
                duration_date = equipment.duration_date

                purchase_date_item = QTableWidgetItem(str(purchase_date))
                purchase_date_item.setData(Qt.UserRole, purchase_date)

                given_date_item = QTableWidgetItem(str(given_date))
                given_date_item.setData(Qt.UserRole, given_date)

                duration_date_item = QTableWidgetItem(str(duration_date))
                duration_date_item.setData(Qt.UserRole, duration_date)

                mac_address = equipment.mac_address
                mac_address_item = QTableWidgetItem(mac_address)
                mac_address_item.setData(Qt.UserRole, mac_address)

                seller_name = equipment.seller_name
                seller_name_item = QTableWidgetItem(seller_name)
                seller_name_item.setData(Qt.UserRole, seller_name)

                aimag = equipment.aimag
                aimag_item = QTableWidgetItem(equipment.aimag_ref.name)
                aimag_item.setData(Qt.UserRole, aimag)

                soum = equipment.soum
                soum_item = QTableWidgetItem(equipment.soum_ref.name)
                soum_item.setData(Qt.UserRole, soum)

                self.equipment_twidget.insertRow(count)
                self.equipment_twidget.setItem(count, 0, id_item)
                self.equipment_twidget.setItem(count, 1, equipment_type_item)
                self.equipment_twidget.setItem(count, 2, officer_user_item)
                self.equipment_twidget.setItem(count, 3, purchase_date_item)
                self.equipment_twidget.setItem(count, 4, given_date_item)
                self.equipment_twidget.setItem(count, 5, duration_date_item)
                self.equipment_twidget.setItem(count, 6, decsription_item)
                self.equipment_twidget.setItem(count, 7, mac_address_item)
                self.equipment_twidget.setItem(count, 8, seller_name_item)
                self.equipment_twidget.setItem(count, 9, aimag_item)
                self.equipment_twidget.setItem(count, 10, soum_item)
                count += 1

            # self.error_label.setText("")
            # self.equipment_results_label.setText(self.tr("Results: ") + str(count))

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    def __remove_equipment_items(self):

        self.equipment_twidget.setRowCount(0)
        # self.equipment_results_label.setText("")

    @pyqtSlot()
    def on_add_equipment_button_clicked(self):

        if self.id_equipment_edit.text() != "":
            PluginUtils.show_message(self, self.tr("Equipment save"), self.tr("Please Save Button click!!!"))
            return

        try:
            equipment_type = self.equipment_list_cbox.itemData(self.equipment_list_cbox.currentIndex())
            equipment_type_text = self.equipment_list_cbox.currentText()
            officer_user = self.users_list_cbox.itemData(self.users_list_cbox.currentIndex())
            officer_user_text = self.users_list_cbox.currentText()
            decsription = self.equipment_desc_text.toPlainText()
            purchase_date = PluginUtils.convert_qt_date_to_python(self.initial_date.date())
            given_date = PluginUtils.convert_qt_date_to_python(self.given_date.date())
            duration_date = PluginUtils.convert_qt_date_to_python(self.duration_date.date())
            mac_address = self.mac_address_edit.text()
            seller_name = self.seller_name_edit.text()
            aimag = self.aimags_cbox.itemData(self.aimags_cbox.currentIndex())
            soum = self.soums_cbox.itemData(self.soums_cbox.currentIndex())
            aimag_text = self.aimags_cbox.currentText()
            soum_text = self.soums_cbox.currentText()

            if equipment_type == -1:
                PluginUtils.show_message(self, self.tr("Equipment type"), self.tr("Equipment type is none!!!"))
                return
            if officer_user == -1:
                PluginUtils.show_message(self, self.tr("officer user"), self.tr("Officer user is none!!!"))
                return

            if aimag == -1:
                PluginUtils.show_message(self, self.tr("Aimag list"), self.tr("Aimag is none!!!"))
                return

            if soum == -1:
                PluginUtils.show_message(self, self.tr("Soum list"), self.tr("Soum is none!!!"))
                return

             #session add
            user = self.session.query(SetRole).filter(SetRole.user_name_real == officer_user).one()

            aimag_ref = self.session.query(AuLevel1).filter(AuLevel1.code == aimag).one()
            soum_ref = self.session.query(AuLevel2).filter(AuLevel2.code == soum).one()

            set_equipment = SetEquipment()
            set_equipment.type = equipment_type
            set_equipment.officer_user = officer_user
            set_equipment.officer_user_ref = user
            set_equipment.description = decsription
            set_equipment.purchase_date = purchase_date
            set_equipment.given_date = given_date
            set_equipment.duration_date = duration_date
            set_equipment.mac_address = mac_address
            set_equipment.seller_name = seller_name
            set_equipment.aimag = aimag
            set_equipment.aimag_ref = aimag_ref
            set_equipment.soum = soum
            set_equipment.soum_ref = soum_ref

            self.session.add(set_equipment)
            self.session.commit()

            id = set_equipment.id

            id_item = QTableWidgetItem(str(id))
            id_item.setData(Qt.UserRole, id)

            equipment_type_item = QTableWidgetItem(equipment_type_text)
            equipment_type_item.setData(Qt.UserRole, equipment_type)

            officer_user_item = QTableWidgetItem(officer_user_text)
            officer_user_item.setData(Qt.UserRole, officer_user)

            decsription_item = QTableWidgetItem(decsription)
            decsription_item.setData(Qt.UserRole, decsription)

            purchase_date_item = QTableWidgetItem(str(purchase_date))
            purchase_date_item.setData(Qt.UserRole, purchase_date)

            given_date_item = QTableWidgetItem(str(given_date))
            given_date_item.setData(Qt.UserRole, given_date)

            duration_date_item = QTableWidgetItem(str(duration_date))
            duration_date_item.setData(Qt.UserRole, duration_date)

            mac_address_item = QTableWidgetItem(mac_address)
            mac_address_item.setData(Qt.UserRole, mac_address)

            seller_name_item = QTableWidgetItem(seller_name)
            seller_name_item.setData(Qt.UserRole, seller_name)

            aimag_item = QTableWidgetItem(aimag_text)
            aimag_item.setData(Qt.UserRole, aimag)

            soum_item = QTableWidgetItem(soum_text)
            soum_item.setData(Qt.UserRole, soum)

            row = self.equipment_twidget.rowCount()
            self.equipment_twidget.insertRow(row)

            self.equipment_twidget.setItem(row, 0, id_item)
            self.equipment_twidget.setItem(row, 1, equipment_type_item)
            self.equipment_twidget.setItem(row, 2, officer_user_item)
            self.equipment_twidget.setItem(row, 3, purchase_date_item)
            self.equipment_twidget.setItem(row, 4, given_date_item)
            self.equipment_twidget.setItem(row, 5, duration_date_item)
            self.equipment_twidget.setItem(row, 6, decsription_item)
            self.equipment_twidget.setItem(row, 7, mac_address_item)
            self.equipment_twidget.setItem(row, 8, seller_name_item)
            self.equipment_twidget.setItem(row, 9, aimag_item)
            self.equipment_twidget.setItem(row, 10, soum_item)

            self.__equipment_clear()

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
            raise


    @pyqtSlot(QTableWidgetItem)
    def on_equipment_twidget_itemClicked(self, item):

        # self.equipment_twidget.selectAll()
        self.add_equipment_button.setDisabled(True)
        self.add_equip_doc_button.setEnabled(True)
        self.view_equip_doc_button.setEnabled(True)
        self.delete_equip_doc_button.setEnabled(True)

        current_row = self.equipment_twidget.currentRow()
        id_item = self.equipment_twidget.item(current_row, 0)
        id = ""
        if id_item is not None:
            id = id_item.data(Qt.UserRole)

        equipment_type_item = self.equipment_twidget.item(current_row, 1)
        user_item = self.equipment_twidget.item(current_row, 2)
        purchase_date_item = self.equipment_twidget.item(current_row, 3)
        given_date_item = self.equipment_twidget.item(current_row, 4)
        duration_date_item = self.equipment_twidget.item(current_row, 5)
        description_item = self.equipment_twidget.item(current_row, 6)
        mac_address_item = self.equipment_twidget.item(current_row, 7)
        seller_name_item = self.equipment_twidget.item(current_row, 8)
        aimag_item = self.equipment_twidget.item(current_row, 9)
        soum_item = self.equipment_twidget.item(current_row, 10)

        equipment = self.session.query(SetEquipment).filter(SetEquipment.id == id).one()

        self.id_equipment_edit.setText(str(id))
        equipment_type = None
        user = None
        purchase_date = None
        if equipment_type_item is not None:
             equipment_type = equipment_type_item.data(Qt.UserRole)
        if user_item is not None:
            user = user_item.data(Qt.UserRole)
        if purchase_date_item is not None:
            purchase_date = purchase_date_item.data(Qt.UserRole)
        if given_date_item is not None:
            given_date = given_date_item.data(Qt.UserRole)
        if duration_date_item is not None:
            duration_date = duration_date_item.data(Qt.UserRole)
        if description_item is not None:
            description = description_item.data(Qt.UserRole)
        if mac_address_item is not None:
            mac_address = mac_address_item.data(Qt.UserRole)
        if seller_name_item is not None:
            seller_name = seller_name_item.data(Qt.UserRole)

        self.equipment_list_cbox.setCurrentIndex(self.equipment_list_cbox.findData(equipment_type))
        self.users_list_cbox.setCurrentIndex(self.users_list_cbox.findData(user))
        self.initial_date.setDate(purchase_date)
        self.given_date.setDate(given_date)
        self.duration_date.setDate(duration_date)
        self.equipment_desc_text.setText(description)
        self.mac_address_edit.setText(mac_address)
        self.seller_name_edit.setText(seller_name)
        self.aimags_cbox.setCurrentIndex(self.aimags_cbox.findData(equipment.aimag_ref.code))
        self.soums_cbox.setCurrentIndex(self.soums_cbox.findData(equipment.soum_ref.code))

        try:
            equipment_doc = self.session.query(SetEquipmentDocument).filter(SetEquipmentDocument.equipment == id).all()
            row = 0
            for item in equipment_doc:
                document_id = item.document
                document = self.session.query(SetDocument).filter(SetDocument.id == document_id).one()

                item = QListWidgetItem(document.name, self.equipment_doc_twidget)
                item.setData(Qt.UserRole, document_id)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        self.__remove_eq_document_items()
        self.__update_user_documents_file_twidget(user)

    def __seller_name_auto_choose(self):

        try:
            seller_list = self.session.query(SetEquipment.seller_name).order_by(SetEquipment.seller_name.desc()).all()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
            self.reject()

        seller_slist = []

        for seller in seller_list:
            if seller[0]:
                seller_slist.append(seller[0])

        seller_model = QStringListModel(seller_slist)
        self.sellerProxyModel = QSortFilterProxyModel()
        self.sellerProxyModel.setSourceModel(seller_model)
        self.sellerCompleter = QCompleter(self.sellerProxyModel, self, activated=self.on_seller_completer_activated)
        self.sellerCompleter.setCompletionMode(QCompleter.PopupCompletion)
        self.seller_name_edit.setCompleter(self.sellerCompleter)

    @pyqtSlot(str)
    def on_seller_completer_activated(self, text):

        if not text:
            return
        self.sellerCompleter.activated[str].emit(text)

    def __set_up_equipment_tab(self):

        self.__seller_name_auto_choose()
        self.equipment_twidget.setRowCount(0)
        try:
            equipment = self.session.query(SetEquipment).all()
            row = 0
            for items in equipment:
                self.equipment_twidget.insertRow(row)

                item = QTableWidgetItem(str(items.id))
                item.setData(Qt.UserRole, items.id)
                self.equipment_twidget.setItem(row, 0, item)

                equipment_type = self.session.query(ClEquipmentList).filter(ClEquipmentList.code == items.type).one()
                item = QTableWidgetItem(equipment_type.description)
                item.setData(Qt.UserRole, items.type)
                self.equipment_twidget.setItem(row, 1, item)

                user = self.session.query(SetRole).filter(SetRole.user_name_real == items.officer_user).one()
                display_name = items.officer_user +": "+ user.surname[:1] + u"."+ user.first_name
                item = QTableWidgetItem(display_name)
                item.setData(Qt.UserRole, items.officer_user)
                self.equipment_twidget.setItem(row, 2, item)

                item = QTableWidgetItem(str(items.purchase_date))
                item.setData(Qt.UserRole, items.purchase_date)
                self.equipment_twidget.setItem(row, 3, item)

                item = QTableWidgetItem(str(items.given_date))
                item.setData(Qt.UserRole, items.given_date)
                self.equipment_twidget.setItem(row, 4, item)

                item = QTableWidgetItem(str(items.duration_date))
                item.setData(Qt.UserRole, items.duration_date)
                self.equipment_twidget.setItem(row, 5, item)

                item = QTableWidgetItem(items.description)
                item.setData(Qt.UserRole, items.description)
                self.equipment_twidget.setItem(row, 6, item)

                item = QTableWidgetItem(items.mac_address)
                item.setData(Qt.UserRole, items.mac_address)
                self.equipment_twidget.setItem(row, 7, item)

                item = QTableWidgetItem(items.seller_name)
                item.setData(Qt.UserRole, items.seller_name)
                self.equipment_twidget.setItem(row, 8, item)

                item = QTableWidgetItem(items.aimag_ref.name)
                item.setData(Qt.UserRole, items.aimag)
                self.equipment_twidget.setItem(row, 9, item)

                item = QTableWidgetItem(items.soum_ref.name)
                item.setData(Qt.UserRole, items.soum)
                self.equipment_twidget.setItem(row, 10, item)

                row += 1

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    @pyqtSlot()
    def on_edit_equipment_button_clicked(self):

        if self.equipment_twidget.rowCount() == 0:
            PluginUtils.show_message(self, self.tr("No row"), self.tr("Equipment no row!!!"))
            return

        self.add_equipment_button.setEnabled(True)
        self.equipment_doc_twidget.clear()
        self.add_equip_doc_button.setDisabled(True)
        self.view_equip_doc_button.setDisabled(True)
        self.delete_equip_doc_button.setDisabled(True)

        selected_row = self.equipment_twidget.currentRow()

        equipment_type_item = self.equipment_twidget.item(selected_row, 1)
        officer_user_item = self.equipment_twidget.item(selected_row, 2)
        purchase_date_item = self.equipment_twidget.item(selected_row, 3)
        given_date_item = self.equipment_twidget.item(selected_row, 4)
        duration_date_item = self.equipment_twidget.item(selected_row, 5)
        decsription_item = self.equipment_twidget.item(selected_row, 6)
        mac_address_item = self.equipment_twidget.item(selected_row, 7)
        seller_name_item = self.equipment_twidget.item(selected_row, 8)
        aimag_item = self.equipment_twidget.item(selected_row, 9)
        soum_item = self.equipment_twidget.item(selected_row, 10)

        equipment_type = self.equipment_list_cbox.itemData(self.equipment_list_cbox.currentIndex())
        equipment_type_text = self.equipment_list_cbox.currentText()
        officer_user = self.users_list_cbox.itemData(self.users_list_cbox.currentIndex())
        officer_user_text = self.users_list_cbox.currentText()
        decsription = self.equipment_desc_text.toPlainText()
        purchase_date = PluginUtils.convert_qt_date_to_python(self.initial_date.date())
        given_date = PluginUtils.convert_qt_date_to_python(self.given_date.date())
        duration_date = PluginUtils.convert_qt_date_to_python(self.duration_date.date())
        mac_address = self.mac_address_edit.text()
        seller_name = self.seller_name_edit.text()
        aimag = self.aimags_cbox.itemData(self.aimags_cbox.currentIndex())
        aimag_text = self.aimags_cbox.currentText()
        soum = self.soums_cbox.itemData(self.soums_cbox.currentIndex())
        soum_text = self.soums_cbox.currentText()

        if equipment_type == -1:
            PluginUtils.show_message(self, self.tr("Equipment type"), self.tr("Equipment type is none!!!"))
            return
        if officer_user == -1:
            PluginUtils.show_message(self, self.tr("officer user"), self.tr("Officer user is none!!!"))
            return
        if aimag == -1:
            PluginUtils.show_message(self, self.tr("Aimag"), self.tr("Aimag is none!!!"))
            return
        if soum == -1:
            PluginUtils.show_message(self, self.tr("Soum"), self.tr("Soum is none!!!"))
            return

        equipment_type_item.setText(equipment_type_text)
        equipment_type_item.setData(Qt.UserRole, equipment_type)
        officer_user_item.setText(officer_user_text)
        officer_user_item.setData(Qt.UserRole, officer_user)
        purchase_date_item.setText(str(purchase_date))
        purchase_date_item.setData(Qt.UserRole, purchase_date)
        given_date_item.setText(str(given_date))
        given_date_item.setData(Qt.UserRole, given_date)
        duration_date_item.setText(str(duration_date))
        duration_date_item.setData(Qt.UserRole, duration_date)
        decsription_item.setText(decsription)
        decsription_item.setData(Qt.UserRole, decsription)
        mac_address_item.setText(mac_address)
        mac_address_item.setData(Qt.UserRole, mac_address)
        seller_name_item.setText(seller_name)
        seller_name_item.setData(Qt.UserRole, seller_name)
        aimag_item.setText(aimag_text)
        aimag_item.setData(Qt.UserRole, aimag)
        soum_item.setText(soum_text)
        soum_item.setData(Qt.UserRole, soum)

        # self.__equipment_clear()
    @pyqtSlot()
    def on_load_equip_doc_button_clicked(self):

        self.__remove_eq_document_items()
        self.__update_eq_documents_file_twidget()
        self.add_equip_doc_button.setEnabled(False)
        self.view_equip_doc_button.setEnabled(False)
        self.delete_equip_doc_button.setEnabled(False)

    @pyqtSlot()
    def on_add_equip_doc_button_clicked(self):

        row = self.equipment_twidget.currentRow()
        username = self.equipment_twidget.item(row, 2).data(Qt.UserRole)
        givedate = str(self.equipment_twidget.item(row, 4).data(Qt.UserRole))

        archive_equipment_path = FilePath.equipment_file_path()
        if not os.path.exists(archive_equipment_path):
            os.makedirs(archive_equipment_path)

        file_dialog = QFileDialog()
        file_dialog.setModal(True)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setFilter(self.tr("Decision Files (*.img *.png *.xls *.xlsx *.pdf)"))

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            file_path = QFileInfo(selected_file).filePath()

            num = []
            working_soum = DatabaseUtils.working_l2_code()
            if self.equipment_doc_twidget.count() == 0:
                file_name = username+ '-' + givedate +'-eq-'+ '01.pdf'
                num.append(int(file_name[-6]+file_name[-5]))
            else:
                for i in range(self.equipment_doc_twidget.count()):
                    doc_name_item = self.equipment_doc_twidget.item(i)
                    doc_name_no = doc_name_item.text()
                    num.append(int(doc_name_no[-6]+doc_name_no[-5]))

                max_num = max(num)
                max_num = str(max_num+1)
                if len((max_num)) == 1:
                    max_num = '0'+(max_num)
                file_name = username+ '-' + givedate +'-eq-'+ max_num +'.pdf'

            item = QListWidgetItem(file_name, self.equipment_doc_twidget)
            item.setData(Qt.UserRole, file_name)

            shutil.copy2(selected_file, archive_equipment_path+'/'+file_name)

    @pyqtSlot()
    def on_view_equip_doc_button_clicked(self):

        archive_equipment_path = FilePath.equipment_file_path()
        if not os.path.exists(archive_equipment_path):
            os.makedirs(archive_equipment_path)

        current_row = self.equipment_doc_twidget.currentRow()
        if current_row == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Select Item."))
            return
        byte_array_item = self.equipment_doc_twidget.selectedItems()[0]
        file_name = byte_array_item.text()

        shutil.copy2(archive_equipment_path + '/'+file_name, FilePath.view_file_path())
        QDesktopServices.openUrl(QUrl.fromLocalFile(FilePath.view_file_path()))


    @pyqtSlot()
    def on_delete_equip_doc_button_clicked(self):

        archive_equipment_path = FilePath.equipment_file_path()
        if not os.path.exists(archive_equipment_path):
            os.makedirs(archive_equipment_path)

        byte_array_item = self.equipment_doc_twidget.selectedItems()[0]
        item_index = self.equipment_doc_twidget.selectedIndexes()[0]

        dec_document_name = byte_array_item.text()
        self.equipment_doc_twidget.takeItem(item_index.row())
        os.remove(archive_equipment_path+'/'+dec_document_name)

    def __equipment_clear(self):

        self.id_equipment_edit.setText("")
        self.equipment_list_cbox.setCurrentIndex(0)
        self.users_list_cbox.setCurrentIndex(0)
        self.initial_date.setDate(QDate().currentDate())
        self.given_date.setDate(QDate().currentDate())
        self.duration_date.setDate(QDate().currentDate())
        self.mac_address_edit.setText("")
        self.equipment_desc_text.setText("")
        self.seller_name_edit.setText("")
        self.add_equipment_button.setEnabled(True)

    @pyqtSlot()
    def on_delete_equipment_button_clicked(self):

        current_row = self.equipment_twidget.currentRow()
        id_item = self.equipment_twidget.item(current_row, 0)
        id = id_item.data(Qt.UserRole)
        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to delete for equipment"))

        yes_button = message_box.addButton(self.tr("Yes"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("No"), QMessageBox.ActionRole)
        message_box.exec_()

        if message_box.clickedButton() == yes_button:
            try:
                equipment = self.session.query(SetEquipment).filter(SetEquipment.id == id).one()
                equipment_document = self.session.query(SetEquipmentDocument).filter(SetEquipmentDocument.equipment == id).all()
                for item in equipment_document:
                    document = self.session.query(SetDocument).filter(SetDocument.id == item.document).one()
                    self.session.delete(document)
                    self.session.delete(item)
                equipment = self.session.query(SetEquipment).filter(SetEquipment.id == id).one()
                self.session.delete(equipment)
                self.equipment_twidget.removeRow(current_row)

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

    @pyqtSlot()
    def on_equipment_find_button_clicked(self):

        print "ok"

    @pyqtSlot(int)
    def on_users_list_cbox_currentIndexChanged(self, idx):

        if self.id_equipment_edit.text() == "":
            self.equipment_twidget.setRowCount(0)
            if idx == -1:
                return
            equipment_type = self.equipment_list_cbox.itemData(self.equipment_list_cbox.currentIndex())
            officer_user = self.users_list_cbox.itemData(self.users_list_cbox.currentIndex())
            filter_is_set = False
            try:
                equipment = self.session.query(SetEquipment)
                if not self.equipment_list_cbox.itemData(self.equipment_list_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    equipment_type = self.equipment_list_cbox.itemData(self.equipment_list_cbox.currentIndex())
                    equipment = equipment.filter(SetEquipment.type == equipment_type)

                if not self.users_list_cbox.itemData(self.users_list_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    officer= self.users_list_cbox.itemData(self.users_list_cbox.currentIndex())
                    equipment = equipment.filter(SetEquipment.officer_user == officer)

                if not self.id_equipment_edit.text() == "":
                    filter_is_set = True
                    id = int(self.id_equipment_edit.text())
                    equipment = equipment.filter(SetEquipment.id == id)

                row = 0
                for items in equipment:
                    self.equipment_twidget.insertRow(row)

                    item = QTableWidgetItem(str(items.id))
                    item.setData(Qt.UserRole, items.id)
                    self.equipment_twidget.setItem(row, 0, item)

                    equipment_type = self.session.query(ClEquipmentList).filter(ClEquipmentList.code == items.type).one()
                    item = QTableWidgetItem(equipment_type.description)
                    item.setData(Qt.UserRole, items.type)
                    self.equipment_twidget.setItem(row, 1, item)

                    user = self.session.query(SetRole).filter(SetRole.user_name_real == items.officer_user).one()
                    display_name = items.officer_user +": "+ user.surname[:1] + u"."+ user.first_name
                    item = QTableWidgetItem(display_name)
                    item.setData(Qt.UserRole, items.officer_user)
                    self.equipment_twidget.setItem(row, 2, item)

                    item = QTableWidgetItem(str(items.purchase_date))
                    item.setData(Qt.UserRole, items.purchase_date)
                    self.equipment_twidget.setItem(row, 3, item)

                    item = QTableWidgetItem(str(items.given_date))
                    item.setData(Qt.UserRole, items.given_date)
                    self.equipment_twidget.setItem(row, 4, item)

                    item = QTableWidgetItem(str(items.duration_date))
                    item.setData(Qt.UserRole, items.duration_date)
                    self.equipment_twidget.setItem(row, 5, item)

                    item = QTableWidgetItem(items.description)
                    item.setData(Qt.UserRole, items.description)
                    self.equipment_twidget.setItem(row, 6, item)

                    item = QTableWidgetItem(items.mac_address)
                    item.setData(Qt.UserRole, items.mac_address)
                    self.equipment_twidget.setItem(row, 7, item)

                    item = QTableWidgetItem(items.seller_name)
                    item.setData(Qt.UserRole, items.seller_name)
                    self.equipment_twidget.setItem(row, 8, item)

                    item = QTableWidgetItem(items.aimag_ref.name)
                    item.setData(Qt.UserRole, items.aimag)
                    self.equipment_twidget.setItem(row, 9, item)

                    item = QTableWidgetItem(items.soum_ref.name)
                    item.setData(Qt.UserRole, items.soum)
                    self.equipment_twidget.setItem(row, 10, item)

                    row += 1

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

    @pyqtSlot(int)
    def on_equipment_list_cbox_currentIndexChanged(self, idx):

        if self.equipment_list_cbox.itemData(idx) == 10:
            self.mac_validator = QRegExpValidator(
                QRegExp("[a-zA-Z0-9]{2}:[a-zA-Z0-9]{2}:[a-zA-Z0-9]{2}:[a-zA-Z0-9]{2}:[a-zA-Z0-9]{2}:[a-zA-Z0-9]{2}"),
                None)
            self.mac_address_edit.setValidator(self.mac_validator)
        else:
            self.mac_validator = QRegExpValidator(
                QRegExp("[a-zA-Z0-9-]+"),
                None)
            self.mac_address_edit.setValidator(self.mac_validator)

        if self.id_equipment_edit.text() == "":
            self.equipment_twidget.setRowCount(0)
            if idx == -1:
                return
            equipment_type = self.equipment_list_cbox.itemData(self.equipment_list_cbox.currentIndex())
            officer_user = self.users_list_cbox.itemData(self.users_list_cbox.currentIndex())
            filter_is_set = False
            try:
                equipment = self.session.query(SetEquipment)
                if not self.equipment_list_cbox.itemData(self.equipment_list_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    equipment_type = self.equipment_list_cbox.itemData(self.equipment_list_cbox.currentIndex())
                    equipment = equipment.filter(SetEquipment.type == equipment_type)

                if not self.users_list_cbox.itemData(self.users_list_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    officer= self.users_list_cbox.itemData(self.users_list_cbox.currentIndex())
                    equipment = equipment.filter(SetEquipment.officer_user == officer)

                if not self.id_equipment_edit.text() == "":
                    filter_is_set = True
                    id = int(self.id_equipment_edit.text())
                    equipment = equipment.filter(SetEquipment.id == id)

                row = 0
                for items in equipment:
                    self.equipment_twidget.insertRow(row)

                    item = QTableWidgetItem(str(items.id))
                    item.setData(Qt.UserRole, items.id)
                    self.equipment_twidget.setItem(row, 0, item)

                    equipment_type = self.session.query(ClEquipmentList).filter(ClEquipmentList.code == items.type).one()
                    item = QTableWidgetItem(equipment_type.description)
                    item.setData(Qt.UserRole, items.type)
                    self.equipment_twidget.setItem(row, 1, item)

                    user = self.session.query(SetRole).filter(SetRole.user_name_real == items.officer_user).one()
                    display_name = items.officer_user +": "+ user.surname[:1] + u"."+ user.first_name
                    item = QTableWidgetItem(display_name)
                    item.setData(Qt.UserRole, items.officer_user)
                    self.equipment_twidget.setItem(row, 2, item)

                    item = QTableWidgetItem(str(items.purchase_date))
                    item.setData(Qt.UserRole, items.purchase_date)
                    self.equipment_twidget.setItem(row, 3, item)

                    item = QTableWidgetItem(str(items.given_date))
                    item.setData(Qt.UserRole, items.given_date)
                    self.equipment_twidget.setItem(row, 4, item)

                    item = QTableWidgetItem(str(items.duration_date))
                    item.setData(Qt.UserRole, items.duration_date)
                    self.equipment_twidget.setItem(row, 5, item)

                    item = QTableWidgetItem(items.description)
                    item.setData(Qt.UserRole, items.description)
                    self.equipment_twidget.setItem(row, 6, item)

                    item = QTableWidgetItem(items.mac_address)
                    item.setData(Qt.UserRole, items.mac_address)
                    self.equipment_twidget.setItem(row, 7, item)

                    item = QTableWidgetItem(items.seller_name)
                    item.setData(Qt.UserRole, items.seller_name)
                    self.equipment_twidget.setItem(row, 8, item)
                    if items.aimag:
                        item = QTableWidgetItem(items.aimag_ref.name)
                        item.setData(Qt.UserRole, items.aimag)
                        self.equipment_twidget.setItem(row, 9, item)
                    if items.soum:
                        item = QTableWidgetItem(items.soum_ref.name)
                        item.setData(Qt.UserRole, items.soum)
                        self.equipment_twidget.setItem(row, 10, item)

                    row += 1

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return


    def __save_report_settings(self):

        report_settings = {Constants.REPORT_LAND_OFFICE_NAME: self.land_office_name_edit.text(),
                           Constants.REPORT_ADDRESS: self.address_edit.toPlainText(),
                           Constants.REPORT_BANK: self.bank_cbox.currentText(),
                           Constants.REPORT_BANK_ACCOUNT: self.bank_account_num_edit.text(),
                           Constants.REPORT_PHONE: self.phone_edit.text(), Constants.REPORT_FAX: self.fax_edit.text(),
                           Constants.REPORT_EMAIL: self.email_address_edit.text(),
                           Constants.REPORT_WEBSITE: self.web_site_edit.text()}

        self.__write_report_settings(report_settings)

    @pyqtSlot()
    def on_add_range_button_clicked(self):

        row = self.certificate_range_twidget.rowCount()
        self.certificate_range_twidget.insertRow(row)
        now_date = QDate.currentDate().toString("yyyy-MM-dd")
        self.__add_certificate_range_row(row,now_date, now_date,1,50,1, self.tr('Enter training information!'), -1)

    def __add_certificate_range_row(self, row, begin_date, end_date, first_range, last_range, current_no, description,id):

        item = QTableWidgetItem(u'{0}'.format(row+1))
        item.setData(Qt.UserRole, id)
        self.certificate_range_twidget.setItem(row, 0, item)

        item = QTableWidgetItem(u'{0}'.format(begin_date))
        self.certificate_range_twidget.setItem(row, 1, item)

        item = QTableWidgetItem('{0}'.format(end_date))
        self.certificate_range_twidget.setItem(row, 2, item)

        item = QTableWidgetItem('{0}'.format(first_range))
        self.certificate_range_twidget.setItem(row, 3, item)

        item = QTableWidgetItem('{0}'.format(last_range))
        self.certificate_range_twidget.setItem(row, 4, item)

        item = QTableWidgetItem('{0}'.format(current_no))
        self.certificate_range_twidget.setItem(row, 5, item)

        item = QTableWidgetItem('{0}'.format(description))
        self.certificate_range_twidget.setItem(row, 6, item)

    @pyqtSlot(int)
    def on_certificate_type_cbox_currentIndexChanged(self, index):

        self.certificate_range_twidget.clearContents()
        self.certificate_range_twidget.setRowCount(0)
        certificate_type = self.certificate_type_cbox.itemData(index)

        try:
            certificate_range = self.session.query(SetCertificate).filter(SetCertificate.certificate_type == certificate_type).all()

            for certificate in certificate_range:

                row = self.certificate_range_twidget.rowCount()
                self.certificate_range_twidget.insertRow(row)

                item = QTableWidgetItem(u'{0}'.format(certificate.id))
                item.setData(Qt.UserRole, certificate.id)
                self.certificate_range_twidget.setItem(row, 0, item)

                item = QTableWidgetItem(u'{0}'.format(certificate.begin_date))
                self.certificate_range_twidget.setItem(row, 1, item)

                item = QTableWidgetItem('{0}'.format(certificate.end_date))
                self.certificate_range_twidget.setItem(row, 2, item)

                item = QTableWidgetItem('{0}'.format(certificate.range_first_no))
                self.certificate_range_twidget.setItem(row, 3, item)

                item = QTableWidgetItem('{0}'.format(certificate.range_last_no))
                self.certificate_range_twidget.setItem(row, 4, item)

                item = QTableWidgetItem('{0}'.format(certificate.current_no))
                self.certificate_range_twidget.setItem(row, 5, item)

                item = QTableWidgetItem('{0}'.format(certificate.description))
                self.certificate_range_twidget.setItem(row, 6, item)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))


    def __save_certificate_settings(self):

        for row in range(self.certificate_range_twidget.rowCount()):
            new_row = False
            cert_id = self.certificate_range_twidget.item(row, 0).data(Qt.UserRole)

            if cert_id == -1:
                new_row = True
                certificate = SetCertificate()
            else:
                certificate = self.session.query(SetCertificate).filter(SetCertificate.id == cert_id).one()

            certificate_type = self.certificate_type_cbox.itemData(self.certificate_type_cbox.currentIndex())
            str_date = self.certificate_range_twidget.item(row,1).text()
            if len(str_date) == 10:
                begin_date = datetime.strptime(str_date, "%Y-%m-%d")
            else:
                begin_date = datetime.strptime(str_date[:10], "%Y-%m-%d")
            certificate.begin_date = begin_date

            str_date = self.certificate_range_twidget.item(row,2).text()
            if len(str_date) == 10:
                end_date = datetime.strptime(str_date, "%Y-%m-%d")
            else:
                end_date = datetime.strptime(str_date[:10], "%Y-%m-%d")
            certificate.end_date = end_date
            certificate.range_first_no = int(self.certificate_range_twidget.item(row, 3).text())
            certificate.range_last_no = int(self.certificate_range_twidget.item(row, 4).text())
            certificate.current_no = int(self.certificate_range_twidget.item(row, 5).text())
            certificate.description = (self.certificate_range_twidget.item(row, 6).text())
            certificate.certificate_type = certificate_type

            if new_row:
                self.session.add(certificate)
        self.__read_certificate()

    def __read_certificate(self):

        self.certificate_range_twidget.clearContents()
        self.certificate_range_twidget.setRowCount(0)
        certificate_type = self.certificate_type_cbox.itemData(self.certificate_type_cbox.currentIndex())

        try:
            certificate_range = self.session.query(SetCertificate).filter(SetCertificate.certificate_type == certificate_type).all()

            for certificate in certificate_range:

                row = self.certificate_range_twidget.rowCount()
                self.certificate_range_twidget.insertRow(row)

                item = QTableWidgetItem(u'{0}'.format(certificate.id))
                item.setData(Qt.UserRole, certificate.id)
                self.certificate_range_twidget.setItem(row, 0, item)

                item = QTableWidgetItem(u'{0}'.format(certificate.begin_date))
                self.certificate_range_twidget.setItem(row, 1, item)

                item = QTableWidgetItem('{0}'.format(certificate.end_date))
                self.certificate_range_twidget.setItem(row, 2, item)

                item = QTableWidgetItem('{0}'.format(certificate.range_first_no))
                self.certificate_range_twidget.setItem(row, 3, item)

                item = QTableWidgetItem('{0}'.format(certificate.range_last_no))
                self.certificate_range_twidget.setItem(row, 4, item)

                item = QTableWidgetItem('{0}'.format(certificate.current_no))
                self.certificate_range_twidget.setItem(row, 5, item)

                item = QTableWidgetItem('{0}'.format(certificate.description))
                self.certificate_range_twidget.setItem(row, 6, item)
        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
            raise

    @pyqtSlot()
    def on_remove_range_button_clicked(self):

        row = self.certificate_range_twidget.currentRow()
        if row == -1:
            return

        id = self.certificate_range_twidget.item(row, 0).data(Qt.UserRole)
        if id != -1:  # already has a row in the database
            fee = self.session.query(SetCertificate).filter(SetCertificate.id == id).one()
            self.session.delete(fee)

        self.certificate_range_twidget.removeRow(row)

    def __save_payment_settings(self):

        payment_settings = {Constants.PAYMENT_LANDFEE_RATE: self.fee_finerate_spinbox.value(),
                            Constants.PAYMENT_LANDTAX_RATE: self.tax_finerate_spinbox.value()}

        self.__write_payment_settings(payment_settings)

    def __save_logging_settings(self):

        self.__write_logging_settings(self.logging_chk_box.isChecked())

    @pyqtSlot()
    def on_apply_button_clicked(self):

        if not self.__save_settings():
            return

        self.commit()
        self.__start_fade_out_timer()

    def __start_fade_out_timer(self):

        self.timer = QTimer()
        self.timer.timeout.connect(self.__fade_status_message)
        self.time_counter = 500
        self.timer.start(10)

    def __fade_status_message(self):

        opacity = int(self.time_counter * 0.5)
        self.status_label.setStyleSheet("QLabel {color: rgba(255,0,0," + str(opacity) + ");}")
        self.status_label.setText(self.tr('Changes applied successfully.'))
        if self.time_counter == 0:
            self.timer.stop()
        self.time_counter -= 1

    @pyqtSlot(int)
    def on_select_codelist_cbox_currentIndexChanged(self, idx):

        if idx == -1:
            return

        if self.old_codelist_index == idx:
            return

        if self.old_codelist_index == -1:
            self.__read_codelist_entries()
        else:
            # try:
            self.__save_codelist_entries()
            # except exc.SQLAlchemyError, e:
            #     PluginUtils.show_error(None, self.tr("SQL Error"), e.message)
            #     self.select_codelist_cbox.setCurrentIndex(self.old_codelist_index)
            #     return

        self.old_codelist_index = idx

    def __read_codelist_entries(self):

        self.table_widget.clearContents()
        self.table_widget.setRowCount(0)

        codelist_name = self.select_codelist_cbox.itemData(self.select_codelist_cbox.currentIndex())

        codelist_class = self.__codelist_class(codelist_name)
        codelist_entries = self.session.query(codelist_class).order_by(codelist_class.code).all()
        self.table_widget.setRowCount(len(codelist_entries))
        row = 0
        for entry in codelist_entries:
            self.__add_codelist_row(row, entry.code, entry.description)
            row += 1

        self.table_widget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)


    def __add_codelist_row(self, row, code, description, lock_item=True):

        if lock_item:
            item = QTableWidgetItem('{0}'.format(code))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        else:
            item = QTableWidgetItem()

        item.setData(Qt.UserRole, code)
        self.table_widget.setItem(row, CODELIST_CODE, item)
        item = QTableWidgetItem(description)
        self.table_widget.setItem(row, CODELIST_DESC, item)

    def __save_codelist_entries(self):

        codelist_name = self.select_codelist_cbox.itemData(self.old_codelist_index, Qt.UserRole)
        codelist_class = self.__codelist_class(codelist_name)

        session = SessionHandler().session_instance()
        self.create_savepoint()

        try:
            for row in range(self.table_widget.rowCount()):
                new_row = False

                code = self.table_widget.item(row, CODELIST_CODE).data(Qt.UserRole)

                if self.table_widget.item(row, CODELIST_CODE).text() == -1:
                    self.status_label.setText(self.tr("-1 is not allowed for code in codelists."))
                    self.rollback_to_savepoint()

                if code == -1:
                    new_row = True
                    # noinspection PyCallingNonCallable
                    codelist_entry = codelist_class()
                else:
                    codelist_entry = self.session.query(codelist_class).get(code)
                try:
                    code_int = int(self.table_widget.item(row, CODELIST_CODE).text())

                except ValueError:
                    self.status_label.setText(self.tr("A code in the codelist has a wrong value."))
                    self.rollback_to_savepoint()
                    raise LM2Exception(self.tr("Error"), self.tr("A code in the codelist has a wrong value."))
                codelist_name = self.select_codelist_cbox.itemData(self.select_codelist_cbox.currentIndex(),
                                                                   Qt.UserRole)
                if codelist_name == "cl_landuse_type":
                    description = self.table_widget.item(row, CODELIST_DESC).text()
                    codelist_entry.code = code_int
                    codelist_entry.description = description
                    codelist_entry.code2 = int(str(code_int)[:2])
                    codelist_entry.description2 = description
                else:
                    description = self.table_widget.item(row, CODELIST_DESC).text()
                    codelist_entry.code = code_int
                    codelist_entry.description = description

                if new_row:
                    session.add(codelist_entry)

        except exc.SQLAlchemyError:
            self.rollback_to_savepoint()
            raise

        self.__read_codelist_entries()

    def __save_documents(self):

        session = SessionHandler().session_instance()
        soum_code = DatabaseUtils.working_l2_code()
        schema_string = 's' + soum_code
        session.execute(
            "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)

        for i in range(self.doc_twidget.rowCount()):

            item_name = self.doc_twidget.item(i, DOC_NAME_COLUMN)
            item_description = self.doc_twidget.item(i, DOC_DESCRIPTION_COLUMN)
            item_visible = self.doc_twidget.item(i, DOC_VISIBLE_COLUMN)
            item_open = self.doc_twidget.item(i, DOC_OPEN_FILE_COLUMN)
            current_id = item_name.data(Qt.UserRole)

            if current_id == -1:
                document = SetOfficialDocument()
                session.add(document)
                session.flush()

                item_name.setData(Qt.UserRole, document.id)
                self.doc_twidget.setItem(i, DOC_NAME_COLUMN, item_name)
            else:
                document = self.session.query(SetOfficialDocument).get(current_id)

            document.name = item_name.text()
            document.description = item_description.text()
            if item_visible.checkState() == Qt.Checked:
                document.visible = True
            else:
                document.visible = False

            path = item_open.data(Qt.UserRole)
            #if file path is -1 it is an existing one & untouched
            if path != -1:
                file_info = QFileInfo(path)
                file_content = DatabaseUtils.file_data(file_info.filePath())
                document.content = bytes(file_content)

    @pyqtSlot()
    def on_add_button_clicked(self):

        if self.select_codelist_cbox.currentIndex() == -1:
            return

        row = self.table_widget.rowCount()
        self.table_widget.insertRow(row)

        self.__add_codelist_row(row, -1, None, False)

    @pyqtSlot()
    def on_delete_button_clicked(self):

        row = self.table_widget.currentRow()
        if row == -1:
            return

        codelist_name = self.select_codelist_cbox.itemData(self.select_codelist_cbox.currentIndex(), Qt.UserRole)
        codelist_class = self.__codelist_class(codelist_name)

        code = self.table_widget.item(row, CODELIST_CODE).data(Qt.UserRole)
        session = SessionHandler().session_instance()
        soum_code = DatabaseUtils.working_l2_code()
        schema_string = 's' + soum_code
        session.execute(
            "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)

        count = self.session.query(codelist_class).filter(codelist_class.code == code).count()
        if count > 0:
            entry = self.session.query(codelist_class).get(code)
            self.create_savepoint()
            try:
                session.delete(entry)

            except exc.SQLAlchemyError, e:
                self.rollback_to_savepoint()
                PluginUtils.show_error(None, self.tr("SQL Error"), e.message)
                return

        self.table_widget.removeRow(row)

    def __codelist_names(self):

        lookup = {}

        try:
            sql = text("select description, relname from pg_description join pg_class on pg_description.objoid = pg_class.oid join pg_namespace on pg_namespace.oid = pg_class.relnamespace where pg_namespace.nspname = 'codelists';")
            result = self.session.execute(sql).fetchall()

            for row in result:
                lookup[row[1]] = row[0]

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)

        return lookup

    def __write_logging_settings(self, log_level):

        session = SessionHandler().session_instance()
        soum_code = DatabaseUtils.working_l2_code()
        schema_string = 's' + soum_code
        session.execute(
            "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)

        try:
            sql = text("UPDATE settings.set_logging SET log_enabled = :logLevel;")
            session.execute(sql, {'logLevel': log_level})

        except exc.SQLAlchemyError:
            raise

    def __write_payment_settings(self, payment_settings):

        session = SessionHandler().session_instance()
        soum_code = DatabaseUtils.working_l2_code()
        schema_string = 's' + soum_code
        session.execute(
            "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)

        try:
            sql = text(
                "UPDATE settings.set_payment SET landfee_fine_rate_per_day = :landfee, landtax_fine_rate_per_day = :landtax;")
            session.execute(sql, {'landfee': payment_settings[Constants.PAYMENT_LANDFEE_RATE],
                                  'landtax': payment_settings[Constants.PAYMENT_LANDTAX_RATE]})

        except exc.SQLAlchemyError:
            raise

    def __write_certificate_settings(self, certificate_settings, certificate_type):

        session = SessionHandler().session_instance()
        soum_code = DatabaseUtils.working_l2_code()
        schema_string = 's' + soum_code
        session.execute(
            "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)

        try:
            certificate_set = self.session.query(SetCertificate).get(certificate_type)
            certificate_set.range_first_no = certificate_settings[Constants.CERTIFICATE_FIRST_NUMBER]
            certificate_set.range_last_no = certificate_settings[Constants.CERTIFICATE_LAST_NUMBER]
            session.flush()

        except exc.SQLAlchemyError:
            raise

    def __write_report_settings(self, report_settings):

        l2_code = DatabaseUtils.working_l2_code()
        session = SessionHandler().session_instance()
        soum_code = DatabaseUtils.working_l2_code()
        schema_string = 's' + soum_code
        session.execute(
            "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)

        for key_name, value in report_settings.iteritems():
            try:
                sql = text("UPDATE "+ "s" +l2_code +".set_report_parameter SET value = :bindValue WHERE name = :bindKey;")
                session.execute(sql, {'bindValue': value, 'bindKey': key_name})

            except exc.SQLAlchemyError:
                raise

    def __logging_settings(self):

        enabled = False

        try:
            sql = text("SELECT * FROM settings.set_logging;")
            result = self.session.execute(sql).fetchall()

            for row in result:
                return row[0]

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)


    def __payment_settings(self):

        lookup = {}

        try:
            sql = text("SELECT * FROM settings.set_payment;")
            result = self.session.execute(sql).fetchall()

            for row in result:
                lookup[Constants.PAYMENT_LANDTAX_RATE] = row[2]
                lookup[Constants.PAYMENT_LANDFEE_RATE] = row[1]

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)

        return lookup

    def __certificate_range(self, certificate_type):

        first_no, last_no, current_no = self.session.query(SetCertificate.range_first_no, SetCertificate.range_last_no, SetCertificate.current_no).filter(SetCertificate.type == certificate_type).one()
        return {Constants.CERTIFICATE_FIRST_NUMBER: first_no, Constants.CERTIFICATE_LAST_NUMBER: last_no, Constants.CERTIFICATE_CURRENT_NUMBER: current_no}

    def __admin_settings(self, table_name):

        lookup = {}
        l2_code = DatabaseUtils.working_l2_code()
        try:
            sql = "SELECT * FROM "+ "s"+l2_code+".{0};".format(table_name)
            result = self.session.execute(sql).fetchall()
            for row in result:
                lookup[row[0]] = row[1]

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)

        return lookup

    def __codelist_class(self, table_name):

        if table_name == 'cl_application_role':
            cls = ClApplicationRole
        elif table_name == "cl_application_status":
            cls = ClApplicationStatus
        elif table_name == "cl_application_type":
            cls = ClApplicationType
        elif table_name == "cl_bank":
            cls = ClBank
        elif table_name == "cl_contract_cancellation_reason":
            cls = ClContractCancellationReason
        elif table_name == "cl_contract_status":
            cls = ClContractStatus
        elif table_name == "cl_contract_condition":
            cls = ClContractCondition
        elif table_name == "cl_decision":
            cls = ClDecision
        elif table_name == "cl_decision_level":
            cls = ClDecisionLevel
        elif table_name == "cl_document_role":
            cls = ClDocumentRole
        elif table_name == "cl_gender":
            cls = ClGender
        elif table_name == "cl_landuse_type":
            cls = ClLanduseType
        #elif table_name == "cl_log_level":
        #    cls = ClLogLevel
        elif table_name == "cl_mortgage_type":
            cls = ClMortgageType
        elif table_name == "cl_payment_frequency":
            cls = ClPaymentFrequency
        elif table_name == "cl_person_role":
            cls = ClPersonRole
        elif table_name == "cl_person_type":
            cls = ClPersonType
        elif table_name == "cl_record_cancellation_reason":
            cls = ClRecordCancellationReason
        elif table_name == "cl_record_status":
            cls = ClRecordStatus
        elif table_name == "cl_record_right_type":
            cls = ClRecordRightType
        elif table_name == "cl_transfer_type":
            cls = ClTransferType
        elif table_name == "cl_right_type":
            cls = ClRightType
        elif table_name == "cl_equipment_list":
            cls = ClEquipmentList
        elif table_name == "va_type_agriculture":
            cls = VaTypeAgriculture
        elif table_name == "va_type_design":
            cls = VaTypeDesign
        elif table_name == "va_type_heat":
            cls = VaTypeHeat
        elif table_name == "va_type_landuse_building":
            cls = VaTypeLanduseBuilding
        elif table_name == "va_type_material":
            cls = VaTypeMaterial
        elif table_name == "va_type_parcel":
            cls = VaTypeParcel
        elif table_name == "va_type_purchase_or_lease":
            cls = VaTypePurchaseOrLease
        elif table_name == "va_type_side_fence":
            cls = VaTypeSideFence
        elif table_name == "va_type_source":
            cls = VaTypeSource
        elif table_name == "va_type_status_building":
            cls = VaTypeStatusBuilding
        elif table_name == "va_type_stove":
            cls = VaTypeStove
        elif table_name == "cl_position_type":
            cls = ClPositionType
        elif table_name == "cl_grud_type":
            cls = ClGrudType
        elif table_name == "cl_pasture_type":
            cls = ClPastureType
        elif table_name == "cl_employee_type":
            cls = ClEmployeeType
        elif table_name == "cl_member_role":
            cls = ClMemberRole
        elif table_name == "cl_user_cancel_reason":
            cls = ClMemberRole
        elif table_name == "cl_pollution_type":
            cls = ClPollutionType
        elif table_name == "cl_mortgage_status":
            cls = ClMortgageStatus
        else:
            return None

        return cls


    def __create_fee_view(self):

        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        sql = ""

        for au_level2 in au_level2_list:

            au_level2 = au_level2.strip()
            if not sql:
                sql = "Create temp view application_search as" + "\n"
            else:
                sql = sql + "UNION" + "\n"

            select = "SELECT application.app_no, application.app_timestamp, application.app_type, status.status, status.status_date, status.officer_in_charge, status.next_officer_in_charge, decision.decision_no, " \
                     "contract.contract_no, person.person_id, person.name, person.first_name, person.middle_name, parcel.parcel_id, tmp_parcel.parcel_id tmp_parcel_id, record.record_no " \
                     "FROM s{0}.ct_application application " \
                     "left join s{0}.ct_application_status status on status.application = application.app_no " \
                     "left join s{0}.ct_decision_application dec_app on dec_app.application = application.app_no " \
                     "left join s{0}.ct_decision decision on decision.decision_no = dec_app.decision " \
                     "left join s{0}.ct_record_application_role rec_app on application.app_no = rec_app.application " \
                     "left join s{0}.ct_ownership_record record on rec_app.record = record.record_no " \
                     "left join s{0}.ct_contract_application_role contract_app on application.app_no = contract_app.application " \
                     "left join s{0}.ct_contract contract on contract_app.contract = contract.contract_no " \
                     "left join s{0}.ct_application_person_role app_pers on app_pers.application = application.app_no " \
                     "left join base.bs_person person on person.person_id = app_pers.person " \
                     "left join s{0}.ca_tmp_parcel tmp_parcel on application.tmp_parcel = tmp_parcel.parcel_id " \
                     "left join s{0}.ca_union_parcel parcel on parcel.parcel_id = application.parcel ".format(au_level2) + "\n"

            sql = sql + select

        sql = "{0} order by app_no;".format(sql)

        try:
            self.session.execute(sql)
            self.commit()
        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    def __set_schema(self):

        soum_code = DatabaseUtils.working_l2_code()
        schema_string = 's' + soum_code
        self.session.execute(
            "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)

    @pyqtSlot(int)
    def on_zone_location_cbox_currentIndexChanged(self, idx):

        self.zones_lwidget.clear()
        self.from_zone_cbox.clear()
        self.to_zone_cbox.clear()

        soum_code = self.zone_location_cbox.itemData(idx, Qt.UserRole)
        self.zone_location_tax_cbox.setCurrentIndex(self.zone_location_tax_cbox.findData(soum_code))

        schema_string = 's'+ soum_code

        self.session.execute(
            "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)

        location = self.zone_location_cbox.currentText()

        if idx == -1:
            return

        zones = self.session.query(SetFeeZone.zone_id, SetFeeZone.zone_no). \
            filter(SetFeeZone.location == location).\
            filter(SetFeeZone.valid_till == 'infinity').order_by(SetFeeZone.zone_no)

        zone_begin = self.session.query(SetFeeZone.valid_from).\
            filter(SetFeeZone.location ==location).group_by(SetFeeZone.valid_from).all()
        for begin_date in zone_begin:
            self.zone_begin_date.addItem(str(begin_date.valid_from), begin_date.valid_from)

        zone_end = self.session.query(SetFeeZone.valid_till). \
            filter(SetFeeZone.location == location).group_by(SetFeeZone.valid_till).all()
        self.zone_end_date.addItem('*', -1)
        for end_date in zone_end:
            if end_date.valid_till:
                if int(end_date.valid_till.year) != 9999:
                    self.zone_end_date.addItem(str(end_date.valid_till), end_date.valid_till)

        for zone_id, zone_no in zones:
            item = QListWidgetItem('{0}'.format(zone_no), self.zones_lwidget)
            item.setData(Qt.UserRole, zone_id)
            self.from_zone_cbox.addItem(str(zone_no), zone_id)
            self.to_zone_cbox.addItem(str(zone_no), zone_id)

        if self.zones_lwidget.count() > 0:
            self.zones_lwidget.setCurrentRow(0)
        if self.to_zone_cbox.count() > 1:
            self.to_zone_cbox.setCurrentIndex(1)

        zone_fid = self.zones_lwidget.item(self.zones_lwidget.currentRow()).data(Qt.UserRole)
        zone = self.session.query(SetFeeZone).filter(SetFeeZone.zone_id == zone_fid).one()

        zone_no = zone.zone_no
        self.landuse_code_list = list()
        del self.landuse_code_list[:]

        if zone_no == 50 or zone_no == 60 or zone_no == 70 or zone_no == 80:
            for code, description in self.session.query(ClLanduseType.code, ClLanduseType.description). \
                    filter(ClLanduseType.code2.in_([11,12,13,14,15])).all():
                self.landuse_code_list.append(u'{0}: {1}'.format(code, description))
            delegate = LandUseComboBoxDelegate(FEE_LAND_USE, self.landuse_code_list, self.land_fee_twidget)
            self.land_fee_twidget.setItemDelegateForColumn(FEE_LAND_USE, delegate)
        else:
            for code, description in self.session.query(ClLanduseType.code, ClLanduseType.description). \
                    filter(ClLanduseType.code2 != 11, ClLanduseType.code2 != 12, ClLanduseType.code2 != 13 \
                               , ClLanduseType.code2 != 14, ClLanduseType.code2 != 15).all():
                self.landuse_code_list.append(u'{0}: {1}'.format(code, description))
            delegate = LandUseComboBoxDelegate(FEE_LAND_USE, self.landuse_code_list, self.land_fee_twidget)
            self.land_fee_twidget.setItemDelegateForColumn(FEE_LAND_USE, delegate)

    @pyqtSlot(int)
    def on_zone_location_tax_cbox_currentIndexChanged(self, idx):

        self.zones_tax_lwidget.clear()
        self.from_zone_tax_cbox.clear()
        self.to_zone_tax_cbox.clear()

        if idx == -1:
            return

        soum_code = self.zone_location_tax_cbox.itemData(idx, Qt.UserRole)
        self.zone_location_cbox.setCurrentIndex(self.zone_location_cbox.findData(soum_code))
        schema_string = 's' + soum_code

        self.session.execute(
            "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)

        location = self.zone_location_tax_cbox.currentText()

        zones = self.session.query(SetTaxAndPriceZone.zone_id, SetTaxAndPriceZone.zone_no). \
            filter(SetTaxAndPriceZone.location == location).order_by(SetTaxAndPriceZone.zone_no)

        for zone_id, zone_no in zones:
            item = QListWidgetItem('{0}'.format(zone_no), self.zones_tax_lwidget)
            item.setData(Qt.UserRole, zone_id)
            self.from_zone_tax_cbox.addItem(str(zone_no), zone_id)
            self.to_zone_tax_cbox.addItem(str(zone_no), zone_id)
        if self.zones_tax_lwidget.count() > 0:
            self.zones_tax_lwidget.setCurrentRow(0)
        if self.to_zone_tax_cbox.count() > 1:
            self.to_zone_tax_cbox.setCurrentIndex(1)

        zone_fid = self.zones_tax_lwidget.item(self.zones_tax_lwidget.currentRow()).data(Qt.UserRole)

        zone = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.zone_id == zone_fid).one()

        zone_no = zone.zone_no
        self.landuse_code_list = list()
        del self.landuse_code_list[:]

        if zone_no == 50 or zone_no == 60 or zone_no == 70 or zone_no == 80:
            for code, description in self.session.query(ClLanduseType.code, ClLanduseType.description). \
                    filter(ClLanduseType.code2.in_([11,12,13,14,15])).all():
                self.landuse_code_list.append(u'{0}: {1}'.format(code, description))
            delegate = LandUseComboBoxDelegate(TAX_LAND_USE, self.landuse_code_list, self.land_tax_twidget)
            self.land_tax_twidget.setItemDelegateForColumn(TAX_LAND_USE, delegate)
        else:
            for code, description in self.session.query(ClLanduseType.code, ClLanduseType.description). \
                    filter(ClLanduseType.code2 != 11, ClLanduseType.code2 != 12, ClLanduseType.code2 != 13 \
                               , ClLanduseType.code2 != 14, ClLanduseType.code2 != 15).all():
                self.landuse_code_list.append(u'{0}: {1}'.format(code, description))
            delegate = LandUseComboBoxDelegate(TAX_LAND_USE, self.landuse_code_list, self.land_tax_twidget)
            self.land_tax_twidget.setItemDelegateForColumn(TAX_LAND_USE, delegate)

    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def on_zones_lwidget_currentItemChanged(self, current_item, previous_item):

        if previous_item is not None:
            prev_zone_fid = previous_item.data(Qt.UserRole)
            self.__save_fees(prev_zone_fid)

        if current_item is not None:
            curr_zone_fid = current_item.data(Qt.UserRole)

            self.__read_fees(curr_zone_fid)
            self.zone_fid = curr_zone_fid

    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def on_zones_tax_lwidget_currentItemChanged(self, current_item, previous_item):

        if previous_item is not None:
            prev_zone_fid = previous_item.data(Qt.UserRole)
            self.__save_taxes(prev_zone_fid)

        if current_item is not None:
            curr_zone_fid = current_item.data(Qt.UserRole)
            self.__read_taxes(curr_zone_fid)

    def __read_fee_doc(self, zone_fid):

        fee = self.session.query(SetFeeZone).filter(SetFeeZone.zone_id == zone_fid).one()
        # for decision_doc in fee.documents:
        #     item = QListWidgetItem(decision_doc.document_ref.name, self.document_twidget)
        #     item.setData(Qt.UserRole, decision_doc)

    def __read_fees(self, zone_fid):

        self.land_fee_twidget.clearContents()
        self.land_fee_twidget.setRowCount(0)
        self.__set_schema()
        zone = self.session.query(SetFeeZone).filter(SetFeeZone.zone_id == zone_fid).one()
        fees = self.session.query(SetBaseFee).filter(SetBaseFee.fee_zone == zone.zone_id).all()
        self.land_fee_twidget.setRowCount(len(fees))
        row = 0
        for fee in fees:
            self.__add_fee_row(row, fee.id, fee.landuse_ref.code, fee.landuse_ref.description, fee.base_fee_per_m2,
                               fee.subsidized_area, fee.subsidized_fee_rate)
            row += 1

        self.land_fee_twidget.sortItems(0, Qt.AscendingOrder)
        self.land_fee_twidget.resizeColumnToContents(1)
        self.land_fee_twidget.resizeColumnToContents(2)
        self.land_fee_twidget.horizontalHeader().setResizeMode(3, QHeaderView.Stretch)

        self.change_begin_date.setDate(zone.valid_from)
        if zone.valid_till:
            self.change_end_date.setDate(zone.valid_till)
        self.document_twidget.clear()
        self.__read_fee_doc(zone_fid)

    def __read_taxes(self, zone_fid):

        self.land_tax_twidget.clearContents()
        self.land_tax_twidget.setRowCount(0)
        self.__set_schema()
        zone = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.zone_id == zone_fid).one()
        taxes = self.session.query(SetBaseTaxAndPrice).filter(SetBaseTaxAndPrice.tax_zone == zone.zone_id).all()
        self.land_tax_twidget.setRowCount(len(taxes))
        row = 0
        for tax in taxes:
            self.__add_tax_row(row, tax.id, tax.landuse_ref.code, tax.landuse_ref.description, tax.base_value_per_m2,
                               tax.base_tax_rate, tax.subsidized_area, tax.subsidized_tax_rate)
            row += 1

        self.land_tax_twidget.sortItems(0, Qt.AscendingOrder)
        self.land_tax_twidget.resizeColumnToContents(1)
        self.land_tax_twidget.resizeColumnToContents(2)
        self.land_tax_twidget.resizeColumnToContents(3)
        self.land_tax_twidget.horizontalHeader().setResizeMode(4, QHeaderView.Stretch)

    def __set_up_land_fee_tab(self):

        self.update_date.setDate(QDate.currentDate())

        zone_fid = self.zones_lwidget.item(self.zones_lwidget.currentRow()).data(Qt.UserRole)

        zone = self.session.query(SetFeeZone).filter(SetFeeZone.zone_id == zone_fid).one()

        zone_no = zone.zone_no
        if len(self.landuse_code_list) == 0:
            if zone_no != 50 or zone_no != 60 or zone_no != 70 or zone_no != 80:
                for code, description in self.session.query(ClLanduseType.code, ClLanduseType.description). \
                        filter(ClLanduseType.code2 != 11, ClLanduseType.code2 != 12, ClLanduseType.code2 != 13 \
                               , ClLanduseType.code2 != 14, ClLanduseType.code2 != 15).all():
                    self.landuse_code_list.append(u'{0}: {1}'.format(code, description))
            else:
                for code, description in self.session.query(ClLanduseType.code, ClLanduseType.description). \
                        filter(ClLanduseType.code2.in_([11,12,13,14,15])).all():
                    self.landuse_code_list.append(u'{0}: {1}'.format(code, description))

        self.__set_up_twidget(self.land_fee_twidget)

        delegate = LandUseComboBoxDelegate(FEE_LAND_USE, self.landuse_code_list, self.land_fee_twidget)
        self.land_fee_twidget.setItemDelegateForColumn(FEE_LAND_USE, delegate)
        # delegate = IntegerSpinBoxDelegate(FEE_BASE_FEE_PER_M2, 0, 10000, 0, 5, self.land_fee_twidget)
        delegate = DoubleSpinBoxDelegate(FEE_BASE_FEE_PER_M2, 0, 100000.0000, 0.0001, 0.001, self.land_fee_twidget)
        self.land_fee_twidget.setItemDelegateForColumn(FEE_BASE_FEE_PER_M2, delegate)
        delegate = IntegerSpinBoxDelegate(FEE_SUBSIDIZED_AREA, 0, 10000, 0, 5, self.land_fee_twidget)
        self.land_fee_twidget.setItemDelegateForColumn(FEE_SUBSIDIZED_AREA, delegate)
        delegate = DoubleSpinBoxDelegate(FEE_SUBSIDIZED_FEE_RATE, 0, 100, 0, 0.01, self.land_fee_twidget)
        self.land_fee_twidget.setItemDelegateForColumn(FEE_SUBSIDIZED_FEE_RATE, delegate)

    def __set_up_land_tax_tab(self):

        self.update_tax_date.setDate(QDate.currentDate())

        zone_fid = self.zones_tax_lwidget.item(self.zones_tax_lwidget.currentRow()).data(Qt.UserRole)

        zone = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.zone_id == zone_fid).one()

        zone_no = zone.zone_no
        if len(self.landuse_code_list) == 0:
            if zone_no != 50 or zone_no != 60 or zone_no != 70 or zone_no != 80:
                for code, description in self.session.query(ClLanduseType.code, ClLanduseType.description). \
                        filter(ClLanduseType.code2 != 11, ClLanduseType.code2 != 12, ClLanduseType.code2 != 13 \
                               , ClLanduseType.code2 != 14, ClLanduseType.code2 != 15).all():
                    self.landuse_code_list.append(u'{0}: {1}'.format(code, description))
            else:
                for code, description in self.session.query(ClLanduseType.code, ClLanduseType.description). \
                        filter(ClLanduseType.code2.in_([11,12,13,14,15])).all():
                    self.landuse_code_list.append(u'{0}: {1}'.format(code, description))

        self.__set_up_twidget(self.land_tax_twidget)

        delegate = LandUseComboBoxDelegate(TAX_LAND_USE, self.landuse_code_list, self.land_tax_twidget)
        self.land_tax_twidget.setItemDelegateForColumn(TAX_LAND_USE, delegate)
        # delegate = IntegerSpinBoxDelegate(TAX_BASE_VALUE_PER_M2, 0, 10000, 0, 5, self.land_tax_twidget)
        delegate = DoubleSpinBoxDelegate(TAX_BASE_VALUE_PER_M2, 0, 100000, 0, 0.01, self.land_tax_twidget)
        self.land_tax_twidget.setItemDelegateForColumn(TAX_BASE_VALUE_PER_M2, delegate)
        delegate = DoubleSpinBoxDelegate(TAX_BASE_TAX_RATE, 0, 100, 0, 0.01, self.land_tax_twidget)
        self.land_tax_twidget.setItemDelegateForColumn(TAX_BASE_TAX_RATE, delegate)
        delegate = IntegerSpinBoxDelegate(TAX_SUBSIDIZED_AREA, 0, 10000, 0, 5, self.land_tax_twidget)
        self.land_tax_twidget.setItemDelegateForColumn(TAX_SUBSIDIZED_AREA, delegate)
        delegate = DoubleSpinBoxDelegate(TAX_SUBSIDIZED_TAX_RATE, 0, 100, 0, 0.01, self.land_tax_twidget)
        self.land_tax_twidget.setItemDelegateForColumn(TAX_SUBSIDIZED_TAX_RATE, delegate)

    def __setup_doc_twidget(self):

        self.doc_twidget.setAlternatingRowColors(True)
        self.doc_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.doc_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.equipment_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.equipment_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.equipment_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.doc_twidget.horizontalHeader().resizeSection(0, 50)
        self.doc_twidget.horizontalHeader().resizeSection(1, 270)
        self.doc_twidget.horizontalHeader().resizeSection(2, 250)
        self.doc_twidget.horizontalHeader().resizeSection(3, 50)
        self.doc_twidget.horizontalHeader().resizeSection(4, 50)

        delegate = OfficialDocumentDelegate(self.doc_twidget, self)
        self.doc_twidget.setItemDelegate(delegate)

        # self.__load_documents()

    def __load_documents(self):

        working_soum = DatabaseUtils.working_l2_code()
        archive_legaldocuments_path = FilePath.legaldocuments_file_path()
        if not os.path.exists(archive_legaldocuments_path):
            os.makedirs(archive_legaldocuments_path)

        for file in os.listdir(archive_legaldocuments_path):
            os.listdir(archive_legaldocuments_path)
            if file.endswith(".pdf"):
                fee_soum = file[:5]
                file_name = file
                file_name1 = file.find('doc')
                if working_soum == fee_soum and file_name1 != -1:
                    item = QListWidgetItem(file_name, self.document_twidget)
                    item.setData(Qt.UserRole, file_name)

                    row = self.doc_twidget.rowCount()
                    self.doc_twidget.insertRow(row)
                    item_visible = QTableWidgetItem()
                    item_visible.setCheckState(Qt.Checked)

                    item_name = QTableWidgetItem()
                    item_name.setText(file_name)
                    item_name.setData(Qt.UserRole, file_name)

                    item_open = QTableWidgetItem()
                    item_open.setData(Qt.UserRole, -1)

                    item_description = QTableWidgetItem()
                    item_description.setText('')

                    self.doc_twidget.setItem(row, DOC_VISIBLE_COLUMN, item_visible)
                    self.doc_twidget.setItem(row, DOC_NAME_COLUMN, item_name)
                    self.doc_twidget.setItem(row, DOC_DESCRIPTION_COLUMN, item_description)
                    self.doc_twidget.setItem(row, DOC_OPEN_FILE_COLUMN, item_open)

    def __set_up_twidget(self, table_widget):

        table_widget.setAlternatingRowColors(True)
        table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        table_widget.setSelectionMode(QTableWidget.SingleSelection)
        table_widget.setColumnWidth(0, 300)

    @pyqtSlot()
    def on_add_fee_button_clicked(self):

        if self.zones_lwidget.currentRow() == -1:
            return

        used_codes = self.__collect_used_codes(self.land_fee_twidget)
        unused_code = '0000'
        for code in self.landuse_code_list:
            if code[0:4] not in used_codes:
                unused_code = code[0:4]
                break
        if unused_code == '0000':
            PluginUtils.show_error(self, self.tr("Add Row"), self.tr('The maximum number of rows is reached.'))
            return
        row = self.land_fee_twidget.rowCount()
        self.land_fee_twidget.insertRow(row)
        self.__add_fee_row(row, -1, unused_code, self.tr('Review entry!'), 0, 0, 0)

    @pyqtSlot()
    def on_add_tax_button_clicked(self):

        if self.zones_tax_lwidget.currentRow() == -1:
            return

        used_codes = self.__collect_used_codes(self.land_tax_twidget)
        unused_code = '0000'
        for code in self.landuse_code_list:
            if code[0:4] not in used_codes:
                unused_code = code[0:4]
                break
        if unused_code == '0000':
            PluginUtils.show_error(self, self.tr("Add Row"), self.tr('The maximum number of rows is reached.'))
            return
        row = self.land_tax_twidget.rowCount()
        self.land_tax_twidget.insertRow(row)
        self.__add_tax_row(row, -1, unused_code, self.tr('Review entry!'), 0, 0, 0, 0)

    def __collect_used_codes(self, fee_or_tax_twidget):

        used_codes = list()
        for row in range(fee_or_tax_twidget.rowCount()):
            landuse_code = fee_or_tax_twidget.item(row, 0).text()[0:4]
            used_codes.append(landuse_code)
        return used_codes

    @pyqtSlot()
    def on_delete_fee_button_clicked(self):

        row = self.land_fee_twidget.currentRow()
        if row == -1:
            return

        fee_id = self.land_fee_twidget.item(row, 0).data(Qt.UserRole)
        if fee_id != -1:  # already has a row in the database
            session = SessionHandler().session_instance()
            soum_code = DatabaseUtils.working_l2_code()
            schema_string = 's' + soum_code
            session.execute(
                "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)
            fee = self.session.query(SetBaseFee).filter(SetBaseFee.id == fee_id).one()
            session.delete(fee)

        self.land_fee_twidget.removeRow(row)

    @pyqtSlot()
    def on_delete_tax_button_clicked(self):

        row = self.land_tax_twidget.currentRow()
        if row == -1:
            return

        tax_id = self.land_tax_twidget.item(row, 0).data(Qt.UserRole)
        if tax_id != -1:  # already has a row in the database
            session = SessionHandler().session_instance()
            soum_code = DatabaseUtils.working_l2_code()
            schema_string = 's' + soum_code
            session.execute(
                "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)
            tax = self.session.query(SetBaseTaxAndPrice).filter(SetBaseTaxAndPrice.id == tax_id).one()
            session.delete(tax)

        self.land_tax_twidget.removeRow(row)

    def __add_fee_row(self, row, fee_id, landuse_code, landuse_desc, base_fee_per_m2, subsidized_area,
                      subsidized_fee_rate):

        item = QTableWidgetItem(u'{0}: {1}'.format(landuse_code, landuse_desc))
        item.setData(Qt.UserRole, fee_id)
        self.land_fee_twidget.setItem(row, FEE_LAND_USE, item)
        item = QTableWidgetItem('{0}'.format(base_fee_per_m2))
        self.land_fee_twidget.setItem(row, FEE_BASE_FEE_PER_M2, item)
        item = QTableWidgetItem('{0}'.format(subsidized_area))
        self.land_fee_twidget.setItem(row, FEE_SUBSIDIZED_AREA, item)
        item = QTableWidgetItem('{0}'.format(subsidized_fee_rate))
        self.land_fee_twidget.setItem(row, FEE_SUBSIDIZED_FEE_RATE, item)

    def __add_tax_row(self, row, tax_id, landuse_code, landuse_desc, base_value_per_m2, base_tax_rate, subsidized_area,
                      subsidized_tax_rate):

        item = QTableWidgetItem(u'{0}: {1}'.format(landuse_code, landuse_desc))
        item.setData(Qt.UserRole, tax_id)
        self.land_tax_twidget.setItem(row, TAX_LAND_USE, item)
        item = QTableWidgetItem('{0}'.format(base_value_per_m2))
        self.land_tax_twidget.setItem(row, TAX_BASE_VALUE_PER_M2, item)
        item = QTableWidgetItem('{0}'.format(base_tax_rate))
        self.land_tax_twidget.setItem(row, TAX_BASE_TAX_RATE, item)
        if not subsidized_area:
            subsidized_area = 0
        item = QTableWidgetItem('{0}'.format(subsidized_area))
        self.land_tax_twidget.setItem(row, TAX_SUBSIDIZED_AREA, item)
        item = QTableWidgetItem('{0}'.format(subsidized_tax_rate))
        self.land_tax_twidget.setItem(row, TAX_SUBSIDIZED_TAX_RATE, item)

    def reject(self):

        self.rollback()
        SessionHandler().destroy_session()
        QDialog.reject(self)

    def __save_fees(self, zone_fid=None):

        try:
            if zone_fid is None:
                zone_fid = self.zones_lwidget.item(self.zones_lwidget.currentRow()).data(Qt.UserRole)
            zone = self.session.query(SetFeeZone).filter(SetFeeZone.zone_id == zone_fid).one()

            for row in range(self.land_fee_twidget.rowCount()):
                new_row = False
                fee_id = self.land_fee_twidget.item(row, FEE_LAND_USE).data(Qt.UserRole)
                if fee_id == -1:
                    new_row = True
                    fee = SetBaseFee()
                else:
                    fee = self.session.query(SetBaseFee).filter(SetBaseFee.id == fee_id).one()

                landuse_code = self.land_fee_twidget.item(row, FEE_LAND_USE).text()[0:4]
                landuse = self.session.query(ClLanduseType).filter(ClLanduseType.code == landuse_code).one()
                fee.landuse_ref = landuse

                fee.base_fee_per_m2 = float(self.land_fee_twidget.item(row, FEE_BASE_FEE_PER_M2).text())
                fee.subsidized_area = int(self.land_fee_twidget.item(row, FEE_SUBSIDIZED_AREA).text())
                fee.subsidized_fee_rate = float(self.land_fee_twidget.item(row, FEE_SUBSIDIZED_FEE_RATE).text())

                if new_row:
                    zone.fees.append(fee)

            self.__read_fees(zone_fid)

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
            raise

    def __save_taxes(self, zone_fid=None):

        try:

            if zone_fid is None:
                zone_fid = self.zones_tax_lwidget.item(self.zones_tax_lwidget.currentRow()).data(Qt.UserRole)
            zone = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.zone_id == zone_fid).one()

            for row in range(self.land_tax_twidget.rowCount()):
                new_row = False
                tax_id = self.land_tax_twidget.item(row, TAX_LAND_USE).data(Qt.UserRole)
                if tax_id == -1:
                    new_row = True
                    tax = SetBaseTaxAndPrice()
                else:
                    tax = self.session.query(SetBaseTaxAndPrice).filter(SetBaseTaxAndPrice.id == tax_id).one()

                landuse_code = self.land_tax_twidget.item(row, TAX_LAND_USE).text()[0:4]
                landuse = self.session.query(ClLanduseType).filter(ClLanduseType.code == landuse_code).one()
                tax.landuse_ref = landuse

                tax.base_value_per_m2 = int(self.land_tax_twidget.item(row, TAX_BASE_VALUE_PER_M2).text())
                tax.base_tax_rate = float(self.land_tax_twidget.item(row, TAX_BASE_TAX_RATE).text())
                tax.subsidized_area = int(self.land_tax_twidget.item(row, TAX_SUBSIDIZED_AREA).text())
                tax.subsidized_tax_rate = float(self.land_tax_twidget.item(row, TAX_SUBSIDIZED_TAX_RATE).text())

                if new_row:
                    zone.taxes.append(tax)

            self.__read_taxes(zone_fid)

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
            raise

    @pyqtSlot()
    def on_copy_fees_button_clicked(self):

        from_zone_idx = self.from_zone_cbox.currentIndex()
        to_zone_idx = self.to_zone_cbox.currentIndex()
        if from_zone_idx == -1 or to_zone_idx == -1:
            return

        if from_zone_idx == to_zone_idx:
            PluginUtils.show_error(self, self.tr('Copy Fee Entries'),
                                    self.tr('Fee entries cannot be copied among the same zone!'))
            return

        # In case of rows just added make sure they get written before the copying
        if from_zone_idx == self.zones_lwidget.currentRow():
            self.__save_fees()

        from_zone_fid = self.from_zone_cbox.itemData(from_zone_idx, Qt.UserRole)

        try:
            session = SessionHandler().session_instance()
            soum_code = DatabaseUtils.working_l2_code()
            schema_string = 's' + soum_code
            session.execute(
                "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)
            from_zone = self.session.query(SetFeeZone).filter(SetFeeZone.zone_id == from_zone_fid).one()
            fee_count = len(from_zone.fees)

            message = self.tr("{0} fee entries will be copied from Zone {1} to"
                              " Zone {2} and overwrite all existing entries in Zone {2}."
                              " Do you want to continue?".format(fee_count, self.from_zone_cbox.currentText(),
                                                                self.to_zone_cbox.currentText()))

            if QMessageBox.No == QMessageBox.question(None, self.tr("Copy Fee Entries"), message,
                                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No):
                return

            to_zone_fid = self.to_zone_cbox.itemData(to_zone_idx, Qt.UserRole)
            to_zone = self.session.query(SetFeeZone).filter(SetFeeZone.zone_id == to_zone_fid).one()
            fee_count = len(to_zone.fees)
            for idx in reversed(xrange(fee_count)):
                del to_zone.fees[idx]
            session.flush()

            for fee in from_zone.fees:
                new_fee = SetBaseFee(landuse=fee.landuse, base_fee_per_m2=fee.base_fee_per_m2,
                                     subsidized_area=fee.subsidized_area,
                                     subsidized_fee_rate=fee.subsidized_fee_rate)
                to_zone.fees.append(new_fee)

            if self.zones_lwidget.currentRow() == to_zone_idx:
                self.__read_fees(to_zone_fid)
            else:
                self.zones_lwidget.setCurrentRow(to_zone_idx)

            PluginUtils.show_message(self, self.tr('Copy Fee Entries'), self.tr('Copying successfully completed.'))

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)

    @pyqtSlot()
    def on_copy_taxes_button_clicked(self):

        from_zone_idx = self.from_zone_tax_cbox.currentIndex()
        to_zone_idx = self.to_zone_tax_cbox.currentIndex()
        if from_zone_idx == -1 or to_zone_idx == -1:
            return

        if from_zone_idx == to_zone_idx:
            PluginUtils.show_error(self, self.tr('Copy Fee Entries'),
                                    self.tr('Tax entries cannot be copied among the same zone!'))
            return

        # In case of rows just added make sure they get written before the copying
        if from_zone_idx == self.zones_tax_lwidget.currentRow():
            self.__save_taxes()

        from_zone_fid = self.from_zone_tax_cbox.itemData(from_zone_idx, Qt.UserRole)

        try:
            session = SessionHandler().session_instance()
            soum_code = DatabaseUtils.working_l2_code()
            schema_string = 's' + soum_code
            session.execute(
                "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)
            from_zone = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.zone_id == from_zone_fid).one()
            tax_count = len(from_zone.taxes)

            message = self.tr("{0} tax entries will be copied from Zone {1} to"
                              " Zone {2} and overwrite all existing entries in Zone {2}."
                              " Do you want to continue?".format(tax_count, self.from_zone_tax_cbox.currentText(),
                                                                self.to_zone_tax_cbox.currentText()))

            if QMessageBox.No == QMessageBox.question(None, self.tr("Copy Tax Entries"), message,
                                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No):
                return

            to_zone_fid = self.to_zone_tax_cbox.itemData(to_zone_idx, Qt.UserRole)
            to_zone = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.zone_id == to_zone_fid).one()
            tax_count = len(to_zone.taxes)
            for idx in reversed(xrange(tax_count)):
                del to_zone.taxes[idx]
            session.flush()

            for tax in from_zone.taxes:
                new_tax = SetBaseTaxAndPrice(landuse=tax.landuse, base_value_per_m2=tax.base_value_per_m2,
                                             base_tax_rate=tax.base_tax_rate,
                                             subsidized_area=tax.subsidized_area,
                                             subsidized_tax_rate=tax.subsidized_tax_rate)
                to_zone.taxes.append(new_tax)

            if self.zones_tax_lwidget.currentRow() == to_zone_idx:
                self.__read_taxes(to_zone_fid)
            else:
                self.zones_tax_lwidget.setCurrentRow(to_zone_idx)

            PluginUtils.show_message(self, self.tr('Copy Tax Entries'), self.tr('Copying successfully completed.'))

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)

    @pyqtSlot("QDate")
    def on_update_date_dateChanged(self, update_date):

        day = update_date.day()
        if day != 1:
            self.update_date.setDate(QDate(update_date.year(), update_date.month(), 1))

    @pyqtSlot("QDate")
    def on_update_tax_date_dateChanged(self, update_date):

        day = update_date.day()
        if day != 1:
            self.update_tax_date.setDate(QDate(update_date.year(), update_date.month(), 1))

    @pyqtSlot()
    def on_update_contracts_button_clicked(self):

        message = 'Are you sure you want to update all contracts based on the new fees?'
        if QMessageBox.No == QMessageBox.question(None, self.tr("Update Contracts"), message,
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No):
            return

        update_date = PluginUtils.convert_qt_date_to_python(self.update_date.date()).date()
        # Warning if update date <= current date
        if update_date <= date.today():
            message = "The update date should be later than the current date. Are you sure you want to update the contracts?"
            if QMessageBox.No == QMessageBox.question(None, self.tr("Update Contracts"), message,
                                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No):
                return

        self.create_savepoint()
        session = SessionHandler().session_instance()
        soum_code = DatabaseUtils.working_l2_code()
        schema_string = 's' + soum_code
        session.execute(
            "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)

        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

            self.__save_fees()

            update_count = 0

            # Loop over restriction array
            l2_units = DatabaseUtils.l2_restriction_array()
            for l2_unit in l2_units:

                session.execute("SET search_path to s{0}, base, codelists, admin_units, settings, public".format(l2_unit))
                # Get active contracts only
                contracts = self.session.query(CtContract).\
                    filter(update_date < func.coalesce(CtContract.cancellation_date, CtContract.contract_end)).all()

                for contract in contracts:
                    application_role = contract.application_roles.\
                        filter(CtContractApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).one()
                    application = application_role.application_ref
                    parcel_id = application.parcel
                    if len(parcel_id) == 0:
                        # TODO: log something
                        # should never happen
                        continue

                    count = self.session.query(SetBaseFee).filter(SetFeeZone.geometry.ST_Contains(CaParcel.geometry)).\
                        filter(CaParcel.parcel_id == parcel_id).\
                        filter(SetBaseFee.fee_zone == SetFeeZone.zone_id).\
                        filter(SetBaseFee.landuse == CaParcel.landuse).\
                        count()

                    if count == 0:
                        # TODO: log something
                        # can happen
                        continue

                    base_fee = self.session.query(SetBaseFee).filter(SetFeeZone.geometry.ST_Contains(CaParcel.geometry)).\
                        filter(CaParcel.parcel_id == parcel_id).\
                        filter(SetBaseFee.fee_zone == SetFeeZone.zone_id).\
                        filter(SetBaseFee.landuse == CaParcel.landuse).\
                        one()

                    new_base_fee_per_m2 = base_fee.base_fee_per_m2
                    new_subsidized_area = base_fee.subsidized_area
                    new_subsidized_fee_rate = base_fee.subsidized_fee_rate

                    # Get latest archived fee
                    latest_archived_fee = contract.archived_fees.order_by(CtArchivedFee.valid_till.desc()).first()
                    if latest_archived_fee is None:
                        valid_from = date(2010, 1, 1)
                    else:
                        valid_from = latest_archived_fee.valid_till

                    count = 0
                    for fee in contract.fees:

                        if fee.base_fee_per_m2 != new_base_fee_per_m2 or\
                                fee.subsidized_area != new_subsidized_area or\
                                fee.subsidized_fee_rate != new_subsidized_fee_rate:

                            self.__archive_fee(contract, fee, valid_from, update_date)
                            self.__update_fee(fee, new_base_fee_per_m2, new_subsidized_area, new_subsidized_fee_rate)

                            if count == 0:
                                count += 1

                    update_count += count

                session.flush()

            QApplication.restoreOverrideCursor()
            PluginUtils.show_message(self, self.tr("Update Contracts"),
                                     self.tr('Updated {0} contracts. Click Apply to save the changes!'
                                             .format(update_count)))

        except exc.SQLAlchemyError, e:
            QApplication.restoreOverrideCursor()
            self.rollback_to_savepoint()
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)

    def __archive_fee(self, contract, fee, valid_from, valid_till):

        archived_fee = CtArchivedFee()
        archived_fee.person = fee.person
        archived_fee.share = fee.share
        archived_fee.area = fee.area
        archived_fee.fee_calculated = fee.fee_calculated
        archived_fee.fee_contract = fee.fee_contract
        archived_fee.grace_period = fee.grace_period
        archived_fee.base_fee_per_m2 = fee.base_fee_per_m2
        archived_fee.subsidized_area = fee.subsidized_area
        archived_fee.subsidized_fee_rate = fee.subsidized_fee_rate
        archived_fee.valid_from = valid_from
        archived_fee.valid_till = valid_till
        archived_fee.payment_frequency = fee.payment_frequency
        contract.archived_fees.append(archived_fee)

    def __update_fee(self, fee, new_base_fee_per_m2, new_subsidized_area, new_subsidized_fee_rate):

        fee.base_fee_per_m2 = new_base_fee_per_m2
        fee.subsidized_area = new_subsidized_area
        fee.subsidized_fee_rate = new_subsidized_fee_rate

        contractor_subsidized_area = int(round(float(fee.share) * new_subsidized_area))
        fee_subsidized = contractor_subsidized_area * new_base_fee_per_m2 * ((new_subsidized_fee_rate) / 100)
        fee_standard = (fee.area - contractor_subsidized_area) * new_base_fee_per_m2
        fee_calculated = int(round(fee_subsidized if fee_standard < 0 else fee_subsidized + fee_standard))

        fee.fee_calculated = fee_calculated
        fee.fee_contract = fee_calculated

    @pyqtSlot()
    def on_update_records_button_clicked(self):

        message = 'Are you sure you want to update all records based on the new taxes?'
        if QMessageBox.No == QMessageBox.question(None, self.tr("Update Ownership Records"), message,
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No):
            return

        update_date = PluginUtils.convert_qt_date_to_python(self.update_tax_date.date()).date()
        # Warning if update date <= current date
        if update_date <= date.today():
            message = "The update date should be later than the current date. Are you sure you want to update the records?"
            if QMessageBox.No == QMessageBox.question(None, self.tr("Update Ownership Records"), message,
                                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No):
                return

        self.create_savepoint()
        session = SessionHandler().session_instance()
        soum_code = DatabaseUtils.working_l2_code()
        schema_string = 's' + soum_code
        session.execute(
            "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)

        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

            self.__save_taxes()

            update_count = 0

            # Loop over restriction array
            l2_units = DatabaseUtils.l2_restriction_array()
            for l2_unit in l2_units:

                session.execute("SET search_path to s{0}, base, codelists, admin_units, settings, public".format(l2_unit))
                # Get active records only
                records = self.session.query(CtOwnershipRecord).\
                    filter(or_(CtOwnershipRecord.cancellation_date.is_(None), update_date < CtOwnershipRecord.cancellation_date)).all()

                for record in records:
                    count = record.application_roles.\
                        filter(CtContractApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).count()
                    if count == 0:
                        # TODO: log something
                        # should never happen
                        continue
                    application_role = record.application_roles.\
                        filter(CtContractApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).one()
                    application = application_role.application_ref
                    parcel_id = application.parcel
                    if len(parcel_id) == 0:
                        # TODO: log something
                        # should never happen
                        continue

                    count = self.session.query(SetBaseTaxAndPrice).filter(SetTaxAndPriceZone.geometry.ST_Contains(CaParcel.geometry)).\
                        filter(CaParcel.parcel_id == parcel_id).\
                        filter(SetBaseTaxAndPrice.tax_zone == SetTaxAndPriceZone.zone_id).\
                        filter(SetBaseTaxAndPrice.landuse == CaParcel.landuse).\
                        count()

                    if count == 0:
                        # TODO: log something
                        # can happen
                        continue

                    base_tax_and_price = self.session.query(SetBaseTaxAndPrice).filter(SetTaxAndPriceZone.geometry.ST_Contains(CaParcel.geometry)).\
                        filter(CaParcel.parcel_id == parcel_id).\
                        filter(SetBaseTaxAndPrice.tax_zone == SetTaxAndPriceZone.zone_id).\
                        filter(SetBaseTaxAndPrice.landuse == CaParcel.landuse).\
                        one()

                    new_base_value_per_m2 = base_tax_and_price.base_value_per_m2
                    new_base_tax_rate = base_tax_and_price.base_tax_rate
                    new_subsidized_area = base_tax_and_price.subsidized_area
                    new_subsidized_tax_rate = base_tax_and_price.subsidized_tax_rate

                    # Get latest archived tax
                    latest_archived_tax = record.archived_taxes.\
                        order_by(CtArchivedTaxAndPrice.valid_till.desc()).first()
                    if latest_archived_tax is None:
                        valid_from = date(2010, 1, 1)
                    else:
                        valid_from = latest_archived_tax.valid_till

                    count = 0
                    for tax in record.taxes:

                        if tax.base_value_per_m2 != new_base_value_per_m2 or\
                                tax.base_tax_rate != new_base_tax_rate or\
                                tax.subsidized_area != new_subsidized_area or\
                                tax.subsidized_tax_rate != new_subsidized_tax_rate:

                            self.__archive_tax(record, tax, valid_from, update_date)
                            self.__update_tax(tax, new_base_value_per_m2, new_base_tax_rate, new_subsidized_area,
                                              new_subsidized_tax_rate)

                            if count == 0:
                                count += 1

                    update_count += count

                session.flush()

            QApplication.restoreOverrideCursor()
            PluginUtils.show_message(self, self.tr("Update Ownership Records"),
                                     self.tr('Updated {0} records. Click Apply to save the changes!'
                                             .format(update_count)))

        except exc.SQLAlchemyError, e:
            QApplication.restoreOverrideCursor()
            self.rollback_to_savepoint()
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)

    def __archive_tax(self, record, tax, valid_from, valid_till):

        archived_tax = CtArchivedTaxAndPrice()
        archived_tax.person = tax.person
        archived_tax.share = tax.share
        archived_tax.area = tax.area
        archived_tax.value_calculated = tax.value_calculated
        archived_tax.price_paid = tax.price_paid
        archived_tax.land_tax = tax.land_tax
        archived_tax.grace_period = tax.grace_period
        archived_tax.base_value_per_m2 = tax.base_value_per_m2
        archived_tax.base_tax_rate = tax.base_tax_rate
        archived_tax.subsidized_area = tax.subsidized_area
        archived_tax.subsidized_tax_rate = tax.subsidized_tax_rate
        archived_tax.valid_from = valid_from
        archived_tax.valid_till = valid_till
        archived_tax.payment_frequency = tax.payment_frequency
        record.archived_taxes.append(archived_tax)

    def __update_tax(self, tax, new_base_value_per_m2, new_base_tax_rate, new_subsidized_area, new_subsidized_tax_rate):

        tax.base_value_per_m2 = new_base_value_per_m2
        tax.base_tax_rate = new_base_tax_rate
        tax.subsidized_area = new_subsidized_area
        tax.subsidized_tax_rate = new_subsidized_tax_rate

        value_calculated = tax.area * new_base_value_per_m2
        owner_subsidized_area = int(round(float(tax.share) * new_subsidized_area))
        tax_subsidized = owner_subsidized_area * new_base_value_per_m2 * ((new_base_tax_rate) / 100) * ((new_subsidized_tax_rate) / 100)
        tax_standard = (tax.area - owner_subsidized_area) * new_base_value_per_m2 * ((new_base_tax_rate) / 100)
        tax_calculated = int(round(tax_subsidized if tax_standard < 0 else tax_subsidized + tax_standard))

        tax.value_calculated = value_calculated
        tax.land_tax = tax_calculated

    @pyqtSlot()
    def on_add_company_button_clicked(self):

        row = self.company_twidget.rowCount()
        self.company_twidget.insertRow(row)
        self.__add_company_row(row, -1, self.tr('Review entry!'), self.tr('Review entry!'))

    @pyqtSlot()
    def on_add_surveyor_button_clicked(self):

        if self.company_twidget.currentRow() == -1:
            return

        if self.company_twidget.item(self.company_twidget.currentRow(), 0).data(Qt.UserRole) == -1:
            PluginUtils.show_error(self, self.tr('Add Surveyor'), self.tr('Apply your changes first!'))
            return

        row = self.surveyor_twidget.rowCount()
        self.surveyor_twidget.insertRow(row)
        self.__add_surveyor_row(row, -1, self.tr('Review entry!'), self.tr('Review entry!'), self.tr('Review entry!'))

    def __set_up_company_tab(self):

        self.__set_up_twidget(self.company_twidget)
        self.__read_companies()

    def __set_up_surveyor_tab(self):

        self.__set_up_twidget(self.surveyor_twidget)
        self.surveyor_twidget.setColumnWidth(SURVEYOR_SURNAME, 250)
        self.surveyor_twidget.setColumnWidth(SURVEYOR_FIRST_NAME, 250)

    def __read_companies(self):

        self.company_twidget.clearContents()
        self.company_twidget.setRowCount(0)

        companies = self.session.query(SetSurveyCompany).order_by(SetSurveyCompany.name).all()
        self.company_twidget.setRowCount(len(companies))
        row = 0
        for company in companies:
            self.__add_company_row(row, company.id, company.name, company.address)
            row += 1

        self.company_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        if self.company_twidget.rowCount() > 0:
            self.company_twidget.setCurrentCell(0, 0)

    def __read_surveyors(self, company_id):

        self.surveyor_twidget.clearContents()
        self.surveyor_twidget.setRowCount(0)

        if company_id == -1:
            return

        company = self.session.query(SetSurveyCompany).filter(SetSurveyCompany.id == company_id).one()
        self.surveyor_twidget.setRowCount(len(company.surveyors))
        row = 0
        for surveyor in company.surveyors:
            self.__add_surveyor_row(row, surveyor.id, surveyor.surname, surveyor.first_name, surveyor.phone)
            row += 1

        self.surveyor_twidget.horizontalHeader().setResizeMode(2, QHeaderView.Stretch)

    def __add_surveyor_row(self, row, surveyor_id, surveyor_surname, surveyor_first_name, surveyor_phone):

        item = QTableWidgetItem(u'{0}'.format(surveyor_surname))
        item.setData(Qt.UserRole, surveyor_id)
        self.surveyor_twidget.setItem(row, SURVEYOR_SURNAME, item)
        item = QTableWidgetItem(u'{0}'.format(surveyor_first_name))
        self.surveyor_twidget.setItem(row, SURVEYOR_FIRST_NAME, item)
        item = QTableWidgetItem(u'{0}'.format(surveyor_phone))
        self.surveyor_twidget.setItem(row, SURVEYOR_PHONE, item)

    def __add_company_row(self, row, company_id, company_name, company_address):

        item = QTableWidgetItem(u'{0}'.format(company_name))
        item.setData(Qt.UserRole, company_id)
        self.company_twidget.setItem(row, COMPANY_NAME, item)
        item = QTableWidgetItem(u'{0}'.format(company_address))
        self.company_twidget.setItem(row, COMPANY_ADDRESS, item)

    @pyqtSlot()
    def on_delete_company_button_clicked(self):

        row = self.company_twidget.currentRow()
        if row == -1:
            return
        if QMessageBox.No == QMessageBox.question(None, self.tr("Delete Company"), self.tr('Deleting a company will also delete the relating surveyors. Continue?'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No):
            return

        company_id = self.company_twidget.item(row, 0).data(Qt.UserRole)
        if company_id != -1:  # already has a row in the database
            session = SessionHandler().session_instance()
            soum_code = DatabaseUtils.working_l2_code()
            schema_string = 's' + soum_code
            session.execute(
                "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)
            company = self.session.query(SetSurveyCompany).filter(SetSurveyCompany.id == company_id).one()
            session.delete(company)

        self.company_twidget.removeRow(row)

    def __save_companies(self):

        try:
            session = SessionHandler().session_instance()
            for row in range(self.company_twidget.rowCount()):
                new_row = False
                company_id = self.company_twidget.item(row, COMPANY_NAME).data(Qt.UserRole)
                if company_id == -1:
                    new_row = True
                    company = SetSurveyCompany()
                else:
                    company = self.session.query(SetSurveyCompany).filter(SetSurveyCompany.id == company_id).one()

                company.name = self.company_twidget.item(row, COMPANY_NAME).text()
                company.address = self.company_twidget.item(row, COMPANY_ADDRESS).text()

                if new_row:
                    session.add(company)

            self.__read_companies()

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
            raise

    @pyqtSlot()
    def on_find_company_button_clicked(self):

        search_text = self.company_ledit.text().strip()
        if search_text is None or len(search_text) == 0:
            return

        items = self.company_twidget.findItems(search_text, Qt.MatchContains)

        for item in items:
            row = self.company_twidget.row(item)
            if search_text != self.company_search_str:
                self.company_twidget.setCurrentCell(row, 0)
                self.company_search_str = search_text
                break
            if row > self.company_twidget.currentRow():
                self.company_twidget.setCurrentCell(row, 0)
                break

    @pyqtSlot(QTableWidgetItem, QTableWidgetItem)
    def on_company_twidget_currentItemChanged(self, current_item, previous_item):

        if previous_item is not None:
            # print 'P:{0}'.format(previous_item.column())
            prev_company_id = self.company_twidget.item(previous_item.row(), 0).data(Qt.UserRole)
            self.__save_surveyors(prev_company_id)

        if current_item is not None:
            # print 'C:{0}'.format(current_item.column())
            prev_company_id = self.company_twidget.item(current_item.row(), 0).data(Qt.UserRole)
            self.__read_surveyors(prev_company_id)

    @pyqtSlot()
    def on_delete_surveyor_button_clicked(self):

        row = self.surveyor_twidget.currentRow()
        if row == -1:
            return

        surveyor_id = self.surveyor_twidget.item(row, 0).data(Qt.UserRole)
        if surveyor_id != -1:  # already has a row in the database
            session = SessionHandler().session_instance()
            surveyor = self.session.query(SetSurveyor).filter(SetSurveyor.id == surveyor_id).one()
            session.delete(surveyor)

        self.surveyor_twidget.removeRow(row)

    def __save_surveyors(self, company_id=None):

        if company_id == -1 or self.company_twidget.rowCount() == 0:
            return

        try:
            session = SessionHandler().session_instance()
            if company_id is None:
                company_id = self.company_twidget.item(self.company_twidget.currentRow(), 0).data(Qt.UserRole)
            # In case this method was called because a company has been deleted:
            count = self.session.query(SetSurveyCompany).filter(SetSurveyCompany.id == company_id).count()
            if count == 0:
                return
            company = self.session.query(SetSurveyCompany).filter(SetSurveyCompany.id == company_id).one()

            for row in range(self.surveyor_twidget.rowCount()):
                new_row = False
                surveyor_id = self.surveyor_twidget.item(row, SURVEYOR_SURNAME).data(Qt.UserRole)
                if surveyor_id == -1:
                    new_row = True
                    surveyor = SetSurveyor()
                else:
                    surveyor = self.session.query(SetSurveyor).filter(SetSurveyor.id == surveyor_id).one()

                surveyor.surname = self.surveyor_twidget.item(row, SURVEYOR_SURNAME).text()
                surveyor.first_name = self.surveyor_twidget.item(row, SURVEYOR_FIRST_NAME).text()
                surveyor.phone = self.surveyor_twidget.item(row, SURVEYOR_PHONE).text()

                if new_row:
                    company.surveyors.append(surveyor)

            self.__read_surveyors(company_id)

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
            raise

    @pyqtSlot()
    def on_add_document_button_clicked(self):

        row = self.doc_twidget.rowCount()
        self.doc_twidget.insertRow(row)
        item_visible = QTableWidgetItem()
        item_visible.setCheckState(Qt.Checked)

        item_name = QTableWidgetItem()
        item_name.setText("000001")
        item_name.setData(Qt.UserRole, -1)

        item_open = QTableWidgetItem()
        item_open.setData(Qt.UserRole, -1)

        item_description = QTableWidgetItem()
        item_description.setText("Undefined")
        self.doc_twidget.setItem(row, DOC_VISIBLE_COLUMN, item_visible)
        self.doc_twidget.setItem(row, DOC_NAME_COLUMN, item_name)
        self.doc_twidget.setItem(row, DOC_DESCRIPTION_COLUMN, item_description)
        self.doc_twidget.setItem(row, DOC_OPEN_FILE_COLUMN, item_open)

    @pyqtSlot()
    def on_load_off_document_button_clicked(self):

        self.__remove_off_document_items()
        self.__load_documents()
        self.add_document_button.setEnabled(True)
        self.remove_document_button.setEnabled(True)

    @pyqtSlot()
    def on_remove_document_button_clicked(self):

        archive_legaldocuments_path = FilePath.legaldocuments_file_path()
        if not os.path.exists(archive_legaldocuments_path):
            os.makedirs(archive_legaldocuments_path)

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to delete the selected document?"))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if message_box.clickedButton() == delete_button:
            try:
                row = self.doc_twidget.currentRow()
                item = self.doc_twidget.item(row, DOC_NAME_COLUMN)
                dec_document_name = item.text()
                os.remove(archive_legaldocuments_path+'/'+dec_document_name)

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            self.doc_twidget.removeRow(row)

    @pyqtSlot(int)
    def on_is_find_date_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.zone_begin_date.setEnabled(True)
            self.zone_end_date.setEnabled(True)
            self.zone_find_button.setEnabled(True)
        else:
            self.zone_begin_date.setEnabled(False)
            self.zone_end_date.setEnabled(False)
            self.zone_find_button.setEnabled(False)

    @pyqtSlot(int)
    def on_begin_date_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.change_begin_date.setEnabled(True)
        else:
            self.change_begin_date.setEnabled(False)

    @pyqtSlot(int)
    def on_end_date_checkbox_stateChanged(self, state):

        session = SessionHandler().session_instance()
        zone = self.session.query(SetFeeZone).filter(SetFeeZone.zone_id == self.zone_fid).one()

        if state == Qt.Checked:
            if zone.valid_till == None:
                self.change_end_date.setDate(QDate().currentDate())
            elif int(zone.valid_till.year) == 9999:
                self.change_end_date.setDate(QDate().currentDate())
            else:
                self.cancel_end_date_checkbox.setDisabled(False)
            self.change_end_date.setEnabled(True)
        else:
            self.change_end_date.setEnabled(False)
            self.change_end_date.setDate(zone.valid_till)
            self.cancel_end_date_checkbox.setDisabled(True)

    @pyqtSlot(int)
    def on_cancel_end_date_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.change_end_date.setReadOnly(True)
            self.end_date_checkbox.setEnabled(False)
            self.end_date_checkbox.setCheckable(False)
            end_date = ('9999-01-01')
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            self.change_end_date.setDate(end_date)
        else:
            self.change_end_date.setReadOnly(False)
            self.end_date_checkbox.setEnabled(True)
            self.end_date_checkbox.setCheckable(True)

    @pyqtSlot()
    def on_change_date_button_clicked(self):

        session = SessionHandler().session_instance()
        zone = self.session.query(SetFeeZone).filter(SetFeeZone.zone_id == self.zone_fid).one()
        if self.begin_date_checkbox.isChecked():
            valid_from = PluginUtils.convert_qt_date_to_python(self.change_begin_date.date())
            zone.valid_from = valid_from
        if self.end_date_checkbox.isChecked():
            valid_till = PluginUtils.convert_qt_date_to_python(self.change_end_date.date())
            zone.valid_till = valid_till
        elif self.cancel_end_date_checkbox.isChecked():
            zone.valid_till = None
        session.flush()

    @pyqtSlot()
    def on_zone_find_button_clicked(self):

        self.zones_lwidget.clear()
        self.from_zone_cbox.clear()
        self.to_zone_cbox.clear()
        session = SessionHandler().session_instance()
        location = self.zone_location_cbox.currentText()

        # if idx == -1:
        #     return
        zone_begin_date = self.zone_begin_date.itemData(self.zone_begin_date.currentIndex(), Qt.UserRole)
        zone_end_date = self.zone_end_date.itemData(self.zone_end_date.currentIndex(), Qt.UserRole)
        if zone_end_date == -1:
            zones = self.session.query(SetFeeZone.zone_id, SetFeeZone.zone_no). \
                filter(SetFeeZone.location == location). \
                filter(SetFeeZone.valid_from >= zone_begin_date).order_by(SetFeeZone.zone_no)
        else:
            zones = self.session.query(SetFeeZone.zone_id, SetFeeZone.zone_no). \
                filter(SetFeeZone.location == location). \
                filter(SetFeeZone.valid_from == zone_begin_date). \
                filter(SetFeeZone.valid_till == zone_end_date).order_by(SetFeeZone.zone_no)

        for zone_id, zone_no in zones:
            item = QListWidgetItem('{0}'.format(zone_no), self.zones_lwidget)
            item.setData(Qt.UserRole, zone_id)
            self.from_zone_cbox.addItem(str(zone_no), zone_id)
            self.to_zone_cbox.addItem(str(zone_no), zone_id)

        if self.zones_lwidget.count() > 0:
            self.zones_lwidget.setCurrentRow(0)
        if self.to_zone_cbox.count() > 1:
            self.to_zone_cbox.setCurrentIndex(1)

        if self.zones_lwidget.currentRow() == -1:
            PluginUtils.show_message(self, self.tr("No Zone"), self.tr("This date found in zone"))
            return
        zone_fid = self.zones_lwidget.item(self.zones_lwidget.currentRow()).data(Qt.UserRole)
        zone = self.session.query(SetFeeZone).filter(SetFeeZone.zone_id == zone_fid).one()

        zone_no = zone.zone_no
        self.landuse_code_list = list()
        del self.landuse_code_list[:]

        if zone_no == 50 or zone_no == 60 or zone_no == 70 or zone_no == 80:
            for code, description in self.session.query(ClLanduseType.code, ClLanduseType.description). \
                    filter(ClLanduseType.code2.in_([11, 12, 13, 14, 15])).all():
                self.landuse_code_list.append(u'{0}: {1}'.format(code, description))
            delegate = LandUseComboBoxDelegate(FEE_LAND_USE, self.landuse_code_list, self.land_fee_twidget)
            self.land_fee_twidget.setItemDelegateForColumn(FEE_LAND_USE, delegate)
        else:
            for code, description in self.session.query(ClLanduseType.code, ClLanduseType.description). \
                    filter(ClLanduseType.code2 != 11, ClLanduseType.code2 != 12, ClLanduseType.code2 != 13 \
                    , ClLanduseType.code2 != 14, ClLanduseType.code2 != 15).all():
                self.landuse_code_list.append(u'{0}: {1}'.format(code, description))
            delegate = LandUseComboBoxDelegate(FEE_LAND_USE, self.landuse_code_list, self.land_fee_twidget)
            self.land_fee_twidget.setItemDelegateForColumn(FEE_LAND_USE, delegate)

    @pyqtSlot()
    def on_doc_add_button_clicked(self):

        self.change_begin_date.setDisplayFormat("yyyy-MM-dd")
        zone_begin_date = self.change_begin_date.text()

        archive_feetaxzone_path = FilePath.feetaxzone_file_path()
        if not os.path.exists(archive_feetaxzone_path):
            os.makedirs(archive_feetaxzone_path)
        file_dialog = QFileDialog()
        file_dialog.setModal(True)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setFilter(self.tr("Land Fee (*.pdf)"))

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            file_path = QFileInfo(selected_file).filePath()
            file_name = QFileInfo(file_path).fileName()
            num = []
            working_soum = DatabaseUtils.working_l2_code()
            if self.document_twidget.count() == 0:
                file_name = working_soum +'-'+ zone_begin_date +'-fee-'+ '01.pdf'
                num.append(int(file_name[-6]+file_name[-5]))
            else:
                for i in range(self.document_twidget.count()):
                    doc_name_item = self.document_twidget.item(i)
                    doc_name_no = doc_name_item.text()
                    num.append(int(doc_name_no[-6]+doc_name_no[-5]))

                max_num = max(num)
                max_num = str(max_num+1)
                if len((max_num)) == 1:
                    max_num = '0'+(max_num)
                file_name = working_soum +'-'+ zone_begin_date +'-fee-'+ max_num +'.pdf'

            item = QListWidgetItem(file_name, self.document_twidget)
            item.setData(Qt.UserRole, file_name)

            shutil.copy2(selected_file, archive_feetaxzone_path+'/'+file_name)

    def __remove_off_document_items(self):

        if not self.doc_twidget:
            return

        while self.doc_twidget.rowCount() > 0:
            self.doc_twidget.clear()

    def __remove_eq_document_items(self):

        if not self.equipment_doc_twidget:
            return

        while self.equipment_doc_twidget.count() > 0:
            self.equipment_doc_twidget.clear()

    def __remove_document_items(self):

        if not self.document_twidget:
            return

        while self.document_twidget.count() > 0:
            self.document_twidget.clear()

    def __update_eq_documents_file_twidget(self):

        archive_equipment_path = FilePath.equipment_file_path()
        if not os.path.exists(archive_equipment_path):
            os.makedirs(archive_equipment_path)

        for file in os.listdir(archive_equipment_path):
            os.listdir(archive_equipment_path)
            if file.endswith(".pdf"):
                file_name = file
                file_name1 = file.find('eq')
                if file_name1 != -1:
                    item = QListWidgetItem(file_name, self.equipment_doc_twidget)
                    item.setData(Qt.UserRole, file_name)

    def __update_user_documents_file_twidget(self, username):

        archive_equipment_path = FilePath.equipment_file_path()
        if not os.path.exists(archive_equipment_path):
            os.makedirs(archive_equipment_path)

        for file in os.listdir(archive_equipment_path):
            os.listdir(archive_equipment_path)
            if file.endswith(".pdf"):
                file_name = file
                file_name1 = file.find(username)
                if file_name1 != -1:
                    item = QListWidgetItem(file_name, self.equipment_doc_twidget)
                    item.setData(Qt.UserRole, file_name)

    def __update_documents_file_twidget(self):

        working_soum = DatabaseUtils.working_l2_code()
        archive_feetaxzone_path = FilePath.feetaxzone_file_path()
        for file in os.listdir(archive_feetaxzone_path):
            os.listdir(archive_feetaxzone_path)
            if file.endswith(".pdf"):
                fee_soum = file[:5]
                file_name = file
                file_name1 = file.find('fee')
                if working_soum == fee_soum and file_name1 != -1:
                    item = QListWidgetItem(file_name, self.document_twidget)
                    item.setData(Qt.UserRole, file_name)

    @pyqtSlot()
    def on_load_document_button_clicked(self):

        self.__remove_document_items()
        self.__update_documents_file_twidget()
        self.doc_add_button.setEnabled(True)
        self.doc_delete_button.setEnabled(True)
        self.doc_view_button.setEnabled(True)

    @pyqtSlot()
    def on_doc_view_button_clicked(self):

        archive_feetaxzone_path = FilePath.feetaxzone_file_path()

        current_row = self.document_twidget.currentRow()
        if current_row == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Select Item."))
            return
        byte_array_item = self.document_twidget.selectedItems()[0]
        file_name = byte_array_item.text()

        shutil.copy2(archive_feetaxzone_path + '/'+file_name, FilePath.view_file_path())
        QDesktopServices.openUrl(QUrl.fromLocalFile(FilePath.view_file_path()))


    @pyqtSlot()
    def on_doc_delete_button_clicked(self):

        archive_feetaxzone_path = FilePath.feetaxzone_file_path()

        current_row = self.document_twidget.currentRow()
        if current_row == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Select Item."))
            return

        item = self.document_twidget.selectedItems()[0]
        item_index = self.document_twidget.selectedIndexes()[0]

        try:
            dec_document_name = item.text()
            self.document_twidget.takeItem(item_index.row())
            os.remove(archive_feetaxzone_path+'/'+dec_document_name)
        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    @pyqtSlot()
    def on_layer_view_button_clicked(self):

        soum_with_equipments = {}

        root = QgsProject.instance().layerTreeRoot()

        LayerUtils.refresh_layer()

        all_rows = self.equipment_twidget.rowCount()
        for row in xrange(0,all_rows):
            id_item = self.equipment_twidget.item(row, 0)
            id = id_item.data(Qt.UserRole)
            equipment = self.session.query(SetEquipment).filter(SetEquipment.id == id).one()
            soum = equipment.soum
            soum_with_equipments[soum] = []
            soum_with_equipments[soum].append(id)

            #####
            tmp_parcel_layer = LayerUtils.layer_by_data_source("settings", "view_equipment")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Мэдээний хяналт")
                vlayer = LayerUtils.load_layer_by_name_equipment("view_equipment", "id")
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_equipment.qml")
                vlayer.setLayerName(self.tr("Equipment Layer"))

                mygroup.addLayer(vlayer)
            ######
        self.__zoom_to_equipment_several_soums(soum_with_equipments)

    def __zoom_to_equipment_several_soums(self, soums):

        feature_ids = []
        LayerUtils.deselect_all()
        is_layer = False
        for soum, parcel_array in soums.iteritems():
            layer = LayerUtils.layer_by_data_source("settings", "view_equipment")

            if layer is None:
                layer = LayerUtils.load_layer_by_name_equipment("view_equipment", "id")

            exp_string = ""

            for id in parcel_array:
                if exp_string == "":
                    exp_string = "id = \'" + str(id) + "\'"
                else:
                    exp_string += " or id = \'" + str(id) + "\'"

            request = QgsFeatureRequest()
            request.setFilterExpression(exp_string)

            feature_ids.append(parcel_array[0])
            is_layer = True
        if is_layer:
            layer.setSelectedFeatures(feature_ids)

            canvas = qgis.utils.iface.mapCanvas()
            canvas.zoomToSelected(layer)

    def __create_equipment_view(self):

            user_name = QSettings().value(SettingsConstants.USER)
            self.userSettings = DatabaseUtils.role_settings(user_name)
            au_level2_string = self.userSettings.restriction_au_level2
            au_level2_list = au_level2_string.split(",")
            sql = ""

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql:
                    sql = "CREATE OR REPLACE temp view equipment_search as" + "\n"
                else:
                    sql = sql + "UNION" + "\n"

                select = "SELECT * " \
                     "FROM settings.set_equipment e " \
                     "LEFT JOIN admin_units.au_level2 au2 on e.soum = au2.code " + "\n"

                sql = sql + select

            sql = "{0} order by id;".format(sql)

            try:
                self.session.execute(sql)
                self.commit()
            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
                return

    @pyqtSlot()
    def on_print_button_clicked(self):

        restrictions = DatabaseUtils.working_l2_code()
        default_path = r'D:/TM_LM2/reports'
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

        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"-"+"equipment_list.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 8)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 30)
        worksheet.set_column('H:H', 15)
        worksheet.set_column('I:I', 15)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 15)

        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.2,right=0.1)

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(14)
        format_header.set_bold()

        format_title = workbook.add_format()
        format_title.set_text_wrap()
        format_title.set_align('center')
        format_title.set_align('vcenter')
        # format1.set_rotation(90)
        format_title.set_font_name('Times New Roman')
        format_title.set_font_size(10)
        format_title.set_border(1)
        format_title.set_bold()

        format1 = workbook.add_format()
        format1.set_text_wrap()
        format1.set_align('center')
        format1.set_align('vcenter')
        # format1.set_rotation(90)
        format1.set_font_name('Times New Roman')
        format1.set_font_size(10)
        format1.set_border(1)

        worksheet.merge_range('A2:K2', u' Тоног төхөөрөмжийн бүртгэлийн жагсаалт',format_header)

        worksheet.write('A4',u"Дугаар", format_title)
        worksheet.write('B4',u"Төхөөрөмжийн нэр", format_title)
        worksheet.write('C4',u"Хэрэглэгчийн нэр", format_title)
        worksheet.write('D4',u"Худалдаж авсан огноо", format_title)
        worksheet.write('E4',u"Хүлээлгэж өгсөн огноо", format_title)
        worksheet.write('F4',u"Баталгаат хугацаа дуусах огноо", format_title)
        worksheet.write('G4',u"Үзүүлэлт", format_title)
        worksheet.write('H4',u"МАК Хаяг", format_title)
        worksheet.write('I4',u"Нийлүүлэгч", format_title)
        worksheet.write('J4',u"Аймаг", format_title)
        worksheet.write('K4',u"Сум", format_title)

        row_count = 4
        col = 0

        all_rows = self.equipment_twidget.rowCount()
        for row in xrange(0,all_rows):
            id_item = self.equipment_twidget.item(row, 0)
            id = id_item.data(Qt.UserRole)
            equipment = self.session.query(SetEquipment).filter(SetEquipment.id == id).one()

            equipment_item = self.equipment_twidget.item(row, 1)
            equipment_name = equipment_item.text()

            user_item = self.equipment_twidget.item(row, 2)
            user_name = user_item.text()

            purchase_date_item = self.equipment_twidget.item(row, 3)
            purchase_date = purchase_date_item.text()

            given_date_item = self.equipment_twidget.item(row, 4)
            given_date = given_date_item.text()

            duration_date_item = self.equipment_twidget.item(row, 5)
            duration_date = duration_date_item.text()

            description_item = self.equipment_twidget.item(row, 6)
            description = description_item.text()

            mac_item = self.equipment_twidget.item(row, 7)
            mac = mac_item.text()

            seller_item = self.equipment_twidget.item(row, 8)
            seller = seller_item.text()

            aimag_item = self.equipment_twidget.item(row, 9)
            aimag = aimag_item.text()

            soum_item = self.equipment_twidget.item(row, 10)
            soum = soum_item.text()

            worksheet.write(row_count, col,  id, format1)
            worksheet.write(row_count, col+1,equipment_name, format1)
            worksheet.write(row_count, col+2,user_name, format1)
            worksheet.write(row_count, col+3,purchase_date, format1)
            worksheet.write(row_count, col+4,given_date, format1)
            worksheet.write(row_count, col+5,duration_date, format1)
            worksheet.write(row_count, col+6,description, format1)
            worksheet.write(row_count, col+7,mac, format1)
            worksheet.write(row_count, col+8,seller, format1)
            worksheet.write(row_count, col+9,aimag, format1)
            worksheet.write(row_count, col+10,soum, format1)
            row_count += 1

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"-"+"equipment_list.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def covert_unc(self, host, path):

        return ''.join(['\\\\', host, '\\', path.replace(':', '$')])

    def wnet_connect(self, host, username, password):

        if self.is_user_checkbox.isChecked():
            dest_dir = '\\archive'
        else:
            dest_dir = '\\documents'

        unc = ''.join(['\\\\', host])
        try:
            win32wnet.WNetAddConnection2(win32netcon.RESOURCETYPE_DISK, '',unc+dest_dir, None, username,password, 0)
            PluginUtils.show_message(self, self.tr("success"), self.tr("Successfully"))
        except Exception, err:
            if isinstance(err, win32wnet.error):

                if err[0] == 1219:
                    win32wnet.WNetCancelConnection2(unc+dest_dir, 0, 0)
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("Not connect. Password incorrect"))

    def netcopy(self, host, source, dest_dir, username=None, password=None, move=False):

        self.wnet_connect(host, username, password)

        dest_dir = self.covert_unc(host, dest_dir)

        filename = 'test.pdf'
        shutil.copy2(source, dest_dir+'/'+filename)

    @pyqtSlot(int)
    def on_doc_path_checkbox_stateChanged(self, state):

        host = QSettings().value(SettingsConstants.HOST)

        # source = 'D:\TM_LM2\pdf_archive/view.pdf'

        # self.netcopy(host, source, dest_dir, username, password)

        default_path = r'D:/TM_LM2/archive'

        if host == 'localhost':
            self.doc_path_checkbox.setChecked(False)
            PluginUtils.show_message(self, self.tr("Local"), self.tr("This local user!!!"))
            self.__check_local_dir()
            return

        if state == Qt.Checked:
            self.is_user_checkbox.setEnabled(True)
            self.host_connect_button.setEnabled(True)
            self.doc_path_edit.clear()
        else:
            self.__check_local_dir()
            self.doc_path_edit.setEnabled(True)
            self.doc_path_edit.setText(default_path)
            self.is_user_checkbox.setEnabled(False)
            self.host_connect_button.setEnabled(False)

    @pyqtSlot(int)
    def on_is_user_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.host_pass_edit.setEnabled(True)
            self.host_user_edit.setEnabled(True)
        else:
            self.host_pass_edit.setEnabled(False)
            self.host_user_edit.setEnabled(False)

    def __check_local_dir(self):

        working_aimag = DatabaseUtils.working_l1_code()
        working_soum = DatabaseUtils.working_l2_code()
        aimag_path = r'D:/TM_LM2/archive/'+working_aimag
        soum_path = r'D:/TM_LM2/archive/'+working_aimag +'/'+ working_soum
        parent_path = r'D:/TM_LM2'
        archive_path = r'D:/TM_LM2/archive'
        archive_app_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/application'
        archive_cert_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/certificate'
        archive_contract_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/contract'
        archive_decision_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/decision'
        archive_equipment_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/equipment'
        archive_feetaxzone_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/feetaxzone'
        archive_legaldocuments_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/legaldocuments'
        archive_ownership_path = r'D:/TM_LM2/archive/'+working_aimag+'/'+working_soum+'/ownership'
        if not os.path.exists(parent_path):
            os.makedirs('D:/TM_LM2')
            os.makedirs('D:/TM_LM2/application_respone')
            os.makedirs('D:/TM_LM2/application_list')
            os.makedirs('D:/TM_LM2/approved_decision')
            os.makedirs('D:/TM_LM2/cad_maintenance')
            os.makedirs('D:/TM_LM2/cad_maps')
            os.makedirs('D:/TM_LM2/contracts')
            os.makedirs('D:/TM_LM2/decision_draft')
            os.makedirs('D:/TM_LM2/dumps')
            os.makedirs('D:/TM_LM2/q_data')
            os.makedirs('D:/TM_LM2/archive')
            os.makedirs('D:/TM_LM2/refused_decision')
            os.makedirs('D:/TM_LM2/reports')
            os.makedirs('D:/TM_LM2/training')
        if not os.path.exists(archive_path):
            os.makedirs('D:/TM_LM2/archive')
            os.makedirs(aimag_path)
            os.makedirs(soum_path)
        if not os.path.exists(aimag_path):
            os.makedirs(aimag_path)
            os.makedirs(soum_path)
        if not os.path.exists(soum_path):
            os.makedirs(soum_path)
        if not os.path.exists(archive_app_path):
            os.makedirs(archive_app_path)
        if not os.path.exists(archive_cert_path):
            os.makedirs(archive_cert_path)
        if not os.path.exists(archive_contract_path):
            os.makedirs(archive_contract_path)
        if not os.path.exists(archive_decision_path):
            os.makedirs(archive_decision_path)
        if not os.path.exists(archive_equipment_path):
            os.makedirs(archive_equipment_path)
        if not os.path.exists(archive_feetaxzone_path):
            os.makedirs(archive_feetaxzone_path)
        if not os.path.exists(archive_legaldocuments_path):
            os.makedirs(archive_legaldocuments_path)
        if not os.path.exists(archive_ownership_path):
            os.makedirs(archive_ownership_path)

    @pyqtSlot()
    def on_host_connect_button_clicked(self):

        source = 'D:\TM_LM2/archive/view.pdf'
        host = QSettings().value(SettingsConstants.HOST)
        if self.is_user_checkbox.isChecked():
            username = self.host_user_edit.text()
            password = self.host_pass_edit.text()
            dest_dir = 'archive'
        else:
            username = 'user'+ QSettings().value(SettingsConstants.DATABASE_NAME)[-4:]
            password = 'user'+ QSettings().value(SettingsConstants.DATABASE_NAME)[-4:]
            dest_dir = 'documents'

        self.doc_path_edit.setEnabled(False)
        self.doc_path_edit.setText(host+'/'+dest_dir)

        self.netcopy(host, source, dest_dir, username, password)

    @pyqtSlot()
    def on_ref_webgis_button_clicked(self):

        QSettings().setValue(SettingsConstants.WEBGIS_IP, self.webgis_ip_edit.text())

    @pyqtSlot()
    def on_help_button_clicked(self):

        if self.tabWidget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/report_parameters.htm")
        elif self.tabWidget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/land_fee_base_values.htm")
        elif self.tabWidget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/land_tax_values.htm")
        elif self.tabWidget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/certificates.htm")
        elif self.tabWidget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/official_documents.htm")
        elif self.tabWidget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/payments.htm")
        elif self.tabWidget.currentIndex() == 6:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/codelists.htm")
        elif self.tabWidget.currentIndex() == 7:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/survey_company.htm")
        elif self.tabWidget.currentIndex() == 8:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/miscellaneous.htm")
        elif self.tabWidget.currentIndex() == 9:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/equipment_List.htm")
        elif self.tabWidget.currentIndex() == 10:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/certificate_registeration.htm")


#training registeration
    @pyqtSlot()
    def on_training_add_button_clicked(self):

        row = self.training_twidget.rowCount()
        self.training_twidget.insertRow(row)
        now_date = QDate.currentDate().toString("yyyy-MM-dd")
        self.__add_training_row(row, -1,self.tr('Enter location name!'), now_date, now_date, self.tr('Enter training information!'))

    @pyqtSlot()
    def on_training_delete_button_clicked(self):

        row = self.training_twidget.currentRow()
        if row == -1:
            return

        id = self.training_twidget.item(row, 0).data(Qt.UserRole)
        if id != -1:  # already has a row in the database
            fee = self.session.query(SetTraining).filter(SetTraining.id == id).one()
            self.session.delete(fee)

        self.training_twidget.removeRow(row)

    def __add_training_row(self, row, id, location_name, begin_date, end_date, description):

        item = QTableWidgetItem(u'{0}'.format(row))
        item.setData(Qt.UserRole, id)
        item.setCheckState(Qt.Unchecked)
        self.training_twidget.setItem(row, 0, item)

        item = QTableWidgetItem('{0}'.format(location_name))
        self.training_twidget.setItem(row, 1, item)

        item = QTableWidgetItem('{0}'.format(begin_date))
        self.training_twidget.setItem(row, 2, item)

        item = QTableWidgetItem('{0}'.format(end_date))
        self.training_twidget.setItem(row, 3, item)

        item = QTableWidgetItem('{0}'.format(description))
        self.training_twidget.setItem(row, 4, item)


    def __setup_certificate_person(self):

        try:
            cl_level = self.session.query(ClTrainingLevel).all()
        except SQLAlchemyError, e:
            QMessageBox.information(self, QApplication.translate("LM2", "Sql Error"), e.message)

        for level in cl_level:
            self.level_cbox.addItem(level.description, level.code)

        self.begin_date.setDate(QDate.currentDate())
        self.begin_date.setDisplayFormat('yyyy-MM-dd')

        self.end_date.setDate(QDate.currentDate())
        self.end_date.setDisplayFormat('yyyy-MM-dd')

        self.training_twidget.sortItems(0, Qt.AscendingOrder)
        self.training_twidget.resizeColumnToContents(0)
        self.training_twidget.resizeColumnToContents(1)
        self.training_twidget.resizeColumnToContents(2)
        self.training_twidget.resizeColumnToContents(3)
        self.training_twidget.resizeColumnToContents(4)

        self.training_twidget.setColumnWidth(1, 200)
        self.training_twidget.setColumnWidth(2, 100)
        self.training_twidget.setColumnWidth(3, 100)
        # self.training_twidget.horizontalHeader().setResizeMode(3, QHeaderView.Stretch)

        self.training_twidget.setAlternatingRowColors(True)
        self.training_twidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.training_twidget.setSelectionMode(QTableWidget.SingleSelection)

        self.set_role_twidget.sortItems(0, Qt.AscendingOrder)
        self.set_role_twidget.resizeColumnToContents(0)
        self.set_role_twidget.resizeColumnToContents(1)
        self.set_role_twidget.resizeColumnToContents(2)
        self.set_role_twidget.resizeColumnToContents(3)

        self.set_role_twidget.setColumnWidth(1, 100)
        self.set_role_twidget.setColumnWidth(2, 100)
        self.set_role_twidget.setColumnWidth(3, 100)

        self.set_role_twidget.setAlternatingRowColors(True)
        self.set_role_twidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.set_role_twidget.setSelectionMode(QTableWidget.SingleSelection)
        self.set_role_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.person_twidget.sortItems(0, Qt.AscendingOrder)
        self.person_twidget.resizeColumnToContents(0)
        self.person_twidget.resizeColumnToContents(1)
        self.person_twidget.resizeColumnToContents(2)
        self.person_twidget.resizeColumnToContents(3)

        self.person_twidget.setColumnWidth(1, 100)
        self.person_twidget.setColumnWidth(2, 100)
        self.person_twidget.setColumnWidth(3, 100)

        self.person_twidget.setAlternatingRowColors(True)
        self.person_twidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.person_twidget.setSelectionMode(QTableWidget.SingleSelection)
        self.person_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.certificate_twidget.sortItems(0, Qt.AscendingOrder)
        self.certificate_twidget.resizeColumnToContents(0)
        self.certificate_twidget.resizeColumnToContents(1)
        self.certificate_twidget.resizeColumnToContents(2)
        self.certificate_twidget.resizeColumnToContents(3)

        self.certificate_twidget.setColumnWidth(1, 100)
        self.certificate_twidget.setColumnWidth(2, 100)
        self.certificate_twidget.setColumnWidth(3, 100)

        self.certificate_twidget.setAlternatingRowColors(True)
        self.certificate_twidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.certificate_twidget.setSelectionMode(QTableWidget.SingleSelection)
        self.certificate_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        delegate = DateDelegate(self.training_twidget)
        self.training_twidget.setItemDelegateForColumn(2, delegate)

        delegate = DateDelegate(self.training_twidget)
        self.training_twidget.setItemDelegateForColumn(3, delegate)

        delegate = LineEditDelegate(1,'',self.training_twidget)
        self.training_twidget.setItemDelegateForColumn(1, delegate)

        delegate = LineEditDelegate(4,'',self.training_twidget)
        self.training_twidget.setItemDelegateForColumn(4, delegate)

        delegate = CertificateDocumentDelegate(self.certificate_twidget, self)
        self.certificate_twidget.setItemDelegate(delegate)

        self.__read_training()
        self.__read_roles()
        self.__read_person()

    def __read_training(self):

        self.training_twidget.clearContents()
        self.training_twidget.setRowCount(0)
        row = 0
        training_count = self.session.query(SetTraining).count()
        if training_count > 0:
            self.training_twidget.setRowCount(training_count)
            trainings = self.session.query(SetTraining).all()
            for training in trainings:
                item = QTableWidgetItem(str(training.id))
                item.setData(Qt.UserRole, training.id)
                item.setCheckState(Qt.Unchecked)
                self.training_twidget.setItem(row, 0, item)

                item = QTableWidgetItem(training.location)
                self.training_twidget.setItem(row, 1, item)

                item = QTableWidgetItem(str(training.begin_date))
                self.training_twidget.setItem(row, 2, item)

                item = QTableWidgetItem(str(training.end_date))
                self.training_twidget.setItem(row, 3, item)

                item = QTableWidgetItem(training.description)
                self.training_twidget.setItem(row, 4, item)

                row += 1

    def __read_roles(self):

        self.set_role_twidget.clearContents()
        self.set_role_twidget.setRowCount(0)
        row = 0
        roles = self.session.query(SetRole).all()
        for role in roles:
            self.set_role_twidget.insertRow(row)

            item = QTableWidgetItem(str(row))
            self.set_role_twidget.setItem(row, 0, item)

            item = QTableWidgetItem(role.user_register)
            self.set_role_twidget.setItem(row, 1, item)

            item = QTableWidgetItem(role.surname)
            self.set_role_twidget.setItem(row, 2, item)

            item = QTableWidgetItem(role.first_name)
            self.set_role_twidget.setItem(row, 3, item)

            item = QTableWidgetItem(role.user_name_real)
            self.set_role_twidget.setItem(row, 4, item)

            aimag_name = ''
            soum_name = ''
            if role.working_au_level1:
                aimag_name = role.working_au_level1_ref.name
            if role.working_au_level2:
                soum_name = role.working_au_level2_ref.name
            item = QTableWidgetItem(aimag_name+'/'+soum_name)
            self.set_role_twidget.setItem(row, 5, item)

            item = QTableWidgetItem(role.is_active)
            self.set_role_twidget.setItem(row, 6, item)

            row += 1

    def __save_training(self):

        try:
            for row in range(self.training_twidget.rowCount()):
                new_row = False
                training_id = self.training_twidget.item(row, 0).data(Qt.UserRole)
                if training_id == -1:
                    new_row = True
                    training = SetTraining()
                else:
                    training = self.session.query(SetTraining).filter(SetTraining.id == training_id).one()

                training.location = self.training_twidget.item(row,1).text()
                str_date = self.training_twidget.item(row,2).text()
                if len(str_date) == 10:
                    begin_date = datetime.strptime(str_date, "%Y-%m-%d")
                else:
                    begin_date = datetime.strptime(str_date[:10], "%Y-%m-%d")
                training.begin_date = begin_date
                str_date = self.training_twidget.item(row,3).text()
                if len(str_date) == 10:
                    end_date = datetime.strptime(str_date, "%Y-%m-%d")
                else:
                    end_date = datetime.strptime(str_date[:10], "%Y-%m-%d")
                training.end_date = end_date
                training.description = self.training_twidget.item(row,4).text()
                if new_row:
                    self.session.add(training)
            self.__read_training()
        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
            raise

    @pyqtSlot(QTableWidgetItem)
    def on_training_twidget_itemClicked(self, item):

        cur_row = self.training_twidget.currentRow()
        item = self.training_twidget.item(cur_row, 0)
        item.setCheckState(Qt.Checked)

        for row in range(self.training_twidget.rowCount()):
            item_dec = self.training_twidget.item(row, 0)
            item_dec.setCheckState(Qt.Unchecked)
        item.setCheckState(Qt.Checked)

        self.__read_training_person(item.data(Qt.UserRole))

    @pyqtSlot(QTableWidgetItem)
    def on_set_role_twidget_itemClicked(self, item):

        cur_row = self.set_role_twidget.currentRow()
        item_person_id = self.set_role_twidget.item(cur_row, 1)
        person_id = item_person_id.text()
        item_surname = self.set_role_twidget.item(cur_row, 2)
        surname = item_surname.text()
        item_firstname = self.set_role_twidget.item(cur_row, 3)
        firstname = item_firstname.text()

        self.person_id_edit.setText(person_id)
        self.surname_edit.setText(surname)
        self.firstname_edit.setText(firstname)

    @pyqtSlot(str)
    def on_search_person_id_textChanged(self, text):

        self.set_role_twidget.setRowCount(0)
        value = "%" + text + "%"
        name = "%" + self.search_person_name.text() + "%"
        row = 0
        roles = self.session.query(SetRole).\
            filter(SetRole.user_register.ilike(value)).\
            filter(SetRole.first_name.ilike(name)).all()
        for role in roles:
            self.set_role_twidget.insertRow(row)

            item = QTableWidgetItem(str(row))
            self.set_role_twidget.setItem(row, 0, item)

            item = QTableWidgetItem(role.user_register)
            self.set_role_twidget.setItem(row, 1, item)

            item = QTableWidgetItem(role.surname)
            self.set_role_twidget.setItem(row, 2, item)

            item = QTableWidgetItem(role.first_name)
            self.set_role_twidget.setItem(row, 3, item)

            item = QTableWidgetItem(role.user_name_real)
            self.set_role_twidget.setItem(row, 4, item)

            aimag_name = ''
            soum_name = ''
            if role.working_au_level1:
                aimag_name = role.working_au_level1_ref.name
            if role.working_au_level2:
                soum_name = role.working_au_level2_ref.name
            item = QTableWidgetItem(aimag_name+'/'+soum_name)
            self.set_role_twidget.setItem(row, 5, item)

            item = QTableWidgetItem(role.is_active)
            self.set_role_twidget.setItem(row, 6, item)

            row += 1

    @pyqtSlot(str)
    def on_search_person_name_textChanged(self, text):

        self.set_role_twidget.setRowCount(0)
        value = "%" + text + "%"
        register = "%" + self.search_person_id.text() + "%"
        row = 0
        roles = self.session.query(SetRole).\
            filter(SetRole.first_name.ilike(value)).\
            filter(SetRole.user_register.ilike(register)).all()
        for role in roles:
            self.set_role_twidget.insertRow(row)

            item = QTableWidgetItem(str(row))
            self.set_role_twidget.setItem(row, 0, item)

            item = QTableWidgetItem(role.user_register)
            self.set_role_twidget.setItem(row, 1, item)

            item = QTableWidgetItem(role.surname)
            self.set_role_twidget.setItem(row, 2, item)

            item = QTableWidgetItem(role.first_name)
            self.set_role_twidget.setItem(row, 3, item)

            item = QTableWidgetItem(role.user_name_real)
            self.set_role_twidget.setItem(row, 4, item)

            aimag_name = ''
            soum_name = ''
            if role.working_au_level1:
                aimag_name = role.working_au_level1_ref.name
            if role.working_au_level2:
                soum_name = role.working_au_level2_ref.name
            item = QTableWidgetItem(aimag_name+'/'+soum_name)
            self.set_role_twidget.setItem(row, 5, item)

            item = QTableWidgetItem(role.is_active)
            self.set_role_twidget.setItem(row, 6, item)

            row += 1

    @pyqtSlot()
    def on_clear_person_button_clicked(self):

        self.person_id_edit.clear()
        self.surname_edit.clear()
        self.firstname_edit.clear()

    @pyqtSlot()
    def on_add_person_button_clicked(self):

        if not self.person_id_edit.text():
            PluginUtils.show_message(self, self.tr("Person Null"), self.tr("Please enter person register id"))
            return
        if not self.surname_edit.text():
            PluginUtils.show_message(self, self.tr("Person Null"), self.tr("Please enter person surname"))
            return
        if not self.firstname_edit.text():
            PluginUtils.show_message(self, self.tr("Person Null"), self.tr("Please enter person firstname"))
            return
        is_register = False
        for row in range(self.person_twidget.rowCount()):
            person_id = self.person_twidget.item(row, 1).text()
            if person_id == self.person_id_edit.text():
                is_register = True
        person_count = self.session.query(SetCertificatePerson).\
            filter(SetCertificatePerson.person_id == self.person_id_edit.text()).count()
        if person_count != 1:
            PluginUtils.show_message(self, self.tr("Person Duplicate"), self.tr("This person already registered"))
            return

        if is_register:
            PluginUtils.show_message(self, self.tr("Person Duplicate"), self.tr("This person already registered"))
            return
        row = self.person_twidget.rowCount()
        self.person_twidget.insertRow(row)

        id = -1
        item = QTableWidgetItem(str(row))
        item.setData(Qt.UserRole, id)
        item.setCheckState(Qt.Unchecked)
        self.person_twidget.setItem(row, 0, item)

        item = QTableWidgetItem(self.person_id_edit.text())
        item.setData(Qt.UserRole, self.person_id_edit.text())
        self.person_twidget.setItem(row, 1, item)

        item = QTableWidgetItem(self.surname_edit.text())
        self.person_twidget.setItem(row, 2, item)

        item = QTableWidgetItem(self.firstname_edit.text())
        self.person_twidget.setItem(row, 3, item)

    @pyqtSlot(str)
    def on_person_id_edit_textChanged(self, text):

        self.person_id_edit.setStyleSheet(self.styleSheet())
        new_text = self.__auto_correct_private_person_id(text)
        if new_text is not text:
            self.person_id_edit.setText(new_text)
            return
        if not self.__validate_private_person_id(text):
            self.person_id_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            return

    def __auto_correct_private_person_id(self, text):

        original_text = text
        first_letters = text[:2]
        rest = text[2:]

        first_large_letters = first_letters.upper()

        reg = QRegExp("[0-9]+")

        new_text = first_large_letters + rest

        if len(rest) > 0:

            if not reg.exactMatch(rest):
                for i in rest:
                    if not i.isdigit():
                        rest = rest.replace(i, "")

                new_text = first_large_letters + rest

        if len(new_text) > 10:
            new_text = new_text[:10]

        return new_text

    def __validate_private_person_id(self, text):

        original_text = text
        first_letters = text[:2]
        rest = text[2:]
        first_large_letters = first_letters.upper()

        reg = QRegExp("[0-9][0-9]+")
        is_valid = True

        if first_large_letters[0:1] not in Constants.CAPITAL_MONGOLIAN \
                and first_large_letters[1:2] not in Constants.CAPITAL_MONGOLIAN:
            self.status_label.setText(
                self.tr("First letters of the person id should be capital letters and in mongolian."))
            is_valid = False

        if len(original_text) > 2:
            if not reg.exactMatch(rest):
                self.status_label.setText(
                    self.tr("After the first two capital letters, the person id should contain only numbers."))
                is_valid = False

        if len(original_text) > 10:
            self.status_label.setText(self.tr("The person id shouldn't be longer than 10 characters."))
            is_valid = False

        return is_valid

    def __save_certificate_person(self):

        try:
            for row in range(self.person_twidget.rowCount()):
                new_row = False
                id = self.person_twidget.item(row, 0).data(Qt.UserRole)
                if id == -1:
                    new_row = True
                    person = SetCertificatePerson()
                else:
                    person = self.session.query(SetCertificatePerson).filter(SetCertificatePerson.id == id).one()

                person.person_id = self.person_twidget.item(row, 1).text()
                person.surname = self.person_twidget.item(row, 2).text()
                person.firstname = self.person_twidget.item(row, 3).text()

                if new_row:
                    self.session.add(person)

            self.__read_person()
        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
            raise

    def __read_person(self):

        self.person_twidget.clearContents()
        self.person_twidget.setRowCount(0)
        row = 0
        person_count = self.session.query(SetCertificatePerson).count()
        if person_count > 0:
            self.person_twidget.setRowCount(person_count)
            persons = self.session.query(SetCertificatePerson).all()
            for person in persons:
                item  = QTableWidgetItem(str(person.id))
                item.setData(Qt.UserRole, person.id)
                item.setCheckState(Qt.Unchecked)
                self.person_twidget.setItem(row, 0, item)

                item  = QTableWidgetItem(person.person_id)
                item.setData(Qt.UserRole, person.person_id)
                self.person_twidget.setItem(row, 1, item)

                item  = QTableWidgetItem(person.surname)
                self.person_twidget.setItem(row, 2, item)

                item  = QTableWidgetItem(person.firstname)
                self.person_twidget.setItem(row, 3, item)

                row += 1

    @pyqtSlot(QTableWidgetItem)
    def on_person_twidget_itemClicked(self, item):

        cur_row = self.person_twidget.currentRow()
        item = self.person_twidget.item(cur_row, 0)
        item.setCheckState(Qt.Checked)

        for row in range(self.person_twidget.rowCount()):
            item_dec = self.person_twidget.item(row, 0)
            item_dec.setCheckState(Qt.Unchecked)
        item.setCheckState(Qt.Checked)

        item = self.person_twidget.item(cur_row, 1)
        self.person_id_edit.setText(item.text())

        item = self.person_twidget.item(cur_row, 2)
        self.surname_edit.setText(item.text())

        item = self.person_twidget.item(cur_row, 3)
        self.firstname_edit.setText(item.text())

    @pyqtSlot()
    def on_delete_person_button_clicked(self):

        row = self.person_twidget.currentRow()
        if row == -1:
            return

        id = self.person_twidget.item(row, 0).data(Qt.UserRole)
        if id != -1:  # already has a row in the database
            fee = self.session.query(SetCertificatePerson).filter(SetCertificatePerson.id == id).one()
            self.session.delete(fee)
        self.person_twidget.removeRow(row)

    @pyqtSlot()
    def on_update_person_button_clicked(self):

        row = self.person_twidget.currentRow()
        if row == -1:
            return

        item = self.person_twidget.item(row, 1)
        item.setText(self.person_id_edit.text())
        item.setData(Qt.UserRole,self.person_id_edit.text())

        item = self.person_twidget.item(row, 2)
        item.setText(self.surname_edit.text())

        item = self.person_twidget.item(row, 3)
        item.setText(self.firstname_edit.text())

    @pyqtSlot()
    def on_connect_cert_button_clicked(self):

        is_training_check = False
        for row in range(self.training_twidget.rowCount()):
            item = self.training_twidget.item(row, 0)
            if item.checkState() == Qt.Checked:
                is_training_check = True

        if not is_training_check:
            PluginUtils.show_message(self, self.tr("Check"), self.tr("Please select training!"))
            return

        is_person_check = False
        for row in range(self.person_twidget.rowCount()):
            item = self.person_twidget.item(row, 0)
            if item.checkState() == Qt.Checked:
                is_person_check = True

        if not is_person_check:
            PluginUtils.show_message(self, self.tr("Check"), self.tr("Please select person!"))
            return

        if not self.certificate_no_edit.text():
            PluginUtils.show_message(self, self.tr("Certificate No"), self.tr("Please enter certificate number!"))
            return

        is_register = False
        training_selected_row = self.training_twidget.currentRow()
        training = self.training_twidget.item(training_selected_row, 0)
        for row in range(self.certificate_twidget.rowCount()):
            cert_no = self.certificate_twidget.item(row, 1).text()
            location_no = self.certificate_twidget.item(row, 2).data(Qt.UserRole)
            if cert_no == self.certificate_no_edit.text() and location_no == training.data(Qt.UserRole):
                is_register = True
        if is_register:
            PluginUtils.show_message(self, self.tr("Certificate Duplicate"), self.tr("This certificate already registered"))
            return

        if self.begin_date.date() == self.end_date.date():
            PluginUtils.show_message(self, self.tr("Date error"), self.tr("not must be equals dates!"))
            return

        if self.begin_date.date() > self.end_date.date():
            PluginUtils.show_message(self, self.tr("Date Validate"), self.tr("End date must be backword!"))
            return

        row  = self.certificate_twidget.rowCount()
        self.certificate_twidget.insertRow(row)

        id = -1
        item = QTableWidgetItem(str(row))
        item.setData(Qt.UserRole, id)
        self.certificate_twidget.setItem(row, 0, item)

        item = QTableWidgetItem(self.certificate_no_edit.text())
        item.setData(Qt.UserRole, self.certificate_no_edit.text())
        self.certificate_twidget.setItem(row, 1, item)

        training_selected_row = self.training_twidget.currentRow()
        training = self.training_twidget.item(training_selected_row, 0)
        training_name = self.training_twidget.item(training_selected_row, 1)

        item = QTableWidgetItem(training_name.text())
        item.setData(Qt.UserRole, training.data(Qt.UserRole))
        self.certificate_twidget.setItem(row, 2, item)

        person_selected_row = self.person_twidget.currentRow()
        person = self.person_twidget.item(person_selected_row, 1)
        person_surname = self.person_twidget.item(person_selected_row, 2)
        person_firstname = self.person_twidget.item(person_selected_row, 3)

        item = QTableWidgetItem(person_surname.text()[:1]+'.'+person_firstname.text()+'/'+person.text()+'/')
        item.setData(Qt.UserRole, person.data(Qt.UserRole))
        self.certificate_twidget.setItem(row, 3, item)

        item = QTableWidgetItem(self.begin_date.text())
        item.setData(Qt.UserRole, self.begin_date.date())
        self.certificate_twidget.setItem(row, 4, item)

        item = QTableWidgetItem(self.end_date.text())
        item.setData(Qt.UserRole, self.end_date.date())
        self.certificate_twidget.setItem(row, 5, item)

        item = QTableWidgetItem(self.level_cbox.currentText())
        item.setData(Qt.UserRole, self.level_cbox.itemData(self.level_cbox.currentIndex()))
        self.certificate_twidget.setItem(row, 6, item)

        item_name = QTableWidgetItem("")
        item_name.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.certificate_twidget.setItem(row, 7, item_name)

    def __save_training_person(self):

        training_id = 0
        for row in range(self.certificate_twidget.rowCount()):
            new_row = False
            id = self.certificate_twidget.item(row, 0).data(Qt.UserRole)
            if id == -1:
                new_row = True
                training_person = SetTrainingPerson()
            else:
                training_person = self.session.query(SetTrainingPerson).\
                    filter(SetTrainingPerson.id == id).one()

            begin_date = PluginUtils.convert_qt_date_to_python(self.certificate_twidget.item(row, 4).data(Qt.UserRole))
            end_date = PluginUtils.convert_qt_date_to_python(self.certificate_twidget.item(row, 5).data(Qt.UserRole))

            training_person.certificate_no = self.certificate_twidget.item(row, 1).data(Qt.UserRole)
            training_person.training_id = self.certificate_twidget.item(row, 2).data(Qt.UserRole)
            training_person.person_id = self.certificate_twidget.item(row, 3).data(Qt.UserRole)
            training_person.begin_date = begin_date
            training_person.end_date = end_date
            training_person.level_id = self.certificate_twidget.item(row, 6).data(Qt.UserRole)

            if new_row:
                self.session.add(training_person)
            training_id = self.certificate_twidget.item(row, 2).data(Qt.UserRole)
        self.__read_training_person(training_id)

    def __read_training_person(self, training_id):

        self.certificate_twidget.clearContents()
        self.certificate_twidget.setRowCount(0)
        row = 0
        training_person_count = self.session.query(SetTrainingPerson).count()
        if training_person_count > 0:
            training_persons = self.session.query(SetTrainingPerson).\
                filter(SetTrainingPerson.training_id == training_id).all()
            for training_person in training_persons:
                self.certificate_twidget.insertRow(row)

                item  = QTableWidgetItem(str(training_person.id))
                item.setData(Qt.UserRole, training_person.id)
                self.certificate_twidget.setItem(row, 0, item)

                item  = QTableWidgetItem((training_person.certificate_no))
                item.setData(Qt.UserRole, training_person.certificate_no)
                self.certificate_twidget.setItem(row, 1, item)

                item  = QTableWidgetItem((training_person.training_ref.location))
                item.setData(Qt.UserRole, training_person.training_id)
                self.certificate_twidget.setItem(row, 2, item)

                item  = QTableWidgetItem((training_person.person_ref.surname[:1]+'.'+training_person.person_ref.firstname+'/'+training_person.person_id+'/'))
                item.setData(Qt.UserRole, training_person.person_id)
                self.certificate_twidget.setItem(row, 3, item)

                begin_date = PluginUtils.convert_python_date_to_qt(training_person.begin_date)
                end_date = PluginUtils.convert_python_date_to_qt(training_person.end_date)
                item  = QTableWidgetItem(str(training_person.begin_date))
                item.setData(Qt.UserRole, begin_date)
                self.certificate_twidget.setItem(row, 4, item)

                item  = QTableWidgetItem(str(training_person.end_date))
                item.setData(Qt.UserRole, end_date)
                self.certificate_twidget.setItem(row, 5, item)

                item  = QTableWidgetItem((training_person.level_ref.description))
                item.setData(Qt.UserRole, training_person.level_id)
                self.certificate_twidget.setItem(row, 6, item)

                item_name = QTableWidgetItem("")
                item_name.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.certificate_twidget.setItem(row, 7, item_name)
                self.__update_cert_documents_file_twidget(row)

                row += 1

    def __update_cert_documents_file_twidget(self, row):

        file_name = (self.certificate_twidget.item(row, 3).data(Qt.UserRole))[2:]+'-cert' + '-' + str(self.certificate_twidget.item(row, 2).data(Qt.UserRole)) +'-'+ self.certificate_twidget.item(row, 1).text()

        archive_cert_path = FilePath.cert_file_path()
        if not os.path.exists(archive_cert_path):
            os.makedirs(archive_cert_path)

        for file in os.listdir(archive_cert_path):
            os.listdir(archive_cert_path)
            cert_name = file.split(".")
            cert_name = cert_name[0]

            if file_name == cert_name:
                item_name = QTableWidgetItem(file)
                item_name.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.certificate_twidget.setItem(row, 7, item_name)

    # cadastre page register

    def __cpage_cbox(self):

        # self.cpage_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        # self.cpage_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        # self.cpage_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.cpage_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        self.cpage_twidget.setAlternatingRowColors(True)
        self.cpage_twidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.cpage_twidget.setSelectionMode(QTableWidget.SingleSelection)

        self.cpage_register_date.setDate(QDate().currentDate())
        self.cpage_end_date.setDate(QDate().currentDate())
        self.cpage_aimag_cbox.currentIndexChanged.connect(self.__working_l1_changed)

        if self.cpage_aimag_cbox.count() == 1:
            self.cpage_aimag_cbox.setCurrentIndex(-1)
            self.cpage_aimag_cbox.setCurrentIndex(0)

        PluginUtils.populate_au_level1_cbox(self.cpage_aimag_cbox, False)
        l1_code = self.cpage_aimag_cbox.itemData(self.cpage_aimag_cbox.currentIndex(), Qt.UserRole)
        PluginUtils.populate_au_level2_cbox(self.cpage_soum_cbox, l1_code, False)

    def __working_l1_changed(self, index):

        l1_code = self.cpage_aimag_cbox.itemData(index)
        try:
            PluginUtils.populate_au_level2_cbox(self.cpage_soum_cbox, l1_code, False, True, False)
        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_message(self,  self.tr("Sql Error"), e.message)
            return

    def __cpage_newid(self):

        au2_code = self.cpage_soum_cbox.itemData(self.cpage_soum_cbox.currentIndex(), Qt.UserRole)
        soum_filter = str(au2_code) + "-%"

        count = self.session.query(SetCadastrePage) \
            .filter(SetCadastrePage.id.like("%-%")) \
            .filter(SetCadastrePage.id.like(soum_filter)) \
            .order_by(func.substr(SetCadastrePage.id, 7, 9).desc()).count()

        if count > 0:
            try:
                max_number_cpage = self.session.query(SetCadastrePage) \
                    .filter(SetCadastrePage.id.like("%-%")) \
                    .filter(SetCadastrePage.id.like(soum_filter)) \
                    .order_by(func.substr(SetCadastrePage.id, 7, 9).desc()).first()
            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            cpage_numbers = max_number_cpage.id.split("-")

            cpage_id = au2_code +'-'+ (str(int(cpage_numbers[1]) + 1).zfill(3))

        else:
            cpage_id = au2_code +'-'+ ("001")

        return cpage_id

    @pyqtSlot()
    def on_cpage_add_button_clicked(self):

        if not self.cpage_first_number_edit.value() > 0:
            PluginUtils.show_message(self, self.tr("First Number"), self.tr("Please enter first number."))
            return

        if not self.cpage_last_number_edit.value() > 0:
            PluginUtils.show_message(self, self.tr("Last Number"), self.tr("Please enter last number."))
            return

        if not self.cpage_last_number_edit.value() > self.cpage_first_number_edit.value():
            PluginUtils.show_message(self, self.tr("Not Allowed"), self.tr("Not allowed last number."))
            return

        if not self.cpage_end_date.date() > self.cpage_register_date.date():
            PluginUtils.show_message(self, self.tr("Not Allowed"), self.tr("Not allowed end date."))
            return

        au1_code = self.cpage_aimag_cbox.itemData(self.cpage_aimag_cbox.currentIndex(), Qt.UserRole)
        au2_code = self.cpage_soum_cbox.itemData(self.cpage_soum_cbox.currentIndex(), Qt.UserRole)

        register_date_qt = PluginUtils.convert_qt_date_to_python(self.cpage_register_date.date())
        end_date_qt = PluginUtils.convert_qt_date_to_python(self.cpage_end_date.date())

        cadastre_page_count = self.session.query(SetCadastrePage)\
            .filter(SetCadastrePage.register_date == register_date_qt)\
            .filter(SetCadastrePage.au_level2 == au2_code).count()

        if cadastre_page_count > 0:
            PluginUtils.show_message(self, self.tr("Not Allowed"), self.tr("Already registered and you edit this information!."))
            return

        au1 = self.session.query(AuLevel1).filter(AuLevel1.code == au1_code).one()
        au2 = self.session.query(AuLevel2).filter(AuLevel2.code == au2_code).one()

        row = self.cpage_twidget.rowCount()
        self.cpage_twidget.insertRow(row)

        id = self.__cpage_newid()
        item = QTableWidgetItem(str(id))
        item.setData(Qt.UserRole, id)
        self.cpage_twidget.setItem(row, 0, item)

        item = QTableWidgetItem(self.cpage_register_date.text())
        item.setData(Qt.UserRole, self.cpage_register_date.date())
        self.cpage_twidget.setItem(row, 1, item)

        item = QTableWidgetItem(self.cpage_end_date.text())
        item.setData(Qt.UserRole, self.cpage_end_date.date())
        self.cpage_twidget.setItem(row, 2, item)

        item = QTableWidgetItem(str(self.cpage_first_number_edit.value()))
        item.setData(Qt.UserRole, self.cpage_first_number_edit.value())
        self.cpage_twidget.setItem(row, 3, item)

        item = QTableWidgetItem(str(self.cpage_last_number_edit.value()))
        item.setData(Qt.UserRole, self.cpage_last_number_edit.value())
        self.cpage_twidget.setItem(row, 4, item)

        item = QTableWidgetItem(str(self.cpage_current_number_edit.value()))
        item.setData(Qt.UserRole, self.cpage_current_number_edit.value())
        self.cpage_twidget.setItem(row, 5, item)

        item = QTableWidgetItem(unicode(au1.name))
        item.setData(Qt.UserRole, au1.code)
        self.cpage_twidget.setItem(row, 6, item)

        item = QTableWidgetItem(unicode(au2.name))
        item.setData(Qt.UserRole, au2.code)
        self.cpage_twidget.setItem(row, 7, item)

        # database insert

        cpage = SetCadastrePage()
        cpage.id = id
        cpage.register_date = register_date_qt
        cpage.end_date = end_date_qt
        cpage.range_first_no = self.cpage_first_number_edit.value()
        cpage.range_last_no = self.cpage_last_number_edit.value()
        cpage.current_no = self.cpage_current_number_edit.value()
        cpage.au_level1 = au1_code
        cpage.au_level1_ref = au1
        cpage.au_level2 = au2_code
        cpage.au_level2_ref = au2

        self.session.add(cpage)

    @pyqtSlot(int)
    def on_cpage_soum_cbox_currentIndexChanged(self, index):

        self.cpage_twidget.setRowCount(0)
        au2_code = self.cpage_soum_cbox.itemData(self.cpage_soum_cbox.currentIndex(), Qt.UserRole)

        cpages = self.session.query(SetCadastrePage).filter(SetCadastrePage.au_level2 == au2_code).all()

        row = 0
        for cpage in cpages:
            au1 = self.session.query(AuLevel1).filter(AuLevel1.code == cpage.au_level1).one()
            au2 = self.session.query(AuLevel2).filter(AuLevel2.code == cpage.au_level2).one()

            self.cpage_twidget.insertRow(row)
            item = QTableWidgetItem(cpage.id)
            item.setData(Qt.UserRole, cpage.id)
            self.cpage_twidget.setItem(row, 0, item)

            item = QTableWidgetItem(str(cpage.register_date))
            item.setData(Qt.UserRole, cpage.register_date)
            self.cpage_twidget.setItem(row, 1, item)

            item = QTableWidgetItem(str(cpage.end_date))
            item.setData(Qt.UserRole, cpage.end_date)
            self.cpage_twidget.setItem(row, 2, item)

            item = QTableWidgetItem(str(cpage.range_first_no))
            item.setData(Qt.UserRole, cpage.range_first_no)
            self.cpage_twidget.setItem(row, 3, item)

            item = QTableWidgetItem(str(cpage.range_last_no))
            item.setData(Qt.UserRole, cpage.range_last_no)
            self.cpage_twidget.setItem(row, 4, item)

            item = QTableWidgetItem(str(cpage.current_no))
            item.setData(Qt.UserRole, cpage.current_no)
            self.cpage_twidget.setItem(row, 5, item)

            item = QTableWidgetItem(unicode(au1.name))
            item.setData(Qt.UserRole, au1.code)
            self.cpage_twidget.setItem(row, 6, item)

            item = QTableWidgetItem(unicode(au2.name))
            item.setData(Qt.UserRole, au2.code)
            self.cpage_twidget.setItem(row, 7, item)

            row += 1

    @pyqtSlot()
    def on_cpage_edit_button_clicked(self):

        selected_items = self.cpage_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose cadastre page!!!"))
            return

        au1_code = self.cpage_aimag_cbox.itemData(self.cpage_aimag_cbox.currentIndex(), Qt.UserRole)
        au2_code = self.cpage_soum_cbox.itemData(self.cpage_soum_cbox.currentIndex(), Qt.UserRole)

        au1 = self.session.query(AuLevel1).filter(AuLevel1.code == au1_code).one()
        au2 = self.session.query(AuLevel2).filter(AuLevel2.code == au2_code).one()

        current_row = self.cpage_twidget.currentRow()
        id = self.cpage_twidget.item(current_row, 0).data(Qt.UserRole)

        item = self.cpage_twidget.item(current_row, 1)
        item.setText(self.cpage_register_date.text())
        item.setData(Qt.UserRole, self.cpage_register_date.date())

        item = self.cpage_twidget.item(current_row, 2)
        item.setText(self.cpage_end_date.text())
        item.setData(Qt.UserRole, self.cpage_end_date.date())

        item = self.cpage_twidget.item(current_row, 3)
        item.setText(str(self.cpage_first_number_edit.value()))
        item.setData(Qt.UserRole, self.cpage_first_number_edit.value())

        item = self.cpage_twidget.item(current_row, 4)
        item.setText(str(self.cpage_last_number_edit.value()))
        item.setData(Qt.UserRole, self.cpage_last_number_edit.value())

        item = self.cpage_twidget.item(current_row, 5)
        item.setText(str(self.cpage_current_number_edit.value()))
        item.setData(Qt.UserRole, self.cpage_current_number_edit.value())

        item = self.cpage_twidget.item(current_row, 6)
        item.setText(unicode(au1.name))
        item.setData(Qt.UserRole, au1.code)

        item = self.cpage_twidget.item(current_row, 7)
        item.setText(unicode(au2.name))
        item.setData(Qt.UserRole, au2.code)

        register_date_qt = PluginUtils.convert_qt_date_to_python(self.cpage_register_date.date())
        end_date_qt = PluginUtils.convert_qt_date_to_python(self.cpage_end_date.date())

        cpage_count = self.session.query(SetCadastrePage).filter(SetCadastrePage.id == id).count()
        if cpage_count == 1:
            cpage = self.session.query(SetCadastrePage).filter(SetCadastrePage.id == id).one()
            cpage.register_date = register_date_qt
            cpage.end_date = end_date_qt
            cpage.range_first_no = self.cpage_first_number_edit.value()
            cpage.range_last_no = self.cpage_last_number_edit.value()
            cpage.current_no = self.cpage_current_number_edit.value()
            cpage.au_level1 = au1_code
            cpage.au_level1_ref = au1
            cpage.au_level2 = au2_code
            cpage.au_level2_ref = au2

    @pyqtSlot(QTableWidgetItem)
    def on_cpage_twidget_itemClicked(self, item):

        current_row = self.cpage_twidget.currentRow()

        item = self.cpage_twidget.item(current_row, 1)
        register_date = item.data(Qt.UserRole)
        self.cpage_register_date.setDate(register_date)

        item = self.cpage_twidget.item(current_row, 2)
        end_date = item.data(Qt.UserRole)
        self.cpage_end_date.setDate(end_date)

        item = self.cpage_twidget.item(current_row, 3)
        first_number = item.data(Qt.UserRole)
        self.cpage_first_number_edit.setValue(first_number)

        item = self.cpage_twidget.item(current_row, 4)
        last_number = item.data(Qt.UserRole)
        self.cpage_last_number_edit.setValue(last_number)

        item = self.cpage_twidget.item(current_row, 5)
        current_number = item.data(Qt.UserRole)
        self.cpage_current_number_edit.setValue(current_number)

        item = self.cpage_twidget.item(current_row, 6)
        au1_code = item.data(Qt.UserRole)
        self.cpage_aimag_cbox.findData(au1_code)

        item = self.cpage_twidget.item(current_row, 7)
        au2_code = item.data(Qt.UserRole)
        self.cpage_soum_cbox.findData(au2_code)

    @pyqtSlot()
    def on_cpage_delete_button_clicked(self):

        selected_items = self.cpage_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose cadastre page!!!"))
            return

        current_row = self.cpage_twidget.currentRow()
        id = self.cpage_twidget.item(current_row, 0).data(Qt.UserRole)

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to delete the cadastre page info ?"))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        cpage_count = self.session.query(SetCadastrePage).filter(SetCadastrePage.id == id).count()
        if cpage_count == 1:
            self.session.query(SetCadastrePage).filter(SetCadastrePage.id == id).delete()
            self.cpage_twidget.removeRow(current_row)