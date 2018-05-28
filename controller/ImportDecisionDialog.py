import os
# coding=utf8

__author__ = 'anna'

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_, and_, desc
from xlrd import open_workbook
from datetime import date
from inspect import currentframe
from ..view.Ui_ImportDecisionDialog import *
from ..model.CtApplicationStatus import *
from ..model.DatabaseHelper import *
from ..model.AuLevel2 import *
from ..model.CtDecision import *
from ..model.CtDecisionDocument import *
from ..model.CtDocument import *
from ..model.CtApplication import *
from ..model.LM2Exception import LM2Exception
from ..model.CtDecisionApplication import *
from ..model.ClLanduseType import *
from ..model.ClRightType import *
from ..model.SetRightTypeApplicationType import *
from ..model import Constants
from ..model import SettingsConstants
from ..model.Enumerations import UserRight
from ..model.CaMaintenanceCase import CaMaintenanceCase
from ..model.BsPerson import *
from ..model.SetRole import SetRole
from ..model.CaBuilding import *
from ..model.Enumerations import ApplicationType
from .DecisionErrorDialog import DecisionErrorDialog
from ..utils.SessionHandler import SessionHandler
from ..utils.PluginUtils import PluginUtils
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.FileUtils import FileUtils
from ..controller.NavigatorWidget import *
from ..model.ApplicationSearchDecision import *
from ..model import SettingsConstants
from ..utils.FilePath import *
import xlsxwriter
import shutil

class ImportDecisionDialog(QDialog, Ui_ImportDecisionDialog, DatabaseHelper):

    def __init__(self, attribute_update, decision=None, parent=None):

        super(ImportDecisionDialog, self).__init__(parent)
        DatabaseHelper.__init__(self)

        self.setupUi(self)
        self.attribute_update = attribute_update
        self.decision = decision
        self.error_list = {}
        self.timer = None
        user = DatabaseUtils.current_user()
        self.original_pa_from = user.pa_from

        self.setWindowTitle(self.tr("Import Decisions Dialog"))
        self.session = SessionHandler().session_instance()

        self.__setup_combo_boxes()
        self.__setup_tree_widget()
        self.app_no = ''
        self.contract_date.setDate(QDate.currentDate())
        self.close_button.clicked.connect(self.reject)

        if self.attribute_update:
            self.select_file_button.setEnabled(False)
            self.import_button.setText(self.tr("Apply"))
            self.__setup_mapping()

        self.__setup_permissions()
        self.__populate_application()
        self.__populate_combobox()
        self.app_type_code = None
        self.is_tmp_parcel = False
        self.add_document_button.setEnabled(False)
        self.delete_document_button.setEnabled(False)
        self.view_document_button.setEnabled(False)

    def __setup_permissions(self):

        user_name = QSettings().value(SettingsConstants.USER)
        user_rights = DatabaseUtils.userright_by_name(user_name)

        if UserRight.contracting_update in user_rights:
            self.import_button.setEnabled(True)
            self.select_file_button.setEnabled(True)
            self.documents_groupbox.setEnabled(True)

        else:
            self.import_button.setEnabled(False)
            self.select_file_button.setEnabled(False)
            self.documents_groupbox.setEnabled(False)

    def __setup_mapping(self):

        if self.decision.decision_level == 70:
            self.seller_buyer_checkbox.setChecked(True)
            for decision_doc in self.decision.documents:

                item = QListWidgetItem(decision_doc.document_ref.name, self.document_twidget)
                item.setData(Qt.UserRole, decision_doc)
            for result in self.decision.results:
                self.application_cbox.addItem(result.application, result.application)
            self.contract_date.setDate(self.decision.decision_date)
            self.level_cbox.setCurrentIndex(self.level_cbox.findData(self.decision.decision_level))
            self.notary_number_edit.setDisabled(True)
            self.contract_id_edit.setDisabled(True)
            self.notary_decision_edit.setText(self.decision.decision_no)
            self.decision_save_button.setDisabled(True)
        else:
            for result in self.decision.results:

                item = QTreeWidgetItem()
                item.setText(0, result.application)
                if result.decision_result == Constants.DECISION_RESULT_APPROVED:
                    self.item_approved.addChild(item)
                else:
                    self.item_refused.addChild(item)

            for decision_doc in self.decision.documents:

                item = QListWidgetItem(decision_doc.document_ref.name, self.document_twidget)
                item.setData(Qt.UserRole, decision_doc)

            self.decision_date_edit.setText(self.decision.decision_date.strftime(Constants.PYTHON_DATE_FORMAT))
            self.decision_no_edit.setText(self.decision.decision_no)
            self.level_cbox.setCurrentIndex(self.level_cbox.findData(self.decision.decision_level))
            self.import_by_edit.setText(self.decision.imported_by)
        self.add_document_button.setEnabled(True)
        self.load_document_button.setEnabled(True)
        self.delete_document_button.setEnabled(True)
        self.view_document_button.setEnabled(True)

    def __setup_tree_widget(self):

        self.item_approved = QTreeWidgetItem()
        self.item_approved.setText(0, self.tr("Approved"))
        self.item_approved.setData(0, Qt.UserRole, Constants.DECISION_RESULT_REFUSED)

        self.item_refused = QTreeWidgetItem()
        self.item_refused.setText(0, self.tr("Refused"))
        self.item_refused.setData(0, Qt.UserRole, Constants.DECISION_RESULT_REFUSED)

        self.item_skipped = QTreeWidgetItem()
        self.item_skipped.setText(0, self.tr("Skipped"))
        self.item_skipped.setData(0, Qt.UserRole, -1)

        self.result_tree_widget.addTopLevelItem(self.item_approved)
        self.result_tree_widget.addTopLevelItem(self.item_refused)
        self.result_tree_widget.addTopLevelItem(self.item_skipped)

    def __setup_combo_boxes(self):

        try:
            levels = self.session.query(ClDecisionLevel.code, ClDecisionLevel.description).all()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        for code, description in levels:
            self.level_cbox.addItem(description, code)

    @pyqtSlot()
    def on_select_file_button_clicked(self):

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

        file_dialog = QFileDialog()
        file_dialog.setFilter(self.tr("Excel Files (*.xlsx)"))
        file_dialog.setModal(True)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setDirectory(default_path)
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            file_name = QFileInfo(selected_file).filePath()
            self.decision_file_edit.setText(file_name)
            self.import_button.setEnabled(True)
            self.__read_xls_file()

    def __read_xls_file(self):

        file_name = self.decision_file_edit.text()
        if file_name == "":
            PluginUtils.show_message(self, self.tr("File operation"), self.tr("Please select a file."))
            return

        if not QFileInfo(file_name).exists():
            PluginUtils.show_message(self, self.tr("File operation"), self.tr("Invalid file."))
            return

        work_book = open_workbook(file_name)

        decision_no_column = -1
        decision_date_column = -1
        decision_level_column = -1
        decision_column = -1
        application_no_column = -1
        application_duration_column = -1
        landuse_column = -1

        for s in work_book.sheets():
            for row in range(1):
                for col in range(s.ncols):
                    if s.cell(row, col).value == Constants.DECISION_COLUMN_NAME:
                        decision_column = col
                    elif s.cell(row, col).value == Constants.DECISION_NO_COLUMN_NAME:
                        decision_no_column = col
                    elif s.cell(row, col).value == Constants.DECISION_DATE_COLUMN_NAME:
                        decision_date_column = col
                    elif s.cell(row, col).value == Constants.DECISION_LEVEL_COLUMN_NAME:
                        decision_level_column = col
                    elif s.cell(row, col).value == Constants.APPLICATION_NO_COLUMN_NAME:
                        application_no_column = col
                    elif s.cell(row, col).value == Constants.APPROVED_DURATION_COLUMN_NAME:
                        application_duration_column = col
                    elif s.cell(row, col).value == Constants.LANDUSE_COLUMN_NAME:
                        landuse_column = col

        # check: if any column wasn't found -> exit
        if decision_no_column == -1 \
                or decision_date_column == -1 \
                or decision_level_column == -1 \
                or decision_column == -1 \
                or application_no_column == -1 \
                or landuse_column == -1 \
                or application_duration_column == -1:

            PluginUtils.show_message(self, self.tr("Error in Excel file"),
                                     self.tr(u"The Excel file doesn't contain the following columns: \n "
                                             u"{0}, {1}, {2}, {3}, {4}, {5}, {6}").format(Constants.DECISION_COLUMN_NAME,
                                             Constants.DECISION_NO_COLUMN_NAME, Constants.DECISION_DATE_COLUMN_NAME,
                                             Constants.APPLICATION_NO_COLUMN_NAME, Constants.DECISION_LEVEL_COLUMN_NAME,
                                             Constants.APPROVED_DURATION_COLUMN_NAME, Constants.LANDUSE_COLUMN_NAME))

            self.error_list["Excel"] = self.tr(u"The Excel file doesn't contain the following columns: \n "
                                             u"{0}, {1}, {2}, {3}, {4}, {5}, {6}").format(Constants.DECISION_COLUMN_NAME,
                                             Constants.DECISION_NO_COLUMN_NAME, Constants.DECISION_DATE_COLUMN_NAME,
                                             Constants.APPLICATION_NO_COLUMN_NAME, Constants.DECISION_LEVEL_COLUMN_NAME,
                                             Constants.APPROVED_DURATION_COLUMN_NAME, Constants.LANDUSE_COLUMN_NAME)

            return

        user = DatabaseUtils.current_user()
        current_employee = self.session.query(SetRole) \
            .filter(SetRole.user_name == user.user_name)\
            .filter(SetRole.is_active == True).one()
        self.import_by_edit.setText(current_employee.user_name_real)

        s = work_book.sheets()[0]

        self.create_savepoint()
        maintenance_cases = []

        try:
            first_date = str(s.cell(1, decision_date_column).value)
            decision_no = s.cell(1, decision_no_column).value
            decision_level = s.cell(1, decision_level_column).value

            if not self.__validate_decision_attributes(first_date, decision_no, decision_level):
                self.import_button.setEnabled(False)
                self.add_document_button.setEnabled(False)
                self.load_document_button.setEnabled(False)
                self.delete_document_button.setEnabled(False)
                self.view_document_button.setEnabled(False)

                return

            user = DatabaseUtils.current_user()
            current_employee = self.session.query(SetRole) \
                .filter(SetRole.user_name == user.user_name) \
                .filter(SetRole.is_active == True).one()

            self.decision = CtDecision()
            self.decision.decision_date = s.cell(1, decision_date_column).value
            self.decision.decision_no = s.cell(1, decision_no_column).value
            self.decision.decision_level = s.cell(1, decision_level_column).value
            self.decision.imported_by = current_employee.user_name_real

            self.decision_no_edit.setText(self.decision.decision_no)
            self.decision_date_edit.setText(str(self.decision.decision_date))
            self.level_cbox.setCurrentIndex(self.level_cbox.findData(self.decision.decision_level))

            parcel_ids = {}

            for row in range(1, s.nrows):

                decision_result = s.cell(row, decision_column).value
                app_no = s.cell(row, application_no_column).value
                current_decision_no = s.cell(row, decision_no_column).value
                duration = s.cell(1, application_duration_column).value
                landuse = s.cell(row, landuse_column).value

                if not self.__validate_row(decision_result, app_no, current_decision_no, self.decision.decision_no,
                                           duration, landuse):
                    item = QTreeWidgetItem()
                    item.setText(0, app_no)
                    self.item_skipped.addChild(item)
                    self.import_button.setEnabled(False)
                    self.error_details_button.setEnabled(True)
                    continue

                decision_app = CtDecisionApplication()
                decision_app.decision_result = decision_result
                decision_app.application = app_no
                self.decision.results.append(decision_app)

                application = self.session.query(CtApplication).filter_by(app_no=app_no).one()
                application_result_exists = False
                application.approved_landuse = landuse
                current_app_type = application.app_type
                parcel_count = self.session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == application.tmp_parcel).count()
                if parcel_count != 0:
                    self.is_tmp_parcel = True

                if self.is_tmp_parcel:

                    parcel = self.session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == application.tmp_parcel).one()
                    tmp_parcel_id = parcel.parcel_id
                    maintenance_case_id = parcel.maintenance_case

                    parcel.landuse = landuse
                    self.__write_changes(maintenance_case_id, tmp_parcel_id, app_no)
                    if decision_app.decision_result == Constants.DECISION_RESULT_APPROVED:

                        if parcel.parcel_id in parcel_ids.values() and application.app_type in parcel_ids.keys():
                            PluginUtils.show_error(self, self.tr("Import error"),
                                                   self.tr("There are two approved applications of the same type for the parcel {0}. ").format(parcel.parcel_id))

                            item = QTreeWidgetItem()
                            item.setText(0, app_no)
                            self.item_skipped.addChild(item)
                            self.import_button.setEnabled(False)
                            self.error_details_button.setEnabled(True)
                            self.error_list[app_no + " # " + str(count)] = self.tr("There are two approved applications of the same type for the parcel {0}. ").format(parcel.parcel_id)
                            continue
                        if application.app_type != ApplicationType.transfer_possession_right \
                                and application.app_type != ApplicationType.possession_right_use_right \
                                and application.app_type != ApplicationType.change_ownership:

                            parcel_ids[application.app_type] = parcel.parcel_id

                        count = application.statuses\
                            .filter(CtApplicationStatus.status == Constants.APP_STATUS_APPROVED).count()
                        if count > 0:
                            application_result_exists = True
                    else:
                        count = application.statuses\
                            .filter(CtApplicationStatus.status == Constants.APP_STATUS_REFUSED).count()
                        if count > 0:
                            application_result_exists = True

                    if not application_result_exists:

                        app_status = CtApplicationStatus()
                        user = DatabaseUtils.current_user()
                        app_status.next_officer_in_charge = current_employee.user_name_real
                        app_status.officer_in_charge = current_employee.user_name_real
                        app_status.application = app_no
                        app_status.status_date = self.decision.decision_date

                        if decision_app.decision_result == Constants.DECISION_RESULT_APPROVED or decision_app.decision_result == '10':
                            app_status.status = Constants.APP_STATUS_APPROVED
                        else:
                            app_status.status = Constants.APP_STATUS_REFUSED

                            #rollback: set date of parcel that isn't approved to NULL
                            #set valid_till of parcels back to infinity
                            application = self.session.query(CtApplication).get(app_no)
                            if application.maintenance_case not in maintenance_cases and application.maintenance_case is not None:
                                maintenance_cases.append(application.maintenance_case)

                        self.session.add(app_status)

                    if application.app_type in Constants.APPLICATION_TYPE_WITH_DURATION:
                        approved_duration = int(duration)
                        application.approved_duration = approved_duration

                    item = QTreeWidgetItem()
                    item.setText(0, decision_app.application)
                    if int(decision_app.decision_result) == int(Constants.DECISION_RESULT_APPROVED):
                        self.item_approved.addChild(item)
                    else:
                        self.item_refused.addChild(item)
                else:
                    parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == application.parcel).one()
                    parcel.landuse = landuse

                    if decision_app.decision_result == Constants.DECISION_RESULT_APPROVED:

                        if parcel.parcel_id in parcel_ids.values() and application.app_type in parcel_ids.keys():

                            PluginUtils.show_error(self, self.tr("Import error"),
                                                   self.tr("There are two approved applications of the same type for the parcel {0}. ").format(parcel.parcel_id))

                            item = QTreeWidgetItem()
                            item.setText(0, app_no)
                            self.item_skipped.addChild(item)
                            self.import_button.setEnabled(False)
                            self.error_details_button.setEnabled(True)
                            self.error_list[app_no + " # " + str(count)] = self.tr("There are two approved applications of the same type for the parcel {0}. ").format(parcel.parcel_id)
                            continue

                        if application.app_type != ApplicationType.transfer_possession_right \
                                and application.app_type != ApplicationType.possession_right_use_right \
                                and application.app_type != ApplicationType.change_ownership:

                            parcel_ids[application.app_type] = parcel.parcel_id

                        count = application.statuses\
                            .filter(CtApplicationStatus.status == Constants.APP_STATUS_APPROVED).count()
                        if count > 0:
                            application_result_exists = True
                    else:
                        count = application.statuses\
                            .filter(CtApplicationStatus.status == Constants.APP_STATUS_REFUSED).count()
                        if count > 0:
                            application_result_exists = True

                    if not application_result_exists:

                        app_status = CtApplicationStatus()
                        user = DatabaseUtils.current_user()
                        app_status.next_officer_in_charge = current_employee.user_name_real
                        app_status.officer_in_charge = current_employee.user_name_real
                        app_status.application = app_no
                        app_status.status_date = self.decision.decision_date

                        if decision_app.decision_result == Constants.DECISION_RESULT_APPROVED or decision_app.decision_result == '10':
                            app_status.status = Constants.APP_STATUS_APPROVED
                        else:
                            app_status.status = Constants.APP_STATUS_REFUSED

                            #rollback: set date of parcel that isn't approved to NULL
                            #set valid_till of parcels back to infinity
                            application = self.session.query(CtApplication).get(app_no)
                            if application.maintenance_case not in maintenance_cases and application.maintenance_case is not None:
                                maintenance_cases.append(application.maintenance_case)

                        self.session.add(app_status)

                    if application.app_type in Constants.APPLICATION_TYPE_WITH_DURATION:
                        approved_duration = int(duration)
                        application.approved_duration = approved_duration

                    item = QTreeWidgetItem()
                    item.setText(0, decision_app.application)
                    if int(decision_app.decision_result) == int(Constants.DECISION_RESULT_APPROVED):
                        self.item_approved.addChild(item)
                    else:
                        self.item_refused.addChild(item)

                user = DatabaseUtils.current_user()

                for m_case_id in maintenance_cases:
                    m_case = self.session.query(CaMaintenanceCase).filter(CaMaintenanceCase.id == m_case_id).one()

                    qt_date = PluginUtils.convert_python_date_to_qt(m_case.completion_date)
                    qt_date = qt_date.addDays(-1)
                    user.pa_from = PluginUtils.convert_qt_date_to_python(qt_date)
                    self.session.flush()

                    for parcel in m_case.parcels:
                        if parcel.valid_till == m_case.completion_date:
                            parcel.valid_till = None
                        elif parcel.valid_from == m_case.completion_date:
                            parcel.old_parcel_id = "refused"
                            parcel.valid_till = None
                            parcel.valid_from = None

                self.session.add(self.decision)
                self.add_document_button.setEnabled(True)
                self.load_document_button.setEnabled(True)
                self.delete_document_button.setEnabled(True)
                self.view_document_button.setEnabled(True)
                self.select_file_button.setEnabled(False)

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Could not import xls file {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    def __write_changes(self, maintenance_case_id, tmp_parcel_id, app_no):

        try:
            application = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
            if application.decision_result == Constants.DECISION_RESULT_REFUSED:
                return
            soum = DatabaseUtils.working_l2_code()
            layer = LayerUtils.layer_by_data_source("s"+soum, "ca_tmp_parcel")
            if layer is None:
                layer = LayerUtils.load_layer_by_name("ca_tmp_parcel", "parcel_id", soum)

            request = QgsFeatureRequest()
            request.setFilterExpression("maintenance_case = " + str(maintenance_case_id))
            iterator = layer.getFeatures(request)

            for feature in iterator:
                point = feature.geometry().centroid()
                break

            srid = PluginUtils.utm_srid_from_point(point.asPoint())

            # Parcels with their geometry replaced
            parcels_to_replace_geometry = self.session.query(CaTmpParcel). \
                filter(CaTmpParcel.parcel_id == CaParcel.parcel_id). \
                filter(~CaTmpParcel.geometry.ST_Equals(CaParcel.geometry)). \
                filter(CaTmpParcel.maintenance_case == maintenance_case_id). \
                filter(CaTmpParcel.parcel_id == tmp_parcel_id).all()

            for tmp_parcel in parcels_to_replace_geometry:
                parcel_replace = self.session.query(CaParcel).get(tmp_parcel.parcel_id)
                parcel_replace.geometry = tmp_parcel.geometry

            # Parcels to become historical: subdivided
            historical_parcels = self.session.query(CaParcel).join(CaMaintenanceCase.parcels). \
                filter(CaMaintenanceCase.id == maintenance_case_id).\
                filter(CaParcel.geometry.ST_Transform(int(srid)).ST_Contains(CaTmpParcel.geometry.ST_Transform(int(srid)).ST_Buffer(-0.005))). \
                filter(CaParcel.geometry.ST_Transform(int(srid)).ST_Area() != CaTmpParcel.geometry.ST_Transform(int(srid)).ST_Area()). \
                filter(CaTmpParcel.parcel_id == tmp_parcel_id).all()

            for old_parcel in historical_parcels:
                old_parcel.valid_till = date.today()

            # Parcels to become historical: merged
            historical_parcels = self.session.query(CaParcel).join(CaMaintenanceCase.parcels). \
                filter(CaMaintenanceCase.id == maintenance_case_id). \
                filter(CaParcel.geometry.ST_Transform(int(srid)).ST_Buffer(-0.005).ST_Within(CaTmpParcel.geometry.ST_Transform(int(srid)))). \
                filter(CaParcel.geometry.ST_Transform(int(srid)).ST_Area() != CaTmpParcel.geometry.ST_Transform(int(srid)).ST_Area()). \
                filter(CaTmpParcel.parcel_id == tmp_parcel_id).all()

            for old_parcel in historical_parcels:
                old_parcel.valid_till = date.today()

            # Parcels to be inserted
            parcels_to_be_inserted = self.session.query(CaTmpParcel). \
                filter(CaTmpParcel.parcel_id.startswith(str(maintenance_case_id) + '-')). \
                filter(CaTmpParcel.parcel_id == tmp_parcel_id).all()
            maintenance_case = self.session.query(CaMaintenanceCase).filter(CaMaintenanceCase.id == maintenance_case_id).one()
            parcel_id = ''
            for tmp_parcel in parcels_to_be_inserted:
                parcel_inserted = CaParcel()
                parcel_inserted.old_parcel_id = tmp_parcel.old_parcel_id
                parcel_inserted.geo_id = tmp_parcel.geo_id
                parcel_inserted.area_m2 = tmp_parcel.area_m2
                parcel_inserted.documented_area_m2 = tmp_parcel.documented_area_m2
                parcel_inserted.address_khashaa = tmp_parcel.address_khashaa
                parcel_inserted.address_streetname = tmp_parcel.address_streetname
                parcel_inserted.address_neighbourhood = tmp_parcel.address_neighbourhood
                parcel_inserted.valid_from = date.today()
                parcel_inserted.geometry = tmp_parcel.geometry
                parcel_inserted.landuse = tmp_parcel.landuse
                maintenance_case.parcels.append(parcel_inserted)
                self.session.add(parcel_inserted)
                self.session.commit()
                parcel_id = parcel_inserted.parcel_id
                # self.session.flush()

                #buildings that intersect
                buildings_to_be_inserted = self.session.query(CaTmpBuilding) \
                    .filter(CaTmpBuilding.geometry.ST_Intersects(parcel_inserted.geometry)).count()

                buildings_to_be_inserted = self.session.query(CaTmpBuilding)\
                    .filter(CaTmpBuilding.geometry.ST_Intersects(parcel_inserted.geometry)).all()

                for building in buildings_to_be_inserted:

                    building_insert = CaBuilding()
                    building_insert.building_no = building.building_no
                    building_insert.geo_id = building.geo_id
                    building_insert.area_m2 = building.area_m2
                    building_insert.address_khashaa = building.address_khashaa
                    building_insert.address_streetname = building.address_streetname
                    building_insert.address_neighbourhood = building.address_neighbourhood
                    building_insert.valid_from = date.today()
                    building_insert.geometry = building.geometry

                    building_update = self.session.query(CaBuilding).get(building.building_id)
                    if building_update:
                        building_update.valid_till = date.today()

                    self.session.add(building_insert)

                    self.session.query(CaTmpBuilding). \
                        filter(CaTmpBuilding.maintenance_case == maintenance_case_id).delete()
            historical_buildings = self.session.query(CaBuilding) \
                .filter(CaBuilding.geometry.ST_Buffer(-0.005).ST_Within(CaTmpBuilding.geometry)) \
                .filter(CaTmpBuilding.maintenance_case == maintenance_case_id) \
                .filter(CaBuilding.geometry.ST_Area() != CaTmpBuilding.geometry.ST_Area()).all()

            for building in historical_buildings:
                building.valid_till = date.today()

            buildings_to_replace_geometry = self.session.query(CaTmpBuilding) \
                .filter(CaTmpBuilding.building_id == CaBuilding.building_id) \
                .filter(~CaTmpBuilding.geometry.ST_Equals(CaBuilding.geometry)) \
                .filter(CaTmpBuilding.maintenance_case == maintenance_case_id).all()

            for tmp_building in buildings_to_replace_geometry:
                building_replace = self.session.query(CaBuilding).get(tmp_building.building_id)
                building_replace.geometry = tmp_building.geometry

            historical_buildings = self.session.query(CaBuilding) \
                .filter(CaBuilding.geometry.ST_Contains(CaTmpBuilding.geometry.ST_Buffer(-0.005))) \
                .filter(CaTmpBuilding.maintenance_case == maintenance_case_id) \
                .filter(CaBuilding.geometry.ST_Area() != CaTmpBuilding.geometry.ST_Area()).all()

            for building in historical_buildings:
                building.valid_till = date.today()

            buildings_to_be_inserted_count = self.session.query(CaTmpBuilding) \
                .filter(CaTmpBuilding.maintenance_case == maintenance_case_id).count()

            if buildings_to_be_inserted_count != 0:
                buildings_to_be_inserted = self.session.query(CaTmpBuilding) \
                    .filter(~CaTmpBuilding.building_id.startswith(str(maintenance_case_id) + "-"))\
                    .filter(CaTmpParcel.geometry.ST_Within(CaTmpBuilding.geometry))\
                    .filter(~CaTmpParcel.parcel_id.startswith(str(maintenance_case_id) + '-')).all()

                for tmp_building in buildings_to_be_inserted:
                    building_insert = CaBuilding()
                    building_insert.geo_id = tmp_building.geo_id
                    building_insert.area_m2 = tmp_building.area_m2
                    building_insert.address_khashaa = tmp_building.address_khashaa
                    building_insert.address_streetname = tmp_building.address_streetname
                    building_insert.address_neighbourhood = tmp_building.address_neighbourhood
                    building_insert.valid_from = date.today()
                    building_insert.geometry = tmp_building.geometry
                    self.maintenance_case.buildings.append(building_insert)

                    self.session.add(building_insert)

                    self.session.query(CaTmpBuilding). \
                        filter(CaTmpBuilding.maintenance_case == maintenance_case_id).delete()

            application.tmp_parcel = None
            application.parcel = parcel_id
            application.approved_duration = application.requested_duration
            self.session.add(application)
            # delete tmp parcels
            app = self.session.query(CtApplication).\
                filter(CtApplication.tmp_parcel == tmp_parcel_id).all()
            for app in app:
                app.tmp_parcel = None
            self.session.flush()
            self.session.query(CaTmpParcel). \
                filter(CaTmpParcel.maintenance_case == maintenance_case_id). \
                filter(CaTmpParcel.parcel_id == tmp_parcel_id).delete()

            self.commit()

        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    def __validate_decision_attributes(self, current_date_string, decision_no, decision_level):

        qt_date = QDate.fromString(current_date_string, Constants.DATABASE_DATE_FORMAT)
        count = 0

        if not qt_date.isValid():
            self.rollback()
            PluginUtils.show_error(self, self.tr("Error in xls file"),
                                   self.tr("The date is not in the correct format. "
                                           "Expected yyyy-MM-dd and found: " + current_date_string))

            self.error_list[decision_no + " # " + str(count)] = self.tr("The date is not in the correct format. "
                                           "Expected yyyy-MM-dd and found: " + current_date_string)
            count += 1
            return False

        try:
            #check that the decision number contains a soum code
            soum_no = decision_no.split("-")[0]
            count = self.session.query(AuLevel2).filter(AuLevel2.code == soum_no).count()
            if count == 0:
                PluginUtils.show_error(self, self.tr("Error in xls file"), self.tr("The decision number {0} "
                                                                                   "contains an invalid soum code.")
                                                                                    .format(decision_no))
                self.error_list[decision_no + " # " + str(count)] = self.tr("The decision number {0} "
                                                                                   "contains an invalid soum code.").format(decision_no)
                count += 1
                return False
            else:
                DatabaseUtils.set_working_schema(soum_no)

            #check if decision_no already exists in case of a new import
            if not self.attribute_update:
                count = self.session.query(CtDecision).filter(CtDecision.decision_no == decision_no).filter(CtDecision.decision_level == decision_level).count()
                if count > 0:
                    PluginUtils.show_error(self, self.tr("Error in xls file"),
                                                self.tr("The decision number {0} already exists in the database.")
                                                    .format(decision_no))
                    self.error_list[decision_no + " # " + str(count)] = self.tr("The decision number {0} already exists in the database.")
                    count += 1
                    return False

            #check if the decision level is in the codelist and of the type int
            try:
                int(decision_level)
            except ValueError:

                PluginUtils.show_error(self, self.tr("Error in xls file"),
                                            self.tr("The decision level code {0} is not of the type integer.")
                                            .format(decision_level))

                self.error_list[decision_no + " # " + str(count)] = self.tr("The decision level code {0} is not of the type integer.").format(decision_level)
                count += 1
                return False

            count = self.session.query(ClDecisionLevel).filter(ClDecisionLevel.code == decision_level).count()
            if count == 0:
                PluginUtils.show_error(self, self.tr("Error in xls file"),
                                            self.tr("The decision level code {0} is not in the database.")
                                                .format(decision_level))

                self.error_list[decision_no + " # " + str(count)] = self.tr("The decision level code {0} is not in the database.").format(decision_level)
                count += 1

                return False

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return False

        return True

    def __validate_row(self, decision_result, app_no, current_decision_no, decision_no, duration, landuse):

        #1st: decision result is type of integer
        #2cnd: decision id exists
        #3rd: application exists
        #4th: check if the decision number is different
        #5th: check the decision level
        #6th: check existance of landuse
        valid_row = True
        count = 1

        try:
            int(decision_result)

        except ValueError:
            self.error_list[app_no + " # " + str(count)] = self.tr("Could not convert decision result: {0} to integer.")\
                                                                    .format(str(decision_result))
            valid_row = False
            count += 1

        if valid_row:
            decision_result_count = self.session.query(ClDecision.code, ClDecision.description)\
                .filter_by(code=int(decision_result)).count()

            if decision_result_count == 0:
                self.error_list[app_no + " # " + str(count)] = \
                    self.tr("Could not find the decision result: {0}. Import will be canceled")\
                        .format(str(decision_result))

                valid_row = False
                count += 1

        try:
            int(landuse)

        except ValueError:
            self.error_list[app_no + " # " + str(count)] = self.tr("Could not convert landuse type: {0} to integer.")\
                                                                    .format(str(decision_result))
            valid_row = False
            count += 1

        if valid_row:
            decision_result_count = self.session.query(ClLanduseType.code, ClLanduseType.description)\
                .filter_by(code=int(landuse)).count()

            if decision_result_count == 0:
                self.error_list[app_no + " # " + str(count)] = \
                    self.tr("Could not find the landuse type: {0}. Import will be canceled")\
                        .format(str(landuse))

                valid_row = False
                count += 1

        application_count = self.session.query(CtApplication).filter_by(app_no=app_no).count()
        if application_count == 0:
            self.error_list[app_no + " # " + str(count)] = \
                self.tr("The application {0} does not exist. Import will be skipped.").format(app_no)

            valid_row = False
            count += 1

        elif application_count == 1:

            application = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()

            if application.app_type in Constants.APPLICATION_TYPE_WITH_DURATION:
                try:
                    int_duration = int(duration)
                    if int_duration == 0:
                        self.error_list[app_no + " # " + str(count)] = \
                            self.tr("The application {0} should have an approved duration.").format(app_no)
                        valid_row = False
                        count += 1
                except ValueError:
                    self.error_list[app_no + " # " + str(count)] = \
                        self.tr("The application {0} should have an approved duration.").format(app_no)
                    valid_row = False
                    count += 1

            if application.decision_result is not None:
                self.error_list[app_no + " # " + str(count)] = \
                    self.tr("There is already a decision for the application {0}.").format(app_no)
                valid_row = False
                count += 1

            count = application.statuses.filter(CtApplicationStatus.status == Constants.APP_STATUS_SEND).count()
            if count == 0:
                self.error_list[app_no + " # " + str(count)] = \
                    self.tr("The application isn't send to the governor.").format(app_no)
                valid_row = False
                count += 1

        if decision_no != current_decision_no:
            self.error_list[app_no + " # " + str(count)] = \
                self.tr("The decision number is not equal in the dataset. Found number {0}").format(current_decision_no)
            valid_row = False
            count += 1

        return valid_row

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
    def on_error_details_button_clicked(self):
        dialog = DecisionErrorDialog(self.error_list, self)
        dialog.exec_()

    @pyqtSlot()
    def on_add_document_button_clicked(self):

        default_path = FilePath.decision_file_path()

        file_dialog = QFileDialog()
        file_dialog.setModal(True)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setFilter(self.tr("Decision Files (*.img *.png *.xls *.xlsx *.pdf)"))

        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            file_path = QFileInfo(selected_file).filePath()
            file_name = QFileInfo(file_path).fileName()

            decision_no = self.decision_no_edit.text()
            decision_no = decision_no.replace("/", "_")
            num = []
            if self.document_twidget.count() == 0:
                file_name = decision_no +'-'+ '01.pdf'
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
                file_name = decision_no +'-'+ (max_num)+'.pdf'

            try:
                item = QListWidgetItem(file_name, self.document_twidget)
                item.setData(Qt.UserRole, file_name)

                shutil.copy2(selected_file, default_path+'/'+file_name)
            except SQLAlchemyError, e:
                self.rollback_to_savepoint()
                PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

    @pyqtSlot()
    def on_load_document_button_clicked(self):

        self.__remove_document_items()
        self.__update_documents_file_twidget()
        self.add_document_button.setEnabled(True)
        self.delete_document_button.setEnabled(True)
        self.view_document_button.setEnabled(True)

    def __update_documents_file_twidget(self):

        file_path = FilePath.decision_file_path()
        for file in os.listdir(file_path):
            os.listdir(file_path)
            if file.endswith(".pdf"):
                decision_no = file[:-7]
                decision_no = decision_no.replace("_", "/")
                file_name = file

                if self.decision.decision_no == decision_no:
                    item = QListWidgetItem(file_name, self.document_twidget)
                    item.setData(Qt.UserRole, file_name)

    def __remove_document_items(self):

        if not self.document_twidget:
            return

        while self.document_twidget.count() > 0:
            self.document_twidget.clear()

    @pyqtSlot()
    def on_delete_document_button_clicked(self):

        default_path = FilePath.decision_file_path()
        current_row = self.document_twidget.currentRow()
        if current_row == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Select Item."))
            return

        item = self.document_twidget.selectedItems()[0]
        item_index = self.document_twidget.selectedIndexes()[0]

        try:
            dec_document_name = item.text()
            self.document_twidget.takeItem(item_index.row())
            os.remove(default_path+'/'+dec_document_name)
        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    @pyqtSlot()
    def on_view_document_button_clicked(self):

        current_row = self.document_twidget.currentRow()
        if current_row == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Select Item."))
            return
        byte_array_item = self.document_twidget.selectedItems()[0]
        file_name = byte_array_item.text()

        default_path = FilePath.decision_file_path()
        shutil.copy2(default_path + '/'+file_name, FilePath.view_file_path())
        QDesktopServices.openUrl(QUrl.fromLocalFile(FilePath.view_file_path()))

    @pyqtSlot()
    def on_import_button_clicked(self):

        try:
            self.commit()

        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        self.__start_fade_out_timer()
        user = DatabaseUtils.current_user()
        user.pa_from = self.original_pa_from

    @pyqtSlot()
    def on_decision_save_button_clicked(self):

        user_name = QSettings().value(SettingsConstants.USER)
        current_employee = self.session.query(SetRole) \
            .filter(SetRole.user_name == user_name) \
            .filter(SetRole.is_active == True).one()
        working_soum = self.session.query(SetRole).filter(SetRole.user_name_real == current_employee.user_name_real).one()

        month_filter = str(self.contract_date.date().toString("MM"))
        day_filter = str(self.contract_date.date().toString("dd"))
        year_filter = str(self.contract_date.date().toString("yyyy"))
        decision_no = working_soum.working_au_level2 + '-' + self.notary_number_edit.text() + '-' + self.contract_id_edit.text() + '/' + year_filter
        try:
            if self.seller_buyer_checkbox.isChecked():
                if self.contract_id_edit.text() == "" or self.contract_id_edit.text() == None:
                    PluginUtils.show_error(self, self.tr("Error saving decision"),
                                       self.tr("It is not allowed to save a decision without an contract no."))
                    return
                if self.application_cbox.currentText()[:5] != working_soum.working_au_level2:
                    PluginUtils.show_error(self, self.tr("Error saving decision"),
                                       self.tr("there is not matching application soum and decision soum."))
                    return

                user = DatabaseUtils.current_user()
                current_employee = self.session.query(SetRole) \
                    .filter(SetRole.user_name == user.user_name) \
                    .filter(SetRole.is_active == True).one()

                decision_count = self.session.query(CtDecision).filter(CtDecision.decision_no == self.notary_decision_edit.text()).\
                    filter(CtDecision.decision_level == self.decision.decision_level).count()
                if decision_count > 0:
                    return
                self.decision = CtDecision()
                self.decision.decision_date = self.contract_date.date().toString(Constants.DATABASE_DATE_FORMAT)
                self.decision.decision_no = self.notary_decision_edit.text()
                self.decision.decision_level = 70
                self.decision.imported_by = current_employee.user_name_real

                decicion_app = CtDecisionApplication()
                decicion_app.decision = self.notary_decision_edit.text()
                decicion_app.decision_result = 10
                decicion_app.application = self.application_cbox.currentText()
                self.decision.results.append(decicion_app)
                self.session.add(self.decision)
                self.add_document_button.setEnabled(True)
                self.load_document_button.setEnabled(True)

                user = DatabaseUtils.current_user()
                current_employee = self.session.query(SetRole) \
                    .filter(SetRole.user_name == user.user_name) \
                    .filter(SetRole.is_active == True).one()

                app_status = CtApplicationStatus()
                app_status.next_officer_in_charge = current_employee.user_name_real
                app_status.officer_in_charge = current_employee.user_name_real
                app_status.application = self.application_cbox.currentText()
                app_status.status_date = self.decision.decision_date
                app_status.status = Constants.APP_STATUS_APPROVED

                application = self.session.query(CtApplication).\
                            filter(CtApplication.app_no == self.application_cbox.currentText()).one()

                if application.tmp_parcel != None:
                    parcel = self.session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == application.tmp_parcel).one()
                    tmp_parcel_id = parcel.parcel_id
                    maintenance_case_id = parcel.maintenance_case

                    self.__write_changes(maintenance_case_id, tmp_parcel_id, application.app_no)
                self.session.add(app_status)

        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    def reject(self):

        self.rollback()
        QDialog.reject(self)

    @pyqtSlot()
    def on_help_button_clicked(self):

        os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/import_decision.htm")

    @pyqtSlot(int)
    def on_seller_buyer_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.decision_file_edit.setEnabled(False)
            self.select_file_button.setEnabled(False)
            self.result_tree_widget.setEnabled(False)

            self.person_id_edit.setEnabled(True)
            self.application_cbox.setEnabled(True)
            self.notary_number_edit.setEnabled(True)
            self.contract_id_edit.setEnabled(True)
            self.contract_date.setEnabled(True)
            self.add_document_button.setEnabled(False)
            self.load_document_button.setEnabled(True)
            self.view_document_button.setEnabled(True)
            self.delete_document_button.setEnabled(True)
            self.level_cbox.setEnabled(True)
            self.decision_save_button.setEnabled(True)
            decision_level = self.session.query(ClDecisionLevel).filter(ClDecisionLevel.code == 70).one()
            self.level_cbox.clear()
            self.level_cbox.addItem(decision_level.description, decision_level.code)
        else:
            self.decision_file_edit.setEnabled(True)
            self.select_file_button.setEnabled(True)
            self.result_tree_widget.setEnabled(True)

            self.person_id_edit.setEnabled(False)
            self.application_cbox.setEnabled(False)
            self.contract_id_edit.setEnabled(False)
            self.notary_number_edit.setEnabled(False)
            self.contract_date.setEnabled(False)
            self.add_document_button.setEnabled(False)
            self.load_document_button.setEnabled(False)
            self.view_document_button.setEnabled(False)
            self.delete_document_button.setEnabled(False)
            self.decision_save_button.setEnabled(False)

    @pyqtSlot(str)
    def on_person_id_edit_textChanged(self, text):

        self.application_cbox.clear()
        value = "%" + text + "%"

        application = self.session.query(CtApplication)\
            .join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application)\
            .join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id)\
            .filter(or_(CtApplication.parcel != None, CtApplication.tmp_parcel != None))\
            .filter(or_(CtApplication.app_type == 15, CtApplication.app_type == 2))\
            .filter(BsPerson.person_id.ilike(value)).all()

        for app in application:
            self.app_no = app.app_no
            self.application_cbox.addItem(self.app_no, self.app_no)

    def __validate_entity_id(self, text):

        if len(text) > 5:
            cut = text[:4]
            self.contract_id_edit.setText(cut)
        return True

    def __validate_notary_no(self, text):

        if len(text) > 3:
            cut = text[:2]
            self.notary_number_edit.setText(cut)
        return  True

    @pyqtSlot(str)
    def on_contract_id_edit_textChanged(self, text):

        if not self.__validate_entity_id(text):
            self.contract_id_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

        user_name = QSettings().value(SettingsConstants.USER)
        current_employee = self.session.query(SetRole) \
            .filter(SetRole.user_name == user_name) \
            .filter(SetRole.is_active == True).one()

        working_soum = self.session.query(SetRole).filter(SetRole.user_name_real == current_employee.user_name_real).one()
        month_filter = str(self.contract_date.date().toString("MM"))
        day_filter = str(self.contract_date.date().toString("dd"))
        year_filter = str(self.contract_date.date().toString("yyyy"))

        notary_decision_no = working_soum.working_au_level2 + '-' + self.notary_number_edit.text() + '-' + text  + '/' + year_filter
        self.notary_decision_edit.setText(notary_decision_no)

    @pyqtSlot(str)
    def on_notary_number_edit_textChanged(self, text):

        if not self.__validate_notary_no(text):
            self.notary_number_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

        user_name = QSettings().value(SettingsConstants.USER)
        current_employee = self.session.query(SetRole) \
            .filter(SetRole.user_name == user_name) \
            .filter(SetRole.is_active == True).one()

        working_soum = self.session.query(SetRole).filter(SetRole.user_name_real == current_employee.user_name_real).one()
        month_filter = str(self.contract_date.date().toString("MM"))
        day_filter = str(self.contract_date.date().toString("dd"))
        year_filter = str(self.contract_date.date().toString("yyyy"))

        notary_decision_no = working_soum.working_au_level2 + '-' + text +'-'+ self.contract_id_edit.text() + '/' + year_filter
        self.notary_decision_edit.setText(notary_decision_no)

    # join application

    @pyqtSlot(str)
    def on_decision_no_search_edit_textChanged(self, text):

        value = "%" + text + "%"
        self.decision_result_twidget.setRowCount(0)
        try:
            decisions = self.session.query(CtDecision).\
                filter(CtDecision.decision_no.ilike(value)).all()

            count = 0
            for decision in decisions:

                item = QTableWidgetItem(decision.decision_no)
                item.setCheckState(Qt.Unchecked)
                item.setData(Qt.UserRole, decision.decision_no)
                self.decision_result_twidget.insertRow(count)
                self.decision_result_twidget.setItem(count, 0, item)
                count +=1
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
            return

    @pyqtSlot(QTableWidgetItem)
    def on_decision_result_twidget_itemClicked(self, item):

        decision_no = item.data(Qt.UserRole)
        item.setCheckState(Qt.Checked)

        try:
            decision = self.session.query(CtDecision).filter_by(decision_no = decision_no).one()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
            return

        self.__populate_decision(decision)

        for row in range(self.decision_result_twidget.rowCount()):
            item_dec = self.decision_result_twidget.item(row, 0)
            item_dec.setCheckState(Qt.Unchecked)
        item.setCheckState(Qt.Checked)

    def __populate_decision(self, decision):

        self.result_tree_widget.clear()
        self.item_approved = QTreeWidgetItem()
        self.item_approved.setText(0, self.tr("Approved"))
        self.item_approved.setData(0, Qt.UserRole, Constants.DECISION_RESULT_REFUSED)

        self.item_refused = QTreeWidgetItem()
        self.item_refused.setText(0, self.tr("Refused"))
        self.item_refused.setData(0, Qt.UserRole, Constants.DECISION_RESULT_REFUSED)

        self.item_skipped = QTreeWidgetItem()
        self.item_skipped.setText(0, self.tr("Skipped"))
        self.item_skipped.setData(0, Qt.UserRole, -1)
        self.result_tree_widget.addTopLevelItem(self.item_approved)
        self.result_tree_widget.addTopLevelItem(self.item_refused)
        self.result_tree_widget.addTopLevelItem(self.item_skipped)
        self.document_twidget.clear()

        try:
            self.decision = decision

            decision_level = self.session.query(ClDecisionLevel).\
                filter(ClDecisionLevel.code == decision.decision_level).one()

            application_type = self.session.query(ClApplicationType).\
                join(CtApplication, ClApplicationType.code == CtApplication.app_type).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtDecisionApplication.decision == decision.decision_no).all()

            self.decision_no_result_edit.setText(decision.decision_no)
            self.decision_date_result_edit.setText(str(decision.decision_date))
            self.level_result_edit.setText(decision_level.description)
            self.app_type_code = 1
            for application_type in application_type:
                self.app_type_code = application_type.code
                self.application_type_edit.setText(application_type.description)

            if self.decision.decision_level == 70:
                self.seller_buyer_checkbox.setChecked(True)
                for decision_doc in self.decision.documents:

                    item = QListWidgetItem(decision_doc.document_ref.name, self.document_twidget)
                    item.setData(Qt.UserRole, decision_doc)
                for result in self.decision.results:
                    self.application_cbox.addItem(result.application, result.application)
                self.contract_date.setDate(self.decision.decision_date)
                self.level_cbox.setCurrentIndex(self.level_cbox.findData(self.decision.decision_level))
                self.notary_number_edit.setDisabled(True)
                self.contract_id_edit.setDisabled(True)
                self.notary_decision_edit.setText(self.decision.decision_no)
                self.decision_save_button.setDisabled(True)
            else:
                for result in self.decision.results:
                    item = QTreeWidgetItem()
                    item.setText(0, result.application)
                    if result.decision_result == Constants.DECISION_RESULT_APPROVED:
                        self.item_approved.addChild(item)
                    else:
                        self.item_refused.addChild(item)

                for decision_doc in self.decision.documents:

                    item = QListWidgetItem(decision_doc.document_ref.name, self.document_twidget)
                    item.setData(Qt.UserRole, decision_doc)

                self.decision_date_edit.setText(self.decision.decision_date.strftime(Constants.PYTHON_DATE_FORMAT))
                self.decision_no_edit.setText(self.decision.decision_no)
                self.level_cbox.setCurrentIndex(self.level_cbox.findData(self.decision.decision_level))
                self.import_by_edit.setText(self.decision.imported_by)
            self.add_document_button.setEnabled(True)
            self.load_document_button.setEnabled(True)
            self.delete_document_button.setEnabled(True)
            self.view_document_button.setEnabled(True)
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
            return

    def __populate_application(self):

        applications = self.session.query(CtApplicationStatus)
        sub = self.session.query(CtApplicationStatus, func.row_number().over(partition_by = CtApplicationStatus.application, order_by = (desc(CtApplicationStatus.status))).label("row_number")).subquery()
        applications = applications.select_entity_from(sub).filter(sub.c.row_number == 1)
        applications = applications.filter(CtApplicationStatus.status == 1)
        count = 0
        for application in applications.distinct(CtApplicationStatus.application).all():
            app = self.session.query(CtApplication).filter(CtApplication.app_no == application.application).one()
            if app.parcel is not None:
                item = QTableWidgetItem(str(app.app_no))
                item.setIcon(QIcon(QPixmap(":/plugins/lm2/application.png")))
                item.setData(Qt.UserRole, app.app_no)
                self.result_app_twidget.insertRow(count)
                self.result_app_twidget.setItem(count, 0, item)
                count += 1

    def __populate_combobox(self):

        try:
            officers = self.session.query(SetRole).all()

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("Sql Error"), e.message)
            return

        self.officer_by_find_cbox.addItem("*", -1)

        for officer in officers:
                self.officer_by_find_cbox.addItem(officer.user_name_real, officer.user_name_real)

    @pyqtSlot()
    def on_clear_button_clicked(self):

        self.person_id_find_edit.setText('')
        self.parcel_id_find_edit.setText('')
        self.app_no_find_edit.setText('')
        # self.officer_by_find_cbox.itemData(self.officer_by_find_cbox.currentIndex())

    @pyqtSlot()
    def on_app_find_button_clicked(self):

        self.__find_application()

    def __find_application(self):

        self.result_app_twidget.setRowCount(0)
        try:
            filter_is_set = False
            applications = self.session.query(CtApplicationStatus)
            sub = self.session.query(CtApplicationStatus, func.row_number().over(partition_by = CtApplicationStatus.application, order_by = (desc(CtApplicationStatus.status))).label("row_number")).subquery()
            applications = applications.select_entity_from(sub).filter(sub.c.row_number == 1)
            applications = applications.filter(CtApplicationStatus.status == 1)

            if self.officer_by_find_cbox.currentIndex() != -1:
                if not self.officer_by_find_cbox.itemData(self.officer_by_find_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    officer = "%" + self.officer_by_find_cbox.itemData(self.officer_by_find_cbox.currentIndex()) + "%"
                    applications = applications.filter(CtApplicationStatus.officer_in_charge.ilike(officer))

            if self.app_no_find_edit.text():
                filter_is_set = True
                app_no = "%" + self.app_no_find_edit.text() + "%"
                applications = applications.filter(CtApplicationStatus.application.ilike(app_no))

            count = 0
            for application in applications.distinct(CtApplicationStatus.application).all():
                app = self.session.query(CtApplication).filter(CtApplication.app_no == application.application).one()
                if app.parcel is not None or app.tmp_parcel is not None:
                    app_number = app.app_no
                    if self.person_id_find_edit.text():
                        filter_is_set = True
                        person_id = self.person_id_find_edit.text()
                        app_count = self.session.query(CtApplicationPersonRole). \
                            filter(CtApplicationPersonRole.person.ilike(person_id)). \
                            filter(CtApplicationPersonRole.application == application.application).count()
                        if app_count == 1:
                            app = self.session.query(CtApplicationPersonRole).\
                                filter(CtApplicationPersonRole.person.ilike(person_id)).\
                                filter(CtApplicationPersonRole.application == application.application).one()
                            app_number = app.application
                    if self.parcel_id_find_edit.text():
                        filter_is_set = True
                        parcel_id = "%" + self.parcel_id_find_edit.text() + "%"
                        app_count = self.session.query(CtApplication).\
                            filter(CtApplication.parcel.ilike(parcel_id)).\
                            filter(CtApplication.app_no == application.application).count()
                        if app_count == 1:
                            app = self.session.query(CtApplication).\
                                filter(CtApplication.parcel.ilike(parcel_id)).\
                                filter(CtApplication.app_no == application.application).one()
                            app_number = app.app_no
                        else:
                            app = self.session.query(CtApplication).\
                                filter(CtApplication.tmp_parcel.ilike(parcel_id)).\
                                filter(CtApplication.app_no == application.application).one()
                            app_number = app.app_no
                    item = QTableWidgetItem(str(app_number))
                    item.setIcon(QIcon(QPixmap(":/plugins/lm2/application.png")))
                    item.setData(Qt.UserRole, app_number)
                    self.result_app_twidget.insertRow(count)
                    self.result_app_twidget.setItem(count, 0, item)
                    count += 1

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    def __selected_application(self):

        selected_items = self.result_app_twidget.selectedItems()
        application_instance = None

        if len(selected_items) != 1:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Only single selection allowed."))
            return None

        selected_item = selected_items[0]
        app_no = selected_item.data(Qt.UserRole)

        app_no_soum = app_no.split("-")[0]

        DatabaseUtils.set_working_schema(app_no_soum)

        try:
            application_instance = self.session.query(CtApplication).filter_by(app_no=app_no).one()

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return None

        return application_instance

    @pyqtSlot()
    def on_app_join_button_clicked(self):

        current_row = self.decision_result_twidget.currentRow()
        if current_row == -1:
            PluginUtils.show_message(self, self.tr("Decision"), self.tr("You must select the decision."))
            return

        app_instance = self.__selected_application()

        selected_items = self.result_app_twidget.selectedItems()
        if len(selected_items) != 1:
            return None

        # set_right_type_app = self.session.query(SetRightTypeApplicationType).filter(SetRightTypeApplicationType.application_type == app_instance.app_type).one()
        # set_right_type_dec = self.session.query(SetRightTypeApplicationType).filter(SetRightTypeApplicationType.application_type == self.app_type_code).one()
        if app_instance.app_type != self.app_type_code:
            PluginUtils.show_message(self, self.tr("Application Type"), self.tr("This application type do not match."))
            return

        selected_row = self.result_app_twidget.currentRow()
        self.result_app_twidget.removeRow(selected_row)

        item = QTableWidgetItem(str(app_instance.app_no))
        item.setIcon(QIcon(QPixmap(":/plugins/lm2/application.png")))
        item.setData(Qt.UserRole, app_instance.app_no)
        row = self.join_app_twidget.rowCount()
        self.join_app_twidget.insertRow(row)
        self.join_app_twidget.setItem(row, 0, item)

        try:
            # decision_app = self.session.query(CtDecisionApplication).filter(CtDecisionApplication.decision == self.decision.decision_no).all()
            decision_app = CtDecisionApplication()
            decision_app.decision = self.decision.decision_no
            decision_app.application = app_instance.app_no
            decision_app.decision_result = 10
            self.session.add(decision_app)
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
            return

    @pyqtSlot()
    def on_app_cancel_button_clicked(self):

        current_row = self.join_app_twidget.currentRow()
        if current_row == -1:
            PluginUtils.show_message(self, self.tr("Applciation"), self.tr("You must choose the application."))
            return

        selected_items = self.join_app_twidget.selectedItems()

        if len(selected_items) != 1:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Only single selection allowed."))
            return None

        selected_items = self.join_app_twidget.selectedItems()
        selected_item = selected_items[0]
        app_no = selected_item.data(Qt.UserRole)

        selected_row = self.join_app_twidget.currentRow()
        self.join_app_twidget.removeRow(selected_row)

        item = QTableWidgetItem(str(app_no))
        item.setIcon(QIcon(QPixmap(":/plugins/lm2/application.png")))
        item.setData(Qt.UserRole, app_no)
        row = self.result_app_twidget.rowCount()
        self.result_app_twidget.insertRow(row)
        self.result_app_twidget.setItem(row, 0, item)

    @pyqtSlot(QTableWidgetItem)
    def on_result_app_twidget_itemClicked(self, item):

        app_no = item.data(Qt.UserRole)

        try:
            application = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
            app_persons = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app_no).all()

            self.app_no_find_edit.setText(application.app_no)
            self.parcel_id_find_edit.setText(application.parcel)
            for app_person in app_persons:
                if app_person.main_applicant == True:
                    self.person_id_find_edit.setText(app_person.person)
                    person = self.session.query(BsPerson).filter(BsPerson.person_id == app_person.person).one()
                    self.surname_edit.setText(person.name)
                    self.firstname_edit.setText(person.first_name)
            parcel_count = self.session.query(CaParcel).filter(CaParcel.parcel_id == application.parcel).count()
            if parcel_count == 1:
                parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == application.parcel).one()
            else:
                parcel = self.session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == application.tmp_parcel).one()
            self.streetname_edit.setText(parcel.address_streetname)
            self.khashaa_edit.setText(parcel.address_khashaa)
            self.parcel_id_find_edit.setText(parcel.parcel_id)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
            return

    @pyqtSlot()
    def on_save_button_clicked(self):

        current_user = DatabaseUtils.current_user()
        current_employee = self.session.query(SetRole) \
            .filter(SetRole.user_name == current_user.user_name) \
            .filter(SetRole.is_active == True).one()
        row = 1
        num_rows = self.join_app_twidget.rowCount()
        if num_rows > 0:
            for row in range(num_rows):
                app_no_item = self.join_app_twidget.item(row, 0)
                app_no = app_no_item.text()

                try:

                    application = self.session.query(CtApplication).\
                        filter(CtApplication.app_no == app_no).one()
                    if application.tmp_parcel != None:
                        parcel = self.session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == application.tmp_parcel).one()
                        tmp_parcel_id = parcel.parcel_id
                        maintenance_case_id = parcel.maintenance_case

                        self.__write_changes(maintenance_case_id,tmp_parcel_id, app_no)

                    application = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()
                    application.approved_duration = application.requested_duration
                    self.session.add(application)

                    new_status = CtApplicationStatus()
                    new_status.application = app_no
                    new_status.next_officer_in_charge = current_employee.user_name_real
                    new_status.officer_in_charge = current_employee.user_name_real
                    new_status.status = Constants.APP_STATUS_APPROVED
                    new_status.status_date = datetime.now().strftime(Constants.PYTHON_DATE_FORMAT)
                    self.session.add(new_status)
                    row +=1
                except SQLAlchemyError, e:
                    PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
                    return

            self.session.commit()

            PluginUtils.show_message(self, self.tr("msg"), self.tr("successfully save"))

            self.join_app_twidget.setRowCount(0)
