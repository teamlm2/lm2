# coding=utf8

__author__ = 'B.Ankhbold'

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
from ..model.BsPerson import *
from ..model.ClPersonRole import *
from ..model.ClPositionType import *
from ..model.ClPastureType import *
from ..model.CtContractApplicationRole import *
from ..model.CtRecordApplicationRole import *
from ..model.CtApplicationStatus import *
from ..model.CtOwnershipRecord import *
from ..model.CaTmpParcel import *
from ..model.CaPastureParcel import *
from ..model.CaPUGBoundary import *
from ..model.CtDecision import *
from ..model.CtDecisionApplication import *
from ..model.ClPastureDocument import *
from ..model.SetPastureDocument import *
from ..model.SetPersonTypeApplicationType import *
from ..model.SetApplicationTypeLanduseType import *
from ..model.SetValidation import *
from ..model.DatabaseHelper import *
from ..model.AuLevel3 import *
from ..model import SettingsConstants
from ..model import ConstantsPasture
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.MaintenanceSearch import *
from ..model.EnumerationsPasture import ApplicationType, UserRight
from ..model.CtPersonGroup import *
from ..model.CtApplicationPUG import *
from ..model.CtApplicationPUGParcel import *
from ..model.CtApplicationParcelPasture import *
from ..model.CtGroupMember import *
from ..model.CtAppGroupBoundary import *
from .qt_classes.PastureApplicationDocumentDelegate import PastureApplicationDocumentDelegate
from .qt_classes.DocumentsTableWidget import DocumentsTableWidget
from .qt_classes.DragTreeWidget import DragTreeWidget
from .qt_classes.DoubleSpinBoxDelegate import DoubleSpinBoxDelegate
from .qt_classes.ComboBoxDelegate import *
from .qt_classes.IntegerSpinBoxDelegate import *
from ..view.Ui_ApplicationsPastureDialog import *
from ..model.PersonSearch import *
from ..model.BsPerson import *
from ..utils.SessionHandler import SessionHandler
from ..utils.PluginUtils import PluginUtils
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.PasturePath import *
from ..utils.LayerUtils import *

DOC_PROVIDED_COLUMN = 0
DOC_FILE_TYPE_COLUMN = 1
DOC_FILE_NAME_COLUMN = 2
DOC_OPEN_FILE_COLUMN = 3
DOC_DELETE_COLUMN = 4
DOC_VIEW_COLUMN = 5
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


class ApplicationsPastureDialog(QDialog, Ui_ApplicationsPastureDialog, DatabaseHelper):

    def __init__(self, plugin,application, navigator, attribute_update=False, parent=None):

        super(ApplicationsPastureDialog, self).__init__(parent)
        DatabaseHelper.__init__(self)
        self.plugin = plugin
        self.navigator = navigator
        self.attribute_update = attribute_update

        self.session = SessionHandler().session_instance()
        self.application = application

        self.timer = None
        self.last_row = None
        self.last_tab = -1
        self.updating = False

        self.applicant_twidget = None
        self.documents_twidget = None
        self.person = None
        self.is_tmp_parcel = False
        self.setupUi(self)
        self.close_button.clicked.connect(self.reject)

        self.__setup_combo_boxes()
        self.__set_up_pasture_type_twidget()
        self.__setup_ui()
        self.__setup_permissions()

    #public functions

    def __set_up_twidget(self, table_widget):

        table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        header = table_widget.horizontalHeader()
        header.setResizeMode(QHeaderView.Stretch)

    def __set_up_pasture_type_twidget(self):

        self.pasture_type_twidget.setAlternatingRowColors(True)
        self.pasture_type_twidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.pasture_type_twidget.setSelectionMode(QTableWidget.SingleSelection)

        month_list = ['1','2','3','4','5','6','7','8','9','10','11','12']

        delegate = ComboBoxDelegate(1, month_list, self.pasture_type_twidget)
        self.pasture_type_twidget.setItemDelegateForColumn(1, delegate)

        delegate = ComboBoxDelegate(2, month_list, self.pasture_type_twidget)
        self.pasture_type_twidget.setItemDelegateForColumn(2, delegate)

        delegate = IntegerSpinBoxDelegate(3, 30, 365, 30, 1, self.pasture_type_twidget)
        self.pasture_type_twidget.setItemDelegateForColumn(3, delegate)

        self.pasture_type_twidget.cellChanged.connect(self.on_pasture_type_twidget_cellChanged)

    @pyqtSlot(int, int)
    def on_pasture_type_twidget_cellChanged(self, row, column):

        days = 0
        if column == 1:
            if self.pasture_type_twidget.item(row, column+1):
                begin_month = self.pasture_type_twidget.item(row, column).text()
                end_month = self.pasture_type_twidget.item(row, 2).text()
                if int(end_month) - int(begin_month) < 0:
                    days = (int(end_month)+(12-int(begin_month)))*30
                else:
                    days = (int(end_month) - int(begin_month))*30

                days_item = self.pasture_type_twidget.item(row, 3)
                days_item.setText(str(days))
                days_item.setData(Qt.UserRole, days)
        elif column == 2:
            if self.pasture_type_twidget.item(row, 3):
                begin_month = self.pasture_type_twidget.item(row, 1).text()
                end_month = self.pasture_type_twidget.item(row, column).text()

                if int(end_month) - int(begin_month) < 0:
                    days = (int(end_month)+(12-int(begin_month)))*30
                else:
                    days = (int(end_month) - int(begin_month))*30

                days_item = self.pasture_type_twidget.item(row, 3)
                days_item.setText(str(days))
                days_item.setData(Qt.UserRole, days)

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

        self.document_path_edit.setText(PasturePath.app_file_path()+'/'+self.application.app_no)
        self.share_spinbox = QDoubleSpinBox()
        self.share_spinbox.setDecimals(2)
        self.share_spinbox.setMaximum(1.0)
        self.share_spinbox.setValue(1.0)
        self.share_spinbox.setSingleStep(0.1)

        self.status_date_date.setDate(QDate().currentDate())

        if self.attribute_update:
            self.__setup_mapping()
        else:
            self.date_time_date.setDateTime(QDateTime.currentDateTime())

        try:
            self.__setup_person_twidget()
            self.__setup_status_widget()
            self.__setup_documents_twidget()
            self.__setup_applicant_twidget()
            self.__setup_parcels_twidget()

        except LM2Exception, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __setup_mapping(self):

        try:
            status_count = self.session.query(CtApplicationStatus)\
                .filter(CtApplication.app_no == self.application.app_no)\
                .filter(CtApplicationStatus.status >= 5).count()
            if status_count > 0:
                self.requested_land_use_type_cbox.setEnabled(False)

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

        if self.application.requested_duration:
            self.requested_year_spin_box.setValue(self.application.requested_duration)

        if self.application.approved_duration:
            self.approved_year_spin_box.setValue(self.application.approved_duration)

        self.remarks_text_edit.setText(self.application.remarks)

        # App_no + Soum + Landuse
        app_no = self.application.app_no
        parts_app_no = app_no.split("-")

        self.application_num_first_edit.setText(parts_app_no[0])
        self.application_num_type_edit.setText(parts_app_no[1])
        self.application_num_middle_edit.setText(parts_app_no[2])
        self.application_num_last_edit.setText(parts_app_no[3])

        # Parcels
        self.__parcels_mapping()
        # Boundary
        self.__boundary_mapping()

    def __parcels_mapping(self):

        app_pug_parcels = self.session.query(CtApplicationPUGParcel).\
            filter(CtApplicationPUGParcel.application == self.application.app_no).all()
        for pug_parcel in app_pug_parcels:
            parcel = self.session.query(CaPastureParcel).filter(CaPastureParcel.parcel_id == pug_parcel.parcel).one()

            item = QTableWidgetItem(parcel.parcel_id)
            item.setIcon(QIcon(QPixmap(":/plugins/lm2/parcel.png")))
            item.setData(Qt.UserRole, parcel.parcel_id)

            count = self.assigned_parcel_twidget.rowCount()
            self.assigned_parcel_twidget.insertRow(count)

            self.assigned_parcel_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(parcel.address_neighbourhood)
            item.setData(Qt.UserRole, parcel.address_neighbourhood)
            self.assigned_parcel_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(str(parcel.area_ga))
            item.setData(Qt.UserRole, parcel.area_ga)
            self.assigned_parcel_twidget.setItem(count, 2, item)


    def __boundary_mapping(self):

        app_boundarys = self.session.query(CtAppGroupBoundary).\
            filter(CtAppGroupBoundary.application == self.application.app_no).all()
        for app_boundary in app_boundarys:
            boundary = self.session.query(CaPUGBoundary).filter(CaPUGBoundary.code == app_boundary.boundary_code).one()

            item = QTableWidgetItem(boundary.code)
            item.setIcon(QIcon(QPixmap(":/plugins/lm2/parcel.png")))
            item.setData(Qt.UserRole, boundary.code)

            count = self.assigned_boundary_twidget.rowCount()
            self.assigned_boundary_twidget.insertRow(count)

            self.assigned_boundary_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(boundary.group_name)
            item.setData(Qt.UserRole, boundary.group_name)
            self.assigned_boundary_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(str(boundary.area_ga))
            item.setData(Qt.UserRole, boundary.area_ga)
            self.assigned_boundary_twidget.setItem(count, 2, item)

    def __setup_permissions(self):

        user_name = QSettings().value(SettingsConstants.USER)
        user_rights = DatabaseUtils.userright_by_name(user_name)

        if UserRight.application_update in user_rights:
            self.apply_button.setEnabled(True)
            self.applicant_twidget.setAcceptDrops(True)
            self.documents_twidget.setEnabled(True)
            self.apply_button.setEnabled(True)
            self.appliciants_remove_button.setEnabled(True)
        else:
            self.applicant_twidget.setAcceptDrops(False)
            self.documents_twidget.setEnabled(False)
            self.apply_button.setEnabled(False)
            self.appliciants_remove_button.setEnabled(False)

    def __setup_parcels_twidget(self):

        self.result_parcel_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.result_parcel_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_parcel_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_parcel_twidget.setSortingEnabled(True)
        header = self.result_parcel_twidget.horizontalHeader()
        header.setResizeMode(QHeaderView.Stretch)

        # PUG Boundary twidget
        self.result_boundary_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.result_boundary_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_boundary_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_boundary_twidget.setSortingEnabled(True)
        header = self.result_boundary_twidget.horizontalHeader()
        header.setResizeMode(QHeaderView.Stretch)

        self.assigned_boundary_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.assigned_boundary_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assigned_boundary_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assigned_boundary_twidget.setSortingEnabled(True)
        header = self.assigned_boundary_twidget.horizontalHeader()
        header.setResizeMode(QHeaderView.Stretch)

        self.assigned_parcel_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.assigned_parcel_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assigned_parcel_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assigned_parcel_twidget.setSortingEnabled(True)
        header = self.assigned_parcel_twidget.horizontalHeader()
        header.setResizeMode(QHeaderView.Stretch)

    def __setup_applicant_twidget(self):

        self.applicant_twidget = DragTreeWidget("person", 20, 200, 720, 150, self.applicants_group_box)

        header = [self.tr("Main Applicant"),
                  self.tr("Personal/Company ID"),
                  self.tr("Surname/Company"),
                  self.tr("First Name")]

        self.applicant_twidget.setup_header(header)
        self.applicant_twidget.itemClicked.connect(self.on_application_twidget_cellChanged)

        try:
            applicants = self.application.stakeholders.filter(
                CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE).all()

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        for applicant in applicants:
            self.__add_applicant_item(applicant)

    def __setup_person_twidget(self):

        self.person_twidget.setColumnCount(1)
        self.person_twidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.person_twidget.horizontalHeader().setVisible(False)
        self.person_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.person_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.person_twidget.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.person_twidget.customContextMenuRequested.connect(self.on_custom_context_menu_requested)
        self.person_twidget.setDragEnabled(True)

    def __setup_status_widget(self):

        self.application_status_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.application_status_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.application_status_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.application_status_twidget.setSortingEnabled(True)

        for status in self.application.statuses:
            self.__add_application_status_item(status)

        self.application_status_twidget.sortItems(0, Qt.AscendingOrder)

    def __setup_documents_twidget(self):

        self.documents_twidget = DocumentsTableWidget(self.documents_group_box)
        delegate = PastureApplicationDocumentDelegate(self.documents_twidget, self)
        self.documents_twidget.setItemDelegate(delegate)

    def __setup_combo_boxes(self):

        self.bag_parcel_cbox.clear()
        self.bag_boundary_cbox.clear()
        l2_code = DatabaseUtils.working_l2_code()

        if l2_code == -1 or not l2_code:
            return

        database_name = QSettings().value(SettingsConstants.DATABASE_NAME)
        user_code = database_name.split('_')[1]
        user_start = 'user' + user_code

        try:
            application_types = self.session.query(ClApplicationType).\
                filter(or_(ClApplicationType.code == ApplicationType.pasture_use, ClApplicationType.code == ApplicationType.legitimate_rights)).\
                order_by(ClApplicationType.code).all()
            statuses = self.session.query(ClApplicationStatus).order_by(ClApplicationStatus.code).all()
            set_roles = self.session.query(SetRole). \
                filter(SetRole.user_name.startswith(user_start)).all()
            landuse_types = self.session.query(ClLanduseType).all()
            ct_member_group = self.session.query(CtPersonGroup).all()

            PluginUtils.populate_au_level3_cbox(self.bag_parcel_cbox, l2_code)
            PluginUtils.populate_au_level3_cbox(self.bag_boundary_cbox, l2_code)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        for item in application_types:
            self.application_type_cbox.addItem(item.description, item.code)

        for status in statuses:
            self.status_cbox.addItem(status.description, status.code)

        for setRole in set_roles:
            self.next_officer_in_charge_cbox.addItem(setRole.surname + ", " + setRole.first_name, setRole.user_name_real)

        for item in landuse_types:
            self.approved_land_use_type_cbox.addItem(str(item.code) + ": " + item.description, item.code)
        if ct_member_group is not None:
            for member in ct_member_group:
                self.pasture_group_cbox.addItem(member.group_name, member.group_no)

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

        if not self.__check_main_capable_applicant() and self.application.app_type == 3:
            self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            applicants_error = self.tr("In uncapable person should be main.")
            error_message = error_message + "\n \n" + applicants_error
            valid = False

        if not self.__check_main_applicant():
            self.applicant_twidget.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            applicants_error = self.tr("Exactly one main applicant has to be defined.")
            error_message = error_message + "\n \n" + applicants_error
            valid = False

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

        return valid, error_message

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
        host = QSettings().value(SettingsConstants.HOST, "")
        app_no = self.application.app_no
        archive_app_path = PasturePath.app_file_path()
        if host == "localhost":
            archive_app_path = archive_app_path + '/' + app_no
            if not os.path.exists(archive_app_path):
                os.makedirs(archive_app_path)
        else:
            archive_app_path = archive_app_path + '\\' + app_no
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
            required_doc_types = self.session.query(SetPastureDocument). \
                filter(SetPastureDocument.app_type == current_app_type).filter(SetPastureDocument.parent_type == 1).all()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        for doc in required_doc_types:

            docType = self.session.query(ClPastureDocument).filter(ClPastureDocument.code == doc.document).one()
            item_provided = QTableWidgetItem()
            item_provided.setCheckState(Qt.Unchecked)

            item_doc_type = QTableWidgetItem(docType.description)
            item_doc_type.setData(Qt.UserRole, docType.code)
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

            try:
                if application_type_code == 1:
                    giving_onwer_count = self.session.query(CtApplicationPersonRole.application)\
                        .join(CtApplicationStatus, CtApplicationPersonRole.application == CtApplicationStatus.application)\
                        .join(CtApplication, CtApplicationPersonRole.application == CtApplication.app_no)\
                        .filter(CtApplicationPersonRole.person == person.person_id)\
                        .filter(CtApplicationPersonRole.role == 30).group_by(CtApplicationPersonRole.application).count()

                    remaining_onwer_count = self.session.query(CtApplicationPersonRole.application) \
                        .join(CtApplicationStatus,
                              CtApplicationPersonRole.application == CtApplicationStatus.application) \
                        .join(CtApplication, CtApplicationPersonRole.application == CtApplication.app_no) \
                        .filter(CtApplicationPersonRole.person == person.person_id) \
                        .filter(CtApplicationPersonRole.role == 40).group_by(
                        CtApplicationPersonRole.application).count()

                    first_owner_count = self.session.query(CtApplicationPersonRole.application) \
                        .join(CtApplicationStatus,
                              CtApplicationPersonRole.application == CtApplicationStatus.application) \
                        .join(CtApplication, CtApplicationPersonRole.application == CtApplication.app_no) \
                        .filter(CtApplicationPersonRole.person == person.person_id) \
                        .filter(CtApplication.app_type == 1).group_by(
                                            CtApplicationPersonRole.application).count()
                    if first_owner_count > 1:
                            PluginUtils.show_error(self, self.tr("Invalid Applicant"),
                                                   self.tr("Before acquiring land Twice do not own"))
                            return

                    if giving_onwer_count == 1:
                        if first_owner_count > 1:
                            PluginUtils.show_error(self, self.tr("Invalid Applicant"),
                                                   self.tr("Before acquiring land Twice do not own"))
                            return
                    elif remaining_onwer_count >= 1:
                        PluginUtils.show_error(self, self.tr("Invalid Applicant"),
                                            self.tr("Before acquiring land Twice do not own"))
                        return

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

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
            if (application_type_code == 5 or application_type_code == 7 or application_type_code == 15):
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
            num_rows = self.application_status_twidget.rowCount()
            if num_rows > 1:
                PluginUtils.show_error(self, self.tr("add applicant error"), self.tr("it will acceptable only applicatin status one."))
                return
            self.__copy_applicant_from_navigator()

        if self.application.stakeholders.count() > 0:
            self.application_type_cbox.setEnabled(False)

    @pyqtSlot(int, int)
    def on_application_twidget_cellChanged(self, item, column):

        root = self.applicant_twidget.invisibleRootItem()
        child_count = root.childCount()
        item_id = 0
        for i in range(child_count):
            item_o = root.child(i)
            item_id = item.data(0, Qt.UserRole+1)
            if item_id == 0:
                item_o.setCheckState(0,Qt.Unchecked)
        if item_id == 0:
            item.setCheckState(0, Qt.Checked)

    @pyqtSlot()
    def on_drop_label_itemDropped(self):

        self.__copy_parcel_from_navigator()

    @pyqtSlot()
    def on_contract_drop_label_itemDropped(self):

        self.__copy_contract_from_navigator()

    @pyqtSlot()
    def on_appliciants_remove_button_clicked(self):

        person_id = ''
        root = self.applicant_twidget.invisibleRootItem()
        for item in self.applicant_twidget.selectedItems():
            (item.parent() or root).removeChild(item)
            person_id = item.data(0, Qt.UserRole)
            group_no = item.data(0, Qt.UserRole+2)
        try:
            applicant_roles = self.application.stakeholders.filter(CtApplicationPersonRole.person == person_id) \
                .filter(CtApplicationPersonRole.role == ConstantsPasture.APPLICANT_ROLE_CODE).one()

            self.application.stakeholders.remove(applicant_roles)

            if group_no:
                self.session.query(CtApplicationPUG).filter(CtApplicationPUG.application == self.application.app_no).\
                    filter(CtApplicationPUG.group_no == group_no).delete()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        if self.application.stakeholders.count() > 0:
            self.application_type_cbox.setEnabled(False)
        elif not self.attribute_update:
            self.application_type_cbox.setEnabled(True)

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

    @pyqtSlot()
    def on_delete_button_clicked(self):

        selected_row = self.application_status_twidget.currentRow()
        status_item = self.application_status_twidget.item(selected_row, 0)

        self.create_savepoint()

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

        if status_id == 5:
            if self.assigned_parcel_twidget.rowCount() == 0:
                PluginUtils.show_message(self, self.tr("Application Status"),
                                         self.tr("First connect to parcels for this application!!"))
                return

        if status_id == 6:
            PluginUtils.show_message(self, self.tr("Application Status"), self.tr("First prepare draft decision for this application!!"))
            return
        if status_id == 7:
            PluginUtils.show_message(self, self.tr("Application Status"), self.tr("First register governor decision!!"))
            return
        for appStatus in self.application.statuses:
            if appStatus.status_ref.code == 8:
                PluginUtils.show_message(self, self.tr("Status error"),
                                         self.tr("This application refused by governor."))
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

    @pyqtSlot()
    def on_apply_button_clicked(self):

        app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())
        self.application.app_type = app_type

        # save application details
        # validity_result = self.__validity_of_application()
        #
        # if not validity_result[0]:
        #     log_message = validity_result[1]
        #
        #     PluginUtils.show_error(self, self.tr("Invalid application"), log_message)
        #     return

        self.__save_application()

        self.__start_fade_out_timer()

        self.attribute_update = True

    def __save_application(self):

        try:
            self.create_savepoint()

            self.__save_application_details()

            self.__save_applicants()
            self.__save_parcels()

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

            status = self.session.query(func.max(CtApplicationStatus.status)).\
                filter(CtApplicationStatus.application == self.application.app_no).one()
            max_status = str(status).split(",")[0][1:]


        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __save_parcels(self):

        try:
            for row in range(self.pasture_type_twidget.rowCount()):
                pasture_code = self.pasture_type_twidget.item(row, 0).data(Qt.UserRole)
                parcel_id = self.pasture_type_twidget.item(row, 0).data(Qt.UserRole+1)
                begin_month = self.pasture_type_twidget.item(row, 1).text()
                end_month = self.pasture_type_twidget.item(row, 2).text()
                days = self.pasture_type_twidget.item(row, 3).text()

                pug_parcel_pasture = self.session.query(CtApplicationParcelPasture). \
                    filter(CtApplicationParcelPasture.application == self.application.app_no). \
                    filter(CtApplicationParcelPasture.parcel == parcel_id). \
                    filter(CtApplicationParcelPasture.pasture == pasture_code).one()

                pug_parcel_pasture.begin_month = int(begin_month)
                pug_parcel_pasture.end_month = int(end_month)
                pug_parcel_pasture.days = int(days)


            for row in range(self.assigned_parcel_twidget.rowCount()):
                parcel_id = self.assigned_parcel_twidget.item(row, 0).data(Qt.UserRole)

                pasture_type_list = ''
                parcel_pastures = self.session.query(CtApplicationParcelPasture).\
                    filter(CtApplicationParcelPasture.application == self.application.app_no).\
                    filter(CtApplicationParcelPasture.parcel == parcel_id).all()
                for pastures in parcel_pastures:
                    pasture = self.session.query(ClPastureType).filter(ClPastureType.code == pastures.pasture).one()
                    pasture_text = pasture.description
                    if pasture_type_list == '':
                        pasture_type_list = pasture_text
                    else:
                        if pasture_type_list != pasture_text:
                            pasture_type_list = pasture_type_list+'-'+pasture_text

                parcel_pasture = self.session.query(CaPastureParcel).filter(CaPastureParcel.parcel_id == parcel_id).one()

                parcel_pasture.pasture_type = pasture_type_list

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("File Error"),
                               self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __save_applicants(self):

        self.create_savepoint()

        root = self.applicant_twidget.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):
            item = root.child(i)
            person_id = item.data(0, Qt.UserRole)
            share = 0
            main = True
            if item.checkState(0) == Qt.Checked:
                main = True
                share = 1
            else:
                main = False
                share = 0
            try:
                applicant = self.application.stakeholders.filter(
                    CtApplicationPersonRole.role == ConstantsPasture.APPLICANT_ROLE_CODE) \
                    .filter(CtApplicationPersonRole.person == person_id).one()

                applicant.main_applicant = main
                applicant.share = share

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
    def on_contract_cancelled_accept_button_clicked(self):

        to_be_accepted_num = self.contract_cancelled_num_edit.text()
        self.contract_to_be_cancelled_edit.setText(to_be_accepted_num)
        self.contract_ca

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

        self.__add_aimag_name(map_composition)
        self.__add_soum_name(map_composition)
        self.__add_app_no(map_composition)
        self.__add_app_date(map_composition)
        self.__add_person_name(map_composition)
        self.__add_officer(map_composition)
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

        officer_full = '                          ' + position + u' албан тушаалтан '+ officer.surname + u' овогтой ' + officer.first_name + ' ___________________ '+ u' хүлээн авав.'
        item = map_composition.getComposerItemById("officer_full")
        item.setText(self.__wrap(officer_full, 200))
        # item.adjustSizeToText()

    def __valid_status(self, status_code):

        count = self.application.statuses.filter(CtApplicationStatus.status == status_code).count()
        if count > 0:
            return False

        return True

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

        member_group_count = self.session.query(CtGroupMember).filter(
            CtGroupMember.person == applicant.person_ref.person_id).count()

        if member_group_count > 0:
            member_group = self.session.query(CtGroupMember).filter(
                CtGroupMember.person == applicant.person_ref.person_id).all()
            group_no = None
            for mem in member_group:
                app_pug_count = self.session.query(CtApplicationPUG).filter(CtApplicationPUG.application == self.application.app_no).\
                    filter(CtApplicationPUG.group_no == mem.group_no).count()
                if app_pug_count == 1:
                    app_pug = self.session.query(CtApplicationPUG).filter(
                        CtApplicationPUG.application == self.application.app_no). \
                        filter(CtApplicationPUG.group_no == mem.group_no).one()
                    group_no = app_pug.group_no
            if group_no:
                group = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == group_no).one()
                leader_info = ['', applicant.person_ref.person_id, applicant.person_ref.name, applicant.person_ref.first_name]

                leader_item = QTreeWidgetItem(leader_info)
                leader_item.setText(0, group.group_name)
                leader_item.setCheckState(0, Qt.Checked) if applicant.main_applicant \
                    else leader_item.setCheckState(0, Qt.Unchecked)

                leader_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2_pasture/group.png")))
                leader_item.setData(0, Qt.UserRole, applicant.person_ref.person_id)
                leader_item.setData(0, Qt.UserRole + 1, 0)
                leader_item.setData(0, Qt.UserRole + 2, group_no)

                self.applicant_twidget.addTopLevelItem(leader_item)
                for member in group.members:
                    if member.role == 20:
                        member_id = member.person_ref.person_id
                        member_name = member.person_ref.name
                        member_firstname = member.person_ref.first_name
                        member_info = ['', member_id, member_name, member_firstname]
                        member_item = QTreeWidgetItem(member_info)
                        member_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2/person.png")))
                        member_item.setData(0, Qt.UserRole, member_id)
                        member_item.setData(0, Qt.UserRole + 1, 1)
                        leader_item.addChild(member_item)

        app_pug_count = self.session.query(CtApplicationPUG).filter(CtApplicationPUG.application == self.application.app_no).count()
        if app_pug_count == 0:
            # person = self.session.query(BsPerson).filter(BsPerson.person_id == applicant.person_ref.person_id).one()
            person_info = ['', applicant.person_ref.person_id, applicant.person_ref.name, applicant.person_ref.first_name]

            person_item = QTreeWidgetItem(person_info)
            person_item.setText(0, u'Бүлэгт хамаарахгүй')
            person_item.setCheckState(0, Qt.Checked) if applicant.main_applicant \
                else person_item.setCheckState(0, Qt.Unchecked)
            person_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2/person.png")))
            person_item.setData(0, Qt.UserRole, applicant.person_ref.person_id)
            person_item.setData(0, Qt.UserRole + 1, 0)
            person_item.setData(0, Qt.UserRole + 2, None)

            self.applicant_twidget.addTopLevelItem(person_item)
        else:
            app_pug = self.session.query(CtApplicationPUG).filter(
                CtApplicationPUG.application == self.application.app_no).all()
            is_reg = True
            for pug in app_pug:
                member_group_count = self.session.query(CtGroupMember).filter(
                    CtGroupMember.person == applicant.person_ref.person_id).\
                    filter(CtGroupMember.group_no == pug.group_no).count()
                if member_group_count == 1:
                    is_reg = False
            if is_reg:
                person_info = ['', applicant.person_ref.person_id, applicant.person_ref.name,
                               applicant.person_ref.first_name]

                person_item = QTreeWidgetItem(person_info)
                person_item.setText(0, u'Бүлэгт хамаарахгүй')
                person_item.setCheckState(0, Qt.Checked) if applicant.main_applicant \
                    else person_item.setCheckState(0, Qt.Unchecked)
                person_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2/person.png")))
                person_item.setData(0, Qt.UserRole, applicant.person_ref.person_id)
                person_item.setData(0, Qt.UserRole + 1, 0)
                person_item.setData(0, Qt.UserRole + 2, None)

                self.applicant_twidget.addTopLevelItem(person_item)

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

        self.pasture_type_cbox.clear()
        application_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())

        if application_type == ApplicationType.pasture_use:
            pastures = self.session.query(ClPastureType).\
                filter(or_(ClPastureType.code == 17,ClPastureType.code == 18,ClPastureType.code == 19,ClPastureType.code == 20)).all()
            self.person_gbox.setVisible(False)
        else:
            pastures = self.session.query(ClPastureType). \
                filter(and_(ClPastureType.code != 17, ClPastureType.code != 18, ClPastureType.code != 19, ClPastureType.code != 20)).all()
            self.person_gbox.setVisible(True)
        if pastures:
            for pasture in pastures:
                self.pasture_type_cbox.addItem(pasture.description, pasture.code)


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

    def __set_visible_tabs(self):

        app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex())

        self.requested_year_spin_box.setVisible(False)
        self.approved_year_spin_box.setVisible(False)
        self.duration_approved_label.setVisible(False)
        self.duration_request_label.setVisible(False)

        self.__landuse_per_application_type(app_type)

        #type: 26 or 27

        # if app_type == ApplicationType.pasture_use:
        #     self.application_tab_widget.removeTab(self.application_tab_widget.indexOf(self.document_tab))
        # elif app_type == ApplicationType.legitimate_rights:
        #     self.application_tab_widget.insertTab(self.application_tab_widget.count() - 2, self.document_tab,
        #                                       self.tr("Application Documents"))

        self.requested_year_spin_box.setVisible(True)
        self.approved_year_spin_box.setVisible(True)
        self.duration_approved_label.setVisible(True)
        self.duration_request_label.setVisible(True)

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
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_details.htm")
            elif self.application_tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_applicants.htm")
            elif self.application_tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_documents.htm")
            elif self.application_tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_parcel.htm")
            elif self.application_tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_record_created.htm")
            elif self.application_tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/application_print.htm")

    @pyqtSlot(int)
    def on_is_group_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.pasture_group_cbox.setEnabled(True)
            self.group_connect_button.setEnabled(True)
        else:
            self.pasture_group_cbox.setEnabled(False)
            self.group_connect_button.setEnabled(False)

    @pyqtSlot(int)
    def on_is_person_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.person_id_edit.setEnabled(True)
            self.firstname_edit.setEnabled(True)
            self.person_twidget.setEnabled(True)
            self.person_find_button.setEnabled(True)
            self.person_connect_button.setEnabled(True)
        else:
            self.__remove_person_items()
            self.person_id_edit.setEnabled(False)
            self.firstname_edit.setEnabled(False)
            self.person_twidget.setEnabled(False)
            self.person_find_button.setEnabled(False)
            self.person_connect_button.setEnabled(False)

    @pyqtSlot(int)
    def on_pasture_group_cbox_currentIndexChanged(self, index):

        self.leader_id_edit.clear()
        self.leader_name_edit.clear()
        group_no = self.pasture_group_cbox.itemData(index)

        group = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == group_no).one()

        for member in group.members:
            if member.role == 10:
                self.leader_id_edit.setText(member.person_ref.person_id)
                self.leader_name_edit.setText(member.person_ref.name +' '+ member.person_ref.first_name)

    @pyqtSlot()
    def on_group_connect_button_clicked(self):

        group_no = self.pasture_group_cbox.itemData(self.pasture_group_cbox.currentIndex())

        group = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == group_no).one()
        leader_id = ''
        leader_name = ''
        leader_firstname = ''

        if group.members.count() == 0:
            PluginUtils.show_message(self, self.tr("Group None"), self.tr("This group not member"))
            return
        for member in group.members:
            if member.role == 10:
                leader_id = member.person_ref.person_id
                leader_name = member.person_ref.name
                leader_firstname = member.person_ref.first_name

        root = self.applicant_twidget.invisibleRootItem()
        child_count = root.childCount()

        if self.application.app_type == ApplicationType.pasture_use:
            if child_count >= 1:
                PluginUtils.show_message(self, self.tr("Group Duplicate"), self.tr("This application only one PUG"))
                return

        for i in range(child_count):
            item = root.child(i)
            item_id = item.data(0, Qt.UserRole)  # text at first (0) column
            if item_id == leader_id:
                PluginUtils.show_message(self, self.tr("Group Duplicate"), self.tr("This group already registered"))
                return

        leader_info = ['', leader_id, leader_name, leader_firstname]
        leader = self.session.query(BsPerson).filter(BsPerson.person_id == leader_id).one()
        leader_item = QTreeWidgetItem(leader_info)
        leader_item.setText(0, group.group_name)
        leader_item.setCheckState(0, Qt.Unchecked)
        leader_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2_pasture/group.png")))
        leader_item.setData(0, Qt.UserRole, leader_id)
        leader_item.setData(0, Qt.UserRole+1, 0)
        leader_item.setData(0, Qt.UserRole + 2, group_no)

        self.applicant_twidget.addTopLevelItem(leader_item)

        role_ref = self.session.query(ClPersonRole).filter_by(
            code=ConstantsPasture.APPLICANT_ROLE_CODE).one()

        app_person_role = CtApplicationPersonRole()
        app_person_role.application = self.application.app_no
        app_person_role.share = Decimal(0.0)
        app_person_role.role_ref = role_ref
        app_person_role.role = ConstantsPasture.APPLICANT_ROLE_CODE
        app_person_role.person = leader_id
        app_person_role.person_ref = leader
        app_person_role.main_applicant = False

        self.application.stakeholders.append(app_person_role)

        app_pug_count = self.session.query(CtApplicationPUG).filter(CtApplicationPUG.application == self.application.app_no).\
            filter(CtApplicationPUG.group_no == group_no).count()
        if app_pug_count == 0:
            app_pug = CtApplicationPUG()
            app_pug.application = self.application.app_no
            app_pug.group_no = group_no
            self.session.add(app_pug)

        for member in group.members:
            if member.role == 20:
                member_id = member.person_ref.person_id
                member_name = member.person_ref.name
                member_firstname = member.person_ref.first_name
                member_info = ['', member_id, member_name, member_firstname]
                member_item = QTreeWidgetItem(member_info)
                member_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2/person.png")))
                member_item.setData(0, Qt.UserRole, member_id)
                member_item.setData(0, Qt.UserRole+1, 1)
                leader_item.addChild(member_item)

    def __remove_person_items(self):

        self.person_twidget.setRowCount(0)

    @pyqtSlot()
    def on_person_find_button_clicked(self):

        self.__search_persons()

    def __search_persons(self):

        try:
            persons = self.session.query(PersonSearch)
            filter_is_set = False
            if self.firstname_edit.text():
                filter_is_set = True
                right_holder = "%" + self.firstname_edit.text() + "%"
                persons = persons.filter(or_(func.lower(PersonSearch.name).like(func.lower(right_holder)),
                                             func.lower(PersonSearch.first_name).ilike(func.lower(right_holder)),
                                             func.lower(PersonSearch.middle_name).ilike(func.lower(right_holder))))

            if self.person_id_edit.text():
                filter_is_set = True
                value = "%" + self.person_id_edit.text() + "%"
                persons = persons.filter(PersonSearch.person_id.ilike(value))

            count = 0

            self.__remove_person_items()

            if persons.distinct(PersonSearch.person_id).count() == 0:
                self.error_label.setText(self.tr("No persons found for this search filter."))
                return
            elif filter_is_set is False:
                self.error_label.setText(self.tr("Please specify a search filter."))
                return

            for person in persons.distinct(PersonSearch.name, PersonSearch.person_id).order_by(PersonSearch.name.asc(),
                                                                                               PersonSearch.person_id.asc()).all():

                if not person.person_id:
                    person_id = self.tr(" (Id: n.a. )")
                else:
                    person_id = self.tr(" (Id: ") + person.person_id + ")"

                first_name = self.tr(" n.a. ") if not person.first_name else person.first_name

                item = QTableWidgetItem(person.name + ", " + first_name + person_id)
                item.setIcon(QIcon(QPixmap(":/plugins/lm2/person.png")))
                item.setData(Qt.UserRole, person.person_id)
                self.person_twidget.insertRow(count)
                self.person_twidget.setItem(count, 0, item)
                count += 1

            self.error_label.setText("")

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    @pyqtSlot()
    def on_person_connect_button_clicked(self):

        selected_items = self.person_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please select person."))
            return

        items = self.person_twidget.selectedItems()
        count = 0
        for item in items:
            person_id = item.data(Qt.UserRole)

            iterator = QTreeWidgetItemIterator(self.applicant_twidget)
            while iterator.value():
                item = iterator.value()
                item_id = item.data(0, Qt.UserRole)
                if item_id == person_id:  # check value here
                    PluginUtils.show_message(self, self.tr("Person Duplicate"), self.tr("This person already registered"))
                    return
                iterator += 1

            root = self.applicant_twidget.invisibleRootItem()
            child_count = root.childCount()
            for i in range(child_count):
                item = root.child(i)
                item_id = item.data(0, Qt.UserRole)  # text at first (0) column
                if item_id == person_id:
                    PluginUtils.show_message(self, self.tr("Person Duplicate"), self.tr("This person already registered"))
                    return

            person = self.session.query(BsPerson).filter(BsPerson.person_id == person_id).one()

            person_info = ['', person_id, person.name, person.first_name]

            person_item = QTreeWidgetItem(person_info)
            person_item.setText(0, u'Бүлэгт хамаарахгүй')
            person_item.setCheckState(0, Qt.Unchecked)
            person_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2/person.png")))
            person_item.setData(0, Qt.UserRole, person_id)
            person_item.setData(0, Qt.UserRole + 1, 0)
            person_item.setData(0, Qt.UserRole + 2, None)

            self.applicant_twidget.addTopLevelItem(person_item)

            count += 1

            # add applicant
            role_ref = self.session.query(ClPersonRole).filter_by(
                code=ConstantsPasture.APPLICANT_ROLE_CODE).one()

            app_person_role = CtApplicationPersonRole()
            app_person_role.application = self.application.app_no
            app_person_role.share = Decimal(0.0)
            app_person_role.role_ref = role_ref
            app_person_role.role = ConstantsPasture.APPLICANT_ROLE_CODE
            app_person_role.person = person.person_id
            app_person_role.person_ref = person
            app_person_role.main_applicant = False

            self.application.stakeholders.append(app_person_role)

    @pyqtSlot()
    def on_find_boundary_number_button_clicked(self):

        self.__search_pug_boundary()

    def __search_pug_boundary(self):

        pug_boundarys = self.session.query(CaPUGBoundary.code, CaPUGBoundary.area_ga, \
                                     CaPUGBoundary.group_name, CaPUGBoundary.geometry)

        if not self.bag_boundary_cbox.itemData(self.bag_boundary_cbox.currentIndex()) == -1:
            value = self.bag_boundary_cbox.itemData(self.bag_boundary_cbox.currentIndex())
            bag = self.session.query(AuLevel3).filter(AuLevel3.code == value).one()
            pug_boundarys = pug_boundarys.filter(CaPUGBoundary.geometry.ST_Intersects(bag.geometry))
        else:
            pug_boundarys = pug_boundarys

        if self.search_boundary_num_edit.text():
            boundary_code = "%" + self.search_boundary_num_edit.text() + "%"
            pug_boundarys = pug_boundarys.filter(CaPUGBoundary.code.ilike(boundary_code))
        else:
            pug_boundarys = pug_boundarys

        self.result_boundary_twidget.setRowCount(0)

        if pug_boundarys.distinct(CaPUGBoundary.code).count() == 0:
            self.error_label.setText(self.tr("No parcels found for this search filter."))
            return

        count = 0
        for group in pug_boundarys.distinct(CaPUGBoundary.code,CaPUGBoundary.area_ga,CaPUGBoundary.group_name).all():

            item = QTableWidgetItem(str(group.code))
            item.setIcon(QIcon(QPixmap(":/plugins/lm2/parcel.png")))
            item.setData(Qt.UserRole, group.code)
            self.result_boundary_twidget.insertRow(count)

            self.result_boundary_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(group.group_name)
            item.setData(Qt.UserRole, group.group_name)
            self.result_boundary_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(str(group.area_ga))
            item.setData(Qt.UserRole, group.area_ga)
            self.result_boundary_twidget.setItem(count, 2, item)

            count += 1

        self.error_label.setText("")

    @pyqtSlot()
    def on_find_parcel_number_button_clicked(self):

        self.__search_parcels()

    def __search_parcels(self):


        parcels = self.session.query(CaPastureParcel.parcel_id, CaPastureParcel.landuse, \
                                     CaPastureParcel.pasture_type, CaPastureParcel.area_ga, CaPastureParcel.geometry)

        # if self.assigned_boundary_twidget.rowCount() == 1:
        #     boundary_id = self.assigned_boundary_twidget.item(0, 0).data(Qt.UserRole)
        #     print boundary_id
        #     boundary = self.session.query(CaPUGBoundary).filter(CaPUGBoundary.code == boundary_id).one()
        #     parcels = parcels.filter(CaPastureParcel.geometry.ST_Within(boundary.geometry))

        if not self.bag_parcel_cbox.itemData(self.bag_parcel_cbox.currentIndex()) == -1:
            value = self.bag_parcel_cbox.itemData(self.bag_parcel_cbox.currentIndex())
            bag = self.session.query(AuLevel3).filter(AuLevel3.code == value).one()
            parcels = parcels.filter(CaPastureParcel.geometry.ST_Covers(bag.geometry))
        else:
            parcels = parcels

        if self.search_parcel_num_edit.text():
            parcel_no = "%" + self.search_parcel_num_edit.text() + "%"
            parcels = parcels.filter(CaPastureParcel.parcel_id.ilike(parcel_no))
        else:
            parcels = parcels

        self.result_parcel_twidget.setRowCount(0)

        if parcels.distinct(CaPastureParcel.parcel_id).count() == 0:
            self.error_label.setText(self.tr("No parcels found for this search filter."))
            return

        count = 0
        for parcel in parcels.distinct(CaPastureParcel.parcel_id,CaPastureParcel.landuse,CaPastureParcel.area_ga).all():
            land_use = ''
            landuse_code = None
            landuse_count = self.session.query(ClLanduseType).filter(ClLanduseType.code == parcel.landuse).count()
            if landuse_count == 1:
                landuse = self.session.query(ClLanduseType).filter(ClLanduseType.code == parcel.landuse).one()
                landuse_code  = parcel.landuse
                land_use = str(parcel.landuse)+':'+landuse.description
            item = QTableWidgetItem(parcel.parcel_id)
            item.setIcon(QIcon(QPixmap(":/plugins/lm2/parcel.png")))
            item.setData(Qt.UserRole, parcel.parcel_id)
            self.result_parcel_twidget.insertRow(count)

            self.result_parcel_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(land_use)
            item.setData(Qt.UserRole, landuse_code)
            self.result_parcel_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(str(parcel.area_ga))
            item.setData(Qt.UserRole, parcel.area_ga)
            self.result_parcel_twidget.setItem(count, 2, item)

            count += 1

        self.error_label.setText("")

    @pyqtSlot()
    def on_boundary_add_button_clicked(self):

        row = self.result_boundary_twidget.currentRow()
        if row == -1:
            return
        boundary_code = self.result_boundary_twidget.item(row, 0).data(Qt.UserRole)

        is_register = False
        for row in range(self.assigned_boundary_twidget.rowCount()):
            id = self.assigned_boundary_twidget.item(row, 0).data(Qt.UserRole)
            if id == boundary_code:
                is_register = True

        if is_register:
            PluginUtils.show_message(self, self.tr("Boundary Duplicate"), self.tr("This boundary already connected"))
            return

        if self.assigned_boundary_twidget.rowCount() > 0:
            PluginUtils.show_message(self, self.tr("Boundary Register"), self.tr("This application already connected PUG boundary"))
            return

        boundary = self.session.query(CaPUGBoundary).filter(CaPUGBoundary.code == boundary_code).one()
        # pasture_type = self.session.query(ClPastureType).filter(ClPastureType.code == 1).one()
        item = QTableWidgetItem(str(boundary.code))
        item.setIcon(QIcon(QPixmap(":/plugins/lm2/parcel.png")))
        item.setData(Qt.UserRole, boundary.code)

        count = self.assigned_boundary_twidget.rowCount()
        self.assigned_boundary_twidget.insertRow(count)

        self.assigned_boundary_twidget.setItem(count, 0, item)

        item = QTableWidgetItem(boundary.group_name)
        item.setData(Qt.UserRole, boundary.group_name)
        self.assigned_boundary_twidget.setItem(count, 1, item)

        item = QTableWidgetItem(str(boundary.area_ga))
        item.setData(Qt.UserRole, boundary.area_ga)
        self.assigned_boundary_twidget.setItem(count, 2, item)

        #group name save
        app_person = self.session.query(CtApplicationPersonRole).filter(
            CtApplicationPersonRole.application == self.application.app_no).all()

        for p in app_person:
            if p.main_applicant == True:
                person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()

        app_pug = self.session.query(CtApplicationPUG).filter(
            CtApplicationPUG.application == self.application.app_no).all()
        group_name = u'Бүлэгт хамаарахгүй'
        group_no = None
        for app_group in app_pug:
            group_member_count = self.session.query(CtGroupMember).filter(
                CtGroupMember.group_no == app_group.group_no). \
                filter(CtGroupMember.person == person.person_id).count()
            if group_member_count == 1:
                group = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == app_group.group_no).one()
                group_name = group.group_name
                group_no = group.group_no

        boundary_count = self.session.query(CaPUGBoundary).\
            filter(CaPUGBoundary.code == boundary_code).count()
        if boundary_count == 1:
            boundary = self.session.query(CaPUGBoundary). \
                filter(CaPUGBoundary.code == boundary_code).one()
            boundary.group_name = group_name

        app_boundary_count = self.session.query(CtAppGroupBoundary).filter(
            CtAppGroupBoundary.application == self.application.app_no). \
            filter(CtAppGroupBoundary.group_no == group_no).\
            filter(CtAppGroupBoundary.boundary_code == boundary_code).count()
        if app_boundary_count == 0:
            app_boundary = CtAppGroupBoundary()
            app_boundary.application = self.application.app_no
            app_boundary.group_no = group_no
            app_boundary.boundary_code = boundary_code
            self.session.add(app_boundary)

    @pyqtSlot()
    def on_parcel_add_button_clicked(self):

        row = self.result_parcel_twidget.currentRow()
        if row == -1:
            return
        parcel_id = self.result_parcel_twidget.item(row, 0).data(Qt.UserRole)

        is_register = False
        for row in range(self.assigned_parcel_twidget.rowCount()):
            id = self.assigned_parcel_twidget.item(row, 0).data(Qt.UserRole)
            if id == parcel_id:
                is_register = True

        if is_register:
            PluginUtils.show_message(self, self.tr("Parcel Duplicate"), self.tr("This parcel already connected"))
            return

        parcel = self.session.query(CaPastureParcel).filter(CaPastureParcel.parcel_id == parcel_id).one()
        # pasture_type = self.session.query(ClPastureType).filter(ClPastureType.code == 1).one()
        item = QTableWidgetItem(parcel.parcel_id)
        item.setIcon(QIcon(QPixmap(":/plugins/lm2/parcel.png")))
        item.setData(Qt.UserRole, parcel.parcel_id)

        count = self.assigned_parcel_twidget.rowCount()
        self.assigned_parcel_twidget.insertRow(count)

        self.assigned_parcel_twidget.setItem(count, 0, item)

        item = QTableWidgetItem(parcel.address_neighbourhood)
        item.setData(Qt.UserRole, parcel.address_neighbourhood)
        self.assigned_parcel_twidget.setItem(count, 1, item)

        item = QTableWidgetItem(str(parcel.area_ga))
        item.setData(Qt.UserRole, parcel.area_ga)
        self.assigned_parcel_twidget.setItem(count, 2, item)

        item = QTableWidgetItem('1')
        item.setData(Qt.UserRole, 1)
        self.assigned_parcel_twidget.setItem(count, 3, item)

        item = QTableWidgetItem('12')
        item.setData(Qt.UserRole, 12)
        self.assigned_parcel_twidget.setItem(count, 4, item)

        item = QTableWidgetItem('360')
        item.setData(Qt.UserRole, 360)
        self.assigned_parcel_twidget.setItem(count, 5, item)

        app_pug_parcel_count = self.session.query(CtApplicationPUGParcel).filter(
            CtApplicationPUGParcel.application == self.application.app_no). \
            filter(CtApplicationPUGParcel.parcel == parcel_id).count()
        if app_pug_parcel_count == 0:
            app_pug_parcel = CtApplicationPUGParcel()
            app_pug_parcel.application = self.application.app_no
            app_pug_parcel.parcel = parcel_id
            self.session.add(app_pug_parcel)

    @pyqtSlot()
    def on_parcel_remove_button_clicked(self):

        selected_row = self.assigned_parcel_twidget.currentRow()
        parcel_id = self.assigned_parcel_twidget.item(selected_row, 0).data(Qt.UserRole)
        self.assigned_parcel_twidget.removeRow(selected_row)

        self.session.query(CtApplicationPUGParcel).filter(CtApplicationPUGParcel.application == self.application.app_no). \
            filter(CtApplicationPUGParcel.parcel == parcel_id).delete()

    @pyqtSlot()
    def on_boundary_remove_button_clicked(self):

        selected_row = self.assigned_boundary_twidget.currentRow()
        boundary_code = self.assigned_boundary_twidget.item(selected_row, 0).data(Qt.UserRole)
        self.assigned_boundary_twidget.removeRow(selected_row)

        boundary_count = self.session.query(CaPUGBoundary). \
            filter(CaPUGBoundary.code == boundary_code).count()
        if boundary_count == 1:
            boundary = self.session.query(CaPUGBoundary). \
                filter(CaPUGBoundary.code == boundary_code).one()
            boundary.group_name = ''

        self.session.query(CtAppGroupBoundary).filter(
            CtAppGroupBoundary.application == self.application.app_no). \
            filter(CtAppGroupBoundary.boundary_code == boundary_code).delete()

    @pyqtSlot()
    def on_pasture_add_button_clicked(self):

        selected_items = self.assigned_parcel_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please select person group."))
            return None

        row = self.assigned_parcel_twidget.currentRow()
        parcel_id = self.assigned_parcel_twidget.item(row, 0).text()

        pasture_item = self.pasture_type_cbox.itemData(self.pasture_type_cbox.currentIndex())

        try:
            count = 0
            pasture = self.session.query(ClPastureType).filter(ClPastureType.code == pasture_item).one()
            being_month = 1
            end_month = 12
            if pasture.code == 17:
                being_month = 6
                end_month = 8
            elif pasture.code == 18:
                being_month = 9
                end_month = 11
            elif pasture.code == 20:
                being_month = 12
                end_month = 2
            elif pasture.code == 18:
                being_month = 3
                end_month = 5

            item = QTableWidgetItem((pasture.description))
            item.setIcon(QIcon(QPixmap(":/plugins/lm2_pasture/bag.png")))
            item.setData(Qt.UserRole, pasture.code)
            item.setData(Qt.UserRole+1, parcel_id)
            self.pasture_type_twidget.insertRow(count)
            self.pasture_type_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(str(being_month))
            item.setData(Qt.UserRole, being_month)
            self.pasture_type_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(str(end_month))
            item.setData(Qt.UserRole, end_month)
            self.pasture_type_twidget.setItem(count, 2, item)

            item = QTableWidgetItem('90')
            item.setData(Qt.UserRole, 90)
            self.pasture_type_twidget.setItem(count, 3, item)

            count += 1
            self.pasture_type_cbox.removeItem(self.pasture_type_cbox.currentIndex())

            parcel_pasture = CtApplicationParcelPasture()
            parcel_pasture.application = self.application.app_no
            parcel_pasture.parcel = parcel_id
            parcel_pasture.pasture = pasture_item
            self.session.add(parcel_pasture)
        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("Sql Error"), e.message)

    @pyqtSlot()
    def on_pasture_remove_button_clicked(self):

        # if not len(self.assigned_parcel_twidget.selectedItems()) == 1:
        #     PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
        #     return
        #
        # if not len(self.pasture_type_twidget.selectedItems()) == 1:
        #     PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
        #     return

        selectedItem = self.pasture_type_twidget.selectedItems()[0]
        pasture_code = selectedItem.data(Qt.UserRole)
        pasture_text = selectedItem.text()

        self.pasture_type_cbox.addItem(pasture_text, pasture_code)
        row = self.pasture_type_twidget.currentRow()
        code = self.pasture_type_twidget.item(row, 0).data(Qt.UserRole)
        self.pasture_type_twidget.removeRow(row)

        row = self.assigned_parcel_twidget.currentRow()
        parcel_id = self.assigned_parcel_twidget.item(row, 0).text()



        self.session.query(CtApplicationParcelPasture).filter(
            CtApplicationParcelPasture.application == self.application.app_no). \
            filter(CtApplicationParcelPasture.parcel == parcel_id).\
            filter(CtApplicationParcelPasture.pasture == code).delete()

    @pyqtSlot(QTableWidgetItem)
    def on_assigned_parcel_twidget_itemClicked(self, item):

        self.__app_type_visible()

        self.pasture_type_twidget.setRowCount(0)
        row = self.assigned_parcel_twidget.currentRow()
        id_item = self.assigned_parcel_twidget.item(row, 0)
        parcel_id = id_item.data(Qt.UserRole)

        parcel_pastures = self.session.query(CtApplicationParcelPasture).\
            filter(CtApplicationParcelPasture.application == self.application.app_no).\
            filter(CtApplicationParcelPasture.parcel == parcel_id).all()
        count = 0
        for parcel_pasture in parcel_pastures:
            pasture = self.session.query(ClPastureType).filter(ClPastureType.code == parcel_pasture.pasture).one()
            code = pasture.code
            name = pasture.description
            item = QTableWidgetItem((name))
            item.setIcon(QIcon(QPixmap(":/plugins/lm2_pasture/bag.png")))
            item.setData(Qt.UserRole, code)
            item.setData(Qt.UserRole+1, parcel_id)
            self.pasture_type_twidget.insertRow(count)
            self.pasture_type_twidget.setItem(count, 0, item)

            begin_month = 0
            if parcel_pasture.begin_month:
                begin_month = parcel_pasture.begin_month
            item = QTableWidgetItem(str(begin_month))
            item.setData(Qt.UserRole, begin_month)
            self.pasture_type_twidget.setItem(count, 1, item)
            end_month = 0
            if parcel_pasture.end_month:
                end_month = parcel_pasture.end_month
            item = QTableWidgetItem(str(end_month))
            item.setData(Qt.UserRole, end_month)
            self.pasture_type_twidget.setItem(count, 2, item)
            days = 0
            if parcel_pasture.days:
                days = parcel_pasture.days
            item = QTableWidgetItem(str(days))
            item.setData(Qt.UserRole, days)
            self.pasture_type_twidget.setItem(count, 3, item)

            count += 1

            self.pasture_type_cbox.removeItem(self.pasture_type_cbox.findData(code))

    @pyqtSlot(QTableWidgetItem)
    def on_assigned_parcel_twidget_itemDoubleClicked(self, item):

        row = self.assigned_parcel_twidget.currentRow()
        parcel_id = self.assigned_parcel_twidget.item(row, 0).data(Qt.UserRole)
        self.__zoom_to_parcel(parcel_id)

    def __zoom_to_parcel(self, parcel_id, layer_name = None):

        LayerUtils.deselect_all()
        if layer_name is None:
            if len(parcel_id) == 12:
                layer_name = "ca_pasture_parcel"

        layer = LayerUtils.layer_by_data_source("s" + DatabaseUtils.current_working_soum_schema(), layer_name)

        restrictions = DatabaseUtils.working_l2_code()
        if layer is None:
            layer = LayerUtils.load_layer_by_name(layer_name, "parcel_id", restrictions)

        exp_string = ""

        if exp_string == "":
            exp_string = "parcel_id = \'" + parcel_id  + "\'"
        else:
            exp_string += " or parcel_id = \'" + parcel_id  + "\'"

        request = QgsFeatureRequest()
        request.setFilterExpression(exp_string)

        feature_ids = []
        iterator = layer.getFeatures(request)

        for feature in iterator:
            feature_ids.append(feature.id())

        if len(feature_ids) == 0:
            self.error_label.setText(self.tr("No parcel assigned"))

        layer.setSelectedFeatures(feature_ids)
        self.plugin.iface.mapCanvas().zoomToSelected(layer)