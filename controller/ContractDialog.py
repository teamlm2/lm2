__author__ = 'Topmap'
# coding=utf8

import os
import re
import math
import time
import locale
import win32api
import win32net
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *
from geoalchemy2.elements import WKTElement
from qgis.core import *
from sqlalchemy import func, or_, extract
from PyQt4.QtXml import *
from qgis.core import *
from qgis.gui import *
from inspect import currentframe
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from datetime import date, datetime, timedelta
from ..model import Constants
from ..model.BsPerson import *
from ..model.ClBank import *
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.AuLevel3 import *
from ..model.SetFeeZone import *
from ..model import SettingsConstants
from ..model.DatabaseHelper import *
from ..view.Ui_ContractDialog import *
from ..model.CtContractDocument import *
from ..model.ClPositionType import *
from ..model.ClContractCondition import *
from ..model.Enumerations import UserRight, UserRight_code
from ..model.CtDecisionApplication import *
from ..model.CtDecision import *
from ..model.LM2Exception import LM2Exception
from ..model.CtContractApplicationRole import *
from ..model.ClContractCancellationReason import *
from ..model.SetContractDocumentRole import SetContractDocumentRole
from ..model.SetApplicationTypeDocumentRole import SetApplicationTypeDocumentRole
from ..model.CtApplicationStatus import *
from ..model.SetCertificate import *
from ..model.SetUserGroupRole import *
from ..utils.FileUtils import FileUtils
from ..utils.PluginUtils import PluginUtils
from ..utils.SessionHandler import SessionHandler
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.FilePath import *
from .qt_classes.ComboBoxDelegate import *
from .qt_classes.DropLabel import DropLabel
from .qt_classes.IntegerSpinBoxDelegate import *
from .qt_classes.ObjectAppDocumentDelegate import ObjectAppDocumentDelegate
from .qt_classes.ContractDocumentDelegate import ContractDocumentDelegate
from docxtpl import DocxTemplate, RichText

CONTRACTOR_NAME = 0
CONTRACTOR_ID = 1
CONTRACTOR_SHARE = 2
CONTRACTOR_AREA = 3
CONTRACTOR_FEE_CALCULATED = 4
CONTRACTOR_FEE_CONTRACT = 5
CONTRACTOR_GRACE_PERIOD = 6
CONTRACTOR_PAYMENT_FREQUENCY = 7

APP_DOC_PROVIDED_COLUMN = 0
APP_DOC_TYPE_COLUMN = 1
APP_DOC_NAME_COLUMN = 2
APP_DOC_VIEW_COLUMN = 3

DOC_PROVIDED_COLUMN = 0
DOC_TYPE_COLUMN = 1
DOC_NAME_COLUMN = 2
DOC_OPEN_COLUMN = 3
DOC_REMOVE_COLUMN = 4
DOC_VIEW_COLUMN = 5


class ContractDialog(QDialog, Ui_ContractDialog, DatabaseHelper):

    def __init__(self, contract, navigator, attribute_update, parent=None):

        super(ContractDialog, self).__init__(parent)
        DatabaseHelper.__init__(self)
        self.navigator = navigator

        self.attribute_update = attribute_update
        self.session = SessionHandler().session_instance()

        self.contract = contract
        self.item_model = None
        self.updating = None

        self.setupUi(self)

        self.contract_date.setDate(QDate().currentDate())
        self.cancelation_date.setDate(QDate().currentDate())

        self.setWindowTitle(self.tr("Create / Edit Contract"))
        self.drop_label = DropLabel("application", self.application_groupbox)
        self.drop_label.itemDropped.connect(self.on_drop_label_itemDropped)
        self.close_button.clicked.connect(self.reject)
        self.contract_end_date.dateChanged.connect(self.__end_date_change)

        self.__setup_combo_boxes()
        self.__set_up_land_fee_twidget()
        self.__set_up_archive_land_fee_twidget()
        self.__setup_doc_twidgets()
        self.status_label.clear()
        self.is_certificate = False
        self.landfee_message_label1.setStyleSheet("QLabel {color : red;}")
        self.landfee_message_label2.setStyleSheet("QLabel {color : red;}")
        self.landfee_message_label1.setText(self.tr('Without parcel no land fee information is available.'))
        self.landfee_message_label2.clear()

        if self.attribute_update:
            self.__setup_mapping()
        else:
            try:
                self.__generate_contract_number()
            except LM2Exception, e:
                PluginUtils.show_error(self, e.title(), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                self.reject()

        self.__setup_permissions()
        self.__user_right_permissions()
        self.__setup_validators()

    def __user_right_permissions(self):

        user_name = QSettings().value(SettingsConstants.USER)
        user = self.session.query(SetRole).\
            filter(SetRole.user_name == user_name).\
            filter(SetRole.is_active == True).one()
        user_name_real = user.user_name_real

        user_rights = self.session.query(SetUserGroupRole).filter(SetUserGroupRole.user_name_real == user_name_real).all()
        for user_right in user_rights:
            if user_right.group_role == UserRight_code.contracting_update:
                if user_right.r_update:
                    self.contract_end_date.setEnabled(True)
                else:
                    self.contract_end_date.setEnabled(False)

    def __end_date_change(self, new_date):

        end = PluginUtils.convert_qt_date_to_python(new_date).date()
        begin_txt = self.contract_begin_edit.text()
        begin = datetime.strptime(begin_txt, '%Y-%m-%d')

        if end and begin:
            age_in_years = end.year - begin.year - ((end.month, end.day) < (begin.month, begin.day))
            months = (end.month - begin.month - (end.day < begin.day)) % 12
            # age = end - begin
            # age_in_days = age.days
            self.contract_duration_edit.setText(str(age_in_years))

    def __setup_validators(self):

        self.numbers_validator = QRegExpValidator(QRegExp("[1-9][0-9]+( *,*[1-9][0-9]+)*"), None)
        self.calculated_num_edit.setValidator(self.numbers_validator)

    def __generate_contract_number(self):

        try:
            contract_number_filter = "%-{0}/%".format(str(QDate().currentDate().toString("yyyy")))

            count = self.session.query(CtContract).filter(CtContract.contract_no != str(self.contract.contract_no)) \
                .filter(CtContract.contract_no.like("%-%")) \
                .filter(CtContract.contract_no.like(contract_number_filter)) \
                .order_by(func.substr(CtContract.contract_no, 10, 16).desc()).count()
            if count == 0:
                cu_max_number = "00001"
            else:
                cu_max_number = self.session.query(CtContract.contract_no) \
                    .filter(CtContract.contract_no != str(self.contract.contract_no)) \
                    .filter(CtContract.contract_no.like("%-%")) \
                    .filter(CtContract.contract_no.like(contract_number_filter)) \
                    .order_by(func.substr(CtContract.contract_no, 10, 16).desc()).first()
                cu_max_number = cu_max_number[0]

                minus_split_number = cu_max_number.split("-")
                slash_split_number = minus_split_number[1].split("/")
                cu_max_number = int(slash_split_number[1]) + 1

            soum = DatabaseUtils.current_working_soum_schema()
            year = QDate().currentDate().toString("yyyy")
            number = soum + "-" + year + "/" + str(cu_max_number).zfill(5)

            self.contract_num_edit.setText(number)
            self.contract.contract_no = number

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __certificate_type(self):

        try:
            # Find the first applicant's person_type and select the certificate number accordingly
            app_no = self.application_this_contract_based_edit.text()
            if len(app_no) == 0:
                return -1
            app_no_count = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).count()
            if app_no_count == 0:
                return -1

            app = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
            contractor = app.stakeholders.filter(CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE).first()

            person = contractor.person_ref
            person_type = person.type
            if person_type == 10 or person_type == 20:
                certificate_type = 10
            elif person_type == 30:
                certificate_type = 20
            elif person_type == 5 or person_type == 6:
                certificate_type = 30
            else:
                certificate_type = 40

            return certificate_type

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __set_certificate_no(self):

        certificate_no = self.__calculate_certificate_no()

        if certificate_no == None:
            certificate_no = 0
        if certificate_no != -1:
            self.calculated_num_edit.setText(str(certificate_no))

    def __calculate_certificate_no(self):

        # try:
        certificate_type = self.__certificate_type()

        certificate_settings = self.__certificate_settings(certificate_type)

        max_certificate_no = certificate_settings[Constants.CERTIFICATE_CURRENT_NUMBER] + 1

        # except SQLAlchemyError, e:
        #     raise LM2Exception(self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        if certificate_settings[Constants.CERTIFICATE_FIRST_NUMBER] <= max_certificate_no \
                <= certificate_settings[Constants.CERTIFICATE_LAST_NUMBER]:

            return max_certificate_no

        else:
            self.error_label.setText(self.tr("The certificate number is out of range. Change the Admin Settings."))
            self.error_label.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            self.apply_button.setEnabled(False)
            return -1

    def __certificate_settings(self, certificate_type):

        first_no, last_no, current_no = self.session.query(SetCertificate.range_first_no, SetCertificate.range_last_no, SetCertificate.current_no)\
            .filter(SetCertificate.certificate_type == certificate_type).order_by(SetCertificate.begin_date.desc()).limit(1).one()

        return {Constants.CERTIFICATE_FIRST_NUMBER: first_no, Constants.CERTIFICATE_LAST_NUMBER: last_no, Constants.CERTIFICATE_CURRENT_NUMBER: current_no}

    def __setup_permissions(self):

        user_name = QSettings().value(SettingsConstants.USER)
        user_rights = DatabaseUtils.userright_by_name(user_name)

        if UserRight.contracting_update in user_rights:
            self.apply_button.setEnabled(True)
            self.unassign_button.setEnabled(True)
            self.search_button.setEnabled(True)
            self.accept_button.setEnabled(True)
            self.status_groupbox.setEnabled(True)
            self.contract_cancellation_groupbox.setEnabled(True)
            self.documents_groupbox.setEnabled(True)
            self.contract_end_date.setEnabled(True)
        else:
            self.apply_button.setEnabled(False)
            self.unassign_button.setEnabled(False)
            self.search_button.setEnabled(False)
            self.accept_button.setEnabled(False)
            self.status_groupbox.setEnabled(False)
            self.contract_cancellation_groupbox.setEnabled(False)
            self.documents_groupbox.setEnabled(False)
            self.contract_end_date.setEnabled(False)

    def __setup_mapping(self):

        self.calculated_num_edit.setEnabled(True)
        self.calculated_num_edit.setReadOnly(True)
        # try:
        self.contract_num_edit.setText(self.contract.contract_no)
        self.calculated_num_edit.setText(str(self.contract.certificate_no))
        qt_date = PluginUtils.convert_python_date_to_qt(self.contract.contract_date)
        if qt_date is not None:
            self.contract_date.setDate(qt_date)

        contract_begin = PluginUtils.convert_python_date_to_qt(self.contract.contract_begin)
        contract_end = PluginUtils.convert_python_date_to_qt(self.contract.contract_end)

        if contract_begin is not None:
            self.contract_begin_edit.setText(contract_begin.toString(Constants.DATABASE_DATE_FORMAT))

        if contract_end is not None:
            # self.contract_end_edit.setText(contract_end.toString(Constants.DATABASE_DATE_FORMAT))
            self.contract_end_date.setDate(contract_end)
            duration = contract_end.year() - contract_begin.year()
            self.contract_duration_edit.setText(str(duration))
        else:
            application_role = self.contract.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CREATES).one()
            application = application_role.application_ref
            parcel = application.parcel_ref
            # decision date
            last_decision = self.session.query(CtDecision).join(CtApplication.decision_result) \
                .join(CtDecisionApplication.decision_ref) \
                .filter(CtApplication.app_no == application.app_no) \
                .filter(CtDecisionApplication.decision_result == Constants.DECISION_RESULT_APPROVED) \
                .one()

            qt_date = PluginUtils.convert_python_date_to_qt(last_decision.decision_date)

            if qt_date is not None:
                self.contract_begin_edit.setText(qt_date.toString(Constants.DATABASE_DATE_FORMAT))

            if application.app_type in Constants.APPLICATION_TYPE_WITH_DURATION:
                years_approved = application.approved_duration
                if years_approved:
                    qt_date = PluginUtils.convert_python_date_to_qt(last_decision.decision_date)

                    if qt_date is not None:
                        dec_year = qt_date.year()
                        end_year = dec_year + int(years_approved)
                        end_date = QDate(end_year, qt_date.month(), qt_date.day())

                        # self.contract_end_edit.setText(end_date.toString(Constants.DATABASE_DATE_FORMAT))
                        self.contract_end_date.setDate(end_date)
                        self.contract_duration_edit.setText(str(years_approved))

        self.__setup_status()

        if self.contract.cancellation_date:
            qt_date = PluginUtils.convert_python_date_to_qt(self.contract.cancellation_date)

            self.cancelation_date.setDate(qt_date)
            self.cancellation_date_check_box.setCheckState(Qt.Checked)

            if self.contract.cancellation_reason is not None:
                self.other_reason_rbutton.setChecked(True)
                self.other_reason_cbox.setCurrentIndex(
                    self.other_reason_cbox.findData(self.contract.cancellation_reason))

            cancellation_application_c = self.contract.application_roles\
                .filter_by(role=Constants.APP_ROLE_CANCEL).count()
            if cancellation_application_c == 1:
                # self.application_based_rbutton.setChecked(True)
                cancellation_application = self.contract.application_roles\
                    .filter_by(role=Constants.APP_ROLE_CANCEL).one()

                if cancellation_application is None:
                    PluginUtils.show_error(self, self.tr("Error loading Contract"),
                                           self.tr("Could not load contract. Cancellation application not found"))
                    self.reject()
                self.app_number_cbox.clear()
                self.app_number_cbox.addItem(cancellation_application.application, cancellation_application.application)
                self.app_number_cbox.setCurrentIndex(
                    self.app_number_cbox.findText(cancellation_application.application))
                self.type_edit.setText(cancellation_application.application_ref.app_type_ref.description)

                app_persons = self.session.query(CtApplicationPersonRole).\
                    filter(CtApplicationPersonRole.application == cancellation_application.application).all()
                for app_person in app_persons:
                    self.person_id_edit.setText(app_person.person)

        application_role = self.contract.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CREATES).one()
        application = application_role.application_ref

        if application_role is None or application is None:
            PluginUtils.show_error(self, self.tr("Error loading Contract"),
                                   self.tr("This contract has no valid application assigned."))
            self.reject()
            return

        self.application_this_contract_based_edit.setText(application.app_no)
        self.application_type_edit.setText(application.app_type_ref.description)

        parcel = application.parcel_ref
        bag_name = ''
        bag_areas = {}
        bag_count = self.session.query(AuLevel3).filter(parcel.geometry.ST_Within(AuLevel3.geometry)).count()
        if bag_count != 0:
            bag = self.session.query(AuLevel3).filter(parcel.geometry.ST_Within(AuLevel3.geometry)).one()
            bag_name = bag.name
        else:
            bags = self.session.query(AuLevel3).filter(parcel.geometry.ST_Intersects(AuLevel3.geometry)).all()
            for bag in bags:
                area = self.session.query(func.ST_Area(parcel.geometry.ST_Intersection(AuLevel3.geometry))).\
             filter(AuLevel3.code == bag.code).\
                    filter(parcel.geometry.ST_Intersects(AuLevel3.geometry)).one()

                bag_areas.update({bag.code:area[0]})
            bag_code = max(bag_areas, key=bag_areas.get)
            bag = self.session.query(AuLevel3).filter(AuLevel3.code == bag_code).one()
            bag_name = bag.name

        self.id_main_edit.setText(parcel.parcel_id)
        self.old_id_edit.setText(parcel.old_parcel_id)
        self.geo_id_edit.setText(parcel.geo_id)
        self.calculated_area_edit.setText(str(round(parcel.area_m2,1)))
        self.bag_edit.setText(bag_name)
        self.street_name_edit.setText(parcel.address_streetname)
        self.khashaa_edit.setText(parcel.address_khashaa)

        if parcel.documented_area_m2 is not None:
            self.documents_area_edit.setText(str(parcel.documented_area_m2))
        else:
            self.documents_area_edit.setText("")

        soum = PluginUtils.soum_from_parcel(parcel.parcel_id)

        if soum is None:
            PluginUtils.show_error(self, self.tr("Error loading Contract"), self.tr("Parcel is not within a soum."))
            self.reject()
            return

        soum_desc = self.session.query(AuLevel2.name).filter(AuLevel2.code == soum).one()
        aimag = self.session.query(AuLevel1.name).filter(AuLevel1.code == soum[:3]).one()
        self.soum_edit.setText(soum_desc[0])
        self.aimag_edit.setText(aimag[0])

        if parcel.landuse_ref:
            self.land_use_type_edit.setText(parcel.landuse_ref.description)

        self.__populate_landfee_tab()
        self.__populate_archive_period_cbox()
        self.__populate_conditions_tab()

        # except SQLAlchemyError, e:
        #     PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __setup_status(self):

        if self.contract.status == Constants.CONTRACT_STATUS_DRAFT:
            self.draft_rbutton.setChecked(True)
        elif self.contract.status == Constants.CONTRACT_STATUS_ACTIVE:
            self.active_rbutton.setChecked(True)
        elif self.contract.status == Constants.CONTRACT_STATUS_EXPIRED:
            self.expired_rbutton.setChecked(True)
        elif self.contract.status == Constants.CONTRACT_STATUS_CANCELLED:
            self.cancelled_rbutton.setChecked(True)

    def __setup_combo_boxes(self):

        database_name = QSettings().value(SettingsConstants.DATABASE_NAME)
        user_code = database_name.split('_')[1]
        user_start = 'user' + user_code

        self.document_path_edit.setText(FilePath.contrac_file_path())
        try:
            restrictions = DatabaseUtils.working_l2_code()
            user = DatabaseUtils.current_user()
            currect_user = user.position
            # if restrictions[3:] == '01':
            self.print_officer_cbox.setDisabled(False)
            print_officers = self.session.query(SetRole).filter(or_(SetRole.position == 9, SetRole.position == currect_user)).all()
                # filter(or_(SetRole.position == 9, SetRole.position == currect_user)). \
                # filter(SetRole.is_active == True). \
                # filter(SetRole.user_name.startswith(user_start)).all()
            for officer in print_officers:
                officer_name = officer.surname[:1]+'.'+officer.first_name
                self.print_officer_cbox.addItem(officer_name, officer.user_name)

            app_contract_count = self.session.query(CtContractApplicationRole).filter(CtContractApplicationRole.contract == self.contract.contract_no).count()

            if app_contract_count == 1:
                app_contract = self.session.query(CtContractApplicationRole).filter_by(contract=self.contract.contract_no).one()
                application = self.session.query(CtApplication).filter_by(app_no=app_contract.application).one()
                apps = self.session.query(CtApplication.app_no).order_by(CtApplication.app_no).all()

                for app in apps:
                    self.app_number_cbox.addItem(app[0])

                self.app_number_cbox.setCurrentIndex(-1)

            reasons = self.session.query(ClContractCancellationReason).all()
            for reason in reasons:
                self.other_reason_cbox.addItem(reason.description, reason.code)

            self.__setup_applicant_cbox()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    def __setup_applicant_cbox(self):

        self.applicant_documents_cbox.clear()
        try:
            con_app_roles = self.contract.application_roles\
                .filter(CtContractApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).all()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        self.updating = True

        for con_app_role in con_app_roles:
            for app_person_role in con_app_role.application_ref.stakeholders.all():
                person = app_person_role.person_ref
                if person.first_name is None:
                    person_label = u"{0}".format(person.name)
                else:
                    person_label = u"{0}, {1}".format(person.name, person.first_name)
                self.applicant_documents_cbox.addItem(person_label, person.person_id)

        self.updating = False
        # self.__update_app_documents_twidget()

    def __copy_application_from_navigator(self):

        selected_applications = self.navigator.application_results_twidget.selectedItems()

        if len(selected_applications) == 0:
            PluginUtils.show_error(self, self.tr("Query error"), self.tr("No applications selected in the Navigator."))
            return

        selected_application = selected_applications[0]

        try:
            current_app_no = selected_application.data(Qt.UserRole)
            app_no_count = self.session.query(CtApplication).filter_by(app_no=current_app_no).count()

            if app_no_count == 0:
                PluginUtils.show_error(self, self.tr("Working Soum"),
                                       self.tr("The selected Application {0} is not within the working soum. \n \n "
                                               "Change the Working soum to create a new application for the parcel.")
                                       .format(current_app_no))
                return

            application = self.session.query(CtApplication).filter_by(app_no=current_app_no).one()

            if not self.__validate_application(application):
                return

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        self.found_edit.setText(application.app_no)

    def __validate_application(self, application):

        #checks that there is a decision for this application
        #checks that the decision was "approved"
        app_contract_count = self.session.query(CtContractApplicationRole).\
            filter(CtContractApplicationRole.application == application.app_no).\
            filter(CtContractApplicationRole.role != 10).count()
        if app_contract_count > 0:
            PluginUtils.show_error(self, self.tr("Application Error"),
                                   self.tr("This application with contract.."))
            return False

        last_decision_count = self.session.query(CtDecision).join(CtApplication.decision_result).filter(
            CtApplication.app_no == application.app_no) \
            .order_by(CtDecision.decision_date.desc()).count()
        if last_decision_count == 0:
            PluginUtils.show_error(self, self.tr("Application Error"),
                                   self.tr("It is not allowed to add an application without decision."))
            return False

        last_decision_count = self.session.query(CtDecision).join(CtApplication.decision_result) \
            .join(CtDecisionApplication.decision_ref) \
            .filter(CtApplication.app_no == application.app_no) \
            .filter(CtDecisionApplication.decision_result == Constants.DECISION_RESULT_APPROVED).count()

        if last_decision_count == 0:
            PluginUtils.show_error(self, self.tr("Application Error"),
                                   self.tr("There is no approved decision result for this application."))
            return False

        #check that there is a parcel for this application
        if application.parcel is None:
            PluginUtils.show_error(self, self.tr("Application Error"),
                                   self.tr("It is not allowed to add applications without assigned parcel."))
            return False

        #check that there is a duration, if there should be one
        if application.app_type in Constants.APPLICATION_TYPE_WITH_DURATION:
            if application.approved_duration == 0 or application is None:
                PluginUtils.show_error(self, self.tr("Application Error"),
                                       self.tr("There is no approved duration for this application."))
                return False

        if application.app_type not in Constants.CONTRACT_TYPES:
            PluginUtils.show_error(self, self.tr("Application Error"),
                                   self.tr("Its not allowed to create a contract based on this application type"))
            return False

        return True

    def __calculate_age(self):

        duration = int(self.contract_duration_edit.text())
        if not duration > 0:
            PluginUtils.show_error(self, self.tr("End Date Error"),
                                       self.tr("Its not allowed to contract date."))
            return False
        return True
        # begin = self.contract.contract_begin
        # end = PluginUtils.convert_qt_date_to_python(self.contract_end_date.date()).date()
        # print begin
        # print end
        # # if end and begin:
        # age_in_years = end.year - begin.year - ((end.month, end.day) < (begin.month, begin.day))
        # months = (end.month - begin.month - (end.day < begin.day)) % 12
        # age = end - begin
        # age_in_days = age.days
        #
        # if not age_in_years > 0:
        #     PluginUtils.show_error(self, self.tr("End Date Error"),
        #                            self.tr("Its not allowed to contract date."))
        #     return False
        # return True
        # if age_in_years >= 80:
        #     return 80, 'years or older'
        # if age_in_years >= 12:
        #     return age_in_years, 'years'
        # elif age_in_years >= 2:
        #     half = 'and a half ' if months > 6 else ''
        #     return age_in_years, '%syears' % half
        # elif months >= 6:
        #     return months, 'months'
        # elif age_in_days >= 14:
        #     return age_in_days / 7, 'weeks'
        # else:
        #     return age_in_days, 'days'

    def __validate_settings(self):

        if len(self.landfee_message_label1.text()) > 0:
            PluginUtils.show_error(self, self.tr("Land Fees"), self.landfee_message_label1.text())
            return False
        if not self.__calculate_age():
            return False

        return True

    def __load_application_information(self):

        # parcel infos:
        application_role = self.contract.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CREATES).one()
        application = application_role.application_ref
        parcel = application.parcel_ref

        self.id_main_edit.setText(parcel.parcel_id)
        self.old_id_edit.setText(parcel.old_parcel_id)
        self.geo_id_edit.setText(parcel.geo_id)
        if parcel.landuse_ref is not None:
            self.land_use_type_edit.setText(parcel.landuse_ref.description)
        self.calculated_area_edit.setText(str(parcel.area_m2))
        if parcel.documented_area_m2 != None:
            self.documents_area_edit.setText(str(parcel.documented_area_m2))
        else:
            self.documents_area_edit.setText(str(" "))

        aimag = application.app_no[:3]
        soum = application.app_no[:5]

        aimag_name = self.session.query(AuLevel1.name).filter(AuLevel1.code == aimag).one()
        soum_name = self.session.query(AuLevel2.name).filter(AuLevel2.code == soum).one()

        self.aimag_edit.setText(aimag_name[0])
        self.soum_edit.setText(soum_name[0])

        self.khashaa_edit.setText(parcel.address_khashaa)
        self.street_name_edit.setText(parcel.address_streetname)
        self.bag_edit.setText(parcel.address_neighbourhood)

        #decision date
        last_decision = self.session.query(CtDecision).join(CtApplication.decision_result) \
            .join(CtDecisionApplication.decision_ref) \
            .filter(CtApplication.app_no == application.app_no) \
            .filter(CtDecisionApplication.decision_result == Constants.DECISION_RESULT_APPROVED) \
            .one()

        qt_date = PluginUtils.convert_python_date_to_qt(last_decision.decision_date)
        if qt_date is not None:
            self.contract_begin_edit.setText(qt_date.toString(Constants.DATABASE_DATE_FORMAT))

        if application.app_type in Constants.APPLICATION_TYPE_WITH_DURATION:
            years_approved = application.approved_duration
            if years_approved:
                qt_date = PluginUtils.convert_python_date_to_qt(last_decision.decision_date)

                if qt_date is not None:
                    dec_year = qt_date.year()
                    end_year = dec_year + int(years_approved)
                    end_date = QDate(end_year, qt_date.month(), qt_date.day())
                    # self.contract_end_edit.setText(end_date.toString(Constants.DATABASE_DATE_FORMAT))
                    self.contract_end_date.setDate(end_date)
                    self.contract_duration_edit.setText(str(years_approved))
            else:
                # self.contract_end_edit.setText("")
                self.contract_duration_edit.setText("")

    def __contract_status(self):

        if self.draft_rbutton.isChecked():
            return Constants.CONTRACT_STATUS_DRAFT
        elif self.active_rbutton.isChecked():
            return Constants.CONTRACT_STATUS_ACTIVE
        elif self.expired_rbutton.isChecked():
            return Constants.CONTRACT_STATUS_EXPIRED
        elif self.cancelled_rbutton.isChecked():
            return Constants.CONTRACT_STATUS_CANCELLED

    def __populate_archive_period_cbox(self):

        self.time_period_cbox.clear()
        query = self.session.query(CtArchivedFee.valid_from, CtArchivedFee.valid_till).distinct(). \
            filter(CtArchivedFee.contract == self.contract.contract_no).order_by(CtArchivedFee.valid_from)
        for valid_from, valid_till in query:
            self.time_period_cbox.addItem(str(valid_from) + ' to ' + str(valid_till), valid_from)

    def __add_archived_fee_row(self, row, person, fee):

        item = QTableWidgetItem(u'{0}, {1}'.format(person.name, person.first_name))
        item.setData(Qt.UserRole, person.person_id)
        self.__lock_item(item)
        self.archive_land_fee_twidget.setItem(row, CONTRACTOR_NAME, item)
        item = QTableWidgetItem(u'{0}'.format(person.person_id))
        self.__lock_item(item)
        self.archive_land_fee_twidget.setItem(row, CONTRACTOR_ID, item)
        item = QTableWidgetItem('{0}'.format(fee.share))
        self.__lock_item(item)
        self.archive_land_fee_twidget.setItem(row, CONTRACTOR_SHARE, item)
        item = QTableWidgetItem('{0}'.format(fee.area))
        self.__lock_item(item)
        self.archive_land_fee_twidget.setItem(row, CONTRACTOR_AREA, item)
        item = QTableWidgetItem('{0}'.format(fee.fee_calculated))
        self.__lock_item(item)
        self.archive_land_fee_twidget.setItem(row, CONTRACTOR_FEE_CALCULATED, item)
        item = QTableWidgetItem('{0}'.format(fee.fee_contract))
        self.__lock_item(item)
        self.archive_land_fee_twidget.setItem(row, CONTRACTOR_FEE_CONTRACT, item)
        item = QTableWidgetItem('{0}'.format(fee.grace_period))
        self.__lock_item(item)
        self.archive_land_fee_twidget.setItem(row, CONTRACTOR_GRACE_PERIOD, item)
        payment_frequency = self.session.query(ClPaymentFrequency).get(fee.payment_frequency)
        item = QTableWidgetItem(u'{0}'.format(payment_frequency.description))
        self.__lock_item(item)
        self.archive_land_fee_twidget.setItem(row, CONTRACTOR_PAYMENT_FREQUENCY, item)

    def __populate_landfee_tab(self):

        self.landfee_message_label1.clear()
        self.landfee_message_label2.clear()

        self.land_fee_twidget.clearContents()
        self.land_fee_twidget.setRowCount(0)

        parcel_id = self.id_main_edit.text().strip()
        if len(parcel_id) == 0:
            self.landfee_message_label1.setText(self.tr('Without parcel no land fee information is available.'))
            return

        count = self.session.query(SetBaseFee).filter(SetFeeZone.geometry.ST_Contains(CaParcel.geometry)). \
            filter(CaParcel.parcel_id == parcel_id). \
            filter(SetBaseFee.fee_zone == SetFeeZone.zone_id). \
            filter(SetBaseFee.landuse == CaParcel.landuse). \
            count()

        if count == 0:
            self.landfee_message_label1.setText(self.tr('No fee zone or base fee found for the parcel.'))
            return

        base_fee = self.session.query(SetBaseFee).filter(SetFeeZone.geometry.ST_Contains(CaParcel.geometry)). \
            filter(CaParcel.parcel_id == parcel_id). \
            filter(SetBaseFee.fee_zone == SetFeeZone.zone_id). \
            filter(SetBaseFee.landuse == CaParcel.landuse). \
            one()

        self.base_fee_edit.setText('{0}'.format(base_fee.base_fee_per_m2))
        self.subsidized_area_edit.setText('{0}'.format(base_fee.subsidized_area))
        self.subsidized_fee_rate_edit.setText('{0}'.format(base_fee.subsidized_fee_rate))

        app_no = self.application_this_contract_based_edit.text()
        if len(app_no) == 0:
            return
        app_no_count = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).count()
        if app_no_count == 0:
            return

        app = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
        contractors = app.stakeholders.filter(CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE).all()

        if app_no[6:-9] == '07' or app_no[6:-9] == '14' or app_no[6:-9] == '23':
            contractors = app.stakeholders.filter(CtApplicationPersonRole.role == Constants.NEW_RIGHT_HOLDER_CODE).all()
        self.land_fee_twidget.setRowCount(len(contractors))
        row = 0
        for contractor in contractors:
            person = contractor.person_ref
            fee_count = person.fees.filter(CtFee.contract == self.contract.contract_no).count()
            if fee_count == 0:
                self.__add_fee_row(row, contractor, parcel_id, base_fee.base_fee_per_m2,
                                   base_fee.subsidized_area, base_fee.subsidized_fee_rate)
            else:
                fee = person.fees.filter(CtFee.contract == self.contract.contract_no).one()
                self.__add_fee_row2(row, contractor, fee)
            row += 1

        self.land_fee_twidget.resizeColumnToContents(0)
        self.land_fee_twidget.resizeColumnToContents(1)
        self.land_fee_twidget.resizeColumnToContents(2)
        self.land_fee_twidget.resizeColumnToContents(3)
        self.land_fee_twidget.resizeColumnToContents(4)
        self.land_fee_twidget.resizeColumnToContents(5)
        self.land_fee_twidget.resizeColumnToContents(6)
        self.land_fee_twidget.horizontalHeader().setResizeMode(7, QHeaderView.Stretch)

    def __set_up_land_fee_twidget(self):

        self.__setup_twidget(self.land_fee_twidget)

        code_list = list()
        descriptions = self.session.query(ClPaymentFrequency.description).order_by(ClPaymentFrequency.description)
        for description in descriptions:
            code_list.append(description[0])

        delegate = IntegerSpinBoxDelegate(CONTRACTOR_FEE_CONTRACT, 0, 10000000, 0, 100, self.land_fee_twidget)
        self.land_fee_twidget.setItemDelegateForColumn(CONTRACTOR_FEE_CONTRACT, delegate)
        delegate = IntegerSpinBoxDelegate(CONTRACTOR_GRACE_PERIOD, 0, 120, 0, 5, self.land_fee_twidget)
        self.land_fee_twidget.setItemDelegateForColumn(CONTRACTOR_GRACE_PERIOD, delegate)
        delegate = ComboBoxDelegate(CONTRACTOR_PAYMENT_FREQUENCY, code_list, self.land_fee_twidget)
        self.land_fee_twidget.setItemDelegateForColumn(CONTRACTOR_PAYMENT_FREQUENCY, delegate)

    def __set_up_archive_land_fee_twidget(self):

        self.__setup_twidget(self.archive_land_fee_twidget)

    def __setup_twidget(self, table_widget):

        table_widget.setAlternatingRowColors(True)
        table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        table_widget.setSelectionMode(QTableWidget.SingleSelection)

    def __setup_doc_twidgets(self):

        self.app_doc_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.app_doc_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.app_doc_twidget.horizontalHeader().setDefaultSectionSize(120)
        self.app_doc_twidget.horizontalHeader().resizeSection(0, 50)
        self.app_doc_twidget.horizontalHeader().resizeSection(1, 350)
        self.app_doc_twidget.horizontalHeader().resizeSection(2, 220)
        self.app_doc_twidget.horizontalHeader().resizeSection(3, 50)

        delegate = ObjectAppDocumentDelegate(self.app_doc_twidget, self)
        self.app_doc_twidget.setItemDelegate(delegate)

        self.doc_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.doc_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.doc_twidget.horizontalHeader().resizeSection(0, 50)
        self.doc_twidget.horizontalHeader().resizeSection(1, 270)
        self.doc_twidget.horizontalHeader().resizeSection(2, 200)
        self.doc_twidget.horizontalHeader().resizeSection(3, 50)
        self.doc_twidget.horizontalHeader().resizeSection(4, 50)
        self.doc_twidget.horizontalHeader().resizeSection(5, 50)

        delegate = ContractDocumentDelegate(self.doc_twidget, self)
        self.doc_twidget.setItemDelegate(delegate)

        try:
            self.__add_doc_types()
            # self.__update_doc_twidget()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    def __remove_document_items(self, twidget):

        while twidget.rowCount() > 0:
            twidget.removeRow(0)

    def __update_app_documents_twidget(self):

        self.__remove_document_items(self.app_doc_twidget)
        try:
            count = self.contract.application_roles\
                        .filter(CtContractApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).count()
            if count == 0: return

            con_app_roles = self.contract.application_roles\
                        .filter(CtContractApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).one()

            current_app_type = con_app_roles.application_ref.app_type
            required_doc_types = self.session.query(SetApplicationTypeDocumentRole)\
                                        .filter_by(application_type=current_app_type).all()

            for docType in required_doc_types:
                item_provided = QTableWidgetItem()
                item_provided.setCheckState(Qt.Unchecked)

                item_doc_type = QTableWidgetItem(docType.document_role_ref.description)
                item_doc_type.setData(Qt.UserRole, docType.document_role_ref.code)
                item_doc_type.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                item_name = QTableWidgetItem("")
                item_name.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                item_view = QTableWidgetItem("")
                row = self.app_doc_twidget.rowCount()

                self.app_doc_twidget.insertRow(row)
                self.app_doc_twidget.setItem(row, APP_DOC_TYPE_COLUMN, item_doc_type)
                self.app_doc_twidget.setItem(row, APP_DOC_NAME_COLUMN, item_name)
                self.app_doc_twidget.setItem(row, APP_DOC_PROVIDED_COLUMN, item_provided)
                self.app_doc_twidget.setItem(row, APP_DOC_VIEW_COLUMN, item_view)

            app_no = self.application_this_contract_based_edit.text()
            file_path = FilePath.app_file_path()+'/'+ app_no

            for file in os.listdir(file_path):
                os.listdir(file_path)
                if file.endswith(".pdf"):
                    doc_type = file[18:-4]
                    file_name = file
                    app_no = file[:17]

                    for i in range(self.app_doc_twidget.rowCount()):
                        doc_type_item = self.app_doc_twidget.item(i, APP_DOC_TYPE_COLUMN)

                        doc_type_code = str(doc_type_item.data(Qt.UserRole))

                        if len(str(doc_type_item.data(Qt.UserRole))) == 1:
                            doc_type_code = '0'+ str(doc_type_item.data(Qt.UserRole))
                        if len(doc_type) == 1:
                            doc_type = '0' + doc_type

                        if doc_type == doc_type_code and self.application_this_contract_based_edit.text() == app_no:
                                item_name = self.app_doc_twidget.item(i, APP_DOC_NAME_COLUMN)
                                item_name.setData(Qt.UserRole, app_no)
                                item_name.setText(file_name)

                                item_provided = self.app_doc_twidget.item(i, APP_DOC_PROVIDED_COLUMN)
                                item_provided.setCheckState(Qt.Checked)

                                self.app_doc_twidget.setItem(i, 0, item_provided)
                                self.app_doc_twidget.setItem(i, 2, item_name)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    def __add_doc_types(self):

        required_doc_types = self.session.query(SetContractDocumentRole).all()

        for docType in required_doc_types:

            item_provided = QTableWidgetItem()
            item_provided.setCheckState(Qt.Unchecked)

            item_doc_type = QTableWidgetItem(docType.role_ref.description)
            item_doc_type.setData(Qt.UserRole, docType.role_ref.code)
            item_doc_type.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

            item_name = QTableWidgetItem("")
            item_name.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

            item_view = QTableWidgetItem("")
            item_delete = QTableWidgetItem("")
            item_open = QTableWidgetItem("")
            row = self.doc_twidget.rowCount()

            self.doc_twidget.insertRow(row)
            self.doc_twidget.setItem(row, DOC_TYPE_COLUMN, item_doc_type)
            self.doc_twidget.setItem(row, DOC_NAME_COLUMN, item_name)
            self.doc_twidget.setItem(row, DOC_PROVIDED_COLUMN, item_provided)
            self.doc_twidget.setItem(row, DOC_VIEW_COLUMN, item_view)
            self.doc_twidget.setItem(row, DOC_OPEN_COLUMN, item_open)
            self.doc_twidget.setItem(row, DOC_REMOVE_COLUMN, item_delete)

    @pyqtSlot()
    def on_load_app_doc_button_clicked(self):

        self.__update_app_documents_twidget()

    @pyqtSlot()
    def on_load_doc_button_clicked(self):

        self.__update_doc_twidget()

    def __update_doc_twidget(self):

        file_path = FilePath.contrac_file_path()
        contract_no = self.contract.contract_no
        contract_no = contract_no.replace("/", "-")
        file_path = file_path + '/' + contract_no
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        for file in os.listdir(file_path):
            os.listdir(file_path)
            if file.endswith(".pdf"):
                doc_type = file[17:-4]
                file_name = file
                contract_no = file[:16]

                contract_no = contract_no[:10] +'/'+ contract_no[-5:]

            for i in range(self.doc_twidget.rowCount()):
                doc_type_item = self.doc_twidget.item(i, DOC_TYPE_COLUMN)

                doc_type_code = str(doc_type_item.data(Qt.UserRole))

                if len(str(doc_type_item.data(Qt.UserRole))) == 1:
                    doc_type_code = '0'+ str(doc_type_item.data(Qt.UserRole))
                if len(doc_type) == 1:
                    doc_type = '0' + doc_type

                if doc_type == doc_type_code and self.contract.contract_no == contract_no:
                    item_name = self.doc_twidget.item(i, DOC_NAME_COLUMN)
                    item_name.setText(file_name)

                    item_provided = self.doc_twidget.item(i, DOC_PROVIDED_COLUMN)
                    item_provided.setCheckState(Qt.Checked)

                    item_open = self.doc_twidget.item(i, DOC_OPEN_COLUMN)
                    item_remove = self.doc_twidget.item(i, DOC_REMOVE_COLUMN)
                    item_view = self.doc_twidget.item(i, DOC_VIEW_COLUMN)

                    self.doc_twidget.setItem(i, DOC_PROVIDED_COLUMN, item_provided)
                    self.doc_twidget.setItem(i, DOC_OPEN_COLUMN, item_open)
                    self.doc_twidget.setItem(i, DOC_REMOVE_COLUMN, item_remove)
                    self.doc_twidget.setItem(i, DOC_VIEW_COLUMN, item_view)
                    self.doc_twidget.setItem(i, DOC_NAME_COLUMN, item_name)

    def __add_fee_row(self, row, contractor, parcel_id, base_fee_per_m2, subsidized_area, subsidized_fee_rate):

        # TODO: fix rounding issues
        parcel_area = self.session.query(CaParcel.area_m2).filter(CaParcel.parcel_id == parcel_id).one()[0]
        parcel_area = round(parcel_area)

        item = QTableWidgetItem(u'{0}, {1}'.format(contractor.person_ref.name, contractor.person_ref.first_name))
        item.setData(Qt.UserRole, contractor.person_ref.person_id)
        self.land_fee_twidget.setItem(row, CONTRACTOR_NAME, item)
        item = QTableWidgetItem(u'{0}'.format(contractor.person_ref.person_id))
        self.__lock_item(item)
        self.land_fee_twidget.setItem(row, CONTRACTOR_ID, item)
        item = QTableWidgetItem('{0}'.format(contractor.share))
        self.__lock_item(item)
        self.land_fee_twidget.setItem(row, CONTRACTOR_SHARE, item)
        contractor_area = int(round(float(contractor.share) * parcel_area))
        item = QTableWidgetItem('{0}'.format(contractor_area))
        self.__lock_item(item)
        self.land_fee_twidget.setItem(row, CONTRACTOR_AREA, item)
        contractor_subsidized_area = int(round(float(contractor.share) * subsidized_area))
        fee_subsidized = (contractor_subsidized_area * float(base_fee_per_m2))-(contractor_subsidized_area * float(base_fee_per_m2) * (float(subsidized_fee_rate) / 100))
        fee_standard = (contractor_area - contractor_subsidized_area) * float(base_fee_per_m2)
        fee_base = contractor_area * float(base_fee_per_m2)*float((100-subsidized_fee_rate)/100)
        fee_calculated = int(round(fee_base if fee_standard <= 0 else fee_subsidized + fee_standard))

        #if parcel_area > subsidized_area:pg_cursors
        #fee_calculated = float(contractor.share) * ((parcel_area - subsidized_area) * base_fee_per_m2 + float(subsidized_area * base_fee_per_m2 * subsidized_fee_rate / 100))
        #elif parcel_area <= subsidized_area:
        #fee_calculated = float(contractor.share) * (parcel_area * base_fee_per_m2 * subsidized_fee_rate / 100)

        item = QTableWidgetItem('{0}'.format(fee_calculated))
        self.__lock_item(item)
        self.land_fee_twidget.setItem(row, CONTRACTOR_FEE_CALCULATED, item)
        item = QTableWidgetItem('{0}'.format(fee_calculated))
        self.land_fee_twidget.setItem(row, CONTRACTOR_FEE_CONTRACT, item)
        item = QTableWidgetItem('{0}'.format(10))
        self.land_fee_twidget.setItem(row, CONTRACTOR_GRACE_PERIOD, item)
        payment_frequency = self.session.query(ClPaymentFrequency).get(10)
        item = QTableWidgetItem(u'{0}'.format(payment_frequency.description))
        self.land_fee_twidget.setItem(row, CONTRACTOR_PAYMENT_FREQUENCY, item)

    def __lock_item(self, item):

        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def __add_fee_row2(self, row, contractor, fee):

        item = QTableWidgetItem(u'{0}, {1}'.format(contractor.person_ref.name, contractor.person_ref.first_name))
        item.setData(Qt.UserRole, contractor.person_ref.person_id)
        self.__lock_item(item)
        self.land_fee_twidget.setItem(row, CONTRACTOR_NAME, item)
        item = QTableWidgetItem(u'{0}'.format(contractor.person_ref.person_id))
        self.__lock_item(item)
        self.land_fee_twidget.setItem(row, CONTRACTOR_ID, item)
        item = QTableWidgetItem('{0}'.format(fee.share))
        self.__lock_item(item)
        self.land_fee_twidget.setItem(row, CONTRACTOR_SHARE, item)
        item = QTableWidgetItem('{0}'.format(fee.area))
        self.__lock_item(item)
        self.land_fee_twidget.setItem(row, CONTRACTOR_AREA, item)
        item = QTableWidgetItem('{0}'.format(fee.fee_calculated))
        self.__lock_item(item)
        self.land_fee_twidget.setItem(row, CONTRACTOR_FEE_CALCULATED, item)
        item = QTableWidgetItem('{0}'.format(fee.fee_contract))
        self.__lock_item(item)
        self.land_fee_twidget.setItem(row, CONTRACTOR_FEE_CONTRACT, item)
        item = QTableWidgetItem('{0}'.format(fee.grace_period))
        self.__lock_item(item)
        self.land_fee_twidget.setItem(row, CONTRACTOR_GRACE_PERIOD, item)
        payment_frequency = self.session.query(ClPaymentFrequency).get(fee.payment_frequency)
        item = QTableWidgetItem(u'{0}'.format(payment_frequency.description))
        self.land_fee_twidget.setItem(row, CONTRACTOR_PAYMENT_FREQUENCY, item)

    def __save_settings(self):

        # try:
        self.__save_contract()
        self.__save_fees()
        self.__save_conditions()
        return True

        # except LM2Exception, e:
        #     PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __save_contract(self):

        # self.create_savepoint()
        # try:
        if self.active_rbutton.isChecked():

            if self.contract.cancellation_date != None:
                PluginUtils.show_error(self, self.tr("Error saving contract"),
                                   self.tr("This contract cancelled. You create a new contract"))
                return

        if self.contract.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CANCELS).count() != 0:
            PluginUtils.show_error(self, self.tr("Error saving contract"),
                                   self.tr("It is not allowed to save a contract. This contract cancelled."))
            return

        if self.contract.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CREATES).count() == 0:
            PluginUtils.show_error(self, self.tr("Error saving contract"),
                                   self.tr("It is not allowed to save a contract without an assigned application."))
            return

        self.contract.status = self.__contract_status()
        if self.calculated_num_edit.text() == '':
            PluginUtils.show_error(self, self.tr("Error saving contract"),
                                   self.tr("It is not allowed to save a contract without an certificate no."))
            return
        calculated_num_edit = ''
        if self.calculated_num_edit.text():
            calculated_num_edit = self.calculated_num_edit.text()
        self.contract.certificate_no = int(calculated_num_edit)

        if self.cancellation_date_check_box.isChecked():

            self.contract.cancellation_date = self.cancelation_date.date().toString(Constants.DATABASE_DATE_FORMAT)

            if self.application_based_rbutton.isChecked():
                self.__save_cancellation_app()
            else:
                self.contract.cancellation_reason = self.other_reason_cbox.itemData(
                    self.other_reason_cbox.currentIndex())


        self.contract.contract_begin = self.contract_begin_edit.text()
        self.contract.contract_date = self.contract_date.date().toString(Constants.DATABASE_DATE_FORMAT)

        # if self.contract_end_edit.text():
        #     self.contract.contract_end = self.contract_end_edit.text()
        if self.contract_end_date.date():
            qt_end_date = PluginUtils.convert_qt_date_to_python(self.contract_end_date.date())
            self.contract.contract_end = qt_end_date
        if not self.attribute_update:
            # initial_certificate_no = int(self.calculated_num_edit.text())
            # check_certificate_no = self.__calculate_certificate_no()
            # if check_certificate_no != initial_certificate_no: # somebody else created a contract meanwhile
            #     self.calculated_num_edit.setText(str(check_certificate_no))
            # self.contract.certificate_no = int(self.calculated_num_edit.text())
            self.contract.certificate_no = int(self.calculated_num_edit.text())
            # certificate_type = self.__certificate_type()
            # certificate_settings = self.session.query(SetCertificate).get(certificate_type)
            # certificate_settings.current_no = int(self.calculated_num_edit.text())
        # if self.is_certificate == False:
        #     PluginUtils.show_error(self, self.tr("Error saving contract"),
        #                            self.tr("It is not allowed to save a contract without an certificate no wrong!!!."))
        #     return

        # except SQLAlchemyError, e:
        #     self.rollback_to_savepoint()
        #     raise LM2Exception(self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

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

    def __save_fees(self):

        # self.create_savepoint()
        # try:
        for row in range(self.land_fee_twidget.rowCount()):
            new_row = False
            contractor_id = self.land_fee_twidget.item(row, CONTRACTOR_ID).text()

            contractor = self.session.query(BsPerson).filter(BsPerson.person_id==contractor_id).one()
            fee_count = contractor.fees.filter(CtFee.contract == self.contract.contract_no).count()
            if fee_count == 0:
                new_row = True
                fee = CtFee(contract=self.contract.contract_no)
            else:
                fee = contractor.fees.filter(CtFee.contract == self.contract.contract_no).one()

            fee.share = float(self.land_fee_twidget.item(row, CONTRACTOR_SHARE).text())
            fee.area = int(self.land_fee_twidget.item(row, CONTRACTOR_AREA).text())
            fee.fee_calculated = int(self.land_fee_twidget.item(row, CONTRACTOR_FEE_CALCULATED).text())
            fee.fee_contract = int(self.land_fee_twidget.item(row, CONTRACTOR_FEE_CONTRACT).text())
            fee.grace_period = int(self.land_fee_twidget.item(row, CONTRACTOR_GRACE_PERIOD).text())
            fee.base_fee_per_m2 = float(self.base_fee_edit.text())
            fee.subsidized_area = int(self.subsidized_area_edit.text())
            fee.subsidized_fee_rate = float(self.subsidized_fee_rate_edit.text())
            payment_frequency_desc = self.land_fee_twidget.item(row, CONTRACTOR_PAYMENT_FREQUENCY).text()
            payment_frequency = self.session.query(ClPaymentFrequency). \
                filter(ClPaymentFrequency.description == payment_frequency_desc).one()
            fee.payment_frequency = payment_frequency.code

            if new_row:
                contractor.fees.append(fee)

        self.__populate_landfee_tab()

        # except SQLAlchemyError, e:
        #     self.rollback_to_savepoint()
        #     raise LM2Exception(self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __save_cancellation_app(self):

        cancel_count = self.contract.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CANCELS).count()
        self.contract.cancellation_reason = None
        if cancel_count > 0:
            # update
            cancellation_app = self.contract.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CANCELS).one()
            cancellation_app.application = self.app_number_cbox.currentText()
        else:
            # insert
            contract_app = CtContractApplicationRole()
            contract_app.application = self.app_number_cbox.currentText()
            contract_app.contract = self.contract.contract_no
            contract_app.role = Constants.APP_ROLE_CANCEL
            self.contract.application_roles.append(contract_app)

    def __save_other_reason(self):

        cancel_count = self.contract.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CANCELS).count()
        if cancel_count > 0:
            self.contract.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CANCELS).delete()

        self.contract.cancellation_reason = self.other_reason_cbox.itemData(self.other_reason_cbox.currentIndex())

    def __read_active_conditions(self):

        for row in range(self.item_model.rowCount(QModelIndex())):
            item = self.item_model.item(row)
            self.__toggle_item(item)

    def __toggle_item(self, item):

        if item.hasChildren():
            for row in range(item.rowCount()):
                child = item.child(row)
                self.__toggle_item(child)
        else:
            code = item.data(Qt.UserRole)
            if code is None:
                return
            if self.__condition_assigned(code):
                item.setCheckState(Qt.Checked)

    def __condition_assigned(self, code):

        contract = self.session.query(CtContract).get(self.contract.contract_no)
        count = contract.conditions.filter(CtContractCondition.condition == code).count()
        if count > 0:
            return True
        return False

    def __item_model(self, app_type):

        model = QStandardItemModel()
        parent_item = model.invisibleRootItem()
        item1 = None

        contract_conditions = self.session.query(ClContractCondition).order_by(ClContractCondition.code).all()

        if app_type == 5:
            right_type = 2  # possession
        elif app_type == 6:
            right_type = 1  # use
        else:
            right_type = 2

        sub_conditions = list()
        used_conditions = list()

        for condition in contract_conditions:

            filter_str = '{0}'.format(right_type)
            code = '{0}'.format(condition.code)
            filter_str += code[1:4]
            level2 = code[4:5]

            if filter_str in sub_conditions:
                continue

            if code.startswith('{0}'.format(right_type)):

                sub_conditions.append(filter_str)
                row = list()
                item = QStandardItem()
                item.setText(u'Гэрээний нөхцөл: {0}.{1}'.format(code[1:2], code[2:4].lstrip('0')))
                item.setCheckable(True)
                row.append(item)
                parent_item.appendRow(row)
                grouped_conditions1 = self.session.query(ClContractCondition). \
                    filter(ClContractCondition.code / 1000 == int(filter_str)).order_by(ClContractCondition.code).all()

                for condition1 in grouped_conditions1:

                    code1 = '{0}'.format(condition1.code)
                    description1 = condition1.description

                    if not condition1.code in used_conditions:
                        item1 = QStandardItem()
                        item1.setText(u'{0}...'.format(description1[:50]))
                        item1.setData(condition1.code, Qt.UserRole)
                        item1.setCheckable(True)
                        item.appendRow(item1)
                        level2 = code1[4:5]
                        used_conditions.append(condition1.code)

                    if level2 != '0':

                        grouped_conditions2 = self.session.query(ClContractCondition). \
                            filter(ClContractCondition.code / 100 == int(filter_str + level2)). \
                            order_by(ClContractCondition.code).all()

                        for condition2 in grouped_conditions2:

                            code2 = '{0}'.format(condition2.code)
                            description2 = condition2.description

                            if not code2.endswith('0'):

                                if condition2.code in used_conditions:
                                    continue

                                item2 = QStandardItem()
                                item2.setText(u'{0}...'.format(description2[:50]))
                                item2.setData(condition2.code, Qt.UserRole)
                                item2.setCheckable(True)
                                item1.appendRow(item2)
                                used_conditions.append(condition2.code)

        headers = [""]
        model.setHorizontalHeaderLabels(headers)

        return model

    def __save_conditions(self):

        conditions_toggled = list()
        if self.item_model is None:
            return

        for row in range(self.item_model.rowCount(QModelIndex())):
            item = self.item_model.item(row)
            self.__check_item(item, conditions_toggled)

        self.create_savepoint()

        try:
            contract = self.session.query(CtContract).get(self.contract.contract_no)
            for condition in contract.conditions:

                if not condition.condition in conditions_toggled:
                    self.session.delete(condition)

            self.session.flush()

            for code in conditions_toggled:

                count = contract.conditions.filter(CtContractCondition.condition == code).count()
                if count == 0:
                    condition = CtContractCondition()
                    condition.condition = code
                    contract.conditions.append(condition)

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __check_item(self, item, toggled_list):

        if item.checkState() != Qt.Unchecked:
            code = item.data(Qt.UserRole)
            if not code is None:
                toggled_list.append(code)
            if item.hasChildren():
                for row in range(item.rowCount()):
                    child = item.child(row)
                    self.__check_item(child, toggled_list)

    def __item_changed(self, item):

        parent = item.parent()

        if item.checkState() == Qt.Checked:
            if item.hasChildren():
                for row in range(item.rowCount()):
                    child = item.child(row)
                    child.setCheckState(Qt.Checked)
            if not parent is None:
                for row in range(parent.rowCount()):
                    child = parent.child(row)
                    if child.checkState() == Qt.Unchecked:
                        parent.setCheckState(Qt.PartiallyChecked)
                        return
                parent.setCheckState(Qt.Checked)

        elif item.checkState() == Qt.Unchecked:
            if item.hasChildren():
                for row in range(item.rowCount()):
                    child = item.child(row)
                    child.setCheckState(Qt.Unchecked)
            if not parent is None:
                for row in range(parent.rowCount()):
                    child = parent.child(row)
                    if child.checkState() == Qt.Checked or child.checkState() == Qt.PartiallyChecked:
                        parent.setCheckState(Qt.PartiallyChecked)
                        return
                parent.setCheckState(Qt.Unchecked)

        else:
            if not parent is None:
                parent.setCheckState(Qt.PartiallyChecked)

    def __show_preview(self, item):

        code = item.data(Qt.UserRole)

        if code is None:
            self.preview_text_edit.setHtml(u'<html><b>{0}</b></html>'.format(item.text()))
        else:
            condition = self.session.query(ClContractCondition).get(code)
            text_len = len(self.preview_text_edit.toPlainText())
            if text_len > 0:
                whitespace = '<html><br></html>'
            else:
                whitespace = '<html></html>'
            if item.hasChildren():
                self.preview_text_edit.setHtml(
                    self.preview_text_edit.toHtml() + whitespace + u'<html><i>{0}</i></html>'.format(
                        condition.description))
            else:
                self.preview_text_edit.setHtml(
                    self.preview_text_edit.toHtml() + whitespace + u'<html>{0}</html>'.format(condition.description))

        if item.hasChildren():
            for row in range(item.rowCount()):
                child = item.child(row)
                self.__show_preview(child)

    def __populate_conditions_tab(self):

        app_no = self.application_this_contract_based_edit.text()
        if len(app_no) == 0:
            return

        app_no_count = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).count()
        if app_no_count == 0:
            return

        app = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()

        # if app.app_type != 5 and app.app_type != 6:
        #     self.tab_widget.removeTab(self.tab_widget.indexOf(self.contract_conditions_tab))
        #     return
        # else:
        #     self.tab_widget.insertTab(self.tab_widget.count() - 5, self.contract_conditions_tab,
        #                               self.tr("Contract Conditions"))
        self.tab_widget.insertTab(self.tab_widget.count() - 5, self.contract_conditions_tab,
                                       self.tr("Contract Conditions"))
        self.item_model = self.__item_model(app.app_type)
        self.item_model.itemChanged.connect(self.__item_changed)
        self.conditions_tree.setModel(self.item_model)
        self.conditions_tree.setUniformRowHeights(True)

        for column in range(self.item_model.columnCount(QModelIndex())):
            self.conditions_tree.resizeColumnToContents(column)

        self.conditions_tree.setEditTriggers(QTableWidget.NoEditTriggers)
        self.__read_active_conditions()

    @pyqtSlot(int)
    def on_app_number_cbox_currentIndexChanged(self, current_index):

        if self.app_number_cbox.currentIndex() == -1:
            return

        try:
            app_number = self.app_number_cbox.itemText(current_index)
            if self.application_this_contract_based_edit.text():
                current_application_creates = self.contract.application_roles.filter_by(
                    role=Constants.APPLICATION_ROLE_CREATES).one()
                if current_application_creates.application_ref.app_no == app_number:
                    PluginUtils.show_error(self, self.tr("Error"),
                                           self.tr("The application that creates the contract, can't cancel it."))
                    self.app_number_cbox.setCurrentIndex(-1)
                    return

            app = self.session.query(CtApplication).filter(CtApplication.app_no == app_number).one()
            self.type_edit.setText(app.app_type_ref.description)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    @pyqtSlot(bool)
    def on_application_based_rbutton_toggled(self, checked):

        if checked:
            self.app_number_cbox.setEnabled(True)
            self.other_reason_cbox.setEnabled(False)
            try:
                if self.app_number_cbox.currentIndex() == -1:
                    return

                app_number = self.app_number_cbox.itemText(self.app_number_cbox.currentIndex())
                app = self.session.query(CtApplication).filter(CtApplication.app_no == app_number).one()
                self.type_edit.setText(app.app_type_ref.description)

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return
        else:
            self.app_number_cbox.setEnabled(False)
            self.other_reason_cbox.setEnabled(True)
            self.type_edit.setText("")

    @pyqtSlot(int)
    def on_cancellation_date_check_box_stateChanged(self, state_status):

        if state_status == Qt.Checked:
            self.cancelation_date.setEnabled(True)
            self.app_number_cbox.setEnabled(True)
            self.application_based_rbutton.setEnabled(True)
            self.other_reason_rbutton.setEnabled(True)
            self.application_type_edit.setEnabled(True)
            self.person_id_edit.setEnabled(True)
        else:
            self.cancelation_date.setEnabled(False)
            self.app_number_cbox.setEnabled(False)
            self.application_based_rbutton.setEnabled(False)
            self.other_reason_rbutton.setEnabled(False)
            self.application_type_edit.setEnabled(False)
            self.person_id_edit.setEnabled(False)

    @pyqtSlot()
    def on_accept_button_clicked(self):

        current_app_no = self.found_edit.text()

        if current_app_no == "":
            return
        try:
            application = self.session.query(CtApplication).filter_by(app_no=current_app_no).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        self.application_this_contract_based_edit.setText(application.app_no)
        self.application_type_edit.setText(application.app_type_ref.description)
        self.found_edit.setText("")

        contract_app = CtContractApplicationRole()
        contract_app.application_ref = application
        contract_app.application = application.app_no
        contract_app.contract = self.contract.contract_no
        contract_app.contract_ref = self.contract

        contract_app.role = Constants.APPLICATION_ROLE_CREATES
        self.contract.application_roles.append(contract_app)

        # try:
        self.__load_application_information()
        self.__populate_landfee_tab()
        self.__populate_archive_period_cbox()
        self.__populate_conditions_tab()
        self.__setup_applicant_cbox()
        self.__set_certificate_no()

        # except SQLAlchemyError, e:
        #     PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
        #     return

        self.accept_button.setEnabled(False)

    @pyqtSlot(int)
    def on_time_period_cbox_currentIndexChanged(self, idx):

        self.archive_land_fee_twidget.clearContents()
        self.archive_land_fee_twidget.setRowCount(0)

        if idx == -1:
            return

        # read begin date from cbox
        begin_date = self.time_period_cbox.itemData(idx, Qt.UserRole)

        base_figures = self.session.query(CtArchivedFee.base_fee_per_m2, CtArchivedFee.subsidized_area,
                                          CtArchivedFee.subsidized_fee_rate).distinct(). \
            filter(CtArchivedFee.contract == self.contract.contract_no). \
            filter(CtArchivedFee.valid_from == begin_date).one()

        self.archive_base_fee_edit.setText('{0}'.format(base_figures.base_fee_per_m2))
        self.archive_subsidized_area_edit.setText('{0}'.format(base_figures.subsidized_area))
        self.archive_subsidized_fee_rate_edit.setText('{0}'.format(base_figures.subsidized_fee_rate))

        app_no = self.application_this_contract_based_edit.text()
        if len(app_no) == 0:
            return
        app_no_count = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).count()
        if app_no_count == 0:
            return

        app = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
        contractors = app.stakeholders.filter(CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE).all()
        if app_no[6:-9] == '07' or app_no[6:-9] == '14':
            contractors = app.stakeholders.filter(CtApplicationPersonRole.role == Constants.NEW_RIGHT_HOLDER_CODE).all()
        row = 0
        for contractor in contractors:
            person = contractor.person_ref
            fee_count = person.archived_fees.filter(CtArchivedFee.contract == self.contract.contract_no). \
                filter(CtArchivedFee.valid_from == begin_date).count()
            if fee_count > 0:
                self.archive_land_fee_twidget.setRowCount(row + 1)
                fee = person.archived_fees.filter(CtArchivedFee.contract == self.contract.contract_no). \
                    filter(CtArchivedFee.valid_from == begin_date).one()
                self.__add_archived_fee_row(row, person, fee)
                row += 1

        self.archive_land_fee_twidget.resizeColumnToContents(0)
        self.archive_land_fee_twidget.resizeColumnToContents(1)
        self.archive_land_fee_twidget.resizeColumnToContents(2)
        self.archive_land_fee_twidget.resizeColumnToContents(3)
        self.archive_land_fee_twidget.resizeColumnToContents(4)
        self.archive_land_fee_twidget.resizeColumnToContents(5)
        self.archive_land_fee_twidget.horizontalHeader().setResizeMode(6, QHeaderView.Stretch)

    @pyqtSlot()
    def on_unassign_button_clicked(self):

        self.application_this_contract_based_edit.setText("")
        self.application_type_edit.setText("")
        self.id_main_edit.setText("")
        self.geo_id_edit.setText("")
        self.old_id_edit.setText("")
        self.land_use_type_edit.setText("")
        self.calculated_area_edit.setText("")
        self.documents_area_edit.setText("")
        self.aimag_edit.setText("")
        self.soum_edit.setText("")
        self.bag_edit.setText("")
        self.street_name_edit.setText("")
        self.contract_duration_edit.setText("")
        self.contract_begin_edit.setText("")
        # self.contract_end_edit.setText("")
        self.khashaa_edit.setText("")

        try:
            self.contract.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CREATES).delete()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        self.accept_button.setEnabled(True)

    @pyqtSlot()
    def on_drop_label_itemDropped(self):

        self.__copy_application_from_navigator()

    @pyqtSlot()
    def on_search_button_clicked(self):

        if not self.enter_application_num_edit.text():
            return

        try:
            app_no = self.enter_application_num_edit.text()
            count = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).count()
            if count == 1:
                application = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()

                if not self.__validate_application(application):
                    return

                self.found_edit.setText(application.app_no)
                self.enter_application_num_edit.setText("")
            else:
                PluginUtils.show_error(self, self.tr("Database Error"),
                                       self.tr("Found multiple applications for the number {0}.").format(app_no))

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    @pyqtSlot()
    def on_apply_button_clicked(self):

        if not self.__validate_settings():
            return

        if not self.__save_settings():
            return
        current_user = DatabaseUtils.current_user()
        current_employee = self.session.query(SetRole) \
            .filter(SetRole.user_name == current_user.user_name) \
            .filter(SetRole.is_active == True).one()

        app_status9_count = self.session.query(CtApplicationStatus)\
            .filter(CtApplicationStatus.application == self.application_this_contract_based_edit.text())\
            .filter(CtApplicationStatus.status == 9).count()
        if self.active_rbutton.isChecked() and app_status9_count == 0:
            new_status = CtApplicationStatus()
            new_status.application = self.application_this_contract_based_edit.text()
            new_status.next_officer_in_charge = current_employee.user_name_real
            new_status.officer_in_charge = current_employee.user_name_real
            new_status.status = 9
            new_status.status_date = self.contract.contract_date
            self.session.add(new_status)

        self.commit()
        self.__start_fade_out_timer()
        self.attribute_update = True

    def reject(self):

        self.rollback()
        QDialog.reject(self)

    def __contract_possess(self):

        aimag_code = self.application_this_contract_based_edit.text()[:3]
        try:
            aimag = self.session.query(AuLevel1).filter(AuLevel1.code == aimag_code).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"),
                               self.tr("aCould not execute: {0}").format(e.message))
        soum_code = self.application_this_contract_based_edit.text()[:5]
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == soum_code).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"),
                               self.tr("aCould not execute: {0}").format(e.message))

        app_no = self.application_this_contract_based_edit.text()
        # try:
        pp = ""
        decision_date = ''
        decision_level = ''
        decision_no = ''
        app_dec = self.session.query(CtDecisionApplication).filter(
            CtDecisionApplication.application == app_no).all()
        for p in app_dec:
            pp = p.decision
        decision_c = self.session.query(CtDecision).filter(CtDecision.decision_no == pp).count()
        if decision_c != 0:
            decision = self.session.query(CtDecision).filter(CtDecision.decision_no == pp).one()
            decision_no = decision.decision_no[6:-5]
            decision_date = str(decision.decision_date)
            decision_level = decision.decision_level

        # except SQLAlchemyError, e:
        #     raise LM2Exception(self.tr("Database Query Error"),
        #                        self.tr("aCould not execute: {0}").format(e.message))
        app_no = self.application_this_contract_based_edit.text()
        try:
            app_status = self.session.query(CtApplicationStatus).filter(
                CtApplicationStatus.application == app_no).all()
            for p in app_status:
                if p.status == 9:
                    officer = self.session.query(SetRole).filter(SetRole.user_name_real == p.officer_in_charge).one()
                else:
                    officer = self.session.query(SetRole).filter(SetRole.user_name_real == p.officer_in_charge).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"),
                               self.tr("aCould not execute: {0}").format(e.message))

        app_no = self.application_this_contract_based_edit.text()

        try:
            app_person = self.session.query(CtApplicationPersonRole).filter(
                CtApplicationPersonRole.application == app_no).all()
            app_person_new_count = self.session.query(CtApplicationPersonRole). \
                filter(CtApplicationPersonRole.application == app_no). \
                filter(CtApplicationPersonRole.role == 70).count()
            if app_person_new_count > 0:
                app_person = self.session.query(CtApplicationPersonRole). \
                    filter(CtApplicationPersonRole.application == app_no). \
                    filter(CtApplicationPersonRole.role == 70).all()

            for p in app_person:
                if p.main_applicant == True:
                    person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()

                    bank_count = self.session.query(ClBank).filter(ClBank.code == person.bank).count()
                    person_bank_name = " "
                    if bank_count != 0:
                        bank = self.session.query(ClBank).filter(ClBank.code == person.bank).one()
                        person_bank_name = bank.description

                    aimag_count = self.session.query(AuLevel1).filter(
                        AuLevel1.code == person.address_au_level1).count()
                    aimag_name = " "
                    if aimag_count != 0:
                        aimag = self.session.query(AuLevel1).filter(AuLevel1.code == person.address_au_level1).one()
                        aimag_name = aimag.name

                    soum_count = self.session.query(AuLevel2).filter(
                        AuLevel2.code == person.address_au_level2).count()
                    soum_name = " "
                    if soum_count != 0:
                        soum_person = self.session.query(AuLevel2).filter(AuLevel2.code == person.address_au_level2).one()
                        soum_name = soum_person.name

                    bag_count = self.session.query(AuLevel2).filter(
                        AuLevel3.code == person.address_au_level3).count()
                    bag_name = " "
                    if bag_count != 0:
                        bag = self.session.query(AuLevel3).filter(AuLevel3.code == person.address_au_level3).one()
                        bag_name = bag.name

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"),
                               self.tr("aCould not execute: {0}").format(e.message))

        base_fee = 0
        payment = 0
        contract_no = self.contract_num_edit.text()

        try:
            fee = self.session.query(CtFee).filter(CtFee.contract == contract_no).all()

            for fee in fee:
                payment = payment + fee.fee_contract
                base_fee = fee.base_fee_per_m2

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"),
                               self.tr("aCould not execute: {0}").format(e.message))

        report_settings = self.__admin_settings("set_report_parameter")
        if len(report_settings) == 0:
            return

        local_name = " "
        address_street_name = ""
        address_khaskhaa = ""
        address_building_no = ""
        address_entrance_no = ""
        address_apartment_no = ""
        if person.address_street_name != None:
            address_street_name = person.address_street_name + u" гудамж, "
        if person.address_khaskhaa != None:
            address_khaskhaa = person.address_khaskhaa
        if person.address_building_no != None:
            address_building_no = person.address_building_no + u" байр, "
        if person.address_entrance_no != None:
            address_entrance_no = person.address_entrance_no + ', '
        if person.address_apartment_no != None:
            address_apartment_no = person.address_apartment_no
        if person.address_street_name != None or person.address_khaskhaa != None:
            if person.address_town_or_local_name != None:
                local_name = person.address_town_or_local_name + ', '
            person_address = aimag_name + ", " + soum_name + ", " + bag_name + ", " + local_name + address_street_name + address_khaskhaa
        elif person.address_building_no != None or person.address_entrance_no != None:
            if person.address_town_or_local_name != None:
                local_name = person.address_town_or_local_name + ', '
            person_address = aimag_name + ", " + soum_name + ", " + bag_name + ", " + local_name + address_building_no + address_entrance_no + address_apartment_no
        else:
            if person.address_town_or_local_name != None:
                local_name = person.address_town_or_local_name
            person_address = aimag_name + ", " + soum_name + ", " + bag_name + ", " + local_name
        app_type = self.application_type_edit.text()[:2]
        path = FileUtils.map_file_path()
        default_path = r'D:/TM_LM2/contracts'
        if app_type == '22':
            tpl = DocxTemplate(path+'geree_THGGA_DX.docx')
        else:
            if person.type == 10 or person.type == 20 or person.type == 30 or person.type == 40:
                tpl = DocxTemplate(path+'geree_ezemshix_DX.docx')
            elif person.type == 50 or person.type == 60:
                tpl = DocxTemplate(path+'geree_ashigluulah_DX.docx')

        aimag_name = aimag.name
        soum_name = soum.name
        contract_no = self.contract_num_edit.text()
        cerificate_no = self.calculated_num_edit.text()
        contract_date = self.contract_date.text()
        contract_date_year = contract_date[0:-6]
        contract_date_month = contract_date[5:-3]
        contract_date_day = contract_date[-2:]
        dec_year = decision_date[:4]
        dec_month = decision_date[5:-3]
        dec_day = decision_date[-2:]
        o_firstname = officer.first_name
        o_surname = officer.surname
        o_position = officer.position_ref.description
        company_name = ''
        person_surname = ''
        person_firstname = ''
        contact_position = ''
        if person.type == 10 or person.type == 20 or person.type == 50:
            person_surname = person.name
            person_firstname = person.first_name
        elif person.type == 30 or person.type == 40 or person.type == 60:
            company_name = person.name
            contact_position = person.contact_position
            person_surname = person.contact_surname
            person_firstname = person.contact_first_name
        area_m2 = self.calculated_area_edit.text()
        if float(area_m2) > 10000:
            area_m2 = str(float(area_m2) / 10000) + u" га"
        else:
            area_m2 = area_m2 + u" м2"

        landuse = self.land_use_type_edit.text()
        base_fee = str(base_fee)

        quarterly1_fee = str(payment / 4)
        quarterly2_fee = str(payment / 4)
        quarterly3_fee = str(payment / 4)
        quarterly4_fee = str(payment / 4)
        payment = str(payment)
        bank_name = report_settings[Constants.REPORT_BANK]
        account_no = report_settings[Constants.REPORT_BANK_ACCOUNT]
        office_address = report_settings[Constants.REPORT_ADDRESS]

        aimag_name = self.aimag_edit.text()
        soum_name = self.soum_edit.text()
        bag_name = self.bag_edit.text()
        street_name = self.street_name_edit.text()
        khashaa_name = self.khashaa_edit.text()

        fee_area = self.subsidized_area_edit.text()
        fee_rate = self.subsidized_fee_rate_edit.text()


        person_bank_name = person_bank_name
        person_account = person.bank_account_no
        person_phone = person.phone
        person_email = person.email_address
        office_phone = report_settings[Constants.REPORT_PHONE]
        parcel_id = self.id_main_edit.text()[1:-9] + self.id_main_edit.text()[4:]
        sum_name_dec = ''
        sum_officer = ''

        if decision_level == 20 or decision_level == 40:
            sum_name_dec = soum.name + u' дүүрэг /сум/-ийн '
            sum_officer = soum.name + u' дүүрэг /сум/-ийн Газрын албаны '
        elif decision_level == 10 or decision_level == 30:
            sum_officer = u'ГХБХБГазрын газрын асуудал эрхэлсэн албан тушаалтан '
        if contact_position is None:
            contact_position = ''
        if company_name is None:
            company_name = ''
        if person_surname is None:
            person_surname = ''
        if person_firstname is None:
            person_firstname = ''

        if person.type == 10 or person.type == 20 or person.type == 50:
            company_name = person_surname + u' овогтой ' + person_firstname
        elif person.type == 30 or person.type == 40 or person.type == 60:
            company_name = company_name + u'-н ' + contact_position + u' ' + person_surname + u' овогтой ' + person_firstname

        if self.is_sign_checkbox.isChecked():
            darga_signature = self.print_officer_cbox.currentText() + u'/.............................../'
            darga_position = u'Дарга '
        else:
            darga_signature = ''
            darga_position = ''

        duration_year = self.contract_duration_edit.text()
        context = {
            'aimag_name': aimag_name,
            'contract_no': contract_no,
            'cert_no': cerificate_no,
            'c_year': time.strftime("%Y"),
            'c_month': time.strftime("%m"),
            'c_day': time.strftime("%d"),
            'sum_name': soum_name,
            'sum_name_dec': sum_name_dec,
            'sum_officer': sum_officer,
            'dec_year': dec_year,
            'dec_month': dec_month,
            'dec_day': dec_day,
            'dec_no': decision_no,
            'o_firstname': o_firstname,
            'o_surname': o_surname,
            'o_position': o_position,
            'company_name': company_name,
            'contact_position': contact_position,
            'person_surname': person_surname,
            'person_firstname': person_firstname,
            'area_m2': area_m2,
            'landuse': landuse,
            'base_fee': base_fee,
            'payment': payment,
            'quarterly1_fee': quarterly1_fee,
            'quarterly2_fee': quarterly2_fee,
            'quarterly3_fee': quarterly3_fee,
            'quarterly4_fee': quarterly4_fee,
            'bank_name': bank_name,
            'account_no': account_no,
            'office_address': office_address,
            'aimag': aimag_name,
            'soum': soum_name,
            'bag': bag_name,
            'street': street_name,
            'khashaa': khashaa_name,
            'fee_area': fee_area,
            'fee_rate': fee_rate,
            'person_address': person_address,
            'person_bank_name': person_bank_name,
            'person_account': person_account,
            'person_phone': person_phone,
            'person_email': person_email,
            'person_id': person.person_id,
            'office_phone': office_phone,
            'parcel_id': parcel_id,
            'duration_year': duration_year,
            'darga_position': darga_position,
            'darga_signature': darga_signature
        }

        tpl.render(context)

        try:
            tpl.save(default_path + "/" + contract_no[:-6] + '-' + contract_no[-5:] + ".docx")
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(default_path + "/" + contract_no[:-6] + '-' + contract_no[-5:] + ".docx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"),
                                   self.tr("This file is already opened. Please close re-run"))

    @pyqtSlot()
    def on_print_contract_button_clicked(self):

        app_no = self.application_this_contract_based_edit.text()
        app_person = self.session.query(CtApplicationPersonRole).filter(
            CtApplicationPersonRole.application == app_no).all()
        app_person_new_count = self.session.query(CtApplicationPersonRole). \
            filter(CtApplicationPersonRole.application == app_no). \
            filter(CtApplicationPersonRole.role == 70).count()
        if app_person_new_count > 0:
            app_person = self.session.query(CtApplicationPersonRole). \
                filter(CtApplicationPersonRole.application == app_no). \
                filter(CtApplicationPersonRole.role == 70).all()

        for p in app_person:
            if p.main_applicant == True:
                person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()

        if not self.pdf_checkbox.isChecked():
            self.__contract_possess()
        else:
            contract_no = self.contract_num_edit.text()
            contract_count = self.session.query(CtContract).filter(CtContract.contract_no == contract_no).count()
            if contract_count == 0:
                PluginUtils.show_error(self, self.tr("contract error"), self.tr("not save"))
                return


            ok = 0
            try:
                app_status = self.session.query(CtApplicationStatus).filter(CtApplicationStatus.application == app_no).all()
                for p in app_status:
                    if p.status == 9:
                        ok = 1
                        officer = self.session.query(SetRole).filter(SetRole.user_name_real == p.officer_in_charge).one()
            except SQLAlchemyError, e:
                raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
            if ok == 0:
                PluginUtils.show_error(self, self.tr("contract error"), self.tr("Application status must be 9 !!!"))
                return
            header = "no text"

            path = FileUtils.map_file_path()
            if person.type == 10 or person.type == 20 or person.type == 30 or person.type == 40:
                template = path + "contract_possess.qpt"
            else:
                template = path + "contract_use.qpt"

            templateDOM = QDomDocument()
            templateDOM.setContent(QFile(template), False)

            map_canvas = QgsMapCanvas()

            map_composition = QgsComposition(map_canvas.mapRenderer())
            map_composition.loadFromTemplate(templateDOM)

            map_composition.setPrintResolution(300)

            default_path = r'D:/TM_LM2/contracts'
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
            printer.setOutputFileName(path+"contract_poss.pdf")
            printer.setPaperSize(QSizeF(map_composition.paperWidth(), map_composition.paperHeight()), QPrinter.Millimeter)
            printer.setFullPage(True)
            printer.setColorMode(QPrinter.Color)
            printer.setResolution(map_composition.printResolution())

            pdfPainter = QPainter(printer)
            paperRectMM = printer.pageRect(QPrinter.Millimeter)
            paperRectPixel = printer.pageRect(QPrinter.DevicePixel)
            map_composition.render(pdfPainter, paperRectPixel, paperRectMM)
            pdfPainter.end()

            contract_no = self.contract_num_edit.text()
            fee_count = self.session.query(CtFee).filter(CtFee.contract == contract_no).count()
            if fee_count == 0:
                PluginUtils.show_message(self,self.tr("Not sava contract"),self.tr("First click save button and then print contract"))
                return
            self.__add_aimag_name(map_composition)
            self.__add_soum_name(map_composition)
            self.__add_contract_no(map_composition)
            self.__add_decision(map_composition)
            self.__add_parcel(map_composition)
            self.__add_fee(map_composition)
            self.__add_contract_condition(map_composition)
            self.__add_person_signature(map_composition)
            # self.__add_app_status_date(map_composition)
            self.__add_person_name(map_composition)
            # self.__add_duration(map_composition)
            self.__add_officer(map_composition)
            self.__officer_info(map_composition)
            map_composition.exportAsPDF(path + "contract_poss.pdf")
            map_composition.exportAsPDF(default_path + "/"+contract_no[:-6]+'-'+contract_no[-5:]+".pdf")
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+contract_no[:-6]+'-'+contract_no[-5:]+".pdf"))

    def __admin_settings(self, table_name):

        session = SessionHandler().session_instance()
        lookup = {}
        l2_code = DatabaseUtils.working_l2_code()
        try:
            sql = "SELECT * FROM " + "s" + l2_code + ".{0};".format(table_name)
            result = session.execute(sql).fetchall()
            for row in result:
                lookup[row[0]] = row[1]

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)

        return lookup

    def __add_duration(self,map_composition):

        duration_year = self.contract_duration_edit.text()

        item = map_composition.getComposerItemById("duration_year")
        item.setText(duration_year)
        item.adjustSizeToText()

    def __add_officer_cert(self,map_composition):

        app_no = self.application_this_contract_based_edit.text()
        try:
            app_status = self.session.query(CtApplicationStatus).filter(CtApplicationStatus.application == app_no).all()
            for p in app_status:
                if p.status == 9:
                    officer = self.session.query(SetRole).filter(SetRole.user_name_real == p.officer_in_charge).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        restrictions = DatabaseUtils.working_l2_code()
        # if restrictions[3:] == '01':
        officer_name = self.print_officer_cbox.currentText()

        item = map_composition.getComposerItemById("officer_name")
        item.setText(officer_name)
        item.adjustSizeToText()

    def __add_cert_officer_name(self):

        app_no = self.application_this_contract_based_edit.text()
        try:
            app_status = self.session.query(CtApplicationStatus).filter(CtApplicationStatus.application == app_no).all()
            for p in app_status:
                if p.status == 9:
                    officer = self.session.query(SetRole).filter(SetRole.user_name_real == p.officer_in_charge).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        restrictions = DatabaseUtils.working_l2_code()
        # if restrictions[3:] == '01':
        officer_name = self.print_officer_cbox.currentText()

        return officer_name

    def __add_officer(self,map_composition):

        report_settings = self.__admin_settings("set_report_parameter")
        if len(report_settings) == 0:
            return

        item = map_composition.getComposerItemById("officer_address")
        item.setText(report_settings[Constants.REPORT_ADDRESS])
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("officer_phone")
        item.setText(report_settings[Constants.REPORT_PHONE])
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("bank_and_account")
        bank_and_account = report_settings[Constants.REPORT_BANK] +u" банкны "+ report_settings[Constants.REPORT_BANK_ACCOUNT]
        item.setText(bank_and_account)
        item.adjustSizeToText()

        app_no = self.application_this_contract_based_edit.text()
        try:
            app_status = self.session.query(CtApplicationStatus).filter(CtApplicationStatus.application == app_no).all()
            for p in app_status:
                if p.status == 9:
                    officer = self.session.query(SetRole).filter(SetRole.user_name_real == p.officer_in_charge).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        item = map_composition.getComposerItemById("officer_name")
        item.setText(officer.first_name+ u",")
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("officer_surname")
        item.setText(officer.surname)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("contract_officer_surname")
        item.setText(officer.surname)
        item.adjustSizeToText()

    def __add_aimag_name_cert(self,map_composition):

        aimag_code = self.application_this_contract_based_edit.text()[:3]
        try:
            aimag = self.session.query(AuLevel1).filter(AuLevel1.code == aimag_code).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        item = map_composition.getComposerItemById("aimag_name")
        item.setText(aimag.name)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("officer_aimag")
        item.setText(aimag.name)
        item.adjustSizeToText()

    def __add_cert_aimag(self):

        aimag_code = self.application_this_contract_based_edit.text()[:3]
        try:
            aimag = self.session.query(AuLevel1).filter(AuLevel1.code == aimag_code).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        return aimag

    def __add_soum_name_cert(self,map_composition):

        soum_code = self.application_this_contract_based_edit.text()[:5]
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == soum_code).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        item = map_composition.getComposerItemById("soum_name")
        item.setText(soum.name)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("officer_soum")
        item.setText(soum.name)
        item.adjustSizeToText()

    def __add_cert_soum(self):

        soum_code = self.application_this_contract_based_edit.text()[:5]
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == soum_code).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        return soum

    def __officer_info(self, map_composition):

        aimag_code = self.application_this_contract_based_edit.text()[:3]
        try:
            aimag = self.session.query(AuLevel1).filter(AuLevel1.code == aimag_code).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        soum_code = self.application_this_contract_based_edit.text()[:5]
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == soum_code).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        aimag_soum = aimag.name + u' аймаг/хот-ийн ' + soum.name + u' сум/дүүрэг-ийн'
        item = map_composition.getComposerItemById("officer_aimag")
        item.setText(aimag_soum)
        item.adjustSizeToText()

        app_no = self.application_this_contract_based_edit.text()
        try:
            app_status = self.session.query(CtApplicationStatus).filter(CtApplicationStatus.application == app_no).all()
            for p in app_status:
                if p.status == 9:
                    officer = self.session.query(SetRole).filter(SetRole.user_name_real == p.officer_in_charge).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        officer_full_name = officer.surname + u' овогтой ' + officer.first_name
        item = map_composition.getComposerItemById("contract_officer_surname")
        item.setText(officer_full_name)
        item.adjustSizeToText()

        if self.is_sign_checkbox.isChecked():
            officer_head_count = self.session.query(SetRole).filter(SetRole.position == 9).count()
            if officer_head_count == 1:
                officer_head = self.session.query(SetRole).filter(SetRole.position == 9).one()
                officer_full_name = officer_head.surname[:1] + u'.' + officer_head.first_name +u'   ......................'
                item = map_composition.getComposerItemById("head_name")
                item.setText(officer_full_name)
                item.adjustSizeToText()

                officer_position = self.session.query(ClPositionType).filter(ClPositionType.code == officer_head.position).one()
                item = map_composition.getComposerItemById("head_position")
                item.setText(officer_position.description)
                item.adjustSizeToText()

    def __add_aimag_name(self,map_composition):

        aimag_code = self.application_this_contract_based_edit.text()[:3]
        try:
            aimag = self.session.query(AuLevel1).filter(AuLevel1.code == aimag_code).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        item = map_composition.getComposerItemById("aimag_name")
        item.setText(aimag.name)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("aimag_name1")
        item.setText(aimag.name)
        item.adjustSizeToText()

    def __add_soum_name(self,map_composition):

        soum_code = self.application_this_contract_based_edit.text()[:5]
        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == soum_code).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        item = map_composition.getComposerItemById("soum_name")
        item.setText(soum.name)
        item.adjustSizeToText()

        app_no = self.application_this_contract_based_edit.text()
        try:
            pp = ""
            app_dec = self.session.query(CtDecisionApplication).filter(CtDecisionApplication.application == app_no).all()
            for p in app_dec:
                pp = p.decision
            decision = self.session.query(CtDecision).filter(CtDecision.decision_no == pp).one()
            decision_level = decision.decision_level
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        if decision_level != 10 and decision_level != 30:
            item = map_composition.getComposerItemById("soum_name1")
            item.setText(soum.name)
            item.adjustSizeToText()

        item = map_composition.getComposerItemById("soum_name2")
        item.setText(soum.name)
        item.adjustSizeToText()

    def __add_decision_cert(self,map_composition):

        app_no = self.application_this_contract_based_edit.text()
        try:
            pp = ""
            app_dec = self.session.query(CtDecisionApplication).filter(CtDecisionApplication.application == app_no).all()
            for p in app_dec:
                pp = p.decision
            decision = self.session.query(CtDecision).filter(CtDecision.decision_no == pp).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        item = map_composition.getComposerItemById("decision")
        decision_date = str(decision.decision_date)
        decision_date = " "+decision_date[1:-6]+u"           " + decision_date[5:-3]+u"            " + decision_date[-2:] + u"               " + decision.decision_no[6:-5]
        item.setText(decision_date)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("approved_duration")
        app_duration = self.contract_duration_edit.text()
        item.setText(app_duration)
        item.adjustSizeToText()

        print_date = QDate().currentDate()
        year = print_date.year()
        month = print_date.month()
        day = print_date.day()

        contract_date = str(year)[-3:] + "           " + str(month) +"              " + str(day)
        item = map_composition.getComposerItemById("contract_date")
        item.setText(contract_date)
        item.adjustSizeToText()

    def __add__cert_decision(self):

        app_no = self.application_this_contract_based_edit.text()
        try:
            pp = ""
            app_dec = self.session.query(CtDecisionApplication).filter(CtDecisionApplication.application == app_no).all()
            for p in app_dec:
                pp = p.decision
            decision = self.session.query(CtDecision).filter(CtDecision.decision_no == pp).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        decision_date = str(decision.decision_date)
        decision_date = " "+decision_date[1:-6]+u"           " + decision_date[5:-3]+u"            " + decision_date[-2:] + u"               " + decision.decision_no[6:-5]

        app_duration = self.contract_duration_edit.text()

        print_date = QDate().currentDate()
        year = print_date.year()
        month = print_date.month()
        day = print_date.day()

        contract_date = str(year)[-3:] + "           " + str(month) +"              " + str(day)
        decision_value = [decision.decision_no, decision_date, app_duration, contract_date]
        return decision_value

    def __add_decision(self,map_composition):

        app_no = self.application_this_contract_based_edit.text()
        try:
            pp = ""
            app_dec = self.session.query(CtDecisionApplication).filter(CtDecisionApplication.application == app_no).all()
            for p in app_dec:
                pp = p.decision
            decision = self.session.query(CtDecision).filter(CtDecision.decision_no == pp).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        item = map_composition.getComposerItemById("decision_no")
        item.setText(decision.decision_no[6:-5])
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("decision_date")
        decision_date = str(decision.decision_date)
        decision_date = decision_date[:4]+u" оны " + decision_date[5:-3]+u" -р сарын " + decision_date[-2:] + u" -ны өдрийн "
        item.setText(decision_date)
        item.adjustSizeToText()

    def __add_person_signature(self,map_composition):

        contact_surname = ''
        contact_first_name = ''
        app_no = self.application_this_contract_based_edit.text()
        person_signature = map_composition.getComposerItemById("person_signature")
        try:
            app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app_no).all()
            if app_no[6:-9] == '07' or app_no[6:-9] == '14':
                app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app_no)\
                                    .filter(CtApplicationPersonRole.role == 70).all()
            for p in app_person:
                person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()
                if person.contact_surname != None:
                    contact_surname = person.contact_surname
                if person.contact_first_name != None:
                    contact_first_name = person.contact_first_name
                if person.type == 10 or person.type == 20 or person.type == 50:
                    name = "___________________"+person.name[:1]+"."+person.first_name + " /"+ person.person_id +"/"
                    person_signature = self.__copy_label(person_signature,name,map_composition)
                elif person.type == 30 or person.type == 40 or person.type == 60:
                    name = "___________________"+ contact_surname[:1]+"."+ contact_first_name + " /"+ person.person_id +"/"
                    person_signature = self.__copy_label(person_signature,name,map_composition)

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

    def __add_person_name_cert(self,map_composition):

        app_no = self.application_this_contract_based_edit.text()
        try:
            app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app_no).all()
            app_person_new_count = self.session.query(CtApplicationPersonRole).\
                filter(CtApplicationPersonRole.application == app_no).\
                filter(CtApplicationPersonRole.role == 70).count()
            if app_person_new_count > 0:
                app_person = self.session.query(CtApplicationPersonRole).\
                    filter(CtApplicationPersonRole.application == app_no).\
                    filter(CtApplicationPersonRole.role == 70).all()

            for p in app_person:
                if p.main_applicant == True:
                    person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()

                    aimag_count = self.session.query(AuLevel1).filter(AuLevel1.code == person.address_au_level1).count()
                    aimag_name = " "
                    if aimag_count != 0:
                        aimag = self.session.query(AuLevel1).filter(AuLevel1.code == person.address_au_level1).one()
                        aimag_name = aimag.name

                    soum_count = self.session.query(AuLevel2).filter(AuLevel2.code == person.address_au_level2).count()
                    soum_name = " "
                    if soum_count != 0:
                        soum = self.session.query(AuLevel2).filter(AuLevel2.code == person.address_au_level2).one()
                        soum_name = soum.name

                    bag_count = self.session.query(AuLevel2).filter(AuLevel3.code == person.address_au_level3).count()
                    bag_name = " "
                    if bag_count != 0:
                        bag = self.session.query(AuLevel3).filter(AuLevel3.code == person.address_au_level3).one()
                        bag_name = bag.name

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        if person.type == 10 or person.type == 20:
            item = map_composition.getComposerItemById("family_name")
            name = person.middle_name
            item.setText(name)
            item.adjustSizeToText()

            item = map_composition.getComposerItemById("surname")
            name = person.name
            item.setText(name)
            item.adjustSizeToText()

            item = map_composition.getComposerItemById("first_name")
            name = person.first_name
            item.setText(name)
            item.adjustSizeToText()

            item = map_composition.getComposerItemById("person_id")
            item.setText(person.person_id)
            item.adjustSizeToText()
        elif person.type == 30 or person.type == 40:
            state_reg = " "
            if person.state_registration_no != None:
                state_reg = person.state_registration_no
            person_id = state_reg +", "+person.person_id
            item = map_composition.getComposerItemById("person_id")
            if item:
                item.setText(person_id)
                item.adjustSizeToText()


            item = map_composition.getComposerItemById("company_name")
            name = person.name
            item.setText(name)
            item.adjustSizeToText()
        elif person.type == 50:
            state_reg = " "
            if person.state_registration_no != None:
                state_reg = person.state_registration_no
            person_id = state_reg +", "+person.person_id
            item = map_composition.getComposerItemById("person_id")
            item.setText(person_id)
            item.adjustSizeToText()

            item = map_composition.getComposerItemById("company_name")
            name = person.name +", "+ person.first_name
            item.setText(name)
            item.adjustSizeToText()
        elif person.type == 60:
            state_reg = " "
            if person.state_registration_no != None:
                state_reg = person.state_registration_no
            person_id = state_reg +", "+person.person_id
            item = map_composition.getComposerItemById("company_id")
            item.setText(person_id)
            item.adjustSizeToText()

            item = map_composition.getComposerItemById("company_name")
            name = person.name
            item.setText(name)
            item.adjustSizeToText()

        item = map_composition.getComposerItemById("person_address")
        local_name = ""
        address_street_name = ""
        address_khaskhaa = ""
        address_building_no = ""
        address_entrance_no = ""
        address_apartment_no = ""
        if person.address_street_name != None:
            address_street_name = person.address_street_name + u" гудамж, "
        if person.address_khaskhaa != None:
            address_khaskhaa = person.address_khaskhaa
        if person.address_building_no != None:
            address_building_no = person.address_building_no + u' байр, '
        if person.address_entrance_no != None:
            address_entrance_no = person.address_entrance_no + ', '
        if person.address_apartment_no != None:
            address_apartment_no = person.address_apartment_no
        if person.address_street_name != None or person.address_khaskhaa != None:
            if person.address_town_or_local_name != None:
                local_name  = person.address_town_or_local_name + ', '
            person_address = aimag_name +", "+ soum_name +", " +bag_name+", "+local_name + address_street_name + address_khaskhaa
        elif person.address_building_no != None or person.address_entrance_no != None:
            if person.address_town_or_local_name != None:
                local_name  = person.address_town_or_local_name + ', '
            person_address = aimag_name +", "+ soum_name +", " +bag_name+", "+local_name + address_building_no + address_entrance_no + address_apartment_no
        else:
            if person.address_town_or_local_name != None:
                local_name  = person.address_town_or_local_name
            person_address = aimag_name +", "+ soum_name +", " +bag_name+", "+local_name
        item.setText(self.__wrap(person_address,100))

    def __add_cert_person(self):

        app_no = self.application_this_contract_based_edit.text()
        try:
            app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app_no).all()
            app_person_new_count = self.session.query(CtApplicationPersonRole).\
                filter(CtApplicationPersonRole.application == app_no).\
                filter(CtApplicationPersonRole.role == 70).count()
            if app_person_new_count > 0:
                app_person = self.session.query(CtApplicationPersonRole).\
                    filter(CtApplicationPersonRole.application == app_no).\
                    filter(CtApplicationPersonRole.role == 70).all()

            for p in app_person:
                if p.main_applicant == True:
                    person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()

                    aimag_count = self.session.query(AuLevel1).filter(AuLevel1.code == person.address_au_level1).count()
                    aimag_name = " "
                    if aimag_count != 0:
                        aimag = self.session.query(AuLevel1).filter(AuLevel1.code == person.address_au_level1).one()
                        aimag_name = aimag.name

                    soum_count = self.session.query(AuLevel2).filter(AuLevel2.code == person.address_au_level2).count()
                    soum_name = " "
                    if soum_count != 0:
                        soum = self.session.query(AuLevel2).filter(AuLevel2.code == person.address_au_level2).one()
                        soum_name = soum.name

                    bag_count = self.session.query(AuLevel2).filter(AuLevel3.code == person.address_au_level3).count()
                    bag_name = " "
                    if bag_count != 0:
                        bag = self.session.query(AuLevel3).filter(AuLevel3.code == person.address_au_level3).one()
                        bag_name = bag.name

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        company_name = ''
        company_id = ''
        family_name = ''
        surname = ''
        first_name = ''

        if person.type == 10 or person.type == 20:
            family_name = person.middle_name
            surname = person.name
            first_name = person.first_name
        elif person.type == 30 or person.type == 40:
            state_reg = " "
            if person.state_registration_no != None:
                state_reg = person.state_registration_no
            person_id = state_reg +", "+person.person_id
            company_name = person.name
        elif person.type == 50:
            state_reg = " "
            if person.state_registration_no != None:
                state_reg = person.state_registration_no
            person_id = state_reg +", "+person.person_id
            company_name = person.name +", "+ person.first_name
        elif person.type == 60:
            state_reg = " "
            if person.state_registration_no != None:
                state_reg = person.state_registration_no
                company_id = state_reg +", "+person.person_id
            company_name = person.name

        local_name = ""
        address_street_name = ""
        address_khaskhaa = ""
        address_building_no = ""
        address_entrance_no = ""
        address_apartment_no = ""
        if person.address_street_name != None:
            address_street_name = person.address_street_name + u" гудамж, "
        if person.address_khaskhaa != None:
            address_khaskhaa = person.address_khaskhaa
        if person.address_building_no != None:
            address_building_no = person.address_building_no + u' байр, '
        if person.address_entrance_no != None:
            address_entrance_no = person.address_entrance_no + ', '
        if person.address_apartment_no != None:
            address_apartment_no = person.address_apartment_no
        if person.address_street_name != None or person.address_khaskhaa != None:
            if person.address_town_or_local_name != None:
                local_name  = person.address_town_or_local_name + ', '
            person_address = aimag_name +", "+ soum_name +", " +bag_name+", "+local_name + address_street_name + address_khaskhaa
        elif person.address_building_no != None or person.address_entrance_no != None:
            if person.address_town_or_local_name != None:
                local_name  = person.address_town_or_local_name + ', '
            person_address = aimag_name +", "+ soum_name +", " +bag_name+", "+local_name + address_building_no + address_entrance_no + address_apartment_no
        else:
            if person.address_town_or_local_name != None:
                local_name  = person.address_town_or_local_name
            person_address = aimag_name +", "+ soum_name +", " +bag_name+", "+local_name

        value = [person.person_id, family_name, surname, first_name, company_name, company_id, person_address]
        return value

    def __add_person_name(self,map_composition):

        app_no = self.application_this_contract_based_edit.text()

        try:
            application = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
            app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app_no).all()
            app_person_new_count = self.session.query(CtApplicationPersonRole).\
                filter(CtApplicationPersonRole.application == app_no).\
                filter(CtApplicationPersonRole.role == 70).count()
            if app_person_new_count > 0:
                app_person = self.session.query(CtApplicationPersonRole).\
                filter(CtApplicationPersonRole.application == app_no).\
                filter(CtApplicationPersonRole.role == 70).all()

            for p in app_person:
                if p.main_applicant == True:
                    person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()

                    bank_count = self.session.query(ClBank).filter(ClBank.code == person.bank).count()
                    bank_name = " "
                    if bank_count != 0:
                        bank = self.session.query(ClBank).filter(ClBank.code == person.bank).one()
                        bank_name = bank.description

                    aimag_count = self.session.query(AuLevel1).filter(AuLevel1.code == person.address_au_level1).count()
                    aimag_name = " "
                    if aimag_count != 0:
                        aimag = self.session.query(AuLevel1).filter(AuLevel1.code == person.address_au_level1).one()
                        aimag_name = aimag.name

                    soum_count = self.session.query(AuLevel2).filter(AuLevel2.code == person.address_au_level2).count()
                    soum_name = " "
                    if soum_count != 0:
                        soum = self.session.query(AuLevel2).filter(AuLevel2.code == person.address_au_level2).one()
                        soum_name = soum.name

                    bag_count = self.session.query(AuLevel2).filter(AuLevel3.code == person.address_au_level3).count()
                    bag_name = " "
                    if bag_count != 0:
                        bag = self.session.query(AuLevel3).filter(AuLevel3.code == person.address_au_level3).one()
                        bag_name = bag.name

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        # item = map_composition.getComposerItemById("person_name")
        # name = person.name +u", "+ person.first_name
        # item.setText(name)
        # item.adjustSizeToText()

        item = map_composition.getComposerItemById("state_reg_no")
        item.setText(person.state_registration_no)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("person_id")
        item.setText(person.person_id)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("person_account_no")
        item.setText(person.bank_account_no)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("person_bank_name")
        item.setText(bank_name)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("person_phone")
        item.setText(person.phone)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("person_email")
        item.setText(person.email_address)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("person_address")
        person_address = ''
        local_name = " "
        address_street_name = ""
        address_khaskhaa = ""
        address_building_no = ""
        address_entrance_no = ""
        address_apartment_no = ""
        if person.address_street_name != None:
            address_street_name = person.address_street_name + u" гудамж, "
        if person.address_khaskhaa != None:
            address_khaskhaa = person.address_khaskhaa
        if person.address_building_no != None:
            address_building_no = person.address_building_no + u" байр, "
        if person.address_entrance_no != None:
            address_entrance_no = person.address_entrance_no + ', '
        if person.address_apartment_no != None:
            address_apartment_no = person.address_apartment_no
        if person.address_street_name != None or person.address_khaskhaa != None:
            if person.address_town_or_local_name != None:
                local_name  = person.address_town_or_local_name + ', '
            person_address = aimag_name +", "+ soum_name +", " +bag_name+", "+local_name + address_street_name + address_khaskhaa
        elif person.address_building_no != None or person.address_entrance_no != None:
            if person.address_town_or_local_name != None:
                local_name  = person.address_town_or_local_name + ', '
            person_address = aimag_name +", "+ soum_name +", " +bag_name+", "+local_name + address_building_no + address_entrance_no + address_apartment_no
        else:
            if person.address_town_or_local_name != None:
                local_name  = person.address_town_or_local_name
            person_address = aimag_name +", "+ soum_name +", " +bag_name+", "+local_name
        item.setText(self.__wrap(person_address,40))
        # item.adjustSizeToText()

    def __copy_label(self, label, text, map_composition):

        label_2 = QgsComposerLabel(map_composition)
        label_2.setText(text)
        map_composition.addItem(label_2)

        label_2.setItemPosition(label.x(), label.y() + 5)

        label_2.setFont(label.font())
        label_2.setFontColor(label.fontColor())
        label_2.setOpacity(label.opacity())
        label_2.setMargin(0)
        label_2.adjustSizeToText()
        return label_2

    def __add_contract_condition(self, map_composition):

        contract_no = self.contract_num_edit.text()
        app_no = self.application_this_contract_based_edit.text()

        try:
            app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app_no).all()
            for p in app_person:
                if p.main_applicant == True:
                    person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()
            contract_condition = self.session.query(CtContractCondition).filter(CtContractCondition.contract == contract_no).all()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        if person.type == 10 or person.type == 20 or person.type == 30 or person.type == 40:
            contract_condition_4_2 = map_composition.getComposerItemById("contract_condition_4_2")
            contract_condition_5_1 = map_composition.getComposerItemById("contract_condition_5_1")
            contract_condition_5_2 = map_composition.getComposerItemById("contract_condition_5_2")
            contract_condition_5_3 = map_composition.getComposerItemById("contract_condition_5_3")
            contract_condition_6_2 = map_composition.getComposerItemById("contract_condition_6_2")
            for c in contract_condition:
                con_code = str(c.condition)
                if con_code[1:-3] == "402":
                    condition =  self.session.query(ClContractCondition).filter(ClContractCondition.code == c.condition).one()
                    text_len = len(condition.description)
                    a = 0
                    b = len(condition.description)
                    i = 0
                    if text_len < 105:
                        contract_condition_4_2 = self.__copy_label(contract_condition_4_2,'  - '+condition.description,map_composition)
                    else:
                        while(text_len > 105):

                            b = b - 105
                            t = condition.description[a:-b]
                            t = t[-20:]
                            count = 0
                            sp = 0
                            for t in t:
                                count = count + 1
                                if t == " ":
                                    sp = count

                            i = 20 - sp
                            b = b + i

                            contract_condition_4_2 = self.__copy_label(contract_condition_4_2,'  - '+condition.description[a:-b],map_composition)
                            y = 105 - i

                            text_len = text_len - y
                            a = a + y
                            if text_len < 105:
                                contract_condition_4_2 = self.__copy_label(contract_condition_4_2,'  - '+condition.description[-(text_len):],map_composition)

                if con_code[1:-3] == "501":
                    condition =  self.session.query(ClContractCondition).filter(ClContractCondition.code == c.condition).one()
                    text_len = len(condition.description)
                    a = 0
                    b = len(condition.description)
                    i = 0
                    if text_len < 105:
                        contract_condition_5_1 = self.__copy_label(contract_condition_5_1,'  - '+condition.description,map_composition)
                    else:
                        while(text_len > 105):

                            b = b - 105
                            t = condition.description[a:-b]
                            t = t[-20:]
                            count = 0
                            sp = 0
                            for t in t:
                                count = count + 1
                                if t == " ":
                                    sp = count

                            i = 20 - sp
                            b = b + i

                            contract_condition_4_2 = self.__copy_label(contract_condition_5_1,'  - '+condition.description[a:-b],map_composition)
                            y = 105 - i

                            text_len = text_len - y
                            a = a + y
                            if text_len < 105:
                                contract_condition_4_2 = self.__copy_label(contract_condition_5_1,'  - '+condition.description[-(text_len):],map_composition)

                if con_code[1:-3] == "502":
                    condition =  self.session.query(ClContractCondition).filter(ClContractCondition.code == c.condition).one()
                    text_len = len(condition.description)
                    a = 0
                    b = len(condition.description)
                    i = 0
                    if text_len < 105:
                        contract_condition_5_2 = self.__copy_label(contract_condition_5_2,'  - '+condition.description,map_composition)
                    else:
                        while(text_len > 105):

                            b = b - 105
                            t = condition.description[a:-b]
                            t = t[-20:]
                            count = 0
                            sp = 0
                            for t in t:
                                count = count + 1
                                if t == " ":
                                    sp = count

                            i = 20 - sp
                            b = b + i

                            contract_condition_5_2 = self.__copy_label(contract_condition_5_2,'  - '+condition.description[a:-b],map_composition)
                            y = 105 - i

                            text_len = text_len - y
                            a = a + y
                            if text_len < 105:
                                contract_condition_5_2 = self.__copy_label(contract_condition_5_2,'  - '+condition.description[-(text_len):],map_composition)

                if con_code[1:-3] == "503":
                    condition =  self.session.query(ClContractCondition).filter(ClContractCondition.code == c.condition).one()
                    text_len = len(condition.description)
                    a = 0
                    b = len(condition.description)
                    i = 0
                    if text_len < 105:
                        contract_condition_5_3 = self.__copy_label(contract_condition_5_3,'  - '+condition.description,map_composition)
                    else:
                        while(text_len > 105):

                            b = b - 105
                            t = condition.description[a:-b]
                            t = t[-20:]
                            count = 0
                            sp = 0
                            for t in t:
                                count = count + 1
                                if t == " ":
                                    sp = count

                            i = 20 - sp
                            b = b + i

                            contract_condition_5_3 = self.__copy_label(contract_condition_5_3,'  - '+condition.description[a:-b],map_composition)
                            y = 105 - i

                            text_len = text_len - y
                            a = a + y
                            if text_len < 105:
                                contract_condition_5_3 = self.__copy_label(contract_condition_5_3,'  - '+condition.description[-(text_len):],map_composition)

                if con_code[1:-3] == "602":
                    condition =  self.session.query(ClContractCondition).filter(ClContractCondition.code == c.condition).one()
                    text_len = len(condition.description)
                    a = 0
                    b = len(condition.description)
                    i = 0
                    if text_len < 105:
                        contract_condition_6_2 = self.__copy_label(contract_condition_6_2,'  - '+condition.description,map_composition)
                    else:
                        while(text_len > 105):

                            b = b - 105
                            t = condition.description[a:-b]
                            t = t[-20:]
                            count = 0
                            sp = 0
                            for t in t:
                                count = count + 1
                                if t == " ":
                                    sp = count

                            i = 20 - sp
                            b = b + i

                            contract_condition_6_2 = self.__copy_label(contract_condition_6_2,'  - '+condition.description[a:-b],map_composition)
                            y = 105 - i

                            text_len = text_len - y
                            a = a + y
                            if text_len < 105:
                                contract_condition_6_2 = self.__copy_label(contract_condition_6_2,'  - '+condition.description[-(text_len):],map_composition)
        elif person.type == 50 or person.type == 60:
            use_contract_condition_3_6 = map_composition.getComposerItemById("contract_condition_3_6")
            use_contract_condition_4_2 = map_composition.getComposerItemById("contract_condition_4_2")
            use_contract_condition_5_1 = map_composition.getComposerItemById("contract_condition_5_1")
            use_contract_condition_5_2 = map_composition.getComposerItemById("contract_condition_5_2")
            use_contract_condition_5_3 = map_composition.getComposerItemById("contract_condition_5_3")
            for c in contract_condition:
                con_code = str(c.condition)
                if con_code[1:-3] == "306":
                    condition =  self.session.query(ClContractCondition).filter(ClContractCondition.code == c.condition).one()
                    text_len = len(condition.description)
                    a = 0
                    b = len(condition.description)
                    i = 0
                    if text_len < 105:
                        use_contract_condition_3_6 = self.__copy_label(use_contract_condition_3_6,'  - '+condition.description,map_composition)
                    else:
                        while(text_len > 105):

                            b = b - 105
                            t = condition.description[a:-b]
                            t = t[-20:]
                            count = 0
                            sp = 0
                            for t in t:
                                count = count + 1
                                if t == " ":
                                    sp = count

                            i = 20 - sp
                            b = b + i

                            use_contract_condition_3_6 = self.__copy_label(use_contract_condition_3_6,'  - '+condition.description[a:-b],map_composition)
                            y = 105 - i

                            text_len = text_len - y
                            a = a + y
                            if text_len < 105:
                                use_contract_condition_3_6 = self.__copy_label(use_contract_condition_3_6,'  - '+condition.description[-(text_len):],map_composition)

                if con_code[1:-3] == "402":
                    condition =  self.session.query(ClContractCondition).filter(ClContractCondition.code == c.condition).one()
                    text_len = len(condition.description)
                    a = 0
                    b = len(condition.description)
                    i = 0
                    if text_len < 105:
                        use_contract_condition_4_2 = self.__copy_label(use_contract_condition_4_2,'  - '+condition.description,map_composition)
                    else:
                        while(text_len > 105):

                            b = b - 105
                            t = condition.description[a:-b]
                            t = t[-20:]
                            count = 0
                            sp = 0
                            for t in t:
                                count = count + 1
                                if t == " ":
                                    sp = count

                            i = 20 - sp
                            b = b + i

                            use_contract_condition_4_2 = self.__copy_label(use_contract_condition_4_2,'  - '+condition.description[a:-b],map_composition)
                            y = 105 - i

                            text_len = text_len - y
                            a = a + y
                            if text_len < 105:
                                use_contract_condition_4_2 = self.__copy_label(use_contract_condition_4_2,'  - '+condition.description[-(text_len):],map_composition)

                if con_code[1:-3] == "501":
                    condition =  self.session.query(ClContractCondition).filter(ClContractCondition.code == c.condition).one()
                    text_len = len(condition.description)
                    a = 0
                    b = len(condition.description)
                    i = 0
                    if text_len < 105:
                        use_contract_condition_5_1 = self.__copy_label(use_contract_condition_5_1,'  - '+condition.description,map_composition)
                    else:
                        while(text_len > 105):

                            b = b - 105
                            t = condition.description[a:-b]
                            t = t[-20:]
                            count = 0
                            sp = 0
                            for t in t:
                                count = count + 1
                                if t == " ":
                                    sp = count

                            i = 20 - sp
                            b = b + i

                            use_contract_condition_5_1 = self.__copy_label(use_contract_condition_5_1,'  - '+condition.description[a:-b],map_composition)
                            y = 105 - i

                            text_len = text_len - y
                            a = a + y
                            if text_len < 105:
                                use_contract_condition_5_1 = self.__copy_label(use_contract_condition_5_1,'  - '+condition.description[-(text_len):],map_composition)

                if con_code[1:-3] == "502":
                    condition =  self.session.query(ClContractCondition).filter(ClContractCondition.code == c.condition).one()
                    text_len = len(condition.description)
                    a = 0
                    b = len(condition.description)
                    i = 0
                    if text_len < 105:
                        use_contract_condition_5_2 = self.__copy_label(use_contract_condition_5_2,'  - '+condition.description,map_composition)
                    else:
                        while(text_len > 105):

                            b = b - 105
                            t = condition.description[a:-b]
                            t = t[-20:]
                            count = 0
                            sp = 0
                            for t in t:
                                count = count + 1
                                if t == " ":
                                    sp = count

                            i = 20 - sp
                            b = b + i

                            use_contract_condition_5_2 = self.__copy_label(use_contract_condition_5_2,'  - '+condition.description[a:-b],map_composition)
                            y = 105 - i

                            text_len = text_len - y
                            a = a + y
                            if text_len < 105:
                                use_contract_condition_5_2 = self.__copy_label(use_contract_condition_5_2,'  - '+condition.description[-(text_len):],map_composition)

                if con_code[1:-3] == "503":
                    condition =  self.session.query(ClContractCondition).filter(ClContractCondition.code == c.condition).one()
                    text_len = len(condition.description)
                    a = 0
                    b = len(condition.description)
                    i = 0
                    if text_len < 105:
                        use_contract_condition_5_3 = self.__copy_label(use_contract_condition_5_3,'  - '+condition.description,map_composition)
                    else:
                        while(text_len > 105):

                            b = b - 105
                            t = condition.description[a:-b]
                            t = t[-20:]
                            count = 0
                            sp = 0
                            for t in t:
                                count = count + 1
                                if t == " ":
                                    sp = count

                            i = 20 - sp
                            b = b + i

                            use_contract_condition_5_3 = self.__copy_label(use_contract_condition_5_3,'  - '+condition.description[a:-b],map_composition)
                            y = 105 - i

                            text_len = text_len - y
                            a = a + y
                            if text_len < 105:
                                use_contract_condition_5_3 = self.__copy_label(use_contract_condition_5_3,'  - '+condition.description[-(text_len):],map_composition)

    def __add_fee(self,map_composition):

        contract_no = self.contract_num_edit.text()
        app_no = self.application_this_contract_based_edit.text()
        try:
            fee = self.session.query(CtFee).filter(CtFee.contract == contract_no).all()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        person_name = map_composition.getComposerItemById("person_name")
        share = map_composition.getComposerItemById("share")

        Quarterly1 = map_composition.getComposerItemById("Quarterly1")

        Quarterly2 = map_composition.getComposerItemById("Quarterly2")

        Quarterly3 = map_composition.getComposerItemById("Quarterly3")

        Quarterly4 = map_composition.getComposerItemById("Quarterly4")

        for fee in fee:
            person = self.session.query(BsPerson).filter(BsPerson.person_id == fee.person).one()
            if person.type == 10 or person.type == 20:
                sub_name = person.name[:1]+"."+person.first_name
            elif person.type == 30 or person.type == 40 or person.type == 60:
                sub_name = person.name
            elif person.type == 50:
                sub_name = person.name +" "+ person.first_name
            person_name = self.__copy_label(person_name,self.__wrap(sub_name,50),map_composition)
            share = self.__copy_label(share,str(fee.share),map_composition)
            Quarterly1 = self.__copy_label(Quarterly1,str(fee.fee_contract/4),map_composition)
            Quarterly2 = self.__copy_label(Quarterly2,str(fee.fee_contract/4),map_composition)
            Quarterly3 = self.__copy_label(Quarterly3,str(fee.fee_contract/4),map_composition)
            Quarterly4 = self.__copy_label(Quarterly4,str(fee.fee_contract/4),map_composition)

    def __add_parcel_cert(self,map_composition):

        app_no = self.application_this_contract_based_edit.text()
        contract_no = self.contract_num_edit.text()
        parcel_id  = self.id_main_edit.text()[1:-9] + self.id_main_edit.text()[4:]

        landuse = self.land_use_type_edit.text()
        area_m2 = self.calculated_area_edit.text()
        area_m2 = str((area_m2)) + " /"+str(float(area_m2)/10000)+"/"

        try:
            parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == self.id_main_edit.text()).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        address_streetname = " "
        address_khashaa = " "
        address_neighbourhood = " "
        if parcel.address_streetname != None:
            address_streetname = parcel.address_streetname
        if parcel.address_khashaa != None:
            address_khashaa = parcel.address_khashaa
        if parcel.address_neighbourhood != None:
            address_neighbourhood = parcel.address_neighbourhood

        bag_name = self.bag_edit.text()
        parcel_address = bag_name + u', ' + address_streetname +u" гудамж, "+ address_khashaa +", "+ address_neighbourhood
        item = map_composition.getComposerItemById("parcel_address")
        item.setText(parcel_address)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("landuse_type")
        item.setText(self.__wrap(landuse,25))
        # item.adjustSizeToText()

        item = map_composition.getComposerItemById("area_m2")
        item.setText(area_m2)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("parcel_id")
        item.setText(parcel_id)
        item.adjustSizeToText()

    def __add_cert_parcel(self):

        app_no = self.application_this_contract_based_edit.text()
        contract_no = self.contract_num_edit.text()
        parcel_id  = self.id_main_edit.text()[1:-9] + self.id_main_edit.text()[4:]

        landuse = self.land_use_type_edit.text()
        area_m2 = self.calculated_area_edit.text()
        area_m2 = str((area_m2)) + " /"+str(float(area_m2)/10000)+"/"

        try:
            parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == self.id_main_edit.text()).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        address_streetname = " "
        address_khashaa = " "
        address_neighbourhood = " "
        if parcel.address_streetname != None:
            address_streetname = parcel.address_streetname
        if parcel.address_khashaa != None:
            address_khashaa = parcel.address_khashaa
        if parcel.address_neighbourhood != None:
            address_neighbourhood = parcel.address_neighbourhood

        bag_name = self.bag_edit.text()
        parcel_address = bag_name + u', ' + address_streetname +u" гудамж, "+ address_khashaa +", "+ address_neighbourhood

        landuse = self.__wrap(landuse,25)

        parcel_value = [parcel_id, landuse, area_m2, parcel_address]
        return parcel_value

    def __add_parcel(self,map_composition):

        base_fee = 0
        payment = 0
        app_no = self.application_this_contract_based_edit.text()
        contract_no = self.contract_num_edit.text()
        parcel_id  = self.id_main_edit.text()[1:-9] + self.id_main_edit.text()[4:]
        landuse = self.land_use_type_edit.text()
        area_m2 = self.calculated_area_edit.text()
        if float(area_m2) > 10000:
            area_m2 = str(float(area_m2)/10000) + u" га"
        else:
            area_m2 = area_m2 + u" м2"

        try:
            fee = self.session.query(CtFee).filter(CtFee.contract == contract_no).all()

            for fee in fee:
                payment =payment + fee.fee_contract
                base_fee = fee.base_fee_per_m2

            item = map_composition.getComposerItemById("base_fee_per_m2")
            item.setText(str(base_fee) + u" төг")
            item.adjustSizeToText()

            item = map_composition.getComposerItemById("fee_year")
            item.setText(str(payment) + u" төг")
            item.adjustSizeToText()

            all_fee = float(payment)
            item = map_composition.getComposerItemById("all_year_fee")
            item.setText(str(all_fee))
            item.adjustSizeToText()

            item = map_composition.getComposerItemById("landuse_type")
            item.setText(self.__wrap(landuse,25))

            item = map_composition.getComposerItemById("landuse_area")
            item.setText(area_m2)
            item.adjustSizeToText()

            item = map_composition.getComposerItemById("area_m2")
            item.setText(area_m2)
            item.adjustSizeToText()

            item = map_composition.getComposerItemById("parcel_id")
            item.setText(parcel_id)
            item.adjustSizeToText()

            item = map_composition.getComposerItemById("parcel_no")
            item.setText(parcel_id)
            item.adjustSizeToText()

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))



    def __add_contract_no(self,map_composition):

        contact_first_name = ''
        contact_surname = ''
        contact_position = ''
        app_no = self.application_this_contract_based_edit.text()
        contract_no = self.contract_num_edit.text()
        cerificate_no = self.calculated_num_edit.text()
        try:
            contract  = self.session.query(CtContract).filter(CtContract.contract_no == contract_no).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        try:
            app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app_no).all()
            if app_no[6:-9] == '07' or app_no[6:-9] == '14':
                app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app_no)\
                                        .filter(CtApplicationPersonRole.role == 70).all()
            for p in app_person:
                person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()
                if person.contact_first_name != None:
                    contact_first_name = person.contact_first_name
                if person.contact_surname != None:
                    contact_surname = person.contact_surname
                if person.contact_position != None:
                    contact_position = person.contact_position
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        header = "no text"
        name  = "no text"
        if person.type == 10 or person.type == 20:
            header = u"ИРГЭНД ГАЗАР ЭЗЭМШҮҮЛЭХ ГЭРЭЭ"
            name = u"                                                                                         " \
                   + person.name +u" овогтой "+ person.first_name + u" нар энэхүү гэрээг байгуулав."
        elif person.type == 30 or person.type == 40:
            header = u"ХУУЛИЙН ЭТГЭЭДЭД ГАЗАР ЭЗЭМШҮҮЛЭХ ГЭРЭЭ"
            name = u"                                                                                         " \
                   + u" (" + person.name + u") " + contact_position + u" ажилтай " + contact_surname + \
                   u" овогтой " + contact_first_name + u" нар энэхүү гэрээг байгуулав."
        elif person.type == 50:
            header = u"ГАДААДЫН ИРГЭНД ГАЗАР АШИГЛУУЛАХ ГЭРЭЭ"
            name = u"                                                                                         " \
                   + person.name +u", "+ person.first_name + u" нар энэхүү гэрээг байгуулав."
        elif person.type == 60:
            header = u"ГАДААДЫН ХУУЛИЙН ЭТГЭЭДЭД ГАЗАР АШИГЛУУЛАХ ГЭРЭЭ"
            name = u"                                                                                         " \
                   + " ("+person.name+") " + contact_position + u"  ажилтай " + contact_surname + \
                   u" овогтой " + contact_first_name + u" нар энэхүү гэрээг байгуулав."

        item = map_composition.getComposerItemById("person_contract")
        item.setText(self.__wrap(name, 250))
        # item.adjustSizeToText()

        item = map_composition.getComposerItemById("contract_header")
        item.setText(header)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("contract_no")
        item.setText(contract_no)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("cerificate_no")
        item.setText(cerificate_no)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("contract_date")
        contract_date = str(contract.contract_date)
        contract_date = contract_date[0:-6]+u" оны " + contract_date[5:-3]+u" сарын " + contract_date[-2:] + u" өдөр"
        item.setText(contract_date)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("contract_begin_date")
        item.setText(str(contract.contract_begin))
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("contract_end_date")
        item.setText(str(contract.contract_end))
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("contract_year")
        contract_begin = PluginUtils.convert_python_date_to_qt(self.contract.contract_begin)
        contract_end = PluginUtils.convert_python_date_to_qt(self.contract.contract_end)
        duration = 0
        if contract_begin is not None:
            self.contract_begin_edit.setText(contract_begin.toString(Constants.DATABASE_DATE_FORMAT))

        if contract_end is not None:
            # self.contract_end_edit.setText(contract_end.toString(Constants.DATABASE_DATE_FORMAT))
            self.contract_end_date.setDate(contract_end)
            duration = contract_end.year() - contract_begin.year()
        duration = '/'+str(duration)+'/'
        item.setText(duration)
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

    @pyqtSlot()
    def on_print_certificate_button_clicked(self):

        app_no = self.application_this_contract_based_edit.text()
        contract_no = self.contract_num_edit.text()
        contract_count = self.session.query(CtContract).filter(CtContract.contract_no == contract_no).count()
        if contract_count == 0:
            PluginUtils.show_error(self, self.tr("contract error"), self.tr("not save"))
            return

        try:
            app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app_no).all()
            for p in app_person:
                if p.main_applicant == True:
                    person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        ok = 0
        try:
            app_status = self.session.query(CtApplicationStatus).filter(CtApplicationStatus.application == app_no).all()
            for p in app_status:
                if p.status == 9:
                    ok = 1
                    officer = self.session.query(SetRole).filter(SetRole.user_name_real == p.officer_in_charge).one()
        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))
        if ok == 0:
            PluginUtils.show_error(self, self.tr("contract error"), self.tr("must status 9"))
            return
        header = "no text"
        if self.pdf_checkbox.isChecked():
            path = FileUtils.map_file_path()
            if person.type == 10 or person.type == 20:
                template = path + "cert_person.qpt"
            elif person.type == 30:
                template = path + "cert_company.qpt"
            elif person.type == 40:
                template = path + "cert_state.qpt"
            elif person.type == 50 or person.type == 60:
                template = path + "cert_use.qpt"

            templateDOM = QDomDocument()
            templateDOM.setContent(QFile(template), False)

            map_canvas = QgsMapCanvas()

            map_composition = QgsComposition(map_canvas.mapRenderer())
            map_composition.loadFromTemplate(templateDOM)

            map_composition.setPrintResolution(300)

            printer = QPrinter()
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path+"certificate.pdf")
            printer.setPaperSize(QSizeF(map_composition.paperWidth(), map_composition.paperHeight()), QPrinter.Millimeter)
            printer.setFullPage(True)
            printer.setColorMode(QPrinter.Color)
            printer.setResolution(map_composition.printResolution())

            pdfPainter = QPainter(printer)
            paperRectMM = printer.pageRect(QPrinter.Millimeter)
            paperRectPixel = printer.pageRect(QPrinter.DevicePixel)
            map_composition.render(pdfPainter, paperRectPixel, paperRectMM)
            pdfPainter.end()

            self.__add_aimag_name_cert(map_composition)
            self.__add_soum_name_cert(map_composition)
            # self.__add_contract_no(map_composition)
            self.__add_decision_cert(map_composition)
            self.__add_parcel_cert(map_composition)
            # self.__add_fee(map_composition)
            # self.__add_contract_condition(map_composition)
            # self.__add_person_signature(map_composition)
            # # self.__add_app_status_date(map_composition)
            self.__add_person_name_cert(map_composition)
            self.__add_officer_cert(map_composition)
            # self.__add_app_remarks(map_composition)
            map_composition.exportAsPDF(path + "certificate.pdf")


            QDesktopServices.openUrl(QUrl.fromLocalFile(path+"certificate.pdf"))
        else:
            self.__cert_docx_print(person)


    def __cert_docx_print(self, person):

        aimag_name = self.__add_cert_aimag().name
        soum_name = self.__add_cert_soum().name
        decision_date = self.__add__cert_decision()[1]
        approved_duration = self.__add__cert_decision()[2]
        contract_date = self.__add__cert_decision()[3]

        parcel_id = self.__add_cert_parcel()[0]
        parcel_address = self.__add_cert_parcel()[3]
        landuse = self.__add_cert_parcel()[1]
        area_m2 = self.__add_cert_parcel()[2]
        person_id = self.__add_cert_person()[0]
        family_name = self.__add_cert_person()[1]
        surname = self.__add_cert_person()[2]
        first_name = self.__add_cert_person()[3]
        company_name = self.__add_cert_person()[4]
        company_id = self.__add_cert_person()[5]
        person_address = self.__add_cert_person()[6]
        officer_name = self.__add_cert_officer_name()

        path = FileUtils.map_file_path()
        tpl = DocxTemplate(path + 'cert_company.docx')
        if person.type == 10 or person.type == 20:
            tpl = DocxTemplate(path + 'cert_person.docx')
        elif person.type == 30:
            tpl = DocxTemplate(path + 'cert_company.docx')
        elif person.type == 40:
            tpl = DocxTemplate(path + 'cert_state.docx')
        elif person.type == 50 or person.type == 60:
            tpl = DocxTemplate(path + 'cert_use.docx')

        context = {
            'aimag_name': aimag_name,
            'soum_name': soum_name,
            'decision': decision_date,
            'parcel_id': parcel_id,
            'parcel_address': parcel_address,
            'person_id': person_id,
            'company_id': company_id,
            'family_name': family_name,
            'surname': surname,
            'first_name': first_name,
            'company_name': company_name,
            'person_address': person_address,
            'landuse': landuse,
            'contract_date': contract_date,
            'officer_name': officer_name,
            'officer_aimag': aimag_name,
            'officer_soum': soum_name,
            'area_m2': area_m2,
            'approved_duration': approved_duration
        }
        tpl.render(context)
        tpl.save(path + 'certificate.docx')
        default_path = r'D:/TM_LM2/contracts'
        # tpl = DocxTemplate(path + 'cert_company.docx')

        QDesktopServices.openUrl(
            QUrl.fromLocalFile(path + 'certificate.docx'))
        # try:
        #     # tpl.save(default_path + "/" + contract_no[:-6] + '-' + contract_no[-5:] + ".docx")
        #     QDesktopServices.openUrl(
        #         QUrl.fromLocalFile(path + 'cert_company.docx'))
        # except IOError, e:
        #     PluginUtils.show_error(self, self.tr("Out error"),
        #                            self.tr("This file is already opened. Please close re-run"))

    @pyqtSlot()
    def on_print_soil_qual_pass_edit_clicked(self):

        current_file = os.path.dirname(__file__) + "/.." + "/pentaho/contract_soil_qual_pass.prpt"
        QDesktopServices.openUrl(QUrl.fromLocalFile(current_file))

    @pyqtSlot(QModelIndex)
    def on_conditions_tree_clicked(self, index):

        item = self.item_model.itemFromIndex(index)
        self.preview_text_edit.clear()
        self.__show_preview(item)

    @pyqtSlot()
    def on_help_button_clicked(self):

        if self.tab_widget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/contracts.htm")
        elif self.tab_widget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/contract_parcel.htm")
        elif self.tab_widget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/contract_contract_details.htm")
        elif self.tab_widget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/contract_conditions.htm")
        elif self.tab_widget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/contract_landfee.htm")
        elif self.tab_widget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/contract_landfee_history.htm")
        elif self.tab_widget.currentIndex() == 6:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/contract_documents.htm")
        elif self.tab_widget.currentIndex() == 7:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/contract_application_document.htm")
        elif self.tab_widget.currentIndex() == 8:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/contract_prints.htm")

    @pyqtSlot(int)
    def on_applicant_documents_cbox_currentIndexChanged(self, index):

        if not self.app_doc_twidget:
            return

        if self.updating:
            return

        # self.__update_app_documents_twidget()

    #public functions
    def current_create_application(self):

        try:
            con_app_roles = self.contract.application_roles\
                    .filter(CtContractApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).one()

        except LM2Exception, e:
                PluginUtils.show_error(self, e.title(), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

        return con_app_roles.application_ref

    def current_document_applicant(self):

        applicant = self.applicant_documents_cbox.itemData(self.applicant_documents_cbox.currentIndex())
        return applicant

    def current_parent_object(self):

        return self.contract

    def current_parent_object_no(self):

        return self.contract_num_edit.text()

    @pyqtSlot(str)
    def on_calculated_num_edit_textChanged(self, text):

        self.calculated_num_edit.setStyleSheet(self.styleSheet())
        if text == '' or text == 'None':
            text = 0
        if text == None:
            text = 0
        new_certificate_no = int(text)
        try:
            values = self.session.query(BsPerson.type, CtApplication.approved_landuse)\
                .join(CtApplicationPersonRole, BsPerson.person_id == CtApplicationPersonRole.person)\
                .join(CtApplication, CtApplicationPersonRole.application == CtApplication.app_no)\
                .filter(CtApplicationPersonRole.application == self.application_this_contract_based_edit.text()).all()
            for value in values:
                if (value.type == 10 or value.type == 20) and (value.approved_landuse == 2205 or value.approved_landuse == 2204 or value.approved_landuse == 2206):
                    certificate_count = self.session.query(SetCertificate)\
                        .filter(SetCertificate.certificate_type == 10)\
                        .filter(SetCertificate.range_first_no <= new_certificate_no)\
                        .filter(SetCertificate.range_last_no >= new_certificate_no).count()
                    if certificate_count == 0:
                        self.calculated_num_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                        self.is_certificate = False
                    else:
                        self.is_certificate = True
                elif (value.type == 10 or value.type == 20 or value.type == 30) and (value.approved_landuse != 2205 or value.approved_landuse != 2204 or value.approved_landuse != 2206):
                    certificate_count = self.session.query(SetCertificate)\
                        .filter(SetCertificate.certificate_type == 20)\
                        .filter(SetCertificate.range_first_no <= new_certificate_no)\
                        .filter(SetCertificate.range_last_no >= new_certificate_no).count()
                    if certificate_count == 0:
                        self.calculated_num_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                        self.is_certificate = False
                    else:
                        self.is_certificate = True
                elif (value.type == 40):
                    certificate_count = self.session.query(SetCertificate)\
                        .filter(SetCertificate.certificate_type == 40)\
                        .filter(SetCertificate.range_first_no <= new_certificate_no)\
                        .filter(SetCertificate.range_last_no >= new_certificate_no).count()
                    if certificate_count == 0:
                        self.calculated_num_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                        self.is_certificate = False
                    else:
                        self.is_certificate = True
                elif (value.type == 50 or value.type == 60):
                    certificate_count = self.session.query(SetCertificate)\
                        .filter(SetCertificate.certificate_type == 30)\
                        .filter(SetCertificate.range_first_no <= new_certificate_no)\
                        .filter(SetCertificate.range_last_no >= new_certificate_no).count()
                    if certificate_count == 0:
                        self.calculated_num_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                        self.is_certificate = False
                    else:
                        self.is_certificate = True
        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    @pyqtSlot(str)
    def on_person_id_edit_textChanged(self, text):

        if self.attribute_update:
            return
        self.app_number_cbox.clear()
        value = "%" + text + "%"

        application = self.session.query(CtApplication)\
            .join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application)\
            .join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id)\
            .filter(BsPerson.person_id.ilike(value)).all()

        for app in application:
            self.app_no = app.app_no
            self.app_number_cbox.addItem(self.app_no, self.app_no)

    @pyqtSlot(bool)
    def on_cancelled_rbutton_toggled(self, state):

        if state:
            try:
                contract_apps = self.session.query(CtContractApplicationRole).\
                    filter(CtContractApplicationRole.contract == self.contract.contract_no).all()
                for contract_app in contract_apps:
                    mortgage_count = self.session.query(CtApp8Ext).\
                        filter(CtApp8Ext.app_no == contract_app.application).count()
                    if mortgage_count > 0:
                        mortgage = self.session.query(CtApp8Ext).\
                        filter(CtApp8Ext.app_no == contract_app.application).one()
                        today = date.today()
                        mortgage_date = mortgage.end_mortgage_period
                        if today < mortgage_date:
                            self.apply_button.setEnabled(False)

                            PluginUtils.show_message(self, self.tr("Mortgage"), self.tr("The Contract can not cancel. it is relating to the mortgage."))
                            self.active_rbutton.setChecked(True)
                            return

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return
        else:
            self.apply_button.setEnabled(True)

    @pyqtSlot(bool)
    def on_draft_rbutton_toggled(self, state):

        if state:
            self.calculated_num_edit.setReadOnly(False)
        else:
            self.calculated_num_edit.setReadOnly(True)

    @pyqtSlot(bool)
    def on_expired_rbutton_toggled(self, state):

        if self.contract.status == Constants.CONTRACT_STATUS_EXPIRED:
            if not state and self.cancelled_rbutton.isChecked() == False:
                PluginUtils.show_message(self, self.tr('Expired contracts'), self.tr('Expired contracts!'))
                self.expired_rbutton.setChecked(True)
                return
        if self.contract.status == Constants.CONTRACT_STATUS_ACTIVE:
            if state and self.cancelled_rbutton.isChecked() == False:
                PluginUtils.show_message(self, self.tr('Activate contracts'), self.tr('Activate contracts!'))
                self.active_rbutton.setChecked(True)
                return