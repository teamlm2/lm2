# coding=utf8

__author__ = 'Anna'

from types import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *
from qgis.core import *
from qgis.gui import *
from sqlalchemy import func, or_, and_, desc,extract
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal
from sqlalchemy.sql import exists
from datetime import date, datetime, timedelta
from inspect import currentframe
import os
import types
import textwrap
import win32api
import win32net
import win32netcon,win32wnet
from ..utils.FileUtils import FileUtils
from ..model.LM2Exception import LM2Exception
from ..model.ClApplicationStatus import ClApplicationStatus
from ..model.ClContractCancellationReason import *
from ..model.ClContractStatus import *
from ..model.ClRecordStatus import *
from ..model.ClMortgageStatus import ClMortgageStatus
from ..model.ClCourtStatus import ClCourtStatus
from ..model.BsPerson import *
from ..model.ClPersonRole import *
from ..model.ClPositionType import *
from ..model.ClRightType import *
from ..model.CtApplication import *
from ..model.CtContractApplicationRole import *
from ..model.CtRecordApplicationRole import *
from ..model.CtApplicationStatus import *
from ..model.CtOwnershipRecord import *
from ..model.CaTmpParcel import *
from ..model.SetBaseTaxAndPrice import *
from ..model.CtDecision import *
from ..model.CtDecisionApplication import *
from ..model.SetApplicationTypeDocumentRole import *
from ..model.SetPersonTypeApplicationType import *
from ..model.SetApplicationTypeLanduseType import *
from ..model.SetRightTypeApplicationType import *
from ..model.SetValidation import *
from ..model.ContractSearch import *
from ..model.RecordSearch import *
from ..model.DatabaseHelper import *
from ..model.SetTaxAndPriceZone import *
from ..model import SettingsConstants
from ..model import Constants
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.MaintenanceSearch import *
from ..model.Enumerations import ApplicationType, UserRight
from .qt_classes.ApplicantDocumentDelegate import ApplicationDocumentDelegate
from .qt_classes.DocumentsTableWidget import DocumentsTableWidget
from .qt_classes.DragTableWidget import DragTableWidget
from .qt_classes.DoubleSpinBoxDelegate import DoubleSpinBoxDelegate
from .qt_classes.DropLabel import DropLabel
from ..view.Ui_ApplicationsDialog import *
from ..utils.SessionHandler import SessionHandler
from ..utils.PluginUtils import PluginUtils
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.FilePath import *

DOC_PROVIDED_COLUMN = 0
DOC_FILE_TYPE_COLUMN = 1
DOC_FILE_NAME_COLUMN = 2
DOC_OPEN_FILE_COLUMN = 3
DOC_DELETE_COLUMN = 4
DOC_VIEW_COLUMN = 5
MORTGAGE_SHARE = 0
MORTGAGE_PERSON_ID = 1
MORTGAGE_NAME = 2
MORTGAGE_SURNAME = 3
MORTGAGE_BEGIN = 4
MORTGAGE_END = 5
MORTGAGE_TYPE = 6
APPLICANT_MAIN = 0
APPLICANT_SHARE = 1
APPLICANT_PERSON_ID = 2
APPLICANT_SURNAME = 3
APPLICANT_FIRST_NAME = 4
LEGAL_REP_PERSON_ID = 0
LEGAL_REP_SURNAME = 1
LEGAL_REP_FIRST_NAME = 2
LEGAL_REP_AGE = 3
NEW_RIGHT_HOLDER_MAIN = 0
OLD_RIGHT_HOLDER_SHARE = 0
NEW_RIGHT_HOLDER_SHARE = 1
NEW_RIGHT_HOLDER_PERSON_ID = 2
NEW_RIGHT_HOLDER_SURNAME = 3
NEW_RIGHT_HOLDER_FIRST_NAME = 4
STATUS_STATE = 0
STATUS_DATE = 1
STATUS_OFFICER = 2
STATUS_NEXT_OFFICER = 3
CO_OWNERSHIP_MAIN = 0
CO_OWNERSHIP_PERSON_ID = 1
CO_OWNERSHIP_SURNAME = 2
CO_OWNERSHIP_FIRST_NAME = 3


class ApplicationsDialog(QDialog, Ui_ApplicationsDialog, DatabaseHelper):

    def __init__(self, application, navigator, attribute_update=False, parent=None):

        super(ApplicationsDialog, self).__init__(parent)
        DatabaseHelper.__init__(self)
        self.navigator = navigator
        self.attribute_update = attribute_update

        self.session = SessionHandler().session_instance()
        self.application = application

        self.timer = None
        self.last_row = None
        self.last_tab = -1
        self.updating = False

        self.applicant_twidget = None
        self.legal_rep_twidget = None
        self.documents_twidget = None
        self.new_right_holders_twidget = None
        self.mortgage_twidget = None
        self.person = None
        self.is_tmp_parcel = False
        self.is_representative = False
        self.setupUi(self)
        self.close_button.clicked.connect(self.reject)

        self.contract_court_decision_label.setVisible(False)
        self.record_court_decision_label.setVisible(False)
        self.contract_court_status_cbox.setVisible(False)
        self.record_court_status_cbox.setVisible(False)

        self.contract_court_decision_label.setVisible(False)
        self.contract_court_status_cbox.setVisible(False)
        self.contract_court_start_label.setVisible(False)
        self.contract_court_end_label.setVisible(False)
        self.contract_court_start_date_edit.setVisible(False)
        self.contract_court_end_date_edit.setVisible(False)

        self.record_court_decision_label.setVisible(False)
        self.record_court_status_cbox.setVisible(False)
        self.record_court_start_label.setVisible(False)
        self.record_court_end_label.setVisible(False)
        self.record_court_start_date_edit.setVisible(False)
        self.record_court_end_date_edit.setVisible(False)

        self.contract_court_start_date_edit.setDate(QDate.currentDate())
        self.record_court_start_date_edit.setDate(QDate.currentDate())

        self.contract_court_end_date_edit.setDate(QDate.currentDate())
        self.record_court_end_date_edit.setDate(QDate.currentDate())

        self.__setup_combo_boxes()
        self.__setup_ui()
        self.__setup_permissions()

    #public functions
    def current_document_applicant(self):

        applicant = self.applicant_documents_cbox.itemData(self.applicant_documents_cbox.currentIndex())
        return applicant

    def current_application(self):

        return self.application

    def current_application_no(self):
        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()

        return app_no
    #end public functions

    def __setup_ui(self):

        self.document_path_edit.setText(FilePath.app_file_path())
        self.share_spinbox = QDoubleSpinBox()
        self.share_spinbox.setDecimals(2)
        self.share_spinbox.setMaximum(1.0)
        self.share_spinbox.setValue(1.0)
        self.share_spinbox.setSingleStep(0.1)

        self.mortgage_start_date_edit.setDate(QDate().currentDate())
        self.mortgage_end_date_edit.setDate(QDate().currentDate())
        self.status_date_date.setDate(QDate().currentDate())

        self.drop_label = DropLabel("parcel", self.search_group_box)
        self.drop_label.itemDropped.connect(self.on_drop_label_itemDropped)

        self.contract_drop_label = DropLabel("contract", self.relating_contract_groupbox)
        self.contract_drop_label.itemDropped.connect(self.on_contract_drop_label_itemDropped)

        self.record_drop_label = DropLabel("Ownership record", self.relating_record_groupbox)
        self.record_drop_label.itemDropped.connect(self.on_record_drop_label_itemDropped)

        if self.attribute_update:
            self.__setup_mapping()
        else:
            self.date_time_date.setDateTime(QDateTime.currentDateTime())

        try:
            self.__setup_status_widget()
            self.__setup_documents_twidget()
            self.__setup_applicant_twidget()
            self.__setup_legal_rep_twidget()
            self.__setup_ownership_twidgets()
            self.__setup_transfer_twidgets()
            self.__setup_mortgage_twidget()

            self.__setup_records()
            self.__setup_contracts()

        except LM2Exception, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __setup_mapping(self):

        try:
            status_count = self.session.query(CtApplicationStatus)\
                .filter(CtApplication.app_no == self.application.app_no)\
                .filter(CtApplicationStatus.status >= 5).count()
            if status_count > 0:
                self.requested_land_use_type_cbox.setEnabled(False)

            status_count_7 = self.session.query(CtApplicationStatus) \
                .filter(CtApplication.app_no == self.application.app_no) \
                .filter(CtApplicationStatus.status >= 7).count()
            if status_count_7 > 0:
                self.status_cbox.removeItem(self.status_cbox.findData(8))

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
        # details
        python_date = self.application.app_timestamp
        app_date = PluginUtils.convert_python_datetime_to_qt(python_date)
        self.date_time_date.setDateTime(app_date)

        self.application_type_cbox.setCurrentIndex(self.application_type_cbox.findData(self.application.app_type))
        self.application_type_cbox.setEnabled(False)
        self.approved_land_use_type_cbox.setCurrentIndex(self.approved_land_use_type_cbox.findData(self.application.approved_landuse))
        self.requested_land_use_type_cbox.setCurrentIndex(self.requested_land_use_type_cbox.findData(self.application.requested_landuse))

        if self.application.parcel is None:
            self.parcel_edit.setText(self.application.tmp_parcel)
            if self.application.tmp_parcel_ref is not None:
                self.parcel_area_edit.setText(str(self.application.tmp_parcel_ref.area_m2))
        else:
            self.parcel_edit.setText(self.application.parcel)
            if self.application.parcel_ref is not None:
                self.parcel_area_edit.setText(str(self.application.parcel_ref.area_m2))

        if self.application.requested_duration:
            self.requested_year_spin_box.setValue(self.application.requested_duration)

        if self.application.approved_duration:
            self.approved_year_spin_box.setValue(self.application.approved_duration)

        self.remarks_text_edit.setText(self.application.remarks)

        # App1Ext
        if self.application.app1ext:
            self.excess_area_spin_box.setValue(self.application.app1ext.excess_area)
            self.price_to_be_paid_spin_box.setValue(self.application.app1ext.price_to_be_paid)

            if self.application.app1ext.applicant_has_paid:
                self.paid_by_applicant_check_box.setCheckState(Qt.Checked)
            else:
                self.paid_by_applicant_check_box.setCheckState(Qt.Unchecked)

        # App8Ext
        if self.application.app8ext:
            mortgage_start = self.application.app8ext.start_mortgage_period
            mortgage_start_qt = PluginUtils.convert_python_date_to_qt(mortgage_start)

            mortgage_end_date = self.application.app8ext.end_mortgage_period
            mortgage_end_qt = PluginUtils.convert_python_date_to_qt(mortgage_end_date)
            self.mortgage_start_date_edit.setDate(mortgage_start_qt)
            self.mortgage_end_date_edit.setDate(mortgage_end_qt)
            self.mortgage_type_cbox.setCurrentIndex(
                self.mortgage_type_cbox.findData(self.application.app8ext.mortgage_type))

            mortgage_status = self.application.app8ext.mortgage_status
            if mortgage_status:
                self.mortgage_status_cbox.setCurrentIndex(self.mortgage_status_cbox.findData(mortgage_status))

        # App15Ext
        if self.application.app15ext:
            transfer_type = self.application.app15ext.transfer_type
            self.type_of_transfer_cbox.setCurrentIndex(self.type_of_transfer_cbox.findData(transfer_type))

        # App29Ext
        if self.application.app29ext:
            court_status = self.application.app29ext.court_status
            start_period = self.application.app29ext.start_period
            start_period_qt = PluginUtils.convert_python_date_to_qt(start_period)

            end_period = self.application.app29ext.end_period
            end_period_qt = PluginUtils.convert_python_date_to_qt(end_period)

            rigth_code = self.rigth_type_cbox.itemData(self.rigth_type_cbox.currentIndex())
            if self.application.app_type == ApplicationType.court_decision:
                if rigth_code == 3:
                    self.record_court_decision_label.setVisible(True)
                    self.record_court_status_cbox.setVisible(True)
                    self.record_court_start_label.setVisible(True)
                    self.record_court_end_label.setVisible(True)
                    self.record_court_start_date_edit.setVisible(True)
                    self.record_court_end_date_edit.setVisible(True)

                    self.record_court_start_date_edit.setDate(start_period_qt)
                    self.record_court_end_date_edit.setDate(end_period_qt)

                    if court_status:
                        self.record_court_status_cbox.setCurrentIndex(self.record_court_status_cbox.findData(court_status))
                else:
                    self.contract_court_decision_label.setVisible(True)
                    self.contract_court_status_cbox.setVisible(True)
                    self.contract_court_start_label.setVisible(True)
                    self.contract_court_end_label.setVisible(True)
                    self.contract_court_start_date_edit.setVisible(True)
                    self.contract_court_end_date_edit.setVisible(True)

                    self.contract_court_start_date_edit.setDate(start_period_qt)
                    self.contract_court_end_date_edit.setDate(end_period_qt)
                    if court_status:
                        self.contract_court_status_cbox.setCurrentIndex(self.contract_court_status_cbox.findData(court_status))

        # App_no + Soum + Landuse
        app_no = self.application.app_no
        parts_app_no = app_no.split("-")

        self.application_num_first_edit.setText(parts_app_no[0])
        self.application_num_type_edit.setText(parts_app_no[1])
        self.application_num_middle_edit.setText(parts_app_no[2])
        self.application_num_last_edit.setText(parts_app_no[3])

        #disable assign button, if application is approved or refused
        status_count = self.session.query(CtApplicationStatus).filter(CtApplicationStatus.application == self.application.app_no)\
            .filter(CtApplicationStatus.status >= Constants.APP_STATUS_SEND).count()

        if status_count > 0:
            self.unassign_button.setEnabled(False)

        if self.application.maintenance_case:
            self.maintenance_case_edit.setText(str(self.application.maintenance_case))

    def __setup_permissions(self):

        user_name = QSettings().value(SettingsConstants.USER)
        user_rights = DatabaseUtils.userright_by_name(user_name)

        if UserRight.application_update in user_rights:
            self.apply_button.setEnabled(True)
            self.applicant_twidget.setAcceptDrops(True)
            self.legal_rep_twidget.setAcceptDrops(True)
            self.drop_label.setAcceptDrops(True)
            self.mortgage_twidget.setAcceptDrops(True)
            self.new_right_holders_twidget.setAcceptDrops(True)
            self.documents_twidget.setEnabled(True)

            self.apply_button.setEnabled(True)
            self.remove_new_right_holder_button.setEnabled(True)
            self.appliciants_remove_button.setEnabled(True)
            self.mortgagee_remove_button.setEnabled(True)
            self.representatives_remove_button.setEnabled(True)
            if not self.unassign_button.isEnabled() is False:
                self.unassign_button.setEnabled(True)
            self.add_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.update_button.setEnabled(True)
            self.accept_parcel_number_button.setEnabled(True)
            self.up_button.setEnabled(True)
            self.down_button.setEnabled(True)
        else:
            self.applicant_twidget.setAcceptDrops(False)
            self.legal_rep_twidget.setAcceptDrops(False)
            self.drop_label.setAcceptDrops(False)
            self.mortgage_twidget.setAcceptDrops(False)
            self.new_right_holders_twidget.setAcceptDrops(False)
            self.documents_twidget.setEnabled(False)

            self.apply_button.setEnabled(False)
            self.remove_new_right_holder_button.setEnabled(False)
            self.appliciants_remove_button.setEnabled(False)
            self.mortgagee_remove_button.setEnabled(False)
            self.representatives_remove_button.setEnabled(False)
            self.unassign_button.setEnabled(False)
            self.accept_parcel_number_button.setEnabled(True)

            self.add_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.update_button.setEnabled(False)
            self.up_button.setEnabled(False)
            self.down_button.setEnabled(False)

    def __setup_transfer_twidgets(self):

        self.old_right_holders_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.old_right_holders_twidget.setSelectionMode(QAbstractItemView.SingleSelection)

        self.new_right_holders_twidget = DragTableWidget("person", 20, 50, 720, 110, self.new_right_holder_groupbox)
        self.new_right_holders_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.new_right_holders_twidget.setSelectionMode(QAbstractItemView.SingleSelection)

        header = [self.tr("Main Applicant"),
                  self.tr("Share (0.0 - 1.0)"),
                  self.tr("Personal/Company ID"),
                  self.tr("Surname/Company"),
                  self.tr("First Name")]

        delegate = DoubleSpinBoxDelegate(NEW_RIGHT_HOLDER_SHARE, 0, 1, 1, 0.1, self.new_right_holders_twidget)
        self.new_right_holders_twidget.setItemDelegateForColumn(NEW_RIGHT_HOLDER_SHARE, delegate)

        delegate = DoubleSpinBoxDelegate(OLD_RIGHT_HOLDER_SHARE, 0, 1, 1, 0.1, self.old_right_holders_twidget)
        self.old_right_holders_twidget.setItemDelegateForColumn(OLD_RIGHT_HOLDER_SHARE, delegate)

        self.new_right_holders_twidget.setup_header(header)
        self.new_right_holders_twidget.itemDropped.connect(self.on_new_right_holder_twidget_itemDropped)
        self.new_right_holders_twidget.cellChanged.connect(self.on_new_right_holder_twidget_cellChanged)

        try:
            applicants_new = self.application.stakeholders.filter(
                CtApplicationPersonRole.role == Constants.NEW_RIGHT_HOLDER_CODE).all()
            applicants_old = self.application.stakeholders.filter(
                CtApplicationPersonRole.role == Constants.OLD_RIGHT_HOLDER_CODE).all()

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        for applicant in applicants_new:
            self.__add_new_right_holder_item(applicant)

        for applicant in applicants_old:
            self.__add_old_right_holder_item(applicant)

    @pyqtSlot(int, int)
    def on_new_right_holder_twidget_cellChanged(self, row, column):

        if column == APPLICANT_MAIN:
            changed_item = self.new_right_holders_twidget.item(row, column)
            if changed_item.checkState() == Qt.Checked:

                for cu_row in range(self.new_right_holders_twidget.rowCount()):
                    item = self.new_right_holders_twidget.item(cu_row, column)
                    if item.checkState() == Qt.Checked and row != cu_row:

                        item.setCheckState(Qt.Unchecked)

    def __setup_mortgage_twidget(self):

        self.mortgage_twidget = DragTableWidget("person", 20, 120, 711, 192, self.mortgage_group_box)

        header = [self.tr("Share (0.0-1.0)"),
                  self.tr("Person/Company ID"),
                  self.tr("Surname/Company"),
                  self.tr("First Name")]

        delegate = DoubleSpinBoxDelegate(MORTGAGE_SHARE, 0, 1, 1, 0.1, self.mortgage_twidget)
        self.mortgage_twidget.setItemDelegateForColumn(MORTGAGE_SHARE, delegate)

        self.mortgage_twidget.setup_header(header)
        self.mortgage_twidget.itemDropped.connect(self.on_mortgage_twidget_itemDropped)

        try:
            stakeholders = self.application.stakeholders.filter(
                CtApplicationPersonRole.role == Constants.MORTGAGEE_ROLE_CODE).all()

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        for applicant in stakeholders:
            self.__add_mortgagee_item(applicant)

    def __setup_ownership_twidgets(self):

        self.owners_remaining_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.owners_remaining_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.owners_remaining_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.owners_giving_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.owners_giving_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.owners_giving_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.owners_remaining_twidget.cellChanged.connect(self.on_owners_remaining_twidget_cellChanged)
        try:
            applicants_remaining = self.application.stakeholders.filter(
                CtApplicationPersonRole.role == Constants.REMAINING_OWNER_CODE).all()
            applicants_giving = self.application.stakeholders.filter(
                CtApplicationPersonRole.role == Constants.GIVING_UP_OWNER_CODE)
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        for applicant in applicants_remaining:
            self.__add_co_ownership_item(applicant, Constants.REMAINING_OWNER_CODE)

        for applicant in applicants_giving:
            self.__add_co_ownership_item(applicant, Constants.GIVING_UP_OWNER_CODE)

    def __setup_legal_rep_twidget(self):

        self.legal_rep_twidget = DragTableWidget("person", 20, 100, 711, 192, self.legal_representative_group_box)

        header = [self.tr("Personal/Company ID"),
                  self.tr("Surname/Company"),
                  self.tr("First Name"),
                  self.tr("Age")]

        self.legal_rep_twidget.setup_header(header)
        self.legal_rep_twidget.itemDropped.connect(self.on_legal_rep_twidget_itemDropped)

        try:
            legal_representatives = self.application.stakeholders.filter(
                CtApplicationPersonRole.role == Constants.LEGAL_REP_ROLE_CODE).all()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        for applicant in legal_representatives:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1,
                                                  self.legal_representative_tab, QIcon(),
                                                  self.tr("Legal Representative"))
            self.is_representative = True
            self.__add_legal_rep_item(applicant)

    def __setup_applicant_twidget(self):

        self.applicant_twidget = DragTableWidget("person", 20, 40, 720, 280, self.applicants_group_box)

        header = [self.tr("Main Applicant"),
                  self.tr("Share [0.0 - 1.0]"),
                  self.tr("Personal/Company ID"),
                  self.tr("Surname/Company"),
                  self.tr("First Name")]

        self.applicant_twidget.setup_header(header)
        delegate = DoubleSpinBoxDelegate(APPLICANT_SHARE, 0, 1, 1, 0.1, self.applicant_twidget)
        self.applicant_twidget.setItemDelegateForColumn(APPLICANT_SHARE, delegate)
        self.applicant_twidget.itemDropped.connect(self.on_application_twidget_itemDropped)
        self.applicant_twidget.cellChanged.connect(self.on_application_twidget_cellChanged)

        try:
            applicants = self.application.stakeholders.filter(
                CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE).all()

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        for applicant in applicants:
            self.__add_applicant_item(applicant)

    def __setup_status_widget(self):

        self.application_status_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.application_status_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.application_status_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.application_status_twidget.setSortingEnabled(True)

        status = self.session.query(func.max(CtApplicationStatus.status)). \
            filter(CtApplicationStatus.application == self.application.app_no).one()
        max_status = str(status).split(",")[0][1:]
        self.status_cbox.setCurrentIndex(self.status_cbox.findData(str(int(max_status)+1)))
        for status in self.application.statuses:
            self.__add_application_status_item(status)

        self.application_status_twidget.sortItems(0, Qt.AscendingOrder)
        self.__update_decision_tab()


    def __setup_documents_twidget(self):

        self.documents_twidget = DocumentsTableWidget(self.documents_group_box)
        delegate = ApplicationDocumentDelegate(self.documents_twidget, self)
        self.documents_twidget.setItemDelegate(delegate)

    def __setup_combo_boxes(self):

        try:
            rigth_types = self.session.query(ClRightType).all()
            application_types = self.session.query(ClApplicationType).\
                filter(and_(ClApplicationType.code != ApplicationType.pasture_use, ClApplicationType.code != ApplicationType.right_land)).\
                order_by(ClApplicationType.code).all()
            statuses = self.session.query(ClApplicationStatus).order_by(ClApplicationStatus.code).all()
            transfer_type = self.session.query(ClTransferType).all()
            set_roles = self.session.query(SetRole).all()
            mortgage_list = self.session.query(ClMortgageType).all()
            landuse_types = self.session.query(ClLanduseType).all()
            mortgage_status = self.session.query(ClMortgageStatus).all()
            court_status = self.session.query(ClCourtStatus).all()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        for item in rigth_types:
            self.rigth_type_cbox.addItem(item.description, item.code)

        for item in application_types:
            self.application_type_cbox.addItem(item.description, item.code)

        for status in statuses:
            self.status_cbox.addItem(status.description, status.code)

        for item in transfer_type:
            self.type_of_transfer_cbox.addItem(item.description, item.code)

        for setRole in set_roles:
            self.next_officer_in_charge_cbox.addItem(setRole.surname + ", " + setRole.first_name, setRole.user_name_real)

        officer = self.session.query(SetRole) \
            .filter(SetRole.user_name == QSettings().value(SettingsConstants.USER)) \
            .filter(SetRole.is_active == True).one()
        current_user = officer.user_name_real
        self.next_officer_in_charge_cbox.setCurrentIndex(self.next_officer_in_charge_cbox.findData(current_user))

        for item in mortgage_list:
            self.mortgage_type_cbox.addItem(item.description, item.code)

        for item in landuse_types:
            self.approved_land_use_type_cbox.addItem(str(item.code) + ": " + item.description, item.code)

        for item in mortgage_status:
            self.mortgage_status_cbox.addItem(item.description, item.code)

        for item in court_status:
            self.contract_court_status_cbox.addItem(item.description, item.code)

        for item in court_status:
            self.record_court_status_cbox.addItem(item.description, item.code)

    def __validity_of_application(self):

        valid = True
        error_message = self.tr("The application can't be saved. The following errors have been found: ")

        if self.application_type_cbox.currentIndex() == -1:
            self.application_type_cbox.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            valid = False
            app_type_error = self.tr("Missing Application type.")
            error_message = error_message + "\n \n" + app_type_error

        if self.date_time_date.date() == "":
            self.date_time_date.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            date_time_error = self.tr("Missing timestamp for Application.")
            error_message = error_message + "\n \n" + date_time_error
            valid = False

        if self.applicant_twidget.rowCount() == 0:
            self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            applicants_error = self.tr("Missing applicants. ")
            error_message = error_message + "\n \n" + applicants_error
            valid = False

        # if not self.__check_age_applicants() or self.person.type == 20:
        #     self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
        #     applicants_error = self.tr("Person under the age of 18.")
        #     error_message = error_message + "\n \n" + applicants_error
        #     valid = False
        if not self.is_representative:
            if not self.__check_share_age_applicants() and self.application.app_type != 3:
                self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
                applicants_error = self.tr("In capable person share should be equal 0 ")
                error_message = error_message + "\n \n" + applicants_error
                valid = False

        if not self.is_representative:
            if not self.__check_share_applicants():
                self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
                applicants_error = self.tr("The sum of share in the applicants is not 1.0 ")
                error_message = error_message + "\n \n" + applicants_error
                valid = False

        if not self.__check_main_capable_applicant() and self.application.app_type == 3:
            self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            applicants_error = self.tr("In uncapable person should be main.")
            error_message = error_message + "\n \n" + applicants_error
            valid = False

        if not self.is_representative:
            if not self.__check_main_age_applicant() and self.application.app_type != 3:
                self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
                applicants_error = self.tr("In capable person should not be main.")
                error_message = error_message + "\n \n" + applicants_error
                valid = False
        if self.is_representative:
            if self.legal_rep_twidget.rowCount() == 0:
                self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
                applicants_error = self.tr("Please enter representative.")
                error_message = error_message + "\n \n" + applicants_error
                valid = False

        if not self.__check_main_applicant():
            self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            applicants_error = self.tr("Exactly one main applicant has to be defined.")
            error_message = error_message + "\n \n" + applicants_error
            valid = False

        if not self.__check_main_new_right_holder() and self.application_type_cbox.itemData(self.application_type_cbox.currentIndex()) == 7:
            self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            applicants_error = self.tr("Exactly one main new right holder has to be defined.")
            error_message = error_message + "\n \n" + applicants_error
            valid = False

        if not self.__check_main_remaining_ownership() and self.application_type_cbox.itemData(self.application_type_cbox.currentIndex()) == 2:
            self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            applicants_error = self.tr("Exactly one main remaining ownership has to be defined.")
            error_message = error_message + "\n \n" + applicants_error
            valid = False

        if self.application.app_type == ApplicationType.giving_up_ownership:
            count = self.applicant_twidget.rowCount()
            # count = self.application.stakeholders.filter(CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE).count()
            if count < 2:
                applicants_error = self.tr("At least two applicants are required for this application type.")
                error_message = error_message + "\n \n" + applicants_error
                valid = False

        if self.application.app_type == ApplicationType.mortgage_possession:
            start_date = self.mortgage_start_date_edit.date()
            end_date = self.mortgage_end_date_edit.date()

            if start_date > end_date:
                self.mortgage_start_date_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                self.mortgage_end_date_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                error_mortgage_date = self.tr("The mortgage start date is later that the end date.")
                error_message = error_message + "\n \n" + error_mortgage_date
                valid = False

            if not self.__check_share(self.mortgage_twidget, MORTGAGE_SHARE):
                error_convert_share = self.tr("The share value is not a valid numerial. \n "
                                              "The share should be between 0.0 and 1.0 with one precision.")
                error_message = error_message + "\n \n" + error_convert_share
                self.mortgage_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
                valid = False

            if not self.__check_share_sum(self.mortgage_twidget, MORTGAGE_SHARE):
                error_share = self.tr("The sum of the mortgagee share is larger than 1.0 .")
                error_message = error_message + "\n \n" + error_share
                self.mortgage_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
                valid = False

            if not self.__check_parcel():
                error_share = self.tr("For this application type a parcel musst be assigned.")
                error_message = error_message + "\n \n" + error_share
                self.parcel_edit.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
                valid = False

        elif self.application.app_type == ApplicationType.change_ownership \
                or self.application.app_type == ApplicationType.transfer_possession_right \
                or self.application.app_type == ApplicationType.possess_split \
                or self.application.app_type == ApplicationType.encroachment \
                or self.application.app_type == ApplicationType.possession_right_use_right:

            if not self.__check_share(self.new_right_holders_twidget, NEW_RIGHT_HOLDER_SHARE) \
                    or not self.__check_share(self.old_right_holders_twidget, OLD_RIGHT_HOLDER_SHARE):

                self.new_right_holders_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
                self.old_right_holders_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
                error_convert_share = self.tr("The share value is not a valid numerial. \n "
                                              "The share should be between 0.0 and 1.0 with one precision.")
                error_message = error_message + "\n \n" + error_convert_share
                valid = False

            if not self.__check_share_old_new_right_holder():
                self.new_right_holders_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
                self.old_right_holders_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
                error_share = self.tr("The sum of the old and new right holders is not equal .")
                error_message = error_message + "\n \n" + error_share
                valid = False

        elif self.application.app_type == ApplicationType.change_ownership:

            if self.application.stakeholders.count() < 2:
                self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
                error_share = self.tr("At least two applicants have to be added. ")
                error_message = error_message + "\n \n" + error_share
                valid = False

        # elif self.application.app_type == ApplicationType.buisness_from_state \
        #     or self.application.app_type == ApplicationType.possession_right_use_right:
        #     if not self.__check_parcel():
        #         error_share = self.tr("For this application type a parcel musst be assigned.")
        #         error_message = error_message + "\n \n" + error_share
        #         self.mortgage_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
        #         valid = False

        if not self.__check_share(self.applicant_twidget, APPLICANT_SHARE):

            self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            error_convert_share = self.tr("The share value is not a valid numerial. "
                                          "\n The share should be between 0.0 and 1.0 with one precision.")
            error_message = error_message + "\n \n" + error_convert_share
            valid = False

        if not self.__check_share_sum(self.applicant_twidget, APPLICANT_SHARE):
            self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            error_share = self.tr("The sum of the applicants share is larger than 1.0 .")
            error_message = error_message + "\n \n" + error_share
            valid = False

        if not self.__check_parcel_app_type():
            error_share = self.tr("For this application connect to a parcel.")
            error_message = error_message + "\n \n" + error_share
            self.mortgage_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            valid = False

        # if not self.__check_app_type2_record_status():
        #     error_share = self.tr("For this parcel connect to ownership record.")
        #     error_message = error_message + "\n \n" + error_share
        #     self.mortgage_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
        #     valid = False

        return valid, error_message

    def __check_app_type2_record_status(self):

        try:
            record_status = self.session.query(CtOwnershipRecord)\
                .join(CtRecordApplicationRole, CtOwnershipRecord.record_no == CtRecordApplicationRole.record)\
                .join(CtApplication, CtRecordApplicationRole.application == CtApplication.app_no)\
                .filter(CtApplication.parcel == self.parcel_edit.text()).all()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        num_rows = self.application_status_twidget.rowCount()
        for row in range(num_rows):
            for status in record_status:
                status_item = self.application_status_twidget.item(row, 0)
                status_data = status_item.data(Qt.UserRole)
                if status_data >= 5 and status.status != 30:
                    return False
        return True

    def __check_parcel_app_type(self):

        num_rows = self.application_status_twidget.rowCount()
        for row in range(num_rows):
            status_item = self.application_status_twidget.item(row, 0)
            status_data = status_item.data(Qt.UserRole)
            if status_data >= 5 and self.parcel_edit.text() == "" and status_data != 2 and status_data != 8:
                return False
        return True

    def __check_age_applicants(self, person_id):

        if self.person.type == 10 or self.person.type == 20:
            self.is_age_18 = None
            today = date.today()
            t_y = today.year
            t_m = today.month
            t_d = today.day
            person = self.session.query(BsPerson).filter(BsPerson.person_id == person_id).one()

            birthday = person.date_of_birth
            if not birthday:
                return True
            b_y = int(birthday.year)
            b_m = int(birthday.month)
            b_d = int(birthday.day)
            age_y = int(t_y) - int(b_y)
            if age_y == 18:
                age_m = t_m - b_m
                if age_m == 0:
                    age_d = int(b_d) - int(t_d)
                    if age_d == 0:
                        self.is_age_18 = True
                    elif age_d > 0:
                        self.is_age_18 = False
                    else:
                        self.is_age_18 = True
                elif age_m > 0:
                    self.is_age_18 = True
                else:
                    self.is_age_18 = False
            elif age_y > 18:
                self.is_age_18 = True
            elif age_y < 18:
                self.is_age_18 = False

            if self.is_age_18 == True:
                return True
            else:
                return False

    def __check_main_capable_applicant(self):

        count = 0
        for row in range(self.applicant_twidget.rowCount()):
            item_main = self.applicant_twidget.item(row, APPLICANT_MAIN)
            if item_main.checkState() == Qt.Checked:
                person_id = item_main.data(Qt.UserRole)
                person = self.session.query(BsPerson).filter(BsPerson.person_id == person_id).one()
                if person.type == 20:
                    return True
                else:
                    return False
                count += 1

        if count <> 1:
            return False
        else:
            return True

    def __check_main_age_applicant(self):

        count = 0
        for row in range(self.applicant_twidget.rowCount()):
            item_main = self.applicant_twidget.item(row, APPLICANT_MAIN)
            if item_main.checkState() == Qt.Checked:
                person_id = item_main.data(Qt.UserRole)
                person = self.session.query(BsPerson).filter(BsPerson.person_id == person_id).one()
                if not self.__check_age_applicants(person_id) and person.type == 20:
                    return False
                count += 1

        if count <> 1:
            return False
        else:
            return True

    def __check_share_age_applicants(self):

        sum_share = Decimal(0.0)

        for row in range(self.applicant_twidget.rowCount()):
            item_share = self.applicant_twidget.item(row, APPLICANT_SHARE)
            item_main = self.applicant_twidget.item(row, APPLICANT_MAIN)
            person_id = item_main.data(Qt.UserRole)
            person = self.session.query(BsPerson).filter(BsPerson.person_id == person_id).one()
            if not self.__check_age_applicants(person_id) and person.type == 20:
                sum_share = sum_share + Decimal(item_share.text())
                if sum_share != Decimal(0.0):
                    return False
        return True

    def __check_share_applicants(self):

        sum_share = Decimal(0.0)

        for row in range(self.applicant_twidget.rowCount()):
            item_share = self.applicant_twidget.item(row, APPLICANT_SHARE)
            sum_share = sum_share + Decimal(item_share.text())

        if sum_share != Decimal(1.0):
            return False

        return True

    def __check_main_applicant(self):

        count = 0
        for row in range(self.applicant_twidget.rowCount()):
            item_main = self.applicant_twidget.item(row, APPLICANT_MAIN)
            if item_main.checkState() == Qt.Checked:
                count += 1

        if count <> 1:
            return False
        else:
            return True

    def __check_main_new_right_holder(self):

        count = 0
        for row in range(self.new_right_holders_twidget.rowCount()):
            item_main = self.new_right_holders_twidget.item(row, NEW_RIGHT_HOLDER_MAIN)
            if item_main.checkState() == Qt.Checked:
                count += 1

        if count <> 1:
            return False
        else:
            return True

    def __check_main_remaining_ownership(self):

        count = 0
        for row in range(self.owners_remaining_twidget.rowCount()):
            item_main = self.owners_remaining_twidget.item(row, NEW_RIGHT_HOLDER_MAIN)
            if item_main.checkState() == Qt.Checked:
                count += 1

        if count <> 1:
            return False
        else:
            return True

    def __check_share_old_new_right_holder(self):

        old_share_all = 0

        for row in range(self.new_right_holders_twidget.rowCount()):
            item_share = self.new_right_holders_twidget.item(row, NEW_RIGHT_HOLDER_SHARE)
            share = Decimal(item_share.text())

            old_share_all = old_share_all + share

        new_share = 0

        for row in range(self.old_right_holders_twidget.rowCount()):
            item_share = self.old_right_holders_twidget.item(row, OLD_RIGHT_HOLDER_SHARE)
            share = Decimal(item_share.text())

            new_share = new_share + share

        if new_share != old_share_all:
            return False
        else:
            return True

    def __check_share(self, twidget, share_column):

        for row in range(twidget.rowCount()):
            item_share = twidget.item(row, share_column)

            try:
                Decimal(item_share.text())
            except ValueError:
                return False

        return True

    def __check_share_sum(self, twidget, column):

        share_all = 0

        for row in range(twidget.rowCount()):
            item_share = twidget.item(row, column)
            try:
                share = Decimal(item_share.text())
            except ValueError:
                return False

            share_all = share_all + share

        if share_all > Decimal(1.0):
            return False
        else:
            return True

    def __check_parcel(self):

        if self.parcel_edit.text() == "":
            return False
        return True

    def __remove_style_sheet(self):

        dialog_style = self.styleSheet()
        self.application_num_middle_edit.setStyleSheet(dialog_style)
        self.application_type_cbox.setStyleSheet(dialog_style)
        self.date_time_date.setStyleSheet(dialog_style)
        self.applicant_twidget.setStyleSheet(dialog_style)

    def __remove_document_items(self):

        if not self.documents_twidget:
            return

        while self.documents_twidget.rowCount() > 0:
            self.documents_twidget.removeRow(0)


    def __setup_records(self):

            try:
                relate_record_count = self.session.query(CtRecordApplicationRole.application) \
                                            .filter(CtRecordApplicationRole.application == self.application.app_no) \
                                            .filter(CtRecordApplicationRole.role == Constants.APPLICATION_ROLE_REFERS).count()

                create_record_count = self.session.query(CtRecordApplicationRole.application) \
                                        .filter(CtRecordApplicationRole.application == self.application.app_no) \
                                        .filter(CtRecordApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).count()

                cancel_record_count = self.session.query(CtRecordApplicationRole.application) \
                                        .filter(CtRecordApplicationRole.application == self.application.app_no) \
                                        .filter(CtRecordApplicationRole.role == Constants.APPLICATION_ROLE_CANCELS).count()

                if relate_record_count == 1:
                    record_app = self.session.query(CtRecordApplicationRole) \
                                    .filter(CtRecordApplicationRole.application == self.application.app_no) \
                                    .filter(CtRecordApplicationRole.role == Constants.APPLICATION_ROLE_REFERS).one()
                    self.relating_record_num_edit.setText(record_app.record_ref.record_no)
                    self.relating_accepted_record_edit.setText(record_app.record_ref.record_no)

                if create_record_count == 1:
                    record_app = self.session.query(CtRecordApplicationRole) \
                                    .filter(CtRecordApplicationRole.application == self.application.app_no) \
                                    .filter(CtRecordApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).one()
                    self.record_created_edit.setText(record_app.record_ref.record_no)

                if cancel_record_count == 1:
                    record_app = self.session.query(CtRecordApplicationRole) \
                                    .filter(CtRecordApplicationRole.application == self.application.app_no) \
                                    .filter(CtRecordApplicationRole.role == Constants.APPLICATION_ROLE_CANCELS).one()
                    self.record_cancelled_num_edit.setText(record_app.record_ref.record_no)
                    self.relating_contract_edit.setText(record_app.record_ref.record_no)
                    self.relating_accepted_record_edit.setText(record_app.record_ref.record_no)

            except SQLAlchemyError, e:
                raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __setup_contracts(self):

        try:

            relate_contract_count = self.session.query(CtContractApplicationRole.application) \
                                        .filter(CtContractApplicationRole.application == self.application.app_no) \
                                        .filter(CtContractApplicationRole.role == Constants.APPLICATION_ROLE_REFERS)\
                                        .count()

            create_contract_count = self.session.query(CtContractApplicationRole.application) \
                                        .filter(CtContractApplicationRole.application == self.application.app_no) \
                                        .filter(CtContractApplicationRole.role == Constants.APPLICATION_ROLE_CREATES)\
                                        .count()

            cancel_contract_count = self.session.query(CtContractApplicationRole.application) \
                                        .filter(CtContractApplicationRole.application == self.application.app_no) \
                                        .filter(CtContractApplicationRole.role == Constants.APPLICATION_ROLE_CANCELS)\
                                        .count()

            if create_contract_count == 1:
                contract_app = self.session.query(CtContractApplicationRole) \
                                    .filter(CtContractApplicationRole.application == self.application.app_no) \
                                    .filter(CtContractApplicationRole.role == Constants.APPLICATION_ROLE_CREATES)\
                                    .one()

                self.contract_created_edit.setText(contract_app.contract_ref.contract_no)

            if cancel_contract_count == 1:
                contract_app = self.session.query(CtContractApplicationRole) \
                                    .filter(CtContractApplicationRole.application == self.application.app_no) \
                                    .filter(CtContractApplicationRole.role == Constants.APPLICATION_ROLE_CANCELS)\
                                    .one()
                self.contract_cancelled_num_edit.setText(contract_app.contract_ref.contract_no)
                self.relating_contract_edit.setText(contract_app.contract_ref.contract_no)
                self.contract_to_be_cancelled_edit.setText(contract_app.contract_ref.contract_no)

            if relate_contract_count == 1:
                relate_contract = self.session.query(CtContractApplicationRole) \
                                        .filter(CtContractApplicationRole.application == self.application.app_no) \
                                        .filter(CtContractApplicationRole.role == Constants.APPLICATION_ROLE_REFERS)\
                                        .one()
                self.relating_contract_edit.setText(relate_contract.contract_ref.contract_no)

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    @pyqtSlot()
    def on_search_parcel_number_button_clicked(self):

        if self.search_parcel_num_edit.text() == "":
            return

        parcel_id = self.search_parcel_num_edit.text()

        try:
            parcel_count = self.session.query(CaTmpParcel.parcel_id).filter_by(parcel_id=parcel_id).count()
            if parcel_count == 0:
                parcel_count = self.session.query(CaParcel.parcel_id).filter_by(parcel_id=parcel_id).count()
                if parcel_count == 0:
                    PluginUtils.show_error(self, self.tr("No Parcel found"),
                                    self.tr("The parcel number {0} could not be found within the current working soum.")
                                    .format(parcel_id))
                    return
                else:
                    parcel = self.session.query(CaParcel.parcel_id).filter_by(parcel_id=parcel_id).one()
                    status_count = self.session.query(CtApplicationStatus).\
                        join(CtApplication, CtApplicationStatus.application == CtApplication.app_no).\
                        filter(CtApplicationStatus.status > 6).\
                        filter(CtApplication.parcel == parcel_id).count()
                    if status_count == 0:
                        PluginUtils.show_message(self, self.tr('delete please'), self.tr('Delete please the parcel. This parcel is not referenced to any applications.'))
                        return
                    else:
                        contract_count = self.session.query(CtContract).\
                            join(CtContractApplicationRole, CtContract.contract_no == CtContractApplicationRole.contract).\
                            join(CtApplication, CtContractApplicationRole.application == CtApplication.app_no).\
                            filter(CtApplication.parcel == parcel_id).count()
                        own_count = self.session.query(CtOwnershipRecord).\
                            join(CtRecordApplicationRole, CtOwnershipRecord.record_no == CtRecordApplicationRole.record).\
                            join(CtApplication, CtRecordApplicationRole.application == CtApplication.app_no).\
                            filter(CtApplication.parcel == parcel_id).count()

                        # if contract_count != 0:
                        #     contract = self.session.query(CtContract.contract_no,func.max(CtContract.cancellation_date).label("max_row")).\
                        #     join(CtContractApplicationRole, CtContract.contract_no == CtContractApplicationRole.contract).\
                        #     join(CtApplication, CtContractApplicationRole.application == CtApplication.app_no).\
                        #     filter(CtApplication.parcel == parcel_id).group_by(CtContract.contract_no).order_by(CtContract.cancellation_date)
                        #     contract_no = None
                        #     contract_cancel_date = None
                        #     for con in contract:
                        #         contract_no = con.contract_no
                        #         contract_cancel_date = con.max_row
                        # if own_count != 0:
                        #     ownership = self.session.query(CtOwnershipRecord.record_no,func.max(CtOwnershipRecord.cancellation_date).label("max_row")).\
                        #     join(CtRecordApplicationRole, CtOwnershipRecord.record_no == CtRecordApplicationRole.record).\
                        #     join(CtApplication, CtRecordApplicationRole.application == CtApplication.app_no).\
                        #     filter(CtApplication.parcel == parcel_id).group_by(CtOwnershipRecord.record_no).order_by(CtOwnershipRecord.cancellation_date)
                        #     record_no = None
                        #     record_cancel_date = None
                        #     for rec in ownership:
                        #         record_no = rec.record_no
                        #         record_cancel_date = rec.max_row

                        if contract_count == 0 and own_count == 0:
                            PluginUtils.show_message(self, self.tr("contract"), self.tr("Decision is approved but contract/ownership record is not yet created!"))
                            return

            else:
                self.is_tmp_parcel = True

            if self.is_tmp_parcel:
                parcel = self.session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == parcel_id).one()
                case_id = parcel.maintenance_case
                maintenance_case = self.session.query(CaMaintenanceCase).filter(CaMaintenanceCase.id == case_id).one()
                if maintenance_case.completion_date is None:
                    PluginUtils.show_message(self, self.tr("Maintenance Error"), self.tr("Cadastre update must be complete"))
                    return
            else:
                parcel = self.session.query(CaParcel.parcel_id).filter_by(parcel_id=parcel_id).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        self.found_parcel_number_edit.setText(parcel.parcel_id)

    @pyqtSlot()
    def on_search_decision_button_clicked(self):

        decision_id = self.search_decision_number_edit.text()
        if decision_id == "":
            return

        try:
            decision = self.session.query(CtDecision.decision_no).filter_by(decision_no=decision_id).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        self.found_decision_edit.setText(decision.decision_no)

    @pyqtSlot()
    def on_accept_decision_button_clicked(self):

        self.assigned_desicion_edit.setText(self.found_decision_edit.text())

    @pyqtSlot()
    def on_accept_parcel_number_button_clicked(self):

        parcel_id = self.found_parcel_number_edit.text()

        person_id = ""

        if parcel_id == "":
            return
        if self.application.app_type == ApplicationType.mortgage_possession:
            for row in range(self.applicant_twidget.rowCount()):
                    person_id  = self.applicant_twidget.item(row, APPLICANT_PERSON_ID).text()

                    person_fee_count = self.session.query(CtFee)\
                        .join(CtContractApplicationRole, CtFee.contract == CtContractApplicationRole.contract)\
                        .join(CtApplication,CtContractApplicationRole.application == CtApplication.app_no)\
                        .filter(CtFee.person == person_id)\
                        .filter(CtApplication.parcel == parcel_id).count()

                    if person_fee_count == 0:
                        PluginUtils.show_error(self, self.tr("Error"),self.tr("This parcel wrong."))
                        return

        num_rows = self.applicant_twidget.rowCount()
        for row in range(num_rows):
            person = self.applicant_twidget.item(row, 2)
            person_id = person.text()

        try:
            app_case_count = self.session.query(MaintenanceSearch).\
                filter(MaintenanceSearch.parcel == parcel_id).\
                filter(MaintenanceSearch.completion_date == None).count()
            if app_case_count > 0:
                PluginUtils.show_message(self, self.tr("Maintenance error"), self.tr("This application process cadastre changing!!!"))
                return

            current_app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())

            if current_app_type == ApplicationType.giving_up_ownership:

                applicants = self.session.query(CtApplicationPersonRole)\
                    .join(CtApplication, CtApplicationPersonRole.application == CtApplication.app_no)\
                    .join(CtRecordApplicationRole, CtApplication.app_no == CtRecordApplicationRole.application)\
                    .join(CtOwnershipRecord, CtRecordApplicationRole.record == CtOwnershipRecord.record_no)\
                    .filter(CtOwnershipRecord.status == 30)\
                    .filter(CtApplication.parcel == parcel_id)\
                    .filter(CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE).all()
                if self.application.app_type == 2:

                    applicants = self.session.query(CtApplicationPersonRole)\
                    .join(CtApplication, CtApplicationPersonRole.application == CtApplication.app_no)\
                    .join(CtRecordApplicationRole, CtApplication.app_no == CtRecordApplicationRole.application)\
                    .join(CtOwnershipRecord, CtRecordApplicationRole.record == CtOwnershipRecord.record_no)\
                    .filter(CtOwnershipRecord.status == 30)\
                    .filter(CtApplication.parcel == parcel_id)\
                    .filter(CtRecordApplicationRole.role == Constants.REMAINING_OWNER_CODE)\
                    .filter(CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE).all()

                app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())
                for applicant in applicants:
                    person = self.session.query(BsPerson).filter_by(person_id=applicant.person).one()

                    applicants_count = self.session.query(CtApplicationPersonRole)\
                        .join(CtApplication, CtApplicationPersonRole.application == CtApplication.app_no)\
                        .filter(CtApplication.parcel == parcel_id)\
                        .filter(CtApplication.app_type == 2)\
                        .filter(CtApplicationPersonRole.person == person.person_id)\
                        .filter(CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE).count()
                    if applicants_count > 0:
                        PluginUtils.show_message(self, self.tr("Application Duplicated"), self.tr("This application is already registered"))
                        return

                    role_ref = self.session.query(ClPersonRole).filter_by(
                            code=Constants.APPLICANT_ROLE_CODE).one()

                    if app_type == ApplicationType.giving_up_ownership:
                        additional_role = self.session.query(ClPersonRole)\
                            .filter_by(code=Constants.REMAINING_OWNER_CODE).one()
                        person_role_code = Constants.REMAINING_OWNER_CODE
                    elif app_type == ApplicationType.transfer_possession_right\
                            or app_type == ApplicationType.change_ownership \
                            or app_type == ApplicationType.possess_split \
                            or app_type == ApplicationType.encroachment \
                            or app_type == ApplicationType.possession_right_use_right:
                        additional_role = self.session.query(ClPersonRole)\
                            .filter_by(code=Constants.OLD_RIGHT_HOLDER_CODE).one()
                        person_role_code = Constants.OLD_RIGHT_HOLDER_CODE

                    app_person_role = CtApplicationPersonRole()
                    app_person_role.application = self.current_application_no()
                    app_person_role.share = applicant.share
                    app_person_role.role_ref = role_ref
                    app_person_role.role = Constants.APPLICANT_ROLE_CODE
                    app_person_role.person = person.person_id
                    app_person_role.person_ref = person
                    app_person_role.main_applicant = False
                    #self.session.flush()

                    if additional_role is not None and person_role_code is not None:
                        if app_type == ApplicationType.giving_up_ownership \
                                or app_type == ApplicationType.transfer_possession_right\
                                or app_type == ApplicationType.change_ownership \
                                or app_type == ApplicationType.possess_split \
                                or app_type == ApplicationType.encroachment \
                                or app_type == ApplicationType.possession_right_use_right:

                            app_person_role_remain = CtApplicationPersonRole()
                            app_person_role_remain.application = self.application.app_no
                            app_person_role_remain.share = Decimal(0.0)
                            app_person_role_remain.role_ref = additional_role
                            app_person_role_remain.role = person_role_code
                            app_person_role_remain.person = person.person_id
                            app_person_role_remain.person_ref = person
                            app_person_role_remain.main_applicant = False
                            #self.session.flush()

                            self.application.stakeholders.append(app_person_role)

                            if app_type == ApplicationType.giving_up_ownership  \
                                or app_type == ApplicationType.transfer_possession_right\
                                or app_type == ApplicationType.change_ownership \
                                or app_type == ApplicationType.possess_split \
                                    or app_type == ApplicationType.encroachment \
                                    or app_type == ApplicationType.possession_right_use_right:

                                self.application.stakeholders.append(app_person_role_remain)

                    self.__add_applicant_item(applicant)
                    self.__add_co_ownership_item(applicant, Constants.REMAINING_OWNER_CODE)

            if current_app_type != ApplicationType.extension_possession and current_app_type != ApplicationType.mortgage_possession and current_app_type != ApplicationType.possession_right_use_right:

                used_parcel_count = self.session.query(CtApplication)\
                    .join(CtContractApplicationRole, CtApplication.app_no == CtContractApplicationRole.application)\
                    .join(CtContract, CtContractApplicationRole.contract == CtContract.contract_no)\
                    .filter(CtContract.status != Constants.CONTRACT_STATUS_CANCELLED)\
                    .filter(CtApplication.parcel == parcel_id).count()
                if used_parcel_count == 0:
                    used_parcel_count = self.session.query(CtApplication)\
                        .join(CtRecordApplicationRole, CtApplication.app_no == CtRecordApplicationRole.application)\
                        .join(CtOwnershipRecord, CtRecordApplicationRole.record == CtOwnershipRecord.record_no)\
                        .filter(CtOwnershipRecord.status != Constants.RECORD_STATUS_CANCELLED)\
                        .filter(CtApplication.parcel == parcel_id).count()

                if used_parcel_count > 0:
                    PluginUtils.show_message(self, self.tr("Parcel Duplicated"), self.tr("This parcel is already connected to person"))
                    return

            # if current_app_type == ApplicationType.extension_possession:
            #     applicants = self.session.query(CtApplicationPersonRole) \
            #         .join(CtApplication, CtApplicationPersonRole.application == CtApplication.app_no) \
            #         .join(CtContractApplicationRole, CtApplication.app_no == CtContractApplicationRole.application) \
            #         .join(CtContract, CtContractApplicationRole.contract == CtContract.contract_no) \
            #         .filter(CtContract.status == Constants.CONTRACT_STATUS_CANCELLED) \
            #         .filter(CtApplication.parcel == parcel_id) \
            #         .filter(CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE).all()
            #
            #     for applicant in applicants:
            #         person = self.session.query(BsPerson).filter_by(person_id=applicant.person).one()
            #
            #         role_ref = self.session.query(ClPersonRole).filter_by(
            #             code=Constants.APPLICANT_ROLE_CODE).one()
            #
            #         app_person_role = CtApplicationPersonRole()
            #         app_person_role.application = self.current_application_no()
            #         app_person_role.share = applicant.share
            #         app_person_role.role_ref = role_ref
            #         app_person_role.role = Constants.APPLICANT_ROLE_CODE
            #         app_person_role.person = person.person_id
            #         app_person_role.person_ref = person
            #         app_person_role.main_applicant = False
            #
            #         self.application.stakeholders.append(app_person_role)
            #         self.__add_applicant_item(applicant)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        parcel_count = self.session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == parcel_id).count()
        if parcel_count != 0:
            self.is_tmp_parcel = True
        if self.is_tmp_parcel:
            parcel = self.session.query(CaTmpParcel.parcel_id, CaTmpParcel.area_m2, CaTmpParcel.landuse, CaTmpParcel.geometry).filter_by(parcel_id=parcel_id).one()
            self.application.tmp_parcel = parcel_id
        else:
            parcel = self.session.query(CaParcel.parcel_id, CaParcel.area_m2, CaParcel.landuse, CaParcel.geometry).filter_by(parcel_id=parcel_id).one()
            self.application.parcel = parcel_id

        if current_app_type == ApplicationType.encroachment:

            other_apps = self.session.query(CtApplication). \
                join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application). \
                join(CtApplicationStatus, CtApplication.app_no == CtApplicationStatus.application). \
                filter(CtApplicationPersonRole.person == person_id). \
                filter(CtApplication.app_type == ApplicationType.encroachment). \
                filter(CtApplicationStatus.status <= 5).all()
            other_area = 0
            for app in other_apps:
                if app.parcel:
                    parcel_count = self.session.query(CaTmpParcel.parcel_id == app.parcel).count()
                    if parcel_count == 1:
                        parcel = self.session.query(CaTmpParcel.parcel_id == app.parcel).one()
                        other_area = other_area + parcel.area_m2
            base_tax_and_price_count = self.session.query(SetBaseTaxAndPrice). \
                filter(SetTaxAndPriceZone.geometry.ST_Contains(parcel.geometry)). \
                filter(parcel.parcel_id == parcel_id). \
                filter(SetBaseTaxAndPrice.tax_zone == SetTaxAndPriceZone.zone_id). \
                filter(SetBaseTaxAndPrice.landuse == parcel.landuse). \
                count()

            if base_tax_and_price_count == 1:

                base_tax_and_price = self.session.query(SetBaseTaxAndPrice). \
                    filter(SetTaxAndPriceZone.geometry.ST_Contains(parcel.geometry)). \
                    filter(parcel.parcel_id == parcel_id). \
                    filter(SetBaseTaxAndPrice.tax_zone == SetTaxAndPriceZone.zone_id). \
                    filter(SetBaseTaxAndPrice.landuse == parcel.landuse). \
                    one()
                subsidized_area = base_tax_and_price.subsidized_area
                limit_area = subsidized_area - (parcel.area_m2 + other_area)
                if limit_area < 0:
                    PluginUtils.show_error(self, self.tr("Area Limit"),
                                           self.tr("The application limit parcel area."))
                    return

        self.parcel_edit.setText(parcel.parcel_id)
        self.parcel_area_edit.setText(str(parcel.area_m2))
        self.found_parcel_number_edit.setText("")\

        tax_zone_count = self.session.query(SetTaxAndPriceZone)\
            .filter(SetTaxAndPriceZone.geometry.ST_Contains(parcel.geometry))\
            .filter(and_(SetTaxAndPriceZone.zone_no != 50,SetTaxAndPriceZone.zone_no != 60,SetTaxAndPriceZone.zone_no != 70,SetTaxAndPriceZone.zone_no != 80)).count()

        if tax_zone_count != 0:
            tax_zone = self.session.query(SetTaxAndPriceZone)\
                .filter(SetTaxAndPriceZone.geometry.ST_Contains(parcel.geometry))\
                .filter(and_(SetTaxAndPriceZone.zone_no != 50,SetTaxAndPriceZone.zone_no != 60,SetTaxAndPriceZone.zone_no != 70,SetTaxAndPriceZone.zone_no != 80)).one()

            price_area_count = self.session.query(SetBaseTaxAndPrice).filter(SetBaseTaxAndPrice.landuse == parcel.landuse)\
                        .filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id)\
                        .filter(or_(SetBaseTaxAndPrice.landuse == 2204,SetBaseTaxAndPrice.landuse == 2205,SetBaseTaxAndPrice.landuse == 2206)).count()
            if price_area_count != 0:
                price_area = self.session.query(SetBaseTaxAndPrice).filter(SetBaseTaxAndPrice.landuse == parcel.landuse)\
                            .filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id)\
                            .filter(or_(SetBaseTaxAndPrice.landuse == 2204,SetBaseTaxAndPrice.landuse == 2205,SetBaseTaxAndPrice.landuse == 2206)).one()

                subsidized_area = 0
                if price_area.subsidized_area is not None:
                    subsidized_area = price_area.subsidized_area

                excess_area = round((parcel.area_m2))-round((subsidized_area))

                if excess_area > 0:
                    self.excess_area_spin_box.setValue(excess_area)
                    self.price_to_be_paid_spin_box.setValue(float(price_area.base_value_per_m2) * float(excess_area))

        self.accept_parcel_number_button.setEnabled(False)

    @pyqtSlot()
    def on_accept_relating_contract_button_clicked(self):

        try:
            con_app = CtContractApplicationRole()
            con_app.application = self.application.app_no
            con_app.contract = self.found_contract_number_edit.text()
            application_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())
            if application_type == ApplicationType.your_request:
                con_app.role = Constants.APPLICATION_ROLE_CANCELS
            elif application_type == ApplicationType.court_decision:
                con_app.role = Constants.APPLICATION_ROLE_CANCELS
            else:
                con_app.role = Constants.APPLICATION_ROLE_REFERS

            self.session.add(con_app)
            self.relating_contract_edit.setText(self.found_contract_number_edit.text())

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    @pyqtSlot()
    def on_accept_relating_record_button_clicked(self):

        try:
            con_app = CtRecordApplicationRole()
            con_app.application = self.application.app_no
            con_app.record = self.relating_record_num_edit.text()
            application_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())
            if application_type == ApplicationType.your_request:
                con_app.role = Constants.APPLICATION_ROLE_CANCELS
            elif application_type == ApplicationType.court_decision:
                con_app.role = Constants.APPLICATION_ROLE_CANCELS
            elif application_type == ApplicationType.encroachment:
                con_app.role = Constants.APPLICATION_ROLE_CANCELS
            else:
                con_app.role = Constants.APPLICATION_ROLE_REFERS

            self.session.add(con_app)
            self.relating_accepted_record_edit.setText(self.relating_record_num_edit.text())

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"),
                                   self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    @pyqtSlot(int)
    def on_applicant_documents_cbox_currentIndexChanged(self, index):

        if not self.documents_twidget:
            return

        if self.updating:
            return

        # self.__update_documents_twidget()

    def __update_documents_twidget(self):

        self.__remove_document_items()

        current_app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())

        try:
            required_doc_types = self.session.query(SetApplicationTypeDocumentRole).filter_by(
                application_type=current_app_type)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        person_id = self.applicant_documents_cbox.itemData(self.applicant_documents_cbox.currentIndex())

        for docType in required_doc_types:
            item_provided = QTableWidgetItem()
            item_provided.setCheckState(Qt.Unchecked)

            item_doc_type = QTableWidgetItem(docType.document_role_ref.description)
            item_doc_type.setData(Qt.UserRole, docType.document_role_ref.code)
            item_doc_type.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

            item_name = QTableWidgetItem("")
            item_name.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

            item_open = QTableWidgetItem("")
            item_remove = QTableWidgetItem("")
            item_view = QTableWidgetItem("")
            row = self.documents_twidget.rowCount()

            self.documents_twidget.insertRow(row)
            self.documents_twidget.setItem(row, DOC_PROVIDED_COLUMN, item_provided)
            self.documents_twidget.setItem(row, DOC_FILE_TYPE_COLUMN, item_doc_type)
            self.documents_twidget.setItem(row, DOC_FILE_NAME_COLUMN, item_name)
            self.documents_twidget.setItem(row, DOC_OPEN_FILE_COLUMN, item_open)
            self.documents_twidget.setItem(row, DOC_DELETE_COLUMN, item_remove)
            self.documents_twidget.setItem(row, DOC_VIEW_COLUMN, item_view)

        app_docs = self.session.query(CtApplicationDocument.role, CtApplicationDocument.person, CtApplicationDocument.document)\
            .filter(CtApplicationDocument.application_ref == self.application).all()

        for app_document in app_docs:
            for i in range(self.documents_twidget.rowCount()):
                doc_type_item = self.documents_twidget.item(i, DOC_FILE_TYPE_COLUMN)
                if app_document.role == doc_type_item.data(Qt.UserRole) and app_document.person == person_id:
                    try:
                        item_name = self.documents_twidget.item(i, DOC_FILE_NAME_COLUMN)
                        document = self.session.query(CtDocument.name).filter(CtDocument.id == app_document.document).one()
                        item_name.setText(document.name)

                        item_provided = self.documents_twidget.item(i, DOC_PROVIDED_COLUMN)
                        item_provided.setCheckState(Qt.Checked)

                        item_open = self.documents_twidget.item(i, DOC_OPEN_FILE_COLUMN)

                        self.documents_twidget.setItem(i, 0, item_provided)
                        self.documents_twidget.setItem(i, 2, item_name)
                        self.documents_twidget.setItem(i, 3, item_open)

                    except SQLAlchemyError, e:
                        PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                        return

    def __update_documents_file_twidget(self):

        current_app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())
        try:
            required_doc_types = self.session.query(SetApplicationTypeDocumentRole).filter_by(
                application_type=current_app_type)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        archive_app_path = FilePath.app_file_path()+'/'+ self.application.app_no
        if not os.path.exists(archive_app_path):
            os.makedirs(archive_app_path)

        for file in os.listdir(archive_app_path):
            os.listdir(archive_app_path)
            if file.endswith(".pdf"):
                doc_type = file[18:-4]
                file_name = file
                app_no = file[:17]

                for i in range(self.documents_twidget.rowCount()):
                    doc_type_item = self.documents_twidget.item(i, DOC_FILE_TYPE_COLUMN)

                    doc_type_code = str(doc_type_item.data(Qt.UserRole))

                    if len(str(doc_type_item.data(Qt.UserRole))) == 1:
                        doc_type_code = '0'+ str(doc_type_item.data(Qt.UserRole))
                    if len(doc_type) == 1:
                        doc_type = '0' + doc_type
                    if doc_type == doc_type_code and self.current_application_no() == app_no:
                        item_name = self.documents_twidget.item(i, DOC_FILE_NAME_COLUMN)
                        item_name.setText(file_name)

                        item_provided = self.documents_twidget.item(i, DOC_PROVIDED_COLUMN)
                        item_provided.setCheckState(Qt.Checked)

                        item_open = self.documents_twidget.item(i, DOC_OPEN_FILE_COLUMN)

                        self.documents_twidget.setItem(i, 0, item_provided)
                        self.documents_twidget.setItem(i, 2, item_name)
                        self.documents_twidget.setItem(i, 3, item_open)

    @pyqtSlot()
    def on_load_doc_button_clicked(self):

        # self.documents_twidget.clear()
        self.__remove_document_items()
        current_app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())
        try:
            required_doc_types = self.session.query(SetApplicationTypeDocumentRole).filter_by(
                application_type=current_app_type)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        for docType in required_doc_types:
            item_provided = QTableWidgetItem()
            item_provided.setCheckState(Qt.Unchecked)

            item_doc_type = QTableWidgetItem(docType.document_role_ref.description)
            item_doc_type.setData(Qt.UserRole, docType.document_role_ref.code)
            item_doc_type.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

            item_name = QTableWidgetItem("")
            item_name.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

            item_open = QTableWidgetItem("")
            item_remove = QTableWidgetItem("")
            item_view = QTableWidgetItem("")
            row = self.documents_twidget.rowCount()

            self.documents_twidget.insertRow(row)
            self.documents_twidget.setItem(row, DOC_PROVIDED_COLUMN, item_provided)
            self.documents_twidget.setItem(row, DOC_FILE_TYPE_COLUMN, item_doc_type)
            self.documents_twidget.setItem(row, DOC_FILE_NAME_COLUMN, item_name)
            self.documents_twidget.setItem(row, DOC_OPEN_FILE_COLUMN, item_open)
            self.documents_twidget.setItem(row, DOC_DELETE_COLUMN, item_remove)
            self.documents_twidget.setItem(row, DOC_VIEW_COLUMN, item_view)

        self.__update_documents_file_twidget()


    @pyqtSlot()
    def on_unassign_button_clicked(self):

        self.parcel_edit.setText("")
        self.parcel_area_edit.setText("")
        self.application.parcel = None
        self.application.tmp_parcel = None
        self.accept_parcel_number_button.setEnabled(True)

    @pyqtSlot()
    def on_application_twidget_itemDropped(self):

        application_type_code = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())
        selection_contains_invalid_persons = False
        selection_invalid_persons = False
        invalid_type = ""
        double_entry = False
        person_name = ""
        mortgagee_found = False

        for item in self.navigator.person_results_twidget.selectedItems():

            try:
                person = self.session.query(BsPerson).filter_by(person_id=item.data(Qt.UserRole)).one()

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return
            if application_type_code == ApplicationType.transfer_possession_right:
                if not self.__is_active_contract(person.person_id):
                    PluginUtils.show_error(self, self.tr("Invalid Applicant"),
                                           self.tr("This applicant not active contract."))
                    return

            if application_type_code == ApplicationType.change_ownership:
                if not self.__is_active_record(person.person_id):
                    PluginUtils.show_error(self, self.tr("Invalid Applicant"),
                                           self.tr("This applicant not active owner record."))
                    return

            try:
                if application_type_code == 1:
                    giving_onwer_count = self.session.query(CtApplicationPersonRole.application)\
                        .join(CtApplicationStatus, CtApplicationPersonRole.application == CtApplicationStatus.application)\
                        .join(CtApplication, CtApplicationPersonRole.application == CtApplication.app_no)\
                        .filter(or_(CtApplication.app_type == 1,CtApplication.app_type == 2, CtApplication.app_type == 15))\
                        .filter(CtApplicationPersonRole.person == person.person_id) \
                        .filter(CtApplicationStatus.status >= 7) \
                        .filter(CtApplicationStatus.status != 8) \
                        .filter(CtApplicationPersonRole.role == 30).group_by(CtApplicationPersonRole.application).count()

                    remaining_onwer_count = self.session.query(CtApplicationPersonRole.application) \
                        .join(CtApplicationStatus,
                              CtApplicationPersonRole.application == CtApplicationStatus.application) \
                        .join(CtApplication, CtApplicationPersonRole.application == CtApplication.app_no) \
                        .filter(or_(CtApplication.app_type == 1,CtApplication.app_type == 2, CtApplication.app_type == 15)) \
                        .filter(CtApplicationPersonRole.person == person.person_id) \
                        .filter(CtApplicationStatus.status >= 7) \
                        .filter(CtApplicationStatus.status != 8) \
                        .filter(CtApplicationPersonRole.role == 40).group_by(
                        CtApplicationPersonRole.application).count()

                    first_owner_count = self.session.query(CtApplicationPersonRole.application) \
                        .join(CtApplicationStatus,
                              CtApplicationPersonRole.application == CtApplicationStatus.application) \
                        .join(CtApplication, CtApplicationPersonRole.application == CtApplication.app_no) \
                        .filter(or_(CtApplication.app_type == 1,CtApplication.app_type == 2, CtApplication.app_type == 15)) \
                        .filter(CtApplicationPersonRole.person == person.person_id) \
                        .filter(CtApplicationStatus.status >= 7) \
                        .filter(CtApplicationStatus.status != 8) \
                        .filter(CtApplicationPersonRole.role == 10).group_by(
                        CtApplicationPersonRole.application).count()
                    if first_owner_count > 0 and giving_onwer_count == 0 and remaining_onwer_count == 0:
                            PluginUtils.show_error(self, self.tr("Invalid Applicant"),
                                                   self.tr("Before acquiring land Twice do not own"))
                            return
                    if first_owner_count > 0 and giving_onwer_count == 0 and remaining_onwer_count > 0:
                            PluginUtils.show_error(self, self.tr("Invalid Applicant"),
                                                   self.tr("Before acquiring land Twice do not own"))
                            return
                    elif first_owner_count > 0 and giving_onwer_count > 0 and remaining_onwer_count > 0:
                        PluginUtils.show_error(self, self.tr("Invalid Applicant"),
                                            self.tr("Before acquiring land Twice do not own"))
                        return

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            #1st check if the person type is allowed for the application type
            #2cnd check if the applicant is already added
            #3rd check in case of app_type = 8 if the applicant is mortgagee

            if not self.__valid_applicant(application_type_code, person.type):
                selection_contains_invalid_persons = True
                invalid_type = person.type_ref.description

            if person.type == Constants.UNCAPABLE_PERSON_TYPE:
                selection_invalid_persons = True

            if self.__double_applicant(item.data(Qt.UserRole)):

                double_entry = True
                person_name = person.name + ", " + person.first_name

            app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())
            if app_type == ApplicationType.mortgage_possession:
                count = self.application.stakeholders.filter_by(person=person.person_id)\
                                        .filter_by(role=Constants.MORTGAGEE_ROLE_CODE).count()

                if count > 0:
                    mortgagee_found = True

        if selection_contains_invalid_persons:
            PluginUtils.show_error(self, self.tr("Invalid Applicant"),
                                self.tr("The applicant of the type {0} can't be added to an application of the type {1}.")
                                .format(unicode(invalid_type), unicode(self.application_type_cbox.currentText())))

        elif selection_invalid_persons:
            if (application_type_code == 5 or application_type_code == 7 or application_type_code == 14 or application_type_code == 15):
                message_box = QMessageBox()
                message_box.setText(self.tr("This person is not aplicable. Do you want to register for this person by legal representative ?"))

                yes_button = message_box.addButton(self.tr("Yes"), QMessageBox.ActionRole)
                message_box.addButton(self.tr("No"), QMessageBox.ActionRole)
                message_box.exec_()

                if message_box.clickedButton() == yes_button:
                    self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1,
                                                      self.legal_representative_tab, QIcon(),
                                                      self.tr("Legal Representative"))
                    self.is_representative = True
                    self.__copy_applicant_from_navigator()
            else:
                self.__copy_applicant_from_navigator()
        elif double_entry:
            PluginUtils.show_error(self, self.tr("Double Applicant"),
                                            self.tr("The applicant {0} is already added.").format(person_name))
        elif mortgagee_found:
            PluginUtils.show_error(self, self.tr("Mortgagee found"),
                                            self.tr("The applicant {0} is already mortgagee.").format(person_name))
        else:
            if app_type != 1:
                num_rows = self.application_status_twidget.rowCount()
                if num_rows > 1:
                    PluginUtils.show_error(self, self.tr("add applicant error"), self.tr("it will acceptable only applicatin status one."))
                    return
            self.__copy_applicant_from_navigator()

        if self.application.stakeholders.count() > 0:
            self.application_type_cbox.setEnabled(False)

    @pyqtSlot(int, int)
    def on_application_twidget_cellChanged(self, row, column):

        if column == APPLICANT_MAIN:
            changed_item = self.applicant_twidget.item(row, column)
            if changed_item.checkState() == Qt.Checked:

                for cu_row in range(self.applicant_twidget.rowCount()):
                    item = self.applicant_twidget.item(cu_row, column)
                    if item.checkState() == Qt.Checked and row != cu_row:

                        item.setCheckState(Qt.Unchecked)

    @pyqtSlot(int, int)
    def on_owners_remaining_twidget_cellChanged(self, row, column):

        if column == APPLICANT_MAIN:
            changed_item = self.owners_remaining_twidget.item(row, column)
            if changed_item.checkState() == Qt.Checked:

                for cu_row in range(self.owners_remaining_twidget.rowCount()):
                    item = self.owners_remaining_twidget.item(cu_row, column)
                    if item.checkState() == Qt.Checked and row != cu_row:

                        item.setCheckState(Qt.Unchecked)

        if column == APPLICANT_SHARE:

            item = self.applicant_twidget.item(row, APPLICANT_MAIN)
            item_share = self.applicant_twidget.item(row, APPLICANT_SHARE)

            person_id = item.data(Qt.UserRole)
            for applicant in self.application.stakeholders:
                if person_id == applicant.person_ref.person_id:
                    applicant.share = Decimal(item_share.text())

    @pyqtSlot()
    def on_drop_label_itemDropped(self):

        self.__copy_parcel_from_navigator()

    @pyqtSlot()
    def on_record_drop_label_itemDropped(self):

        self.__copy_record_from_navigator()

    @pyqtSlot()
    def on_contract_drop_label_itemDropped(self):

        self.__copy_contract_from_navigator()

        # if self.parcel_edit.text():
        #     self.__copy_contract_from_navigator()
        # else:
        #     PluginUtils.show_message(self, self.tr("Error"),
        #                              self.tr("Assign the parcel before adding the relating contract."))

    @pyqtSlot()
    def on_mortgage_twidget_itemDropped(self):

        self.__copy_mortgagee_from_navigator()

    @pyqtSlot()
    def on_legal_rep_twidget_itemDropped(self):

        self.__copy_legal_rep_from_navigator()

    @pyqtSlot()
    def on_new_right_holder_twidget_itemDropped(self):

        self.__copy_new_right_holder_from_navigator()

    @pyqtSlot()
    def on_appliciants_remove_button_clicked(self):

        current_row = self.applicant_twidget.currentRow()
        person_item = self.applicant_twidget.item(current_row, 0)
        person_id = person_item.data(Qt.UserRole)

        try:
            applicant_roles = self.application.stakeholders.filter(CtApplicationPersonRole.person == person_id) \
                .filter(CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE).one()

            #in case of ApplicationType.giving_up_ownership
            # or in case of a Transfer (possession or ownership):
            # Remove the applicants also from the co-ownership widget

            app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())
            self.application.stakeholders.remove(applicant_roles)
            self.applicant_twidget.removeRow(current_row)

            if app_type == ApplicationType.giving_up_ownership:

                giving_count = self.application.stakeholders.filter(CtApplicationPersonRole.person == person_id)\
                    .filter(CtApplicationPersonRole.role == Constants.GIVING_UP_OWNER_CODE).count()
                remaining_count = self.application.stakeholders.filter(CtApplicationPersonRole.person == person_id)\
                    .filter(CtApplicationPersonRole.role == Constants.REMAINING_OWNER_CODE).count()

                if giving_count > 0:
                    ownership_giving_roles = self.application.stakeholders\
                                                .filter(CtApplicationPersonRole.person == person_id)\
                                                .filter(CtApplicationPersonRole.role == Constants.GIVING_UP_OWNER_CODE)\
                                                .one()

                    self.application.stakeholders.remove(ownership_giving_roles)
                    self.__remove_person_from_co_ownership_twidgets(person_id, Constants.GIVING_UP_OWNER_CODE)

                if remaining_count > 0:
                    ownership_remain_roles = self.application.stakeholders\
                                                .filter(CtApplicationPersonRole.person == person_id)\
                                                .filter(CtApplicationPersonRole.role == Constants.REMAINING_OWNER_CODE)\
                                                .one()

                    self.application.stakeholders.remove(ownership_remain_roles)
                    self.__remove_person_from_co_ownership_twidgets(person_id, Constants.REMAINING_OWNER_CODE)

            elif app_type == ApplicationType.transfer_possession_right or app_type == ApplicationType.change_ownership \
                    or  app_type == ApplicationType.possess_split or app_type == ApplicationType.encroachment \
                    or app_type == ApplicationType.possession_right_use_right:

                old_count = self.application.stakeholders.filter(CtApplicationPersonRole.person == person_id)\
                                .filter(CtApplicationPersonRole.role == Constants.OLD_RIGHT_HOLDER_CODE).count()

                if old_count > 0:
                    old_right_holders = self.application.stakeholders\
                                            .filter(CtApplicationPersonRole.person == person_id)\
                                            .filter(CtApplicationPersonRole.role == Constants.OLD_RIGHT_HOLDER_CODE)\
                                            .all()

                    for applicant in old_right_holders:
                        self.application.stakeholders.remove(applicant)
                        self.__remove_old_right_holder(applicant.person)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        if self.application.stakeholders.count() > 0:
            self.application_type_cbox.setEnabled(False)
        elif not self.attribute_update:
            self.application_type_cbox.setEnabled(True)

    @pyqtSlot()
    def on_representatives_remove_button_clicked(self):

        self.create_savepoint()

        current_row = self.legal_rep_twidget.currentRow()
        person_item = self.legal_rep_twidget.item(current_row, 0)
        person_id = person_item.data(Qt.UserRole)

        try:

            applicants = self.application.stakeholders.filter(CtApplicationPersonRole.person == person_id) \
                .filter(CtApplicationPersonRole.role == Constants.LEGAL_REP_ROLE_CODE).all()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        for ctApplicationPersonRole in applicants:

            try:
                self.application.stakeholders.remove(ctApplicationPersonRole)

            except SQLAlchemyError, e:
                self.rollback_to_savepoint()
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            self.legal_rep_twidget.removeRow(current_row)
            return

    @pyqtSlot()
    def on_up_button_clicked(self):

        try:
            remaining_role = self.session.query(ClPersonRole).filter_by(code=Constants.REMAINING_OWNER_CODE).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        for row in range(self.owners_giving_twidget.rowCount()):
            item = self.owners_giving_twidget.item(row, 0)

            if item is not None and item.isSelected():

                row_count = self.owners_remaining_twidget.rowCount()
                self.owners_remaining_twidget.insertRow(row_count)
                main_item = QTableWidgetItem(QIcon(), "")
                main_item.setCheckState(Qt.Unchecked)

                for column in range(self.owners_giving_twidget.columnCount()):
                    item1 = self.owners_giving_twidget.takeItem(row, column)
                    self.owners_remaining_twidget.setItem(row_count, column+1, item1)
                    self.owners_remaining_twidget.setItem(row_count, 0 , main_item)

                try:
                    # applicant = self.application.stakeholders.filter_by(person=item.data(Qt.UserRole)) \
                    #     .filter_by(role=Constants.GIVING_UP_OWNER_CODE)
                    applicant = self.session.query(CtApplicationPersonRole)\
                        .filter(CtApplicationPersonRole.person == item.data(Qt.UserRole))\
                        .filter(CtApplicationPersonRole.role == Constants.GIVING_UP_OWNER_CODE)\
                        .filter(CtApplicationPersonRole.application == self.application.app_no).one()

                    applicant.role = Constants.REMAINING_OWNER_CODE
                    applicant.role_ref = remaining_role
                except SQLAlchemyError, e:
                    PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                    return

                self.owners_giving_twidget.removeRow(row)

    @pyqtSlot()
    def on_down_button_clicked(self):

        try:
            giving_role = self.session.query(ClPersonRole).filter_by(code=Constants.GIVING_UP_OWNER_CODE).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        row_count = self.owners_remaining_twidget.rowCount()

        if row_count == 1:
            PluginUtils.show_message(self, self.tr("Change of co-ownership"),
                                     self.tr("At least one owner should remain."))
            return

        for row in range(self.owners_remaining_twidget.rowCount()):
            item = self.owners_remaining_twidget.item(row, 1)

            if item is not None and item.isSelected():
                row_count = self.owners_giving_twidget.rowCount()
                self.owners_giving_twidget.insertRow(row_count)

                item = self.owners_remaining_twidget.takeItem(row, 1)
                self.owners_giving_twidget.setItem(row_count, 0, item)

                item = self.owners_remaining_twidget.takeItem(row, 2)
                self.owners_giving_twidget.setItem(row_count, 1, item)

                item = self.owners_remaining_twidget.takeItem(row, 3)
                self.owners_giving_twidget.setItem(row_count, 2, item)
                # for column in range(self.owners_remaining_twidget.columnCount()):
                #     item = self.owners_remaining_twidget.takeItem(row, column)
                #     self.owners_giving_twidget.setItem(row_count, column-1, item)
                try:
                    applicant = self.application.stakeholders.filter_by(person=item.data(Qt.UserRole)).filter_by(
                        role=Constants.REMAINING_OWNER_CODE).one()
                    applicant.role = Constants.GIVING_UP_OWNER_CODE
                    applicant.role_ref = giving_role

                except SQLAlchemyError, e:
                    PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                    return

                self.owners_remaining_twidget.removeRow(row)

    @pyqtSlot(int)
    def on_application_tab_widget_currentChanged(self, current_index):

        self.last_tab = current_index

        if self.application_tab_widget.widget(current_index) == self.document_tab:
            self.__update_applicant_cbox()

        app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())

        if app_type == ApplicationType.change_ownership \
            or app_type == ApplicationType.transfer_possession_right \
                or app_type == ApplicationType.possess_split \
                or app_type == ApplicationType.encroachment \
                or app_type == ApplicationType.possession_right_use_right:

            self.old_right_holders_twidget.setRowCount(0)

            for applicant in self.application.stakeholders.filter(CtApplicationPersonRole.role == Constants.OLD_RIGHT_HOLDER_CODE):
                self.__add_old_right_holder_item(applicant)

    @pyqtSlot(int)
    def on_rigth_type_cbox_currentIndexChanged(self, index):

        self.application_type_cbox.clear()
        rigth_code = self.rigth_type_cbox.itemData(self.rigth_type_cbox.currentIndex())

        rigth_apps = self.session.query(SetRightTypeApplicationType).filter(SetRightTypeApplicationType.right_type == rigth_code).\
            order_by(SetRightTypeApplicationType.application_type).all()

        for item in rigth_apps:
            app_type = self.session.query(ClApplicationType).filter(ClApplicationType.code == item.application_type).one()
            self.application_type_cbox.addItem(app_type.description, app_type.code)

    @pyqtSlot(int)
    def on_application_type_cbox_currentIndexChanged(self, index):

        self.__generate_application_number()

        self.__set_visible_tabs()

        self.__app_type_visible()

    @pyqtSlot()
    def on_application_status_twidget_itemSelectionChanged(self):

        current_row = self.application_status_twidget.currentRow()
        status_item = self.application_status_twidget.item(current_row, 0)

        if status_item is None:
            return

        date_item = self.application_status_twidget.item(current_row, 1)
        next_officer_item = self.application_status_twidget.item(current_row, 3)

        self.status_date_date.setDate(QDate.fromString(date_item.text(), Constants.DATE_FORMAT))
        self.status_cbox.setCurrentIndex(self.status_cbox.findData(status_item.data(Qt.UserRole)))
        self.next_officer_in_charge_cbox.setCurrentIndex(
            self.next_officer_in_charge_cbox.findData(next_officer_item.data(Qt.UserRole)))

        status = self.session.query(func.max(CtApplicationStatus.status)).\
            filter(CtApplicationStatus.application == self.application.app_no).one()
        mas_status = str(status).split(",")[0][1:]
        if mas_status == '7':
            self.add_button.setEnabled(False)
            self.update_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        #     select_item = status_item.data(Qt.UserRole)
        #     if select_item != 9:
        #         self.add_button.setEnabled(False)
        #         self.update_button.setEnabled(False)
        #         self.delete_button.setEnabled(False)
        #     else:
        #         self.add_button.setEnabled(True)
        #         self.update_button.setEnabled(True)
        #         self.delete_button.setEnabled(True)
        # elif mas_status == '7':
        #     select_item = status_item.data(Qt.UserRole)
        #     if select_item != 7:
        #         self.add_button.setEnabled(False)
        #         self.update_button.setEnabled(False)
        #         self.delete_button.setEnabled(False)
        #     else:
        #         self.add_button.setEnabled(True)
        #         self.update_button.setEnabled(True)
        #         self.delete_button.setEnabled(True)
        # elif mas_status == '8':
        #     select_item = status_item.data(Qt.UserRole)
        #     if select_item != 8:
        #         self.add_button.setEnabled(False)
        #         self.update_button.setEnabled(False)
        #         self.delete_button.setEnabled(False)
        #     else:
        #         self.add_button.setEnabled(True)
        #         self.update_button.setEnabled(True)
        #         self.delete_button.setEnabled(True)

    @pyqtSlot()
    def on_delete_button_clicked(self):

        selected_row = self.application_status_twidget.currentRow()
        status_item = self.application_status_twidget.item(selected_row, 0)

        self.create_savepoint()

        if self.__max_status_object().next_officer_in_charge != self.__current_real_user().user_name_real:
            PluginUtils.show_message(self, self.tr("Application Status"),
                                     self.tr("Permission Status!!"))
            return

        for app_status in self.application.statuses:
            if app_status.status_ref.code == status_item.data(Qt.UserRole):
                if app_status.status_ref.code == Constants.FIRST_STATUS_CODE:
                    PluginUtils.show_message(self, self.tr("Status error"), self.tr("First status can't be deleted."))
                    return
                try:
                    self.application.statuses.remove(app_status)

                except SQLAlchemyError, e:
                    self.rollback_to_savepoint()
                    PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                    return

                self.application_status_twidget.removeRow(selected_row)
                return

    @pyqtSlot()
    def on_update_button_clicked(self):

        selected_row = self.application_status_twidget.currentRow()
        if selected_row is None:
            return

        if self.__max_status_object().officer_in_charge != self.__current_real_user().user_name_real:
            PluginUtils.show_message(self, self.tr("Application Status"),
                                     self.tr("Permission Status!!"))
            return

        status_item = self.application_status_twidget.item(selected_row, 0)
        date_item = self.application_status_twidget.item(selected_row, 1)
        next_officer_item = self.application_status_twidget.item(selected_row, 3)
        status_code = self.status_cbox.itemData(self.status_cbox.currentIndex(), Qt.UserRole)

        if status_item is None:
            return

        for appStatus in self.application.statuses:

            if appStatus.status_ref.code == status_item.data(Qt.UserRole):

                if not self.__valid_status(status_code) \
                        and not appStatus.status_ref.code == status_code:
                    PluginUtils.show_message(self, self.tr("Status error"),
                                             self.tr("This status is already added to the application."))
                    return

                if appStatus.status_ref.code == 8:
                    PluginUtils.show_message(self, self.tr("Status error"),
                                             self.tr("This application refused by governor."))
                    return

                try:
                    self.create_savepoint()

                     #Status 1 can't be updated
                    if appStatus.status_ref.code != Constants.FIRST_STATUS_CODE:
                        status_id = self.status_cbox.itemData(self.status_cbox.currentIndex(), Qt.UserRole)
                        appStatus.status = status_id

                    index = self.next_officer_in_charge_cbox.currentIndex()
                    next_officer_user_name = self.next_officer_in_charge_cbox.itemData(index, Qt.UserRole)
                    appStatus.next_officer_in_charge = next_officer_user_name
                    python_date = PluginUtils.convert_qt_date_to_python(self.status_date_date.date())
                    appStatus.status_date = python_date
                    #self.commit()

                except SQLAlchemyError, e:
                    PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                    return

                status_item.setText(appStatus.status_ref.description)
                status_item.setData(Qt.UserRole, appStatus.status_ref.code)
                qt_date = PluginUtils.convert_python_date_to_qt(appStatus.status_date)
                date_item.setText(qt_date.toString(Constants.DATE_FORMAT))
                next_officer = appStatus.next_officer_in_charge_ref.surname + ", " \
                               + appStatus.next_officer_in_charge_ref.first_name
                next_officer_item.setText(next_officer)
                next_officer_item.setData(Qt.UserRole, appStatus.next_officer_in_charge_ref.user_name_real)

    @pyqtSlot()
    def on_add_button_clicked(self):

        next_officer_username = self.next_officer_in_charge_cbox.itemData(
            self.next_officer_in_charge_cbox.currentIndex(), Qt.UserRole)
        status_id = self.status_cbox.itemData(self.status_cbox.currentIndex(), Qt.UserRole)

        if self.__max_status_object().next_officer_in_charge != self.__current_real_user().user_name_real:
            PluginUtils.show_message(self, self.tr("Application Status"),
                                     self.tr("Permission Status!!"))
            return

        if status_id == 5:
            if self.parcel_edit.text() == '':
                PluginUtils.show_message(self, self.tr("Application Status"),
                                         self.tr("First connect to parcel for this application!!"))
                return
        if status_id == 6:
            PluginUtils.show_message(self, self.tr("Application Status"), self.tr("First prepare draft decision for this application!!"))
            return
        if status_id == 7:
            PluginUtils.show_message(self, self.tr("Application Status"), self.tr("First register governor decision!!"))
            return

        contract_app_count = self.session.query(CtContractApplicationRole).\
        filter(CtContractApplicationRole.application == self.application.app_no).count()

        if status_id == 9:
            if contract_app_count == 0:
                PluginUtils.show_message(self, self.tr("Application Status"),
                                         self.tr("First create contract!!"))
                return

        for appStatus in self.application.statuses:
            if appStatus.status_ref.code == 8:
                PluginUtils.show_message(self, self.tr("Status error"),
                                         self.tr("This application refused by governor."))
                return

        if self.application.app_type == ApplicationType.privatization or self.application.app_type == ApplicationType.buisness_from_state:
            if status_id == 5:
                if not self.paid_by_applicant_check_box.isChecked():
                    PluginUtils.show_message(self, self.tr("Status error"),
                                             self.tr("This applicant must excess area price to be paid."))
                    return

        new_status = CtApplicationStatus()

        try:
            officer = self.session.query(SetRole)\
                .filter(SetRole.user_name == QSettings().value(SettingsConstants.USER))\
                .filter(SetRole.is_active == True).one()
            next_officer = self.session.query(SetRole).filter_by(user_name_real=next_officer_username).one()
            status = self.session.query(ClApplicationStatus).filter_by(code=status_id).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        try:

            app_excess_count = self.session.query(CtApp1Ext)\
                .join(CtApplication, CtApp1Ext.app_no == CtApplication.app_no)\
                .filter(CtApp1Ext.app_no == self.application.app_no)\
                .filter(or_(CtApplication.app_type == 1, CtApplication.app_type == 3)).count()

            # if app_excess_count == 1:
            #     app_excess = self.session.query(CtApp1Ext)\
            #         .join(CtApplication, CtApp1Ext.app_no == CtApplication.app_no)\
            #         .filter(CtApp1Ext.app_no == self.application.app_no)\
            #         .filter(or_(CtApplication.app_type == 1, CtApplication.app_type == 3)).one()
            #     if app_excess.applicant_has_paid == False and status_id != 8 and self.parcel_edit.text() != '':
            #         PluginUtils.show_error(self, self.tr("Status error"),
            #                         self.tr("This parcel excess area paid!!!."))
            #         return
            maintenance_count = self.session.query(CtApplication)\
                .join(CaMaintenanceCase, CtApplication.maintenance_case == CaMaintenanceCase.id)\
                .filter(CaMaintenanceCase.completion_date == None)\
                .filter(CtApplication.app_no == self.application.app_no)\
                .filter(CtApplication.parcel != None).count()
            if self.parcel_edit.text() != '':
                maintenance_count = self.session.query(CaParcel).\
                    filter(CaParcel.parcel_id == self.parcel_edit.text()).\
                    filter(CaParcel.geometry.ST_Overlaps(CaTmpParcel.geometry)).count()
            if maintenance_count > 0:
                PluginUtils.show_error(self, self.tr("Status error"),
                                    self.tr("This parcel cadastre changing!!!."))
                return

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        check_count = self.application.statuses.filter(CtApplicationStatus.status == (status_id-1)).count()
        status_7_count = self.application.statuses.filter(CtApplicationStatus.status == 7).count()
        if check_count == 0 and status_id != 8 and status_7_count == 0:
            PluginUtils.show_error(self, self.tr("Status error"),
                                self.tr("Application status must be in order!."))
            return

        new_status.officer_in_charge_ref = officer
        new_status.officer_in_charge = QSettings().value(SettingsConstants.USER)
        new_status.next_officer_in_charge = next_officer_username
        new_status.next_officer_in_charge_ref = next_officer
        ui_date = self.status_date_date.date()
        new_status.status_date = date(ui_date.year(), ui_date.month(), ui_date.day())
        new_status.status = status_id
        new_status.status_ref = status

        if not self.__valid_status(status_id):
            PluginUtils.show_error(self, self.tr("Status error"),
                                self.tr("This status is already added to the application."))
            return

        try:
            self.application.statuses.append(new_status)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        if new_status.status >= 5:
            self.requested_land_use_type_cbox.setEnabled(False)
        self.__add_application_status_item(new_status)
        self.__update_decision_tab()

    def __current_real_user(self):

        officer = self.session.query(SetRole) \
            .filter(SetRole.user_name == QSettings().value(SettingsConstants.USER)) \
            .filter(SetRole.is_active == True).one()

        return officer

    def __max_application_status(self):

        status = self.session.query(func.max(CtApplicationStatus.status)). \
            filter(CtApplicationStatus.application == self.application.app_no).one()
        max_status = str(status).split(",")[0][1:]
        return int(max_status)

    def __max_status_object(self):

        status = self.session.query(CtApplicationStatus).\
            filter(CtApplicationStatus.application == self.application.app_no).\
            filter(CtApplicationStatus.status == self.__max_application_status()).one()
        return status

    @pyqtSlot()
    def on_apply_button_clicked(self):

        app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())
        self.application.app_type = app_type

        # save application details
        validity_result = self.__validity_of_application()

        if not validity_result[0]:
            log_message = validity_result[1]

            PluginUtils.show_error(self, self.tr("Invalid application"), log_message)
            return

        self.__save_application()

        self.__start_fade_out_timer()

        self.attribute_update = True

    def __save_application(self):

        try:
            self.create_savepoint()

            self.__save_application_details()

            self.__save_applicants()

            if self.application.app_type == ApplicationType.privatization \
                    or self.application.app_type == ApplicationType.privatization_representation:

                self.__save_privatization()

            elif self.application.app_type == ApplicationType.change_ownership:

                self.__save_change_ownership()

            elif self.application.app_type == ApplicationType.mortgage_possession:

                self.__save_mortgage_application()

            elif self.application.app_type == ApplicationType.transfer_possession_right:

                self.__save_transfer_possession()

            elif self.application.app_type == ApplicationType.possess_split:

                self.__save_transfer_possession()

            elif self.application.app_type == ApplicationType.encroachment:

                self.__save_transfer_possession()

            elif self.application.app_type == ApplicationType.possession_right_use_right:

                self.__save_transfer_possession()

            elif self.application.app_type == ApplicationType.court_decision:

                self.__save_court_decision()

            self.commit()

        except LM2Exception, e:
            self.rollback_to_savepoint()
            PluginUtils.show_error(self, e.title(), e.message())
            return

    def __save_application_details(self):

        self.create_savepoint()

        try:
            app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()

            #check if the app_no is still valid, otherwise generate new one
            if not self.attribute_update:
                app_no_count = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).count()
                if app_no_count > 0:

                    self.__generate_application_number()

                    app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()

                    PluginUtils.show_message(self, self.tr("Application Number"), self.tr("The application number was updated to the next available number."))

            self.application.app_no = app_no
            self.application.requested_landuse = self.requested_land_use_type_cbox.itemData(self.requested_land_use_type_cbox.currentIndex())
            #self.application.approved_landuse = self.requested_land_use_type_cbox.itemData(self.requested_land_use_type_cbox.currentIndex())
            self.application.app_timestamp = self.date_time_date.dateTime().toString(Constants.DATABASE_DATETIME_FORMAT)
            self.application.requested_duration = self.requested_year_spin_box.value()
            #self.application.approved_duration = self.approved_year_spin_box.value()
            self.application.remarks = self.remarks_text_edit.toPlainText()

            parcel_id = self.parcel_edit.text()
            parcel_count = self.session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == parcel_id).count()
            if parcel_count != 0:
                self.is_tmp_parcel = True

            status = self.session.query(func.max(CtApplicationStatus.status)).\
                filter(CtApplicationStatus.application == self.application.app_no).one()
            max_status = str(status).split(",")[0][1:]
            if self.parcel_edit.text() == "":
                self.application.parcel = None
            else:
                if max_status != '8':
                    if self.is_tmp_parcel and max_status < '7':
                        self.application.tmp_parcel = self.parcel_edit.text()
                        parcel = self.session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == self.parcel_edit.text()).one()
                        parcel.landuse = self.application.requested_landuse
                    else:
                        self.application.parcel = self.parcel_edit.text()
                        parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_edit.text()).one()
                        parcel.landuse = self.application.requested_landuse

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __save_privatization(self):

        self.create_savepoint()

        if self.application.app1ext is None:

            try:
                self.application.app1ext = CtApp1Ext()

            except SQLAlchemyError, e:
                self.rollback_to_savepoint()
                raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        try:
            self.application.app1ext.applicant_has_paid = self.paid_by_applicant_check_box.isChecked()
            self.application.app1ext.excess_area = self.excess_area_spin_box.value()
            self.application.app1ext.price_to_be_paid = self.price_to_be_paid_spin_box.value()

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __save_change_ownership(self):

        self.create_savepoint()

        try:
            if self.application.app15ext is None:

                self.application.app15ext = CtApp15Ext()

            self.application.app15ext.transfer_type = self.type_of_transfer_cbox.itemData(
                self.type_of_transfer_cbox.currentIndex())

            for row in range(self.old_right_holders_twidget.rowCount()):

                share_item = self.old_right_holders_twidget.item(row, OLD_RIGHT_HOLDER_SHARE)
                person_id = share_item.data(Qt.UserRole)
                applicant = self.application.stakeholders.filter(
                    CtApplicationPersonRole.role == Constants.OLD_RIGHT_HOLDER_CODE) \
                    .filter(CtApplicationPersonRole.person == person_id).one()
                applicant.share = Decimal(share_item.text())

            for row in range(self.new_right_holders_twidget.rowCount()):

                share_item = self.new_right_holders_twidget.item(row, NEW_RIGHT_HOLDER_SHARE)
                main_item = self.new_right_holders_twidget.item(row, NEW_RIGHT_HOLDER_MAIN)
                main = True if main_item.checkState() == Qt.Checked else False
                person_id = share_item.data(Qt.UserRole)
                applicant = self.application.stakeholders.filter(
                    CtApplicationPersonRole.role == Constants.NEW_RIGHT_HOLDER_CODE) \
                    .filter(CtApplicationPersonRole.person == person_id).one()

                applicant.main_applicant = main
                applicant.share = Decimal(share_item.text())

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __save_transfer_possession(self):

        self.create_savepoint()

        try:

            for row in range(self.old_right_holders_twidget.rowCount()):

                share_item = self.old_right_holders_twidget.item(row, OLD_RIGHT_HOLDER_SHARE)
                person_id = share_item.data(Qt.UserRole)

                applicant = self.application.stakeholders.filter(
                    CtApplicationPersonRole.role == Constants.OLD_RIGHT_HOLDER_CODE) \
                    .filter(CtApplicationPersonRole.person == person_id).one()
                applicant.share = Decimal(share_item.text())

            for row in range(self.new_right_holders_twidget.rowCount()):

                item = self.new_right_holders_twidget.item(row, NEW_RIGHT_HOLDER_MAIN)
                person_id = item.data(Qt.UserRole)
                main = True if item.checkState() == Qt.Checked else False

                share_item = self.new_right_holders_twidget.item(row, NEW_RIGHT_HOLDER_SHARE)
                person_id = share_item.data(Qt.UserRole)

                applicant = self.application.stakeholders.filter(
                    CtApplicationPersonRole.role == Constants.NEW_RIGHT_HOLDER_CODE) \
                    .filter(CtApplicationPersonRole.person == person_id).one()
                applicant.main_applicant = main
                applicant.share = Decimal(share_item.text())

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __save_applicants(self):

        self.create_savepoint()

        for row in range(self.applicant_twidget.rowCount()):
            item = self.applicant_twidget.item(row, APPLICANT_MAIN)
            person_id = item.data(Qt.UserRole)
            main = True if item.checkState() == Qt.Checked else False

            try:
                person = self.session.query(BsPerson).filter(BsPerson.person_id == person_id).one()
                applicant_count = self.application.stakeholders.filter(
                    CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE) \
                    .filter(CtApplicationPersonRole.person == person_id).count()
                if applicant_count == 1:
                    applicant = self.application.stakeholders.filter(
                        CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE) \
                        .filter(CtApplicationPersonRole.person == person_id).one()

                    applicant.main_applicant = main
                    share_item = self.applicant_twidget.item(row, APPLICANT_SHARE)
                    if person.type == 20:
                        applicant.share = 0
                    else:
                        applicant.share = Decimal(share_item.text())
            except SQLAlchemyError, e:
                self.rollback_to_savepoint()
                raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
        self.__save_remaining_ownership()

    def __save_remaining_ownership(self):

        self.create_savepoint()

        for row in range(self.owners_remaining_twidget.rowCount()):
            item = self.owners_remaining_twidget.item(row, 0)
            person_id = item.data(Qt.UserRole)
            if item.checkState() == Qt.Checked:
                main = True
                try:
                    applicant = self.application.stakeholders.filter(
                        CtApplicationPersonRole.role == Constants.REMAINING_OWNER_CODE) \
                        .filter(CtApplicationPersonRole.person == person_id).one()

                    applicant.main_applicant = main
                    share_item = self.applicant_twidget.item(row, APPLICANT_SHARE)
                    applicant.share = Decimal(share_item.text())

                except SQLAlchemyError, e:
                    self.rollback_to_savepoint()
                    raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            else:
                main = False
                try:
                    applicant = self.application.stakeholders.filter(
                        CtApplicationPersonRole.role == Constants.REMAINING_OWNER_CODE) \
                        .filter(CtApplicationPersonRole.person == person_id).one()

                    applicant.main_applicant = main
                    share_item = self.applicant_twidget.item(row, APPLICANT_SHARE)
                    applicant.share = Decimal(share_item.text())

                except SQLAlchemyError, e:
                    self.rollback_to_savepoint()
                    raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __save_court_decision(self):

        self.create_savepoint()
        right_type = self.rigth_type_cbox.itemData(self.rigth_type_cbox.currentIndex())

        try:

            if self.application.app29ext is None:
                self.application.app29ext = CtApp29Ext()
            if right_type != 3:
                self.application.app29ext.end_period = self.contract_court_end_date_edit.date().toString(
                    Constants.DATABASE_DATE_FORMAT)
                self.application.app29ext.start_period = self.contract_court_start_date_edit.date().toString(
                    Constants.DATABASE_DATE_FORMAT)
                self.application.app29ext.court_status = self.contract_court_status_cbox.itemData(
                    self.contract_court_status_cbox.currentIndex())
            else:
                self.application.app29ext.end_period = self.record_court_end_date_edit.date().toString(
                    Constants.DATABASE_DATE_FORMAT)
                self.application.app29ext.start_period = self.record_court_start_date_edit.date().toString(
                    Constants.DATABASE_DATE_FORMAT)
                self.application.app29ext.court_status = self.record_court_status_cbox.itemData(
                    self.record_court_status_cbox.currentIndex())


        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __save_mortgage_application(self):

        self.create_savepoint()

        try:

            if self.application.app8ext is None:
                self.application.app8ext = CtApp8Ext()

            self.application.app8ext.end_mortgage_period = self.mortgage_end_date_edit.date().toString(
                Constants.DATABASE_DATE_FORMAT)
            self.application.app8ext.start_mortgage_period = self.mortgage_start_date_edit.date().toString(
                Constants.DATABASE_DATE_FORMAT)
            self.application.app8ext.mortgage_type = self.mortgage_type_cbox.itemData(
                self.mortgage_type_cbox.currentIndex())
            self.application.app8ext.mortgage_status = self.mortgage_status_cbox.itemData(
                self.mortgage_status_cbox.currentIndex())

            for row in range(self.mortgage_twidget.rowCount()):

                item = self.mortgage_twidget.item(row, MORTGAGE_SHARE)

                mortgagee = self.application.stakeholders.filter_by(role=Constants.MORTGAGEE_ROLE_CODE) \
                    .filter_by(person=item.data(Qt.UserRole)).one()

                mortgagee.share = Decimal(item.text())

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __landuse_per_application_type(self, app_type):

        try:
            types = exists().where(ClLanduseType.code == SetApplicationTypeLanduseType.landuse_type)\
                            .where(SetApplicationTypeLanduseType.application_type == app_type)
            landuse_types = self.session.query(ClLanduseType).filter(types).order_by(ClLanduseType.code).all()
            landuse_count = self.session.query(ClLanduseType).filter(types).count()

            if landuse_count == 0:
                landuse_types = self.session.query(ClLanduseType).order_by(ClLanduseType.code).all()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        self.requested_land_use_type_cbox.clear()

        for item in landuse_types:
            self.requested_land_use_type_cbox.addItem(str(item.code) + ": " + item.description, item.code)

    def reject(self):

        self.rollback()

        if QDateTime.currentDateTime().toString("yyMMdd") in self.current_application_no():

            # when an auto-flush is executed the temp-Application is already committed
            # to the database and needs to be deleted again
            application_count = self.session.query(CtApplication.app_no).filter_by(app_no=self.application.app_no).count()
            if application_count > 0:
                self.session.query(CtApplication).filter_by(app_no=self.application.app_no).delete()

        QDialog.reject(self)

    @pyqtSlot()
    def on_from_get_decision_from_nav_button_clicked(self):

        self.__copy_decision_from_navigator()

    @pyqtSlot()
    def on_from_get_representatives_from_nav_button_clicked(self):

        self.__copy_legal_rep_from_navigator()

    @pyqtSlot()
    def on_relating_contract_accept_button_clicked(self):

        to_be_accepted_parcel_num = self.relating_contract_num_edit.text()
        self.relating_contract_edit.setText(to_be_accepted_parcel_num)

    @pyqtSlot()
    def on_contract_cancelled_accept_button_clicked(self):

        to_be_accepted_num = self.contract_cancelled_num_edit.text()
        self.contract_to_be_cancelled_edit.setText(to_be_accepted_num)
        self.contract_ca

    @pyqtSlot()
    def on_from_get_new_right_holder_from_nav_button_clicked(self):

        self.__copy_new_right_holder_from_navigator()

    @pyqtSlot()
    def on_remove_new_right_holder_button_clicked(self):

        for row in range(self.new_right_holders_twidget.rowCount()):
            item = self.new_right_holders_twidget.item(row, 0)
            if item is not None and item.isSelected():
                person_id = item.data(Qt.UserRole)
                applicant_roles = self.application.stakeholders.filter(CtApplicationPersonRole.person == person_id) \
                    .filter(CtApplicationPersonRole.role == Constants.NEW_RIGHT_HOLDER_CODE).one()
                self.application.stakeholders.remove(applicant_roles)
                self.new_right_holders_twidget.removeRow(row)

    @pyqtSlot()
    def on_mortgagee_remove_button_clicked(self):

        self.create_savepoint()

        for row in range(self.mortgage_twidget.rowCount()):
            item = self.mortgage_twidget.item(row, 0)
            person_id = item.data(Qt.UserRole)
            if item is not None and item.isSelected():
                self.mortgage_twidget.removeRow(row)
                mortgagee = self.application.stakeholders.filter_by(role=Constants.MORTGAGEE_ROLE_CODE) \
                    .filter_by(person=person_id).one()
                try:
                    self.application.stakeholders.remove(mortgagee)

                except SQLAlchemyError, e:
                    self.rollback_to_savepoint()
                    PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    @pyqtSlot()
    def on_reg_receipt_print_button_clicked(self):

        # current_file = os.path.dirname(__file__) + "/.." + "/pentaho/application_registration_reciept.prpt"
        # QDesktopServices.openUrl(QUrl.fromLocalFile(current_file))
        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()
        app_count = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).count()
        if app_count == 0:
            PluginUtils.show_error(self, self.tr("application error"), self.tr("not save"))
            return
        path = FileUtils.map_file_path()
        template = path + "app_reciept.qpt"

        templateDOM = QDomDocument()
        templateDOM.setContent(QFile(template), False)

        map_canvas = QgsMapCanvas()

        map_composition = QgsComposition(map_canvas.mapRenderer())
        map_composition.loadFromTemplate(templateDOM)

        map_composition.setPrintResolution(300)

        default_path = r'D:/TM_LM2/application_list'
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

        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path+"/app_reciept.pdf")
        printer.setPaperSize(QSizeF(map_composition.paperWidth(), map_composition.paperHeight()), QPrinter.Millimeter)
        printer.setFullPage(True)
        printer.setColorMode(QPrinter.Color)
        printer.setResolution(map_composition.printResolution())

        pdfPainter = QPainter(printer)
        paperRectMM = printer.pageRect(QPrinter.Millimeter)
        paperRectPixel = printer.pageRect(QPrinter.DevicePixel)
        map_composition.render(pdfPainter, paperRectPixel, paperRectMM)
        pdfPainter.end()

        self.__add_person_address(map_composition)
        self.__add_aimag_name(map_composition)
        self.__add_soum_name(map_composition)
        self.__add_app_no(map_composition)
        self.__add_app_date(map_composition)
        self.__add_person_name(map_composition)
        self.__add_officer(map_composition)
        self.__add_card_officer_full(map_composition)
        self.__add_card_person_name(map_composition)
        map_composition.exportAsPDF(path + "/app_reciept.pdf")
        map_composition.exportAsPDF(default_path + "/"+app_no+".pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(default_path+"/"+app_no+".pdf"))

    @pyqtSlot()
    def on_app_return_button_clicked(self):

        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()
        app_count = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).count()
        if app_count == 0:
            PluginUtils.show_error(self, self.tr("application error"), self.tr("not save"))
            return
        app_status = self.session.query(CtApplicationStatus).filter(CtApplicationStatus.application == app_no).all()
        ok = 0
        for s in app_status:
            if s.status == 8:
                ok = 1

        if ok == 0:
            PluginUtils.show_error(self, self.tr("application error"), self.tr("there is no information in the remarks if application details. Application status must be 8."))
            return
        path = FileUtils.map_file_path()
        template = path + "app_return_reciept.qpt"

        templateDOM = QDomDocument()
        templateDOM.setContent(QFile(template), False)

        map_canvas = QgsMapCanvas()

        map_composition = QgsComposition(map_canvas.mapRenderer())
        map_composition.loadFromTemplate(templateDOM)

        map_composition.setPrintResolution(300)

        default_path = r'D:/TM_LM2/application_response'
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


        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path+"app_response.pdf")
        printer.setPaperSize(QSizeF(map_composition.paperWidth(), map_composition.paperHeight()), QPrinter.Millimeter)
        printer.setFullPage(True)
        printer.setColorMode(QPrinter.Color)
        printer.setResolution(map_composition.printResolution())

        pdfPainter = QPainter(printer)
        paperRectMM = printer.pageRect(QPrinter.Millimeter)
        paperRectPixel = printer.pageRect(QPrinter.DevicePixel)
        map_composition.render(pdfPainter, paperRectPixel, paperRectMM)
        pdfPainter.end()

        self.__add_aimag_name(map_composition)
        self.__add_soum_name(map_composition)
        self.__add_app_no(map_composition)
        self.__add_app_status_date(map_composition)
        self.__add_person_name(map_composition)
        self.__add_officer_name(map_composition)
        self.__add_card_officer_full(map_composition)
        self.__add_app_remarks(map_composition)

        map_composition.exportAsPDF(path + "app_response.pdf")
        map_composition.exportAsPDF(default_path + "/"+app_no+".pdf")
        QDesktopServices.openUrl(QUrl.fromLocalFile(default_path+"/"+app_no+".pdf"))

    def __add_aimag_name(self,map_composition):

        aimag_code = self.application_num_first_edit.text()[:3]
        try:
            aimag = self.session.query(AuLevel1).filter(AuLevel1.code == aimag_code).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        item = map_composition.getComposerItemById("aimag_name")
        item.setText(aimag.name)
        item.adjustSizeToText()

    def __add_soum_name(self,map_composition):

        soum_code = self.application_num_first_edit.text()
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == soum_code).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        item = map_composition.getComposerItemById("soum_name")
        item.setText(soum.name)
        item.adjustSizeToText()

    def __add_app_no(self,map_composition):

        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()
        item = map_composition.getComposerItemById("app_no")
        item.setText(app_no)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("card_app_no")
        item.setText(app_no)
        item.adjustSizeToText()

        app_type = self.application_type_cbox.currentText()
        app_type = app_type.split(':')[1]
        item = map_composition.getComposerItemById("card_app_type")
        item.setText(app_type)
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

    def __add_app_remarks(self,map_composition):

        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()

        try:
            app = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        item = map_composition.getComposerItemById("app_remarks")

        item.setText(self.__wrap(app.remarks,140))
        # item.adjustSizeToText()

    def __add_app_date(self,map_composition):

        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()
        try:
            app = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        item = map_composition.getComposerItemById("year")
        item.setText(str(app.app_timestamp)[:4])
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("month")
        item.setText(str(app.app_timestamp)[5:-12])
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("day")
        item.setText(str(app.app_timestamp)[8:-9])
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("hour")
        item.setText(str(app.app_timestamp)[10:-6])
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("minute")
        item.setText(str(app.app_timestamp)[14:-3])
        item.adjustSizeToText()

        long_date = str(app.app_timestamp)[:4]+'.'+ str(app.app_timestamp)[5:-12] +'.'+ str(app.app_timestamp)[8:-9]
        item = map_composition.getComposerItemById("card_app_date")
        item.setText(long_date)
        item.adjustSizeToText()

        long_date = str(app.app_timestamp)[:4]+'.'+ str(app.app_timestamp)[5:-12] +'.'+ str(app.app_timestamp)[8:-9]
        item = map_composition.getComposerItemById("card_date")
        item.setText(long_date)
        item.adjustSizeToText()

    def __add_app_status_date(self,map_composition):

        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()
        try:
            app_status = self.session.query(CtApplicationStatus).filter(CtApplicationStatus.application == app_no) \
                                                                .filter(CtApplicationStatus.status == 8).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        item = map_composition.getComposerItemById("year")
        item.setText(str(app_status.status_date)[:4])
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("month")
        item.setText(str(app_status.status_date)[5:-3])
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("day")
        item.setText(str(app_status.status_date)[8:])
        item.adjustSizeToText()

    def __add_app_date_minut(self,map_composition):

        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()
        try:
            app = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        item = map_composition.getComposerItemById("app_date_minut")
        item.setText(str(app.app_timestamp)[10:])
        item.adjustSizeToText()

    def __add_person_address(self,map_composition):

        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                 + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()
        try:
            if self.application.app_type == 7 or self.application.app_type == 15:
                app_person = self.session.query(CtApplicationPersonRole). \
                    filter(CtApplicationPersonRole.application == app_no). \
                    filter(CtApplicationPersonRole.role == Constants.NEW_RIGHT_HOLDER_CODE).all()
            elif self.application.app_type == 2:
                app_person = self.session.query(CtApplicationPersonRole). \
                    filter(CtApplicationPersonRole.application == app_no). \
                    filter(CtApplicationPersonRole.role == Constants.REMAINING_OWNER_CODE).all()
            else:
                app_person = self.session.query(CtApplicationPersonRole). \
                    filter(CtApplicationPersonRole.application == app_no).all()
            for p in app_person:
                if p.main_applicant == True:
                    person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        item = map_composition.getComposerItemById("person_address")

        aimag = ''
        if person.au_level1_ref:
            aimag = person.au_level1_ref.name

        soum = ''
        if person.au_level2_ref:
            soum = person.au_level2_ref.name
        bag = ''
        if person.au_level3_ref:
            bag = person.au_level3_ref.name
        street = ''
        if person.address_street_name:
            street = person.address_street_name
        khashaa = ''
        if person.address_khaskhaa:
            khashaa = person.address_khaskhaa

        person_address = aimag +' '+ soum + ' '+ bag +' ' + street + ' '+ khashaa

        item.setText(person_address)
        item.adjustSizeToText()

    def __add_person_name(self,map_composition):

        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()
        try:
            if self.application.app_type == 7 or self.application.app_type == 15:
                app_person = self.session.query(CtApplicationPersonRole).\
                    filter(CtApplicationPersonRole.application == app_no).\
                    filter(CtApplicationPersonRole.role == Constants.NEW_RIGHT_HOLDER_CODE).all()
            elif self.application.app_type == 2:
                app_person = self.session.query(CtApplicationPersonRole). \
                    filter(CtApplicationPersonRole.application == app_no). \
                    filter(CtApplicationPersonRole.role == Constants.REMAINING_OWNER_CODE).all()
            else:
                app_person = self.session.query(CtApplicationPersonRole). \
                    filter(CtApplicationPersonRole.application == app_no).all()
            for p in app_person:
                if p.main_applicant == True:
                    person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        item = map_composition.getComposerItemById("person_name")
        first_name = ''
        if person.first_name == None:
            first_name = u' '
        else:
            first_name = person.first_name
        name = person.name +u", "+ first_name
        item.setText(name)
        item.adjustSizeToText()

    def __add_card_person_name(self,map_composition):

        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()
        try:
            if self.application.app_type == 7 or self.application.app_type == 15:
                app_person = self.session.query(CtApplicationPersonRole).\
                    filter(CtApplicationPersonRole.application == app_no).\
                    filter(CtApplicationPersonRole.role == Constants.NEW_RIGHT_HOLDER_CODE).all()
            elif self.application.app_type == 2:
                app_person = self.session.query(CtApplicationPersonRole). \
                    filter(CtApplicationPersonRole.application == app_no). \
                    filter(CtApplicationPersonRole.role == Constants.REMAINING_OWNER_CODE).all()
            else:
                app_person = self.session.query(CtApplicationPersonRole). \
                    filter(CtApplicationPersonRole.application == app_no).all()
            for p in app_person:
                if p.main_applicant == True:
                    person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        item = map_composition.getComposerItemById("card_person_name")

        first_name = ''
        if person.first_name == None:
            first_name = u' '
        else:
            first_name = person.first_name
        card_person_name = person.name +u", "+ first_name
        item.setText(card_person_name)
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

    def __add_officer_name(self,map_composition):

        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()
        try:
            app_status = self.session.query(CtApplicationStatus).\
                filter(CtApplicationStatus.application == app_no).\
                filter(CtApplicationStatus.status == 8).all()
            for p in app_status:
                officer = self.session.query(SetRole).filter(SetRole.user_name_real == p.officer_in_charge).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        position = 10
        if officer.position != None:
            position = officer.position
            position = self.session.query(ClPositionType).filter(ClPositionType.code == position).one()
        officer_full = '                          ' + position.description + u' албан тушаалтан '+ officer.surname + u' овогтой ' + officer.first_name + ' ___________________ '+ u' хүлээн авав.'
        item = map_composition.getComposerItemById("officer_surname")
        item.setText(officer.surname)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("officer_name")
        item.setText(officer.first_name)
        item.adjustSizeToText()

    def __add_officer(self,map_composition):

        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()
        try:
            app_status = self.session.query(CtApplicationStatus).filter(CtApplicationStatus.application == app_no).all()
            for p in app_status:
                if p.status == 1:
                    officer = self.session.query(SetRole).filter(SetRole.user_name_real == p.officer_in_charge).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        position = ''
        if officer.position != None:
            position = officer.position
            position = self.session.query(ClPositionType).filter(ClPositionType.code == position).one()
            position = position.description

        officer_full = '                          ' + position + ' ' + officer.surname[:1] + '.' + officer.first_name + ' ___________________ '+ u' хүлээн авав.'
        item = map_composition.getComposerItemById("officer_full")
        item.setText(self.__wrap(officer_full, 200))
        # item.adjustSizeToText()

    def __add_card_officer_full(self, map_composition):

        app_no = self.application_num_first_edit.text() + "-" + self.application_num_type_edit.text() + "-" \
                     + self.application_num_middle_edit.text() + "-" + self.application_num_last_edit.text()
        try:
                app_status = self.session.query(CtApplicationStatus).filter(
                    CtApplicationStatus.application == app_no).all()
                for p in app_status:
                    if p.status == 1:
                        officer = self.session.query(SetRole).filter(
                            SetRole.user_name_real == p.next_officer_in_charge).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"),
                                   self.tr("aCould not execute: {0}").format(e.message))
        position = ''
        if officer.position != None:
            position = officer.position
            position = self.session.query(ClPositionType).filter(ClPositionType.code == position).one()
            position = position.description

        card_officer_full = position + ' ' + officer.surname[:1] + '.' + officer.first_name
        item = map_composition.getComposerItemById("card_officer_full")
        item.setText(self.__wrap(card_officer_full, 200))
        # item.adjustSizeToText()

    def __duplicate_new_applicant(self, new_person_id):

        is_duplicate = False
        for row in range(self.applicant_twidget.rowCount()):
            person_id = self.applicant_twidget.item(row, APPLICANT_PERSON_ID).text()
            if person_id == new_person_id:
                is_duplicate = True
        return is_duplicate

    def __copy_new_right_holder_from_navigator(self):

        selected_persons = []
        self.create_savepoint()
        application_type_code = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())

        for item in self.navigator.person_results_twidget.selectedItems():
            person_id = item.data(Qt.UserRole)
            if application_type_code == ApplicationType.transfer_possession_right:
                if self.__duplicate_new_applicant(person_id):
                    PluginUtils.show_error(self, self.tr("Invalid Applicant"),
                                           self.tr("This new right holder duplicate applicant."))
                    return
            try:
                person = self.session.query(BsPerson).filter_by(person_id=person_id).one()
                role_ref = self.session.query(ClPersonRole).filter_by(
                    code=Constants.NEW_RIGHT_HOLDER_CODE).one()
                if person.type == Constants.FOREIGN_ENTITY_PERSON_TYPE \
                        or person.type == Constants.STATE_PERSON_TYPE:
                        PluginUtils.show_error(self, self.tr("Error"),
                                               self.tr("#state organisations or entities of "
                                                                               "foreign countries to this application type"))
                        return
                if person.type == Constants.UNCAPABLE_PERSON_TYPE:
                    # PluginUtils.show_error(self, self.tr("Error"),
                    #                            self.tr("Its not allowed to add incapable persons"))

                    message_box = QMessageBox()
                    message_box.setText(self.tr("This person is not aplicable. Do you want to register for this person by legal representative ?"))

                    yes_button = message_box.addButton(self.tr("Yes"), QMessageBox.ActionRole)
                    message_box.addButton(self.tr("No"), QMessageBox.ActionRole)
                    message_box.exec_()

                    if message_box.clickedButton() == yes_button:
                        self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1,
                                                          self.legal_representative_tab, QIcon(),
                                                          self.tr("Legal Representative"))
                        self.is_representative = True
                        # self.__copy_applicant_from_navigator()

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            app_person_role = CtApplicationPersonRole()
            app_person_role.application = self.application.app_no
            app_person_role.share = Decimal(1.0)
            app_person_role.role = Constants.NEW_RIGHT_HOLDER_CODE
            app_person_role.role_ref = role_ref
            app_person_role.person = person.person_id
            app_person_role.person_ref = person
            app_person_role.main_applicant = False

            try:
                self.application.stakeholders.append(app_person_role)

            except SQLAlchemyError, e:
                self.rollback_to_savepoint()
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            selected_persons.append(app_person_role)

        for person in selected_persons:
            self.__add_new_right_holder_item(person)

    def __copy_contract_from_navigator(self):

        selected_contracts = self.navigator.contract_results_twidget.selectedItems()

        if len(selected_contracts) == 0:
            # PluginUtils.show_error(self, self.tr("Query error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        selected_contract = selected_contracts[0]
        current_app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())

        # try:
        contract_no = selected_contract.data(Qt.UserRole)
        contract_count = self.session.query(CtContract).filter_by(contract_no=contract_no).count()

        if contract_count == 0:
            PluginUtils.show_error(self, self.tr("Working Soum"),
                                    self.tr("The selected Contract {0} is not within the working soum. "
                                            "\n \n Change the Working soum to create an "
                                            "application for this contract.").format(contract_no))
            return

        contract = self.session.query(CtContract).filter_by(contract_no=contract_no).one()

        contract_apps = contract.application_roles.all()
        for contract_app in contract_apps:
            app = self.session.query(CtApplication). \
                filter(CtApplication.app_no == contract_app.application).one()
            if app.app8ext:
                app8ext = app.app8ext
                if app8ext.mortgage_status == 10:
                    PluginUtils.show_error(self, self.tr("Error"),
                                           self.tr("The contract {0} is mortgagee!").format(contract_no))
                    return

            if app.app29ext:
                app29ext = app.app29ext
                if app29ext.court_status == 10 or app29ext.court_status == 20:
                    PluginUtils.show_error(self, self.tr("Error"),
                                           self.tr("The contract {0} is court decision!").format(contract_no))
                    return

        contract_app_c = self.session.query(CtContractApplicationRole).\
            join(CtApplication, CtContractApplicationRole.application == CtApplication.app_no).\
            join(CtContract, CtContractApplicationRole.contract == CtContract.contract_no).\
            filter(CtContractApplicationRole.contract == contract_no).\
            filter(CtContract.status == 20).\
            filter(or_(CtApplication.app_type != ApplicationType.mortgage_possession, \
                       CtApplication.app_type != ApplicationType.your_request, \
                       CtApplication.app_type != ApplicationType.court_decision)).count()
        if contract_app_c == 1:
            contract_app = self.session.query(CtContractApplicationRole).\
                join(CtApplication, CtContractApplicationRole.application == CtApplication.app_no).\
                join(CtContract, CtContractApplicationRole.contract == CtContract.contract_no).\
                filter(CtContractApplicationRole.contract == contract_no).\
                filter(CtContract.status == 20).\
                filter(or_(CtApplication.app_type != ApplicationType.mortgage_possession, \
                       CtApplication.app_type != ApplicationType.your_request, \
                       CtApplication.app_type != ApplicationType.court_decision)).one()
            app = self.session.query(CtApplication).\
                filter(CtApplication.app_no == contract_app.application).one()

            landuse_type = app.requested_landuse

            self.requested_land_use_type_cbox.setCurrentIndex(self.requested_land_use_type_cbox.findData(landuse_type))

        # if current_app_type != ApplicationType.encroachment:
        if contract.status == 40:
            PluginUtils.show_error(self, self.tr("Error"),
                                   self.tr("The contract {0} is already cancelled.").format(contract_no))
            return

        if contract.status == 30:
            PluginUtils.show_error(self, self.tr("Error"),
                                   self.tr("The contract {0} is already expired.").format(contract_no))
            return

        applicants_count = self.session.query(CtApplicationPersonRole). \
            join(CtContractApplicationRole,
                 CtApplicationPersonRole.application == CtContractApplicationRole.application). \
            join(CtContract, CtContractApplicationRole.contract == CtContract.contract_no). \
            filter(CtContractApplicationRole.contract == contract_no). \
            filter(CtApplicationPersonRole.role == 70). \
            filter(CtContract.status == 20). \
            filter(CtContractApplicationRole.role == 20).count()

        if applicants_count != 0:
            applicants = self.session.query(CtApplicationPersonRole).\
                join(CtContractApplicationRole, CtApplicationPersonRole.application == CtContractApplicationRole.application).\
                join(CtContract, CtContractApplicationRole.contract == CtContract.contract_no) .\
                filter(CtContractApplicationRole.contract == contract_no). \
                filter(CtApplicationPersonRole.role == 70) . \
                filter(CtContract.status == 20) . \
                filter(CtContractApplicationRole.role == 20).all()
        else:
            applicants = self.session.query(CtApplicationPersonRole). \
                join(CtContractApplicationRole,
                     CtApplicationPersonRole.application == CtContractApplicationRole.application). \
                join(CtContract, CtContractApplicationRole.contract == CtContract.contract_no). \
                filter(CtContractApplicationRole.contract == contract_no). \
                filter(CtApplicationPersonRole.role == 10). \
                filter(CtContract.status == 20). \
                filter(CtContractApplicationRole.role == 20).all()

        for applicant in applicants:
            self.__add_applicant_item(applicant)
            app_person_role_count = self.session.query(CtApplicationPersonRole)\
                .filter(CtApplicationPersonRole.application == self.application.app_no)\
                .filter(CtApplicationPersonRole.person == applicant.person)\
                .filter(CtContractApplicationRole.role == applicant.role).count()
            if app_person_role_count == 0:

                app_person_role = CtApplicationPersonRole()

                app_person_role.application = self.application.app_no
                app_person_role.share = applicant.share
                app_person_role.role = applicant.role
                app_person_role.role_ref = applicant.role_ref
                app_person_role.person = applicant.person
                app_person_role.person_ref = applicant.person_ref
                app_person_role.main_applicant = applicant.main_applicant

                self.application.stakeholders.append(app_person_role)

            application = self.session.query(CtApplication).filter(CtApplication.app_no == applicant.application).one()
            self.parcel_edit.setText(application.parcel)
            parcel = self.session.query(CaParcel.parcel_id, CaParcel.area_m2, CaParcel.landuse, CaParcel.geometry).filter_by(parcel_id=application.parcel).one()
            self.parcel_area_edit.setText(str(parcel.area_m2))
        self.found_contract_number_edit.setText(contract_no)

        if current_app_type == ApplicationType.your_request or current_app_type == ApplicationType.court_decision:
            cancellation_date = PluginUtils.convert_qt_date_to_python(self.date_time_date.date())

            status = self.session.query(ClContractStatus).filter(ClContractStatus.code == 40).one()
            contract = self.session.query(CtContract).filter(CtContract.contract_no == contract_no).one()

            contract.cancellation_date = cancellation_date

            if current_app_type == ApplicationType.your_request:
                cancellation_reason = self.session.query(ClContractCancellationReason).\
                    filter(ClContractCancellationReason.code == 60).one()
                contract.cancellation_reason = cancellation_reason.code
                contract.cancellation_reason_ref = cancellation_reason
            contract.status = status.code
            contract.status_ref = status

        # except SQLAlchemyError, e:
        #     PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __copy_record_from_navigator(self):

        selected_records = self.navigator.record_results_twidget.selectedItems()

        if len(selected_records) == 0:
            # PluginUtils.show_error(self, self.tr("Query error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        selected_record = selected_records[0]
        current_app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())

        # try:
        record_no = selected_record.data(Qt.UserRole)
        record_count = self.session.query(CtOwnershipRecord).filter_by(record_no=record_no).count()

        if record_count == 0:
            PluginUtils.show_error(self, self.tr("Working Soum"),
                                    self.tr("The selected Contract {0} is not within the working soum. "
                                            "\n \n Change the Working soum to create an "
                                            "application for this contract.").format(record_no))
            return

        record = self.session.query(CtOwnershipRecord).filter_by(record_no=record_no).one()
        record_app_c = self.session.query(CtRecordApplicationRole). \
            join(CtOwnershipRecord, CtRecordApplicationRole.record == CtOwnershipRecord.record_no). \
            join(CtApplication, CtRecordApplicationRole.application == CtApplication.app_no).\
            filter(CtOwnershipRecord.record_no == record_no).\
            filter(CtOwnershipRecord.status == 20).\
            filter(or_(CtApplication.app_type != ApplicationType.encroachment,
                       CtApplication.app_type != ApplicationType.your_request,
                       CtApplication.app_type != ApplicationType.court_decision)).count()

        if record_app_c == 1:
            record_app = self.session.query(CtRecordApplicationRole). \
                join(CtOwnershipRecord, CtRecordApplicationRole.record == CtOwnershipRecord.record_no). \
                join(CtApplication, CtRecordApplicationRole.application == CtApplication.app_no). \
                filter(CtOwnershipRecord.record_no == record_no). \
                filter(CtOwnershipRecord.status == 20). \
                filter(or_(CtApplication.app_type != ApplicationType.encroachment,
                       CtApplication.app_type != ApplicationType.your_request,
                       CtApplication.app_type != ApplicationType.court_decision)).one()

            app = self.session.query(CtApplication).\
                filter(CtApplication.app_no == record_app.application).one()

            landuse_type = app.requested_landuse

            self.requested_land_use_type_cbox.setCurrentIndex(self.requested_land_use_type_cbox.findData(landuse_type))

        # if current_app_type != ApplicationType.encroachment:
        if record.status == 30:
            PluginUtils.show_error(self, self.tr("Error"),
                                   self.tr("The contract {0} is already cancelled.").format(record_no))
            return

        applicants = self.session.query(CtApplicationPersonRole).\
            join(CtRecordApplicationRole, CtApplicationPersonRole.application == CtRecordApplicationRole.application).\
            filter(CtRecordApplicationRole.record == record_no).all()

        for applicant in applicants:
            self.__add_applicant_item(applicant)

            app_person_role = CtApplicationPersonRole()

            app_person_role.application = self.application.app_no
            app_person_role.share = applicant.share
            app_person_role.role = applicant.role
            app_person_role.role_ref = applicant.role_ref
            app_person_role.person = applicant.person
            app_person_role.person_ref = applicant.person_ref
            app_person_role.main_applicant = applicant.main_applicant

            self.application.stakeholders.append(app_person_role)
            application = self.session.query(CtApplication).filter(CtApplication.app_no == applicant.application).one()
            if current_app_type != ApplicationType.encroachment:
                if application.parcel:
                    self.parcel_edit.setText(application.parcel)
                    parcel = self.session.query(CaParcel.parcel_id, CaParcel.area_m2, CaParcel.landuse, CaParcel.geometry).filter_by(parcel_id=application.parcel).one()
                    self.parcel_area_edit.setText(str(parcel.area_m2))
        self.relating_record_num_edit.setText(record_no)

        if current_app_type == ApplicationType.encroachment:
            cancellation_date = PluginUtils.convert_qt_date_to_python(self.date_time_date.date())

            status = self.session.query(ClRecordStatus).filter(ClRecordStatus.code == 30).one()
            record = self.session.query(CtOwnershipRecord).filter(CtOwnershipRecord.record_no == record_no).one()

            record.cancellation_date = cancellation_date

            if current_app_type == ApplicationType.your_request:
                cancellation_reason = self.session.query(ClRecordCancellationReason).\
                    filter(ClRecordCancellationReason.code == 40).one()
                record.cancellation_reason = cancellation_reason.code
                record.cancellation_reason_ref = cancellation_reason
            record.status = status.code
            record.status_ref = status

        # except SQLAlchemyError, e:
        #     PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __copy_parcel_from_navigator(self):

        selected_parcels = self.navigator.parcel_results_twidget.selectedItems()

        if len(selected_parcels) == 0:
            PluginUtils.show_error(self, self.tr("Query error"), self.tr("No parcel selected in the Navigator."))
            return

        selected_parcel = selected_parcels[0]
        current_parcel_id = selected_parcel.data(Qt.UserRole)
        parcel_count = self.session.query(CaTmpParcel).filter_by(parcel_id=current_parcel_id).count()
        if parcel_count != 0:
            self.is_tmp_parcel = True
        try:
            current_app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())

            if self.is_tmp_parcel:
                if parcel_count == 0:
                    PluginUtils.show_error(self, self.tr("Working Soum"),
                                            self.tr("The selected Parcel {0} is not within the working soum. "
                                                    "\n \n Change the Working soum to create a new application for "
                                                    "the parcel.").format(current_parcel_id))
                    return


                validation_id = "app_type_{0}_drop_parcel".format(current_app_type)

                set_validation = self.session.query(SetValidation).get(validation_id)

                if set_validation:
                    result = self.session.execute(set_validation.sql_statement.format(current_parcel_id)).fetchall()

                    count = 0
                    for row in result:
                        count = row[0]

                    if count != 0:
                        PluginUtils.show_error(self, self.tr("Working Soum"),
                                                self.tr("There is already an existing application for the parcel {0}").format(current_parcel_id))

                parcel = self.session.query(CaTmpParcel).filter_by(parcel_id=current_parcel_id).one()
                case_id = parcel.maintenance_case
                maintenance_case = self.session.query(CaMaintenanceCase).filter(CaMaintenanceCase.id == case_id).one()
                if maintenance_case.completion_date is None:
                    PluginUtils.show_message(self, self.tr("Maintenance Error"), self.tr("Is not complete"))
                    return
            else:
                status_count = self.session.query(CtApplicationStatus). \
                    join(CtApplication, CtApplicationStatus.application == CtApplication.app_no). \
                    filter(CtApplicationStatus.status > 6). \
                    filter(CtApplication.parcel == current_parcel_id).count()
                if status_count == 0:
                    PluginUtils.show_message(self, self.tr('delete please'), self.tr(
                        'Delete please the parcel. This parcel is not referenced to any applications.'))
                    return
                parcel_count = self.session.query(CaParcel).filter_by(parcel_id=current_parcel_id).count()

                if parcel_count == 0:
                    PluginUtils.show_error(self, self.tr("Working Soum"),
                                            self.tr("The selected Parcel {0} is not within the working soum. "
                                                    "\n \n Change the Working soum to create a new application for "
                                                    "the parcel.").format(current_parcel_id))
                    return


                validation_id = "app_type_{0}_drop_parcel".format(current_app_type)

                set_validation = self.session.query(SetValidation).get(validation_id)

                if set_validation:
                    result = self.session.execute(set_validation.sql_statement.format(current_parcel_id)).fetchall()

                    count = 0
                    for row in result:
                        count = row[0]

                    if count != 0:
                        PluginUtils.show_error(self, self.tr("Working Soum"),
                                                self.tr("There is already an existing application for the parcel {0}").format(current_parcel_id))

                parcel = self.session.query(CaParcel).filter_by(parcel_id=current_parcel_id).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        self.found_parcel_number_edit.setText(parcel.parcel_id)

    def __copy_decision_from_navigator(self):

        selected_decisions = self.navigator.decision_results_twidget.selectedItems()
        if len(selected_decisions) == 0:
            PluginUtils.show_error(self, self.tr("Query error"), self.tr("No decision selected in the Navigator."))
            return

        selected_decision = selected_decisions[0]

        try:
            decision = self.session.query(CtDecision).filter_by(decision_no=selected_decision.data(Qt.UserRole)).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        self.found_decision_edit.setText(decision.decision_no)

    def __is_active_contract(self, person_id):

        active_contract_count = self.session.query(ContractSearch).\
            filter(ContractSearch.person_id == person_id).count()

        if active_contract_count == 0:
            return False
        else:
            return True

    def __is_active_record(self, person_id):

        active_record_count= self.session.query(RecordSearch).\
            filter(RecordSearch.person_id == person_id). \
            filter(RecordSearch.status == 20).count()

        if active_record_count == 0:
            return False
        else:
            return True


    def __copy_applicant_from_navigator(self):

        selected_persons = []
        selected_remain_persons = []
        additional_role = None
        person_role_code = None

        app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())

        for item in self.navigator.person_results_twidget.selectedItems():

            try:
                person = self.session.query(BsPerson).filter_by(person_id=item.data(Qt.UserRole)).one()
                role_ref = self.session.query(ClPersonRole).filter_by(
                    code=Constants.APPLICANT_ROLE_CODE).one()

                #In case of App-type = 2 or App-type = 7 the applicants are the
                #Remaining owners or the old right holder codes

                if app_type == ApplicationType.giving_up_ownership:
                    additional_role = self.session.query(ClPersonRole)\
                        .filter_by(code=Constants.REMAINING_OWNER_CODE).one()
                    person_role_code = Constants.REMAINING_OWNER_CODE
                elif app_type == ApplicationType.transfer_possession_right\
                        or app_type == ApplicationType.change_ownership \
                        or app_type == ApplicationType.possess_split \
                        or app_type == ApplicationType.encroachment \
                        or app_type == ApplicationType.possession_right_use_right:
                    additional_role = self.session.query(ClPersonRole)\
                        .filter_by(code=Constants.OLD_RIGHT_HOLDER_CODE).one()
                    person_role_code = Constants.OLD_RIGHT_HOLDER_CODE

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            app_person_role = CtApplicationPersonRole()
            app_person_role.application = self.application.app_no
            app_person_role.share = Decimal(0.0)
            app_person_role.role_ref = role_ref
            app_person_role.role = Constants.APPLICANT_ROLE_CODE
            app_person_role.person = person.person_id
            app_person_role.person_ref = person
            app_person_role.main_applicant = False
            #self.session.flush()

            if additional_role is not None and person_role_code is not None:
                if app_type == ApplicationType.giving_up_ownership \
                        or app_type == ApplicationType.transfer_possession_right\
                        or app_type == ApplicationType.change_ownership \
                        or app_type == ApplicationType.possess_split \
                        or app_type == ApplicationType.encroachment \
                        or app_type == ApplicationType.possession_right_use_right:

                    app_person_role_remain = CtApplicationPersonRole()
                    app_person_role_remain.application = self.application.app_no
                    app_person_role_remain.share = Decimal(0.0)
                    app_person_role_remain.role_ref = additional_role
                    app_person_role_remain.role = person_role_code
                    app_person_role_remain.person = person.person_id
                    app_person_role_remain.person_ref = person
                    app_person_role_remain.main_applicant = False
                    #self.session.flush()
            try:
                self.application.stakeholders.append(app_person_role)

                if app_type == ApplicationType.giving_up_ownership  \
                    or app_type == ApplicationType.transfer_possession_right\
                    or app_type == ApplicationType.change_ownership \
                        or app_type == ApplicationType.possess_split \
                        or app_type == ApplicationType.encroachment \
                        or app_type == ApplicationType.possession_right_use_right:

                    self.application.stakeholders.append(app_person_role_remain)

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            selected_persons.append(app_person_role)

            if app_type == ApplicationType.giving_up_ownership \
                    or app_type == ApplicationType.change_ownership\
                    or app_type == ApplicationType.transfer_possession_right \
                    or app_type == ApplicationType.possess_split \
                    or app_type == ApplicationType.encroachment \
                    or app_type == ApplicationType.possession_right_use_right:

                selected_remain_persons.append(app_person_role_remain)

        for person in selected_persons:
            self.__add_applicant_item(person)

        if app_type == ApplicationType.giving_up_ownership:
            for owner in selected_remain_persons:
                self.__add_co_ownership_item(owner, Constants.REMAINING_OWNER_CODE)

    def __copy_mortgagee_from_navigator(self):

        selected_persons = []
        self.create_savepoint()

        for item in self.navigator.person_results_twidget.selectedItems():

            try:
                count = self.application.stakeholders.filter_by(person=item.data(Qt.UserRole))\
                                        .filter_by(role=Constants.MORTGAGEE_ROLE_CODE).count()
                if count > 0:
                    PluginUtils.show_message(self, self.tr("Mortgagee"), self.tr("This mortgagee is already added."))
                    return

                count = self.application.stakeholders.filter_by(person=item.data(Qt.UserRole))\
                                        .filter_by(role=Constants.APPLICANT_ROLE_CODE).count()
                if count > 0:
                    PluginUtils.show_message(self, self.tr("Mortgagee"), self.tr("This mortgagee is already applicant."))
                    return

                person = self.session.query(BsPerson).filter_by(person_id=item.data(Qt.UserRole)).one()

                if person.type == Constants.UNCAPABLE_PERSON_TYPE:
                    PluginUtils.show_message(self, self.tr("Mortgagee"), self.tr("A uncapable person can't be added as mortgagee."))
                    return

                role_ref = self.session.query(ClPersonRole) \
                    .filter_by(code=Constants.MORTGAGEE_ROLE_CODE).one()

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            app_person_role = CtApplicationPersonRole()
            app_person_role.application = self.application.app_no
            app_person_role.role_ref = role_ref
            app_person_role = CtApplicationPersonRole()
            app_person_role.share = Decimal(0.0)
            app_person_role.role = Constants.MORTGAGEE_ROLE_CODE
            app_person_role.person = person.person_id
            app_person_role.person_ref = person
            app_person_role.main_applicant = False

            try:
                self.application.stakeholders.append(app_person_role)

            except SQLAlchemyError, e:
                self.rollback_to_savepoint()
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            selected_persons.append(app_person_role)

        for applicant in selected_persons:
            self.__add_mortgagee_item(applicant)

    def __copy_legal_rep_from_navigator(self):

        selected_persons = []

        for item in self.navigator.person_results_twidget.selectedItems():
            try:
                person = self.session.query(BsPerson).filter_by(person_id=item.data(Qt.UserRole)).one()
                role_ref = self.session.query(ClPersonRole).filter_by(
                    code=Constants.LEGAL_REP_ROLE_CODE).one()
            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            if person.type != Constants.MONGOLIAN_CAPABLE:
                PluginUtils.show_message(self, self.tr("Invalid input"),
                                         self.tr("A legal represantative has to be a mongolian capable person."))
                return

            app_person_role = CtApplicationPersonRole()
            app_person_role.application = self.application.app_no
            app_person_role.share = Decimal(1)
            app_person_role.role_ref = role_ref
            app_person_role.role = Constants.LEGAL_REP_ROLE_CODE
            app_person_role.person = person.person_id
            app_person_role.person_ref = person
            app_person_role.main_applicant = False

            try:
                self.application.stakeholders.append(app_person_role)

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            selected_persons.append(app_person_role)

        for person in selected_persons:
            self.__add_legal_rep_item(person)

    def __valid_status(self, status_code):

        count = self.application.statuses.filter(CtApplicationStatus.status == status_code).count()
        if count > 0:
            return False

        return True

    def __add_new_right_holder_item(self, applicant):

        main_item = QTableWidgetItem(QIcon(), "")
        main_item.setCheckState(Qt.Checked) if applicant.main_applicant \
            else main_item.setCheckState(Qt.Unchecked)

        main_item.setData(Qt.UserRole, applicant.person)

        share_item = QTableWidgetItem(str(applicant.share))
        share_item.setData(Qt.UserRole, applicant.person)

        person_id_item = QTableWidgetItem(applicant.person_ref.person_id)
        person_id_item.setData(Qt.UserRole, applicant.person)
        person_id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        surname_item = QTableWidgetItem(applicant.person_ref.name)
        surname_item.setData(Qt.UserRole, applicant.person)
        surname_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        first_name_item = QTableWidgetItem(applicant.person_ref.first_name)
        first_name_item.setData(Qt.UserRole, applicant.person)
        first_name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        inserted_row = self.new_right_holders_twidget.rowCount()

        self.new_right_holders_twidget.insertRow(inserted_row)

        self.new_right_holders_twidget.setItem(inserted_row, APPLICANT_MAIN, main_item)
        self.new_right_holders_twidget.setItem(inserted_row, NEW_RIGHT_HOLDER_SHARE, share_item)
        self.new_right_holders_twidget.setItem(inserted_row, NEW_RIGHT_HOLDER_PERSON_ID, person_id_item)
        self.new_right_holders_twidget.setItem(inserted_row, NEW_RIGHT_HOLDER_SURNAME, surname_item)
        self.new_right_holders_twidget.setItem(inserted_row, NEW_RIGHT_HOLDER_FIRST_NAME, first_name_item)

    def __add_old_right_holder_item(self, applicant):

        share_item = QTableWidgetItem(str(applicant.share))
        share_item.setData(Qt.UserRole, applicant.person)

        person_id_item = QTableWidgetItem(applicant.person_ref.person_id)
        person_id_item.setData(Qt.UserRole, applicant.person)
        person_id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        surname_item = QTableWidgetItem(applicant.person_ref.name)
        surname_item.setData(Qt.UserRole, applicant.person)
        surname_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        first_name_item = QTableWidgetItem(applicant.person_ref.first_name)
        first_name_item.setData(Qt.UserRole, applicant.person)
        first_name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        inserted_row = self.old_right_holders_twidget.rowCount()

        self.old_right_holders_twidget.insertRow(inserted_row)
        self.old_right_holders_twidget.setItem(inserted_row, 0, share_item)
        self.old_right_holders_twidget.setItem(inserted_row, 1, person_id_item)
        self.old_right_holders_twidget.setItem(inserted_row, 2, surname_item)
        self.old_right_holders_twidget.setItem(inserted_row, 3, first_name_item)

    def __add_mortgagee_item(self, applicant):

        share_item = QTableWidgetItem(str(applicant.share))
        share_item.setData(Qt.UserRole, applicant.person)

        person_id_item = QTableWidgetItem(applicant.person_ref.person_id)
        person_id_item.setData(Qt.UserRole, applicant.person)
        person_id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        surname_item = QTableWidgetItem(applicant.person_ref.name)
        surname_item.setData(Qt.UserRole, applicant.person)
        surname_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        first_name_item = QTableWidgetItem(applicant.person_ref.first_name)
        first_name_item.setData(Qt.UserRole, applicant.person)
        first_name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        inserted_row = self.mortgage_twidget.rowCount()

        self.mortgage_twidget.insertRow(inserted_row)
        self.mortgage_twidget.setItem(inserted_row, MORTGAGE_SHARE, share_item)
        self.mortgage_twidget.setItem(inserted_row, MORTGAGE_PERSON_ID, person_id_item)
        self.mortgage_twidget.setItem(inserted_row, MORTGAGE_SURNAME, surname_item)
        self.mortgage_twidget.setItem(inserted_row, MORTGAGE_NAME, first_name_item)

    def __add_co_ownership_item(self, applicant, code):

        main_item = QTableWidgetItem(QIcon(), "")
        main_item.setCheckState(Qt.Checked) if applicant.main_applicant \
            else main_item.setCheckState(Qt.Unchecked)

        main_item.setData(Qt.UserRole, applicant.person)

        person_id_item = QTableWidgetItem(applicant.person_ref.person_id)
        person_id_item.setData(Qt.UserRole, applicant.person)

        surname_item = QTableWidgetItem(applicant.person_ref.name)
        surname_item.setData(Qt.UserRole, applicant.person)

        first_name_item = QTableWidgetItem(applicant.person_ref.first_name)
        first_name_item.setData(Qt.UserRole, applicant.person)

        if code == Constants.REMAINING_OWNER_CODE:
            inserted_row = self.owners_remaining_twidget.rowCount()
            self.owners_remaining_twidget.insertRow(inserted_row)
            self.owners_remaining_twidget.setItem(inserted_row, CO_OWNERSHIP_MAIN, main_item)
            self.owners_remaining_twidget.setItem(inserted_row, CO_OWNERSHIP_PERSON_ID, person_id_item)
            self.owners_remaining_twidget.setItem(inserted_row, CO_OWNERSHIP_SURNAME, surname_item)
            self.owners_remaining_twidget.setItem(inserted_row, CO_OWNERSHIP_FIRST_NAME, first_name_item)

        elif code == Constants.GIVING_UP_OWNER_CODE:
            inserted_row = self.owners_giving_twidget.rowCount()
            self.owners_giving_twidget.insertRow(inserted_row)
            self.owners_giving_twidget.setItem(inserted_row, 0, person_id_item)
            self.owners_giving_twidget.setItem(inserted_row, 1, surname_item)
            self.owners_giving_twidget.setItem(inserted_row, 2, first_name_item)

    def __add_applicant_item(self, applicant):

        try:
            person = self.session.query(BsPerson).filter(BsPerson.person_id == (applicant.person_ref.person_id)).one()
            self.person = person
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        main_item = QTableWidgetItem(QIcon(), "")
        main_item.setCheckState(Qt.Checked) if applicant.main_applicant \
            else main_item.setCheckState(Qt.Unchecked)

        main_item.setData(Qt.UserRole, applicant.person)

        if person.type == 20:
            share_item = QTableWidgetItem(str(0))
            share_item.setData(Qt.UserRole, applicant.person)
        else:
            share_item = QTableWidgetItem(str(applicant.share))
            share_item.setData(Qt.UserRole, applicant.person)

        person_id_item = QTableWidgetItem(applicant.person_ref.person_id)
        person_id_item.setData(Qt.UserRole, applicant.person)
        person_id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        surname_item = QTableWidgetItem(applicant.person_ref.name)
        surname_item.setData(Qt.UserRole, applicant.person)
        surname_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        first_name_item = QTableWidgetItem(applicant.person_ref.first_name)
        first_name_item.setData(Qt.UserRole, applicant.person)
        first_name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        inserted_row = self.applicant_twidget.rowCount()

        self.applicant_twidget.insertRow(inserted_row)
        self.applicant_twidget.setItem(inserted_row, APPLICANT_MAIN, main_item)
        self.applicant_twidget.setItem(inserted_row, APPLICANT_SHARE, share_item)
        self.applicant_twidget.setItem(inserted_row, APPLICANT_PERSON_ID, person_id_item)
        self.applicant_twidget.setItem(inserted_row, APPLICANT_SURNAME, surname_item)
        self.applicant_twidget.setItem(inserted_row, APPLICANT_FIRST_NAME, first_name_item)

    def __add_legal_rep_item(self, legal_rep):

        item_person_id = QTableWidgetItem(legal_rep.person_ref.person_id)
        item_person_id.setData(Qt.UserRole, legal_rep.person)
        item_person_id.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        item_surname = QTableWidgetItem(legal_rep.person_ref.name)
        item_surname.setData(Qt.UserRole, legal_rep.person)
        item_surname.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        item_fistname = QTableWidgetItem(legal_rep.person_ref.first_name)
        item_fistname.setData(Qt.UserRole, legal_rep.person)
        item_fistname.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        if legal_rep.person_ref.date_of_birth:
            date_of_birth = QDate(legal_rep.person_ref.date_of_birth)
            years = int(date_of_birth.daysTo(QDate().currentDate()) / 365.25)

            item_age = QTableWidgetItem(str(years))
            item_age.setData(Qt.UserRole, legal_rep.person)
            item_age.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        inserted_row = self.legal_rep_twidget.rowCount()

        self.legal_rep_twidget.insertRow(inserted_row)
        self.legal_rep_twidget.setItem(inserted_row, LEGAL_REP_PERSON_ID, item_person_id)
        self.legal_rep_twidget.setItem(inserted_row, LEGAL_REP_SURNAME, item_surname)
        self.legal_rep_twidget.setItem(inserted_row, LEGAL_REP_FIRST_NAME, item_fistname)
        if legal_rep.person_ref.date_of_birth:
            self.legal_rep_twidget.setItem(inserted_row, LEGAL_REP_AGE, item_age)

    def __add_application_status_item(self, status):

        item_status = QTableWidgetItem(status.status_ref.description)
        item_status.setData(Qt.UserRole, status.status_ref.code)
        item_date = QTableWidgetItem(status.status_date.isoformat())

        next_officer = status.next_officer_in_charge_ref.surname + ", " + status.next_officer_in_charge_ref.first_name
        officer = status.officer_in_charge_ref.surname + ", " + status.officer_in_charge_ref.first_name

        item_next_officer = QTableWidgetItem(next_officer)
        item_next_officer.setData(Qt.UserRole, status.next_officer_in_charge)

        item_officer = QTableWidgetItem(officer)
        item_officer.setData(Qt.UserRole, status.officer_in_charge)

        row = self.application_status_twidget.rowCount()
        self.application_status_twidget.insertRow(row)

        self.application_status_twidget.setItem(row, STATUS_STATE, item_status)
        self.application_status_twidget.setItem(row, STATUS_DATE, item_date)
        self.application_status_twidget.setItem(row, STATUS_OFFICER, item_officer)
        self.application_status_twidget.setItem(row, STATUS_NEXT_OFFICER, item_next_officer)

    def __app_type_visible(self):

        application_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())

        if application_type == 8:
            self.applicants_group_box.setEnabled(False)
            self.search_parcel_num_edit.setEnabled(False)
            self.accept_parcel_number_button.setEnabled(False)

    def __generate_application_number(self):

        au_level2 = DatabaseUtils.current_working_soum_schema()
        application_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())

        if au_level2 is None or application_type is None:
            return

        if self.attribute_update:
            return

        self.application_num_first_edit.setText(au_level2)
        self.application_num_type_edit.setText(str(application_type).zfill(2))
        app_type_filter = "%-" + str(application_type).zfill(2) + "-%"
        soum_filter = str(au_level2) + "-%"
        year_filter = "%-" + str(QDate().currentDate().toString("yy"))

        try:

            count = self.session.query(CtApplication).filter(CtApplication.app_no != self.application.app_no) \
                        .filter(CtApplication.app_no.like("%-%"))\
                        .filter(CtApplication.app_no.like(app_type_filter))  \
                        .filter(CtApplication.app_no.like(soum_filter)) \
                        .filter(CtApplication.app_no.like(year_filter)) \
                    .order_by(func.substr(CtApplication.app_no, 10, 14).desc()).count()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        if count > 0:
            try:
                max_number_app = self.session.query(CtApplication)\
                    .filter(CtApplication.app_no != self.application.app_no) \
                    .filter(CtApplication.app_no.like("%-%"))\
                    .filter(CtApplication.app_no.like(app_type_filter)) \
                    .filter(CtApplication.app_no.like(soum_filter)) \
                    .filter(CtApplication.app_no.like(year_filter)) \
                    .order_by(func.substr(CtApplication.app_no, 10, 14).desc()).first()
            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            app_no_numbers = max_number_app.app_no.split("-")

            self.application_num_middle_edit.setText(str(int(app_no_numbers[2]) + 1).zfill(5))

        else:
            self.application_num_middle_edit.setText("00001")

        self.application_num_last_edit.setText(QDate().currentDate().toString("yy"))

    def __update_decision_tab(self):

        # Enables the Decision Tab if the Status is >= 5
        self.application_tab_widget.removeTab(self.application_tab_widget.indexOf(self.decision_tab))
        decision_tab_enabled = False

        for status in self.application.statuses:
            if status.status_ref.code > Constants.DECISION_AVAILABLE_CODE:
                decision_tab_enabled = True

        if decision_tab_enabled:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.decision_tab,
                                                  self.tr("Decision"))

            try:

                decision_count = self.session.query(CtDecision).join(CtDecisionApplication.decision_ref)\
                    .filter(CtDecisionApplication.application == self.application.app_no).count()
                if decision_count > 0:
                    decision = self.session.query(CtDecision).join(CtDecisionApplication.decision_ref)\
                        .filter(CtDecisionApplication.application == self.application.app_no).one()

                    self.decision_number_edit.setText(decision.decision_no)
                    self.decision_date_edit.setText(PluginUtils.convert_python_date_to_qt(decision.decision_date)
                                                    .toString(Constants.DATE_FORMAT))
                    self.decision_level_edit.setText(decision.decision_level_ref.description)

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __set_visible_tabs(self):

        app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())
        right_type = self.rigth_type_cbox.itemData(self.rigth_type_cbox.currentIndex())

        self.application_tab_widget.removeTab(self.application_tab_widget.indexOf(self.legal_representative_tab))
        self.application_tab_widget.removeTab(self.application_tab_widget.indexOf(self.change_of_co_ownership_tab))
        self.application_tab_widget.removeTab(self.application_tab_widget.indexOf(self.transfer_tab))
        self.application_tab_widget.removeTab(self.application_tab_widget.indexOf(self.relating_contract_tab))
        self.application_tab_widget.removeTab(self.application_tab_widget.indexOf(self.new_contract_tab))
        self.application_tab_widget.removeTab(self.application_tab_widget.indexOf(self.mortgage_tab))
        self.application_tab_widget.removeTab(self.application_tab_widget.indexOf(self.decision_tab))
        self.application_tab_widget.removeTab(self.application_tab_widget.indexOf(self.cancel_contract_tab))
        self.application_tab_widget.removeTab(self.application_tab_widget.indexOf(self.relating_record_tab))
        self.application_tab_widget.removeTab(self.application_tab_widget.indexOf(self.record_cancelled_tab))
        self.application_tab_widget.removeTab(self.application_tab_widget.indexOf(self.created_record_tab))

        self.first_time_ownership_group_box.setVisible(False)
        self.requested_year_spin_box.setVisible(False)
        self.approved_year_spin_box.setVisible(False)
        self.duration_approved_label.setVisible(False)
        self.duration_request_label.setVisible(False)

        self.__landuse_per_application_type(app_type)

        # type: 1
        # creates new ownership-record
        if app_type == ApplicationType.privatization:
            self.document_tab.setEnabled(True)
            self.applicants_tab.setEnabled(True)
            self.application_detail_tab.setEnabled(True)
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.created_record_tab,
                                                  self.tr("Record Created"))

            self.first_time_ownership_group_box.setVisible(True)
            self.requested_year_spin_box.setVisible(False)
            self.approved_year_spin_box.setVisible(False)
            self.duration_approved_label.setVisible(False)
            self.duration_request_label.setVisible(False)

        # type: 2
        # deletes old ownership-record
        #creates new ownership-record
        elif app_type == ApplicationType.giving_up_ownership:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1,
                                                  self.change_of_co_ownership_tab, QIcon(),
                                                  self.tr("Change Of Co-Ownership"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.record_cancelled_tab,
                                                  self.tr("Record Cancelled"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.created_record_tab,
                                                  self.tr("Record Created"))

            self.requested_year_spin_box.setVisible(False)
            self.approved_year_spin_box.setVisible(False)
            self.duration_approved_label.setVisible(False)
            self.duration_request_label.setVisible(False)

        #type: 3
        #Creates new Ownership-Record
        elif app_type == ApplicationType.privatization_representation:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1,
                                                  self.legal_representative_tab, QIcon(),
                                                  self.tr("Legal Representative"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.created_record_tab,
                                                  self.tr("Record Created"))

            self.first_time_ownership_group_box.setVisible(True)

            self.requested_year_spin_box.setVisible(False)
            self.approved_year_spin_box.setVisible(False)
            self.duration_approved_label.setVisible(False)
            self.duration_request_label.setVisible(False)

        #type: 4
        #Creates new Ownership-Record
        elif app_type == ApplicationType.buisness_from_state:
            self.first_time_ownership_group_box.setVisible(True)
            self.document_tab.setEnabled(True)
            self.applicants_tab.setEnabled(True)
            self.application_detail_tab.setEnabled(True)
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.created_record_tab,
                                                  self.tr("Record Created"))

            self.requested_year_spin_box.setVisible(False)
            self.approved_year_spin_box.setVisible(False)
            self.duration_approved_label.setVisible(False)
            self.duration_request_label.setVisible(False)

        #type: 5
        #Creates new Contract
        elif app_type == ApplicationType.possession_right:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.new_contract_tab,
                                                  QIcon(), self.tr("Contract Created"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)
        #type: 6
        #Creates new Contract
        elif app_type == ApplicationType.use_right:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.new_contract_tab,
                                                  QIcon(), self.tr("Contract Created"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        #type: 7
        #Creates new Contract
        #Deletes old Contract
        elif app_type == ApplicationType.transfer_possession_right:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.transfer_tab, QIcon(),
                                                  self.tr("Transfer Of Right"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.new_contract_tab,
                                                  QIcon(), self.tr("Contract Created"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.cancel_contract_tab,
                                                  QIcon(), self.tr("Contract Cancelled"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        #type: 8
        #Relates to Contract
        elif app_type == ApplicationType.mortgage_possession:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.relating_contract_tab,
                                                  QIcon(), self.tr("Relating Contract"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.mortgage_tab, QIcon(),
                                                  self.tr("Mortgagee"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        #type: 9
        #Creates new Contract/Ownership-Record
        #Deletes Contract/Ownership-Record
        elif app_type == ApplicationType.change_land_use:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.cancel_contract_tab,
                                                  QIcon(), self.tr("Contract Cancelled"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.record_cancelled_tab,
                                                  QIcon(), self.tr("Record Cancelled"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.new_contract_tab,
                                                  QIcon(), self.tr("Contract Created"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.created_record_tab,
                                                  QIcon(), self.tr("Record Created"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        #type: 10
        #Creates new Contract
        #Deletes old Contract
        elif app_type == ApplicationType.extension_possession:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.cancel_contract_tab,
                                                  QIcon(), self.tr("Contract Cancelled"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.new_contract_tab,
                                                  QIcon(), self.tr("Contract Created"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        #type: 11
        #Relates to Contract
        elif app_type == ApplicationType.possession_right_use_right:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.transfer_tab, QIcon(),
                                                  self.tr("Transfer Of Right"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.relating_contract_tab,
                                                  QIcon(), self.tr("Relating Contract"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        #type: 12
        #Relates to Contract
        elif app_type == ApplicationType.reissue_possession_use_right:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.relating_contract_tab,
                                                  QIcon(), self.tr("Relating Contract"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        #type: 13
        #Creates new Contract/Ownership-Record
        #Deletes Contract/Ownership-Record
        elif app_type == ApplicationType.change_of_area:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.cancel_contract_tab,
                                                  QIcon(), self.tr("Contract Cancelled"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.new_contract_tab,
                                                  QIcon(), self.tr("Contract Created"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.created_record_tab,
                                                  QIcon(), self.tr("Record Created"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        #type: 14
        #Creates new Contract
        #Deletes old Contract
        elif app_type == ApplicationType.encroachment:
            # self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.transfer_tab, QIcon(),
            #                                       self.tr("Transfer Of Right"))
            # self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.cancel_contract_tab,
            #                                       QIcon(), self.tr("Contract Cancelled"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.record_cancelled_tab,
                                                  QIcon(), self.tr("Record Cancelled"))
            # self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.new_contract_tab,
            #                                       QIcon(), self.tr("Contract Created"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.created_record_tab,
                                                  QIcon(), self.tr("Record Created"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.relating_record_tab,
                                                  QIcon(), self.tr("Relateing Record"))

            self.requested_year_spin_box.setVisible(False)
            self.approved_year_spin_box.setVisible(False)
            self.duration_approved_label.setVisible(False)
            self.duration_request_label.setVisible(False)

        #type:15
        #Creates new Ownership-Record
        #Deletes old Ownership-Record
        elif app_type == ApplicationType.change_ownership:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.transfer_tab, QIcon(),
                                                  self.tr("Transfer Of Right"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.record_cancelled_tab,
                                                  QIcon(), self.tr("Record Cancelled"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.created_record_tab,
                                                  QIcon(), self.tr("Record Created"))

            self.requested_year_spin_box.setVisible(False)
            self.approved_year_spin_box.setVisible(False)
            self.duration_approved_label.setVisible(False)
            self.duration_request_label.setVisible(False)

        #type:16
        elif app_type == ApplicationType.auctioning_owner:
            self.requested_year_spin_box.setVisible(False)
            self.approved_year_spin_box.setVisible(False)
            self.duration_approved_label.setVisible(False)
            self.duration_request_label.setVisible(False)

        #type:17
        elif app_type == ApplicationType.auctioning_possess:
            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        #type:18
        elif app_type == ApplicationType.auctioning_use:
            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        #type: 19
        #Creates new Contract
        elif app_type == 19:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.new_contract_tab,
                                                  QIcon(), self.tr("Contract Created"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        #type: 20
        #Creates new Contract
        elif app_type == 20:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.new_contract_tab,
                                                  QIcon(), self.tr("Contract Created"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        #type: 21
        #Creates new Contract
        elif app_type == 21:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.new_contract_tab,
                                                  QIcon(), self.tr("Contract Created"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)
        #type: 22
        #Creates new Contract
        elif app_type == ApplicationType.special_use:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.new_contract_tab,
                                                  QIcon(), self.tr("Contract Created"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        # type: 23

        elif app_type == ApplicationType.possess_split:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.transfer_tab, QIcon(),
                                                  self.tr("Transfer Of Right"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.new_contract_tab,
                                                  QIcon(), self.tr("Contract Created"))
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.cancel_contract_tab,
                                                  QIcon(), self.tr("Contract Cancelled"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        # type: 24
        elif app_type == ApplicationType.advantage_possess:
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.new_contract_tab,
                                                  QIcon(), self.tr("Contract Created"))

            self.requested_year_spin_box.setVisible(True)
            self.approved_year_spin_box.setVisible(True)
            self.duration_approved_label.setVisible(True)
            self.duration_request_label.setVisible(True)

        # type: 25
        # Creates new Ownership-Record
        elif app_type == ApplicationType.advantage_ownership:
            self.document_tab.setEnabled(True)
            self.applicants_tab.setEnabled(True)
            self.application_detail_tab.setEnabled(True)
            self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.created_record_tab,
                                                  self.tr("Record Created"))

            self.requested_year_spin_box.setVisible(False)
            self.approved_year_spin_box.setVisible(False)
            self.duration_approved_label.setVisible(False)
            self.duration_request_label.setVisible(False)

        # type: 28
        # Relates to Contract
        elif app_type == ApplicationType.your_request:
            if right_type != 3:
                self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.relating_contract_tab,
                                                      QIcon(), self.tr("Relating Contract"))
                self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.cancel_contract_tab,
                                                      QIcon(), self.tr("Contract Cancelled"))

                self.requested_year_spin_box.setVisible(True)
                self.approved_year_spin_box.setVisible(True)
                self.duration_approved_label.setVisible(True)
                self.duration_request_label.setVisible(True)
            elif right_type == 3:
                self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1,
                                                      self.record_cancelled_tab,
                                                      QIcon(), self.tr("Record Cancelled"))

                self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1, self.relating_record_tab,
                                                      QIcon(), self.tr("Relateing Record"))

                self.requested_year_spin_box.setVisible(False)
                self.approved_year_spin_box.setVisible(False)
                self.duration_approved_label.setVisible(False)
                self.duration_request_label.setVisible(False)
        # type: 29
        # Relates to Contract
        elif app_type == ApplicationType.court_decision:
            if right_type != 3:
                self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1,
                                                      self.relating_contract_tab,
                                                      QIcon(), self.tr("Relating Contract"))

                self.requested_year_spin_box.setVisible(True)
                self.approved_year_spin_box.setVisible(True)
                self.duration_approved_label.setVisible(True)
                self.duration_request_label.setVisible(True)

                self.contract_court_decision_label.setVisible(True)
                self.contract_court_status_cbox.setVisible(True)
                self.contract_court_start_label.setVisible(True)
                self.contract_court_end_label.setVisible(True)
                self.contract_court_start_date_edit.setVisible(True)
                self.contract_court_end_date_edit.setVisible(True)
            elif right_type == 3:
                self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1,
                                                      self.record_cancelled_tab,
                                                      QIcon(), self.tr("Record Cancelled"))

                self.application_tab_widget.insertTab(self.application_tab_widget.count() - 1,
                                                      self.relating_record_tab,
                                                      QIcon(), self.tr("Relateing Record"))

                self.requested_year_spin_box.setVisible(False)
                self.approved_year_spin_box.setVisible(False)
                self.duration_approved_label.setVisible(False)
                self.duration_request_label.setVisible(False)

                self.record_court_decision_label.setVisible(True)
                self.record_court_status_cbox.setVisible(True)
                self.record_court_start_label.setVisible(True)
                self.record_court_end_label.setVisible(True)
                self.record_court_start_date_edit.setVisible(True)
                self.record_court_end_date_edit.setVisible(True)

        self.application_tab_widget.setCurrentIndex(0)

    def __is_contract_query(self, application_type):

        result = True if application_type in Constants.CONTRACT_TYPES else False
        return result

    def __update_applicant_cbox(self):

        self.applicant_documents_cbox.clear()
        self.updating = True
        for applicant in self.application.stakeholders:
            if applicant.role == Constants.APPLICANT_ROLE_CODE:
                person = self.session.query(BsPerson.person_id, BsPerson.name, BsPerson.first_name).filter_by(person_id=applicant.person).one()
                if person.first_name is None:
                    person_label = u"{0}".format(person.name)
                else:
                    person_label = u"{0}, {1}".format(person.name, person.first_name)
                self.applicant_documents_cbox.addItem(person_label, person.person_id)
        self.updating = False

        # if self.applicant_documents_cbox.count() > 0:
        #     self.__update_documents_twidget()

    def __remove_old_right_holder(self, person_id):

        for row in range(self.old_right_holders_twidget.rowCount()):
            item = self.old_right_holders_twidget.item(row, 0)

            if item is not None and item.data(Qt.UserRole) == person_id:
                self.old_right_holders_twidget.removeRow(row)
                return

    def __remove_person_from_co_ownership_twidgets(self, person_id, person_role):

        if person_role == Constants.REMAINING_OWNER_CODE:
            for row in range(self.owners_remaining_twidget.rowCount()):
                item = self.owners_remaining_twidget.item(row, 0)
                if item.data(Qt.UserRole) == person_id:
                    self.owners_remaining_twidget.removeRow(row)
                    return

        elif person_role == Constants.GIVING_UP_OWNER_CODE:
            for row in range(self.owners_giving_twidget.rowCount()):
                item = self.owners_giving_twidget.item(row, 0)
                if item.data(Qt.UserRole) == person_id:
                    self.owners_giving_twidget.removeRow(row)
                    return

    def __double_applicant(self, person_id):

        try:
            count = self.application.stakeholders.filter_by(person=person_id)\
                                    .filter_by(role=Constants.APPLICANT_ROLE_CODE).count()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return True

        if count > 0:
            return True

        return False

    def __valid_applicant_person(self, app_type_code, person_type_code):

        try:
            count = self.session.query(SetPersonTypeApplicationType).filter_by(application_type=app_type_code) \
                .filter_by(person_type=person_type_code).filter_by((SetPersonTypeApplicationType.person_type==10, SetPersonTypeApplicationType.person_type==20)).count()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return False

        if count > 0:
            return True
        else:
            return False

    def __valid_applicant(self, app_type_code, person_type_code):

        try:
            count = self.session.query(SetPersonTypeApplicationType).filter_by(application_type=app_type_code) \
                .filter_by(person_type=person_type_code).count()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return False

        if count > 0:
            return True
        else:
            return False

    def __remove_remaining_owners(self):

        while self.owners_remaining_twidget.rowCount() > 0:
            self.owners_remaining_twidget.removeRow(0)

    def __applicant_in_ownership_widget(self, applicant_id):
        for row in range(self.owners_remaining_twidget.rowCount()):
            item = self.owners_remaining_twidget.item(row, 0)
            if item.data(Qt.UserRole) == applicant_id:
                return True

        for row in range(self.owners_giving_twidget.rowCount()):
            item = self.owners_giving_twidget.item(row, 0)
            if item.data(Qt.UserRole) == applicant_id:
                return True

        return False

    def __fade_status_message(self):

        opacity = int(self.time_counter * 0.5)
        self.status_label.setStyleSheet("QLabel {color: rgba(255,0,0," + str(opacity) + ");}")
        self.status_label.setText(self.tr('Changes applied successfully.'))
        if self.time_counter == 0:
            self.timer.stop()
        self.time_counter -= 1

    def __start_fade_out_timer(self):

        self.timer = QTimer()
        self.timer.timeout.connect(self.__fade_status_message)
        self.time_counter = 500
        self.timer.start(10)

    @pyqtSlot()
    def on_help_button_clicked(self):

        app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())

        if app_type == 01:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_1_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_1_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_1_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_1_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_1_current_record.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_1_print.htm")
        if app_type == 02:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_2_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_2_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_2_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_2_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_2_change_of_Co-Ownership.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_2_record_cancelled.htm")
            elif self.application_tab_widget.currentIndex() == 6:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_2_record_Created.htm")
            elif self.application_tab_widget.currentIndex() == 7:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_2_print.htm")
        if app_type == 03:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_3_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_3_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_3_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_3_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_3_legal_representative.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_3_record_Created.htm")
            elif self.application_tab_widget.currentIndex() == 6:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_3_print.htm")
        if app_type == 04:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_4_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_4_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_4_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_4_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_4_record_Created.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_4_print.htm")
        if app_type == 05:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_5_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_5_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_5_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_5_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_5_contract.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_5_print.htm")
        if app_type == 06:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_6_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_6_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_6_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_6_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_6_contract.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_6_print.htm")
        if app_type == 07:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_7_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_7_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_7_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_7_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_7_transfer_of_Rigth.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_7_contract.htm")
            elif self.application_tab_widget.currentIndex() == 6:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_7_contract_cancelled.htm")
            elif self.application_tab_widget.currentIndex() == 7:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_7_print.htm")
        if app_type == 8:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_8_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_8_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_8_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_8_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_8_relating_Contract.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_8_mortgagee.htm")
            elif self.application_tab_widget.currentIndex() == 6:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_8_print.htm")
        if app_type == 9:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_9_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_9_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_9_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_9_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_9_contract_cancelled.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_9_record_cancelled.htm")
            elif self.application_tab_widget.currentIndex() == 6:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_9_contract.htm")
            elif self.application_tab_widget.currentIndex() == 7:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_9_record_Created.htm")
            elif self.application_tab_widget.currentIndex() == 8:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_9_print.htm")
        if app_type == 10:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_10_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_10_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_10_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_10_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_10_contract_cancelled.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_contract_created.htm")
            elif self.application_tab_widget.currentIndex() == 6:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_10_print.htm")
        if app_type == 11:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_11_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_11_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_11_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_11_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_11_transfer_of_Rigth.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_11_relating_Contract.htm")
            elif self.application_tab_widget.currentIndex() == 6:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_11_print.htm")
        if app_type == 12:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_12_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_12_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_12_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_12_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_12_relating_Contract.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_12_print.htm")
        if app_type == 13:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_13_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_13_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_13_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_13_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_13_contract_cancelled.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_13_contract.htm")
            elif self.application_tab_widget.currentIndex() == 6:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_13_record_Created.htm ")
            elif self.application_tab_widget.currentIndex() == 7:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_13_print.htm")
        if app_type == 14:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_14_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_14_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_14_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_14_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_14_transfer_of_Rigth.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_14_contract_cancelled.htm")
            elif self.application_tab_widget.currentIndex() == 6:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_14_record_cancelled.htm")
            elif self.application_tab_widget.currentIndex() == 7:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_14_record_cancelled.htm")
            elif self.application_tab_widget.currentIndex() == 8:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_record_created.htm")
            elif self.application_tab_widget.currentIndex() == 9:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_14_print.htm")
        if app_type == 15:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_15_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_15_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_15_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_15_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_15_transfer_of_Rigth.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_15_record_cancelled.htm")
            elif self.application_tab_widget.currentIndex() == 6:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_record_created.htm")
            elif self.application_tab_widget.currentIndex() == 7:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_15_print.htm")
        if app_type == 16:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_16_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_16_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_16_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_16_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_16_print.htm")
        if app_type == 17:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_17_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_17_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_17_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_17_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_17_print.htm")
        if app_type == 18:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_18_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_18_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_18_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_18_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_18_print.htm")
        if app_type == 19:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_19_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_19_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_19_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_19_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_19_print.htm")
        if app_type == 20:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_20_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_20_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_20_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_20_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_20_print.htm")
        if app_type == 21:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_21_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_21_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_21_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_21_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_21_print.htm")

        if app_type == 22:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_22_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_22_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_22_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_22_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_22_print.htm")
        if app_type == 23:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_23_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_23_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_23_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_23_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_23_transfer_of_Rigth.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_23_contract_cancelled.htm")
            elif self.application_tab_widget.currentIndex() == 6:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_23_print.htm")
        if app_type == 24:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_24_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_24_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_24_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_24_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_24_contract.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_23_print.htm")

        if app_type == 25:
            if self.application_tab_widget.currentIndex() == 0:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_25_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_25_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_25_attachments.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_25_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_25_record_Created.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                          :-10]) + "help\output\help_lm2.chm::/html/application_25_print.htm")