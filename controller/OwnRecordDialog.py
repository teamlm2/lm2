__author__ = 'ankhbold'

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from inspect import currentframe
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_
from ..view.Ui_OwnRecordDialog import *
from ..controller.qt_classes.DropLabel import DropLabel
from ..model import Constants
from ..model.AuLevel1 import AuLevel1
from ..model.AuLevel2 import AuLevel2
from ..model.CtApplicationStatus import *
from ..model.CtOwnershipRecord import *
from ..model.CtRecordApplicationRole import *
from ..model.ClRecordCancellationReason import *
from ..model.CtDecision import *
from ..model.CtDecisionApplication import *
from ..model.CtTaxAndPrice import *
from ..model.ClPaymentFrequency import *
from ..model import SettingsConstants
from ..model.BsPerson import *
from ..model.Enumerations import UserRight
from ..model.DatabaseHelper import DatabaseHelper
from ..model.SetContractDocumentRole import *
from ..model.SetApplicationTypeDocumentRole import *
from .qt_classes.IntegerSpinBoxDelegate import *
from .qt_classes.ComboBoxDelegate import *
from .qt_classes.RecordDocumentDelegate import RecordDocumentDelegate
from .qt_classes.ObjectAppDocumentDelegate import ObjectAppDocumentDelegate
from ..model.SetTaxAndPriceZone import *
from ..utils.SessionHandler import SessionHandler
from ..utils.PluginUtils import PluginUtils
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.FilePath import *
from ..utils.FileUtils import FileUtils
from ..model.LM2Exception import LM2Exception
import win32net
import os

OWNER_NAME = 0
OWNER_ID = 1
OWNER_SHARE = 2
OWNER_AREA = 3
OWNER_VALUE_CALCULATED = 4
OWNER_PRICE_PAID = 5
OWNER_TAX = 6
OWNER_GRACE_PERIOD = 7
OWNER_PAYMENT_FREQUENCY = 8

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


class OwnRecordDialog(QDialog, Ui_OwnRecordDialog, DatabaseHelper):

    def __init__(self, record, navigator, attribute_update, parent=None):

        super(OwnRecordDialog,  self).__init__(parent)
        DatabaseHelper.__init__(self)
        self.navigator = navigator
        self.record = record
        self.attribute_update = attribute_update
        self.timer = None
        self.session = SessionHandler().session_instance()
        self.updating = False

        self.setupUi(self)
        self.close_button.clicked.connect(self.reject)
        self.setWindowTitle(self.tr("Ownership Dialog"))

        self.record_date_date.setDate(QDate.currentDate())
        self.ownership_end_date.setDate(QDate.currentDate())
        self.ownership_begin_edit.setDate(QDate.currentDate())

        self.drop_label = DropLabel("application", self.application_groupbox)
        self.drop_label.itemDropped.connect(self.on_drop_label_itemDropped)

        self.__setup_combo_boxes()
        self.__set_up_land_tax_twidget()
        self.__set_up_archive_land_tax_twidget()
        self.__setup_doc_twidgets()

        self.status_label.clear()
        self.landtax_message_label1.setStyleSheet("QLabel {color : red;}")
        self.landtax_message_label2.setStyleSheet("QLabel {color : red;}")
        self.landtax_message_label1.setText(self.tr('Without parcel no land tax information is available.'))
        self.landtax_message_label2.clear()

        if self.attribute_update:
            self.__setup_mapping()
        else:
            self.__generate_record_number()

        self.__setup_permissions()

    def __setup_mapping(self):

        self.record_number_edit.setText(self.record.record_no)
        self.certificate_number_edit.setText(str(self.record.certificate_no))

        self.__setup_status()
        self.__setup_right_type()

        qt_date = PluginUtils.convert_python_date_to_qt(self.record.record_date)
        if qt_date is not None:
            self.record_date_date.setDate(qt_date)

        record_begin = PluginUtils.convert_python_date_to_qt(self.record.record_begin)
        cancellation_date = PluginUtils.convert_python_date_to_qt(self.record.cancellation_date)

        if record_begin is not None:
            self.ownership_begin_edit.setDate(record_begin)

        if cancellation_date is not None:
            self.ownership_end_date.setDate(cancellation_date)
            self.cancellation_date_check_box.setCheckState(Qt.Checked)

            if self.record.cancellation_reason is not None:
                self.other_reason_rbutton.setChecked(True)
                self.other_reason_cbox.setCurrentIndex(self.other_reason_cbox.findData(self.record.cancellation_reason))

            # self.application_based_rbutton.setChecked(True)
            cancellation_application_c = self.record.application_roles.filter_by(role=Constants.APP_ROLE_CANCEL).count()
            if cancellation_application_c == 1:
                cancellation_application = self.record.application_roles.filter_by(role=Constants.APP_ROLE_CANCEL).one()
                if cancellation_application is None:
                    PluginUtils.show_error(self, self.tr("Error loading record"),
                                           self.tr("Could not load record. Cancellation application not found"))
                    self.reject()

                self.app_number_cbox.clear()
                self.app_number_cbox.addItem(cancellation_application.application, cancellation_application.application)
                self.app_number_cbox.setCurrentIndex(self.app_number_cbox.findText(cancellation_application.application))
                self.type_edit.setText(cancellation_application.application_ref.app_type_ref.description)

                app_persons = self.session.query(CtApplicationPersonRole). \
                    filter(CtApplicationPersonRole.application == cancellation_application.application).all()
                for app_person in app_persons:
                    self.person_id_edit.setText(app_person.person)

        application_role = self.record.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CREATES).one()
        application = application_role.application_ref

        if application_role is None or application is None:
            PluginUtils.show_error(self, self.tr("Error loading record"),
                                   self.tr("This record has no valid application assigned."))
            self.reject()
            return

        self.application_based_edit.setText(application.app_no)
        self.application_type_edit.setText(application.app_type_ref.description)

        parcel = application.parcel_ref
        self.id_main_edit.setText(parcel.parcel_id)
        self.old_id_edit.setText(parcel.old_parcel_id)
        self.geo_id_edit.setText(parcel.geo_id)
        self.calculated_area_edit.setText(str(parcel.area_m2))
        if parcel.documented_area_m2 == None:
            self.documented_area_edit.setText("")
        else:
            self.documented_area_edit.setText(str(parcel.documented_area_m2))

        soum = PluginUtils.soum_from_parcel(parcel.parcel_id)
        if soum is None:
            PluginUtils.show_error(self, self.tr("Error loading Record"),
                                   self.tr("Could not find the soum for the parcel."))
            self.reject()
            return

        soum_desc = self.session.query(AuLevel2.name).filter(AuLevel2.code == soum).one()
        self.soum_edit.setText(soum_desc[0])
        aimag = self.session.query(AuLevel1.name).filter(AuLevel1.code == soum[:3]).one()
        self.aimag_edit.setText(aimag[0])
        self.bag_edit.setText(parcel.address_neighbourhood)
        self.street_name_edit.setText(parcel.address_streetname)
        self.khashaa_edit.setText(parcel.address_khashaa)

        if parcel.landuse_ref:
            self.land_use_type_edit.setText(parcel.landuse_ref.description)

        self.__populate_landtax_tab()
        self.__populate_archive_period_cbox()

    def __setup_status(self):

        if self.record.status == Constants.RECORD_STATUS_ACTIVE:
            self.active_rbutton.setChecked(True)
        elif self.record.status == Constants.RECORD_STATUS_CANCELLED:
            self.cancelled_rbutton.setChecked(True)
        elif self.record.status == Constants.RECORD_STATUS_DRAFT:
            self.draft_rbutton.setChecked(True)

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

        delegate = RecordDocumentDelegate(self.doc_twidget, self)
        self.doc_twidget.setItemDelegate(delegate)

        try:
            self.__add_doc_types()
            # self.__update_doc_twidget()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    def __add_doc_types(self):

        #same document roles are required for the ownership record
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

        file_path = FilePath.ownership_file_path()
        record_no = self.record.record_no
        record_no = record_no.replace("/", "-")
        file_path = file_path + '/' + record_no
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        for file in os.listdir(file_path):
            os.listdir(file_path)
            if file.endswith(".pdf"):
                doc_type = file[17:-4]
                file_name = file
                record_no = file[:16]

                record_no = record_no[:10] +'/'+ record_no[-5:]

            for i in range(self.doc_twidget.rowCount()):
                doc_type_item = self.doc_twidget.item(i, DOC_TYPE_COLUMN)

                doc_type_code = str(doc_type_item.data(Qt.UserRole))

                if len(str(doc_type_item.data(Qt.UserRole))) == 1:
                    doc_type_code = '0'+ str(doc_type_item.data(Qt.UserRole))
                if len(doc_type) == 1:
                    doc_type = '0' + doc_type

                if doc_type == doc_type_code and self.record.record_no == record_no:
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

    def __setup_right_type(self):

        if self.record.right_type == Constants.ADVANCED_RIGHT_TYPE:
            self.advanced_right_rbutton.setChecked(True)
        else:
            self.standard_right_rbutton.setChecked(True)

    def __setup_combo_boxes(self):

        self.document_path_edit.setText(FilePath.ownership_file_path())
        try:
            apps = self.session.query(CtApplication.app_no)\
                .filter(or_(CtApplication.app_type == 2,CtApplication.app_type == 4,CtApplication.app_type == 5,CtApplication.app_type == 9,\
                            CtApplication.app_type == 14,CtApplication.app_type == 15,CtApplication.app_type == 16,CtApplication.app_type == 20)).all()
            reasons = self.session.query(ClRecordCancellationReason).all()

            for app in apps:
                self.app_number_cbox.addItem(app[0])

            self.app_number_cbox.setCurrentIndex(-1)

            for reason in reasons:
                self.other_reason_cbox.addItem(reason.description, reason.code)

            self.__setup_applicant_cbox()

        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            self.reject()

    def __setup_applicant_cbox(self):

        self.applicant_documents_cbox.clear()

        count = self.record.application_roles\
            .filter(CtRecordApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).count()

        if count == 0:
            return

        record_app_roles = self.record.application_roles\
            .filter(CtRecordApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).all()

        self.updating = True

        for record_app_role in record_app_roles:
            for rec_person_role in record_app_role.application_ref.stakeholders.all():
                person = rec_person_role.person_ref
                if person.first_name is None:
                    person_label = u"{0}".format(person.name)
                else:
                    person_label = u"{0}, {1}".format(person.name, person.first_name)
                self.applicant_documents_cbox.addItem(person_label, person.person_id)

        self.updating = False
        self.__update_app_documents_twidget()

    def __remove_document_items(self, twidget):

        while twidget.rowCount() > 0:
            twidget.removeRow(0)

    def __update_app_documents_twidget(self):

        self.__remove_document_items(self.app_doc_twidget)
        try:
            count = self.record.application_roles\
                        .filter(CtRecordApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).count()
            if count == 0: return

            con_app_roles = self.record.application_roles\
                        .filter(CtRecordApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).one()

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

            file_path = FilePath.ownership_file_path()

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

                        if doc_type == doc_type_code and self.application_based_edit.text() == app_no:
                                item_name = self.app_doc_twidget.item(i, APP_DOC_NAME_COLUMN)
                                item_name.setText(file_name)

                                item_provided = self.app_doc_twidget.item(i, APP_DOC_PROVIDED_COLUMN)
                                item_provided.setCheckState(Qt.Checked)

                                self.app_doc_twidget.setItem(i, 0, item_provided)
                                self.app_doc_twidget.setItem(i, 2, item_name)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    def __setup_permissions(self):

        user_name = QSettings().value(SettingsConstants.USER)
        user_rights = DatabaseUtils.userright_by_name(user_name)

        if UserRight.contracting_update in user_rights:
            self.apply_button.setEnabled(True)
            self.unassign_button.setEnabled(True)
            self.accept_button.setEnabled(True)
            self.search_button.setEnabled(True)
            self.record_date_date.setEnabled(True)
            self.record_status_groupbox.setEnabled(True)
            self.right_groupbox.setEnabled(True)
            self.documents_groupbox.setEnabled(True)
            self.ownership_end_groupbox.setEnabled(True)

        else:
            self.apply_button.setEnabled(False)
            self.unassign_button.setEnabled(False)
            self.accept_button.setEnabled(False)
            self.search_button.setEnabled(False)
            self.record_date_date.setEnabled(False)
            self.record_status_groupbox.setEnabled(False)
            self.right_groupbox.setEnabled(False)
            self.documents_groupbox.setEnabled(False)
            self.ownership_end_groupbox.setEnabled(False)

    def on_drop_label_itemDropped(self):

        self.__copy_record_from_navigator()

    @pyqtSlot()
    def on_accept_button_clicked(self):

        current_app_no = self.found_edit.text()

        if current_app_no == "":
            PluginUtils.show_error(self, self.tr("Record Error"), self.tr("No Application Number found."))
            return

        try:
            app_status = self.session.query(func.max(CtApplicationStatus.status)).\
                filter(CtApplicationStatus.application == current_app_no).one()

            if app_status[0] < 7:
                PluginUtils.show_error(self, self.tr("Record Error"), self.tr("First register decision and notary."))
                return

            application = self.session.query(CtApplication).filter_by(app_no=current_app_no).one()

        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        self.application_based_edit.setText(application.app_no)
        self.application_type_edit.setText(application.app_type_ref.description)
        self.found_edit.setText("")

        record_app = CtRecordApplicationRole()
        record_app.application_ref = application
        record_app.application = application.app_no
        record_app.record = self.record.record_no
        record_app.record_ref = self.record

        record_app.role = Constants.APPLICATION_ROLE_CREATES
        self.record.application_roles.append(record_app)

        try:
            self.__load_application_information()
            self.__populate_landtax_tab()
            self.__populate_archive_period_cbox()
            self.__setup_applicant_cbox()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        self.accept_button.setEnabled(False)

    def __populate_archive_period_cbox(self):

        self.time_period_cbox.clear()
        query = self.session.query(CtArchivedTaxAndPrice.valid_from, CtArchivedTaxAndPrice.valid_till).distinct(). \
            filter(CtArchivedTaxAndPrice.record == self.record.record_no).order_by(CtArchivedTaxAndPrice.valid_from)
        for valid_from, valid_till in query:
            self.time_period_cbox.addItem(str(valid_from) + ' to ' + str(valid_till), valid_from)

    @pyqtSlot(int)
    def on_time_period_cbox_currentIndexChanged(self, idx):

        self.archive_land_tax_twidget.clearContents()
        self.archive_land_tax_twidget.setRowCount(0)

        if idx == -1:
            return

        # read begin date from cbox
        begin_date = self.time_period_cbox.itemData(idx, Qt.UserRole)

        base_figures = self.session.query(CtArchivedTaxAndPrice.base_value_per_m2,
                                          CtArchivedTaxAndPrice.base_tax_rate,
                                          CtArchivedTaxAndPrice.subsidized_area,
                                          CtArchivedTaxAndPrice.subsidized_tax_rate).distinct(). \
            filter(CtArchivedTaxAndPrice.record == self.record.record_no). \
            filter(CtArchivedTaxAndPrice.valid_from == begin_date).one()

        self.archive_base_value_edit.setText('{0}'.format(base_figures.base_value_per_m2))
        self.archive_base_tax_rate_edit.setText('{0}'.format(base_figures.base_tax_rate))
        self.archive_subsidized_area_edit.setText('{0}'.format(base_figures.subsidized_area))
        self.archive_subsidized_tax_rate_edit.setText('{0}'.format(base_figures.subsidized_tax_rate))

        app_no = self.application_based_edit.text()
        if len(app_no) == 0:
            return
        app_no_count = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).count()
        if app_no_count == 0:
            return

        app = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
        owners = app.stakeholders.filter(CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE).all()
        if app_no[6:-9] == '02':
            owners = app.stakeholders.filter(CtApplicationPersonRole.role == Constants.REMAINING_OWNER_CODE).all()
        elif app_no[6:-9] == '14' or app_no[6:-9] == '15':
            owners = app.stakeholders.filter(CtApplicationPersonRole.role == Constants.NEW_RIGHT_HOLDER_CODE).all()
        row = 0
        for owner in owners:
            person = owner.person_ref
            tax_count = person.archived_taxes.filter(CtArchivedTaxAndPrice.record == self.record.record_no). \
                filter(CtArchivedTaxAndPrice.valid_from == begin_date).count()
            if tax_count > 0:
                self.archive_land_tax_twidget.setRowCount(row + 1)
                tax = person.archived_taxes.filter(CtArchivedTaxAndPrice.record == self.record.record_no). \
                    filter(CtArchivedTaxAndPrice.valid_from == begin_date).one()
                self.__add_archived_tax_row(row, person, tax)
                row += 1

        self.archive_land_tax_twidget.resizeColumnToContents(0)
        self.archive_land_tax_twidget.resizeColumnToContents(1)
        self.archive_land_tax_twidget.resizeColumnToContents(2)
        self.archive_land_tax_twidget.resizeColumnToContents(3)
        self.archive_land_tax_twidget.resizeColumnToContents(4)
        self.archive_land_tax_twidget.resizeColumnToContents(5)
        self.archive_land_tax_twidget.resizeColumnToContents(6)
        self.archive_land_tax_twidget.horizontalHeader().setResizeMode(7, QHeaderView.Stretch)

    def __add_archived_tax_row(self, row, person, tax):

        item = QTableWidgetItem(u'{0}, {1}'.format(person.name, person.first_name))
        item.setData(Qt.UserRole, person.person_id)
        self.__lock_item(item)
        self.archive_land_tax_twidget.setItem(row, OWNER_NAME, item)
        item = QTableWidgetItem(u'{0}'.format(person.person_id))
        self.__lock_item(item)
        self.archive_land_tax_twidget.setItem(row, OWNER_ID, item)
        item = QTableWidgetItem('{0}'.format(tax.share))
        self.__lock_item(item)
        self.archive_land_tax_twidget.setItem(row, OWNER_SHARE, item)
        item = QTableWidgetItem('{0}'.format(tax.area))
        self.__lock_item(item)
        self.archive_land_tax_twidget.setItem(row, OWNER_AREA, item)
        item = QTableWidgetItem('{0}'.format(tax.value_calculated))
        self.__lock_item(item)
        self.archive_land_tax_twidget.setItem(row, OWNER_VALUE_CALCULATED, item)
        item = QTableWidgetItem('{0}'.format(tax.price_paid))
        self.__lock_item(item)
        self.archive_land_tax_twidget.setItem(row, OWNER_PRICE_PAID, item)
        item = QTableWidgetItem('{0}'.format(tax.land_tax))
        self.__lock_item(item)
        self.archive_land_tax_twidget.setItem(row, OWNER_TAX, item)
        item = QTableWidgetItem('{0}'.format(tax.grace_period))
        self.__lock_item(item)
        self.archive_land_tax_twidget.setItem(row, OWNER_GRACE_PERIOD, item)
        payment_frequency = self.session.query(ClPaymentFrequency).get(tax.payment_frequency)
        item = QTableWidgetItem(u'{0}'.format(payment_frequency.description))
        self.__lock_item(item)
        self.archive_land_tax_twidget.setItem(row, OWNER_PAYMENT_FREQUENCY, item)

    def __populate_landtax_tab(self):

        self.landtax_message_label1.clear()
        self.landtax_message_label2.clear()

        self.land_tax_twidget.clearContents()
        self.land_tax_twidget.setRowCount(0)

        parcel_id = self.id_main_edit.text().strip()
        if len(parcel_id) == 0:
            self.landtax_message_label1.setText(self.tr('Without parcel no land tax information is available.'))
            return

        count = self.session.query(SetBaseTaxAndPrice).\
            filter(SetTaxAndPriceZone.geometry.ST_Contains(CaParcel.geometry)). \
            filter(CaParcel.parcel_id == parcel_id). \
            filter(SetBaseTaxAndPrice.tax_zone == SetTaxAndPriceZone.zone_id). \
            filter(SetBaseTaxAndPrice.landuse == CaParcel.landuse). \
            count()

        if count == 0:
            self.landtax_message_label1.setText(self.tr('No tax zone or base value found for the parcel.'))
            return

        base_tax_and_price = self.session.query(SetBaseTaxAndPrice).\
            filter(SetTaxAndPriceZone.geometry.ST_Contains(CaParcel.geometry)). \
            filter(CaParcel.parcel_id == parcel_id). \
            filter(SetBaseTaxAndPrice.tax_zone == SetTaxAndPriceZone.zone_id). \
            filter(SetBaseTaxAndPrice.landuse == CaParcel.landuse). \
            one()

        self.base_value_edit.setText('{0}'.format(base_tax_and_price.base_value_per_m2))
        self.base_tax_rate_edit.setText('{0}'.format(base_tax_and_price.base_tax_rate))
        self.subsidized_area_edit.setText('{0}'.format(base_tax_and_price.subsidized_area))
        self.subsidized_tax_rate_edit.setText('{0}'.format(base_tax_and_price.subsidized_tax_rate))

        app_no = self.application_based_edit.text()
        if len(app_no) == 0:
            return
        app_no_count = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).count()
        if app_no_count == 0:
            return

        app = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
        owners = app.stakeholders.filter(CtApplicationPersonRole.role == Constants.APPLICANT_ROLE_CODE).all()
        if app_no[6:-9] == '02':
            owners = app.stakeholders.filter(CtApplicationPersonRole.role == Constants.REMAINING_OWNER_CODE).all()
        elif app_no[6:-9] == '14' or app_no[6:-9] == '15':
            owners = app.stakeholders.filter(CtApplicationPersonRole.role == Constants.NEW_RIGHT_HOLDER_CODE).all()
        self.land_tax_twidget.setRowCount(len(owners))
        row = 0
        for owner in owners:
            person = owner.person_ref
            tax_count = person.taxes.filter(CtTaxAndPrice.record == self.record.record_no).count()
            if tax_count == 0:
                self.__add_tax_row(row, owner, parcel_id, base_tax_and_price.base_value_per_m2,
                                   base_tax_and_price.base_tax_rate,
                                   base_tax_and_price.subsidized_area, base_tax_and_price.subsidized_tax_rate)
            else:
                tax = person.taxes.filter(CtTaxAndPrice.record == self.record.record_no).one()
                self.__add_tax_row2(row, owner, tax)
            row += 1

        self.land_tax_twidget.resizeColumnToContents(0)
        self.land_tax_twidget.resizeColumnToContents(1)
        self.land_tax_twidget.resizeColumnToContents(2)
        self.land_tax_twidget.resizeColumnToContents(3)
        self.land_tax_twidget.resizeColumnToContents(4)
        self.land_tax_twidget.resizeColumnToContents(5)
        self.land_tax_twidget.resizeColumnToContents(6)
        self.land_tax_twidget.horizontalHeader().setResizeMode(7, QHeaderView.Stretch)

    def __set_up_land_tax_twidget(self):

        self.__set_up_twidget(self.land_tax_twidget)

        code_list = list()
        # In case of ownership annual payment is allowed only
        descriptions = self.session.query(ClPaymentFrequency.description).filter(ClPaymentFrequency.code == 10)\
            .order_by(ClPaymentFrequency.description)
        for description in descriptions:
            code_list.append(description[0])

        delegate = IntegerSpinBoxDelegate(OWNER_PRICE_PAID, 0, 1000000000, 0, 100, self.land_tax_twidget)
        self.land_tax_twidget.setItemDelegateForColumn(OWNER_PRICE_PAID, delegate)
        delegate = IntegerSpinBoxDelegate(OWNER_GRACE_PERIOD, 0, 120, 0, 5, self.land_tax_twidget)
        self.land_tax_twidget.setItemDelegateForColumn(OWNER_GRACE_PERIOD, delegate)
        delegate = ComboBoxDelegate(OWNER_PAYMENT_FREQUENCY, code_list, self.land_tax_twidget)
        self.land_tax_twidget.setItemDelegateForColumn(OWNER_PAYMENT_FREQUENCY, delegate)

    def __set_up_archive_land_tax_twidget(self):

        self.__set_up_twidget(self.archive_land_tax_twidget)

    def __set_up_twidget(self, table_widget):

        table_widget.setAlternatingRowColors(True)
        table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        table_widget.setSelectionMode(QTableWidget.SingleSelection)

    def __add_tax_row(self, row, owner, parcel_id, base_value_per_m2, base_tax_rate, subsidized_area, subsidized_tax_rate):

        # TODO: fix rounding issues
        parcel_area = self.session.query(CaParcel.area_m2).filter(CaParcel.parcel_id == parcel_id).one()[0]
        parcel_area = round(parcel_area)

        item = QTableWidgetItem(u'{0}, {1}'.format(owner.person_ref.name, owner.person_ref.first_name))
        item.setData(Qt.UserRole, owner.person_ref.person_id)
        self.land_tax_twidget.setItem(row, OWNER_NAME, item)
        item = QTableWidgetItem(u'{0}'.format(owner.person_ref.person_id))
        self.__lock_item(item)
        self.land_tax_twidget.setItem(row, OWNER_ID, item)
        item = QTableWidgetItem('{0}'.format(owner.share))
        self.__lock_item(item)
        self.land_tax_twidget.setItem(row, OWNER_SHARE, item)
        owner_area = int(round(float(owner.share) * parcel_area))
        item = QTableWidgetItem('{0}'.format(owner_area))
        self.__lock_item(item)
        self.land_tax_twidget.setItem(row, OWNER_AREA, item)

        value_calculated = owner_area * base_value_per_m2
        # owner_subsidized_area = int(round(float(owner.share) * subsidized_area))
        # tax_subsidized = owner_subsidized_area * base_value_per_m2 * (float(base_tax_rate) / 100) \
        #     * (float(subsidized_tax_rate) / 100)
        # tax_standard = (owner_area - owner_subsidized_area) * base_value_per_m2 * (float(base_tax_rate) / 100)
        # tax_calculated = int(round(tax_subsidized if tax_standard < 0 else tax_subsidized + tax_standard))
        tax_calculated = ((float(value_calculated) * float(base_tax_rate / 100) * float((100-subsidized_tax_rate) / 100)))

        item = QTableWidgetItem('{0}'.format(value_calculated))
        self.__lock_item(item)
        self.land_tax_twidget.setItem(row, OWNER_VALUE_CALCULATED, item)
        item = QTableWidgetItem('{0}'.format(value_calculated))
        self.land_tax_twidget.setItem(row, OWNER_PRICE_PAID, item)
        item = QTableWidgetItem('{0}'.format(tax_calculated))
        self.__lock_item(item)
        self.land_tax_twidget.setItem(row, OWNER_TAX, item)
        item = QTableWidgetItem('{0}'.format(10))
        self.land_tax_twidget.setItem(row, OWNER_GRACE_PERIOD, item)
        payment_frequency = self.session.query(ClPaymentFrequency).get(10)
        item = QTableWidgetItem(u'{0}'.format(payment_frequency.description))
        self.land_tax_twidget.setItem(row, OWNER_PAYMENT_FREQUENCY, item)

    def __lock_item(self, item):

        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def __add_tax_row2(self, row, owner, tax):

        item = QTableWidgetItem(u'{0}, {1}'.format(owner.person_ref.name, owner.person_ref.first_name))
        item.setData(Qt.UserRole, owner.person_ref.person_id)
        self.__lock_item(item)
        self.land_tax_twidget.setItem(row, OWNER_NAME, item)
        item = QTableWidgetItem(u'{0}'.format(owner.person_ref.person_id))
        self.__lock_item(item)
        self.land_tax_twidget.setItem(row, OWNER_ID, item)
        item = QTableWidgetItem('{0}'.format(tax.share))
        self.__lock_item(item)
        self.land_tax_twidget.setItem(row, OWNER_SHARE, item)
        item = QTableWidgetItem('{0}'.format(tax.area))
        self.__lock_item(item)
        self.land_tax_twidget.setItem(row, OWNER_AREA, item)
        item = QTableWidgetItem('{0}'.format(tax.value_calculated))
        self.__lock_item(item)
        self.land_tax_twidget.setItem(row, OWNER_VALUE_CALCULATED, item)
        item = QTableWidgetItem('{0}'.format(tax.price_paid))
        self.__lock_item(item)
        self.land_tax_twidget.setItem(row, OWNER_PRICE_PAID, item)
        item = QTableWidgetItem('{0}'.format(tax.land_tax))
        self.__lock_item(item)
        self.land_tax_twidget.setItem(row, OWNER_TAX, item)
        item = QTableWidgetItem('{0}'.format(tax.grace_period))
        self.__lock_item(item)
        self.land_tax_twidget.setItem(row, OWNER_GRACE_PERIOD, item)
        payment_frequency = self.session.query(ClPaymentFrequency).get(tax.payment_frequency)
        item = QTableWidgetItem(u'{0}'.format(payment_frequency.description))
        self.land_tax_twidget.setItem(row, OWNER_PAYMENT_FREQUENCY, item)

    def __load_application_information(self):

        # parcel infos:
        application_role = self.record.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CREATES).one()
        application = application_role.application_ref
        parcel = application.parcel_ref

        self.id_main_edit.setText(parcel.parcel_id)
        self.old_id_edit.setText(parcel.old_parcel_id)
        self.geo_id_edit.setText(parcel.geo_id)
        if parcel.landuse_ref is not None:
            self.land_use_type_edit.setText(parcel.landuse_ref.description)

        self.calculated_area_edit.setText(str(parcel.area_m2))
        if parcel.documented_area_m2 == None:
            self.documented_area_edit.setText("")
        else:
            self.documented_area_edit.setText(str(parcel.documented_area_m2))

        aimag = application.app_no[:3]
        soum = application.app_no[:5]

        try:
            aimag_name = self.session.query(AuLevel1.name).filter(AuLevel1.code == aimag).one()
            soum_name = self.session.query(AuLevel2.name).filter(AuLevel2.code == soum).one()

            self.aimag_edit.setText(aimag_name[0])
            self.soum_edit.setText(soum_name[0])

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        self.khashaa_edit.setText(parcel.address_khashaa)
        self.street_name_edit.setText(parcel.address_streetname)
        self.bag_edit.setText(parcel.address_neighbourhood)

        #decision date
        if not application.app_type in Constants.RECORD_WITHOUT_DECISION:
            last_decision = self.session.query(CtDecision).join(CtApplication.decision_result)\
                                .join(CtDecisionApplication.decision_ref)\
                                .filter(CtApplication.app_no == application.app_no)\
                                .filter(CtDecisionApplication.decision_result == Constants.DECISION_RESULT_APPROVED)\
                                .one()

            qt_date = PluginUtils.convert_python_date_to_qt(last_decision.decision_date)
            if qt_date is not None:
                self.ownership_begin_edit.setDate(qt_date)
                self.ownership_begin_edit.setEnabled(False)

    def __copy_record_from_navigator(self):

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
                                        self.tr("The selected Application {0} is not within the working soum. "
                                                "\n \n Change the Working soum to create a new "
                                                "application for the parcel.").format(current_app_no))
                return

            application = self.session.query(CtApplication).filter_by(app_no=current_app_no).one()

            if not self.__validate_application(application):
                return

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"),
                                   self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        self.found_edit.setText(application.app_no)

    def __validate_application(self, application):

        try:
            app_contract_count = application.records.count()
            if app_contract_count > 0:
                PluginUtils.show_error(self, self.tr("Application Error"),
                                       self.tr("This application with owner record."))
                return False

            if application.app_type not in Constants.RECORD_WITHOUT_DECISION:
                highest_status = self.session.query(CtApplicationStatus.status)\
                                        .filter(CtApplicationStatus.application == application.app_no)\
                                        .order_by(CtApplicationStatus.status.desc()).first()
                if highest_status <= Constants.APP_STATUS_SEND:
                    PluginUtils.show_error(self, self.tr("Application Error"),
                                           self.tr("It is not allowed to add an application without a status > 5."))
                    return False

            if application.app_type not in Constants.RECORD_WITHOUT_DECISION:
                last_decision_count = self.session.query(CtDecision).join(CtApplication.decision_result)\
                                            .filter(CtApplication.app_no == application.app_no)\
                                            .order_by(CtDecision.decision_date.desc()).count()
                if last_decision_count == 0:
                    PluginUtils.show_error(self, self.tr("Application Error"),
                                           self.tr("It is not allowed to add an application without decision."))
                    return False

                last_decision_count = self.session.query(CtDecision).join(CtApplication.decision_result)\
                    .join(CtDecisionApplication.decision_ref)\
                    .filter(CtApplication.app_no == application.app_no)\
                    .filter(CtDecisionApplication.decision_result == Constants.DECISION_RESULT_APPROVED).count()

                if last_decision_count == 0:
                    PluginUtils.show_error(self, self.tr("Application Error"),
                                           self.tr("There is no approved decision result for this application."))
                    return False

            if application.app_type not in Constants.RECORD_TYPES:
                PluginUtils.show_error(self, self.tr("Application Error"),
                                       self.tr("The application doesn't create an ownership record. "
                                               "It's not allowed to add it to the ownership record."))
                return False

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return False

        #check that there is a parcel for this application
        if application.parcel is None:
            PluginUtils.show_error(self, self.tr("Application Error"),
                                   self.tr("It is not allowed to add applications without assigned parcel."))
            return False

        return True

    def __generate_record_number(self):

        try:
            record_number_filter = "%-{0}/%".format(str(QDate.currentDate().toString("yyyy")))

            count = self.session.query(CtOwnershipRecord).filter(CtOwnershipRecord.record_no != str(self.record.record_no)) \
                        .filter(CtOwnershipRecord.record_no.like("%-%"))\
                        .filter(CtOwnershipRecord.record_no.like(record_number_filter))  \
                        .order_by(func.substr(CtOwnershipRecord.record_no, 10, 16).desc()).count()
            if count == 0:
                cu_max_number = "00001"

            else:
                cu_max_number = self.session.query(CtOwnershipRecord.record_no)\
                                    .filter(CtOwnershipRecord.record_no != str(self.record.record_no)) \
                                    .filter(CtOwnershipRecord.record_no.like("%-%"))\
                                    .filter(CtOwnershipRecord.record_no.like(record_number_filter))  \
                                    .order_by(func.substr(CtOwnershipRecord.record_no, 10, 16).desc()).first()

                cu_max_number = cu_max_number[0]
                minus_split_number = cu_max_number.split("-")
                slash_split_number = minus_split_number[1].split("/")
                cu_max_number = int(slash_split_number[1]) + 1

            soum = DatabaseUtils.current_working_soum_schema()
            year = QDate.currentDate().toString("yyyy")
            number = soum + "-" + year + "/" + str(cu_max_number).zfill(5)

            self.record_number_edit.setText(number)
            self.record.record_no = number

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __record_status(self):

        if self.draft_rbutton.isChecked():
            return Constants.RECORD_STATUS_DRAFT
        elif self.active_rbutton.isChecked():
            return Constants.RECORD_STATUS_ACTIVE
        elif self.cancelled_rbutton.isChecked():
            return Constants.RECORD_STATUS_CANCELLED

    def __record_right_type(self):

        if self.advanced_right_rbutton.isChecked():
            return Constants.ADVANCED_RIGHT_TYPE
        else:
            return Constants.STANDARD_RIGHT_TYPE

    def __save_cancellation_app(self):

        self.create_savepoint()

        try:
            self.record.cancellation_reason = None
            cancel_count = self.record.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CANCELS).count()

            if cancel_count > 0:
                #update
                cancellation_app = self.record.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CANCELS).one()
                cancellation_app.application = self.app_number_cbox.currentText()
            else:
                #insert
                record_app = CtRecordApplicationRole()
                record_app.application = self.app_number_cbox.currentText()
                record_app.record = self.record.record_no
                record_app.role = Constants.APP_ROLE_CANCEL
                self.record.application_roles.append(record_app)

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __save_other_reason(self):

        self.create_savepoint()

        try:

            cancel_count = self.record.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CANCELS).count()
            if cancel_count > 0:
                self.record.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CANCELS).delete()
            self.record.cancellation_reason = self.other_reason_cbox.itemData(self.other_reason_cbox.currentIndex())

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

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

    def __save_taxes(self):

        self.create_savepoint()

        try:
            for row in range(self.land_tax_twidget.rowCount()):
                new_row = False
                owner_id = self.land_tax_twidget.item(row, OWNER_NAME).data(Qt.UserRole)
                owner = self.session.query(BsPerson).get(owner_id)
                tax_count = owner.taxes.filter(CtTaxAndPrice.record == self.record.record_no).count()
                if tax_count == 0:
                    new_row = True
                    tax = CtTaxAndPrice(record=self.record.record_no)
                else:
                    tax = owner.taxes.filter(CtTaxAndPrice.record == self.record.record_no).one()

                tax.share = float(self.land_tax_twidget.item(row, OWNER_SHARE).text())
                tax.area = int(self.land_tax_twidget.item(row, OWNER_AREA).text())
                tax.value_calculated = int(self.land_tax_twidget.item(row, OWNER_VALUE_CALCULATED).text())
                tax.price_paid = int(self.land_tax_twidget.item(row, OWNER_PRICE_PAID).text())
                tax.land_tax = float(self.land_tax_twidget.item(row, OWNER_TAX).text())
                tax.grace_period = int(self.land_tax_twidget.item(row, OWNER_GRACE_PERIOD).text())
                tax.base_value_per_m2 = int(self.base_value_edit.text())
                tax.base_tax_rate = float(self.base_tax_rate_edit.text())

                if not self.subsidized_area_edit.text():
                    tax.subsidized_area = int(self.subsidized_area_edit.text())
                else:
                    tax.subsidized_area = 0
                tax.subsidized_tax_rate = float(self.subsidized_tax_rate_edit.text())
                payment_frequency_desc = self.land_tax_twidget.item(row, OWNER_PAYMENT_FREQUENCY).text()
                payment_frequency = self.session.query(ClPaymentFrequency). \
                    filter(ClPaymentFrequency.description == payment_frequency_desc).one()
                tax.payment_frequency = payment_frequency.code

                if new_row:
                    owner.taxes.append(tax)

            self.__populate_landtax_tab()

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def reject(self):

        self.rollback()
        QDialog.reject(self)

    @pyqtSlot(int)
    def on_cancellation_date_check_box_stateChanged(self, state):

        if state == Qt.Checked:
            self.ownership_end_date.setEnabled(True)
            self.application_based_rbutton.setEnabled(True)
            self.other_reason_rbutton.setEnabled(True)
            self.app_number_cbox.setEnabled(True)
            self.application_type_edit.setEnabled(True)
        else:
            self.ownership_end_date.setEnabled(False)
            self.application_based_rbutton.setEnabled(False)
            self.other_reason_rbutton.setEnabled(False)
            self.app_number_cbox.setEnabled(False)
            self.application_type_edit.setEnabled(False)

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
                PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return
        else:
            self.app_number_cbox.setEnabled(False)
            self.other_reason_cbox.setEnabled(True)
            self.type_edit.setText("")

    @pyqtSlot(int)
    def on_app_number_cbox_currentIndexChanged(self, current_index):

        if self.app_number_cbox.currentIndex() == -1:
            return

        try:
            app_number = self.app_number_cbox.itemText(current_index)
            if self.application_based_edit.text():
                current_application_creates = self.record.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CREATES).one()
                if current_application_creates.application_ref.app_no == app_number:
                    PluginUtils.show_error(self, self.tr("Error"), self.tr("The application that creates the record, can't cancel it."))
                    self.app_number_cbox.setCurrentIndex(-1)
                    return

            app = self.session.query(CtApplication).filter(CtApplication.app_no == app_number).one()
            self.type_edit.setText(app.app_type_ref.description)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    def __save_settings(self):

        try:

            self.__save_record()
            self.__save_taxes()
            return True

        except LM2Exception, e:
            PluginUtils.show_error(self, e.title(), e.message())

    def __validate_settings(self):

        return True

    @pyqtSlot()
    def on_apply_button_clicked(self):

        if not self.__validate_settings():
            return

        if not self.__save_settings():
            return

        user = DatabaseUtils.current_user()
        officers = self.session.query(SetRole) \
            .filter(SetRole.user_name == user.user_name) \
            .filter(SetRole.is_active == True).one()

        app_status9_count = self.session.query(CtApplicationStatus)\
            .filter(CtApplicationStatus.application == self.application_based_edit.text())\
            .filter(CtApplicationStatus.status == 9).count()
        if self.active_rbutton.isChecked() and app_status9_count == 0:
            new_status = CtApplicationStatus()
            new_status.application = self.application_based_edit.text()
            new_status.next_officer_in_charge = officers.user_name_real
            new_status.officer_in_charge = officers.user_name_real
            new_status.status = 9
            new_status.status_date = self.record.record_date
            self.session.add(new_status)

        self.commit()
        self.__start_fade_out_timer()

    def __save_record(self):

        self.create_savepoint()

        if self.record.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CREATES).count() == 0:
            PluginUtils.show_error(self, self.tr("Error saving ownership record"), self.tr("It is not allowed to save a "
                                                                                   "record without an assigned application."))
            return
        # try:

        self.record.status = self.__record_status()
        self.record.right_type = self.__record_right_type()

        if self.cancellation_date_check_box.isChecked():

            self.record.cancellation_date = PluginUtils.convert_qt_date_to_python(self.ownership_end_date.date())

            if self.application_based_rbutton.isChecked():
                self.__save_cancellation_app()
            else:
                self.__save_other_reason()

        self.record.record_begin = PluginUtils.convert_qt_date_to_python(self.ownership_begin_edit.date())
        self.record.record_date = PluginUtils.convert_qt_date_to_python(self.record_date_date.date())
        certificate_no = 0
        a = self.certificate_number_edit.text()
        if a.isdigit():
            certificate_no = int(self.certificate_number_edit.text())
        self.record.certificate_no = certificate_no
        self.commit()

        # except SQLAlchemyError, e:
        #     self.rollback_to_savepoint()
        #     raise LM2Exception(self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
        #     return

        self.__start_fade_out_timer()

    @pyqtSlot()
    def on_unassign_button_clicked(self):

        self.application_based_edit.setText("")
        self.application_type_edit.setText("")
        self.id_main_edit.setText("")
        self.old_id_edit.setText("")
        self.geo_id_edit.setText("")
        self.land_use_type_edit.setText("")
        self.calculated_area_edit.setText("")
        self.documented_area_edit.setText("")
        self.aimag_edit.setText("")
        self.soum_edit.setText("")
        self.bag_edit.setText("")
        self.street_name_edit.setText("")
        self.khashaa_edit.setText("")

        try:
            self.record.application_roles.filter_by(role=Constants.APPLICATION_ROLE_CREATES).delete()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        self.accept_button.setEnabled(True)

    @pyqtSlot()
    def on_search_button_clicked(self):

        if not self.enter_application_edit.text():
            return

        try:
            app_no = self.enter_application_edit.text()
            count = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).count()
            if count == 1:
                application = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()

                if not self.__validate_application(application):
                    return

                self.found_edit.setText(application.app_no)
                self.enter_application_edit.setText("")
            else:
                PluginUtils.show_error(self, self.tr("Database Error"), self.tr("Found multiple applications for the number {0}.").format(app_no))

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

    @pyqtSlot()
    def on_land_tax_summary_button_clicked(self):

        current_file = os.path.dirname(__file__) + "/.." + "/pentaho/record_land_tax_summary.prpt"
        QDesktopServices.openUrl(QUrl.fromLocalFile(current_file))

    @pyqtSlot()
    def on_help_button_clicked(self):

        if self.tabWidget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/ownership_Records.htm")
        elif self.tabWidget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/ownership_parcel.htm")
        elif self.tabWidget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/ownership_details.htm")
        elif self.tabWidget.currentIndex() == 3:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/ownership_land_tax.htm")
        elif self.tabWidget.currentIndex() == 4:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/land_tax_history.htm")
        elif self.tabWidget.currentIndex() == 5:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/ownerhsip_documents.htm")
        elif self.tabWidget.currentIndex() == 6:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/ownerhsip_application%20documents.htm")
        elif self.tabWidget.currentIndex() == 7:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/ownerhsip_history.htm")

    def current_create_application(self):

        try:
            rec_app_roles = self.record.application_roles\
                    .filter(CtRecordApplicationRole.role == Constants.APPLICATION_ROLE_CREATES).one()

        except LM2Exception, e:
                PluginUtils.show_error(self, e.title(), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

        return rec_app_roles.application_ref

    @pyqtSlot(int)
    def on_applicant_documents_cbox_currentIndexChanged(self, index):

        if not self.app_doc_twidget:
            return

        if self.updating:
            return

        self.__update_app_documents_twidget()

    def current_document_applicant(self):

        applicant = self.applicant_documents_cbox.itemData(self.applicant_documents_cbox.currentIndex())
        return applicant

    def current_parent_object(self):

        return self.record

    def current_parent_object_no(self):

        return self.record_number_edit.text()

    @pyqtSlot(str)
    def on_person_id_edit_textChanged(self, text):

        self.app_number_cbox.clear()
        value = "%" + text + "%"

        application = self.session.query(CtApplication)\
            .join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application)\
            .join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id)\
            .filter(or_(CtApplication.app_type == 2,CtApplication.app_type == 4,CtApplication.app_type == 5,CtApplication.app_type == 9,\
                            CtApplication.app_type == 14,CtApplication.app_type == 15,CtApplication.app_type == 16,CtApplication.app_type == 20))\
            .filter(BsPerson.person_id.ilike(value)).all()

        for app in application:
            self.app_no = app.app_no
            self.app_number_cbox.addItem(self.app_no, self.app_no)