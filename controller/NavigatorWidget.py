__author__ = 'Topmap'
# coding=utf8

from qgis.core import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtXml import *
from PyQt4.QtCore import QDate
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func, or_, and_, desc
from sqlalchemy.sql.expression import cast
from sqlalchemy import func
from ..controller.DraftDecisionPrintDialog import *
from ..view.Ui_NavigatorWidget import Ui_NavigatorWidget
from ..utils.LayerUtils import LayerUtils
from ..model.AuCadastreBlock import *
from ..model.CtApplication import *
from ..model.CtRecordApplicationRole import *
from ..model.CtDecisionApplication import *
from ..model.CtContractApplicationRole import *
from ..model.PersonSearch import *
from ..model.ApplicationSearch import *
from ..model.ContractSearch import *
from ..model.DecisionSearch import *
from ..model.RecordSearch import *
from ..model.ParcelSearch import *
from ..model.TmpParcelSearch import *
from ..model.MaintenanceSearch import *
from ..model.ClLanduseType import ClLanduseType
from ..model.ClPersonType import *
from ..model.CtDecision import *
from ..model.SetTaxAndPriceZone import *
from ..model.SetFeeZone import *
from ..model.SetSurveyCompany import SetSurveyCompany
from ..model.CaTmpBuilding import CaTmpBuilding
from ..model.CaTmpParcel import CaTmpParcel
from ..model.Enumerations import ApplicationType, UserRight, UserRight_code
from ..model.SetApplicationTypeLanduseType import *
from ..model.ParcelGt1 import *
from ..model.ParcelReport import *
from ..model.CaParcelConservation import *
from ..model.ClConservationType import *
from ..model.ClPollutionType import *
from ..model.ClContractStatus import *
from ..model.ClRecordStatus import *
from ..model.CaParcelPollution import *
from ..model.ParcelFeeReport import *
from ..model.ParcelTaxReport import *
from ..model.DialogInspector import DialogInspector
from ..model.FeeUnified import *
from ..model.SetUserGroupRole import *
from ..controller.CadastrePageReportDialog import *
from ..utils.DatabaseUtils import *
from PersonDialog import PersonDialog
from ContractDialog import ContractDialog
from ImportDecisionDialog import ImportDecisionDialog
from ApplicationsDialog import ApplicationsDialog
from OwnRecordDialog import OwnRecordDialog
from FinalizeCaseDialog import FinalizeCaseDialog
from CreateCaseDialog import CreateCaseDialog
from LandTaxPaymentsDialog import *
from LandFeePaymentsDialog import *
from datetime import timedelta
from xlsxwriter.utility import xl_rowcol_to_cell, xl_col_to_name
import xlsxwriter
import time

LANDUSE_1 = u'Хөдөө аж ахуйн газар'
LANDUSE_2 = u'Хот, тосгон, бусад суурины газар'
LANDUSE_3 = u'Зам, шугам сүлжээний газар'
LANDUSE_4 = u'Ойн сан бүхий газар'
LANDUSE_5 = u'Усны сан бүхий газар'
LANDUSE_6 = u'Улсын тусгай хэрэгцээний газар'

class NavigatorWidget(QDockWidget, Ui_NavigatorWidget, DatabaseHelper):

    def __init__(self,  plugin, parent=None):

        super(NavigatorWidget,  self).__init__(parent)
        DatabaseHelper.__init__(self)

        self.setupUi(self)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.plugin = plugin
        self.session = SessionHandler().session_instance()

        self.userSettings = None
        self.khashaa_model = None
        self.khashaa_proxy_model = None
        self.khashaa_completer = None
        self.current_dialog = None
        self.street_model = None
        self.street_proxy_model = None
        self.street_completer = None

        self.contract_date.setDate(QDate.currentDate())
        self.record_date_edit.setDate(QDate.currentDate())
        self.decision_date.setDate(QDate.currentDate())
        self.case_completion_date_edit.setDate(QDate.currentDate())
        self.application_datetime_edit.setDate(QDate.currentDate())

        self.__setup_combo_boxes()
        self.working_l1_cbox.currentIndexChanged.connect(self.__working_l1_changed)
        self.working_l2_cbox.currentIndexChanged.connect(self.__working_l2_changed)
        self.__setup_twidgets()
        self.__load_role_settings()
        # self.__setup_permissions()
        self.__user_right_permissions()
        self.__report_setup()
        self.tabWidget.setCurrentIndex(0)

        self.year_sbox.setMinimum(1950)
        self.year_sbox.setMaximum(2200)
        self.year_sbox.setSingleStep(1)
        self.year_sbox.setValue(QDate.currentDate().year())

        if self.working_l1_cbox.count() == 1:
            self.working_l1_cbox.setCurrentIndex(-1)
            self.working_l1_cbox.setCurrentIndex(0)
        self.progressBar.setMinimum(1)
        self.progressBar.setValue(0)
        self.progressBar.setVisible(False)

        #Gt's Reports values
        self.session = SessionHandler().session_instance()
        self.begin_year_sbox.setMinimum(1900)
        self.begin_year_sbox.setMaximum(2200)
        self.begin_year_sbox.setSingleStep(1)
        self.begin_year_sbox.setValue(QDate.currentDate().year())

        self.end_date = (str(self.begin_year_sbox.value() + 1) + '-01-01')
        self.end_date = datetime.strptime(self.end_date, "%Y-%m-%d").date()

        self.before_date = (str(self.begin_year_sbox.value()) + '-01-01')
        self.before_date = datetime.strptime(self.before_date, "%Y-%m-%d").date()

        self.after_year_date = (str(self.begin_year_sbox.value() + 2) + '-01-01')
        self.after_year_date = datetime.strptime(self.after_year_date, "%Y-%m-%d").date()

        self.userSettings = None
        self.__setup_combo_box()
        self.__load_role_setting()
        self.progressBar.setMinimum(1)
        self.progressBar.setValue(0)
        self.progressBar.setVisible(False)
        self.__setup_address_fill()

        # while True:
        #     self.__auto_find()

    def __setup_twidgets(self):

        self.context_menu = QMenu()
        self.zoom_to_parcel_action = QAction(QIcon(":/plugins/lm2/parcel.png"), self.tr("Zoom to parcel"), self)
        self.copy_number_action = QAction(QIcon(":/plugins/lm2/copy.png"), self.tr("Copy number"), self)
        self.context_menu.addAction(self.zoom_to_parcel_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.copy_number_action)
        self.zoom_to_parcel_action.triggered.connect(self.on_zoom_to_parcel_action_clicked)
        self.copy_number_action.triggered.connect(self.on_copy_number_action_clicked)

        self.contract_context_menu = QMenu()
        self.land_fee_payments_action = QAction(QIcon(":/plugins/lm2/landfeepayment.png"),
                                                self.tr("Register Land Fee Payments"), self)
        self.land_fee_payments_action.triggered.connect(self.__show_land_fee_payments_dialog)
        self.contract_context_menu.addAction(self.land_fee_payments_action)
        self.contract_context_menu.addAction(self.zoom_to_parcel_action)
        self.contract_context_menu.addSeparator()
        self.contract_context_menu.addAction(self.copy_number_action)

        self.record_context_menu = QMenu()
        self.land_tax_payments_action = QAction(QIcon(":/plugins/lm2/landtaxpayment.png"),
                                                self.tr("Register Land Tax Payments"), self)
        self.land_tax_payments_action.triggered.connect(self.__show_land_tax_payments_dialog)
        self.record_context_menu.addAction(self.land_tax_payments_action)
        self.record_context_menu.addAction(self.zoom_to_parcel_action)
        self.record_context_menu.addSeparator()
        self.record_context_menu.addAction(self.copy_number_action)

        self.person_results_twidget.setColumnCount(1)
        self.person_results_twidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.person_results_twidget.horizontalHeader().setVisible(False)
        self.person_results_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.person_results_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.person_results_twidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.person_results_twidget.customContextMenuRequested.connect(self.on_custom_context_menu_requested)
        self.person_results_twidget.setDragEnabled(True)

        self.application_results_twidget.setColumnCount(1)
        self.application_results_twidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.application_results_twidget.horizontalHeader().setVisible(False)
        self.application_results_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.application_results_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.application_results_twidget.setDragEnabled(True)
        self.application_results_twidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.application_results_twidget.customContextMenuRequested.connect(self.on_custom_context_menu_requested)

        self.decision_results_twidget.setColumnCount(1)
        self.decision_results_twidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.decision_results_twidget.horizontalHeader().setVisible(False)
        self.decision_results_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.decision_results_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.decision_results_twidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.decision_results_twidget.customContextMenuRequested.connect(self.on_custom_context_menu_requested)

        self.contract_results_twidget.setColumnCount(1)
        self.contract_results_twidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.contract_results_twidget.horizontalHeader().setVisible(False)
        self.contract_results_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.contract_results_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.contract_results_twidget.setDragEnabled(True)
        self.contract_results_twidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.contract_results_twidget.customContextMenuRequested.connect(self.on_custom_context_menu_requested)

        self.record_results_twidget.setColumnCount(1)
        self.record_results_twidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.record_results_twidget.horizontalHeader().setVisible(False)
        self.record_results_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.record_results_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.record_results_twidget.setDragEnabled(True)
        self.record_results_twidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.record_results_twidget.customContextMenuRequested.connect(self.on_custom_context_menu_requested)

        self.parcel_results_twidget.setColumnCount(1)
        self.parcel_results_twidget.setDragEnabled(True)
        self.parcel_results_twidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.parcel_results_twidget.horizontalHeader().setVisible(False)
        self.parcel_results_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.parcel_results_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parcel_results_twidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.parcel_results_twidget.customContextMenuRequested.connect(self.on_custom_context_menu_requested)

        self.case_results_twidget.setColumnCount(1)
        self.case_results_twidget.setDragEnabled(False)
        self.case_results_twidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.case_results_twidget.horizontalHeader().setVisible(False)
        self.case_results_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.case_results_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.case_results_twidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.case_results_twidget.customContextMenuRequested.connect(self.on_custom_context_menu_requested)

        self.report_result_twidget.setAlternatingRowColors(True)
        self.report_result_twidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.report_result_twidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.report_result_twidget.setSelectionMode(QTableWidget.SingleSelection)
        self.report_result_twidget.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)
        self.report_result_twidget.hide()

    def __load_role_settings(self):

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)

        if self.userSettings.pa_till.year == 9999:
            self.infinity_check_box.setChecked(True)
            self.till_date_edit.setEnabled(False)
        else:
            self.till_date_edit.setDate(self.userSettings.pa_till)

        self.from_date_edit.setDate(self.userSettings.pa_from)
        self.extent_rbutton.setChecked(True)

        self.__create_person_view()
        self.__create_application_view()
        self.__create_contract_view()
        self.__create_decision_view()
        self.__create_parcel_view()
        self.__create_tmp_parcel_view()
        self.__create_record_view()
        self.__create_maintenance_case_view()
        self.__create_parcel_view_gts()
        self.__create_fee_unifeid_view()

    def __setup_combo_boxes(self):

        try:
            PluginUtils.populate_au_level1_cbox(self.aimag_cbox)
            PluginUtils.populate_au_level1_cbox(self.working_l1_cbox, False)

            l1_code = self.working_l1_cbox.itemData(self.working_l1_cbox.currentIndex(), Qt.UserRole)
            PluginUtils.populate_au_level2_cbox(self.working_l2_cbox, l1_code, False)

            cl_applicationstatus = self.session.query(ClApplicationStatus).order_by(ClApplicationStatus.code).all()
            cl_landusetype = self.session.query(ClLanduseType).all()
            cl_landofficer = self.session.query(SetRole).all()
            cl_app_type = self.session.query(ClApplicationType). \
                filter(and_(ClApplicationType.code != ApplicationType.pasture_use,
                            ClApplicationType.code != ApplicationType.right_land)).all()
            cl_person_type = self.session.query(ClPersonType).all()
            cl_contract_status = self.session.query(ClContractStatus).all()
            cl_record_status = self.session.query(ClRecordStatus).all()

            set_surveyors = self.session.query(SetSurveyor).all()
            set_roles = self.session.query(SetRole).order_by(SetRole.user_name)

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("Sql Error"), e.message)
            return

        self.status_cbox.addItem("*", -1)
        self.office_in_charge_cbox.addItem("*", -1)
        self.next_officer_in_charge_cbox.addItem("*", -1)
        self.land_use_type_cbox.addItem("*", -1)
        self.surveyed_by_land_officer_cbox.addItem("*", -1)
        self.finalized_by_cbox.addItem("*", -1)
        self.surveyed_by_company_cbox.addItem("*", -1)
        self.app_type_cbox.addItem("*", -1)
        self.person_type_cbox.addItem("*", -1)
        self.application_type_cbox.addItem("*", -1)
        self.contract_status_cbox.addItem("*", -1)
        self.record_status_cbox.addItem("*", -1)

        self.case_status_cbox.addItem("*", -1)
        self.case_status_cbox.addItem(self.tr("Completed"), Constants.CASE_STATUS_COMPLETED)
        self.case_status_cbox.addItem(self.tr("In progress"), Constants.CASE_STATUS_IN_PROGRESS)

        if set_surveyors is not None:
            for surveryor in set_surveyors:
                company = self.session.query(SetSurveyCompany).filter(SetSurveyCompany.id == surveryor.company).one()
                display_name = surveryor.surname + ' ' + surveryor.first_name + ' (' + company.name + ')'
                self.surveyed_by_company_cbox.addItem(display_name, surveryor.id)
        if cl_landofficer is not None:
            # try:
            officers = self.session.query(CaMaintenanceCase.created_by).group_by(CaMaintenanceCase.created_by).all()
            # except exc.SQLAlchemyError, e:
            #     self.session.rollback()
            #     raise LM2Exception(QApplication.translate("LM2", "Database Query Error"),
            #                        QApplication.translate("LM2", "Could not execute: {0}").format(e.message))
            for officer in officers:
                self.surveyed_by_land_officer_cbox.addItem(officer.created_by, officer.created_by)
        if cl_landofficer is not None:
            for officer in cl_landofficer:
                session = SessionHandler().session_instance()
                try:
                    sql = "select rolname from pg_user join pg_auth_members on (pg_user.usesysid=pg_auth_members.member) " \
                          "join pg_roles on (pg_roles.oid=pg_auth_members.roleid) where pg_user.usename=:bindName;"

                    result = session.execute(sql, {'bindName': officer.user_name}).fetchall()

                    for right_result in result:

                        if right_result[0] == UserRight.cadastre_update:
                            # restrictions = DatabaseUtils.working_l2_code()
                            # if officer.user_name_real.find(restrictions[1:]) != -1:
                                self.finalized_by_cbox.addItem(officer.user_name, officer.user_name)


                except exc.SQLAlchemyError, e:
                    session.rollback()
                    raise LM2Exception(QApplication.translate("LM2", "Database Query Error"),
                                       QApplication.translate("LM2", "Could not execute: {0}").format(e.message))

                # self.finalized_by_cbox.addItem(officer.user_name, officer.user_name)

        if cl_applicationstatus is not None:
            for status in cl_applicationstatus:
                self.status_cbox.addItem(status.description, status)

        if cl_app_type is not None:
            for app_type in cl_app_type:
                self.app_type_cbox.addItem(app_type.description, app_type)
                #person search
                self.application_type_cbox.addItem(app_type.description, app_type)
        if cl_contract_status is not None:
            for status in cl_contract_status:
                self.contract_status_cbox.addItem(status.description, status)

        if cl_record_status is not None:
            for status in cl_record_status:
                self.record_status_cbox.addItem(status.description, status)

        current_user = DatabaseUtils.current_user()
        restrictions = current_user.restriction_au_level2.split(",")
        soum_code = DatabaseUtils.working_l2_code()
        # for restriction in restrictions:
        #     restriction = restriction.strip()
        if set_roles is not None:
            for role in set_roles:
                l2_code_list = role.restriction_au_level2.split(',')
                if soum_code in l2_code_list:
                    # if role.user_name_real.find(restriction[1:]) != -1:
                    self.office_in_charge_cbox.addItem(role.surname + ", " + role.first_name, role)
                    self.next_officer_in_charge_cbox.addItem(role.surname + ", " + role.first_name, role)

        if cl_landusetype is not None:
            for landuse in cl_landusetype:
                self.land_use_type_cbox.addItem(landuse.description, landuse)

        if cl_person_type is not None:
            for type in cl_person_type:
                self.person_type_cbox.addItem(type.description, type)

    @pyqtSlot(int)
    def on_aimag_cbox_currentIndexChanged(self, index):

        l1_code = self.aimag_cbox.itemData(index)

        self.soum_cbox.clear()
        self.bag_cbox.clear()

        if l1_code == -1 or not l1_code:
            return
        elif l1_code == 01:
            PluginUtils.populate_au_level2_cbox(self.soum_cbox, l1_code)
        else:
            try:
                if l1_code.startswith('1') or l1_code.startswith('01'):
                    PluginUtils.populate_au_level3_cbox(self.bag_cbox, l1_code)
                else:
                    PluginUtils.populate_au_level2_cbox(self.soum_cbox, l1_code)
            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("Sql Error"), e.message)
                return

    def __working_l1_changed(self, index):

        l1_code = self.working_l1_cbox.itemData(index)
        try:
            role = DatabaseUtils.current_user()
            if l1_code == -1 or not l1_code:
                return
            self.create_savepoint()
            role.working_au_level1 = l1_code
            self.commit()
            PluginUtils.populate_au_level2_cbox(self.working_l2_cbox, l1_code, False, True, False)

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_message(self,  self.tr("Sql Error"), e.message)
            return

    @pyqtSlot(int)
    def on_soum_cbox_currentIndexChanged(self, index):

        l2_code = self.soum_cbox.itemData(index)

        if l2_code == -1 or not l2_code:
            return
        else:
            try:
                PluginUtils.populate_au_level3_cbox(self.bag_cbox, l2_code)
            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("Sql Error"), e.message)

    @pyqtSlot(int)
    def on_bag_cbox_currentIndexChanged(self, index):

        l3_code = self.bag_cbox.itemData(index)

        if l3_code == -1 or not l3_code:
            return
        else:
            try:
                # Streets
                street_names = []
                for street_name in self.session.query(CaParcel.address_streetname).distinct().filter(CaParcel.geometry.ST_Within(AuLevel3.geometry)).filter(AuLevel3.code == l3_code).order_by(CaParcel.address_streetname):
                    if street_name[0]:
                        street_names.append(street_name[0])

                self.street_model = QStringListModel(street_names)

                self.street_proxy_model = QSortFilterProxyModel()
                self.street_proxy_model.setSourceModel(self.street_model)

                self.street_completer = QCompleter(self.street_proxy_model, self,
                                                   activated=self.on_street_completer_activated)
                self.street_completer.setCompletionMode(QCompleter.PopupCompletion)

                self.street_line_edit.setCompleter(self.street_completer)
                self.street_line_edit.textEdited.connect(self.street_proxy_model.setFilterFixedString)

                # Khashaas
                khashaas = []
                for khashaa in self.session.query(CaParcel.address_khashaa).distinct()\
                                .filter(CaParcel.geometry.ST_Within(AuLevel3.geometry))\
                                .filter(AuLevel3.code == l3_code).order_by(CaParcel.address_khashaa):

                    if khashaa[0]:
                        khashaas.append(khashaa[0])

                self.khashaa_model = QStringListModel(khashaas)
                self.khashaa_proxy_model = QSortFilterProxyModel()
                self.khashaa_proxy_model.setSourceModel(self.khashaa_model)

                self.khashaa_completer = QCompleter(self.khashaa_proxy_model, self,
                                                    activated=self.on_khashaa_completer_activated)
                self.khashaa_completer.setCompletionMode(QCompleter.PopupCompletion)

                self.khashaa_line_edit.setCompleter(self.khashaa_completer)
                self.khashaa_line_edit.textEdited.connect(self.khashaa_proxy_model.setFilterFixedString)

            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("Sql Error"), e.message)
                return

    @pyqtSlot(str)
    def on_street_completer_activated(self, text):

        if not text:
            return

        self.street_completer.activated[str].emit(text)

    @pyqtSlot(str)
    def on_khashaa_completer_activated(self, text):

        if not text:
            return
        self.khashaa_completer.activated[str].emit(text)

    def __working_l2_changed(self, index):

        l2_code = self.working_l2_cbox.itemData(index)

        self.create_savepoint()

        try:
            role = DatabaseUtils.current_user()
            if not l2_code:
                role.working_au_level2 = None
            else:
                role.working_au_level2 = l2_code

            DatabaseUtils.set_working_schema(l2_code)
            self.commit()

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_message(self,  self.tr("Sql Error"), e.message)
            return

    @pyqtSlot(int)
    def on_infinity_check_box_stateChanged(self, state):

        if state == Qt.Checked:
            self.till_date_edit.setEnabled(False)
        else:
            self.till_date_edit.setEnabled(True)

    @pyqtSlot()
    def on_get_extent_button_clicked(self):

        rect = self.plugin.iface.mapCanvas().extent()
        self.extent_east_spinbox.setValue(rect.xMaximum())
        self.extent_west_spinbox.setValue(rect.xMinimum())
        self.extent_north_spinbox.setValue(rect.yMaximum())
        self.extent_south_spinbox.setValue(rect.yMinimum())

    @pyqtSlot(bool)
    def on_admin_unit_rbutton_toggled(self, state):

        if state:
            self.aimag_cbox.setEnabled(True)
            self.soum_cbox.setEnabled(True)
            self.bag_cbox.setEnabled(True)
            self.street_line_edit.setEnabled(True)
            self.khashaa_line_edit.setEnabled(True)
            self.buffer_spinbox.setEnabled(True)
            self.extent_north_spinbox.setEnabled(False)
            self.extent_south_spinbox.setEnabled(False)
            self.extent_west_spinbox.setEnabled(False)
            self.extent_east_spinbox.setEnabled(False)
            self.get_extent_button.setEnabled(False)
        else:
            self.extent_north_spinbox.setEnabled(True)
            self.extent_south_spinbox.setEnabled(True)
            self.extent_west_spinbox.setEnabled(True)
            self.extent_east_spinbox.setEnabled(True)
            self.get_extent_button.setEnabled(True)
            self.aimag_cbox.setEnabled(False)
            self.soum_cbox.setEnabled(False)
            self.bag_cbox.setEnabled(False)
            self.street_line_edit.setEnabled(False)
            self.khashaa_line_edit.setEnabled(False)
            self.buffer_spinbox.setEnabled(False)

    @pyqtSlot()
    def on_clear_b_box_button_clicked(self):

        # self.session.execute("refresh materialized view webgis.view_contract")
        self.extent_west_spinbox.setValue(0)
        self.extent_east_spinbox.setValue(0)
        self.extent_south_spinbox.setValue(0)
        self.extent_north_spinbox.setValue(0)

    @pyqtSlot()
    def on_remove_button_clicked(self):

        database = QSettings().value(SettingsConstants.DATABASE_NAME, '', type=str)
        host = QSettings().value(SettingsConstants.HOST, '', type=str)
        port = QSettings().value(SettingsConstants.PORT, '5432', type=str)
        user = QSettings().value(SettingsConstants.USER, '', type=str)

        layermap = QgsMapLayerRegistry.instance().mapLayers()
        for layer_id, layer in layermap.iteritems():

            if layer.type() != QgsMapLayer.VectorLayer or layer.dataProvider().name() != "postgres":
                continue
            uri = QgsDataSourceURI(layer.source())
            if uri.database() != database or uri.host() != host or uri.port() != port or uri.username() != user:
                continue

            geometry_column = uri.geometryColumn().upper()
            subset_string = layer.subsetString()

            if subset_string.upper().find('ST_WITHIN') != -1 \
                    or subset_string.upper().find(geometry_column + ' &&') != -1 \
                    or subset_string.upper().find('ST_TRANSFORM') != -1:
                idx = subset_string.upper().find(' AND ')
                if idx == -1:
                    subset_string = ''
                else:
                    subset_string = subset_string[idx+5]

            layer.setSubsetString(subset_string)

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.plugin.iface.mapCanvas().refresh()
        QApplication.restoreOverrideCursor()
        project = QgsProject.instance()
        project.setDirty(True)

    @pyqtSlot()
    def on_apply_button_clicked(self):

        database = QSettings().value(SettingsConstants.DATABASE_NAME, '', type=str)
        host = QSettings().value(SettingsConstants.HOST, '', type=str)
        port = QSettings().value(SettingsConstants.PORT, '5432', type=str)
        user = QSettings().value(SettingsConstants.USER, '', type=str)

        core_subset_string = None
        layermap = QgsMapLayerRegistry.instance().mapLayers()
        for layer_id, layer in layermap.iteritems():

            if layer.type() != QgsMapLayer.VectorLayer or layer.dataProvider().name() != "postgres":
                continue
            uri = QgsDataSourceURI(layer.source())
            if uri.database() != database or uri.host() != host or uri.port() != port or uri.username() != user:
                continue

            subset_string = layer.subsetString()
            geometry_column = uri.geometryColumn().upper()

            if subset_string.upper().find('ST_WITHIN') != -1 \
                    or subset_string.upper().find(geometry_column + ' &&') != -1 \
                    or subset_string.upper().find('ST_TRANSFORM') != -1:

                idx = subset_string.upper().find(' AND ')
                if idx == -1:
                    subset_string = ''
                else:
                    subset_string = subset_string[idx:]
            else:
                if len(subset_string) > 0:
                    subset_string = ' AND ' + subset_string

            if self.admin_unit_rbutton.isChecked():
                if core_subset_string is None:
                    core_subset_string = self.__getAdminUnitSubsetString(geometry_column)
            else:
                if core_subset_string is None:
                    core_subset_string = self.__getBBoxSubsetString(layer)

            subset_string = core_subset_string + subset_string
            layer.setSubsetString(subset_string)

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.plugin.iface.mapCanvas().refresh()
        QApplication.restoreOverrideCursor()
        project = QgsProject.instance()
        project.setDirty(True)

    def __getBBoxSubsetString(self, layer):

        x_min = self.extent_west_spinbox.value()
        x_max = self.extent_east_spinbox.value()
        y_min = self.extent_south_spinbox.value()
        y_max = self.extent_north_spinbox.value()

        srs_id = layer.crs().postgisSrid()

        point1 = QgsPoint(x_min, y_min)
        point2 = QgsPoint(x_max, y_max)

        point1 = self.plugin.transformPoint(point1, srs_id)
        point2 = self.plugin.transformPoint(point2, srs_id)

        uri = QgsDataSourceURI(layer.source())
        geometry_column = uri.geometryColumn()

        return "ST_Within({0}, ST_SetSRID(ST_MakeBox2D(ST_Point({1}), ST_Point({2})), {3}))".format(geometry_column, point1.toString(), point2.toString(), srs_id)

    def __getAdminUnitSubsetString(self, geometry_column):

        au_table_name = 'au_level1'
        au_code = self.aimag_cbox.itemData(self.aimag_cbox.currentIndex())
        current_buffer = self.buffer_spinbox.value()
        extent = []

        if self.soum_cbox.currentIndex() > 0:  # '*'
            au_table_name = 'au_level2'
            au_code = self.soum_cbox.itemData(self.soum_cbox.currentIndex())

        if self.bag_cbox.currentIndex() > 0:  # '*'
            au_table_name = 'au_level3'
            au_code = self.bag_cbox.itemData(self.bag_cbox.currentIndex())
            khashaa = self.khashaa_line_edit.text().strip()
            street = self.street_line_edit.text().strip()

            if len(khashaa) > 0 or len(street) > 0:
                try:

                    if len(khashaa) > 0 and len(street) > 0:
                        extent = self.session.query(CaParcel.geometry.ST_Extent()).\
                            filter(CaParcel.address_khashaa == khashaa).\
                            filter(CaParcel.address_streetname == street).\
                            filter(CaParcel.geometry.ST_Within(AuLevel3.geometry)).\
                            filter(AuLevel3.code == au_code).one()

                    elif len(khashaa) > 0 and len(street) == 0:
                        extent = self.session.query(CaParcel.geometry.ST_Extent()).\
                            filter(CaParcel.address_khashaa == khashaa).\
                            filter(CaParcel.geometry.ST_Within(AuLevel3.geometry)).\
                            filter(AuLevel3.code == au_code).one()

                    else:
                        extent = self.session.query(CaParcel.geometry.ST_Extent()).\
                            filter(CaParcel.address_streetname == street).\
                            filter(CaParcel.geometry.ST_Within(AuLevel3.geometry)).\
                            filter(AuLevel3.code == au_code).one()
                except SQLAlchemyError, e:
                    PluginUtils.show_message(self,  self.tr("Sql Error"), e.message)
                    return None

                if extent[0]:
                    box_text = extent[0]
                    point1 = box_text[box_text.find('(')+1:box_text.find(')')].split(',')[0]
                    point2 = box_text[box_text.find('(')+1:box_text.find(')')].split(',')[1]

                    if current_buffer == 0:
                        return "ST_Within({0}, ST_Buffer(ST_SetSRID(ST_MakeBox2D(ST_PointFromText('POINT({1})'), " \
                               "ST_PointFromText('POINT({2})')), {3}), 0.00005))".format(geometry_column, point1, point2, 4326)
                    else:

                        where_clause = "ST_Within(ST_Transform({0}, base.find_utm_srid(St_Centroid({0}))), ST_Buffer(ST_Transform(ST_SetSRID(ST_MakeBox2D(ST_PointFromText('POINT({1})'), " \
                                "ST_PointFromText('POINT({2})')), {3}), base.find_utm_srid(St_Centroid({0}))), {4}))"\
                                .format(geometry_column, point1, point2, 4326, current_buffer)

                        return where_clause

        if current_buffer != 0:
            subset_string = "ST_Transform(GEOMETRY, base.find_utm_srid(ST_Centroid(GEOMETRY))) && (SELECT st_buffer(ST_Transform({0}, base.find_utm_srid(ST_Centroid({0}))), {3}) FROM admin_units.{1} WHERE code = '{2}')"\
                .format(geometry_column, au_table_name, au_code, current_buffer)
            #QMessageBox.information(None, "test", subset_string)
        else:
            subset_string = "{0} && (SELECT {0} FROM admin_units.{1} WHERE code = '{2}')"\
                .format(geometry_column, au_table_name, au_code)

        return subset_string

    @pyqtSlot()
    def on_temp_filter_apply_button_clicked(self):

        self.create_savepoint()

        try:
            if self.infinity_check_box.isChecked():
                self.userSettings.pa_till = date(9999, 12, 31)
            else:
                self.userSettings.pa_till = DatabaseUtils.convert_date(self.till_date_edit.date())

            self.userSettings.pa_from = DatabaseUtils.convert_date(self.from_date_edit.date())

            self.commit()

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_message(self,  self.tr("Sql Error"), e.message)
            return

        self.plugin.iface.mapCanvas().refresh()

    def __create_person_view(self):

        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        sql = ""

        for au_level2 in au_level2_list:

            au_level2 = au_level2.strip()
            if not sql:
                sql = "Create temp view person_search as" + "\n"
            else:
                sql = sql + "UNION" + "\n"

            select = "SELECT person.name, person.first_name, person.middle_name, person.person_id, person.state_registration_no, " \
                     "person.mobile_phone, person.phone, parcel.parcel_id, tmp_parcel.parcel_id tmp_parcel_id, application.app_no, decision.decision_no, " \
                     "contract.contract_no, record.record_no, person.type, application.app_type " \
                     "FROM base.bs_person person " \
                     "left join s{0}.ct_application_person_role app_per on app_per.person = person.person_id " \
                     "left join s{0}.ct_application application on application.app_no = app_per.application " \
                     "left join s{0}.ca_parcel parcel on parcel.parcel_id = application.parcel " \
                     "left join s{0}.ca_tmp_parcel tmp_parcel on tmp_parcel.parcel_id = application.tmp_parcel " \
                     "left join s{0}.ct_decision_application dec_app on dec_app.application = application.app_no " \
                     "left join s{0}.ct_decision decision on decision.decision_no = dec_app.decision " \
                     "left join s{0}.ct_record_application_role rec_app on rec_app.application = application.app_no " \
                     "left join s{0}.ct_ownership_record record on record.record_no = rec_app.record " \
                     "left join s{0}.ct_contract_application_role contract_app on application.app_no = contract_app.application " \
                     "left join s{0}.ct_contract contract on contract_app.contract = contract.contract_no ".format(au_level2)  + "\n"
            sql = sql + select

        sql = "{0} order by person_id;".format(sql)

        # try:
        self.session.execute(sql)
        self.commit()

        # except SQLAlchemyError, e:
        #     PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
        #     return

    def __create_fee_unifeid_view(self):

        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        sql = ""

        for au_level2 in au_level2_list:

            au_level2 = au_level2.strip()
            if not sql:
                sql = "Create temp view land_fee_unified as" + "\n"
            else:
                sql = sql + "UNION" + "\n"

            select = "SELECT contract.contract_no, payment.year_paid_for,contract.status, fee.fee_contract, sum(payment.amount_paid) as paid, person.person_id, p_paid.p_paid ,landuse.description as landuse, " \
                        "decision.decision_date ,decision.decision_no, person.first_name, person.name, person.contact_surname, person.contact_first_name ,person.address_street_name as person_streetname, person.address_khaskhaa as person_khashaa, " \
                        "parcel.parcel_id, contract.certificate_no, au3_person.name as person_bag,au3.name as bag_name, person.mobile_phone, parcel.area_m2, application.approved_duration, parcel.address_streetname, parcel.address_khashaa " \
                     "FROM s{0}.ct_contract contract " \
                     "LEFT JOIN s{0}.ct_contract_application_role con_app on con_app.contract = contract.contract_no "\
                     "LEFT JOIN s{0}.ct_application application ON application.app_no = con_app.application " \
                     "LEFT JOIN s{0}.ct_application_person_role app_pers on application.app_no = app_pers.application "\
                     "LEFT JOIN base.bs_person person ON app_pers.person = person.person_id " \
                     "LEFT JOIN s{0}.ca_parcel parcel on parcel.parcel_id = application.parcel " \
                     "LEFT JOIN admin_units.au_level3 au3 on ST_Within(parcel.geometry,au3.geometry) "\
                     "LEFT JOIN admin_units.au_level3 au3_person on person.address_au_level3 = au3_person.code " \
                     "LEFT JOIN codelists.cl_landuse_type landuse on parcel.landuse = landuse.code " \
                     "LEFT JOIN s{0}.ct_fee fee on contract.contract_no = fee.contract " \
                     "LEFT JOIN s{0}.ct_decision_application dec_app on dec_app.application = application.app_no " \
                     "LEFT JOIN s{0}.ct_decision decision on decision.decision_no = dec_app.decision " \
                     "LEFT JOIN (select p.contract, sum(p.amount_paid) as p_paid from s{0}.ct_fee_payment p where p.year_paid_for < date_part('year', NOW())::int group by p.contract) p_paid on contract.contract_no = p_paid.contract " \
                     "LEFT JOIN s{0}.ct_fee_payment payment on fee.contract = payment.contract".format(au_level2)  + "\n"

            sql = sql + select
            sql = "{0} group by contract_no, payment.year_paid_for,contract.status,fee.fee_contract, person.person_id, p_paid.p_paid,decision.decision_no, decision.decision_date, contract.certificate_no, parcel.parcel_id,au3.name, application.approved_duration,landuse.description,parcel.area_m2, parcel.address_streetname, parcel.address_khashaa,au3_person.name ".format(sql)
        sql = "{0}  order by contract_no;".format(sql)
        # try:
        self.session.execute(sql)
        self.commit()

        # except SQLAlchemyError, e:
        #     PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
        #     return

    def __create_application_view(self):

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

        # try:
        self.session.execute(sql)
        self.commit()
        # except SQLAlchemyError, e:
        #     PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
        #     return

    def __create_decision_view(self):

        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        sql = ""

        for au_level2 in au_level2_list:

            au_level2 = au_level2.strip()
            if not sql:
                sql = "Create temp view decision_search as" + "\n"
            else:
                sql = sql + "UNION" + "\n"

            select = "SELECT decision.decision_no, decision.decision_date, person.person_id, person.name, person.middle_name, person.first_name, parcel.parcel_id, application.app_no, contract.contract_no, record.record_no " \
                     "FROM s{0}.ct_decision decision " \
                     "LEFT JOIN s{0}.ct_decision_application dec_app ON dec_app.decision = decision.decision_no " \
                     "LEFT JOIN s{0}.ct_application application ON dec_app.application = application.app_no " \
                     "LEFT JOIN s{0}.ct_application_person_role app_pers ON application.app_no = app_pers.application " \
                     "LEFT JOIN base.bs_person person ON app_pers.person = person.person_id " \
                     "LEFT JOIN s{0}.ca_parcel parcel ON parcel.parcel_id = application.parcel " \
                     "LEFT JOIN s{0}.ct_record_application_role rec_app ON rec_app.application = application.app_no " \
                     "LEFT JOIN s{0}.ct_ownership_record record ON record.record_no = rec_app.record " \
                     "LEFT JOIN s{0}.ct_contract_application_role con_app ON con_app.application = application.app_no " \
                     "LEFT JOIN s{0}.ct_contract contract ON contract.contract_no = con_app.contract".format(au_level2)  + "\n"

            sql = sql + select

        sql = "{0} order by decision_no;".format(sql)

        try:
            self.session.execute(sql)
            self.commit()

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    def __create_contract_view(self):

        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        sql = ""

        for au_level2 in au_level2_list:

            au_level2 = au_level2.strip()
            if not sql:
                sql = "Create temp view contract_search as" + "\n"
            else:
                sql = sql + "UNION" + "\n"

            select = "SELECT contract.contract_no, contract.certificate_no, contract.status ,app_pers.role as person_role,"\
                     "contract.contract_date, person.person_id, person.name, person.middle_name, person.first_name, "\
                     "parcel.parcel_id, application.app_no, decision.decision_no, au2.code as au2_code, application.app_type " \
                     "FROM s{0}.ct_contract contract " \
                     "LEFT JOIN s{0}.ct_contract_application_role con_app on con_app.contract = contract.contract_no "\
                     "LEFT JOIN s{0}.ct_application application ON application.app_no = con_app.application " \
                     "LEFT JOIN s{0}.ct_application_person_role app_pers on application.app_no = app_pers.application "\
                     "LEFT JOIN base.bs_person person ON app_pers.person = person.person_id " \
                     "LEFT JOIN s{0}.ca_parcel parcel on parcel.parcel_id = application.parcel " \
                     "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry) " \
                     "LEFT JOIN s{0}.ct_decision_application dec_app on dec_app.application = application.app_no " \
                     "LEFT JOIN s{0}.ct_decision decision on decision.decision_no = dec_app.decision".format(au_level2)  + "\n"

            sql = sql + select

        sql = "{0} order by contract_no;".format(sql)

        try:
            self.session.execute(sql)
            self.commit()

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    def __create_record_view(self):

            au_level2_string = self.userSettings.restriction_au_level2
            au_level2_list = au_level2_string.split(",")
            sql = ""

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql:
                    sql = "Create temp view record_search as" + "\n"
                else:
                    sql = sql + "UNION" + "\n"

                select = "SELECT record.status, record.record_no, record.record_date, person.person_id, person.name, person.middle_name, person.first_name, parcel.parcel_id, application.app_no, decision.decision_no, au2.code as au2_code " \
                         "FROM s{0}.ct_ownership_record record " \
                         "LEFT JOIN s{0}.ct_record_application_role rec_app on rec_app.record = record.record_no " \
                         "LEFT JOIN s{0}.ct_application application ON application.app_no = rec_app.application " \
                         "LEFT JOIN s{0}.ct_application_person_role app_pers on application.app_no = app_pers.application " \
                         "LEFT JOIN base.bs_person person ON app_pers.person = person.person_id " \
                         "LEFT JOIN s{0}.ca_parcel parcel on parcel.parcel_id = application.parcel " \
                         "LEFT JOIN s{0}.ct_decision_application dec_app on dec_app.application = application.app_no " \
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry) " \
                         "LEFT JOIN s{0}.ct_decision decision on decision.decision_no = dec_app.decision".format(au_level2)  + "\n"

                sql = sql + select

            sql = "{0} order by record_no;".format(sql)

            try:
                self.session.execute(sql)
                self.commit()

            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
                return

    def __create_parcel_view(self):

            au_level2_string = self.userSettings.restriction_au_level2
            au_level2_list = au_level2_string.split(",")
            sql = ""

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql:
                    sql = "Create temp view parcel_search as" + "\n"
                else:
                    sql = sql + "UNION" + "\n"

                select = "SELECT parcel.parcel_id, app_pers.main_applicant ,app_pers.role as person_role, parcel.old_parcel_id, parcel.geo_id, parcel.landuse, person.person_id, " \
                         "person.name, person.middle_name, person.first_name,  application.app_no, decision.decision_no, contract.contract_no, contract.status contract_status, " \
                         "record.record_no, record.status record_status, parcel.address_streetname, parcel.address_khashaa, au2.code as au2_code " \
                         "FROM s{0}.ca_parcel parcel " \
                         "LEFT JOIN s{0}.ct_application application on application.parcel = parcel.parcel_id " \
                         "LEFT JOIN s{0}.ct_application_person_role app_pers on application.app_no = app_pers.application " \
                         "LEFT JOIN base.bs_person person ON app_pers.person = person.person_id " \
                         "LEFT JOIN s{0}.ct_contract_application_role con_app on con_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_contract contract on con_app.contract = contract.contract_no " \
                         "LEFT JOIN s{0}.ct_record_application_role rec_app on rec_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_ownership_record record on rec_app.record = record.record_no " \
                         "LEFT JOIN s{0}.ct_decision_application dec_app on dec_app.application = application.app_no " \
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry) " \
                         "LEFT JOIN s{0}.ct_decision decision on decision.decision_no = dec_app.application".format(au_level2)  + "\n"

                sql = sql + select

            sql = "{0} order by parcel_id;".format(sql)

            try:
                self.session.execute(sql)
                self.commit()

            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
                return

    def __create_tmp_parcel_view(self):

            au_level2_string = self.userSettings.restriction_au_level2
            au_level2_list = au_level2_string.split(",")
            sql = ""

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql:
                    sql = "Create temp view tmp_parcel_search as" + "\n"
                else:
                    sql = sql + "UNION" + "\n"

                select = "SELECT parcel.parcel_id, parcel.old_parcel_id, parcel.geo_id, parcel.landuse, person.person_id, person.name, person.middle_name, person.first_name,  application.app_no, decision.decision_no, contract.contract_no, record.record_no, parcel.address_streetname, parcel.address_khashaa, au2.code as au2_code " \
                         "FROM s{0}.ca_tmp_parcel parcel " \
                         "LEFT JOIN s{0}.ct_application application on application.tmp_parcel = parcel.parcel_id " \
                         "LEFT JOIN s{0}.ct_application_person_role app_pers on application.app_no = app_pers.application " \
                         "LEFT JOIN base.bs_person person ON app_pers.person = person.person_id " \
                         "LEFT JOIN s{0}.ct_contract_application_role con_app on con_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_contract contract on con_app.contract = contract.contract_no " \
                         "LEFT JOIN s{0}.ct_record_application_role rec_app on rec_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_ownership_record record on rec_app.record = record.record_no " \
                         "LEFT JOIN s{0}.ct_decision_application dec_app on dec_app.application = application.app_no " \
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry) " \
                         "LEFT JOIN s{0}.ct_decision decision on decision.decision_no = dec_app.application".format(au_level2)  + "\n"

                sql = sql + select

            sql = "{0} order by parcel_id;".format(sql)

            try:
                self.session.execute(sql)
                self.commit()

            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
                return

    def __create_maintenance_case_view(self):

        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        sql = ""

        for au_level2 in au_level2_list:

            au_level2 = au_level2.strip()
            if not sql:
                sql = "Create temp view maintenance_search as" + "\n"
            else:
                sql = sql + "UNION" + "\n"

            select = "SELECT m_case.id, m_case.completion_date, m_case.created_by, m_case.surveyed_by_land_office, m_case.surveyed_by_surveyor, " \
                     "m_case.completed_by, parcel_case.parcel, building.building, application.app_no, '{0}' as soum, company.id as company, person.person_id, person.name, person.first_name " \
                     "FROM s{0}.ca_maintenance_case m_case " \
                     "left join s{0}.ca_parcel_maintenance_case parcel_case on parcel_case.maintenance = m_case.id " \
                     "left join s{0}.ca_building_maintenance_case building on building.maintenance = m_case.id " \
                     "left join s{0}.ct_application application on application.maintenance_case = m_case.id " \
                     "LEFT JOIN s{0}.ct_application_person_role app_pers on application.app_no = app_pers.application " \
                     "LEFT JOIN base.bs_person person ON app_pers.person = person.person_id " \
                     "left join settings.set_surveyor surveyor on m_case.surveyed_by_surveyor = surveyor.id " \
                     "left join settings.set_survey_company company on surveyor.company = company.id".format(au_level2) + "\n"

            sql = sql + select

        sql = "{0} order by id;".format(sql)

        try:
            self.session.execute(sql)
            self.commit()

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    def __selected_parcel_id(self):

        selected_items = self.parcel_results_twidget.selectedItems()

        if len(selected_items) != 1:
            self.error_label.setText(self.tr("Only single selection allowed."))
            return None

        selected_item = selected_items[0]
        parcel_no = selected_item.data(Qt.UserRole)
        return parcel_no

    def __selected_decision(self):

        selected_items = self.decision_results_twidget.selectedItems()

        if len(selected_items) != 1:
            self.error_label.setText(self.tr("Only single selection allowed."))
            return None

        selected_item = selected_items[0]
        decision_no = selected_item.data(Qt.UserRole)
        decision_no_soum = decision_no.split("-")[0]
        DatabaseUtils.set_working_schema(decision_no_soum)

        try:
            decision_instance = self.session.query(CtDecision).filter_by(decision_no=decision_no).one()
        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return None

        return decision_instance

    def __selected_application(self):

        selected_items = self.application_results_twidget.selectedItems()

        if len(selected_items) != 1:
            self.error_label.setText(self.tr("Only single selection allowed."))
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

    def __selected_maintenance_case(self):

        selected_items = self.case_results_twidget.selectedItems()
        case_instance = None

        if len(selected_items) != 1:
            self.error_label.setText(self.tr("Only single selection allowed."))
            return None

        selected_case_item = selected_items[0]
        item_id = selected_case_item.data(Qt.UserRole)
        soum = selected_case_item.data(Qt.UserRole + 1)

        DatabaseUtils.set_working_schema(soum)

        try:
            case_instance = self.session.query(CaMaintenanceCase).filter_by(id=item_id).one()
        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return None

        return case_instance

    def __selected_contract(self):

        selected_items = self.contract_results_twidget.selectedItems()

        if len(selected_items) != 1:
            self.error_label.setText(self.tr("Only single selection allowed."))
            return None

        selected_contract_item = selected_items[0]
        cu_contract_no = selected_contract_item.data(Qt.UserRole)

        l2_code = self.working_l2_cbox.itemData(self.working_l2_cbox.currentIndex())
        DatabaseUtils.set_working_schema(l2_code)

        try:
            contract_instance = self.session.query(CtContract).filter_by(contract_no = cu_contract_no).one()
        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return None

        return contract_instance

    def __selected_record(self):

        selected_items = self.record_results_twidget.selectedItems()

        if len(selected_items) != 1:
            self.error_label.setText(self.tr("Only single selection allowed."))
            return None

        selected_record_item = selected_items[0]
        cu_record_no = selected_record_item.data(Qt.UserRole)

        l2_code = self.working_l2_cbox.itemData(self.working_l2_cbox.currentIndex())
        DatabaseUtils.set_working_schema(l2_code)

        try:
            record_instance = self.session.query(CtOwnershipRecord).filter_by(record_no=cu_record_no).one()
        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return None

        return record_instance

    @pyqtSlot()
    def on_person_find_button_clicked(self):

        self.__search_persons()

    def __search_persons(self):

        try:
            persons = self.session.query(PersonSearch)
            filter_is_set = False
            if self.name_edit.text():
                filter_is_set = True
                right_holder = "%" + self.name_edit.text() + "%"
                persons = persons.filter(or_(func.lower(PersonSearch.name).like(func.lower(right_holder)), func.lower(PersonSearch.first_name).ilike(func.lower(right_holder)), func.lower(PersonSearch.middle_name).ilike(func.lower(right_holder))))

            if self.personal_edit.text():
                filter_is_set = True
                value = "%" + self.personal_edit.text() + "%"
                persons = persons.filter(PersonSearch.person_id.ilike(value))

            if self.state_reg_num_edit.text():
                filter_is_set = True
                value = "%" + self.state_reg_num_edit.text() + "%"
                persons = persons.filter(PersonSearch.state_registration_no.ilike(value))

            if self.mobile_num_edit.text():
                filter_is_set = True
                number = "%" + self.mobile_num_edit.text() + "%"
                persons = persons.filter(or_(PersonSearch.mobile_phone.ilike(number), PersonSearch.phone.ilike(number)))

            if self.person_parcel_num_edit.text():
                filter_is_set = True
                value = "%" + self.person_parcel_num_edit.text() + "%"
                persons_count = persons.filter(PersonSearch.parcel_id.ilike(value)).count()
                if persons_count > 0:
                    persons = persons.filter(PersonSearch.parcel_id.ilike(value))
                else:
                    persons = persons.filter(PersonSearch.tmp_parcel_id.ilike(value))
            if self.person_application_num_edit.text():
                filter_is_set = True
                value = "%" + self.person_application_num_edit.text() + "%"
                persons = persons.filter(PersonSearch.app_no.ilike(value))

            if self.person_decision_num_edit.text():
                filter_is_set = True
                value = "%" + self.person_application_num_edit.text() + "%"
                persons = persons.filter(PersonSearch.decision_no.ilike(value))

            if self.person_contract_num_edit.text():
                filter_is_set = True
                value = "%" + self.person_contract_num_edit.text() + "%"
                persons = persons.filter(or_(PersonSearch.contract_no.ilike(value), PersonSearch.record_no.ilike(value)))

            if not self.person_type_cbox.itemData(self.person_type_cbox.currentIndex()) == -1:
                filter_is_set = True
                person_type = self.person_type_cbox.itemData(self.person_type_cbox.currentIndex()).code
                persons = persons.filter(PersonSearch.type == person_type)
            if not self.application_type_cbox.itemData(self.application_type_cbox.currentIndex()) == -1:
                filter_is_set = True
                app_type = self.application_type_cbox.itemData(self.application_type_cbox.currentIndex()).code
                persons = persons.filter(PersonSearch.app_type == app_type)

            count = 0

            self.__remove_person_items()

            if persons.distinct(PersonSearch.person_id).count() == 0:
                self.error_label.setText(self.tr("No persons found for this search filter."))
                return
            elif filter_is_set is False:
                self.error_label.setText(self.tr("Please specify a search filter."))
                return

            for person in persons.distinct(PersonSearch.name, PersonSearch.person_id).order_by(PersonSearch.name.asc(), PersonSearch.person_id.asc()).all():

                if not person.person_id:
                    person_id = self.tr(" (Id: n.a. )")
                else:
                    person_id = self.tr(" (Id: ") + person.person_id + ")"

                first_name = self.tr(" n.a. ") if not person.first_name else person.first_name

                item = QTableWidgetItem(person.name + ", " + first_name + person_id)
                item.setIcon(QIcon(QPixmap(":/plugins/lm2/person.png")))
                item.setData(Qt.UserRole, person.person_id)
                self.person_results_twidget.insertRow(count)
                self.person_results_twidget.setItem(count, 0, item)
                count += 1

            self.error_label.setText("")
            self.person_results_label.setText(self.tr("Results: ") + str(count))

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    @pyqtSlot(int)
    def on_app_date_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.application_datetime_edit.setEnabled(True)
        else:
            self.application_datetime_edit.setEnabled(False)

    @pyqtSlot()
    def on_application_find_button_clicked(self):

        self.__search_applications()

    def __search_applications(self):

        try:
            applications = self.session.query(ApplicationSearch)
            filter_is_set = False
            sub = self.session.query(ApplicationSearch, func.row_number().over(partition_by = ApplicationSearch.app_no, order_by = (desc(ApplicationSearch.status_date), desc(ApplicationSearch.status))).label("row_number")).subquery()
            applications = applications.select_entity_from(sub).filter(sub.c.row_number == 1)

            applications = applications. \
                filter(and_(ApplicationSearch.app_type != ApplicationType.pasture_use,
                            ApplicationSearch.app_type != ApplicationType.right_land))

            if self.status_cbox.currentIndex() != -1:
                if not self.status_cbox.itemData(self.status_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    status = self.status_cbox.itemData(self.status_cbox.currentIndex()).code

                    applications = applications.filter(ApplicationSearch.status == status)

            if self.office_in_charge_cbox.currentIndex() != -1:
                if not self.office_in_charge_cbox.itemData(self.office_in_charge_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    officer = "%" + self.office_in_charge_cbox.itemData(self.office_in_charge_cbox.currentIndex()).user_name_real + "%"

                    applications = applications.filter(ApplicationSearch.officer_in_charge.ilike(officer))

            if self.application_application_num_edit.text():
                filter_is_set = True
                app_no = "%" + self.application_application_num_edit.text() + "%"
                applications = applications.filter(ApplicationSearch.app_no.ilike(app_no))

            if self.app_type_cbox.currentIndex() != -1:
                if not self.app_type_cbox.itemData(self.app_type_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    applications = applications.filter(ApplicationSearch.app_type == self.app_type_cbox.itemData(self.app_type_cbox.currentIndex()).code)

            if self.next_officer_in_charge_cbox.currentIndex() != -1:
                if not self.next_officer_in_charge_cbox.itemData(self.next_officer_in_charge_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    officer = "%" + self.next_officer_in_charge_cbox.itemData(self.next_officer_in_charge_cbox.currentIndex()).user_name_real + "%"
                    applications = applications.filter(ApplicationSearch.next_officer_in_charge.ilike(officer))

            if self.application_right_holder_name_edit.text():
                filter_is_set = True
                right_holder = self.application_right_holder_name_edit.text()
                if "," in right_holder:
                    right_holder_strings = right_holder.split(",")
                    surname = "%" + right_holder_strings[0].strip() + "%"
                    first_name = "%" + right_holder_strings[1].strip() + "%"
                    applications = applications.filter(and_(func.lower(ApplicationSearch.name).ilike(func.lower(surname)), func.lower(ApplicationSearch.first_name).ilike(func.lower(first_name))))
                else:
                    right_holder = "%" + self.application_right_holder_name_edit.text() + "%"
                    applications = applications.filter(or_(func.lower(ApplicationSearch.name).ilike(func.lower(right_holder)), func.lower(ApplicationSearch.first_name).ilike(func.lower(right_holder)), func.lower(ApplicationSearch.middle_name).ilike(func.lower(right_holder))))

            if self.application_parcel_num_edit.text():
                filter_is_set = True
                parcel_no = "%" + self.application_parcel_num_edit.text() + "%"
                applications_count = applications.filter(ApplicationSearch.parcel_id.ilike(parcel_no)).count()
                if applications_count > 0:
                    applications = applications.filter(ApplicationSearch.parcel_id.ilike(parcel_no))
                else:
                    applications = applications.filter(ApplicationSearch.tmp_parcel_id.ilike(parcel_no))
            if self.application_decision_num_edit.text():
                filter_is_set = True
                decision_no = "%" + self.application_decision_num_edit.text() + "%"
                applications = applications.filter(ApplicationSearch.decision_no.ilike(decision_no))

            if self.application_contract_num_edit.text():
                filter_is_set = True
                contract_num = "%" + self.application_contract_num_edit.text() + "%"
                applications = applications.filter(or_(ApplicationSearch.contract_no.ilike(contract_num), ApplicationSearch.record_no.ilike(contract_num)))

            if self.personal_application_edit.text():
                filter_is_set = True
                person_id = "%" + self.personal_application_edit.text() + "%"
                applications = applications.filter(ApplicationSearch.person_id.ilike(person_id))

            if self.app_date_checkbox.isChecked():
                filter_is_set = True
                qt_date = self.application_datetime_edit.date().toString(Constants.DATABASE_DATE_FORMAT)
                python_date = datetime.strptime(str(qt_date), Constants.PYTHON_DATE_FORMAT)

                applications = applications.filter(ApplicationSearch.app_timestamp >= python_date)

            count = 0

            self.__remove_application_items()

            if applications.distinct(ApplicationSearch.app_no).count() == 0:
                self.error_label.setText(self.tr("No applications found for this search filter."))
                return

            elif filter_is_set is False:
                self.error_label.setText(self.tr("Please specify a search filter."))
                return

            for application in applications.distinct(ApplicationSearch.app_no).all():
                app_type = "" if not application.app_type_ref else application.app_type_ref.description

                item = QTableWidgetItem(str(application.app_no) + " ( " + unicode(app_type) + " )")
                item.setIcon(QIcon(QPixmap(":/plugins/lm2/application.png")))
                item.setData(Qt.UserRole, application.app_no)
                self.application_results_twidget.insertRow(count)
                self.application_results_twidget.setItem(count, 0, item)
                count += 1

            self.error_label.setText("")
            self.application_results_label.setText(self.tr("Results: ") + str(count))

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    @pyqtSlot()
    def on_case_find_button_clicked(self):

        self.__search_cases()

    def __search_cases(self):

        try:
            maintenance_search = self.session.query(MaintenanceSearch)
            filter_is_set = False

            if self.case_app_no_edit.text():
                filter_is_set = True
                app_no = "%" + self.case_app_no_edit.text() + "%"
                maintenance_search = maintenance_search.filter(MaintenanceSearch.app_no.ilike(app_no))

            if self.case_completion_date_checkbox.isChecked():
                filter_is_set = True
                qt_date = self.case_completion_date_edit.date().toString(Constants.DATABASE_DATE_FORMAT)
                python_date = datetime.strptime(str(qt_date), Constants.PYTHON_DATE_FORMAT)
                maintenance_search = maintenance_search.filter(MaintenanceSearch.completion_date >= python_date)

            if self.case_no_edit.text():
                filter_is_set = True
                case_no = "%" + self.case_no_edit.text() + "%"
                maintenance_search = maintenance_search.filter(cast(MaintenanceSearch.id, String).ilike(case_no))

            if self.case_parcel_no_edit.text():
                filter_is_set = True
                parcel = "%" + self.case_parcel_no_edit.text() + "%"
                maintenance_search = maintenance_search.filter(MaintenanceSearch.parcel.ilike(parcel))

            if self.surveyed_by_land_officer_cbox.itemData(self.surveyed_by_land_officer_cbox.currentIndex()) != -1:
                filter_is_set = True
                surveyed_by = self.surveyed_by_land_officer_cbox.itemData(self.surveyed_by_land_officer_cbox.currentIndex())
                maintenance_search = maintenance_search.filter(MaintenanceSearch.surveyed_by_land_office == surveyed_by)

            if self.finalized_by_cbox.itemData(self.finalized_by_cbox.currentIndex()) != -1:
                filter_is_set = True
                finalized_by = self.finalized_by_cbox.itemData(self.finalized_by_cbox.currentIndex())
                maintenance_search = maintenance_search.filter(MaintenanceSearch.completed_by == finalized_by)

            if self.surveyed_by_company_cbox.itemData(self.surveyed_by_company_cbox.currentIndex()) != -1:
                filter_is_set = True
                surveyor = self.surveyed_by_company_cbox.itemData(self.surveyed_by_company_cbox.currentIndex())

                maintenance_search = maintenance_search.filter(MaintenanceSearch.surveyed_by_surveyor == surveyor)

            if self.case_status_cbox.itemData(self.case_status_cbox.currentIndex()) != -1:
                filter_is_set = True
                status = self.case_status_cbox.itemData(self.case_status_cbox.currentIndex())
                if status == Constants.CASE_STATUS_IN_PROGRESS:
                    maintenance_search = maintenance_search.filter(MaintenanceSearch.completion_date == None)
                else:
                    maintenance_search = maintenance_search.filter(MaintenanceSearch.completion_date != None)
            if self.case_right_holder_name_edit.text():
                filter_is_set = True
                right_holder = self.case_right_holder_name_edit.text()
                if "," in right_holder:
                    right_holder_strings = right_holder.split(",")
                    surname = "%" + right_holder_strings[0].strip() + "%"
                    first_name = "%" + right_holder_strings[1].strip() + "%"
                    maintenance_search = maintenance_search.filter(and_(func.lower(MaintenanceSearch.name).ilike(func.lower(surname)), func.lower(MaintenanceSearch.first_name).ilike(func.lower(first_name))))
                else:
                    right_holder = "%" + self.application_right_holder_name_edit.text() + "%"
                    maintenance_search = maintenance_search.filter(or_(func.lower(MaintenanceSearch.name).ilike(func.lower(right_holder)), func.lower(MaintenanceSearch.first_name).ilike(func.lower(right_holder))))
            if self.personal_case_edit.text():
                filter_is_set = True
                person_id = "%" + self.personal_case_edit.text() + "%"
                maintenance_search = maintenance_search.filter(MaintenanceSearch.person_id.ilike(person_id))

            count = 0

            self.__remove_maintenance_case_items()

            if maintenance_search.distinct(MaintenanceSearch.id).count() == 0:
                self.error_label.setText(self.tr("No maintenance cases found for this search filter."))
                return

            elif filter_is_set is False:
                self.error_label.setText(self.tr("Please specify a search filter."))
                return

            for case in maintenance_search.distinct(MaintenanceSearch.id).all():
                item = QTableWidgetItem(str(case.id) + self.tr(" (Soum: {0})".format(case.soum)))
                item.setIcon(QIcon(QPixmap(":/plugins/lm2/case.png")))
                item.setData(Qt.UserRole, case.id)
                item.setData(Qt.UserRole + 1, str(case.soum))
                self.case_results_twidget.insertRow(count)
                self.case_results_twidget.setItem(count, 0, item)
                count += 1

            self.error_label.setText("")
            self.case_results_label.setText(self.tr("Results: ") + str(count))

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    @pyqtSlot()
    def on_decision_find_button_clicked(self):

        self.__search_decisions()

    def __search_decisions(self):
        try:
            decisions = self.session.query(DecisionSearch.decision_no)
            filter_is_set = False

            if self.decision_num_edit.text():
                filter_is_set = True
                decision_no = "%" + self.decision_num_edit.text() + "%"
                decisions = decisions.filter(DecisionSearch.decision_no.ilike(decision_no))

            if self.decision_date_cbox.isChecked():
                filter_is_set = True
                qt_date = self.decision_date.date().toString(Constants.DATABASE_DATE_FORMAT)
                python_date = datetime.strptime(str(qt_date), Constants.PYTHON_DATE_FORMAT)
                decisions = decisions.filter(DecisionSearch.decision_date >= python_date)

            if self.decision_parcel_num_edit.text():
                filter_is_set = True
                parcel_num = "%" + self.decision_parcel_num_edit.text() + "%"
                decisions = decisions.filter(DecisionSearch.parcel_id.ilike(parcel_num))

            if self.decision_right_holder_name_edit.text():
                filter_is_set = True
                right_holder = "%" + self.decision_right_holder_name_edit.text() + "%"
                decisions = decisions.filter(or_(func.lower(DecisionSearch.name).ilike(func.lower(right_holder)), func.lower(DecisionSearch.first_name).ilike(func.lower(right_holder)), func.lower(DecisionSearch.middle_name).ilike(func.lower(right_holder))))

            if self.decision_application_num_edit.text():
                filter_is_set = True
                app_no = "%" + self.decision_application_num_edit.text() + "%"
                decisions = decisions.filter(DecisionSearch.app_no.ilike(app_no))

            if self.decision_contract_num_edit.text():
                filter_is_set = True
                contract_no = "%" + self.decision_contract_num_edit.text() +"%"
                decisions = decisions.filter(or_(DecisionSearch.contract_no.ilike(contract_no), DecisionSearch.record_no.ilike(contract_no)))

            if self.personal_decision_edit.text():
                filter_is_set = True
                person_id = "%" + self.personal_decision_edit.text() + "%"
                decisions = decisions.filter(DecisionSearch.person_id.ilike(person_id))

            count = 0

            self.__remove_decision_items()

            if decisions.distinct(DecisionSearch.decision_no).count() == 0:
                self.error_label.setText(self.tr("No decisions found for this search filter."))
                return

            elif filter_is_set is False:
                self.error_label.setText(self.tr("Please specify a search filter."))
                return

            for decision in decisions.distinct(DecisionSearch.decision_no).all():
                item = QTableWidgetItem(decision.decision_no)
                item.setIcon(QIcon(QPixmap(":/plugins/lm2/decision.png")))
                item.setData(Qt.UserRole, decision.decision_no)
                self.decision_results_twidget.insertRow(count)
                self.decision_results_twidget.setItem(count, 0, item)
                count += 1

            self.error_label.setText("")
            self.decision_results_label.setText(self.tr("Results: ") + str(count))

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    @pyqtSlot()
    def on_contract_find_button_clicked(self):

        self.__search_contracts()

    def __search_contracts(self):
        try:
            contracts = self.session.query(ContractSearch.contract_no).\
                filter(and_(ContractSearch.app_type != ApplicationType.right_land, ContractSearch.app_type != ApplicationType.pasture_use))

            filter_is_set = False

            if self.contract_num_edit.text():
                filter_is_set = True
                contract_no = "%" + self.contract_num_edit.text() + "%"
                contracts = contracts.filter(ContractSearch.contract_no.ilike(contract_no))

            if self.contract_date_cbox.isChecked():
                filter_is_set = True
                qt_date = self.contract_date.date().toString(Constants.DATABASE_DATE_FORMAT)
                python_date = datetime.strptime(str(qt_date), Constants.PYTHON_DATE_FORMAT)
                contracts = contracts.filter(ContractSearch.contract_date >= python_date)

            if self.contract_parcel_num_edit.text():
                filter_is_set = True
                parcel_num = "%" + self.contract_parcel_num_edit.text() + "%"
                contracts = contracts.filter(ContractSearch.parcel_id.ilike(parcel_num))

            if self.contract_right_holder_num_edit.text():
                filter_is_set = True
                right_holder = "%" + self.contract_right_holder_num_edit.text() + "%"
                contracts = contracts.filter(or_(func.lower(ContractSearch.name).ilike(func.lower(right_holder)), func.lower(ContractSearch.first_name).ilike(func.lower(right_holder)), func.lower(ContractSearch.middle_name).ilike(func.lower(right_holder))))

            if self.contract_application_num_edit.text():
                filter_is_set = True
                app_no = "%" + self.contract_application_num_edit.text() + "%"
                contracts = contracts.filter(ContractSearch.app_no.ilike(app_no))

            if self.contract_decision_num_edit.text():
                filter_is_set = True
                decision_no = "%" + self.contract_decision_num_edit.text() + "%"
                contracts = contracts.filter(ContractSearch.decision_no.ilike(decision_no))

            if self.personal_contract_edit.text():
                filter_is_set = True
                person_id = "%" + self.personal_contract_edit.text() + "%"
                contracts = contracts.filter(ContractSearch.person_id.ilike(person_id))

            if self.contract_status_cbox.currentIndex() != -1:
                if not self.contract_status_cbox.itemData(self.contract_status_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    status = self.contract_status_cbox.itemData(self.contract_status_cbox.currentIndex()).code

                    contracts = contracts.filter(ContractSearch.status == status)

            count = 0

            self.__remove_contract_items()

            if contracts.distinct(ContractSearch.contract_no).count() == 0:
                self.error_label.setText(self.tr("No contract found for this search filter."))
                return

            elif filter_is_set is False:
                self.error_label.setText(self.tr("Please specify a search filter."))
                return

            for contract in contracts.distinct(ContractSearch.contract_no).all():

                item = QTableWidgetItem(contract.contract_no)
                item.setIcon(QIcon(QPixmap(":/plugins/lm2/contract.png")))
                item.setData(Qt.UserRole, contract.contract_no)
                self.contract_results_twidget.insertRow(count)
                self.contract_results_twidget.setItem(count, 0, item)
                count += 1

            self.error_label.setText("")
            self.contract_results_label.setText(self.tr("Results: ") + str(count))

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    @pyqtSlot()
    def on_record_find_button_clicked(self):

        self.__search_records()

    def __search_records(self):

        try:

            filter_is_set = False
            records = self.session.query(RecordSearch.record_no)

            if self.record_record_num_edit.text():
                filter_is_set = True
                value = "%" + self.record_record_num_edit.text() + "%"
                records = records.filter(RecordSearch.record_no.ilike(value))

            if self.record_date_cbox.isChecked():
                filter_is_set = True
                qt_date = self.record_date_edit.date().toString(Constants.DATABASE_DATE_FORMAT)
                python_date = datetime.strptime(str(qt_date), Constants.PYTHON_DATE_FORMAT)
                records = records.filter(RecordSearch.record_date >= python_date)

            if self.record_parcel_num_edit.text():
                filter_is_set = True
                value = "%" + self.record_parcel_num_edit.text() + "%"
                records = records.filter(RecordSearch.parcel_id.ilike(value))

            if self.record_right_holder_edit.text():
                filter_is_set = True
                right_holder = "%" + self.record_right_holder_edit.text() + "%"
                records = records.filter(or_(func.lower(RecordSearch.name).ilike(func.lower(right_holder)), func.lower(RecordSearch.first_name).ilike(func.lower(right_holder)), func.lower(RecordSearch.middle_name).ilike(func.lower(right_holder))))

            if self.record_app_num_edit.text():
                filter_is_set = True
                value = "%" + self.record_app_num_edit.text() + "%"
                records = records.filter(RecordSearch.app_no.ilike(value))

            if self.record_decision_num_edit.text():
                filter_is_set = True
                value = "%" + self.record_app_num_edit.text() + "%"
                records = records.filter(RecordSearch.decision_no.ilike(value))

            if self.personal_record_edit.text():
                filter_is_set = True
                value = "%" + self.personal_record_edit.text() + "%"
                records = records.filter(RecordSearch.person_id.ilike(value))

            if self.record_status_cbox.currentIndex() != -1:
                if not self.record_status_cbox.itemData(self.record_status_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    status = self.record_status_cbox.itemData(self.record_status_cbox.currentIndex()).code

                    records = records.filter(RecordSearch.status == status)

            count = 0

            self.__remove_record_items()

            if records.distinct(RecordSearch.record_no).count() == 0:
                self.error_label.setText(self.tr("No records found for this search filter."))
                return

            elif filter_is_set is False:
                self.error_label.setText(self.tr("Please specify a search filter."))
                return

            for record in records.distinct(RecordSearch.record_no).all():
                item = QTableWidgetItem(record.record_no)
                item.setIcon(QIcon(QPixmap(":/plugins/lm2/land_ownership.png")))
                item.setData(Qt.UserRole, record.record_no)
                self.record_results_twidget.insertRow(count)
                self.record_results_twidget.setItem(count, 0, item)
                count += 1

            self.error_label.setText("")
            self.record_results_label.setText(self.tr("Results: ") + str(count))

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    @pyqtSlot()
    def on_parcel_find_button_clicked(self):

        self.__search_parcels()

    def __search_parcels(self):

        try:
            if self.is_parcel_checkbox.isChecked():
                parcels = self.session.query(ParcelSearch.parcel_id, ParcelSearch.geo_id, ParcelSearch.landuse_ref,\
                                             ParcelSearch.address_khashaa, ParcelSearch.address_streetname)

                filter_is_set = False

                if self.parcel_num_edit.text():
                    filter_is_set = True
                    parcel_no = "%" + self.parcel_num_edit.text() + "%"
                    parcels = parcels.filter(ParcelSearch.parcel_id.ilike(parcel_no))

                if self.geo_id_edit.text():
                    filter_is_set = True
                    value = "%" + self.geo_id_edit.text() + "%"
                    parcels = parcels.filter(ParcelSearch.geo_id.ilike(value))

                if not self.land_use_type_cbox.itemData(self.land_use_type_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    value = self.land_use_type_cbox.itemData(self.land_use_type_cbox.currentIndex()).code
                    parcels = parcels.filter(ParcelSearch.landuse == value)

                if self.parcel_app_num_edit.text():
                    filter_is_set = True
                    value = "%" + self.parcel_app_num_edit.text() + "%"
                    parcels = parcels.filter(ParcelSearch.app_no.ilike(value))

                if self.parcel_right_holder_name_edit.text():
                    filter_is_set = True
                    right_holder = "%" + self.parcel_right_holder_name_edit.text() + "%"
                    parcels = parcels.filter(or_(func.lower(ParcelSearch.name).ilike(func.lower(right_holder)), func.lower(ParcelSearch.first_name).ilike(func.lower(right_holder)), func.lower(ParcelSearch.middle_name).ilike(func.lower(right_holder))))

                if self.parcel_decision_num_edit.text():
                    filter_is_set = True
                    value = "%" + self.parcel_decision_num_edit.text() + "%"
                    parcels = parcels.filter(ParcelSearch.app_no.ilike(value))

                if self.parcel_contract_num_edit.text():
                    filter_is_set = True
                    value = "%" + self.parcel_contract_num_edit.text() + "%"
                    parcels = parcels.filter(or_(ParcelSearch.contract_no.ilike(value), ParcelSearch.record_no.ilike(value)))

                if self.personal_parcel_edit.text():
                    filter_is_set = True
                    value = "%" + self.personal_parcel_edit.text() + "%"
                    parcels = parcels.filter(ParcelSearch.person_id.ilike(value))

                if self.parcel_streetname_edit.text():
                    filter_is_set = True
                    value = "%" + self.parcel_streetname_edit.text() + "%"
                    parcels = parcels.filter(ParcelSearch.address_streetname.ilike(value))

                if self.parcel_khashaa_edit.text():
                    filter_is_set = True
                    value = "%" + self.parcel_khashaa_edit.text() + "%"
                    parcels = parcels.filter(ParcelSearch.address_khashaa.ilike(value))

                count = 0

                self.__remove_parcel_items()

                if parcels.distinct(ParcelSearch.parcel_id).count() == 0:
                    self.error_label.setText(self.tr("No parcels found for this search filter."))
                    return

                elif filter_is_set is False:
                    self.error_label.setText(self.tr("Please specify a search filter."))
                    return

                for parcel in parcels.distinct(ParcelSearch.parcel_id).all():
                    # geo_id = self.tr("n.a.") if not parcel.geo_id else parcel.geo_id
                    address_khashaa = ''
                    address_streetname = ''
                    if parcel.address_khashaa:
                        address_khashaa = parcel.address_khashaa
                    if parcel.address_streetname:
                        address_streetname = parcel.address_streetname
                    item = QTableWidgetItem(parcel.parcel_id + " ("+address_khashaa+", "+ address_streetname+")")
                    item.setIcon(QIcon(QPixmap(":/plugins/lm2/parcel.png")))
                    item.setData(Qt.UserRole, parcel.parcel_id)
                    self.parcel_results_twidget.insertRow(count)
                    self.parcel_results_twidget.setItem(count, 0, item)
                    count += 1

                self.error_label.setText("")
                self.parcel_results_label.setText(self.tr("Results: ") + str(count))
            else:
                parcels = self.session.query(TmpParcelSearch.parcel_id, TmpParcelSearch.geo_id, TmpParcelSearch.landuse_ref,\
                                             TmpParcelSearch.address_khashaa, TmpParcelSearch.address_streetname)

                filter_is_set = False

                if self.parcel_num_edit.text():
                    filter_is_set = True
                    parcel_no = "%" + self.parcel_num_edit.text() + "%"
                    parcels = parcels.filter(TmpParcelSearch.parcel_id.ilike(parcel_no))

                if self.geo_id_edit.text():
                    filter_is_set = True
                    value = "%" + self.geo_id_edit.text() + "%"
                    parcels = parcels.filter(TmpParcelSearch.geo_id.ilike(value))

                if not self.land_use_type_cbox.itemData(self.land_use_type_cbox.currentIndex()) == -1:
                    filter_is_set = True
                    value = self.land_use_type_cbox.itemData(self.land_use_type_cbox.currentIndex()).code
                    parcels = parcels.filter(TmpParcelSearch.landuse == value)

                if self.parcel_app_num_edit.text():
                    filter_is_set = True
                    value = "%" + self.parcel_app_num_edit.text() + "%"
                    parcels = parcels.filter(TmpParcelSearch.app_no.ilike(value))

                if self.parcel_right_holder_name_edit.text():
                    filter_is_set = True
                    right_holder = "%" + self.parcel_right_holder_name_edit.text() + "%"
                    parcels = parcels.filter(or_(func.lower(TmpParcelSearch.name).ilike(func.lower(right_holder)), func.lower(TmpParcelSearch.first_name).ilike(func.lower(right_holder)), func.lower(ParcelSearch.middle_name).ilike(func.lower(right_holder))))

                if self.parcel_decision_num_edit.text():
                    filter_is_set = True
                    value = "%" + self.parcel_decision_num_edit.text() + "%"
                    parcels = parcels.filter(TmpParcelSearch.app_no.ilike(value))

                if self.parcel_contract_num_edit.text():
                    filter_is_set = True
                    value = "%" + self.parcel_contract_num_edit.text() + "%"
                    parcels = parcels.filter(or_(TmpParcelSearch.contract_no.ilike(value), TmpParcelSearch.record_no.ilike(value)))

                if self.personal_parcel_edit.text():
                    filter_is_set = True
                    value = "%" + self.personal_parcel_edit.text() + "%"
                    parcels = parcels.filter(TmpParcelSearch.person_id.ilike(value))
                count = 0

                self.__remove_parcel_items()

                if parcels.distinct(TmpParcelSearch.parcel_id).count() == 0:
                    self.error_label.setText(self.tr("No parcels found for this search filter."))
                    return

                elif filter_is_set is False:
                    self.error_label.setText(self.tr("Please specify a search filter."))
                    return

                for parcel in parcels.distinct(TmpParcelSearch.parcel_id).all():
                    # geo_id = self.tr("n.a.") if not parcel.geo_id else parcel.geo_id
                    address_khashaa = ''
                    address_streetname = ''
                    if parcel.address_khashaa:
                        address_khashaa = parcel.address_khashaa
                    if parcel.address_streetname:
                        address_streetname = parcel.address_streetname

                    item = QTableWidgetItem(parcel.parcel_id + " ("+address_khashaa+", "+ address_streetname+")")
                    item.setIcon(QIcon(QPixmap(":/plugins/lm2/parcel.png")))
                    item.setData(Qt.UserRole, parcel.parcel_id)
                    self.parcel_results_twidget.insertRow(count)
                    self.parcel_results_twidget.setItem(count, 0, item)
                    count += 1

                self.error_label.setText("")
                self.parcel_results_label.setText(self.tr("Results: ") + str(count))

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    def __remove_person_items(self):

        self.person_results_twidget.setRowCount(0)
        self.person_results_label.setText("")

    def __clear_person(self):

        self.name_edit.clear()
        self.personal_edit.clear()
        self.state_reg_num_edit.clear()
        self.mobile_num_edit.clear()
        self.person_parcel_num_edit.clear()
        self.person_application_num_edit.clear()
        self.person_decision_num_edit.clear()
        self.person_contract_num_edit.clear()
        self.person_type_cbox.setCurrentIndex(self.person_type_cbox.findData(-1))
        self.application_type_cbox.setCurrentIndex(self.application_type_cbox.findData(-1))

    def __clear_app(self):

        self.application_application_num_edit.clear()
        self.application_right_holder_name_edit.clear()
        self.application_parcel_num_edit.clear()
        self.application_decision_num_edit.clear()
        self.application_contract_num_edit.clear()
        self.personal_application_edit.clear()

        self.app_type_cbox.setCurrentIndex(self.app_type_cbox.findData(-1))
        self.status_cbox.setCurrentIndex(self.status_cbox.findData(-1))
        self.office_in_charge_cbox.setCurrentIndex(self.office_in_charge_cbox.findData(-1))
        self.next_officer_in_charge_cbox.setCurrentIndex(self.next_officer_in_charge_cbox.findData(-1))


    def __clear_parcel(self):

        self.parcel_num_edit.clear()
        self.geo_id_edit.clear()
        self.parcel_right_holder_name_edit.clear()
        self.parcel_app_num_edit.clear()
        self.parcel_decision_num_edit.clear()
        self.parcel_contract_num_edit.clear()
        self.personal_parcel_edit.clear()
        self.land_use_type_cbox.setCurrentIndex(self.land_use_type_cbox.findData(-1))
        self.parcel_streetname_edit.clear()
        self.parcel_khashaa_edit.clear()

    def __clear_decision(self):

        self.decision_num_edit.clear()
        self.decision_date.setDate(QDate.currentDate())
        self.decision_right_holder_name_edit.clear()
        self.personal_decision_edit.clear()
        self.decision_parcel_num_edit.clear()
        self.decision_application_num_edit.clear()
        self.decision_contract_num_edit.clear()

    def __clear_maintenance(self):

        self.case_no_edit.clear()
        self.case_completion_date_edit.clear()
        self.case_completion_date_edit.setDate(QDate.currentDate())
        self.case_parcel_no_edit.clear()
        self.case_app_no_edit.clear()
        self.case_right_holder_name_edit.clear()
        self.personal_case_edit.clear()

        self.surveyed_by_company_cbox.setCurrentIndex(self.surveyed_by_company_cbox.findData(-1))
        self.surveyed_by_land_officer_cbox.setCurrentIndex(self.surveyed_by_land_officer_cbox.findData(-1))
        self.finalized_by_cbox.setCurrentIndex(self.finalized_by_cbox.findData(-1))

    def __clear_contract(self):

        self.contract_num_edit.clear()
        self.contract_date.setDate(QDate.currentDate())
        self.contract_right_holder_num_edit.clear()
        self.personal_contract_edit.clear()
        self.contract_parcel_num_edit.clear()
        self.contract_decision_num_edit.clear()
        self.contract_application_num_edit.clear()

    def __clear_record(self):

        self.record_record_num_edit.clear()
        self.record_date_edit.setDate(QDate.currentDate())
        self.record_right_holder_edit.clear()
        self.personal_record_edit.clear()
        self.record_parcel_num_edit.clear()
        self.record_decision_num_edit.clear()
        self.record_app_num_edit.clear()

    def __remove_application_items(self):

        self.application_results_twidget.setRowCount(0)
        self.application_results_label.setText("")

    def __remove_decision_items(self):

        self.decision_results_twidget.setRowCount(0)
        self.decision_results_label.setText("")

    def __remove_maintenance_case_items(self):

        self.case_results_twidget.setRowCount(0)
        self.case_results_label.setText("")

    def __remove_contract_items(self):

        self.contract_results_twidget.setRowCount(0)
        self.contract_results_label.setText("")

    def __remove_record_items(self):

        self.record_results_twidget.setRowCount(0)
        self.record_results_label.setText("")

    def __remove_report_items(self):

        self.report_result_twidget.setRowCount(0)
        # self.report_result_twidget.setText("")

    def __remove_parcel_items(self):

        self.parcel_results_twidget.setRowCount(0)
        self.parcel_results_label.setText("")

    @pyqtSlot()
    def on_person_clear_button_clicked(self):

        self.__remove_person_items()
        self.__clear_person()

    @pyqtSlot()
    def on_application_clear_button_clicked(self):

        self.__remove_application_items()
        self.__clear_app()

    @pyqtSlot()
    def on_case_clear_button_clicked(self):

        self.__remove_maintenance_case_items()
        self.__clear_maintenance()

    @pyqtSlot()
    def on_decision_clear_button_clicked(self):

        self.__remove_decision_items()
        self.__clear_decision()

    @pyqtSlot()
    def on_contract_clear_button_clicked(self):

        self.__remove_contract_items()
        self.__clear_contract()

    @pyqtSlot()
    def on_record_clear_button_clicked(self):

        self.__remove_record_items()
        self.__clear_record()

    @pyqtSlot()
    def on_parcel_clear_button_clicked(self):

        self.__remove_parcel_items()
        self.__clear_parcel()

    @pyqtSlot()
    def on_person_delete_button_clicked(self):

        if len(self.person_results_twidget.selectedItems()) == 0:
            return

        items = self.person_results_twidget.selectedItems()
        message_box = QMessageBox()

        if len(items) == 1:
            message_box.setText(self.tr("Do you want to delete the person {0}?").format(items[0].text()))
        else:
            message_box.setText(self.tr("Do you want to delete the {0} selected persons?").format(str(len(items))))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        for item in items:

            self.create_savepoint()

            try:
                self.session.query(BsPerson).filter(BsPerson.person_id == item.data(Qt.UserRole)).delete()
                self.commit()

            except SQLAlchemyError, e:
                self.rollback_to_savepoint()
                self.__search_persons()

                if e.__class__ == IntegrityError:
                    self.error_label.setText(self.tr("This person is still assigned. Please remove the assignment in order to remove the person."))
                else:
                    PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
                return

        self.__search_persons()

    @pyqtSlot()
    def on_application_delete_button_clicked(self):

        if not len(self.application_results_twidget.selectedItems()):
            return

        items = self.application_results_twidget.selectedItems()
        message_box = QMessageBox()

        if len(items) > 1:
            message_box.setText(self.tr("Do you want to delete {0} selected applications?").format(len(items)))
        elif len(items) == 1:
            message_box.setText(self.tr("Do you want to delete the application {0}").format(str(items[0].data(Qt.UserRole))))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)

        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        for item in items:
            app_no = item.data(Qt.UserRole)
            try:

                self.create_savepoint()

                app_no_soum = app_no.split("-")[0]
                DatabaseUtils.set_working_schema(app_no_soum)

                # self.session.query(CtApplicationPersonRole).filter(CtApplication.app_no == app_no).delete()
                self.session.query(CtApplication).filter(CtApplication.app_no == app_no).delete()

                self.commit()

            except SQLAlchemyError, e:
                self.rollback_to_savepoint()
                self.__search_applications()

                if e.__class__ == IntegrityError:
                    self.error_label.setText(self.tr("This application is still assigned. "
                                                     "Please remove the assignment in order to remove the application."))
                else:
                    PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
                DatabaseUtils.set_working_schema()
                return

        DatabaseUtils.set_working_schema()
        self.__search_applications()

    @pyqtSlot()
    def on_decision_delete_button_clicked(self):

        if not len(self.decision_results_twidget.selectedItems()):
            return

        items = self.decision_results_twidget.selectedItems()

        message_box = QMessageBox()
        if len(items) > 1:
            message_box.setText(self.tr("Do you want to delete the {0} selected decisions?").format(str(len(items))))
        elif len(items) == 1:
            message_box.setText(self.tr("Do you want to delete the decision {0}").format(items[0].text()))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        for item in items:

            try:
                #1st check if there are contracts
                self.create_savepoint()

                decision_no = item.data(Qt.UserRole)
                if self.__contracts_based_on_decision(decision_no) != 0:
                    self.error_label.setText(self.tr("There is already a contract based on this decision. Delete the contracts first."))
                    return

                #delete status from application
                applications = self.session.query(CtApplication)\
                    .join(CtDecisionApplication.application_ref)\
                    .join(CtDecision).filter(CtDecision.decision_no == item.data(Qt.UserRole)).all()

                for application in applications:
                    application.statuses.filter(CtApplicationStatus.status > Constants.APP_STATUS_SEND).delete()

                self.session.query(CtDecision).filter(CtDecision.decision_no == decision_no).delete()

                self.commit()

            except SQLAlchemyError, e:
                self.rollback_to_savepoint()
                self.__search_decisions()

                if e.__class__ == IntegrityError:
                    PluginUtils.show_message(self, self.tr("Sql Error"), self.tr("This decision is still assigned. Please remove the assignment in order to remove the decision."))
                else:
                    PluginUtils.show_message(self, self.tr("Sql Error"), e.message)
                return

        self.__search_decisions()

    def __contracts_based_on_decision(self, decision_no):

        try:
            DatabaseUtils.set_working_schema(decision_no[:5])

            decision = self.session.query(CtDecision).filter(CtDecision.decision_no == decision_no).one()
            for result in decision.results:
                return result.application_ref.contracts.count()

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("Sql Error"), e.message)
        return 0

    @pyqtSlot()
    def on_contract_delete_button_clicked(self):

        if not len(self.contract_results_twidget.selectedItems()):
            return

        items = self.contract_results_twidget.selectedItems()

        message_box = QMessageBox()
        if len(items) > 1:
            message_box.setText(self.tr("Do you want to delete {0} selected contracts?").format(len(items)))
        elif len(items) == 1:
            message_box.setText(self.tr("Do you want to delete the contract {0}").format(items[0].text()))

        for item in items:
            contract_no = item.data(Qt.UserRole)
            contract_result = self.session.query(ContractSearch).filter(ContractSearch.contract_no == contract_no).one()
            status = contract_result.status
            if status == 20:
                PluginUtils.show_message(self, self.tr("Contract"), self.tr("Do not delete the active contract!!!"))
                return

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        for item in items:
            try:

                self.create_savepoint()
                contract_no = item.data(Qt.UserRole)

                contract_result = self.session.query(ContractSearch).filter(ContractSearch.contract_no == contract_no).one()
                app_no = contract_result.app_no

                status_count = self.session.query(CtApplicationStatus).filter(CtApplicationStatus.application == app_no).\
                    filter(CtApplicationStatus.status == 9).count()

                self.session.query(CtContract).filter(CtContract.contract_no == item.data(Qt.UserRole)).delete()
                if status_count == 1:
                    self.session.query(CtApplicationStatus).filter(CtApplicationStatus.application == app_no).\
                        filter(CtApplicationStatus.status == 9).delete()
                self.commit()

            except SQLAlchemyError, e:
                self.rollback_to_savepoint()
                self.__search_contracts()

                if e.__class__ == IntegrityError:
                    self.error_label.setText(self.tr("This contract is still assigned."))
                else:
                    PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
                return

        self.__search_contracts()

    @pyqtSlot()
    def on_record_delete_button_clicked(self):

        if not len(self.record_results_twidget.selectedItems()):
            return

        items = self.record_results_twidget.selectedItems()

        message_box = QMessageBox()

        if len(items) > 1:
            message_box.setText(self.tr("Do you want to delete {0} selected records?").format(len(items)))
        elif len(items) == 1:
            message_box.setText(self.tr("Do you want to delete the record {0}").format((items[0].text())))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        for item in items:
            try:
                self.create_savepoint()

                record_no = item.data(Qt.UserRole)
                DatabaseUtils.set_working_schema(record_no[:5])
                self.session.query(CtOwnershipRecord).filter(CtOwnershipRecord.record_no == record_no).delete()

                self.commit()

            except SQLAlchemyError, e:
                self.rollback_to_savepoint()
                self.__search_records()

                if e.__class__ == IntegrityError:
                    self.error_label.setText(self.tr("This record is still assigned. Please remove the assignment in order to remove the record."))
                else:
                    DatabaseUtils.set_working_schema()
                    PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
                return

        DatabaseUtils.set_working_schema()
        self.__search_records()

    @pyqtSlot()
    def on_person_add_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        person = BsPerson()
        dialog = PersonDialog(person)
        dialog.rejected.connect(self.on_current_dialog_closed)
        DialogInspector().set_dialog_visible(True)
        dialog.exec_()

    @pyqtSlot()
    def on_person_edit_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        person = self.__selected_person()
        if not person:
            return

        dialog = PersonDialog(person)
        dialog.rejected.connect(self.on_current_dialog_closed)
        DialogInspector().set_dialog_visible(True)

        dialog.exec_()

    def __selected_person(self):

        if not len(self.person_results_twidget.selectedItems()) == 1:
            self.error_label.setText(self.tr("Select one item to start editing."))
            return

        selected_items = self.person_results_twidget.selectedItems()[0]
        person_id = selected_items.data(Qt.UserRole)
        person = None

        try:
            person = self.session.query(BsPerson).filter(BsPerson.person_id == person_id).one()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
            return None

        return person

    @pyqtSlot(QPoint)
    def on_custom_context_menu_requested(self, point):

        if self.tabWidget.currentWidget() == self.person_tab:
            item = self.person_results_twidget.itemAt(point)
            if item is None: return
            self.context_menu.exec_(self.person_results_twidget.mapToGlobal(point))

        elif self.tabWidget.currentWidget() == self.parcel_tab:
            item = self.parcel_results_twidget.itemAt(point)
            if item is None: return
            self.context_menu.exec_(self.parcel_results_twidget.mapToGlobal(point))

        elif self.tabWidget.currentWidget() == self.parcel_tab:
            item = self.parcel_results_twidget.itemAt(point)
            if item is None: return
            self.context_menu.exec_(self.parcel_results_twidget.mapToGlobal(point))

        elif self.tabWidget.currentWidget() == self.application_tab:
            item = self.application_results_twidget.itemAt(point)
            if item is None: return
            self.context_menu.exec_(self.application_results_twidget.mapToGlobal(point))

        elif self.tabWidget.currentWidget() == self.contract_tab:
            item = self.contract_results_twidget.itemAt(point)
            if item is None: return
            self.contract_context_menu.exec_(self.contract_results_twidget.mapToGlobal(point))

        elif self.tabWidget.currentWidget() == self.record_tab:
            item = self.record_results_twidget.itemAt(point)
            if item is None: return
            self.record_context_menu.exec_(self.record_results_twidget.mapToGlobal(point))

        elif self.tabWidget.currentWidget() == self.maintenance_tab:
            item = self.case_results_twidget.itemAt(point)
            if item is None: return
            self.context_menu.exec_(self.case_results_twidget.mapToGlobal(point))

        elif self.tabWidget.currentWidget() == self.decision_tab:
            item = self.decision_results_twidget.itemAt(point)
            if item is None: return
            self.context_menu.exec_(self.decision_results_twidget.mapToGlobal(point))


    @pyqtSlot()
    def on_application_add_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        DatabaseUtils.set_working_schema()
        application = PluginUtils.create_new_application()
        self.current_dialog = ApplicationsDialog(application, self, False, self.plugin.iface.mainWindow())
        self.current_dialog.setModal(False)
        self.current_dialog.rejected.connect(self.on_current_dialog_closed)
        DialogInspector().set_dialog_visible(True)
        self.current_dialog.show()

    @pyqtSlot()
    def on_application_edit_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        app_instance = self.__selected_application()
        if app_instance is not None:

            self.current_dialog = ApplicationsDialog(app_instance, self, True, self.plugin.iface.mainWindow())
            self.current_dialog.rejected.connect(self.on_current_dialog_closed)
            DialogInspector().set_dialog_visible(True)
            self.current_dialog.setModal(False)
            self.current_dialog.show()

        DatabaseUtils.set_working_schema()

    @pyqtSlot()
    def on_current_dialog_closed(self):

        DialogInspector().set_dialog_visible(False)

    @pyqtSlot()
    def on_case_revert_button_clicked(self):

        if not len(self.case_results_twidget.selectedItems()):
            return

        items = self.case_results_twidget.selectedItems()
        message_box = QMessageBox()

        if len(items) > 1:
            message_box.setText(self.tr("Do you want to delete {0} selected maintenance cases and roll back the edits?").format(len(items)))
        elif len(items) == 1:
            message_box.setText(self.tr("Do you want to delete the maintenance case {0}").format(str(items[0].data(Qt.UserRole))))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)

        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        for item in items:

            self.create_savepoint()

            case_no = item.data(Qt.UserRole)
            case_soum = item.data(Qt.UserRole + 1)
            case_soum = case_soum.strip()

            DatabaseUtils.set_working_schema(case_soum)
            try:
                m_case = self.session.query(CaMaintenanceCase).filter(CaMaintenanceCase.id == case_no).one()

                if m_case.completion_date is not None:
                    if len(m_case.parcels) != 0:
                        self.error_label.setText(self.tr("The maintenance case {0} is finalized and has parcels assigned.".format(str(case_no))))
                        return
                    else:
                        self.session.query(CaTmpBuilding).filter(CaTmpBuilding.maintenance_case == case_no).delete()
                        self.session.query(CaMaintenanceCase).filter(CaMaintenanceCase.id == case_no).delete()
                        self.commit()
                        self.__search_cases()
                        return

                self.session.query(CaTmpParcel).filter(CaTmpParcel.maintenance_case == case_no).delete()
                self.session.query(CaTmpBuilding).filter(CaTmpBuilding.maintenance_case == case_no).delete()
                self.session.query(CaMaintenanceCase).filter(CaMaintenanceCase.id == case_no).delete()

                self.commit()

            except SQLAlchemyError, e:
                self.rollback_to_savepoint()
                PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
                DatabaseUtils.set_working_schema()
                return

        self.__search_cases()
        DatabaseUtils.set_working_schema()

    @pyqtSlot()
    def on_case_finalize_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        case_instance = self.__selected_maintenance_case()

        if case_instance is not None:

            if case_instance.completion_date is None:
                selected_item = self.case_results_twidget.selectedItems()[0]
                soum = selected_item.data(Qt.UserRole + 1)

                self.current_dialog = FinalizeCaseDialog(case_instance, soum, self.plugin, self.plugin.iface.mainWindow())
                DialogInspector().set_dialog_visible(True)
                self.current_dialog.rejected.connect(self.on_current_dialog_closed)
                self.current_dialog.setModal(False)
                self.current_dialog.show()

            else:
                PluginUtils.show_message(self, self.tr("Maintenance Case"), self.tr("The maintenance case is already finalized."))
                return

        self.__search_cases()

        self.plugin.iface.mapCanvas().refresh()

    @pyqtSlot()
    def on_case_create_button_clicked(self):

        if DialogInspector().dialog_visible():
            return
        session = SessionHandler().session_instance()
        ca_maintenance_case = CaMaintenanceCase()
        user = DatabaseUtils.current_user()
        officers = self.session.query(SetRole) \
            .filter(SetRole.user_name == user.user_name) \
            .filter(SetRole.is_active == True).one()

        ca_maintenance_case.created_by = officers.user_name_real
        session.add(ca_maintenance_case)

        DatabaseUtils.set_working_schema()
        create_new_m_case = PluginUtils.create_new_m_case()
        self.current_dialog = CreateCaseDialog(self.plugin, create_new_m_case, False, self.plugin.iface.mainWindow())
        self.current_dialog.rejected.connect(self.on_current_dialog_closed)
        DialogInspector().set_dialog_visible(True)
        self.current_dialog.setModal(False)
        self.current_dialog.show()

    @pyqtSlot()
    def on_decision_add_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        DatabaseUtils.set_working_schema()

        dialog = ImportDecisionDialog(False)
        dialog.rejected.connect(self.on_current_dialog_closed)
        dialog.exec_()


    @pyqtSlot()
    def on_decision_edit_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        decision = self.__selected_decision()

        dialog = ImportDecisionDialog(True, decision)
        dialog.rejected.connect(self.on_current_dialog_closed)
        DialogInspector().set_dialog_visible(True)
        dialog.exec_()

    @pyqtSlot()
    def on_contract_add_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        DatabaseUtils.set_working_schema()
        contract = PluginUtils.create_new_contract()

        self.current_dialog = ContractDialog(contract, self, False, self.plugin.iface.mainWindow())
        self.current_dialog.rejected.connect(self.on_current_dialog_closed)
        DialogInspector().set_dialog_visible(True)
        self.current_dialog.setModal(False)
        self.current_dialog.show()

    @pyqtSlot()
    def on_contract_edit_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        contract = self.__selected_contract()
        if contract is None:
            return

        self.current_dialog = ContractDialog(contract, self, True, self.plugin.iface.mainWindow())
        self.current_dialog.rejected.connect(self.on_current_dialog_closed)
        DialogInspector().set_dialog_visible(True)
        self.current_dialog.setModal(False)
        self.current_dialog.show()

    @pyqtSlot()
    def on_record_add_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        DatabaseUtils.set_working_schema()
        record = PluginUtils.create_new_record()

        self.current_dialog = OwnRecordDialog(record, self, False, self.plugin.iface.mainWindow())
        self.current_dialog.rejected.connect(self.on_current_dialog_closed)
        DialogInspector().set_dialog_visible(True)
        self.current_dialog.setModal(False)

        self.current_dialog.show()

    @pyqtSlot()
    def on_record_edit_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        record = self.__selected_record()
        dialog = OwnRecordDialog(record, self, True, self.plugin.iface.mainWindow())
        dialog.rejected.connect(self.on_current_dialog_closed)
        DialogInspector().set_dialog_visible(True)

        dialog.exec_()

    @pyqtSlot(QTableWidgetItem)
    def on_application_results_twidget_itemDoubleClicked(self, item):

        if DialogInspector().dialog_visible():
            return

        app_instance = self.__selected_application()

        if app_instance is not None:
            self.current_dialog = ApplicationsDialog(app_instance, self, True, self.plugin.iface.mainWindow())
            DialogInspector().set_dialog_visible(True)
            self.current_dialog.rejected.connect(self.on_current_dialog_closed)
            self.current_dialog.setModal(False)
            self.current_dialog.show()

    @pyqtSlot(QTableWidgetItem)
    def on_zoom_to_parcel_action_clicked(self):

        soum_with_parcels = {}

        if self.tabWidget.currentWidget() == self.person_tab:
            person = self.__selected_person()
            try:
                person_search_results = self.session.query(PersonSearch.app_no).distinct(PersonSearch.app_no).filter(PersonSearch.person_id == person.person_id).all()
                for person_result in person_search_results:

                    if person_result.app_no is not None:

                        app_no_soum = person_result.app_no.split("-")[0]

                        if app_no_soum not in soum_with_parcels.keys():
                            soum_with_parcels[app_no_soum] = []

                        DatabaseUtils.set_working_schema(app_no_soum)

                        count = self.session.query(CtApplication.parcel).filter(CtApplication.app_no == person_result.app_no).count()
                        if count <> 1:
                            continue

                        application = self.session.query(CtApplication.parcel).filter(CtApplication.app_no == person_result.app_no).one()

                        if application[0] is not None:
                            soum_with_parcels[app_no_soum].append(application[0])

            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("Sql Error"), e.message)
                DatabaseUtils.set_working_schema()
                return

            self.__zoom_to_parcel_several_soums(soum_with_parcels)

        elif self.tabWidget.currentWidget() == self.application_tab:

            application = self.__selected_application()
            if application.parcel is not None:
                #check refused parcels
                count = self.session.query(CaParcel).filter(CaParcel.parcel_id == application.parcel).count()
                if count == 0:
                    layer_name = "ca_refused_parcel"
                else:
                    layer_name = "ca_parcel"

                self.__zoom_to_parcel_ids([application.parcel], layer_name)
            else:
                self.error_label.setText(self.tr("No parcel assigned."))

        elif self.tabWidget.currentWidget() == self.maintenance_tab:

            m_case = self.__selected_maintenance_case()

            if len(m_case.parcels) > 0:
                self.__zoom_to_parcels(m_case.parcels)
            else:
                #its an m_case in progress
                #take care that the working schema in __selected_maintenance_case did not change
                self.__zoom_to_tmp_parcels(m_case.id)

        elif self.tabWidget.currentWidget() == self.contract_tab:

            contract = self.__selected_contract()
            if contract is None:
                return

            parcels = []

            for app_roles in contract.application_roles:
                application = app_roles.application_ref
                if application.parcel is not None:
                    parcels.append(application.parcel)

            self.__zoom_to_parcel_ids(parcels)

        elif self.tabWidget.currentWidget() == self.record_tab:

            record = self.__selected_record()
            if record is None:
                return

            parcels = []

            for app_roles in record.application_roles:
                application = app_roles.application_ref
                if application.parcel is not None:
                    parcels.append(application.parcel)

            self.__zoom_to_parcel_ids(parcels)

        elif self.tabWidget.currentWidget() == self.maintenance_tab:

            m_case = self.__selected_maintenance_case()
            self.__zoom_to_parcels(m_case.parcels)

        elif self.tabWidget.currentWidget() == self.parcel_tab:

            parcel_id = self.__selected_parcel_id()
            self.__zoom_to_parcel_ids([parcel_id])

        elif self.tabWidget.currentWidget() == self.decision_tab:

            decision = self.__selected_decision()
            if decision is None:
                return

            parcels = []

            for result in decision.results:
                application = result.application_ref
                if application.parcel is not None:
                    parcels.append(application.parcel)

            self.__zoom_to_parcel_ids(parcels)

        DatabaseUtils.set_working_schema()

    def __zoom_to_parcel_several_soums(self, soums):

        LayerUtils.deselect_all()

        for soum, parcel_array in soums.iteritems():

            layer = LayerUtils.layer_by_data_source("s" + soum, "ca_parcel")

            if layer is None:
                layer = LayerUtils.load_layer_by_name("ca_parcel", "parcel_id", soum)

            exp_string = ""

            for parcel_id in parcel_array:
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

    def __zoom_to_parcel_ids(self, parcel_ids, layer_name = None):

        LayerUtils.deselect_all()
        if layer_name is None:
            for parcel_id in parcel_ids:
                if len(parcel_id) == 12:
                    layer_name = "ca_parcel"
                else:
                    layer_name = "ca_tmp_parcel"

        layer = LayerUtils.layer_by_data_source("s" + DatabaseUtils.current_working_soum_schema(), layer_name)

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
        if layer is None:
            layer = LayerUtils.load_layer_by_name(layer_name, "parcel_id", restrictions)

        exp_string = ""

        for parcel_id in parcel_ids:
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

    def __zoom_to_parcels(self, parcels):

        LayerUtils.deselect_all()

        layer = LayerUtils.layer_by_data_source("s" + DatabaseUtils.current_working_soum_schema(), "ca_parcel")

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
        if layer is None:
            layer = LayerUtils.load_layer_by_name("ca_parcel", "parcel_id", restrictions)

        request = QgsFeatureRequest()
        exp_string = ""

        for parcel in parcels:
            if exp_string == "":
                exp_string = "parcel_id = \'" + parcel.parcel_id  + "\'"
            else:
                exp_string += " or parcel_id = \'" + parcel.parcel_id  + "\'"

        request.setFilterExpression(exp_string)
        feature_ids = []
        iterator = layer.getFeatures(request)

        for feature in iterator:
            feature_ids.append(feature.id())

        if len(feature_ids) == 0:
            self.error_label.setText(self.tr("No parcel assigned"))

        layer.setSelectedFeatures(feature_ids)
        self.plugin.iface.mapCanvas().zoomToSelected(layer)

    def __zoom_to_tmp_parcels(self, m_case_no):

        LayerUtils.deselect_all()

        layer = LayerUtils.layer_by_data_source("s" + DatabaseUtils.current_working_soum_schema(), "ca_tmp_parcel")

        restrictions = DatabaseUtils.working_l2_code()
        if layer is None:
            layer = LayerUtils.load_layer_by_name("ca_tmp_parcel", "parcel_id", restrictions)

        request = QgsFeatureRequest()
        exp_string = "maintenance_case = {0}".format(m_case_no)
        request.setFilterExpression(exp_string)
        feature_ids = []
        iterator = layer.getFeatures(request)

        for feature in iterator:
            feature_ids.append(feature.id())

        if len(feature_ids) == 0:
            self.error_label.setText(self.tr("No parcel assigned"))

        layer.setSelectedFeatures(feature_ids)
        self.plugin.iface.mapCanvas().zoomToSelected(layer)

    @pyqtSlot()
    def on_copy_number_action_clicked(self):

        if self.tabWidget.currentWidget() == self.person_tab:
            person = self.__selected_person()
            QApplication.clipboard().setText(person.person_id)
        elif self.tabWidget.currentWidget() == self.parcel_tab:
            parcel_id = self.__selected_parcel_id()
            QApplication.clipboard().setText(parcel_id)
        elif self.tabWidget.currentWidget() == self.application_tab:
            app = self.__selected_application()
            QApplication.clipboard().setText(app.app_no)
        elif self.tabWidget.currentWidget() == self.contract_tab:
            contract = self.__selected_contract()
            QApplication.clipboard().setText(contract.contract_no)
        elif self.tabWidget.currentWidget() == self.record_tab:
            record = self.__selected_record()
            QApplication.clipboard().setText(record.record_no)
        elif self.tabWidget.currentWidget() == self.maintenance_tab:
            m_case = self.__selected_maintenance_case()
            QApplication.clipboard().setText(m_case.id)
        elif self.tabWidget.currentWidget() == self.decision_tab:
            decision = self.__selected_decision()
            QApplication.clipboard().setText(decision.decision_no)


    @pyqtSlot(QTableWidgetItem)
    def on_case_results_twidget_itemDoubleClicked(self, item):

        if DialogInspector().dialog_visible():
            return

        case_instance = self.__selected_maintenance_case()

        selected_case_item = self.case_results_twidget.selectedItems()[0]
        soum = selected_case_item.data(Qt.UserRole + 1)

        DatabaseUtils.set_working_schema(soum)

        if case_instance is not None:
            self.current_dialog = CreateCaseDialog(self.plugin, case_instance, True, self.plugin.iface.mainWindow())
            self.current_dialog.rejected.connect(self.on_current_dialog_closed)
            DialogInspector().set_dialog_visible(True)
            self.current_dialog.setModal(False)
            self.current_dialog.show()

    @pyqtSlot(QTableWidgetItem)
    def on_person_results_twidget_itemDoubleClicked(self, item):

        person = self.__selected_person()
        if not person:
            return

        dialog = PersonDialog(person)
        dialog.exec_()

    @pyqtSlot(QTableWidgetItem)
    def on_decision_results_twidget_itemDoubleClicked(self, item):

        decision = self.__selected_decision()

        dialog = ImportDecisionDialog(True, decision)
        dialog.exec_()

    @pyqtSlot(QTableWidgetItem)
    def on_contract_results_twidget_itemDoubleClicked(self, item):

        if DialogInspector().dialog_visible():
            return

        contract = self.__selected_contract()

        self.current_dialog = ContractDialog(contract, self, True, self.plugin.iface.mainWindow())
        self.current_dialog.rejected.connect(self.on_current_dialog_closed)
        self.current_dialog.setModal(False)
        DialogInspector().set_dialog_visible(True)
        self.current_dialog.show()

    @pyqtSlot(QTableWidgetItem)
    def on_record_results_twidget_itemDoubleClicked(self, item):

        if DialogInspector().dialog_visible():
            return

        record = self.__selected_record()

        self.current_dialog = OwnRecordDialog(record, self, True, self.plugin.iface.mainWindow())
        self.current_dialog.rejected.connect(self.on_current_dialog_closed)
        self.current_dialog.setModal(False)
        DialogInspector().set_dialog_visible(True)
        self.current_dialog.show()

    @pyqtSlot(int)
    def on_tabWidget_currentChanged(self):

        self.error_label.setText("")

    @pyqtSlot(QTableWidgetItem)
    def on_parcel_results_twidget_itemDoubleClicked(self, item):

        current_user = DatabaseUtils.current_user()
        restrictions = current_user.restriction_au_level2.split(",")

        for restriction in restrictions:
            restriction = restriction.strip()
            DatabaseUtils.set_working_schema(restriction)
            try:
                count = self.session.query(CaParcel).filter(CaParcel.parcel_id == item.data(Qt.UserRole)).count()

                if count == 0:
                    continue
                else:
                    parcel_layer = LayerUtils.layer_by_data_source("s" + restriction, "ca_parcel")
                    if parcel_layer is None:
                        message_box = QMessageBox()
                        message_box.setText(self.tr("Do you want to load the layer ca_parcel from soum {0}?".format(restriction)))
                        load_button = message_box.addButton(self.tr("Load Layers"), QMessageBox.ActionRole)
                        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
                        message_box.exec_()

                        if message_box.clickedButton() == load_button:
                            parcel_layer = LayerUtils.load_layer_by_name("ca_parcel", "parcel_id", restriction)

                    parcel_id = item.data(Qt.UserRole)

                    if parcel_layer is None:
                        return

                    feature_request = QgsFeatureRequest()
                    feature_request.setFilterExpression("parcel_id = \'" + parcel_id + "\'")
                    iterator = parcel_layer.getFeatures(feature_request)
                    for feature in iterator:
                        parcel_layer.setSelectedFeatures([feature.id()])
                        self.plugin.iface.mapCanvas().zoomToSelected(parcel_layer)

                        return

            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("Sql Error"), e.message)
                DatabaseUtils.set_working_schema()
                return

        DatabaseUtils.set_working_schema()

    def __user_right_permissions(self):

        self.__disable_all()

        user_name = QSettings().value(SettingsConstants.USER)
        user = self.session.query(SetRole).\
            filter(SetRole.user_name == user_name).\
            filter(SetRole.is_active == True).one()
        user_name_real = user.user_name_real

        user_rights = self.session.query(SetUserGroupRole).filter(SetUserGroupRole.user_name_real == user_name_real).all()
        for user_right in user_rights:
            if user_right.group_role == UserRight_code.person_update:
                if user_right.r_view:
                    self.person_find_button.setEnabled(True)
                    self.person_clear_button.setEnabled(True)
                    self.person_edit_button.setEnabled(True)
                    self.person_edit_button.setText(self.tr("view"))
                if user_right.r_add:
                    self.person_find_button.setEnabled(True)
                    self.person_clear_button.setEnabled(True)
                    self.person_add_button.setEnabled(True)
                if user_right.r_remove:
                    self.person_find_button.setEnabled(True)
                    self.person_clear_button.setEnabled(True)
                    self.person_delete_button.setEnabled(True)
                if user_right.r_update:
                    self.person_find_button.setEnabled(True)
                    self.person_clear_button.setEnabled(True)
                    self.person_edit_button.setEnabled(True)
                    self.person_edit_button.setText(self.tr("view"))
            if user_right.group_role == UserRight_code.cadastre_update:
                if user_right.r_view:
                    self.parcel_find_button.setEnabled(True)
                    self.parcel_clear_button.setEnabled(True)
                    self.parcel_view_button.setEnabled(True)
                    # maintenance
                    self.case_find_button.setEnabled(True)
                    self.case_clear_button.setEnabled(True)
                if user_right.r_add:
                    # maintenance
                    self.case_find_button.setEnabled(True)
                    self.case_clear_button.setEnabled(True)
                    self.case_create_button.setEnabled(True)
                if user_right.r_remove:
                    self.parcel_find_button.setEnabled(True)
                    self.parcel_clear_button.setEnabled(True)
                    self.parcel_view_button.setEnabled(True)
                    self.delete_parcel_button.setEnabled(True)
                    # maintenance
                    self.case_find_button.setEnabled(True)
                    self.case_clear_button.setEnabled(True)
                    self.case_revert_button.setEnabled(True)
                if user_right.r_update:
                    # maintenance
                    self.case_find_button.setEnabled(True)
                    self.case_clear_button.setEnabled(True)
                    self.case_finalize_button.setEnabled(True)
            if user_right.group_role == UserRight_code.application_update:
                if user_right.r_view:
                    self.application_find_button.setEnabled(True)
                    self.application_clear_button.setEnabled(True)
                    self.application_edit_button.setEnabled(True)
                    self.application_edit_button.setText(self.tr("view"))
                if user_right.r_add:
                    self.application_find_button.setEnabled(True)
                    self.application_clear_button.setEnabled(True)
                    self.application_add_button.setEnabled(True)
                if user_right.r_remove:
                    self.application_find_button.setEnabled(True)
                    self.application_clear_button.setEnabled(True)
                    self.application_delete_button.setEnabled(True)
                if user_right.r_update:
                    self.application_find_button.setEnabled(True)
                    self.application_clear_button.setEnabled(True)
                    self.application_edit_button.setEnabled(True)
                    self.application_edit_button.setText(self.tr("Edit"))
            if user_right.group_role == UserRight_code.decision_update:
                if user_right.r_view:
                    self.decision_find_button.setEnabled(True)
                    self.decision_clear_button.setEnabled(True)
                    self.decision_edit_button.setEnabled(True)
                    self.decision_edit_button.setText(self.tr("View"))
                if user_right.r_add:
                    self.decision_find_button.setEnabled(True)
                    self.decision_clear_button.setEnabled(True)
                    self.decision_add_button.setEnabled(True)
                if user_right.r_remove:
                    self.decision_find_button.setEnabled(True)
                    self.decision_clear_button.setEnabled(True)
                    self.decision_delete_button.setEnabled(True)
                if user_right.r_update:
                    self.decision_find_button.setEnabled(True)
                    self.decision_clear_button.setEnabled(True)
                    self.decision_edit_button.setEnabled(True)
                    self.decision_edit_button.setText(self.tr("Edit"))
            if user_right.group_role == UserRight_code.contracting_update:
                if user_right.r_view:
                    self.contract_find_button.setEnabled(True)
                    self.contract_clear_button.setEnabled(True)
                    self.contract_edit_button.setEnabled(True)
                    self.contract_edit_button.setText(self.tr("View"))
                if user_right.r_add:
                    self.contract_find_button.setEnabled(True)
                    self.contract_clear_button.setEnabled(True)
                    self.contract_add_button.setEnabled(True)
                if user_right.r_remove:
                    self.contract_find_button.setEnabled(True)
                    self.contract_clear_button.setEnabled(True)
                    self.contract_delete_button.setEnabled(True)
                if user_right.r_update:
                    self.contract_find_button.setEnabled(True)
                    self.contract_clear_button.setEnabled(True)
                    self.contract_edit_button.setEnabled(True)
                    self.contract_edit_button.setText(self.tr("Edit"))
            if user_right.group_role == UserRight_code.ownership_update:
                if user_right.r_view:
                    self.record_find_button.setEnabled(True)
                    self.record_clear_button.setEnabled(True)
                    self.record_edit_button.setEnabled(True)
                    self.record_edit_button.setText(self.tr("View"))
                if user_right.r_add:
                    self.record_find_button.setEnabled(True)
                    self.record_clear_button.setEnabled(True)
                    self.record_add_button.setEnabled(True)
                if user_right.r_remove:
                    self.record_find_button.setEnabled(True)
                    self.record_clear_button.setEnabled(True)
                    self.record_delete_button.setEnabled(True)
                if user_right.r_update:
                    self.record_find_button.setEnabled(True)
                    self.record_clear_button.setEnabled(True)
                    self.record_edit_button.setEnabled(True)
                    self.record_edit_button.setText(self.tr("Edit"))
            if user_right.group_role == UserRight_code.reporting:
                if user_right.r_view:
                    self.report_print_button.setEnabled(True)
                    self.report_find_button.setEnabled(True)
                    self.report_layer_button.setEnabled(True)

                    self.print_button.setEnabled(True)
                    self.layer_view_button.setEnabled(True)
            if user_right.group_role == UserRight_code.role_management:
                if user_right.r_update:
                    self.till_date_edit.setEnabled(True)
                    self.infinity_check_box.setEnabled(True)

    def __setup_permissions(self):

        user_name = QSettings().value(SettingsConstants.USER)
        user_rights = DatabaseUtils.userright_by_name(user_name)

        self.__disable_all()

        if UserRight.application_view in user_rights:

            self.application_edit_button.setText(self.tr("View"))
            self.person_edit_button.setText(self.tr("View"))

            self.person_edit_button.setEnabled(True)
            self.application_edit_button.setEnabled(True)

            self.parcel_find_button.setEnabled(True)
            self.parcel_clear_button.setEnabled(True)
            self.person_find_button.setEnabled(True)
            self.person_clear_button.setEnabled(True)
            self.application_find_button.setEnabled(True)
            self.application_clear_button.setEnabled(True)

        if UserRight.application_update in user_rights:

            self.application_add_button.setEnabled(True)
            self.application_delete_button.setEnabled(True)
            self.person_add_button.setEnabled(True)
            self.person_delete_button.setEnabled(True)

            self.application_edit_button.setText(self.tr("Edit"))
            self.person_edit_button.setText(self.tr("Edit"))

            self.person_edit_button.setEnabled(True)
            self.application_edit_button.setEnabled(True)

            self.parcel_find_button.setEnabled(True)
            self.parcel_clear_button.setEnabled(True)

            self.person_find_button.setEnabled(True)
            self.person_clear_button.setEnabled(True)
            self.application_find_button.setEnabled(True)
            self.application_clear_button.setEnabled(True)

        if UserRight.contracting_view in user_rights:

            self.contract_edit_button.setText(self.tr("View"))
            self.record_edit_button.setText(self.tr("View"))
            self.application_edit_button.setText(self.tr("View"))
            self.person_edit_button.setText(self.tr("View"))
            self.decision_edit_button.setText(self.tr("View"))

            self.decision_edit_button.setEnabled(True)
            self.person_edit_button.setEnabled(True)
            self.application_edit_button.setEnabled(True)
            self.record_edit_button.setEnabled(True)
            self.contract_edit_button.setEnabled(True)

            self.parcel_find_button.setEnabled(True)
            self.parcel_clear_button.setEnabled(True)
            self.record_find_button.setEnabled(True)
            self.record_clear_button.setEnabled(True)
            self.contract_find_button.setEnabled(True)
            self.contract_clear_button.setEnabled(True)
            self.decision_find_button.setEnabled(True)
            self.decision_clear_button.setEnabled(True)
            self.person_find_button.setEnabled(True)
            self.person_clear_button.setEnabled(True)
            self.application_find_button.setEnabled(True)
            self.application_clear_button.setEnabled(True)

            # self.case_finalize_button.setEnabled(False)
            # self.case_create_button.setEnabled(False)
            # self.case_revert_button.setEnabled(False)

        if UserRight.contracting_update in user_rights:

            self.contract_add_button.setEnabled(True)
            self.contract_delete_button.setEnabled(True)
            self.record_add_button.setEnabled(True)
            self.record_delete_button.setEnabled(True)
            self.decision_add_button.setEnabled(True)
            self.decision_delete_button.setEnabled(True)

            self.contract_edit_button.setText(self.tr("Edit"))
            self.contract_edit_button.setText(self.tr("Edit"))
            self.record_edit_button.setText(self.tr("Edit"))
            self.decision_edit_button.setText(self.tr("Edit"))

            self.decision_edit_button.setEnabled(True)
            self.record_edit_button.setEnabled(True)
            self.contract_edit_button.setEnabled(True)

            self.parcel_find_button.setEnabled(True)
            self.parcel_clear_button.setEnabled(True)
            self.record_find_button.setEnabled(True)
            self.record_clear_button.setEnabled(True)
            self.contract_find_button.setEnabled(True)
            self.contract_clear_button.setEnabled(True)
            self.decision_find_button.setEnabled(True)
            self.decision_clear_button.setEnabled(True)
            self.person_find_button.setEnabled(True)
            self.person_clear_button.setEnabled(True)
            self.application_find_button.setEnabled(True)
            self.application_clear_button.setEnabled(True)

            self.case_finalize_button.setEnabled(True)
            self.case_create_button.setEnabled(True)
            self.case_revert_button.setEnabled(True)

        if UserRight.cadastre_view in user_rights:
            self.parcel_find_button.setEnabled(True)
            self.parcel_clear_button.setEnabled(True)

        if UserRight.cadastre_update in user_rights:
            self.parcel_find_button.setEnabled(True)
            self.parcel_clear_button.setEnabled(True)

    def __disable_all(self):

        self.contract_add_button.setEnabled(False)
        self.contract_delete_button.setEnabled(False)
        self.record_add_button.setEnabled(False)
        self.record_delete_button.setEnabled(False)
        self.decision_add_button.setEnabled(False)
        self.decision_delete_button.setEnabled(False)
        self.application_add_button.setEnabled(False)
        self.application_delete_button.setEnabled(False)
        self.person_add_button.setEnabled(False)
        self.person_delete_button.setEnabled(False)

        self.parcel_find_button.setEnabled(False)
        self.parcel_clear_button.setEnabled(False)
        self.parcel_view_button.setEnabled(False)
        self.delete_parcel_button.setEnabled(False)
        self.record_find_button.setEnabled(False)
        self.record_clear_button.setEnabled(False)
        self.contract_find_button.setEnabled(False)
        self.contract_clear_button.setEnabled(False)
        self.decision_find_button.setEnabled(False)
        self.decision_clear_button.setEnabled(False)
        self.person_find_button.setEnabled(False)
        self.person_clear_button.setEnabled(False)
        self.application_find_button.setEnabled(False)
        self.application_clear_button.setEnabled(False)

        self.contract_edit_button.setText(self.tr("View"))
        self.record_edit_button.setText(self.tr("View"))
        self.application_edit_button.setText(self.tr("View"))
        self.person_edit_button.setText(self.tr("View"))
        self.decision_edit_button.setText(self.tr("View"))

        self.decision_edit_button.setEnabled(False)
        self.person_edit_button.setEnabled(False)
        self.application_edit_button.setEnabled(False)
        self.record_edit_button.setEnabled(False)
        self.contract_edit_button.setEnabled(False)

        self.report_print_button.setEnabled(False)
        self.report_find_button.setEnabled(False)
        self.report_layer_button.setEnabled(False)
        self.print_button.setEnabled(False)
        self.layer_view_button.setEnabled(False)

        self.case_find_button.setEnabled(False)
        self.case_clear_button.setEnabled(False)
        self.case_create_button.setEnabled(False)
        self.case_revert_button.setEnabled(False)
        self.case_finalize_button.setEnabled(False)

        self.till_date_edit.setEnabled(False)
        self.infinity_check_box.setEnabled(False)


    def keyPressEvent(self, event):

        key = event.key()

        if key in (Qt.Key_Enter, Qt.Key_Return):

            if self.tabWidget.currentWidget() == self.person_tab:
                self.__search_persons()
            elif self.tabWidget.currentWidget() == self.parcel_tab:
                self.__search_parcels()
            elif self.tabWidget.currentWidget() == self.application_tab:
                self.__search_applications()
            elif self.tabWidget.currentWidget() == self.contract_tab:
                self.__search_contracts()
            elif self.tabWidget.currentWidget() == self.record_tab:
                self.__search_records()
            elif self.tabWidget.currentWidget() == self.maintenance_tab:
                self.__search_cases()
            elif self.tabWidget.currentWidget() == self.decision_tab:
                self.__search_decisions()

    def __show_land_fee_payments_dialog(self):

        current_working_soum = DatabaseUtils.current_working_soum_schema()

        contract = self.__selected_contract()
        dlg = LandFeePaymentsDialog(contract)
        dlg.exec_()

        DatabaseUtils.set_working_schema(current_working_soum)

    def __show_land_tax_payments_dialog(self):

        current_working_soum = DatabaseUtils.current_working_soum_schema()

        record = self.__selected_record()
        dlg = LandTaxPaymentsDialog(record)
        dlg.exec_()

        DatabaseUtils.set_working_schema(current_working_soum)

    # Report
    def __report_setup(self):

        self.report_begin_date.setDateTime(QDateTime().currentDateTime())
        self.report_end_date.setDateTime(QDateTime().currentDateTime())

        try:
            application_type = self.session.query(ClApplicationType). \
                filter(and_(ClApplicationType.code != ApplicationType.pasture_use,
                            ClApplicationType.code != ApplicationType.right_land)).all()
            application_status = self.session.query(ClApplicationStatus).all()
            land_use_type = self.session.query(ClLanduseType).all()
            person_type = self.session.query(ClPersonType).all()
        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("Sql Error"), e.message)
            return

        self.report_app_type_cbox.addItem("*", -1)
        self.report_app_status_cbox.addItem("*", -1)
        self.report_land_use_cbox.addItem("*", -1)
        self.report_person_type_cbox.addItem("*", -1)

        for app_type in application_type:
            self.report_app_type_cbox.addItem(app_type.description, app_type.code)

        for app_status in application_status:
            self.report_app_status_cbox.addItem(app_status.description, app_status.code)

        for land_use in land_use_type:
            self.report_land_use_cbox.addItem(land_use.description, land_use.code)

        for person in person_type:
            self.report_person_type_cbox.addItem(person.description, person.code)

    @pyqtSlot(QListWidgetItem)
    def on_listWidget_itemClicked(self, item):

        self.report_result_twidget.hide()

        code = str(item.text()[:2])

        if code == '01':
            self.report_land_use_cbox.setDisabled(True)
            self.year_sbox.setDisabled(True)
            self.person_id.setDisabled(True)
            self.parcel_id.setDisabled(True)

            self.report_begin_date.setEnabled(True)
            self.report_end_date.setEnabled(True)
            self.report_app_type_cbox.setEnabled(True)
            self.report_person_type_cbox.setEnabled(True)
            self.report_app_status_cbox.setEnabled(True)
            self.report_layer_button.setEnabled(True)
        elif code == '02':
            self.report_land_use_cbox.setDisabled(True)
            self.report_app_type_cbox.setDisabled(True)
            self.report_person_type_cbox.setDisabled(True)
            self.report_app_status_cbox.setDisabled(True)
            self.year_sbox.setDisabled(True)
            self.person_id.setDisabled(True)
            self.parcel_id.setDisabled(True)
            self.report_layer_button.setDisabled(True)

            self.report_begin_date.setEnabled(True)
            self.report_end_date.setEnabled(True)
        elif code == '03' or code == '04':
            self.report_land_use_cbox.setDisabled(True)
            self.report_app_type_cbox.setDisabled(True)
            self.report_person_type_cbox.setDisabled(True)
            self.report_app_status_cbox.setDisabled(True)
            self.year_sbox.setDisabled(True)
            self.person_id.setDisabled(True)
            self.parcel_id.setDisabled(True)
            self.report_begin_date.setDisabled(True)
            self.report_end_date.setDisabled(True)

            self.report_layer_button.setEnabled(True)
        elif code == '05':
            self.report_app_status_cbox.setDisabled(True)
            self.year_sbox.setDisabled(True)
            self.person_id.setDisabled(True)
            self.parcel_id.setDisabled(True)

            self.report_begin_date.setEnabled(True)
            self.report_end_date.setEnabled(True)
            self.report_app_type_cbox.setEnabled(True)
            self.report_person_type_cbox.setEnabled(True)
            self.report_land_use_cbox.setEnabled(True)
            self.report_layer_button.setEnabled(True)
        elif code == '07':
            self.report_app_status_cbox.setDisabled(True)
            self.year_sbox.setDisabled(True)

            self.report_begin_date.setEnabled(True)
            self.report_end_date.setEnabled(True)
            self.report_app_type_cbox.setEnabled(True)
            self.report_person_type_cbox.setEnabled(True)
            self.report_land_use_cbox.setEnabled(True)
            self.person_id.setEnabled(True)
            self.parcel_id.setEnabled(True)
            self.report_layer_button.setEnabled(True)
        elif code == '08':
            self.report_app_status_cbox.setDisabled(True)
            self.year_sbox.setDisabled(True)

            self.report_begin_date.setEnabled(True)
            self.report_end_date.setEnabled(True)
            self.report_app_type_cbox.setEnabled(True)
            self.report_person_type_cbox.setEnabled(True)
            self.report_land_use_cbox.setEnabled(True)
            self.person_id.setEnabled(True)
            self.parcel_id.setEnabled(True)
            self.report_layer_button.setEnabled(True)
        elif code == '09':
            self.report_app_status_cbox.setDisabled(True)
            self.year_sbox.setDisabled(True)

            self.report_begin_date.setEnabled(True)
            self.report_end_date.setEnabled(True)
            self.report_app_type_cbox.setEnabled(True)
            self.report_person_type_cbox.setEnabled(True)
            self.report_land_use_cbox.setEnabled(True)
            self.person_id.setEnabled(True)
            self.parcel_id.setEnabled(True)
            self.report_layer_button.setEnabled(True)
        elif code == '10':
            self.report_app_status_cbox.setDisabled(True)
            self.person_id.setDisabled(True)
            self.parcel_id.setDisabled(True)

            self.year_sbox.setEnabled(True)
            self.report_begin_date.setEnabled(True)
            self.report_end_date.setEnabled(True)
            self.report_app_type_cbox.setEnabled(True)
            self.report_person_type_cbox.setEnabled(True)
            self.report_land_use_cbox.setEnabled(True)
            self.report_layer_button.setEnabled(True)
        elif code == '12':
            self.report_find_button.setEnabled(True)
            self.report_result_twidget.show()
            self.report_result_twidget.setEnabled(True)
            self.person_id.setEnabled(True)
            self.parcel_id.setEnabled(True)

    @pyqtSlot()
    def on_report_print_button_clicked(self):

        self.progressBar.setVisible(True)
        self.progressBar.setMinimum(1)
        self.progressBar.setValue(0)
        itemsList = self.listWidget.selectedItems()
        code = '0'
        for item in itemsList:
            code = str(item.text()[:2])
        if code == '01':
            self.__application_list()
        elif code == '02':
            self.__app_steps_progress()
        elif code == '03':
            type = 0
            self.dlg = DraftDecisionPrintDialog(type)
            self.dlg.show()
        elif code == '04':
            type = 1
            self.dlg = DraftDecisionPrintDialog(type)
            self.dlg.show()
        elif code == '05':
            self.__invalid_parcel()
        elif code == '06':
            self.__end_parcel_yearly()
        elif code == '07':
            self.__book_for_land_use()
        elif code == '08':
            self.__book_for_land_possess()
        elif code == '09':
            self.__book_for_land_ownership()
        elif code == '10':
            self.__land_tax()
        elif code == '11':
            self.__land_tax_paid()
        elif code == '12':
            self.__land_fee_quarterly()
        elif code == '13':
            self.__auction_info()
        elif code == '14':
            self.__selection_of_draft()
        elif code == '15':
            self.__condominium_area()
        self.progressBar.setVisible(False)

    @pyqtSlot()
    def on_report_find_button_clicked(self):

        self.progressBar.setVisible(True)
        self.progressBar.setMinimum(1)
        self.progressBar.setValue(0)
        itemsList = self.listWidget.selectedItems()
        code = '0'
        for item in itemsList:
            code = str(item.text()[:2])
        if code == '01':
            self.__application_list()
        elif code == '02':
            self.__app_steps_progress()
        elif code == '03':
            type = 0
            self.dlg = DraftDecisionPrintDialog(type)
            self.dlg.show()
        elif code == '04':
            type = 1
            self.dlg = DraftDecisionPrintDialog(type)
            self.dlg.show()
        elif code == '05':
            self.__invalid_parcel()
        elif code == '06':
            self.__end_parcel_yearly()
        elif code == '07':
            self.__book_for_land_use()
        elif code == '08':
            self.__book_for_land_possess()
        elif code == '09':
            self.__book_for_land_ownership()
        elif code == '10':
            self.__land_tax()
        elif code == '11':
            self.__land_tax_paid()
        elif code == '12':
            self.__land_fee_quarterly_find()
        elif code == '13':
            self.dlg = CadastrePageReportDialog()
            self.dlg.show()

        self.progressBar.setVisible(False)

    def __land_fee_quarterly_find(self):

        fee_unified = self.session.query(FeeUnified)

        # fee_unified = fee_unified.filter(FeeUnified.year_paid_for == int(self.year_sbox.value()))

        if self.person_id.text():
                filter_is_set = True
                value = "%" + self.person_id.text() + "%"
                fee_unified = fee_unified.filter(FeeUnified.person_id.ilike(value))
        if self.parcel_id.text():
                filter_is_set = True
                value = "%" + self.parcel_id.text() + "%"
                fee_unified = fee_unified.filter(FeeUnified.parcel_id.ilike(value))

        self.__remove_report_items()
        count = 0
        for fee in fee_unified:
            fee_contract = 0
            if fee.fee_contract:
                fee_contract = fee.fee_contract

            p_paid = 0
            if fee.p_paid:
                p_paid = fee.p_paid

            paid = 0
            if fee.paid:
                paid = fee.paid

            status = ''
            if fee.status == 10:
                status = u'Төсөл'
            if fee.status == 20:
                status = u'Идэвхтэй'
            if fee.status == 30:
                status = u'Хугацаа хэтэрсэн'
            if fee.status == 40:
                status = u'Цуцалсан'

            self.report_result_twidget.insertRow(count)

            item = QTableWidgetItem(fee.contract_no)
            item.setData(Qt.UserRole, str(fee.contract_no))
            item.setData(Qt.UserRole+1, fee.parcel_id)
            self.report_result_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(status)
            item.setData(Qt.UserRole, fee.status)
            self.report_result_twidget.setItem(count, 1, item)

            person_info = '/'+fee.person_id + '/ ' + fee.name + ' ' + fee.first_name
            item = QTableWidgetItem(unicode(person_info))
            item.setData(Qt.UserRole, fee.person_id)
            self.report_result_twidget.setItem(count, 2, item)

            item = QTableWidgetItem(str(fee_contract))
            item.setData(Qt.UserRole, fee_contract)
            self.report_result_twidget.setItem(count, 3, item)

            item = QTableWidgetItem(str(p_paid))
            item.setData(Qt.UserRole, p_paid)
            self.report_result_twidget.setItem(count, 4, item)

            item = QTableWidgetItem(str(paid))
            item.setData(Qt.UserRole, paid)
            self.report_result_twidget.setItem(count, 5, item)

            count += 1

        self.report_results_label.setText(self.tr("Results: ") + str(count))

    def __application_list(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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
            os.makedirs('D:/TM_LM2/archive')
            os.makedirs('D:/TM_LM2/refused_decision')
            os.makedirs('D:/TM_LM2/reports')
            os.makedirs('D:/TM_LM2/training')
        if not os.path.exists(default_path):
            os.makedirs(default_path)

        # path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"-"+"app_list.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 10)
        worksheet.set_column('D:D', 11)
        worksheet.set_column('E:E', 9)
        worksheet.set_column('F:F', 4)
        worksheet.set_column('G:G', 2.5)
        worksheet.set_column('H:H', 4)
        worksheet.set_column('I:I', 2.5)
        worksheet.set_column('J:J', 2.5)
        worksheet.set_column('K:K', 2.5)
        worksheet.set_column('L:L', 2.5)
        worksheet.set_column('M:M', 5)
        worksheet.set_column('N:N', 5)
        worksheet.set_column('O:O', 5)
        worksheet.set_column('P:P', 2.5)
        worksheet.set_column('Q:Q', 3)
        worksheet.set_column('R:R', 3)
        worksheet.set_column('S:S', 3)
        worksheet.set_column('T:T', 3)
        worksheet.set_column('U:U', 3)
        worksheet.set_column('V:V', 3)
        worksheet.set_column('W:W', 3)
        worksheet.set_column('X:X', 5)
        worksheet.set_column('Y:Y', 5)
        worksheet.set_row(4,150)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.2,right=0.1)

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(10)
        format.set_border(1)

        format1 = workbook.add_format()
        format1.set_text_wrap()
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_rotation(90)
        format1.set_font_name('Times New Roman')
        format1.set_font_size(10)
        format1.set_border(1)

        format2 = workbook.add_format()
        format2.set_text_wrap()
        format2.set_align('center')
        format2.set_align('vcenter')
        format2.set_font_name('Times New Roman')
        format2.set_font_size(10)
        format2.set_border(1)

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(14)
        format_header.set_bold()

        worksheet.merge_range('D2:M2', u'Өргөдлийн бүртгэл',format_header)
        worksheet.merge_range('A4:A5', u'Өргөдлийн дугаар',format)
        worksheet.merge_range('B4:B5', u'Иргэн, хуулийн этгээдийн нэр', format)
        worksheet.merge_range('C4:C5', u'Эзэмшил(э), ашиглалт(а), өмчлөл(ө) - ийн аль нь болох', format)
        worksheet.merge_range('D4:D5', u'Регистрийн дугаар', format)
        worksheet.merge_range('E4:E5', u'Өргөдөл хүлээн авсан огноо', format)
        worksheet.merge_range('F4:F5', u'Өргөдөлд хавсаргасан материалын тоо', format1)
        worksheet.merge_range('G4:W4', u'Үүнд', format)
        worksheet.write('G5',u"Газрын өргөдөл", format1)
        worksheet.write('H5',u"Иргэний үнэмлэх/төрсний гэрчилгээ/-ний хуулбар", format1)
        worksheet.write('I5',u"Оршин суугаа газрын тодорхойлолт", format1)
        worksheet.write('J5',u"Гэрчилгээ", format1)
        worksheet.write('K5',u"Гэрээ", format1)
        worksheet.write('L5',u"Тойм зураг", format1)
        worksheet.write('M5',u"Газар өмчлөх эрхийн улсын бүртгэлийн гэрчилгээний хуулбар", format1)
        worksheet.write('N5',u"Газар өмчлөх эрх олгосон ЗД захирмжийн хуулбар", format1)
        worksheet.write('O5',u"Газрын төлөв байдал, чанарын хянан баталгааны паспортын хуулбар", format1)
        worksheet.write('P5',u"Кадастрын зураг", format1)
        worksheet.write('Q5',u"Дуудлага худалдаа төсөл сонгон шалгаруулалтын материал", format1)
        worksheet.write('R5',u"Хууль ёсны төлөөлөгчийг нотлох ЗД, шүүхийн шийдвэрийн хуулбар, итгэмжлэх эх", format1)
        worksheet.write('S5',u"Газрын төлбөр төлсөн тухай баримт", format1)
        worksheet.write('T5',u"Газрын гэрчилгээ үргэдүүлснийг нотлох баримт", format1)
        worksheet.write('U5',u"Эрхийн гэрчилгээний үнэ төлсөн баримт", format1)
        worksheet.write('V5',u"Газар өмчлөх эрх шилжүүлэх гэрээний эх хувь", format1)
        worksheet.write('W5',u"Хамтран эзэмшигч, ашиглагч, өмчлөгчдийн иргэний үнэмлэхийн хуулбар", format1)
        worksheet.merge_range('X4:X5', u'Тайлбар',format)
        worksheet.merge_range('Y4:Y5', u'Гарын үсэг',format)

        row = 5
        col = 0
        app_doc_1 = 0
        app_doc_2 = 0
        app_doc_3 = 0
        app_doc_4 = 0
        app_doc_5 = 0
        app_doc_6 = 0
        app_doc_7 = 0
        app_doc_8 = 0
        app_doc_9 = 0
        app_doc_10 = 0
        app_doc_11 = 0
        app_doc_12 = 0
        app_doc_13 = 0
        app_doc_14 = 0
        app_doc_15 = 0
        app_doc_16 = 0
        app_doc_17 = 0
        begin_date = DatabaseUtils.convert_date(self.report_begin_date.date())
        end_date = DatabaseUtils.convert_date(self.report_end_date.date())
        end_date = end_date + timedelta(days=1)
        try:
            application = self.session.query(CtApplication).\
                filter(CtApplication.app_timestamp.between(begin_date, end_date)).all()
            if not self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex()) == -1:
                app_type = self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex())
                application = self.session.query(CtApplication).filter(CtApplication.app_type == app_type).\
                    filter(CtApplication.app_timestamp.between(begin_date, end_date)).all()
            if not self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex()) == -1:
                person_type = self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex())
                application = self.session.query(CtApplication).\
                    join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application).\
                    join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id).filter(BsPerson.type == person_type).\
                    filter(CtApplication.app_timestamp.between(begin_date, end_date)).all()
            if not self.report_app_status_cbox.itemData(self.report_app_status_cbox.currentIndex()) == -1:
                status = self.report_app_status_cbox.itemData(self.report_app_status_cbox.currentIndex())
                application = self.session.query(CtApplication).\
                    join(CtApplicationStatus, CtApplication.app_no == CtApplicationStatus.application).\
                    filter(CtApplicationStatus.status == status).\
                    filter(CtApplication.app_timestamp.between(begin_date, end_date)).all()
            count = len(application)
            self.progressBar.setMaximum(count)
            for app in application:
                app_person_count = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app.app_no).count()
                if app_person_count != 0:
                    app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app.app_no).all()

                    name = ''
                    type = ''
                    for app_person in app_person:
                        if app_person.main_applicant == True:
                            if app_person.person_ref.type == 10 or app_person.person_ref.type == 20 or app_person.person_ref.type == 50:
                                name = app_person.person_ref.name[:1] +'.'+ app_person.person_ref.first_name
                            elif app_person.person_ref.type == 30 or app_person.person_ref.type == 40 or app_person.person_ref.type == 60:
                                name = app_person.person_ref.name
                            app_doc_count = self.session.query(CtApplicationDocument)\
                                .join(CtApplicationPersonRole, CtApplicationDocument.application == CtApplicationPersonRole.application)\
                                .join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id)\
                                .filter(CtApplicationDocument.application == app.app_no)\
                                .filter(BsPerson.person_id == app_person.person).count()

                    if app.app_type == 01 or app.app_type == 02 or app.app_type == 03 or app.app_type == 04 or app.app_type == 15:
                        type = u'Ө'
                    elif (app.app_type == 06 or app.app_type == 9 or app.app_type == 10 or app.app_type == 12 or app.app_type == 13 or app.app_type == 14)\
                            and (app_person.person_ref.type == 50 or app_person.person_ref.type == 60):
                        type = u'А'
                    elif app.app_type == 05 or app.app_type == 07 or app.app_type == 8 or app.app_type == 10 or app.app_type == 0 or app.app_type == 11 \
                        and app.app_type == 12 or app.app_type == 13 or app.app_type == 14:
                        type = u'Э'

                    worksheet.write(row, col,  app.app_no, format)
                    worksheet.write(row, col+1,name, format)
                    worksheet.write(row, col+2,type, format)
                    worksheet.write(row, col+3,app_person.person_ref.person_id, format)
                    worksheet.write(row, col+4, str(app.app_timestamp),format)
                    worksheet.write(row, col+5, str(app_doc_count),format)
                    worksheet.write(row, col+23, app.remarks,format)
                    worksheet.write(row, col+24, '____',format)

                    if app_doc_count != 0:
                        app_doc = self.session.query(CtApplicationDocument)\
                            .join(CtApplicationPersonRole, CtApplicationDocument.application == CtApplicationPersonRole.application)\
                            .join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id)\
                            .filter(CtApplicationDocument.application == app.app_no)\
                            .filter(BsPerson.person_id == app_person.person_ref.person_id).all()
                        for doc in app_doc:
                            if doc.role == 1:
                                app_doc_1 = 1
                            elif doc.role == 2:
                                app_doc_2 = 1
                            elif doc.role == 3:
                                app_doc_3 = 1
                            elif doc.role == 8:
                                app_doc_4 = 1
                            elif doc.role == 9:
                                app_doc_5 = 1
                            elif doc.role == 4:
                                app_doc_6 = 1
                            elif doc.role == 18:
                                app_doc_7 = 1
                            elif doc.role == 17:
                                app_doc_8 = 1
                            elif doc.role == 12:
                                app_doc_9 = 1
                            elif doc.role == 11:
                                app_doc_10 = 1
                            elif doc.role == 5:
                                app_doc_11 = 1
                            elif doc.role == 16:
                                app_doc_12 = 1
                            elif doc.role == 13:
                                app_doc_13 = 1
                            elif doc.role == 10:
                                app_doc_14 = 1
                            elif doc.role == 14:
                                app_doc_15 = 1
                            elif doc.role == 19:
                                app_doc_16 = 1
                            elif doc.role == 23:
                                app_doc_17 = 1
                            worksheet.write(row, col+6, str(app_doc_1),format)
                            worksheet.write(row, col+7, str(app_doc_2),format)
                            worksheet.write(row, col+8, str(app_doc_3),format)
                            worksheet.write(row, col+9, str(app_doc_4),format)
                            worksheet.write(row, col+10, str(app_doc_5),format)
                            worksheet.write(row, col+11, str(app_doc_6),format)
                            worksheet.write(row, col+12, str(app_doc_7),format)
                            worksheet.write(row, col+13, str(app_doc_8),format)
                            worksheet.write(row, col+14, str(app_doc_9),format)
                            worksheet.write(row, col+15, str(app_doc_10),format)
                            worksheet.write(row, col+16, str(app_doc_11),format)
                            worksheet.write(row, col+17, str(app_doc_12),format)
                            worksheet.write(row, col+18, str(app_doc_13),format)
                            worksheet.write(row, col+19, str(app_doc_14),format)
                            worksheet.write(row, col+20, str(app_doc_15),format)
                            worksheet.write(row, col+21, str(app_doc_16),format)
                            worksheet.write(row, col+22, str(app_doc_17),format)
                        app_doc_1 = 0
                        app_doc_2 = 0
                        app_doc_3 = 0
                        app_doc_4 = 0
                        app_doc_5 = 0
                        app_doc_6 = 0
                        app_doc_7 = 0
                        app_doc_8 = 0
                        app_doc_9 = 0
                        app_doc_10 = 0
                        app_doc_11 = 0
                        app_doc_12 = 0
                        app_doc_13 = 0
                        app_doc_14 = 0
                        app_doc_15 = 0
                        app_doc_16 = 0
                        app_doc_17 = 0
                    else:

                        worksheet.write(row, col+6, str(app_doc_1),format)
                        worksheet.write(row, col+7, str(app_doc_2),format)
                        worksheet.write(row, col+8, str(app_doc_3),format)
                        worksheet.write(row, col+9, str(app_doc_4),format)
                        worksheet.write(row, col+10, str(app_doc_5),format)
                        worksheet.write(row, col+11, str(app_doc_6),format)
                        worksheet.write(row, col+12, str(app_doc_7),format)
                        worksheet.write(row, col+13, str(app_doc_8),format)
                        worksheet.write(row, col+14, str(app_doc_9),format)
                        worksheet.write(row, col+15, str(app_doc_10),format)
                        worksheet.write(row, col+16, str(app_doc_11),format)
                        worksheet.write(row, col+17, str(app_doc_12),format)
                        worksheet.write(row, col+18, str(app_doc_13),format)
                        worksheet.write(row, col+19, str(app_doc_14),format)
                        worksheet.write(row, col+20, str(app_doc_15),format)
                        worksheet.write(row, col+21, str(app_doc_16),format)
                        worksheet.write(row, col+22, str(app_doc_17),format)

                    row += 1
                    value_p = self.progressBar.value() + 1
                    self.progressBar.setValue(value_p)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"-"+"app_list.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __app_steps_progress(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"-"+"app_steps_progress.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 45)
        worksheet.set_column('B:B', 9)
        worksheet.set_column('C:C', 9)
        worksheet.set_column('D:D', 9)
        worksheet.set_column('E:E', 9)
        worksheet.set_column('F:F', 9)
        worksheet.set_column('G:G', 9)
        worksheet.set_column('H:H', 9)
        worksheet.set_column('I:I', 9)
        worksheet.set_column('J:J', 9)

        worksheet.set_row(3,99)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.3,right=0.3)

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(10)
        format.set_border(1)

        format1 = workbook.add_format()
        format1.set_text_wrap()
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_font_name('Times New Roman')
        format1.set_rotation(90)
        format1.set_font_size(10)
        format1.set_border(1)

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(14)
        format_header.set_bold()

        worksheet.merge_range('A2:J2', u'Өргөдөл шийдвэрлэлтийн бүртгэл',format_header)
        worksheet.write('A4', u'Өргөдлийн төрөл',format)
        worksheet.write('B4', u'1. Өргөдөл хүлээн авч бүртгэсэн', format1)
        worksheet.write('C4', u'2. Суурин судалгаа хийх', format1)
        worksheet.write('D4', u'3. Хээрийн судалгаа хийх', format1)
        worksheet.write('E4', u'4. Кадастрын зурагт шинэчлэл хийх', format1)
        worksheet.write('F4', u'5. Засаг даргын захирамжийн төсөлд оруулах', format1)
        worksheet.write('G4', u'6. Засаг даргын захирамжийн төсөлд явуулах', format1)
        worksheet.write('H4', u'7. Засаг даргын захирамж бүртгэх', format1)
        worksheet.write('I4', u'8. Засаг даргын захирамжийн хариу мэдэгдэх', format1)
        worksheet.write('J4', u'9. Гэрээ байгуулж гэрчилгээ олгох', format1)

        row = 4
        col = 0
        status1 = 0
        status2 = 0
        status3 = 0
        status4 = 0
        status5 = 0
        status6 = 0
        status7 = 0
        status8 = 0
        status9 = 0
        begin_date = DatabaseUtils.convert_date(self.report_begin_date.date())
        end_date = DatabaseUtils.convert_date(self.report_end_date.date())
        end_date = end_date + timedelta(days=1)
        try:
            app_type = self.session.query(ClApplicationType). \
                filter(and_(ClApplicationType.code != ApplicationType.pasture_use,
                            ClApplicationType.code != ApplicationType.right_land)).all()
            app_statuses = self.session.query(ClApplicationStatus).all()

            values = self.session.query(CtApplication, CtApplicationStatus).\
                join(CtApplicationStatus, CtApplication.app_no == CtApplicationStatus.application).\
                filter(CtApplicationStatus.status == 1).\
                filter(CtApplication.app_timestamp.between(begin_date, end_date)).all()

            applications = self.session.query(ApplicationSearch)

            filter_is_set = False
            sub = self.session.query(ApplicationSearch, func.row_number().over(partition_by = ApplicationSearch.app_no, order_by = (desc(ApplicationSearch.status_date), desc(ApplicationSearch.status))).label("row_number")).subquery()
            applications = applications.select_entity_from(sub)

            applications = applications. \
                filter(and_(ApplicationSearch.app_type != ApplicationType.pasture_use,
                            ApplicationSearch.app_type != ApplicationType.right_land))

            applications = applications. \
                filter(and_(ApplicationSearch.app_type != ApplicationType.pasture_use,
                            ApplicationSearch.app_type != ApplicationType.right_land))

            applications = applications. \
                join(CtApplication, ApplicationSearch.app_no == CtApplication.app_no). \
                filter(sub.c.row_number == 1). \
                filter(CtApplication.app_timestamp.between(begin_date, end_date))

            count = len(app_type)
            self.progressBar.setMaximum(count)
            for type in app_type:
                for value in values:
                    if value.CtApplication.app_type == type.code:
                        status1 += 1
                for status in app_statuses:
                    if status.code != 1:
                        applications_count = applications.filter(ApplicationSearch.status == status.code)\
                            .filter(ApplicationSearch.app_type == type.code).count()
                        if status.code == 2:
                            status2 = applications_count
                        elif status.code == 3:
                            status3 = applications_count
                        elif status.code == 4:
                            status4 = applications_count
                        elif status.code == 5:
                            status5 = applications_count
                        elif status.code == 6:
                            status6 = applications_count
                        elif status.code == 7:
                            status7 = applications_count
                        elif status.code == 8:
                            status8 = applications_count
                        elif status.code == 9:
                            status9 = applications_count

                worksheet.write(row, col, type.description,format)
                worksheet.write(row, col+1,status1,format)
                worksheet.write(row, col+2,status2,format)
                worksheet.write(row, col+3,status3,format)
                worksheet.write(row, col+4,status4,format)
                worksheet.write(row, col+5,status5,format)
                worksheet.write(row, col+6,status6,format)
                worksheet.write(row, col+7,status7,format)
                worksheet.write(row, col+8,status8,format)
                worksheet.write(row, col+9,status9,format)

                row += 1
                status1 = 0
                status2 = 0
                status3 = 0
                status4 = 0
                status5 = 0
                status6 = 0
                status7 = 0
                status8 = 0
                status9 = 0
                value_p = self.progressBar.value() + 1
                self.progressBar.setValue(value_p)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"-"+"app_steps_progress.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __invalid_parcel(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path +"/"+restrictions+"-"+ "invalid_parcel.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 12)
        worksheet.set_column('D:D', 16)
        worksheet.set_column('E:E', 18)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 9)
        worksheet.set_column('H:H', 9)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 12)
        worksheet.set_column('K:K', 11)
        worksheet.set_column('L:L', 5)

        worksheet.set_row(3,20)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.3,right=0.3)

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(10)
        format.set_border(1)

        format1 = workbook.add_format()
        format1.set_text_wrap()
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_font_name('Times New Roman')
        format1.set_rotation(90)
        format1.set_font_size(10)
        format1.set_border(1)

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(14)
        format_header.set_bold()

        worksheet.merge_range('C2:I2', u'Хүчингүй нэгж талбарын жагсаалт',format_header)
        worksheet.merge_range('A4:A5', u'Д/д',format)
        worksheet.merge_range('B4:E4', u'Нэгж талбарын мэдээлэл', format)
        worksheet.write('B5', u'Дугаар',format)
        worksheet.write('C5', u'Хуучин дугаар', format)
        worksheet.write('D5', u'Хаяг', format)
        worksheet.write('E5', u'Ангилал', format)
        worksheet.merge_range('F4:I4', u'Ирэн, Хуулийн этгээдийн мэдээлэл', format)
        worksheet.write('F5', u'Иргэн, Хуулийн этгээдийн нэр', format)
        worksheet.write('G5', u'Регистрийн дугаар', format)
        worksheet.write('H5', u'Хувь', format)
        worksheet.merge_range('I4:J4', u'Өргөдлийн Мэдээлэл', format)
        worksheet.write('I5', u'Өргөдлийн дугаар', format)
        worksheet.write('J5', u'Өргөдлийн хугацаа', format)

        try:
            row = 5
            col = 0
            row_number = 1
            khashaa = ''
            streetname = ''
            landuse = ''
            person_name = ''
            person_id = ''
            a3_name = ''
            person_share = 0
            c_status = 0
            application = self.session.query(CtApplication).\
                join(CaParcel, CtApplication.parcel == CaParcel.parcel_id).\
                join(CtApplicationStatus, CtApplication.app_no == CtApplicationStatus.application).\
                filter(CtApplicationStatus.status == 8).all()
            if not self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex()) == -1:
                application = self.session.query(CtApplication).\
                join(CaParcel, CtApplication.parcel == CaParcel.parcel_id).\
                filter(CtApplication.app_type == self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex())).all()
            if not self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex()) == -1:
                application = self.session.query(CtApplication).\
                    join(CaParcel, CtApplication.parcel == CaParcel.parcel_id).\
                    filter(CtApplication.approved_landuse == self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex())).all()
            count = len(application)
            self.progressBar.setMaximum(count)
            for app in application:
                if app.parcel != None:
                    a3 = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(app.parcel_ref.geometry)).one()
                    a3_name = a3.name
                parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == app.parcel_ref.parcel_id).one()
                app_person_count = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app.app_no).count()

                if parcel.landuse != None:
                    landuse = parcel.landuse_ref.description
                    landuse_code = parcel.landuse_ref.code
                if app.parcel_ref.address_khashaa != None:
                    khashaa = app.parcel_ref.address_khashaa
                if app.parcel_ref.address_streetname != None:
                    app.parcel_ref.streetname = streetname

                if app_person_count == 1:
                    app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app.app_no).one()
                    if app_person.person != None:
                        if app_person.person_ref.type == 10 or app_person.person_ref.type == 20 or app_person.person_ref.type == 50:
                            person_name = app_person.person_ref.name[:1] +'.'+ app_person.person_ref.first_name
                        elif app_person.person_ref.type == 30 or app_person.person_ref.type == 40 or app_person.person_ref.type == 60:
                            person_name = app_person.person_ref.name
                        person_id = app_person.person_ref.person_id
                        person_share = str(app_person.share)
                    parcel_address = a3_name + ', '+ streetname +u' гудамж,'+ khashaa + u' хашаа'

                    worksheet.write(row, col, row_number,format)
                    worksheet.write(row, col+1,app.parcel_ref.parcel_id,format)
                    worksheet.write(row, col+2,app.parcel_ref.old_parcel_id,format)
                    worksheet.write(row, col+3,parcel_address,format)
                    worksheet.write(row, col+4,landuse,format)
                    worksheet.write(row, col+5,person_name,format)
                    worksheet.write(row, col+6,person_id,format)
                    worksheet.write(row, col+7,person_share,format)
                    worksheet.write(row, col+8,app.app_no,format)
                    worksheet.write(row, col+9,str(app.app_timestamp),format)

                    row += 1
                    row_number += 1
                    value_p = self.progressBar.value() + 1
                    self.progressBar.setValue(value_p)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path +"/"+restrictions+"-"+ "invalid_parcel.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __end_parcel_yearly(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/"+ restrictions + "-" + "end_parcel.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 12)
        worksheet.set_column('D:D', 16)
        worksheet.set_column('E:E', 18)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 9)
        worksheet.set_column('H:H', 9)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 12)
        worksheet.set_column('K:K', 11)
        worksheet.set_column('L:L', 5)

        worksheet.set_row(3,20)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.3,right=0.3)

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(10)
        format.set_border(1)

        format1 = workbook.add_format()
        format1.set_text_wrap()
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_font_name('Times New Roman')
        format1.set_rotation(90)
        format1.set_font_size(10)
        format1.set_border(1)

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(14)
        format_header.set_bold()

        worksheet.merge_range('D2:N2', u'Тухайн жил хугацаа нь дуусах нэгж талбарын жагсаалт',format_header)
        worksheet.merge_range('A4:A5', u'Д/д',format)
        worksheet.merge_range('B4:E4', u'Нэгж талбарын мэдээлэл', format)
        worksheet.write('B5', u'Дугаар',format)
        worksheet.write('C5', u'Хуучин дугаар', format)
        worksheet.write('D5', u'Хаяг', format)
        worksheet.write('E5', u'Ангилал', format)
        worksheet.merge_range('F4:I4', u'Гэрээ/Өмчлөл-ийн мэдээлэл', format)
        worksheet.write('F5', u'Гэрээ/Өмчлөл-ийн бүртгэлийн дугаар', format)
        worksheet.write('G5', u'Гэрээ/Өмчлөл-ийн огноо', format)
        worksheet.write('H5', u'Гэрээ дуусах огноо', format)
        worksheet.write('I5', u'Гэрээ/Өмчлөл-ийн төлөв', format)
        worksheet.merge_range('J4:L4', u'Иргэн хуулийн этгээдийн мэдээлэл', format)
        worksheet.write('J5', u'Иргэн, хуулийн тэгээдийн нэр', format)
        worksheet.write('K5', u'Регистрийн дугаар', format)
        worksheet.write('L5', u'Хувь', format)

        try:
            row = 5
            col = 0
            row_number = 1
            khashaa = ''
            streetname = ''
            landuse = ''
            person_name = ''
            person_id = ''
            contract_no = ''
            contract_begin = ''
            contract_end = ''
            contract_status = ''
            parcel_address = ''
            person_share = 0
            a3_name = ''
            c_status = 0
            application = self.session.query(CtApplication).\
                join(CaParcel, CtApplication.parcel == CaParcel.parcel_id).all()
            if not self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex()) == -1:
                application = self.session.query(CtApplication).\
                    join(CaParcel, CtApplication.parcel == CaParcel.parcel_id).\
                    filter(CtApplication.app_type == self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex())).all()
            if not self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex()) == -1:
                application = self.session.query(CtApplication).\
                    join(CaParcel, CtApplication.parcel == CaParcel.parcel_id).\
                    filter(CtApplication.approved_landuse == self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex())).all()
            count = len(application)
            self.progressBar.setMaximum(count)
            for app in application:

                if app.parcel != None:
                    a3_count = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(app.parcel_ref.geometry)).count()
                    if a3_count != 0:
                        a3 = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(app.parcel_ref.geometry)).one()
                        a3_name = a3.name
                parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == app.parcel_ref.parcel_id).one()
                app_contract_count = self.session.query(CtContractApplicationRole).filter(CtContractApplicationRole.application == app.app_no).count()

                if app_contract_count == 1:
                    app_contract = self.session.query(CtContractApplicationRole).filter(CtContractApplicationRole.application == app.app_no).one()
                    contract = self.session.query(CtContract).filter(CtContract.contract_no == app_contract.contract).one()
                    contract_no = contract.contract_no
                    contract_begin = contract.contract_begin
                    contract_end = str(contract.contract_end)
                    contract_status = contract.status_ref.description
                    c_status = contract.status_ref.code
                    begin_date = DatabaseUtils.convert_date(self.report_begin_date.date())
                    end_date = DatabaseUtils.convert_date(self.report_end_date.date())
                    end_date = end_date + timedelta(days=1)

                app_person_count = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app.app_no).count()

                first_name = ''
                name = ''
                if parcel.landuse != None:
                    landuse = parcel.landuse_ref.description
                    landuse_code = parcel.landuse_ref.code
                if app.parcel_ref.address_khashaa != None:
                    khashaa = app.parcel_ref.address_khashaa
                if app.parcel_ref.address_streetname != None:
                    app.parcel_ref.streetname = streetname
                if app_person_count == 1:
                    app_person_role = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app.app_no).one()
                    person_count = self.session.query(BsPerson).filter(BsPerson.person_id == app_person_role.person).count()
                    if person_count != 0:
                        app_person = self.session.query(BsPerson).filter(BsPerson.person_id == app_person_role.person).one()
                        if app_person.person_id != None:
                            if app_person.type == 10 or app_person.type == 20 or app_person.type == 50:
                                if app_person.first_name != None:
                                    first_name = app_person.first_name
                                if app_person.name != None:
                                    name = app_person.name
                                person_name = name[:1] +'.'+ first_name
                            elif app_person.type == 30 or app_person.type == 40 or app_person.type == 60:
                                person_name = app_person.name
                            person_id = app_person.person_id
                            person_share = str(app_person_role.share)
                        parcel_address = a3_name + ', '+ streetname +u' гудамж,'+ khashaa + u' хашаа'

                if app_contract_count == 1 and contract.contract_end != None and contract.contract_end >= begin_date and contract.contract_end <= end_date:
                    app_person_role = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == app.app_no).one()
                    person_count = self.session.query(BsPerson).filter(BsPerson.person_id == app_person_role.person).count()
                    if person_count != 0:

                        app_person = self.session.query(BsPerson).filter(BsPerson.person_id == app_person_role.person).one()
                        if not self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex()) == -1:
                            if app_person.type == self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex()):
                                worksheet.write(row, col, row_number,format)
                                worksheet.write(row, col+1,app.parcel_ref.parcel_id,format)
                                worksheet.write(row, col+2,app.parcel_ref.old_parcel_id,format)
                                worksheet.write(row, col+3,parcel_address,format)
                                worksheet.write(row, col+4,landuse,format)
                                worksheet.write(row, col+5,contract_no,format)
                                worksheet.write(row, col+6,str(contract_begin),format)
                                worksheet.write(row, col+7,contract_end,format)
                                worksheet.write(row, col+8,contract_status,format)
                                worksheet.write(row, col+9,person_name,format)
                                worksheet.write(row, col+10,person_id,format)
                                worksheet.write(row, col+11,person_share,format)
                                row += 1
                                row_number += 1
                        else:
                            worksheet.write(row, col, row_number,format)
                            worksheet.write(row, col+1,app.parcel_ref.parcel_id,format)
                            worksheet.write(row, col+2,app.parcel_ref.old_parcel_id,format)
                            worksheet.write(row, col+3,parcel_address,format)
                            worksheet.write(row, col+4,landuse,format)
                            worksheet.write(row, col+5,contract_no,format)
                            worksheet.write(row, col+6,str(contract_begin),format)
                            worksheet.write(row, col+7,contract_end,format)
                            worksheet.write(row, col+8,contract_status,format)
                            worksheet.write(row, col+9,person_name,format)
                            worksheet.write(row, col+10,person_id,format)
                            worksheet.write(row, col+11,person_share,format)
                            row += 1
                            row_number += 1
                            value_p  = self.progressBar.value() + 1
                            self.progressBar.setValue(value_p)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+ restrictions + "-" + "end_parcel.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __book_for_land_ownership(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/" + restrictions + "-" + "book_for_land_ownership.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 7)
        worksheet.set_column('D:D', 7)
        worksheet.set_column('E:E', 8)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 9)
        worksheet.set_column('H:H', 9)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 12)
        worksheet.set_column('K:K', 11)
        worksheet.set_column('L:L', 11)
        worksheet.set_column('M:M', 11)
        worksheet.set_column('N:N', 11)
        worksheet.set_column('O:O', 10)
        worksheet.set_column('P:P', 10)
        worksheet.set_column('Q:Q', 10)
        worksheet.set_column('R:R', 10)
        worksheet.set_column('S:S', 10)
        worksheet.set_column('T:T', 8)
        worksheet.set_column('U:U', 11)
        worksheet.set_column('V:V', 12)
        worksheet.set_column('W:W', 12)
        worksheet.set_column('X:X', 11)
        worksheet.set_column('Y:Y', 12)
        worksheet.set_column('Z:Z', 10)
        worksheet.set_column('AA:AA', 12)

        worksheet.set_row(3,25)
        worksheet.set_row(5,50)
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

        worksheet.merge_range('D2:L2', u'Газар өмчлөгчийн улсын бүртгэл',format_header)
        worksheet.merge_range('A4:A6', u'Д/д',format)
        worksheet.merge_range('B4:J4', u'Нэгж талбарын мэдээлэл', format)
        worksheet.merge_range('C5:D5', u'Газрын хэмжээ', format)
        worksheet.merge_range('G5:J5', u'Газрын байршлын нэр, хаяг', format)
        worksheet.merge_range('B5:B6', u'Нэгж талбарын дугаар', format)
        worksheet.write('C6',u'м2', format)
        worksheet.write('D6',u'га', format)
        worksheet.merge_range('E5:E6', u'Газрын үнэ /мян.төг/', format)
        worksheet.merge_range('F5:F6', u'Газрын зориулалт', format)
        worksheet.write('G6', u'Баг /хороо/', format)
        worksheet.write('H6', u'Гудамж /хороолол/', format)
        worksheet.write('I6', u'Байр /хашаа,хаалга/-ны дугаар', format)
        worksheet.write('J6', u'Байршшил', format)
        worksheet.merge_range('K4:S4', u'Газар өмчлөгчийн мэдээлэл', format)
        worksheet.merge_range('K5:K6', u'Овог', format)
        worksheet.merge_range('L5:L6', u'Эцэг /эх/-ийн нэр', format)
        worksheet.merge_range('M5:M6', u'Нэр', format)
        worksheet.merge_range('N5:N6', u'Регистрийн дугаар', format)
        worksheet.merge_range('P5:S5', u'Байнгын хаяг', format)
        worksheet.write('O6', u'Аймаг /нийслэл/', format)
        worksheet.write('P6', u'Сум /дүүрэг/', format)
        worksheet.write('Q6', u'Баг /хороо/', format)
        worksheet.write('R6', u'Гудамж /хороолол/', format)
        worksheet.write('S6', u'Байр /хашаа, хаалга/-ны дугаар', format)
        worksheet.merge_range('T4:U4', u'Газар өмчлүүлэх эрх олгосон үндэслэл', format)
        worksheet.merge_range('T5:T6', u'Огноо', format)
        worksheet.merge_range('U5:U6', u'Захирамжийн дугаар', format)
        worksheet.merge_range('V4:X4', u'Итгэмжлэгдсэн төлөөлөгч', format)
        worksheet.merge_range('V5:V6', u'Эцэг /эх/-ийн нэр', format)
        worksheet.merge_range('W5:W6', u'Нэр', format)
        worksheet.merge_range('X5:X6', u'Регистрийн дугаар', format)
        worksheet.merge_range('Y4:Y6', u'худалдсан-Ху, арилжсан-А, өвлүүлсэн-Ө, бэлэглэсэн-Б, Хасагдсан-Ха аль нь болох', format)
        worksheet.merge_range('Z4:Z6', u'Бүртгэсэн огноо', format)
        worksheet.merge_range('AA4:AA6', u'Албан тушаалтны гарын үсэг', format)

        begin_date = DatabaseUtils.convert_date(self.report_begin_date.date())
        end_date = DatabaseUtils.convert_date(self.report_end_date.date())
        end_date = end_date + timedelta(days=1)

        row = 6
        col = 0
        row_number = 1
        c_status = 0
        try:
            values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).\
                filter(CtApplication.parcel_ref != None).all()
            if not self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex()) == -1:
                type = self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex())
                values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).\
                filter(CtApplication.app_type == type).\
                filter(CtApplication.parcel_ref != None).all()
            if not self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex()) == -1:
                type = self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex())
                values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).\
                filter(CtApplication.approved_landuse == type).\
                filter(CtApplication.parcel_ref != None).all()
            if not self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex()) == -1:
                type = self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex())
                values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application).\
                join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).\
                filter(BsPerson.type == type).\
                filter(CtApplication.parcel_ref != None).all()
            if self.parcel_id.text():
                value_like = "%" + self.parcel_id.text() + "%"
                values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application).\
                join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).\
                filter(CtApplication.parcel.ilike(value_like)).\
                filter(CtApplication.parcel_ref != None).all()
            if self.person_id.text():
                value_like = "%" + self.person_id.text() + "%"
                values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application).\
                join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).\
                filter(BsPerson.person_id.ilike(value_like)).\
                filter(CtApplication.parcel_ref != None).all()

            count = len(values)
            self.progressBar.setMaximum(count)
            for value in values:

                khashaa = ''
                streetname = ''
                neighbourhood = ''
                landuse = ''
                middle_name = ''
                first_name = ''
                surname = ''
                person_address_a1 = '-'
                person_address_a2 = '-'
                person_address_a3 = '-'
                person_address_street_name = '-'
                person_address_khaskhaa = '-'
                legal_surname = ''
                legal_name = ''
                legal_person_id = ''
                owner_change = ''
                price = ''
                a3_name = ''
                person_name = ''
                person_id = ''
                contract_no = ''
                contract_begin = ''
                contract_end = ''
                contract_status = ''

                if value.CtApplication.approved_landuse != None:
                    landuse = value.CtApplication.approved_landuse_ref.description
                    landuse_code = value.CtApplication.approved_landuse_ref.code
                if value.CtApplication.parcel_ref != None:

                    if value.CtApplication.parcel_ref != None:
                        khashaa = value.CtApplication.parcel_ref.address_khashaa
                    if value.CtApplication.parcel_ref != None:
                        streetname = value.CtApplication.parcel_ref.address_streetname
                    if value.CtApplication.parcel_ref != None:
                        neighbourhood = value.CtApplication.parcel_ref.address_neighbourhood

                    app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == value.CtApplication.app_no).all()
                    if value.CtApplication.app_type == 02:
                        app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == value.CtApplication.app_no)\
                                        .filter(CtApplicationPersonRole.role == 40).all()
                    elif value.CtApplication.app_type == 15 or value.CtApplication.app_type == 14:
                        app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == value.CtApplication.app_no)\
                                        .filter(CtApplicationPersonRole.role == 70).all()
                    else:
                        app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == value.CtApplication.app_no)\
                                        .filter(CtApplicationPersonRole.main_applicant == True).all()
                    for person_app in app_person:
                        person_count = self.session.query(BsPerson).filter(BsPerson.person_id == person_app.person).count()
                        if person_count != 0:
                            person = self.session.query(BsPerson).filter(BsPerson.person_id == person_app.person).one()
                            a3_count = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).\
                                filter(value.CtApplication.parcel_ref != None).count()
                            if a3_count != 0:
                                a3 = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).one()
                                a3_name = a3.name
                            tax_zone_count = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).count()
                            if tax_zone_count == 1:
                                tax_zone = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).one()
                                tax_count = self.session.query(SetBaseTaxAndPrice).\
                                    filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id).\
                                    filter(SetBaseTaxAndPrice.landuse == value.CtApplication.approved_landuse).count()
                                if tax_count == 1:
                                    tax = self.session.query(SetBaseTaxAndPrice).\
                                        filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id).\
                                        filter(SetBaseTaxAndPrice.landuse == value.CtApplication.approved_landuse).one()
                                    price = str(float(tax.base_value_per_m2) * value.CtApplication.parcel_ref.area_m2)
                            if person.address_au_level3 != None:
                                person_a3 = self.session.query(AuLevel3).filter(AuLevel3.code == person.address_au_level3).one()
                                person_address_a3 = person_a3.name
                            if person.address_au_level2 != None:
                                person_a2 = self.session.query(AuLevel2).filter(AuLevel2.code == person.address_au_level2).one()
                                person_address_a2 = person_a2.name
                            if person.address_au_level1 != None:
                                person_a1 = self.session.query(AuLevel1).filter(AuLevel1.code == person.address_au_level1).one()
                                person_address_a1 = person_a1.name
                            if person.address_street_name != None:
                                person_address_street_name = person.address_street_name
                            if person.address_khaskhaa != None:
                                person_address_khaskhaa = person.address_khaskhaa

                            if person.type == 10 or person.type == 20 \
                                or person.type == 50:
                                if person.middle_name != None:
                                    middle_name = person.middle_name
                                if person.first_name != None:
                                    first_name = person.first_name
                                if person.name != None:
                                    surname = person.name
                            if person.type == 30 or person.type == 40 \
                                or person.type == 60:
                                first_name = person.name

                            if person_app.role == Constants.LEGAL_REP_ROLE_CODE:
                                legal_surname = person.name
                                legal_name = person.first_name
                                legal_person_id = person.person_id

                                worksheet.write(row, col+21, legal_surname, format)
                                worksheet.write(row, col+22, legal_name, format)
                                worksheet.write(row, col+23, legal_person_id, format)

                            elif person_app.role == Constants.GIVING_UP_OWNER_CODE:
                                owner_change = u'Ха'
                                worksheet.write(row, col+24, owner_change, format)
                            else:
                                worksheet.write(row, col, row_number, format)
                                worksheet.write(row, col+1, value.CtApplication.parcel_ref.parcel_id, format)
                                worksheet.write(row, col+2, str(value.CtApplication.parcel_ref.area_m2), format)
                                worksheet.write(row, col+3, str(value.CtApplication.parcel_ref.area_m2/10000), format)
                                worksheet.write(row, col+4, price, format)
                                worksheet.write(row, col+5, landuse, format)
                                worksheet.write(row, col+6, a3_name, format)
                                worksheet.write(row, col+7, streetname, format)
                                worksheet.write(row, col+8, khashaa, format)
                                worksheet.write(row, col+9, neighbourhood, format)
                                worksheet.write(row, col+10, middle_name, format)
                                worksheet.write(row, col+11, surname, format)
                                worksheet.write(row, col+12, first_name, format)
                                worksheet.write(row, col+13, person.person_id, format)
                                worksheet.write(row, col+14, person_address_a1, format)
                                worksheet.write(row, col+15, person_address_a2, format)
                                worksheet.write(row, col+16, person_address_a3, format)
                                worksheet.write(row, col+17, person_address_street_name, format)
                                worksheet.write(row, col+18, person_address_khaskhaa, format)
                                worksheet.write(row, col+19, str(value.CtDecisionApplication.decision_ref.decision_date), format)
                                worksheet.write(row, col+20, value.CtDecisionApplication.decision, format)
                                worksheet.write(row, col+21, legal_surname, format)
                                worksheet.write(row, col+22, legal_name, format)
                                worksheet.write(row, col+23, legal_person_id, format)
                                worksheet.write(row, col+24, owner_change, format)
                                worksheet.write(row, col+25, str(value.CtOwnershipRecord.record_date), format)
                                worksheet.write(row, col+26, u'_________', format)
                                row += 1
                                row_number += 1
                                value_p = self.progressBar.value() + 1
                                self.progressBar.setValue(value_p)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/" + restrictions + "-" + "book_for_land_ownership.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __book_for_land_possess(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/" + restrictions + "-" + "book_for_land_possess.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 7)
        worksheet.set_column('D:D', 7)
        worksheet.set_column('E:E', 8)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 9)
        worksheet.set_column('H:H', 9)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 12)
        worksheet.set_column('K:K', 11)
        worksheet.set_column('L:L', 11)
        worksheet.set_column('M:M', 11)
        worksheet.set_column('N:N', 11)
        worksheet.set_column('O:O', 10)
        worksheet.set_column('P:P', 10)
        worksheet.set_column('Q:Q', 10)
        worksheet.set_column('R:R', 10)
        worksheet.set_column('S:S', 10)
        worksheet.set_column('T:T', 8)
        worksheet.set_column('U:U', 11)
        worksheet.set_column('V:V', 12)
        worksheet.set_column('W:W', 12)
        worksheet.set_column('X:X', 11)
        worksheet.set_column('Y:Y', 12)
        worksheet.set_column('Z:Z', 10)
        worksheet.set_column('AA:AA', 12)
        worksheet.set_column('AB:AB', 12)
        worksheet.set_column('AC:AC', 12)
        worksheet.set_column('AE:AE', 12)

        worksheet.set_row(3,25)
        worksheet.set_row(4,25)
        worksheet.set_row(5,50)
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

        worksheet.merge_range('D2:L2', u'Газар эзэмшигчийн улсын бүртгэл',format_header)
        worksheet.merge_range('A4:A6', u'Д/д',format)
        worksheet.merge_range('B4:J4', u'Нэгж талбарын мэдээлэл', format)
        worksheet.merge_range('C5:D5', u'Газрын хэмжээ', format)
        worksheet.merge_range('G5:J5', u'Газрын байршлын нэр, хаяг', format)
        worksheet.merge_range('B5:B6', u'Нэгж талбарын дугаар', format)
        worksheet.write('C6',u'м2', format)
        worksheet.write('D6',u'га', format)
        worksheet.merge_range('E5:E6', u'Газрын үнэ /мян.төг/', format)
        worksheet.merge_range('F5:F6', u'Газрын зориулалт', format)
        worksheet.write('G6', u'Баг /хороо/', format)
        worksheet.write('H6', u'Гудамж /хороолол/', format)
        worksheet.write('I6', u'Байр /хашаа,хаалга/-ны дугаар', format)
        worksheet.write('J6', u'Байршшил', format)
        worksheet.merge_range('K4:S4', u'Газар өмчлөгчийн мэдээлэл', format)
        worksheet.merge_range('K5:K6', u'Овог', format)
        worksheet.merge_range('L5:L6', u'Эцэг /эх/-ийн нэр', format)
        worksheet.merge_range('M5:M6', u'Нэр', format)
        worksheet.merge_range('N5:N6', u'Регистрийн дугаар', format)
        worksheet.merge_range('P5:S5', u'Байнгын хаяг', format)
        worksheet.write('O6', u'Аймаг /нийслэл/', format)
        worksheet.write('P6', u'Сум /дүүрэг/', format)
        worksheet.write('Q6', u'Баг /хороо/', format)
        worksheet.write('R6', u'Гудамж /хороолол/', format)
        worksheet.write('S6', u'Байр /хашаа, хаалга/-ны дугаар', format)
        worksheet.merge_range('T4:U4', u'Газар өмчлүүлэх эрх олгосон үндэслэл', format)
        worksheet.merge_range('T5:T6', u'Огноо', format)
        worksheet.merge_range('U5:U6', u'Захирамжийн дугаар', format)
        worksheet.merge_range('V4:X4', u'Гэрээ', format)
        worksheet.merge_range('V5:V6', u'Эрхийн гэрчилгээний дугаар', format)
        worksheet.merge_range('W5:W6', u'Гэрээний дугаар', format)
        worksheet.merge_range('X5:X6', u'Хугацаа', format)
        worksheet.merge_range('Y4:AD4', u'Гэрээ, гэрчилгээ, эрхийн өөрчлөлт, шилжилт', format)
        worksheet.merge_range('Y5:Y6', u'Гэрээ, гэрчилгээний хугацаа сунгах', format)
        worksheet.merge_range('Z5:Z6', u'Нөхөн авсан гэрчилгээний дугаар', format)
        worksheet.merge_range('AA5:AA6', u'Өөрчлөгдөн газар ашиглалтын зориулалт', format)
        worksheet.merge_range('AB5:AB6', u'худалдсан-Х, арилжсан-А, өвлүүлсэн-Ө, бэлэглэсэн-Б аль нь болох', format)
        worksheet.merge_range('AC5:AD5', u'Эзэмшигчийн эрх хүчингүй болсон', format)
        worksheet.write('AC6', u'Огноо', format)
        worksheet.write('AD6', u'Захирамж шийдвэрийн дугаар', format)
        worksheet.merge_range('AE4:AE6', u'Тайлбар', format)
        worksheet.merge_range('AF4:AF6', u'Бүртгэсэн огноо', format)
        worksheet.merge_range('AG4:AG6', u'Албан тушаалтны гарын үсэг', format)

        begin_date = DatabaseUtils.convert_date(self.report_begin_date.date())
        end_date = DatabaseUtils.convert_date(self.report_end_date.date())
        end_date = end_date + timedelta(days=1)
        row = 6
        col = 0
        row_number = 1
        c_status = 0
        try:
            values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
                join(CtContractApplicationRole.application_ref).\
                join(CtContract).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtContract.contract_date.between(begin_date, end_date)).all()
            if not self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex()) == -1:
                type = self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex())
                values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
                join(CtContractApplicationRole.application_ref).\
                join(CtContract).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtContract.contract_date.between(begin_date, end_date)).\
                filter(CtApplication.app_type == type).all()
            if not self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex()) == -1:
                type = self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex())
                values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
                join(CtContractApplicationRole.application_ref).\
                join(CtContract).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtContract.contract_date.between(begin_date, end_date)).\
                filter(CtApplication.approved_landuse == type).all()
            if not self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex()) == -1:
                type = self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex())
                values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
                join(CtContractApplicationRole.application_ref).\
                join(CtContract).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application).\
                join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id).\
                filter(CtContract.contract_date.between(begin_date, end_date)).\
                filter(BsPerson.type == type).all()
            if self.parcel_id.text():
                value_like = "%" + self.parcel_id.text() + "%"
                values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
                join(CtContractApplicationRole.application_ref).\
                join(CtContract).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application).\
                join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id).\
                filter(CtContract.contract_date.between(begin_date, end_date)).\
                filter(CtApplication.parcel.ilike(value_like)).all()
            if self.person_id.text():
                value_like = "%" + self.person_id.text() + "%"
                values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
                join(CtContractApplicationRole.application_ref).\
                join(CtContract).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application).\
                join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id).\
                filter(CtContract.contract_date.between(begin_date, end_date)).\
                filter(BsPerson.person_id.ilike(value_like)).all()

            count = len(values)
            self.progressBar.setMaximum(count)
            for value in values:

                khashaa = ''
                streetname = ''
                neighbourhood = ''
                landuse = ''
                middle_name = ''
                first_name = ''
                surname = ''
                person_address_a1 = '-'
                person_address_a2 = '-'
                person_address_a3 = '-'
                person_address_street_name = '-'
                person_address_khaskhaa = '-'
                extend_time = ''
                new_certificate_no = ''
                new_landuse_type = ''
                transfer_type = ''
                legal_surname = ''
                legal_name = ''
                legal_person_id = ''
                owner_change = ''
                price = ''
                person_name = ''
                person_id = ''
                contract_no = ''
                certificate_no = ''
                contract_time = ''
                app_remarks = ''
                a3_name = ''
                contract_begin = ''
                contract_end = ''
                contract_status = ''

                if value.CtApplication.approved_landuse != None:
                    landuse = value.CtApplication.approved_landuse_ref.description
                    landuse_code = value.CtApplication.approved_landuse_ref.code
                if value.CtApplication.parcel_ref.address_khashaa != None:
                    khashaa = value.CtApplication.parcel_ref.address_khashaa
                if value.CtApplication.parcel_ref.address_streetname != None:
                    streetname = value.CtApplication.parcel_ref.address_streetname
                if value.CtApplication.parcel_ref.address_neighbourhood != None:
                    neighbourhood = value.CtApplication.parcel_ref.address_neighbourhood
                if value.CtContract.contract_no != None:
                    contract_no = value.CtContract.contract_no
                if value.CtContract.certificate_no != None:
                    certificate_no = str(value.CtContract.certificate_no)
                if value.CtContract.contract_begin != None and value.CtContract.contract_end != None:
                    contract_time = str(value.CtContract.contract_end.year - value.CtContract.contract_begin.year)
                if value.CtApplication.remarks != None:
                    app_remarks = value.CtApplication.remarks

                app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == value.CtApplication.app_no).all()
                if value.CtApplication.app_type == 05 or value.CtApplication.app_type == 8 or value.CtApplication.app_type == 9 or value.CtApplication.app_type == 10 or value.CtApplication.app_type == 11:
                    app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == value.CtApplication.app_no)\
                                        .filter(CtApplicationPersonRole.main_applicant == True).all()
                elif value.CtApplication.app_type == 07 or value.CtApplication.app_type == 14:
                    app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == value.CtApplication.app_no)\
                                        .filter(CtApplicationPersonRole.role == 70).all()

                for person_app in app_person:
                    person_count = self.session.query(BsPerson).filter(BsPerson.person_id == person_app.person).count()
                    if person_count != 0:
                        person = self.session.query(BsPerson).filter(BsPerson.person_id == person_app.person).one()
                        a3_count = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).count()
                        if a3_count != 0:
                            a3 = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).one()
                            a3_name = a3.name
                        tax_zone_count = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).count()
                        if tax_zone_count == 1:
                            tax_zone = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).one()
                            tax_count = self.session.query(SetBaseTaxAndPrice).filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id).count()
                            if tax_count == 1:
                                tax = self.session.query(SetBaseTaxAndPrice).filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id).one()
                                price = str(float(tax.base_value_per_m2) * value.CtApplication.parcel_ref.area_m2)
                        if person.address_au_level3 != None:
                            person_a3 = self.session.query(AuLevel3).filter(AuLevel3.code == person.address_au_level3).one()
                            person_address_a3 = person_a3.name
                        if person.address_au_level2 != None:
                            person_a2 = self.session.query(AuLevel2).filter(AuLevel2.code == person.address_au_level2).one()
                            person_address_a2 = person_a2.name
                        if person.address_au_level1 != None:
                            person_a1 = self.session.query(AuLevel1).filter(AuLevel1.code == person.address_au_level1).one()
                            person_address_a1 = person_a1.name
                        if person.address_street_name != None:
                            person_address_street_name = person.address_street_name
                        if person.address_khaskhaa != None:
                            person_address_khaskhaa = person.address_khaskhaa

                        if person.type == 10 or person.type == 20 \
                            or person.type == 50:
                            if person.middle_name != None:
                                middle_name = person.middle_name
                            if person.first_name != None:
                                first_name = person.first_name
                            if person.name != None:
                                surname = person.name
                        if person.type == 30 or person.type == 40 \
                            or person.type == 60:
                            first_name = person.name

                        if value.CtApplication.app_type == 10:
                            extend_time = str(value.CtApplication.approved_duration)
                        if value.CtApplication.app_type == 12:
                            new_certificate_no = value.CtContract.certificate_no
                        if value.CtApplication.app_type == 9:
                            new_landuse_type = value.CtApplication.approved_landuse_ref.description
                        if value.CtApplication.app_type == 7:
                            transfer_count = self.session.query(CtApp15Ext).filter(CtApp15Ext.app_no == value.CtApplication.app_no).count()
                            if transfer_count == 1:
                                transfer = self.session.query(CtApp15Ext).filter(CtApp15Ext.app_no == value.CtApplication.app_no).one()
                                if transfer.transfer_type == 10:
                                    transfer_type = u'Х'
                                elif transfer.transfer_type == 20:
                                    transfer_type = u'Б'
                                elif transfer.transfer_type == 30:
                                    transfer_type = u'Ө'
                                elif transfer.transfer_type == 40:
                                    transfer_type = u'Д'
                            # decision_app = self.session.query(CtDec
                            # isionApplication).filter(CtDecisionApplication.application)

                        worksheet.write(row, col, row_number, format)
                        worksheet.write(row, col+1, value.CtApplication.parcel_ref.parcel_id, format)
                        worksheet.write(row, col+2, str(value.CtApplication.parcel_ref.area_m2), format)
                        worksheet.write(row, col+3, str(value.CtApplication.parcel_ref.area_m2/10000), format)
                        worksheet.write(row, col+4, price, format)
                        worksheet.write(row, col+5, landuse, format)
                        worksheet.write(row, col+6, a3_name, format)
                        worksheet.write(row, col+7, streetname, format)
                        worksheet.write(row, col+8, khashaa, format)
                        worksheet.write(row, col+9, neighbourhood, format)
                        worksheet.write(row, col+10, middle_name, format)
                        worksheet.write(row, col+11, surname, format)
                        worksheet.write(row, col+12, first_name, format)
                        worksheet.write(row, col+13, person.person_id, format)
                        worksheet.write(row, col+14, person_address_a1, format)
                        worksheet.write(row, col+15, person_address_a2, format)
                        worksheet.write(row, col+16, person_address_a3, format)
                        worksheet.write(row, col+17, person_address_street_name, format)
                        worksheet.write(row, col+18, person_address_khaskhaa, format)
                        worksheet.write(row, col+19, str(value.CtDecisionApplication.decision_ref.decision_date), format)
                        worksheet.write(row, col+20, value.CtDecisionApplication.decision, format)
                        worksheet.write(row, col+21, certificate_no, format)
                        worksheet.write(row, col+22, contract_no, format)
                        worksheet.write(row, col+23, contract_time, format)
                        worksheet.write(row, col+24, extend_time, format)
                        worksheet.write(row, col+25, str(new_certificate_no), format)
                        worksheet.write(row, col+26, new_landuse_type, format)
                        worksheet.write(row, col+27, transfer_type, format)
                        worksheet.write(row, col+28, '', format)
                        worksheet.write(row, col+29, '', format)
                        worksheet.write(row, col+30, app_remarks, format)
                        worksheet.write(row, col+31, str(value.CtContract.contract_date), format)
                        worksheet.write(row, col+32, u'_________', format)
                        row += 1
                        row_number += 1
                        value_p = self.progressBar.value() + 1
                        self.progressBar.setValue(value_p)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return
        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/" + restrictions + "-" + "book_for_land_possess.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __book_for_land_use(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/" + restrictions + "-" + "book_for_land_use.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 7)
        worksheet.set_column('D:D', 7)
        worksheet.set_column('E:E', 8)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 9)
        worksheet.set_column('H:H', 9)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 12)
        worksheet.set_column('K:K', 11)
        worksheet.set_column('L:L', 11)
        worksheet.set_column('M:M', 11)
        worksheet.set_column('N:N', 11)
        worksheet.set_column('O:O', 10)
        worksheet.set_column('P:P', 10)
        worksheet.set_column('Q:Q', 10)
        worksheet.set_column('R:R', 10)
        worksheet.set_column('S:S', 10)
        worksheet.set_column('T:T', 8)
        worksheet.set_column('U:U', 11)
        worksheet.set_column('V:V', 12)
        worksheet.set_column('W:W', 12)
        worksheet.set_column('X:X', 11)
        worksheet.set_column('Y:Y', 12)
        worksheet.set_column('Z:Z', 10)
        worksheet.set_column('AA:AA', 12)
        worksheet.set_column('AB:AB', 12)
        worksheet.set_column('AC:AC', 12)
        worksheet.set_column('AE:AE', 12)

        worksheet.set_row(3,25)
        worksheet.set_row(4,25)
        worksheet.set_row(5,50)
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

        worksheet.merge_range('D2:L2', u'Газар ашиглагчийн улсын бүртгэл',format_header)
        worksheet.merge_range('A4:A6', u'Д/д',format)
        worksheet.merge_range('B4:J4', u'Нэгж талбарын мэдээлэл', format)
        worksheet.merge_range('C5:D5', u'Газрын хэмжээ', format)
        worksheet.merge_range('G5:J5', u'Газрын байршлын нэр, хаяг', format)
        worksheet.merge_range('B5:B6', u'Нэгж талбарын дугаар', format)
        worksheet.write('C6',u'м2', format)
        worksheet.write('D6',u'га', format)
        worksheet.merge_range('E5:E6', u'Газрын үнэ /мян.төг/', format)
        worksheet.merge_range('F5:F6', u'Газрын зориулалт', format)
        worksheet.write('G6', u'Баг /хороо/', format)
        worksheet.write('H6', u'Гудамж /хороолол/', format)
        worksheet.write('I6', u'Байр /хашаа,хаалга/-ны дугаар', format)
        worksheet.write('J6', u'Байршшил', format)
        worksheet.merge_range('K4:S4', u'Газар ашиглагчийн мэдээлэл', format)
        worksheet.merge_range('K5:K6', u'Овог', format)
        worksheet.merge_range('L5:L6', u'Эцэг /эх/-ийн нэр', format)
        worksheet.merge_range('M5:M6', u'Нэр', format)
        worksheet.merge_range('N5:N6', u'Регистрийн дугаар', format)
        worksheet.merge_range('P5:S5', u'Байнгын хаяг', format)
        worksheet.write('O6', u'Аймаг /нийслэл/', format)
        worksheet.write('P6', u'Сум /дүүрэг/', format)
        worksheet.write('Q6', u'Баг /хороо/', format)
        worksheet.write('R6', u'Гудамж /хороолол/', format)
        worksheet.write('S6', u'Байр /хашаа, хаалга/-ны дугаар', format)
        worksheet.merge_range('T4:U4', u'Газар ашиглуулах эрх олгосон үндэслэл', format)
        worksheet.merge_range('T5:T6', u'Огноо', format)
        worksheet.merge_range('U5:U6', u'Захирамжийн дугаар', format)
        worksheet.merge_range('V4:X4', u'Гэрээ', format)
        worksheet.merge_range('V5:V6', u'Эрхийн гэрчилгээний дугаар', format)
        worksheet.merge_range('W5:W6', u'Гэрээний дугаар', format)
        worksheet.merge_range('X5:X6', u'Хугацаа', format)
        worksheet.merge_range('Y4:AE4', u'Гэрээ, гэрчилгээ, эрхийн өөрчлөлт, шилжилт', format)
        worksheet.merge_range('Y5:Y6', u'Гэрээ, гэрчилгээний хугацаа сунгах', format)
        worksheet.merge_range('Z5:Z6', u'Нөхөн авсан гэрчилгээний дугаар', format)
        worksheet.merge_range('AA5:AA6', u'Өөрчлөгдөн газар ашиглалтын зориулалт', format)
        worksheet.merge_range('AB5:AB6', u'Ашиглагчийн эрх шилжсэн тохиолдолд бүртгэсэн дэвтэр, хуудасны дугаар', format)
        worksheet.merge_range('AC5:AC6', u'Нэгж талбарын хэмжээнд өөрчлөлт орсон тохиолдолд шинээр үүссэн нэгж талбарын дугаар', format)
        worksheet.merge_range('AD5:AE5', u'Ашиглагчийн эрх хүчингүй болсон', format)
        worksheet.write('AD6', u'Огноо', format)
        worksheet.write('AE6', u'Захирамж шийдвэрийн дугаар', format)
        worksheet.merge_range('AF4:AF6', u'Тайлбар', format)
        worksheet.merge_range('AG4:AG6', u'Бүртгэсэн огноо', format)
        worksheet.merge_range('AH4:AH6', u'Албан тушаалтны гарын үсэг', format)

        begin_date = DatabaseUtils.convert_date(self.report_begin_date.date())
        end_date = DatabaseUtils.convert_date(self.report_end_date.date())
        row = 6
        col = 0
        row_number = 1
        c_status = 0
        try:
            values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
                join(CtContractApplicationRole.application_ref).\
                join(CtContract).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtContract.contract_date.between(begin_date, end_date)).\
                filter(CtApplication.app_type == 6).all()
            if not self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex()) == -1:
                type = self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex())
                values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
                join(CtContractApplicationRole.application_ref).\
                join(CtContract).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtContract.contract_date.between(begin_date, end_date)).\
                filter(CtApplication.app_type == type).\
                filter(CtApplication.app_type == 6).all()
            if not self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex()) == -1:
                type = self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex())
                values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
                join(CtContractApplicationRole.application_ref).\
                join(CtContract).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtContract.contract_date.between(begin_date, end_date)).\
                filter(CtApplication.approved_landuse == type).\
                filter(CtApplication.app_type == 6).all()
            if not self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex()) == -1:
                type = self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex())
                values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
                join(CtContractApplicationRole.application_ref).\
                join(CtContract).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application).\
                join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id).\
                filter(CtContract.contract_date.between(begin_date, end_date)).\
                filter(BsPerson.type == type).\
                filter(CtApplication.app_type == 6).all()
            if self.parcel_id.text():
                value_like = "%" + self.parcel_id.text() + "%"
                values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
                join(CtContractApplicationRole.application_ref).\
                join(CtContract).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application).\
                join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id).\
                filter(CtContract.contract_date.between(begin_date, end_date)).\
                filter(CtApplication.parcel.ilike(value_like)).\
                filter(CtApplication.app_type == 6).all()
            if self.person_id.text():
                value_like = "%" + self.person_id.text() + "%"
                values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
                join(CtContractApplicationRole.application_ref).\
                join(CtContract).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application).\
                join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id).\
                filter(CtContract.contract_date.between(begin_date, end_date)).\
                filter(BsPerson.person_id.ilike(value_like)).\
                filter(CtApplication.app_type == 6).all()

            count = len(values)
            self.progressBar.setMaximum(count)
            for value in values:

                khashaa = ''
                streetname = ''
                neighbourhood = ''
                landuse = ''
                middle_name = ''
                first_name = ''
                surname = ''
                person_address_a1 = '-'
                person_address_a2 = '-'
                person_address_a3 = '-'
                person_address_street_name = '-'
                person_address_khaskhaa = '-'
                extend_time = ''
                new_certificate_no = ''
                new_landuse_type = ''
                transfer_type = ''
                a3_name = ''
                legal_surname = ''
                legal_name = ''
                legal_person_id = ''
                owner_change = ''
                price = ''
                person_name = ''
                person_id = ''
                contract_no = ''
                certificate_no = ''
                contract_time = ''
                app_remarks = ''
                contract_begin = ''
                contract_end = ''
                contract_status = ''

                if value.CtApplication.approved_landuse != None:
                    landuse = value.CtApplication.approved_landuse_ref.description
                    landuse_code = value.CtApplication.approved_landuse_ref.code
                if value.CtApplication.parcel_ref.address_khashaa != None:
                    khashaa = value.CtApplication.parcel_ref.address_khashaa
                if value.CtApplication.parcel_ref.address_streetname != None:
                    streetname = value.CtApplication.parcel_ref.address_streetname
                if value.CtApplication.parcel_ref.address_neighbourhood != None:
                    neighbourhood = value.CtApplication.parcel_ref.address_neighbourhood
                if value.CtContract.contract_no != None:
                    contract_no = value.CtContract.contract_no
                if value.CtContract.certificate_no != None:
                    certificate_no = str(value.CtContract.certificate_no)
                if value.CtContract.contract_begin != None and value.CtContract.contract_end != None:
                    contract_time = str(value.CtContract.contract_end.year - value.CtContract.contract_begin.year)
                if value.CtApplication.remarks != None:
                    app_remarks = value.CtApplication.remarks

                app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == value.CtApplication.app_no).all()
                for person_app in app_person:
                    person_count = self.session.query(BsPerson).filter(BsPerson.person_id == person_app.person).count()
                    if person_count != 0:
                        person = self.session.query(BsPerson).filter(BsPerson.person_id == person_app.person).one()
                        a3_count = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).count()
                        if a3_count != 0:
                            a3 = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).one()
                            a3_name = a3.name
                        tax_zone_count = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).count()
                        if tax_zone_count == 1:
                            tax_zone = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).one()
                            tax_count = self.session.query(SetBaseTaxAndPrice).filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id).count()
                            if tax_count == 1:
                                tax = self.session.query(SetBaseTaxAndPrice).filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id).one()
                                price = str(float(tax.base_value_per_m2) * value.CtApplication.parcel_ref.area_m2)
                        if person.address_au_level3 != None:
                            person_a3 = self.session.query(AuLevel3).filter(AuLevel3.code == person.address_au_level3).one()
                            person_address_a3 = person_a3.name
                        if person.address_au_level2 != None:
                            person_a2 = self.session.query(AuLevel2).filter(AuLevel2.code == person.address_au_level2).one()
                            person_address_a2 = person_a2.name
                        if person.address_au_level1 != None:
                            person_a1 = self.session.query(AuLevel1).filter(AuLevel1.code == person.address_au_level1).one()
                            person_address_a1 = person_a1.name
                        if person.address_street_name != None:
                            person_address_street_name = person.address_street_name
                        if person.address_khaskhaa != None:
                            person_address_khaskhaa = person.address_khaskhaa

                        if person.type == 10 or person.type == 20 \
                            or person.person_ref.type == 50:
                            if person.person_ref.middle_name != None:
                                middle_name = person.person_ref.middle_name
                            if person.person_ref.first_name != None:
                                first_name = person.person_ref.first_name
                            if person.person_ref.name != None:
                                surname = person.person_ref.name
                        if person.type == 30 or person.type == 40 \
                            or person.type == 60:
                            first_name = person.name

                        if value.CtApplication.app_type == 10:
                            extend_time = str(value.CtApplication.approved_duration)
                        if value.CtApplication.app_type == 12:
                            new_certificate_no = value.CtContract.certificate_no
                        if value.CtApplication.app_type == 9:
                            new_landuse_type = value.CtApplication.approved_landuse_ref.description
                        if value.CtApplication.app_type == 7:
                            transfer_count = self.session.query(CtApp15Ext).filter(CtApp15Ext.app_no == value.CtApplication.app_no).count()
                            if transfer_count == 1:
                                transfer = self.session.query(CtApp15Ext).filter(CtApp15Ext.app_no == value.CtApplication.app_no).one()
                                if transfer.transfer_type == 10:
                                    transfer_type = u'Х'
                                elif transfer.transfer_type == 20:
                                    transfer_type = u'Б'
                                elif transfer.transfer_type == 30:
                                    transfer_type = u'Ө'
                                elif transfer.transfer_type == 40:
                                    transfer_type = u'Д'
                        if person_app.main_applicant == True:
                            worksheet.write(row, col, row_number, format)
                            worksheet.write(row, col+1, value.CtApplication.parcel_ref.parcel_id, format)
                            worksheet.write(row, col+2, str(value.CtApplication.parcel_ref.area_m2), format)
                            worksheet.write(row, col+3, str(value.CtApplication.parcel_ref.area_m2/10000), format)
                            worksheet.write(row, col+4, price, format)
                            worksheet.write(row, col+5, landuse, format)
                            worksheet.write(row, col+6, a3_name, format)
                            worksheet.write(row, col+7, streetname, format)
                            worksheet.write(row, col+8, khashaa, format)
                            worksheet.write(row, col+9, neighbourhood, format)
                            worksheet.write(row, col+10, middle_name, format)
                            worksheet.write(row, col+11, surname, format)
                            worksheet.write(row, col+12, first_name, format)
                            worksheet.write(row, col+13, person.person_id, format)
                            worksheet.write(row, col+14, person_address_a1, format)
                            worksheet.write(row, col+15, person_address_a2, format)
                            worksheet.write(row, col+16, person_address_a3, format)
                            worksheet.write(row, col+17, person_address_street_name, format)
                            worksheet.write(row, col+18, person_address_khaskhaa, format)
                            worksheet.write(row, col+19, str(value.CtDecisionApplication.decision_ref.decision_date), format)
                            worksheet.write(row, col+20, value.CtDecisionApplication.decision, format)
                            worksheet.write(row, col+21, certificate_no, format)
                            worksheet.write(row, col+22, contract_no, format)
                            worksheet.write(row, col+23, contract_time, format)
                            worksheet.write(row, col+24, extend_time, format)
                            worksheet.write(row, col+25, str(new_certificate_no), format)
                            worksheet.write(row, col+26, new_landuse_type, format)
                            worksheet.write(row, col+27, transfer_type, format)
                            worksheet.write(row, col+28, '', format)
                            worksheet.write(row, col+29, '', format)
                            worksheet.write(row, col+30, '', format)
                            worksheet.write(row, col+31, app_remarks, format)
                            worksheet.write(row, col+32, str(value.CtContract.contract_date), format)
                            worksheet.write(row, col+33, u'_________', format)
                            row += 1
                            row_number += 1
                            value_p = self.progressBar.value() + 1
                            self.progressBar.setValue(value_p)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/" + restrictions + "-" + "book_for_land_use.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __land_tax(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/" + restrictions + "-" + "land_tax.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 7)
        worksheet.set_column('D:D', 7)
        worksheet.set_column('E:E', 8)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 9)
        worksheet.set_column('H:H', 9)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 12)
        worksheet.set_column('K:K', 11)
        worksheet.set_column('L:L', 11)
        worksheet.set_column('M:M', 11)
        worksheet.set_column('N:N', 11)
        worksheet.set_column('O:O', 10)
        worksheet.set_column('P:P', 10)
        worksheet.set_column('Q:Q', 10)
        worksheet.set_column('R:R', 10)
        worksheet.set_column('S:S', 10)
        worksheet.set_column('T:T', 8)
        worksheet.set_column('U:U', 11)
        worksheet.set_column('V:V', 12)
        worksheet.set_column('W:W', 12)
        worksheet.set_column('X:X', 11)
        worksheet.set_column('Y:Y', 12)
        worksheet.set_column('Z:Z', 10)
        worksheet.set_column('AA:AA', 12)
        worksheet.set_column('AB:AB', 12)
        worksheet.set_column('AC:AC', 12)
        worksheet.set_column('AE:AE', 12)

        worksheet.set_row(3,25)
        worksheet.set_row(4,25)
        worksheet.set_row(5,50)
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

        worksheet.merge_range('D2:L2', u'Газар албан татвар ноогдуулалтын мэдээ',format_header)
        worksheet.merge_range('A4:A6', u'Д/д',format)
        worksheet.merge_range('B4:J4', u'Нэгж талбарын мэдээлэл', format)
        worksheet.merge_range('C5:D5', u'Газрын хэмжээ', format)
        worksheet.merge_range('G5:J5', u'Газрын байршлын нэр, хаяг', format)
        worksheet.merge_range('B5:B6', u'Нэгж талбарын дугаар', format)
        worksheet.write('C6',u'м2', format)
        worksheet.write('D6',u'га', format)
        worksheet.merge_range('E5:E6', u'Газрын үнэ /мян.төг/', format)
        worksheet.merge_range('F5:F6', u'Газрын зориулалт', format)
        worksheet.write('G6', u'Баг /хороо/', format)
        worksheet.write('H6', u'Гудамж /хороолол/', format)
        worksheet.write('I6', u'Байр /хашаа,хаалга/-ны дугаар', format)
        worksheet.write('J6', u'Байршшил', format)
        worksheet.merge_range('K4:S4', u'Газар ашиглагчийн мэдээлэл', format)
        worksheet.merge_range('K5:K6', u'Овог', format)
        worksheet.merge_range('L5:L6', u'Эцэг /эх/-ийн нэр', format)
        worksheet.merge_range('M5:M6', u'Нэр', format)
        worksheet.merge_range('N5:N6', u'Регистрийн дугаар', format)
        worksheet.merge_range('P5:S5', u'Байнгын хаяг', format)
        worksheet.write('O6', u'Аймаг /нийслэл/', format)
        worksheet.write('P6', u'Сум /дүүрэг/', format)
        worksheet.write('Q6', u'Баг /хороо/', format)
        worksheet.write('R6', u'Гудамж /хороолол/', format)
        worksheet.write('S6', u'Байр /хашаа, хаалга/-ны дугаар', format)
        worksheet.merge_range('T4:T6', u'Ноогдуулах татвар/төг/', format)
        worksheet.merge_range('U4:U6', u'Татварын чөлөөлөт', format)
        worksheet.merge_range('V4:W4', u'Татварын хөнгөлөлт', format)
        worksheet.merge_range('V5:V6', u'Хөнгөлөлтийн хувь', format)
        worksheet.merge_range('W5:W6', u'Хөнгөлөлтийн хэмжээ/төг/', format)
        worksheet.merge_range('X4:X6', u'Тайлант онд ногдуулсан жилийн татвар /төг/', format)
        worksheet.merge_range('Y4:Y6', u'Урьд оны үлдэгдэл илүү', format)
        worksheet.merge_range('Z4:Z6', u'Урьд оны үлдэгдэл  дутуу', format)
        worksheet.merge_range('AA4:AA6', u'Тайлант онд нийт төлбөл зохих татварын дүн', format)


        begin_date = DatabaseUtils.convert_date(self.report_begin_date.date())
        end_date = DatabaseUtils.convert_date(self.report_end_date.date())
        end_date = end_date + timedelta(days=1)
        row = 6
        col = 0
        row_number = 1
        c_status = 0
        try:
            values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).all()
            if not self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex()) == -1:
                type = self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex())
                values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).\
                filter(CtApplication.app_type == type).all()
            if not self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex()) == -1:
                type = self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex())
                values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).\
                filter(CtApplication.approved_landuse == type).all()
            if not self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex()) == -1:
                type = self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex())
                values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application).\
                join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).\
                filter(BsPerson.type == type).all()

            count = len(values)
            self.progressBar.setMaximum(count)
            for value in values:
                khashaa = ''
                streetname = ''
                neighbourhood = ''
                landuse = ''
                middle_name = ''
                first_name = ''
                surname = ''
                person_address_a1 = '-'
                person_address_a2 = '-'
                person_address_a3 = '-'
                person_address_street_name = '-'
                person_address_khaskhaa = '-'
                price = 0
                base_tax = 0
                bas_tax_amount = 0
                subsidized_tax_rate = 0
                base_tax_rate = 0
                subsidized_tax_amount = 0
                tax_to_pay_for_current_year = 0
                paid_for_current_year = 0
                surplus = 0
                partial = 0
                tax_left_to_pay = 0
                tax_right_to_pay = 0
                tax_pay = 0
                a3_name = ''
                if value.CtApplication.approved_landuse != None:
                    landuse = value.CtApplication.approved_landuse_ref.description
                    landuse_code = value.CtApplication.approved_landuse_ref.code
                if value.CtApplication.parcel_ref != None:
                    if value.CtApplication.parcel_ref.address_khashaa != None:
                        khashaa = value.CtApplication.parcel_ref.address_khashaa
                    if value.CtApplication.parcel_ref.address_streetname != None:
                        streetname = value.CtApplication.parcel_ref.address_streetname
                    if value.CtApplication.parcel_ref.address_neighbourhood != None:
                        neighbourhood = value.CtApplication.parcel_ref.address_neighbourhood

                    app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == value.CtApplication.app_no).all()
                    for person_app in app_person:
                        person_count = self.session.query(BsPerson).filter(BsPerson.person_id == person_app.person).count()
                        if person_count != 0:
                            person = self.session.query(BsPerson).filter(BsPerson.person_id == person_app.person).one()
                            a3_count = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).count()
                            if a3_count != 0:
                                a3 = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).one()
                                a3_name = a3.name
                            tax_zone_count = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).count()
                            if str(value.CtApplication.parcel_ref.landuse)[:1] == '1':
                                tax_zone_count = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).\
                                    filter(or_(SetTaxAndPriceZone.zone_no == 50, SetTaxAndPriceZone.zone_no == 60, SetTaxAndPriceZone.zone_no == 70, SetTaxAndPriceZone.zone_no == 80)).count()
                            else:
                                tax_zone_count = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).\
                                    filter(and_(SetTaxAndPriceZone.zone_no != 50, SetTaxAndPriceZone.zone_no != 60, SetTaxAndPriceZone.zone_no != 70, SetTaxAndPriceZone.zone_no != 80)).count()
                            if tax_zone_count == 1:
                                if str(value.CtApplication.parcel_ref.landuse)[:1] == '1':
                                    tax_zone = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).\
                                        filter(or_(SetTaxAndPriceZone.zone_no == 50, SetTaxAndPriceZone.zone_no == 60, SetTaxAndPriceZone.zone_no == 70, SetTaxAndPriceZone.zone_no == 80)).one()
                                else:
                                    tax_zone = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).\
                                        filter(and_(SetTaxAndPriceZone.zone_no != 50, SetTaxAndPriceZone.zone_no != 60, SetTaxAndPriceZone.zone_no != 70, SetTaxAndPriceZone.zone_no != 80)).one()
                                tax_count = self.session.query(SetBaseTaxAndPrice).\
                                    filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id).\
                                    filter(SetBaseTaxAndPrice.landuse == value.CtApplication.approved_landuse).count()
                                if tax_count == 1:

                                    tax = self.session.query(SetBaseTaxAndPrice).\
                                        filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id).\
                                        filter(SetBaseTaxAndPrice.landuse == value.CtApplication.approved_landuse).one()
                                    price = float(tax.base_value_per_m2) * value.CtApplication.parcel_ref.area_m2
                                    base_tax = price*float(tax.base_tax_rate)/100

                                    subsidized_tax_rate = float(tax.subsidized_tax_rate)
                                    subsidized_tax_amount = base_tax*subsidized_tax_rate/100
                                    bas_tax_amount = base_tax - subsidized_tax_amount
                                    base_tax_rate = tax.base_tax_rate
                                    payment_year = self.year_sbox.value()
                                    tax_c = self.session.query(CtTaxAndPrice).filter(CtTaxAndPrice.person == person.person_id)\
                                                                            .filter(CtTaxAndPrice.record == value.CtOwnershipRecord.record_no).count()
                                    if tax_c == 1:
                                        tax = self.session.query(CtTaxAndPrice).filter(CtTaxAndPrice.person == person.person_id)\
                                                                            .filter(CtTaxAndPrice.record == value.CtOwnershipRecord.record_no).one()

                                        tax_to_pay_for_current_year = \
                                            self.__tax_to_pay_per_period(tax, date(payment_year, 1, 1), date(payment_year+1, 1, 1))

                                        paid_for_current_year = self.session.query(func.sum(CtTaxAndPricePayment.amount_paid))\
                                            .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
                                            .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()

                                        if paid_for_current_year is None:
                                            paid_for_current_year = 0

                                        partial = self.__sum_year_amount_paid(tax, value.CtOwnershipRecord)
                                        surplus = self.__surplus_from_previous_years(tax, value.CtOwnershipRecord)
                                        if surplus < 0:
                                            surplus = 0

                                        tax_left_to_pay = tax_to_pay_for_current_year - (paid_for_current_year + surplus)

                                        tax_pay = tax_to_pay_for_current_year - surplus + partial

                            if person.address_au_level3 != None:
                                person_a3 = self.session.query(AuLevel3).filter(AuLevel3.code == person.address_au_level3).one()
                                person_address_a3 = person_a3.name
                            if person.address_au_level2 != None:
                                person_a2 = self.session.query(AuLevel2).filter(AuLevel2.code == person.address_au_level2).one()
                                person_address_a2 = person_a2.name
                            if person.address_au_level1 != None:
                                person_a1 = self.session.query(AuLevel1).filter(AuLevel1.code == person.address_au_level1).one()
                                person_address_a1 = person_a1.name
                            if person.address_street_name != None:
                                person_address_street_name = person.address_street_name
                            if person.address_khaskhaa != None:
                                person_address_khaskhaa = person.address_khaskhaa

                            if person.type == 10 or person.type == 20 \
                                or person.type == 50:
                                if person.middle_name != None:
                                    middle_name = person.middle_name
                                if person.first_name != None:
                                    first_name = person.first_name
                                if person.name != None:
                                    surname = person.name
                            if person.type == 30 or person.type == 40 \
                                or person.type == 60:
                                first_name = person.name

                            if person_app.main_applicant == True:
                                worksheet.write(row, col, row_number, format)
                                worksheet.write(row, col+1, value.CtApplication.parcel_ref.parcel_id, format)
                                worksheet.write(row, col+2, str(value.CtApplication.parcel_ref.area_m2), format)
                                worksheet.write(row, col+3, str(value.CtApplication.parcel_ref.area_m2/10000), format)
                                worksheet.write(row, col+4, str(price), format)
                                worksheet.write(row, col+5, landuse, format)
                                worksheet.write(row, col+6, a3_name, format)
                                worksheet.write(row, col+7, streetname, format)
                                worksheet.write(row, col+8, khashaa, format)
                                worksheet.write(row, col+9, neighbourhood, format)
                                worksheet.write(row, col+10, middle_name, format)
                                worksheet.write(row, col+11, surname, format)
                                worksheet.write(row, col+12, first_name, format)
                                worksheet.write(row, col+13, person.person_id, format)
                                worksheet.write(row, col+14, person_address_a1, format)
                                worksheet.write(row, col+15, person_address_a2, format)
                                worksheet.write(row, col+16, person_address_a3, format)
                                worksheet.write(row, col+17, person_address_street_name, format)
                                worksheet.write(row, col+18, person_address_khaskhaa, format)
                                worksheet.write(row, col+19, str(base_tax), format)
                                worksheet.write(row, col+20, str(base_tax_rate), format)
                                worksheet.write(row, col+21, str(subsidized_tax_rate), format)
                                worksheet.write(row, col+22, str(subsidized_tax_amount), format)
                                worksheet.write(row, col+23, str(tax_to_pay_for_current_year), format)
                                worksheet.write(row, col+24, str(surplus), format)
                                worksheet.write(row, col+25, str(partial), format)
                                worksheet.write(row, col+26, str(tax_pay), format)

                                row += 1
                                row_number += 1
                                value_p = self.progressBar.value() + 1
                                self.progressBar.setValue(value_p)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/" + restrictions + "-" + "land_tax.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __tax_to_pay_per_period(self, tax, period_begin, period_end):

        # Intersect record duration with payment period
        sql = "select lower(daterange(record_begin, 'infinity', '[)') * daterange(:from, :to, '[)'))," \
              " upper(daterange(record_begin, 'infinity', '[)') * daterange(:from, :to, '[)')) " \
              "from ct_ownership_record where record_no = :record_no"

        result = self.session.execute(sql, {'from': period_begin,
                                            'to': period_end,
                                            'record_no': tax.record})
        for row in result:
            effective_begin = row[0]
            effective_end = row[1]

        if effective_begin is None and effective_end is None:
            return 0

        # Intersect the effective payment period with the archived taxes
        sql = "select upper(daterange(valid_from, valid_till, '[)') * daterange(:begin, :end, '[)')) - "\
                 "lower(daterange(valid_from, valid_till, '[)') * daterange(:begin, :end, '[)')) as days, "\
                 "land_tax from ct_archived_tax_and_price where record = :record and person = :person"

        result = self.session.execute(sql, {'begin': effective_begin,
                                            'end': effective_end,
                                            'record': tax.record,
                                            'person': tax.person})
        tax_for_period = 0
        total_days = 0

        for row in result:
            days = row[0]
            if days is None:
                continue
            annual_tax = row[1]
            adjusted_tax = (annual_tax / 365) * days
            tax_for_period += adjusted_tax
            total_days += days

        effective_days = (effective_end-effective_begin).days

        if effective_days - total_days > 0:
            tax_for_period += (effective_days-total_days) * tax.land_tax / 365

        return int(round(tax_for_period))

    def __sum_year_amount_paid_fee(self, fee, contract):

        year_to_pay_for = self.year_sbox.value()
        paid_year = 0
        surplus = 0
        sum_amount_paid = 0
        sum_land_fee = 0
        for payment_year in range(contract.contract_begin.year, year_to_pay_for):

            tax_to_pay_for_current_year = \
                self.__fee_to_pay_per_period(fee, date(payment_year, 1, 1), date(payment_year+1, 1, 1))

            amount_paid = self.session.query(func.sum(CtFeePayment.amount_paid))\
                .filter(CtFeePayment.contract == fee.contract).filter(CtFeePayment.person == fee.person)\
                .filter(CtFeePayment.year_paid_for == payment_year).scalar()
            if amount_paid == None:
                amount_paid = 0
            sum_amount_paid = sum_amount_paid + amount_paid
            sum_land_fee = sum_land_fee + tax_to_pay_for_current_year
        surplus = sum_land_fee - sum_amount_paid
        return surplus

    def __sum_year_amount_paid(self, tax, record):

        year_to_pay_for = self.year_sbox.value()
        paid_year = 0
        surplus = 0
        sum_amount_paid = 0
        sum_land_tax = 0
        for payment_year in range(record.record_begin.year, year_to_pay_for):

            tax_to_pay_for_current_year = \
                self.__tax_to_pay_per_period(tax, date(payment_year, 1, 1), date(payment_year+1, 1, 1))

            amount_paid = self.session.query(func.sum(CtTaxAndPricePayment.amount_paid))\
                .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
                .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()
            if amount_paid == None:
                amount_paid = 0
            sum_amount_paid = sum_amount_paid + amount_paid
            sum_land_tax = sum_land_tax + tax_to_pay_for_current_year
        surplus = sum_land_tax - sum_amount_paid
        return surplus

    def __surplus_from_previous_years(self, tax, record):

        year_to_pay_for = self.year_sbox.value()

        surplus_last_year = 0
        for payment_year in range(record.record_begin.year, year_to_pay_for):

            amount_paid = self.session.query(func.sum(CtTaxAndPricePayment.amount_paid))\
                .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
                .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()
            if amount_paid is None:
                amount_paid = 0

            tax_to_pay = self.__tax_to_pay_per_period(tax, date(payment_year, 1, 1), date(payment_year+1, 1, 1))
            if (amount_paid + surplus_last_year) - tax_to_pay > 0:
                surplus_last_year = (amount_paid + surplus_last_year) - tax_to_pay
            else:
                surplus_last_year = 0

        return surplus_last_year

    def __partial_from_previous_years(self, tax, record):

        year_to_pay_for = self.year_sbox.value()
        partial_last_year = 0

        for payment_year in range(record.record_begin.year, year_to_pay_for):

            amount_paid = self.session.query(func.sum(CtTaxAndPricePayment.amount_paid))\
                .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
                .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()
            if amount_paid is None:
                amount_paid = 0

            tax_to_pay = self.__tax_to_pay_per_period(tax, date(payment_year, 1, 1), date(payment_year+1, 1, 1))
            if tax_to_pay - (amount_paid + partial_last_year) > 0:
                partial_last_year = tax_to_pay - (amount_paid + partial_last_year)
            else:
                partial_last_year = 0

        return partial_last_year

    def __tax_to_pay_per_period(self, tax, period_begin, period_end):

        # Intersect record duration with payment period
        sql = "select lower(daterange(record_begin, 'infinity', '[)') * daterange(:from, :to, '[)'))," \
              " upper(daterange(record_begin, 'infinity', '[)') * daterange(:from, :to, '[)')) " \
              "from ct_ownership_record where record_no = :record_no"

        result = self.session.execute(sql, {'from': period_begin,
                                            'to': period_end,
                                            'record_no': tax.record})
        for row in result:
            effective_begin = row[0]
            effective_end = row[1]

        if effective_begin is None and effective_end is None:
            return 0

        # Intersect the effective payment period with the archived taxes
        sql = "select upper(daterange(valid_from, valid_till, '[)') * daterange(:begin, :end, '[)')) - "\
                 "lower(daterange(valid_from, valid_till, '[)') * daterange(:begin, :end, '[)')) as days, "\
                 "land_tax from ct_archived_tax_and_price where record = :record and person = :person"

        result = self.session.execute(sql, {'begin': effective_begin,
                                            'end': effective_end,
                                            'record': tax.record,
                                            'person': tax.person})
        tax_for_period = 0
        total_days = 0

        for row in result:
            days = row[0]
            if days is None:
                continue
            annual_tax = row[1]
            adjusted_tax = (annual_tax / 365) * days
            tax_for_period += adjusted_tax
            total_days += days

        effective_days = (effective_end-effective_begin).days

        if effective_days - total_days > 0:
            tax_for_period += (effective_days-total_days) * tax.land_tax / 365

        return int(round(tax_for_period))

    def __land_tax_paid(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/" + restrictions + "-" + "land_taxation.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 7)
        worksheet.set_column('D:D', 7)
        worksheet.set_column('E:E', 8)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 9)
        worksheet.set_column('H:H', 9)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 12)
        worksheet.set_column('K:K', 11)
        worksheet.set_column('L:L', 11)
        worksheet.set_column('M:M', 11)
        worksheet.set_column('N:N', 11)
        worksheet.set_column('O:O', 10)
        worksheet.set_column('P:P', 10)
        worksheet.set_column('Q:Q', 10)
        worksheet.set_column('R:R', 10)
        worksheet.set_column('S:S', 10)
        worksheet.set_column('T:T', 8)
        worksheet.set_column('U:U', 8)
        worksheet.set_column('V:V', 12)
        worksheet.set_column('W:W', 12)
        worksheet.set_column('X:X', 12)
        worksheet.set_column('Y:Y', 12)
        worksheet.set_column('Z:Z', 12)
        worksheet.set_column('AA:AA', 12)
        worksheet.set_column('AB:AB', 12)
        worksheet.set_column('AC:AC', 12)
        worksheet.set_column('AE:AE', 12)

        worksheet.set_row(3,25)
        worksheet.set_row(4,25)
        worksheet.set_row(5,50)
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

        worksheet.merge_range('D2:L2', u'Газар албан татвар ноогдуулалтын мэдээ',format_header)
        worksheet.merge_range('A4:A6', u'Д/д',format)
        worksheet.merge_range('B4:J4', u'Нэгж талбарын мэдээлэл', format)
        worksheet.merge_range('C5:D5', u'Газрын хэмжээ', format)
        worksheet.merge_range('G5:J5', u'Газрын байршлын нэр, хаяг', format)
        worksheet.merge_range('B5:B6', u'Нэгж талбарын дугаар', format)
        worksheet.write('C6',u'м2', format)
        worksheet.write('D6',u'га', format)
        worksheet.merge_range('E5:E6', u'Газрын үнэ /мян.төг/', format)
        worksheet.merge_range('F5:F6', u'Газрын зориулалт', format)
        worksheet.write('G6', u'Баг /хороо/', format)
        worksheet.write('H6', u'Гудамж /хороолол/', format)
        worksheet.write('I6', u'Байр /хашаа,хаалга/-ны дугаар', format)
        worksheet.write('J6', u'Байршшил', format)
        worksheet.merge_range('K4:S4', u'Газар ашиглагчийн мэдээлэл', format)
        worksheet.merge_range('K5:K6', u'Овог', format)
        worksheet.merge_range('L5:L6', u'Эцэг /эх/-ийн нэр', format)
        worksheet.merge_range('M5:M6', u'Нэр', format)
        worksheet.merge_range('N5:N6', u'Регистрийн дугаар', format)
        worksheet.merge_range('P5:S5', u'Байнгын хаяг', format)
        worksheet.write('O6', u'Аймаг /нийслэл/', format)
        worksheet.write('P6', u'Сум /дүүрэг/', format)
        worksheet.write('Q6', u'Баг /хороо/', format)
        worksheet.write('R6', u'Гудамж /хороолол/', format)
        worksheet.write('S6', u'Байр /хашаа, хаалга/-ны дугаар', format)
        worksheet.merge_range('T4:T6', u'Урьд оны үлдэгдэл илүү', format)
        worksheet.merge_range('U4:U6', u'Урьд оны үлдэгдэл дутуу', format)
        worksheet.merge_range('V4:V6', u'Тайлант онд ноогдуулсан жилийн татвар/төг/', format)
        worksheet.merge_range('W4:X4', u'Хяналтаар ноогдуулсан', format)
        worksheet.merge_range('W5:W6', u'Нөхөн төлбөр', format)
        worksheet.merge_range('X5:X6', u'Хүү торгууль', format)
        worksheet.merge_range('Y4:Y6', u'Тайлант онд нийт төлбөл зохих татварын дүн /төг/', format)
        worksheet.merge_range('Z4:AC4', u'Тайлант онд төлсөн /төг/', format)
        worksheet.merge_range('Z5:Z6', u'Урьд оны дутуу төлөлтөөс', format)
        worksheet.merge_range('AA5:AA6', u'Тайлангаар ноогдуулснаас', format)
        worksheet.merge_range('AB5:AB6', u'Хүү торгууль үлдэгдэл', format)
        worksheet.merge_range('AC5:AC6', u'Бүгд дүн', format)
        worksheet.merge_range('AD4:AD6', u'Тайлант оны эцэст илүү дутуу төлөлт', format)


        begin_date = DatabaseUtils.convert_date(self.report_begin_date.date())
        end_date = DatabaseUtils.convert_date(self.report_end_date.date())
        end_date = end_date + timedelta(days=1)
        row = 6
        col = 0
        row_number = 1
        c_status = 0
        try:
            values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).all()
            if not self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex()) == -1:
                type = self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex())
                values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).\
                filter(CtApplication.app_type == type).all()
            if not self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex()) == -1:
                type = self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex())
                values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).\
                filter(CtApplication.approved_landuse == type).all()
            if not self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex()) == -1:
                type = self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex())
                values = self.session.query(CtApplication,CtOwnershipRecord,CtDecisionApplication).\
                join(CtRecordApplicationRole.application_ref).\
                join(CtOwnershipRecord).\
                join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
                join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application).\
                join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id).\
                filter(CtOwnershipRecord.record_date.between(begin_date, end_date)).\
                filter(BsPerson.type == type).all()

            count = len(values)
            self.progressBar.setMaximum(count)
            for value in values:
                khashaa = ''
                streetname = ''
                neighbourhood = ''
                landuse = ''
                middle_name = ''
                first_name = ''
                surname = ''
                person_address_a1 = '-'
                person_address_a2 = '-'
                person_address_a3 = '-'
                person_address_street_name = '-'
                person_address_khaskhaa = '-'
                price = 0
                base_tax = 0
                bas_tax_amount = 0
                subsidized_tax_rate = 0
                base_tax_rate = 0
                subsidized_tax_amount = 0
                tax_to_pay_for_current_year = 0
                paid_for_current_year = 0
                surplus = 0
                partial = 0
                paid_difference = 0
                potential_fine_for_current_year = 0
                surplus_and_partial = 0
                tax_left_to_pay = 0
                tax_right_to_pay = 0
                a3_name = ''
                tax_pay = 0
                if value.CtApplication.approved_landuse != None:
                    landuse = value.CtApplication.approved_landuse_ref.description
                    landuse_code = value.CtApplication.approved_landuse_ref.code
                if value.CtApplication.parcel and value.CtApplication.parcel_ref:
                    if value.CtApplication.parcel_ref.address_khashaa != None:
                        khashaa = value.CtApplication.parcel_ref.address_khashaa
                    if value.CtApplication.parcel_ref.address_streetname != None:
                        streetname = value.CtApplication.parcel_ref.address_streetname
                    if value.CtApplication.parcel_ref.address_neighbourhood != None:
                        neighbourhood = value.CtApplication.parcel_ref.address_neighbourhood

                    app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == value.CtApplication.app_no).all()
                    for person_app in app_person:
                        person_count = self.session.query(BsPerson).filter(BsPerson.person_id == person_app.person).count()
                        if person_count != 0:
                            person = self.session.query(BsPerson).filter(BsPerson.person_id == person_app.person).one()
                            a3_count = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).count()
                            if a3_count != 0:
                                a3 = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).one()
                                a3_name = a3.name
                            if str(value.CtApplication.parcel_ref.landuse)[:1] == '1':
                                tax_zone_count = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).\
                                    filter(or_(SetTaxAndPriceZone.zone_no == 50, SetTaxAndPriceZone.zone_no == 60, SetTaxAndPriceZone.zone_no == 70, SetTaxAndPriceZone.zone_no == 80)).count()
                            else:
                                tax_zone_count = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).\
                                    filter(and_(SetTaxAndPriceZone.zone_no != 50, SetTaxAndPriceZone.zone_no != 60, SetTaxAndPriceZone.zone_no != 70, SetTaxAndPriceZone.zone_no != 80)).count()
                            if tax_zone_count == 1:
                                if str(value.CtApplication.parcel_ref.landuse)[:1] == '1':
                                    tax_zone = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).\
                                        filter(or_(SetTaxAndPriceZone.zone_no == 50, SetTaxAndPriceZone.zone_no == 60, SetTaxAndPriceZone.zone_no == 70, SetTaxAndPriceZone.zone_no == 80)).one()
                                else:
                                    tax_zone = self.session.query(SetTaxAndPriceZone).filter(SetTaxAndPriceZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).\
                                    filter(and_(SetTaxAndPriceZone.zone_no != 50, SetTaxAndPriceZone.zone_no != 60, SetTaxAndPriceZone.zone_no != 70, SetTaxAndPriceZone.zone_no != 80)).one()
                                tax_count = self.session.query(SetBaseTaxAndPrice).\
                                    filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id).\
                                    filter(SetBaseTaxAndPrice.landuse == value.CtApplication.approved_landuse).count()
                                if tax_count == 1:

                                    tax = self.session.query(SetBaseTaxAndPrice).\
                                        filter(SetBaseTaxAndPrice.tax_zone == tax_zone.zone_id).\
                                        filter(SetBaseTaxAndPrice.landuse == value.CtApplication.approved_landuse).one()
                                    price = float(tax.base_value_per_m2) * value.CtApplication.parcel_ref.area_m2
                                    base_tax = price*float(tax.base_tax_rate)/100

                                    subsidized_tax_rate = float(tax.subsidized_tax_rate)
                                    subsidized_tax_amount = base_tax*subsidized_tax_rate/100
                                    bas_tax_amount = base_tax - subsidized_tax_amount

                                    payment_year = self.year_sbox.value()
                                    tax_c = self.session.query(CtTaxAndPrice).filter(CtTaxAndPrice.person == person.person_id)\
                                                                            .filter(CtTaxAndPrice.record == value.CtOwnershipRecord.record_no).count()
                                    if tax_c == 1:
                                        tax = self.session.query(CtTaxAndPrice).filter(CtTaxAndPrice.person == person.person_id)\
                                                                            .filter(CtTaxAndPrice.record == value.CtOwnershipRecord.record_no).one()

                                        tax_to_pay_for_current_year = \
                                            self.__tax_to_pay_per_period(tax, date(payment_year, 1, 1), date(payment_year+1, 1, 1))

                                        paid_for_current_year = self.session.query(func.sum(CtTaxAndPricePayment.amount_paid))\
                                            .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
                                            .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()

                                        if paid_for_current_year is None:
                                            paid_for_current_year = 0

                                        partial = self.__sum_year_amount_paid(tax, value.CtOwnershipRecord)
                                        surplus = self.__surplus_from_previous_years(tax, value.CtOwnershipRecord)
                                        if surplus < 0:
                                            surplus = 0

                                        tax_left_to_pay = tax_to_pay_for_current_year - (paid_for_current_year + surplus)

                                        potential_fine_for_current_year = self.__potential_fine_for_year(tax, payment_year)
                                        tax_pay = tax_to_pay_for_current_year - surplus + partial + paid_difference

                                        paid_difference = paid_for_current_year - tax_pay

                            if person.address_au_level3 != None:
                                person_a3 = self.session.query(AuLevel3).filter(AuLevel3.code == person.address_au_level3).one()
                                person_address_a3 = person_a3.name
                            if person.address_au_level2 != None:
                                person_a2 = self.session.query(AuLevel2).filter(AuLevel2.code == person.address_au_level2).one()
                                person_address_a2 = person_a2.name
                            if person.address_au_level1 != None:
                                person_a1 = self.session.query(AuLevel1).filter(AuLevel1.code == person.address_au_level1).one()
                                person_address_a1 = person_a1.name
                            if person.address_street_name != None:
                                person_address_street_name = person.address_street_name
                            if person.address_khaskhaa != None:
                                person_address_khaskhaa = person.address_khaskhaa

                            if person.type == 10 or person.type == 20 \
                                or person.type == 50:
                                if person.middle_name != None:
                                    middle_name = person.middle_name
                                if person.first_name != None:
                                    first_name = person.first_name
                                if person.name != None:
                                    surname = person.name
                            if person.type == 30 or person.type == 40 \
                                or person.type == 60:
                                first_name = person.name

                            if person_app.main_applicant == True:
                                worksheet.write(row, col, row_number, format)
                                worksheet.write(row, col+1, value.CtApplication.parcel_ref.parcel_id, format)
                                worksheet.write(row, col+2, str(value.CtApplication.parcel_ref.area_m2), format)
                                worksheet.write(row, col+3, str(value.CtApplication.parcel_ref.area_m2/10000), format)
                                worksheet.write(row, col+4, str(price), format)
                                worksheet.write(row, col+5, landuse, format)
                                worksheet.write(row, col+6, a3_name, format)
                                worksheet.write(row, col+7, streetname, format)
                                worksheet.write(row, col+8, khashaa, format)
                                worksheet.write(row, col+9, neighbourhood, format)
                                worksheet.write(row, col+10, middle_name, format)
                                worksheet.write(row, col+11, surname, format)
                                worksheet.write(row, col+12, first_name, format)
                                worksheet.write(row, col+13, person.person_id, format)
                                worksheet.write(row, col+14, person_address_a1, format)
                                worksheet.write(row, col+15, person_address_a2, format)
                                worksheet.write(row, col+16, person_address_a3, format)
                                worksheet.write(row, col+17, person_address_street_name, format)
                                worksheet.write(row, col+18, person_address_khaskhaa, format)
                                worksheet.write(row, col+19, str(surplus), format)
                                worksheet.write(row, col+20, str(partial), format)
                                worksheet.write(row, col+21, str(tax_to_pay_for_current_year), format)
                                worksheet.write(row, col+22, str(''), format)
                                worksheet.write(row, col+23, str(potential_fine_for_current_year), format)
                                worksheet.write(row, col+24, str(tax_pay), format)
                                worksheet.write(row, col+25, str(''), format)
                                worksheet.write(row, col+26, str(''), format)
                                worksheet.write(row, col+27, str(''), format)
                                worksheet.write(row, col+28, str(paid_for_current_year), format)
                                worksheet.write(row, col+29, str(paid_difference), format)

                                row += 1
                                row_number += 1
                                value_p = self.progressBar.value() + 1
                                self.progressBar.setValue(value_p)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/" + restrictions + "-" + "land_taxation.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __potential_fine_for_year_fee(self, fee, payment_year):

        return self.__total_fine_fee(fee, payment_year, False)

    def __total_fine_fee(self, fee, payment_year, effective_fine=True):

        count = self.session.query(CtFeePayment)\
            .filter(CtFeePayment.contract == fee.contract)\
            .filter(CtFeePayment.person == fee.person)\
            .filter(CtFeePayment.year_paid_for == payment_year)\
            .filter(CtFeePayment.left_to_pay_for_q1 == 0)\
            .filter(CtFeePayment.left_to_pay_for_q2 == 0)\
            .filter(CtFeePayment.left_to_pay_for_q3 == 0)\
            .filter(CtFeePayment.left_to_pay_for_q4 == 0).count()

        if effective_fine:
            if count == 0:
                return 0
        else:
            if count != 0:
                return 0

        payment_frequency = fee.payment_frequency
        total_fine = 0
        fine = self.session.query(func.sum(CtFeePayment.fine_for_q1))\
            .filter(CtFeePayment.contract == fee.contract).filter(CtFeePayment.person == fee.person)\
            .filter(CtFeePayment.year_paid_for == payment_year).scalar()
        if fine is not None and payment_frequency == 20:
            total_fine += fine
        fine = self.session.query(func.sum(CtFeePayment.fine_for_q2))\
            .filter(CtFeePayment.contract == fee.contract).filter(CtFeePayment.person == fee.person)\
            .filter(CtFeePayment.year_paid_for == payment_year).scalar()
        if fine is not None and payment_frequency == 20:
            total_fine += fine
        fine = self.session.query(func.sum(CtFeePayment.fine_for_q3))\
            .filter(CtFeePayment.contract == fee.contract).filter(CtFeePayment.person == fee.person)\
            .filter(CtFeePayment.year_paid_for == payment_year).scalar()
        if fine is not None and payment_frequency == 20:
            total_fine += fine
        fine = self.session.query(func.sum(CtFeePayment.fine_for_q4))\
            .filter(CtFeePayment.contract == fee.contract).filter(CtFeePayment.person == fee.person)\
            .filter(CtFeePayment.year_paid_for == payment_year).scalar()
        if fine is not None:
            total_fine += fine

        return int(round(total_fine))

    def __potential_fine_for_year(self, tax, payment_year):

        return self.__total_fine(tax, payment_year, False)

    def __total_fine(self, tax, payment_year, effective_fine=True):

        count = self.session.query(CtTaxAndPricePayment)\
            .filter(CtTaxAndPricePayment.record == tax.record)\
            .filter(CtTaxAndPricePayment.person == tax.person)\
            .filter(CtTaxAndPricePayment.year_paid_for == payment_year)\
            .filter(CtTaxAndPricePayment.left_to_pay_for_q1 == 0)\
            .filter(CtTaxAndPricePayment.left_to_pay_for_q2 == 0)\
            .filter(CtTaxAndPricePayment.left_to_pay_for_q3 == 0)\
            .filter(CtTaxAndPricePayment.left_to_pay_for_q4 == 0).count()

        if effective_fine:
            if count == 0:
                return 0
        else:
            if count != 0:
                return 0

        payment_frequency = tax.payment_frequency
        total_fine = 0
        fine = self.session.query(func.sum(CtTaxAndPricePayment.fine_for_q1))\
            .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
            .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()
        if fine is not None and payment_frequency == 20:
            total_fine += fine
        fine = self.session.query(func.sum(CtTaxAndPricePayment.fine_for_q2))\
            .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
            .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()
        if fine is not None and payment_frequency == 20:
            total_fine += fine
        fine = self.session.query(func.sum(CtTaxAndPricePayment.fine_for_q3))\
            .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
            .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()
        if fine is not None and payment_frequency == 20:
            total_fine += fine
        fine = self.session.query(func.sum(CtTaxAndPricePayment.fine_for_q4))\
            .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
            .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()
        if fine is not None:
            total_fine += fine

        return int(round(total_fine))

    def __land_fee_quarterly(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/" + restrictions + "-" + "land_fee_quarterly.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 12)
        worksheet.set_column('C:C', 7)
        worksheet.set_column('D:D', 7)
        worksheet.set_column('E:E', 8)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 9)
        worksheet.set_column('H:H', 9)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 12)
        worksheet.set_column('K:K', 11)
        worksheet.set_column('L:L', 11)
        worksheet.set_column('M:M', 11)
        worksheet.set_column('N:N', 11)
        worksheet.set_column('O:O', 10)
        worksheet.set_column('P:P', 10)
        worksheet.set_column('Q:Q', 10)
        worksheet.set_column('R:R', 10)
        worksheet.set_column('S:S', 10)
        worksheet.set_column('T:T', 8)
        worksheet.set_column('U:U', 8)
        worksheet.set_column('V:V', 12)
        worksheet.set_column('W:W', 12)
        worksheet.set_column('X:X', 12)
        worksheet.set_column('Y:Y', 12)
        worksheet.set_column('Z:Z', 12)
        worksheet.set_column('AA:AA', 12)
        worksheet.set_column('AB:AB', 12)
        worksheet.set_column('AC:AC', 12)
        worksheet.set_column('AE:AE', 12)
        worksheet.set_column('AF:AF', 12)

        worksheet.set_row(3,25)
        worksheet.set_row(4,25)
        worksheet.set_row(5,50)
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

        a1 = self.working_l1_cbox.currentText()
        a2 = self.working_l2_cbox.currentText()
        worksheet.merge_range('D2:L2', a1 + u' аймаг/хотын ' + a2 + u' сум/дүүрэг-н хагас, бүтэн жилийн газрын төлбөрийн тайлан',format_header)
        worksheet.merge_range('A4:A6', u'Д/д',format)
        worksheet.merge_range('B4:J4', u'Нэгж талбарын мэдээлэл', format)
        worksheet.merge_range('C5:D5', u'Газрын хэмжээ', format)
        worksheet.merge_range('G5:J5', u'Газрын байршлын нэр, хаяг', format)
        worksheet.merge_range('B5:B6', u'Нэгж талбарын дугаар', format)
        worksheet.write('C6',u'м2', format)
        worksheet.write('D6',u'га', format)
        worksheet.merge_range('E5:E6', u'Газрын үнэ /мян.төг/', format)
        worksheet.merge_range('F5:F6', u'Газрын зориулалт', format)
        worksheet.write('G6', u'Баг /хороо/', format)
        worksheet.write('H6', u'Гудамж /хороолол/', format)
        worksheet.write('I6', u'Байр /хашаа,хаалга/-ны дугаар', format)
        worksheet.write('J6', u'Байршшил', format)
        worksheet.merge_range('K4:S4', u'Газар ашиглагчийн мэдээлэл', format)
        worksheet.merge_range('K5:K6', u'Овог', format)
        worksheet.merge_range('L5:L6', u'Эцэг /эх/-ийн нэр', format)
        worksheet.merge_range('M5:M6', u'Нэр', format)
        worksheet.merge_range('N5:N6', u'Регистрийн дугаар', format)
        worksheet.merge_range('P5:S5', u'Байнгын хаяг', format)
        worksheet.write('O6', u'Аймаг /нийслэл/', format)
        worksheet.write('P6', u'Сум /дүүрэг/', format)
        worksheet.write('Q6', u'Баг /хороо/', format)
        worksheet.write('R6', u'Гудамж /хороолол/', format)
        worksheet.write('S6', u'Байр /хашаа, хаалга/-ны дугаар', format)
        worksheet.merge_range('T4:AF4', u'Газрын төлбөрийн тооцоо', format)
        worksheet.merge_range('T5:T6', u'Урьд оны үлдэгдэл илүү', format)
        worksheet.merge_range('U5:U6', u'Урьд оны үлдэгдэл дутуу', format)
        worksheet.merge_range('V5:V6', u'Тайлант онд ноогдуулсан жилийн төлбөр/төг/', format)
        worksheet.merge_range('W5:X5', u'Хяналтаар ноогдуулсан', format)
        worksheet.write('W6', u'Нөхөн төлбөр', format)
        worksheet.write('X6', u'Хүү торгууль', format)
        worksheet.merge_range('Y5:Y6', u'Тайлант онд нийт төлбөл зохих төлбөрийн дүн /төг/', format)
        worksheet.merge_range('Z5:AC5', u'Тайлант онд төлсөн /төг/', format)
        worksheet.write('Z6', u'Урьд оны дутуу төлөлтөөс', format)
        worksheet.write('AA6', u'Тайлангаар ноогдуулснаас', format)
        worksheet.write('AB6', u'Хүү торгууль нөхөн төлбөр', format)
        worksheet.write('AC6', u'Бүгд дүн', format)
        worksheet.merge_range('AD5:AD6', u'Хүчингүй болсон дүн', format)
        worksheet.merge_range('AE5:AE6', u'Тайлант оны эцэст илүү дутуу төлөлт', format)
        worksheet.merge_range('AF5:AF6', u'Тайлбар', format)

        begin_date = DatabaseUtils.convert_date(self.report_begin_date.date())
        end_date = DatabaseUtils.convert_date(self.report_end_date.date())
        end_date = end_date + timedelta(days=1)
        row = 6
        col = 0
        row_number = 1
        c_status = 0
        # try:
        values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
            join(CtContractApplicationRole.application_ref).\
            join(CtContract).\
            join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
            filter(CtContract.contract_begin.between(begin_date, end_date)).all()
        if not self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex()) == -1:
            type = self.report_app_type_cbox.itemData(self.report_app_type_cbox.currentIndex())
            values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
            join(CtContractApplicationRole.application_ref).\
            join(CtContract).\
            join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
            filter(CtContract.contract_begin.between(begin_date, end_date)).\
            filter(CtApplication.app_type == type).all()
        if not self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex()) == -1:
            type = self.report_land_use_cbox.itemData(self.report_land_use_cbox.currentIndex())
            values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
            join(CtContractApplicationRole.application_ref).\
            join(CtContract).\
            join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
            filter(CtContract.contract_begin.between(begin_date, end_date)).\
            filter(CtApplication.approved_landuse == type).all()
        if not self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex()) == -1:
            type = self.report_person_type_cbox.itemData(self.report_person_type_cbox.currentIndex())
            values = self.session.query(CtApplication,CtContract,CtDecisionApplication).\
            join(CtContractApplicationRole.application_ref).\
            join(CtContract).\
            join(CtDecisionApplication, CtApplication.app_no == CtDecisionApplication.application).\
            join(CtApplicationPersonRole, CtApplication.app_no == CtApplicationPersonRole.application).\
            join(BsPerson, CtApplicationPersonRole.person == BsPerson.person_id).\
            filter(CtContract.contract_begin.between(begin_date, end_date)).\
            filter(BsPerson.type == type).all()

        count = len(values)
        self.progressBar.setMaximum(count)
        for value in values:
            khashaa = ''
            streetname = ''
            neighbourhood = ''
            landuse = ''
            middle_name = ''
            first_name = ''
            surname = ''
            person_address_a1 = '-'
            person_address_a2 = '-'
            person_address_a3 = '-'
            person_address_street_name = '-'
            person_address_khaskhaa = '-'
            price = 0
            base_tax = 0
            bas_tax_amount = 0
            subsidized_tax_rate = 0
            base_tax_rate = 0
            subsidized_tax_amount = 0
            tax_to_pay_for_current_year = 0
            fee_to_pay_for_current_year = 0
            paid_for_current_year = 0
            surplus = 0
            partial = 0
            paid_difference = 0
            potential_fine_for_current_year = 0
            surplus_and_partial = 0
            tax_left_to_pay = 0
            tax_right_to_pay = 0
            a3_name = ''
            fee_pay = 0
            if value.CtApplication.approved_landuse != None:
                landuse = value.CtApplication.approved_landuse_ref.description
                landuse_code = value.CtApplication.approved_landuse_ref.code

            if value.CtApplication.parcel and value.CtApplication.parcel_ref:
                if value.CtApplication.parcel_ref:
                    if value.CtApplication.parcel_ref.address_khashaa:
                        khashaa = value.CtApplication.parcel_ref.address_khashaa
                if value.CtApplication.parcel_ref:
                    if value.CtApplication.parcel_ref.address_streetname:
                        streetname = value.CtApplication.parcel_ref.address_streetname
                if value.CtApplication.parcel_ref:
                    if value.CtApplication.parcel_ref.address_neighbourhood:
                        neighbourhood = value.CtApplication.parcel_ref.address_neighbourhood

                app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == value.CtApplication.app_no).all()
                for person_app in app_person:
                    person_count = self.session.query(BsPerson).filter(BsPerson.person_id == person_app.person).count()
                    if person_count != 0:
                        person = self.session.query(BsPerson).filter(BsPerson.person_id == person_app.person).one()

                        a3_count = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).count()
                        if a3_count != 0:
                            a3 = self.session.query(AuLevel3).filter(AuLevel3.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).one()
                            a3_name = a3.name
                        if str(value.CtApplication.parcel_ref.landuse)[:1] == '1':
                            tax_zone_count = self.session.query(SetFeeZone).filter(SetFeeZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).\
                                filter(or_(SetFeeZone.zone_no == 50, SetFeeZone.zone_no == 60, SetFeeZone.zone_no == 70, SetFeeZone.zone_no == 80)).count()
                        else:
                            tax_zone_count = self.session.query(SetFeeZone).filter(SetFeeZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).\
                                filter(and_(SetFeeZone.zone_no != 50, SetFeeZone.zone_no != 60, SetFeeZone.zone_no != 70, SetFeeZone.zone_no != 80)).count()
                        if tax_zone_count == 1:
                            if str(value.CtApplication.parcel_ref.landuse)[:1] == '1':
                                tax_zone = self.session.query(SetFeeZone).filter(SetFeeZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).\
                                    filter(or_(SetFeeZone.zone_no == 50, SetFeeZone.zone_no == 60, SetFeeZone.zone_no == 70, SetFeeZone.zone_no == 80)).one()
                            else:
                                tax_zone = self.session.query(SetFeeZone).filter(SetFeeZone.geometry.ST_Contains(value.CtApplication.parcel_ref.geometry)).\
                                    filter(and_(SetFeeZone.zone_no != 50, SetFeeZone.zone_no != 60, SetFeeZone.zone_no != 70, SetFeeZone.zone_no != 80)).one()

                            tax_count = self.session.query(SetBaseFee).\
                                filter(SetBaseFee.fee_zone == tax_zone.zone_id).\
                                filter(SetBaseFee.landuse == value.CtApplication.approved_landuse).count()
                            if tax_count == 1:

                                payment_year = self.year_sbox.value()

                                fee_c = self.session.query(CtFee).filter(CtFee.person == person.person_id)\
                                                                 .filter(CtFee.contract == value.CtContract.contract_no).count()
                                if value.CtContract.contract_end and value.CtContract.contract_begin:
                                    if fee_c == 1 and (value.CtContract.contract_end.year-value.CtContract.contract_begin.year) > 1:
                                        fee = self.session.query(CtFee).filter(CtFee.person == person.person_id)\
                                                                        .filter(CtFee.contract == value.CtContract.contract_no).one()
                                        fee_to_pay_for_current_year = \
                                            self.__fee_to_pay_per_period(fee, date(payment_year, 1, 1), date(payment_year+1, 1, 1))

                                        paid_for_current_year = self.session.query(func.sum(CtFeePayment.amount_paid))\
                                            .filter(CtFeePayment.contract == fee.contract).filter(CtFeePayment.person == fee.person)\
                                            .filter(CtFeePayment.year_paid_for == payment_year).scalar()

                                        if paid_for_current_year is None:
                                            paid_for_current_year = 0

                                        partial = self.__sum_year_amount_paid_fee(fee, value.CtContract)
                                        surplus = self.__surplus_from_previous_years_fee(fee, value.CtContract)

                                        potential_fine_for_current_year = self.__potential_fine_for_year_fee(fee, payment_year)
                                        fee_pay = fee_to_pay_for_current_year - surplus + partial + potential_fine_for_current_year
                                        paid_difference = paid_for_current_year - fee_pay
                        if person.address_au_level3 != None:
                            person_a3_c = self.session.query(AuLevel3).filter(
                                AuLevel3.code == person.address_au_level3).count()
                            if person_a3_c == 1:
                                person_a3 = self.session.query(AuLevel3).filter(AuLevel3.code == person.address_au_level3).one()
                                person_address_a3 = person_a3.name
                        if person.address_au_level2 != None:
                            person_a2_c = self.session.query(AuLevel2).filter(
                                AuLevel2.code == person.address_au_level2).count()
                            if person_a2_c == 1:
                                person_a2 = self.session.query(AuLevel2).filter(AuLevel2.code == person.address_au_level2).one()
                                person_address_a2 = person_a2.name
                        if person.address_au_level1 != None:
                            person_a1_c = self.session.query(AuLevel1).filter(
                                AuLevel1.code == person.address_au_level1).count()
                            if person_a1_c == 1:
                                person_a1 = self.session.query(AuLevel1).filter(AuLevel1.code == person.address_au_level1).one()
                                person_address_a1 = person_a1.name
                        if person.address_street_name != None:
                            person_address_street_name = person.address_street_name
                        if person.address_khaskhaa != None:
                            person_address_khaskhaa = person.address_khaskhaa

                        if person.type == 10 or person.type == 20 \
                            or person.type == 50:
                            if person.middle_name != None:
                                middle_name = person.middle_name
                            if person.first_name != None:
                                first_name = person.first_name
                            if person.name != None:
                                surname = person.name
                        if person.type == 30 or person.type == 40 \
                            or person.type == 60:
                            first_name = person.name

                        if person_app.main_applicant == True:
                            worksheet.write(row, col, row_number, format)
                            worksheet.write(row, col+1, value.CtApplication.parcel_ref.parcel_id, format)
                            worksheet.write(row, col+2, str(value.CtApplication.parcel_ref.area_m2), format)
                            worksheet.write(row, col+3, str(value.CtApplication.parcel_ref.area_m2/10000), format)
                            worksheet.write(row, col+4, str(price), format)
                            worksheet.write(row, col+5, landuse, format)
                            worksheet.write(row, col+6, a3_name, format)
                            worksheet.write(row, col+7, streetname, format)
                            worksheet.write(row, col+8, khashaa, format)
                            worksheet.write(row, col+9, neighbourhood, format)
                            worksheet.write(row, col+10, middle_name, format)
                            worksheet.write(row, col+11, surname, format)
                            worksheet.write(row, col+12, first_name, format)
                            worksheet.write(row, col+13, person.person_id, format)
                            worksheet.write(row, col+14, person_address_a1, format)
                            worksheet.write(row, col+15, person_address_a2, format)
                            worksheet.write(row, col+16, person_address_a3, format)
                            worksheet.write(row, col+17, person_address_street_name, format)
                            worksheet.write(row, col+18, person_address_khaskhaa, format)
                            worksheet.write(row, col+19, str(surplus), format)
                            worksheet.write(row, col+20, str(partial), format)
                            worksheet.write(row, col+21, str(fee_to_pay_for_current_year), format)
                            worksheet.write(row, col+22, str(''), format)
                            worksheet.write(row, col+23, str(potential_fine_for_current_year), format)
                            worksheet.write(row, col+24, str(fee_pay), format)
                            worksheet.write(row, col+25, str(''), format)
                            worksheet.write(row, col+26, str(''), format)
                            worksheet.write(row, col+27, str(''), format)
                            worksheet.write(row, col+28, str(paid_for_current_year), format)
                            worksheet.write(row, col+29, str(''), format)
                            worksheet.write(row, col+30, str(paid_difference), format)
                            worksheet.write(row, col+31, str(''), format)

                            row += 1
                            row_number += 1
                            value_p = self.progressBar.value() + 1
                            self.progressBar.setValue(value_p)

        # except SQLAlchemyError, e:
        #     PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
        #     return
        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/" + restrictions + "-" + "land_fee_quarterly.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))


    def __fee_to_pay_per_period(self, fee, period_begin, period_end):

        # Intersect contract duration with payment period
        sql = "select lower(daterange(contract_begin, contract_end, '[)') * daterange(:from, :to, '[)'))," \
              " upper(daterange(contract_begin, contract_end, '[)') * daterange(:from, :to, '[)')) " \
              "from ct_contract where contract_no = :contract_no"

        result = self.session.execute(sql, {'from': period_begin,
                                            'to': period_end,
                                            'contract_no': fee.contract})
        for row in result:
            effective_begin = row[0]
            effective_end = row[1]

        if effective_begin is None and effective_end is None:
            return 0

        # Intersect the effective payment period with the archived fees
        sql = "select upper(daterange(valid_from, valid_till, '[)') * daterange(:begin, :end, '[)')) - "\
                 "lower(daterange(valid_from, valid_till, '[)') * daterange(:begin, :end, '[)')) as days, "\
                 "fee_contract from ct_archived_fee where contract = :contract and person = :person"

        result = self.session.execute(sql, {'begin': effective_begin,
                                            'end': effective_end,
                                            'contract': fee.contract,
                                            'person': fee.person})
        fee_for_period = 0
        total_days = 0

        for row in result:
            days = row[0]
            if days is None:
                continue
            annual_fee = row[1]
            adjusted_fee = (annual_fee / 365) * days
            fee_for_period += adjusted_fee
            total_days += days

        effective_days = (effective_end-effective_begin).days

        if effective_days - total_days > 0:
            fee_for_period += (effective_days-total_days) * fee.fee_contract / 365

        return int(round(fee_for_period))

    def __surplus_from_previous_years_fee(self, fee, contract):

        year_to_pay_for = self.year_sbox.value()

        surplus_last_year = 0

        for payment_year in range(contract.contract_begin.year, year_to_pay_for):

            amount_paid = self.session.query(func.sum(CtFeePayment.amount_paid))\
                .filter(CtFeePayment.contract == fee.contract).filter(CtFeePayment.person == fee.person)\
                .filter(CtFeePayment.year_paid_for == payment_year).scalar()
            if amount_paid is None:
                amount_paid = 0

            fee_to_pay = self.__fee_to_pay_per_period(fee, date(payment_year, 1, 1), date(payment_year+1, 1, 1))
            if (amount_paid + surplus_last_year) - fee_to_pay > 0:
                surplus_last_year = (amount_paid + surplus_last_year) - fee_to_pay
            else:
                surplus_last_year = 0

        return surplus_last_year

    def __auction_info(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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

        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"-"+"auction_info.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 11)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 10)
        worksheet.set_column('H:H', 10)
        worksheet.set_column('I:I', 15)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 10)
        worksheet.set_column('L:L', 10)
        worksheet.set_column('M:M', 10)
        worksheet.set_column('N:N', 10)
        worksheet.set_column('O:O', 15)
        worksheet.set_column('P:P', 15)
        worksheet.set_column('Q:Q', 15)
        worksheet.set_column('R:R', 10)
        worksheet.set_column('S:S', 10)
        worksheet.set_column('T:T', 10)
        worksheet.set_column('U:U', 10)
        worksheet.set_column('V:V', 10)
        worksheet.set_column('W:W', 20)
        worksheet.set_row(5,50)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.2,right=0.1)

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(10)
        format.set_border(1)

        format1 = workbook.add_format()
        format1.set_text_wrap()
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_rotation(90)
        format1.set_font_name('Times New Roman')
        format1.set_font_size(10)
        format1.set_border(1)

        format2 = workbook.add_format()
        format2.set_text_wrap()
        format2.set_align('center')
        format2.set_align('vcenter')
        format2.set_font_name('Times New Roman')
        format2.set_font_size(10)
        format2.set_border(1)

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(14)
        format_header.set_bold()

        worksheet.merge_range('D2:M2', u'Дуудлага худалдааны мэдээ',format_header)
        worksheet.merge_range('A4:A6', u'№',format)
        worksheet.merge_range('B4:B6', u'Аймаг/Нийслэл, сум/дүүрэг-н нэр', format)
        worksheet.merge_range('C4:F4', u'Газрын мэдээлэл', format)
        worksheet.merge_range('C5:C6', u'Ашиглалтын зориулалт', format)
        worksheet.merge_range('D5:D6', u'Хэмжээ/м2/', format)
        worksheet.merge_range('E5:E6', u'Байршил', format)
        worksheet.merge_range('F5:F6', u'Эзэмшүүлэх, ашиглуулах хугацаа', format)
        worksheet.merge_range('G4:N4', u'Дуудлага худалдааны мэдээлэл', format)
        worksheet.merge_range('G5:H5', u'Зарласан захирамжийн', format)
        worksheet.write('G6',u"огноо", format)
        worksheet.write('H6',u"дугаар", format)
        worksheet.merge_range('I5:I6', u'Өмчлөх, Эзэмших, Ашиглах', format)
        worksheet.merge_range('J5:J6', u'Анхны үнэ /мян.төг/', format)
        worksheet.merge_range('K5:K6', u'Оролцогчидын тоо', format)
        worksheet.merge_range('L5:M5', u'Зохион байгуулсан', format)
        worksheet.write('L6',u"огноо", format)
        worksheet.write('M6',u"Гарсан зардал/мян.төг/", format)
        worksheet.merge_range('N4:N6', u'Оролцогчгүйн улмаас явуулаагүй эсэх', format)
        worksheet.merge_range('O4:Q4', u'Дэнчингийн мэдээлэл', format)
        worksheet.merge_range('O5:O6', u'Дэнчингийн үнэ/мян.төг/', format)
        worksheet.merge_range('P5:P6', u'Нийт дэнчин/мян.төг/', format)
        worksheet.merge_range('Q5:Q6', u'Буцаагдсан дэнчин/мян.төг/', format)
        worksheet.merge_range('R4:S5', u'Дуудлага худалдааны ялагч', format)
        worksheet.write('R6',u"Иргэн", format)
        worksheet.write('S6',u"Хуулийн этгээд", format)
        worksheet.merge_range('T4:V4', u'Орлогын мэдээлэл', format)
        worksheet.merge_range('T5:T6', u'Үнэ төлж авсан/мян.төг/', format)
        worksheet.merge_range('U5:U6', u'Үнэ төлөөгүйн улмаас буцаасан/мян.төг/', format)
        worksheet.merge_range('V5:V6', u'Төсөвт орсон орлого/мян.төг/', format)
        worksheet.merge_range('W4:W6', u'Тайлбар',format)


        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/" + restrictions + "-" + "auction_info.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __selection_of_draft(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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

        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"-"+"selection_of_draft.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 11)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 10)
        worksheet.set_column('H:H', 10)
        worksheet.set_column('I:I', 15)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 10)
        worksheet.set_column('L:L', 10)
        worksheet.set_column('R:R', 20)

        worksheet.set_row(5,50)
        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.2,right=0.1)

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(10)
        format.set_border(1)

        format1 = workbook.add_format()
        format1.set_text_wrap()
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_rotation(90)
        format1.set_font_name('Times New Roman')
        format1.set_font_size(10)
        format1.set_border(1)

        format2 = workbook.add_format()
        format2.set_text_wrap()
        format2.set_align('center')
        format2.set_align('vcenter')
        format2.set_font_name('Times New Roman')
        format2.set_font_size(10)
        format2.set_border(1)

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(14)
        format_header.set_bold()

        worksheet.merge_range('D2:M2', u'Төсөл сонгон шалгаруулалтын мэдээ',format_header)
        worksheet.merge_range('A4:A6', u'№',format)
        worksheet.merge_range('B4:B6', u'Аймаг/Нийслэл, сум/дүүрэг-н нэр', format)
        worksheet.merge_range('C4:F4', u'Газрын мэдээлэл', format)
        worksheet.merge_range('C5:C6', u'Ашиглалтын зориулалт', format)
        worksheet.merge_range('D5:D6', u'Хэмжээ/м2/', format)
        worksheet.merge_range('E5:E6', u'Байршил', format)
        worksheet.merge_range('F5:F6', u'Эзэмшүүлэх хугацаа', format)
        worksheet.merge_range('G4:M4', u'Төсөл сонгон шалгаруулалтын мэдээлэл', format)
        worksheet.merge_range('G5:H5', u'Зарласан захирамжийн', format)
        worksheet.write('G6',u"огноо", format)
        worksheet.write('H6',u"дугаар", format)
        worksheet.merge_range('I5:I6', u'Анхны үнэ /мян.төг/', format)
        worksheet.merge_range('J5:J6', u'Ирүүлсэн төслийн тоо', format)
        worksheet.merge_range('K5:L5', u'Зохион байгуулсан', format)
        worksheet.write('K6',u"огноо", format)
        worksheet.write('L6',u"Гарсан зардал/мян.төг/", format)
        worksheet.merge_range('M5:M6', u'Төсөл ирүүлээгүйн улмаас явуулаагүй эсэх', format)

        worksheet.merge_range('N4:O5', u'Төсөл сонгон шалгаруулалтын ялагч', format)
        worksheet.write('N6',u"Иргэн", format)
        worksheet.write('O6',u"Хуулийн этгээд", format)
        worksheet.merge_range('P4:Q4', u'Орлогын мэдээлэл', format)
        worksheet.merge_range('P5:P6', u'Үнэ төлж авсан/мян.төг/', format)
        worksheet.merge_range('Q5:Q6', u'Төсөвт орсон орлого/мян.төг/', format)
        worksheet.merge_range('R4:R6', u'Тайлбар',format)

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/" + restrictions + "-" + "selection_of_draft.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __condominium_area(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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

        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"-"+"condominium_area.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 8)
        worksheet.set_column('D:D', 8)
        worksheet.set_column('E:E', 8)
        worksheet.set_column('F:F', 8)
        worksheet.set_column('G:G', 10)
        worksheet.set_column('H:H', 10)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 10)
        worksheet.set_column('K:K', 10)
        worksheet.set_column('L:L', 10)

        worksheet.set_landscape()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.2,right=0.1)

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(10)
        format.set_border(1)

        format1 = workbook.add_format()
        format1.set_text_wrap()
        format1.set_align('center')
        format1.set_align('vcenter')
        format1.set_rotation(90)
        format1.set_font_name('Times New Roman')
        format1.set_font_size(10)
        format1.set_border(1)

        format2 = workbook.add_format()
        format2.set_text_wrap()
        format2.set_align('center')
        format2.set_align('vcenter')
        format2.set_font_name('Times New Roman')
        format2.set_font_size(10)
        format2.set_border(1)

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(14)
        format_header.set_bold()

        worksheet.merge_range('C2:M2', u'СӨХ-ийн орчны газрын ашиглалт, гэрчилгээжүүлэлтийн тайлан',format_header)
        worksheet.merge_range('A4:A5', u'№',format)
        worksheet.merge_range('B4:B5', u'Аймаг/Нийслэл, сум/дүүрэг-н нэр', format)
        worksheet.merge_range('C4:C5', u'Нийт СӨХ-ийн тоо', format1)
        worksheet.merge_range('D4:D5', u'Тооллогонд хамрагдсан СӨХ-ийн тоо', format1)
        worksheet.merge_range('E4:E5', u'Газар ашиглахаар хүсэлт гаргасан СӨХ-ийн тоо', format1)
        worksheet.merge_range('F4:F5', u'Засаг даргын захирамжаар баталгаажсан', format1)
        worksheet.merge_range('G4:J4', u'Үүнээс', format)
        worksheet.write('G5',u"Захирамжаар баталгаажигдсан СӨХ-ээс газар ашиглах эрхийн гэрээ байгуулсан", format1)
        worksheet.write('H5',u"Нийт СӨХ-ны ашиглаж байгаа талбайн хэмжээ /м2/", format1)
        worksheet.write('I5',u"Маргаантай болон судлаж байгаа", format1)
        worksheet.write('J5',u"Захирамж гарахаар хүлээгдэж байгаа", format1)
        worksheet.merge_range('K4:K5', u'Ерөнхий төлөвлөгөө хийгдэж байгаа СӨХ-ийн тоо', format1)
        worksheet.merge_range('L4:L5', u'Ерөнхий төлөвлөгөө хийгдсэн СӨХ-ийн тоо', format1)

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/" + restrictions + "-" + "condominium_area.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    @pyqtSlot()
    def on_report_layer_button_clicked(self):

        root = QgsProject.instance().layerTreeRoot()

        LayerUtils.refresh_layer()

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
        itemsList = self.listWidget.selectedItems()
        code = '0'
        for item in itemsList:
            code = str(item.text()[:2])
        if code == '01':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_application_list")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_application_list", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_application.qml")
                vlayer.setLayerName(self.tr("Application Layer"))
                mygroup.addLayer(vlayer)
        elif code == '03':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_waiting_list")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_waiting_list", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_waiting.qml")
                vlayer.setLayerName(self.tr("Wait governor list"))
                mygroup.addLayer(vlayer)
        elif code == '04':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_governor_decision_list")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_governor_decision_list", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_governor_decision.qml")
                vlayer.setLayerName(self.tr("Governor decision list"))
                mygroup.addLayer(vlayer)
        elif code == '05':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_refused_list")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_refused_list", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_refused.qml")
                vlayer.setLayerName(self.tr("Refused decision list"))
                mygroup.addLayer(vlayer)
        elif code == '06':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_end_of_this_year_list")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_end_of_this_year_list", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_end of this year.qml")
                vlayer.setLayerName(self.tr("Parcel end of this year list"))
                mygroup.addLayer(vlayer)
        elif code == '07':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_land_users_list")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_land_users_list", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_land_users.qml")
                vlayer.setLayerName(self.tr("Land users list"))
                mygroup.addLayer(vlayer)
        elif code == '08':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_land_possessors_list")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_land_possessors_list", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_possessors.qml")
                vlayer.setLayerName(self.tr("Land possessors list"))
                mygroup.addLayer(vlayer)
        elif code == '09':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_land_ownerships_list")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_land_ownerships_list", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_land_ownership.qml")
                vlayer.setLayerName(self.tr("Land ownerships list"))
                mygroup.addLayer(vlayer)
        elif code == '10':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_land_tax_list")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_land_tax_list", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_land_tax.qml")
                vlayer.setLayerName(self.tr("Land tax list"))
                mygroup.addLayer(vlayer)
        elif code == '11':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_land_tax_payment_list")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_land_tax_payment_list", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_land_tax_payment.qml")
                vlayer.setLayerName(self.tr("Land tax payment list"))
                mygroup.addLayer(vlayer)
        elif code == '12':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_land_fee_payment_list")
            tmp_parcel_fee_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_land_fee_list")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_land_fee_payment_list", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_land_fee_payment.qml")
                vlayer.setLayerName(self.tr("Land fee payment list"))
                mygroup.addLayer(vlayer)
            if tmp_parcel_fee_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_land_fee_list", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_land_fee.qml")
                vlayer.setLayerName(self.tr("Land fee list"))
                mygroup.addLayer(vlayer)
        elif code == '14':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_mortgage_parcel")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_mortgage_parcel", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_land_fee_payment.qml")
                vlayer.setLayerName(self.tr("Mortgage"))
                mygroup.addLayer(vlayer)
        elif code == '15':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_court_parcel")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"Тайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_court_parcel", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/view_land_tax.qml")
                vlayer.setLayerName(self.tr("Court"))
                mygroup.addLayer(vlayer)
                
    @pyqtSlot(QTableWidgetItem)
    def on_person_results_twidget_itemClicked(self, item):

        id = item.data(Qt.UserRole)
        try:

            person_result = self.session.query(PersonSearch).filter(PersonSearch.person_id == id).one()
            self.name_edit.setText(person_result.first_name)
            self.personal_edit.setText(person_result.person_id)
            self.state_reg_num_edit.setText(person_result.state_registration_no)
            self.mobile_num_edit.setText(person_result.phone)
            self.person_application_num_edit.setText(person_result.app_no)
            self.person_decision_num_edit.setText(person_result.decision_no)
            if person_result.contract_no != None:
                self.person_contract_num_edit.setText(person_result.contract_no)
            else:
                self.person_contract_num_edit.setText(person_result.record_no)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    @pyqtSlot(QTableWidgetItem)
    def on_parcel_results_twidget_itemClicked(self, item):

        id = item.data(Qt.UserRole)

        # try:

        if self.is_parcel_checkbox.isChecked():
            parcel_result_count = self.session.query(ParcelSearch).filter(ParcelSearch.parcel_id == id).count()

            if parcel_result_count > 1:
                parcel_results = self.session.query(ParcelSearch).filter(ParcelSearch.parcel_id == id).all()
                for parcel in parcel_results:

                    if parcel.main_applicant:
                        parcel_result = self.session.query(ParcelSearch).filter(ParcelSearch.parcel_id == id).\
                            filter(ParcelSearch.main_applicant == True).one()
                    # if parcel.person_role == 70:
                    #     parcel_result = self.session.query(ParcelSearch).filter(ParcelSearch.parcel_id == id)\
                    #         .filter(ParcelSearch.person_role == 70).filter(ParcelSearch.main_applicant == True).one()
                    # elif parcel.person_role == 40:
                    #     parcel_result = self.session.query(ParcelSearch).filter(ParcelSearch.parcel_id == id) \
                    #         .filter(ParcelSearch.person_role == 40).filter(ParcelSearch.main_applicant == True).one()
            elif parcel_result_count == 1:
                parcel_result = self.session.query(ParcelSearch).filter(ParcelSearch.parcel_id == id).one()
            else:
                parcel_result = self.session.query(TmpParcelSearch).filter(TmpParcelSearch.parcel_id == id).one()

            soum_code = parcel_result.au2_code
            aimag_code = soum_code[:3]
            self.working_l1_cbox.setCurrentIndex(self.working_l1_cbox.findData(aimag_code))
            self.working_l2_cbox.setCurrentIndex(self.working_l2_cbox.findData(soum_code))

            self.parcel_num_edit.setText(parcel_result.parcel_id)
            self.geo_id_edit.setText(parcel_result.geo_id)
            self.parcel_right_holder_name_edit.setText(parcel_result.first_name)
            self.parcel_app_num_edit.setText(parcel_result.app_no)
            self.parcel_decision_num_edit.setText(parcel_result.decision_no)
            if parcel_result.contract_no != None:
                self.parcel_contract_num_edit.setText(parcel_result.contract_no)
            else:
                self.parcel_contract_num_edit.setText(parcel_result.record_no)
            self.personal_parcel_edit.setText(parcel_result.person_id)
            self.land_use_type_cbox.setCurrentIndex(self.land_use_type_cbox.findData(parcel_result.landuse))
        else:
            parcel_result = self.session.query(TmpParcelSearch).filter(TmpParcelSearch.parcel_id == id).one()

            soum_code = parcel_result.au2_code
            aimag_code = soum_code[:3]
            self.working_l1_cbox.setCurrentIndex(self.working_l1_cbox.findData(aimag_code))
            self.working_l2_cbox.setCurrentIndex(self.working_l2_cbox.findData(soum_code))

            self.parcel_num_edit.setText(parcel_result.parcel_id)
            self.geo_id_edit.setText(parcel_result.geo_id)

            self.parcel_right_holder_name_edit.setText(parcel_result.first_name)
            self.parcel_app_num_edit.setText(parcel_result.app_no)
            self.parcel_decision_num_edit.setText(parcel_result.decision_no)
            if parcel_result.contract_no != None:
                self.parcel_contract_num_edit.setText(parcel_result.contract_no)
            else:
                self.parcel_contract_num_edit.setText(parcel_result.record_no)
            self.personal_parcel_edit.setText(parcel_result.person_id)
            self.land_use_type_cbox.setCurrentIndex(self.land_use_type_cbox.findData(parcel_result.landuse))

        # except SQLAlchemyError, e:
        #     PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
        #     return

    @pyqtSlot(QTableWidgetItem)
    def on_application_results_twidget_itemClicked(self, item):

        id = item.data(Qt.UserRole)
        soum_code = id.split("-")[0]
        aimag_code = soum_code[:3]
        self.working_l1_cbox.setCurrentIndex(self.working_l1_cbox.findData(aimag_code))
        self.working_l2_cbox.setCurrentIndex(self.working_l2_cbox.findData(soum_code))
        try:
            app_result = self.session.query(ApplicationSearch).filter(ApplicationSearch.app_no == id).one()
            self.application_application_num_edit.setText(app_result.app_no)
            self.application_right_holder_name_edit.setText(app_result.first_name)
            self.application_parcel_num_edit.setText(app_result.parcel_id)
            self.application_decision_num_edit.setText(app_result.decision_no)
            if app_result.contract_no != None:
                self.application_contract_num_edit.setText(app_result.contract_no)
            else:
                self.application_contract_num_edit.setText(app_result.record_no)
            self.personal_application_edit.setText(app_result.person_id)

            self.app_type_cbox.setCurrentIndex(self.app_type_cbox.findData(app_result.app_type))
            self.status_cbox.setCurrentIndex(self.status_cbox.findData(app_result.status))
            self.office_in_charge_cbox.setCurrentIndex(self.office_in_charge_cbox.findData(app_result.officer_in_charge))
            self.next_officer_in_charge_cbox.setCurrentIndex(self.next_officer_in_charge_cbox.findData(app_result.next_officer_in_charge))

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    @pyqtSlot(QTableWidgetItem)
    def on_decision_results_twidget_itemClicked(self, item):

        id = item.data(Qt.UserRole)
        try:
            decision_result = self.session.query(DecisionSearch).filter(DecisionSearch.decision_no == id).one()
            self.decision_num_edit.setText(decision_result.decision_no)
            self.decision_date.setDate(decision_result.decision_date)
            self.decision_right_holder_name_edit.setText(decision_result.first_name)
            self.personal_decision_edit.setText(decision_result.person_id)
            self.decision_parcel_num_edit.setText(decision_result.parcel_id)
            self.decision_application_num_edit.setText(decision_result.app_no)
            if decision_result.contract_no != None:
                self.decision_contract_num_edit.setText(decision_result.contract_no)
            else:
                self.decision_contract_num_edit.setText(decision_result.record_no)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    @pyqtSlot(QTableWidgetItem)
    def on_case_results_twidget_itemClicked(self, item):

        id = item.data(Qt.UserRole)
        try:
            maintenance_result = self.session.query(MaintenanceSearch).filter(MaintenanceSearch.id == id).one()
            self.case_no_edit.setText(str(maintenance_result.id))
            if maintenance_result.completion_date != None:
                self.case_completion_date_edit.setDate(maintenance_result.completion_date)
            self.case_parcel_no_edit.setText(maintenance_result.parcel)
            if maintenance_result.app_no != None:
                self.case_app_no_edit.setText(maintenance_result.app_no)

            if maintenance_result.surveyed_by_surveyor != None:
                self.surveyed_by_company_cbox.setCurrentIndex(self.surveyed_by_company_cbox.findData(maintenance_result.surveyed_by_surveyor))
            if maintenance_result.surveyed_by_land_office != None:
                self.surveyed_by_land_officer_cbox.setCurrentIndex(self.surveyed_by_land_officer_cbox.findData(maintenance_result.surveyed_by_land_office))
            if maintenance_result.completed_by!= None:
                self.finalized_by_cbox.setCurrentIndex(self.finalized_by_cbox.findData(maintenance_result.completed_by))

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    @pyqtSlot(QTableWidgetItem)
    def on_contract_results_twidget_itemClicked(self, item):

        id = item.data(Qt.UserRole)
        try:
            contract_result = self.session.query(ContractSearch).filter(ContractSearch.contract_no == id).\
                filter(ContractSearch.person_role == 70).count()
            if  contract_result > 0:
                contract_result = self.session.query(ContractSearch).filter(ContractSearch.contract_no == id). \
                    filter(ContractSearch.person_role == 70).all()
            else:
                contract_result = self.session.query(ContractSearch).filter(ContractSearch.contract_no == id).all()
            contract_date = QDate.currentDate()
            for contract_result in contract_result:
                soum_code = contract_result.au2_code
                if soum_code:
                    aimag_code = soum_code[:3]
                    self.working_l1_cbox.setCurrentIndex(self.working_l1_cbox.findData(aimag_code))
                    self.working_l2_cbox.setCurrentIndex(self.working_l2_cbox.findData(soum_code))

                    if contract_result.contract_date:
                        contract_date = contract_result.contract_date
                    self.contract_num_edit.setText(str(contract_result.contract_no))
                    self.contract_date.setDate(contract_date)
                    self.contract_right_holder_num_edit.setText(contract_result.first_name)
                    self.personal_contract_edit.setText(contract_result.person_id)
                    self.contract_parcel_num_edit.setText(contract_result.parcel_id)
                    self.contract_decision_num_edit.setText(contract_result.decision_no)
                    self.contract_application_num_edit.setText(contract_result.app_no)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    @pyqtSlot(QTableWidgetItem)
    def on_record_results_twidget_itemClicked(self, item):

        id = item.data(Qt.UserRole)
        try:
            record_result = self.session.query(RecordSearch).filter(RecordSearch.record_no == id).one()
            record_no = ''
            soum_code = record_result.au2_code
            if soum_code:
                aimag_code = soum_code[:3]
                self.working_l1_cbox.setCurrentIndex(self.working_l1_cbox.findData(aimag_code))
                self.working_l2_cbox.setCurrentIndex(self.working_l2_cbox.findData(soum_code))
                if record_result.record_no is not None:
                    record_no = record_result.record_no

                self.record_record_num_edit.setText((record_no))
                self.record_date_edit.setDate(record_result.record_date)
                self.record_right_holder_edit.setText(record_result.first_name)
                self.personal_record_edit.setText(record_result.person_id)
                self.record_parcel_num_edit.setText(record_result.parcel_id)
                self.record_decision_num_edit.setText(record_result.decision_no)
                self.record_app_num_edit.setText(record_result.app_no)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    #Gt's Reports
    @pyqtSlot(int)
    def on_begin_year_sbox_valueChanged(self, sbox_value):

        self.end_date = (str(sbox_value + 1) + '-01-01')
        self.end_date = datetime.strptime(self.end_date, "%Y-%m-%d").date()

        self.before_date = (str(sbox_value) + '-01-01')
        self.before_date = datetime.strptime(self.before_date, "%Y-%m-%d").date()

    def __load_role_setting(self):

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        au2_count = 0
        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        au1_count = 0
        for au2 in au_level2_list:
            au2_count = au2_count + 1
        for au1 in au_level1_list:
            au1_count = au1_count + 1
        if au1_count > 1:
            self.work_level_lbl.setText(u'Улсын хэмжээнд ажиллах аймгын тоо:'+ str(au1_count))
        else:
            self.aimag_cbox.setDisabled(True)
            if au2_count > 1:
                self.work_level_lbl.setText(u'Аймгийн хэмжээнд ажиллах сум/дүүрэг-н тоо:'+ str(au2_count))
            else:
                self.work_level_lbl.setText(u'Зөвхөн нэг сум/дүүрэгт ажиллах эрхтэй')

    def __create_parcel_view_gts(self):

            au_level2_string = self.userSettings.restriction_au_level2
            au_level2_list = au_level2_string.split(",")
            sql = ""
            sql_gt1 = ""
            sql_conservation = ""
            sql_pollution = ""
            sql_fee_payment = ""
            sql_tax_payment = ""
            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql:
                    sql = "Create temp view parcel_report as" + "\n"
                else:
                    sql = sql + "UNION" + "\n"

                select = "SELECT parcel.parcel_id, parcel.area_m2, au1.code as au1_code,au2.code as au2_code, parcel.landuse,\
                                          application.app_type, app1_ext.excess_area,app_pers.share, person.person_id, \
                                          person.type as person_type, person.name, person.middle_name, person.first_name, \
                                          application.app_no, decision.decision_no, contract.contract_no, record.record_no, \
                                          record.record_date, record.right_type, contract.contract_date, parcel.valid_till, parcel.valid_from, \
                                          landuse.code2 as landuse_code2, record.status as record_status, contract.status as contract_status " \
                         "FROM s{0}.ca_parcel parcel " \
                         "LEFT JOIN s{0}.ct_application application on application.parcel = parcel.parcel_id " \
                         "LEFT JOIN s{0}.ct_application_person_role app_pers on application.app_no = app_pers.application " \
                         "LEFT JOIN base.bs_person person ON app_pers.person = person.person_id " \
                         "LEFT JOIN s{0}.ct_contract_application_role con_app on con_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_contract contract on con_app.contract = contract.contract_no " \
                         "LEFT JOIN s{0}.ct_record_application_role rec_app on rec_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_ownership_record record on rec_app.record = record.record_no " \
                         "LEFT JOIN s{0}.ct_decision_application dec_app on dec_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_decision decision on decision.decision_no = dec_app.application "\
                         "LEFT JOIN s{0}.ct_app1_ext app1_ext on application.app_no = app1_ext.app_no "\
                         "LEFT JOIN codelists.cl_landuse_type landuse on parcel.landuse = landuse.code "\
                         "LEFT JOIN admin_units.au_level1 au1 on ST_Within(parcel.geometry, au1.geometry) "\
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry)".format(au_level2)  + "\n"

                sql = sql + select

            sql = "{0} order by parcel_id;".format(sql)

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql_gt1:
                    sql_gt1 = "Create temp view parcel_gt1 as" + "\n"
                else:
                    sql_gt1 = sql_gt1 + "UNION" + "\n"

                select = "SELECT parcel.parcel_id, parcel.area_m2, au1.code as au1_code,au2.code as au2_code,parcel.valid_from, parcel.valid_till, parcel.landuse, landuse.code2 as landuse_code2, parcel.geometry " \
                         "FROM s{0}.ca_parcel parcel " \
                         "LEFT JOIN codelists.cl_landuse_type landuse on parcel.landuse = landuse.code "\
                         "LEFT JOIN admin_units.au_level1 au1 on ST_Within(parcel.geometry, au1.geometry) "\
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry)".format(au_level2)  + "\n"

                sql_gt1 = sql_gt1 + select

            sql_gt1 = "{0} order by parcel_id;".format(sql_gt1)

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql_conservation:
                    sql_conservation = "Create temp view parcel_conservation as" + "\n"
                else:
                    sql_conservation = sql_conservation + "UNION" + "\n"

                select = "SELECT parcel.gid, parcel.conservation, parcel.area_m2, parcel.polluted_area_m2, parcel.address_khashaa, parcel.address_streetname, \
                                  parcel.address_neighbourhood, parcel.valid_from, parcel.valid_till, parcel.geometry " \
                         "FROM s{0}.ca_parcel_conservation parcel " \
                         "LEFT JOIN admin_units.au_level1 au1 on ST_Within(parcel.geometry, au1.geometry) "\
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry)".format(au_level2)  + "\n"

                sql_conservation = sql_conservation + select

            sql_conservation = "{0} order by conservation;".format(sql_conservation)

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql_pollution:
                    sql_pollution = "Create temp view parcel_pollution as" + "\n"
                else:
                    sql_pollution = sql_pollution + "UNION" + "\n"

                select = "SELECT parcel.gid, parcel.pollution, parcel.area_m2, parcel.polluted_area_m2, parcel.address_khashaa, parcel.address_streetname, \
                                  parcel.address_neighbourhood, parcel.valid_from, parcel.valid_till, parcel.geometry " \
                         "FROM s{0}.ca_parcel_pollution parcel " \
                         "LEFT JOIN admin_units.au_level1 au1 on ST_Within(parcel.geometry, au1.geometry) "\
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry)".format(au_level2)  + "\n"

                sql_pollution = sql_pollution + select

            sql_pollution = "{0} order by pollution;".format(sql_pollution)

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql_fee_payment:
                    sql_fee_payment = "Create temp view parcel_fee as" + "\n"
                else:
                    sql_fee_payment = sql_fee_payment + "UNION" + "\n"

                select = "SELECT fee_payment.id,parcel.parcel_id, parcel.area_m2, au1.code as au1_code,au2.code as au2_code, parcel.landuse,\
                                          application.app_type, \
                                          application.app_no, contract.contract_no, \
                                          fee.area as fee_area, fee.subsidized_area, fee.fee_contract, fee_payment.amount_paid, \
                                          contract.contract_date, parcel.valid_till, parcel.valid_from, \
                                          landuse.code2 as landuse_code2, contract.status as contract_status " \
                         "FROM s{0}.ca_parcel parcel " \
                         "LEFT JOIN s{0}.ct_application application on application.parcel = parcel.parcel_id " \
                         "LEFT JOIN s{0}.ct_application_person_role app_pers on application.app_no = app_pers.application " \
                         "LEFT JOIN s{0}.ct_contract_application_role con_app on con_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_contract contract on con_app.contract = contract.contract_no " \
                         "LEFT JOIN s{0}.ct_fee fee on contract.contract_no = fee.contract " \
                         "LEFT JOIN s{0}.ct_fee_payment fee_payment on fee.person = fee_payment.person " \
                         "LEFT JOIN codelists.cl_landuse_type landuse on parcel.landuse = landuse.code "\
                         "LEFT JOIN admin_units.au_level1 au1 on ST_Within(parcel.geometry, au1.geometry) "\
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry)".format(au_level2)  + "\n"

                sql_fee_payment = sql_fee_payment + select

            sql_fee_payment = "{0} group by parcel.parcel_id, parcel.area_m2, au1.code,au2.code, landuse,\
                                          app_type, id, \
                                          app_no, contract_no,\
                                          area, subsidized_area, fee_contract, amount_paid,\
                                          contract_date, valid_till, valid_from, \
                                          code2, status, left_to_pay_for_q1,left_to_pay_for_q2,left_to_pay_for_q3,left_to_pay_for_q4;".format(sql_fee_payment)

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql_tax_payment:
                    sql_tax_payment = "Create temp view parcel_tax as" + "\n"
                else:
                    sql_tax_payment = sql_tax_payment + "UNION" + "\n"

                select = "SELECT tax_payment.id,parcel.parcel_id, parcel.area_m2, au1.code as au1_code,au2.code as au2_code, parcel.landuse,\
                                          application.app_type, \
                                          application.app_no, record.record_no, \
                                          tax.area as tax_area, tax.subsidized_area, tax.land_tax, tax_payment.amount_paid, \
                                          record.record_date, parcel.valid_till, parcel.valid_from, \
                                          landuse.code2 as landuse_code2, record.status as record_status " \
                         "FROM s{0}.ca_parcel parcel " \
                         "LEFT JOIN s{0}.ct_application application on application.parcel = parcel.parcel_id " \
                         "LEFT JOIN s{0}.ct_application_person_role app_pers on application.app_no = app_pers.application " \
                         "LEFT JOIN s{0}.ct_record_application_role rec_app on rec_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_ownership_record record on rec_app.record = record.record_no " \
                         "LEFT JOIN s{0}.ct_tax_and_price tax on record.record_no = tax.record " \
                         "LEFT JOIN s{0}.ct_tax_and_price_payment tax_payment on tax.person = tax_payment.person " \
                         "LEFT JOIN codelists.cl_landuse_type landuse on parcel.landuse = landuse.code "\
                         "LEFT JOIN admin_units.au_level1 au1 on ST_Within(parcel.geometry, au1.geometry) "\
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry)".format(au_level2)  + "\n"

                sql_tax_payment = sql_tax_payment + select

            sql_tax_payment = "{0} group by parcel.parcel_id, parcel.area_m2, au1.code,au2.code, landuse,\
                                          app_type, id, \
                                          app_no, record_no,\
                                          area, subsidized_area, land_tax, amount_paid,\
                                          record_date, valid_till, valid_from, \
                                          code2, status, left_to_pay_for_q1,left_to_pay_for_q2,left_to_pay_for_q3,left_to_pay_for_q4;".format(sql_tax_payment)

            try:
                self.session.execute(sql)
                self.session.execute(sql_gt1)
                self.session.execute(sql_conservation)
                self.session.execute(sql_pollution)
                self.session.execute(sql_fee_payment)
                self.session.execute(sql_tax_payment)
                self.commit()

            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
                return

    def __setup_combo_box(self):

        PluginUtils.populate_au_level1_cbox(self.aimag_cbox,True,True,False)

    def __report_gt_1(self):

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        au2_count = 0
        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        au1_count = 0
        for au2 in au_level2_list:
            au2_count = au2_count + 1
        for au1 in au_level1_list:
            au1_count = au1_count + 1

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_1.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_landscape()
        worksheet.set_paper(8)
        worksheet.set_margins(left=0.3, right=0.3, top=0.3, bottom=0.3)
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)

        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        row = 9
        count = 1
        code1 = 0
        code2 = 0


        worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 1 дүгээр хавсралт',format_header)
        worksheet.merge_range('K2:M2', u'/га-гаар/            Маягт ГТ-1 ',format_header)
        worksheet.merge_range('A4:A8', u'д/д', format)
        worksheet.merge_range('B4:B8', u'Аймаг/Нийслэл-сум/дүүрэг-н нэр',format)
        worksheet.merge_range('C4:C8', u'Нийт',format)
        worksheet.write(8,0, 0,format)
        worksheet.write(8,1, 1,format)
        worksheet.write(8,2, 2,format)

        landuse_type = self.session.query(ClLanduseType).order_by(ClLanduseType.code.asc()).all()
        worksheet.merge_range('D2:J2', u'ГАЗРЫН НЭГДМЭЛ САНГИЙН АНГИЛЛЫН '+str(self.begin_year_sbox.value())+u' ОНЫ ТАЙЛАН',format_header)
        # all aimags
        if len(au_level1_list) > 1:
            admin_unit_1 = self.session.query(AuLevel1)\
                        .filter(AuLevel1.code.in_(au_level1_list)).all()
        elif len(au_level1_list) == 1 or len(au_level2_list) >= 1:
            admin_unit_1 = self.session.query(AuLevel2)\
                        .filter(AuLevel2.code.in_(au_level2_list)).all()

            for au1 in admin_unit_1:
                area_level_2 = 0
                area_level_3 = 0
                all_area_landuse = 0
                col = 0
                column = col+2

                worksheet.write(row, col, (count),format)
                worksheet.write(row, col+1, au1.name,format)
                #landuse all area
                all_area = self.session.query(func.sum(ParcelGt1.area_m2).label("area"))\
                    .join(AuLevel1, ParcelGt1.geometry.ST_Within(AuLevel1.geometry))\
                    .join(AuLevel2, ParcelGt1.geometry.ST_Within(AuLevel2.geometry))\
                    .filter(ParcelGt1.valid_till == 'infinity')\
                    .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code))\
                    .filter(ParcelGt1.valid_from < self.end_date).one()

                if all_area.area == None:
                    area_level_1 = 0
                else:
                    area_level_1 = (all_area.area/10000)
                worksheet.write(row, col+2, (round(area_level_1,2)),format)

                column_count_1 = 0
                column_count_2 = 0
                all_landuse_count = 0
                for landuse in landuse_type:
                    if code1 == str(landuse.code)[:1]:
                        if code2 == str(landuse.code)[:2]:
                            column = column + 1
                            worksheet.write(8,column, column,format)
                            worksheet.write(7,column,landuse.description,format_90)
                            #

                            all_area = self.session.query(func.sum(ParcelGt1.area_m2).label("area"))\
                                .join(AuLevel1, ParcelGt1.geometry.ST_Within(AuLevel1.geometry))\
                                .join(AuLevel2, ParcelGt1.geometry.ST_Within(AuLevel2.geometry))\
                                .filter(ParcelGt1.landuse == landuse.code)\
                                .filter(ParcelGt1.valid_till == 'infinity')\
                                .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code))\
                                .filter(ParcelGt1.valid_from < self.end_date).one()
                            if all_area.area == None:
                                area_ga = 0
                            else:
                                area_ga = (all_area.area/10000)
                            worksheet.write(row, column, (round(area_ga,2)),format)
                            area_level_3 = area_level_3 + area_ga
                            area_level_2 = area_level_2 + area_ga
                            all_area_landuse = all_area_landuse + area_ga
                            all_landuse_count += 1
                            column_count_2 += 1
                            column_count_1 += 1
                        else:
                            code2 = 0
                            worksheet.write(row, column-column_count_2, (round(area_level_3,2)),format)
                            if column_count_2 > 1:
                                worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                            else:
                                worksheet.write(6,column, u"Үүнээс",format)
                            area_level_3 = 0
                            column_count_2 = 0

                        if code2 == 0:
                            code2 = str(landuse.code)[:2]
                            column = column + 1
                            worksheet.write(8,column, column,format)
                            worksheet.merge_range(6,column,7,column, landuse.description2,format_90)
                            column = column + 1
                            worksheet.write(8,column, column,format)
                            all_landuse_count += 1
                            column_count_1 += 1
                            worksheet.write(7,column,landuse.description,format_90)
                            all_area = self.session.query(func.sum(ParcelGt1.area_m2).label("area"))\
                                .join(AuLevel1, ParcelGt1.geometry.ST_Within(AuLevel1.geometry))\
                                .join(AuLevel2, ParcelGt1.geometry.ST_Within(AuLevel2.geometry))\
                                .filter(ParcelGt1.landuse == landuse.code)\
                                .filter(ParcelGt1.valid_till == 'infinity')\
                                .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code))\
                                .filter(ParcelGt1.valid_from < self.end_date).one()
                            if all_area.area == None:
                                area_ga = 0
                            else:
                                area_ga = (all_area.area/10000)
                            worksheet.write(row, column, (round(area_ga,1)),format)
                            area_level_3 = area_level_3 + area_ga
                            area_level_2 = area_level_2 + area_ga
                            all_area_landuse = all_area_landuse + area_ga
                            all_landuse_count += 1
                            column_count_2 += 1
                            column_count_1 += 1
                    else:
                        worksheet.write(row, column-column_count_1, (round(area_level_2,2)),format)
                        worksheet.merge_range(5,column-column_count_1+1,5,column, u"Үүнээс",format)
                        if code1 == '1':
                            worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_1,format)
                        elif code1 == '2':
                            worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_2,format)
                        elif code1 == '3':
                            worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_3,format)
                        elif code1 == '4':
                            worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_4,format)
                        elif code1 == '5':
                            worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_5,format)
                        elif code1 == '6':
                            worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_6,format)
                        code1 = 0
                        column_count_1 = 0
                        area_level_2 = 0

                        code2 = 0
                        worksheet.write(row, column-column_count_2, (round(area_level_3,2)),format)
                        if column_count_2 > 1:
                            worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                        else:
                            worksheet.write(6,column, u"Үүнээс",format)
                        area_level_3 = 0
                        column_count_2 = 0

                    if code1 == 0:
                        code1 = str(landuse.code)[:1]
                        code2 = str(landuse.code)[:2]
                        column = column + 1
                        worksheet.write(8,column, column,format)
                        worksheet.merge_range(5,column,7,column, u'Бүгд',format)
                        column = column + 1
                        worksheet.write(8,column, column,format)
                        all_landuse_count += 1
                        worksheet.merge_range(6,column,7,column, landuse.description2,format_90)
                        column_count_1 += 1
                        all_landuse_count += 1
                        column = column + 1
                        worksheet.write(8,column, column,format)
                        worksheet.write(7,column,landuse.description,format_90)
                        all_area = self.session.query(func.sum(ParcelGt1.area_m2).label("area"))\
                                .join(AuLevel1, ParcelGt1.geometry.ST_Within(AuLevel1.geometry))\
                                .join(AuLevel2, ParcelGt1.geometry.ST_Within(AuLevel2.geometry))\
                                .filter(ParcelGt1.landuse == landuse.code)\
                                .filter(ParcelGt1.valid_till == 'infinity')\
                                .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code))\
                                .filter(ParcelGt1.valid_from < self.end_date).one()
                        if all_area.area == None:
                            area_ga = 0
                        else:
                            area_ga = (all_area.area/10000)
                        worksheet.write(row, column, (round(area_ga,2)),format)
                        area_level_3 = area_level_3 + area_ga
                        area_level_2 = area_level_2 + area_ga
                        all_area_landuse = all_area_landuse + area_ga
                        all_landuse_count += 1
                        column_count_1 += 1
                        column_count_2 += 1
                code1 = 0
                worksheet.write(row, column-column_count_1, (round(area_level_2,2)),format)
                worksheet.merge_range(5,column-column_count_1+1,5,column, u"Үүнээс",format)
                worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_6,format)
                worksheet.merge_range(3,3,3,column, u"Үүнээс газрын ангиаллын төрлөөр",format)

                code2 = 0
                worksheet.write(row, column-column_count_2, (round(area_level_3,2)),format)
                if column_count_2 > 1:
                    worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                else:
                    worksheet.write(6,column, u"Үүнээс",format)
                worksheet.write(row, column-all_landuse_count, (round(all_area_landuse,2)),format)
                # cell = xl_rowcol_to_cell(row, column-all_landuse_count)
                # column = xl_col_to_name(column)

                value_p = self.progressBar.value() + 1
                self.progressBar.setValue(value_p)
                row += 1
                count +=1
            worksheet.merge_range(row,0,row,1,u"ДҮН",format)
            for i in range(2,column+1):
                cell_up = xl_rowcol_to_cell(9, i)
                cell_down = xl_rowcol_to_cell(row-1, i)
                worksheet.write(row,i,'=SUM('+cell_up+':'+cell_down+')',format)
                i = i + 1

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_1.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_2(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_2.xlsx")
        worksheet = workbook.add_worksheet()

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)
        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        col = 0
        column = col+4
        code1 = 0
        code2 = 0


        worksheet.merge_range('D2:J2', u'ГАЗРЫН НЭГДМЭЛ САНГИЙН ЭРХ ЗҮЙН БАЙДЛЫН '+str(self.begin_year_sbox.value())+u' ОНЫ ТАЙЛАН',format_header)
        worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 2 дугаар хавсралт',format_header)
        worksheet.merge_range('K2:M2', u'/га-гаар/            Маягт ГТ-2 ',format_header)
        worksheet.merge_range('A4:A8', u'д/д', format)
        worksheet.merge_range('B4:C8', u'Газар өмчлөгч, эзэмшигч, ашиглагч',format)
        worksheet.merge_range('D4:D8', u'д/д',format)
        worksheet.merge_range('E4:E8', u'Нийт',format)
        worksheet.write(8,0, u'А',format)
        worksheet.merge_range(8,1,8,2, u'Б',format)
        worksheet.write(8,3, 0,format)
        worksheet.write(8,4, 1,format)
        worksheet.merge_range('B10:B11', u'Өмчлөгч',format_90)
        worksheet.merge_range('B12:B15', u'Эзэмшигч',format_90)
        worksheet.merge_range('B16:B19', u'Бусдын эзэмшил газрыг ашиглагч Монгол улсын',format_90)
        worksheet.merge_range('B20:B22', u'Ашиглагч',format_90)
        worksheet.write('A10', 1,format)
        worksheet.write('A11', 2,format)
        worksheet.write('A12', 1,format)
        worksheet.write('A13', 2,format)
        worksheet.write('A14', 3,format)
        worksheet.write('A15', 4,format)
        worksheet.write('A16', 5,format)
        worksheet.write('A17', 6,format)
        worksheet.write('A18', 7,format)
        worksheet.write('A19', 8,format)
        worksheet.write('A20', 9,format)
        worksheet.write('A21', 10,format)
        worksheet.write('A22', 11,format)

        worksheet.write('C10', u'а/гэр бүлийн хэрэгцээнд',format)
        worksheet.write('C11', u'б/аж ахуйн зориулалтаар',format)
        worksheet.write('C12', u'а/иргэн',format)
        worksheet.write('C13', u'б/төрийн байгууллага',format)
        worksheet.write('C14', u'в/аж ахуйн нэгж',format)
        worksheet.write('C15', u'Дүн',format)
        worksheet.write('C16', u'а/иргэн',format)
        worksheet.write('C17', u'б/төрийн байгууллага',format)
        worksheet.write('C18', u'в/аж ахуйн нэгж',format)
        worksheet.write('C19', u'Дүн',format)
        worksheet.write('C20', u'а/гадаадын иргэн болон харъялалгүй хүн',format)
        worksheet.write('C21', u'б/гадаадын хөрөнгө оруулалтай аж ахуйн нэгж, гадаадын хуулийн этгээд',format)
        worksheet.write('C22', u'Дүн',format)
        worksheet.merge_range('A23:C23', u'Нийт дүн',format)

        worksheet.write('D10', 1,format)
        worksheet.write('D11', 2,format)
        worksheet.write('D12', 3,format)
        worksheet.write('D13', 4,format)
        worksheet.write('D14', 5,format)
        worksheet.write('D15', 6,format)
        worksheet.write('D16', 7,format)
        worksheet.write('D17', 8,format)
        worksheet.write('D18', 9,format)
        worksheet.write('D19', 10,format)
        worksheet.write('D20', 11,format)
        worksheet.write('D21', 12,format)
        worksheet.write('D22', 13,format)
        worksheet.write('D23', 14,format)

        landuse_type = self.session.query(ClLanduseType).order_by(ClLanduseType.code.asc()).all()
        column_count_1 = 0
        column_count_2 = 0
        all_landuse_count = 0
        column_number = 1
        landuse_all_1_level_1 = 0
        landuse_all_1_level_2 = 0
        landuse_all_1_level_3 = 0
        landuse_all_2_level_1 = 0
        landuse_all_2_level_2 = 0
        landuse_all_2_level_3 = 0
        landuse_all_3_level_1 = 0
        landuse_all_3_level_2 = 0
        landuse_all_3_level_3 = 0
        landuse_all_4_level_1 = 0
        landuse_all_4_level_2 = 0
        landuse_all_4_level_3 = 0
        landuse_all_5_level_1 = 0
        landuse_all_5_level_2 = 0
        landuse_all_5_level_3 = 0
        landuse_all_7_level_1 = 0
        landuse_all_7_level_2 = 0
        landuse_all_7_level_3 = 0
        landuse_all_8_level_1 = 0
        landuse_all_8_level_2 = 0
        landuse_all_8_level_3 = 0
        landuse_all_9_level_1 = 0
        landuse_all_9_level_2 = 0
        landuse_all_9_level_3 = 0
        landuse_all_11_level_1 = 0
        landuse_all_11_level_2 = 0
        landuse_all_11_level_3 = 0
        landuse_all_12_level_1 = 0
        landuse_all_12_level_2 = 0
        landuse_all_12_level_3 = 0

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        au2_count = 0
        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        au1_count = 0
        for au2 in au_level2_list:
            au2_count = au2_count + 1
        for au1 in au_level1_list:
            au1_count = au1_count + 1
        if au1_count > 1:
            self.work_level_lbl.setText(u'Улсын хэмжээнд ажиллах аймгын тоо:'+ str(au1_count))
        else:
            self.aimag_cbox.setDisabled(True)
            if au2_count > 1:
                self.work_level_lbl.setText(u'Аймаг/Нийслэлийн хэмжээнд ажиллах сум/дүүрэг-н тоо:'+ str(au2_count))
            else:
                self.work_level_lbl.setText(u'Зөвхөн нэг суманд ажиллах эрхтэй')

        progress_count = len(landuse_type)
        self.progressBar.setMaximum(progress_count)
        for landuse in landuse_type:
            area_ga = 0
            if code1 == str(landuse.code)[:1]:
                if code2 == str(landuse.code)[:2]:
                    column = column + 1
                    column_number = column_number + 1
                    worksheet.write(8,column, column_number,format)
                    worksheet.write(7,column,landuse.description,format_90)
                    #OWNERSHIP
                    #NO 1
                    landuse_area_1 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area"))\
                                    .filter(ParcelReport.app_type == 1)\
                                    .filter(ParcelReport.valid_till == 'infinity')\
                                    .filter(ParcelReport.record_date < self.end_date)\
                                    .filter(ParcelReport.record_status == 20)\
                                    .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                    .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_1.area == None or landuse_area_1.area == 0:
                        area_no_1 = ''
                    else:
                        area_no_1 = round((landuse_area_1.area/10000),2)
                    worksheet.write(9, column, area_no_1,format)
                    if area_no_1 == '':
                        area_no_1 = 0
                    landuse_all_1_level_1 = landuse_all_1_level_1 + area_no_1
                    landuse_all_1_level_2 = landuse_all_1_level_2 + area_no_1
                    landuse_all_1_level_3 = landuse_all_1_level_3 + area_no_1
                    #NO 2
                    landuse_area_2 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 4)\
                                    .filter(ParcelReport.valid_till == 'infinity')\
                                    .filter(ParcelReport.record_date < self.end_date)\
                                    .filter(ParcelReport.record_status == 20)\
                                    .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                    .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_2.area == None or landuse_area_1.area == 0:
                        area_no_2 = ''
                    else:
                        area_no_2 = round((landuse_area_2.area/10000),2)
                    worksheet.write(10, column, area_no_2,format)
                    if area_no_2 == '':
                        area_no_2 = 0
                    landuse_all_2_level_1 = landuse_all_2_level_1 + area_no_2
                    landuse_all_2_level_2 = landuse_all_2_level_2 + area_no_2
                    landuse_all_2_level_3 = landuse_all_2_level_3 + area_no_2
                    #POSSESS
                    #NO 3
                    landuse_area_3 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_3.area == None or landuse_area_3.area == 0:
                        area_no_3 = ''
                    else:
                        area_no_3 = round((landuse_area_3.area/10000),2)
                    worksheet.write(11, column, area_no_3,format)
                    if area_no_3 == '':
                        area_no_3 = 0
                    landuse_all_3_level_1 = landuse_all_3_level_1 + area_no_3
                    landuse_all_3_level_2 = landuse_all_3_level_2 + area_no_3
                    landuse_all_3_level_3 = landuse_all_3_level_3 + area_no_3
                    #NO 4
                    landuse_area_4 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_4.area == None or landuse_area_4.area == 0:
                        area_no_4 = ''
                    else:
                        area_no_4 = round((landuse_area_4.area/10000),2)
                    worksheet.write(12, column, area_no_4,format)
                    if area_no_4 == '':
                        area_no_4 = 0
                    landuse_all_4_level_1 = landuse_all_4_level_1 + area_no_4
                    landuse_all_4_level_2 = landuse_all_4_level_2 + area_no_4
                    landuse_all_4_level_3 = landuse_all_4_level_3 + area_no_4
                    #NO 5
                    landuse_area_5 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_5.area == None or landuse_area_5.area == 0:
                        area_no_5 = ''
                    else:
                        area_no_5 = round((landuse_area_5.area/10000),2)
                    worksheet.write(13, column, area_no_5,format)
                    if area_no_5 == '':
                        area_no_5 = 0
                    landuse_all_5_level_1 = landuse_all_5_level_1 + area_no_5
                    landuse_all_5_level_2 = landuse_all_5_level_2 + area_no_5
                    landuse_all_5_level_3 = landuse_all_5_level_3 + area_no_5
                    #NO 6 ALL
                    cell_up = xl_rowcol_to_cell(11, column)
                    cell_down = xl_rowcol_to_cell(13, column)
                    worksheet.write(14, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #POSSESSION RIGHT TO BE USED BY OTHERS
                    #NO 7
                    landuse_area_7 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_7.area == None or landuse_area_7.area == 0:
                        area_no_7 = ''
                    else:
                        area_no_7 = round((landuse_area_7.area/10000),2)
                    worksheet.write(15, column, area_no_7,format)
                    if area_no_7 == '':
                        area_no_7 = 0
                    landuse_all_7_level_1 = landuse_all_7_level_1 + area_no_7
                    landuse_all_7_level_2 = landuse_all_7_level_2 + area_no_7
                    landuse_all_7_level_3 = landuse_all_7_level_3 + area_no_7
                    #NO 8
                    landuse_area_8 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_8.area == None or landuse_area_8.area == 0:
                        area_no_8 = ''
                    else:
                        area_no_8 = round((landuse_area_8.area/10000),2)
                    worksheet.write(16, column, area_no_8,format)
                    if area_no_8 == '':
                        area_no_8 = 0
                    landuse_all_8_level_1 = landuse_all_8_level_1 + area_no_8
                    landuse_all_8_level_2 = landuse_all_8_level_2 + area_no_8
                    landuse_all_8_level_3 = landuse_all_8_level_3 + area_no_8
                    #NO 9
                    landuse_area_9 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_9.area == None or landuse_area_9.area == 0:
                        area_no_9 = ''
                    else:
                        area_no_9 = round((landuse_area_9.area/10000),2)
                    worksheet.write(17, column, area_no_9,format)
                    if area_no_9 == '':
                        area_no_9 = 0
                    landuse_all_9_level_1 = landuse_all_9_level_1 + area_no_9
                    landuse_all_9_level_2 = landuse_all_9_level_2 + area_no_9
                    landuse_all_9_level_3 = landuse_all_9_level_3 + area_no_9
                    #NO 10
                    cell_up = xl_rowcol_to_cell(15, column)
                    cell_down = xl_rowcol_to_cell(17, column)
                    worksheet.write(18, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #USE
                    #NO 11
                    landuse_area_11 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 50)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_11.area == None or landuse_area_11.area == 0:
                        area_no_11 = ''
                    else:
                        area_no_11 = round((landuse_area_11.area/10000),2)
                    worksheet.write(19, column, area_no_11,format)
                    if area_no_11 == '':
                        area_no_11 = 0
                    landuse_all_11_level_1 = landuse_all_11_level_1 + area_no_11
                    landuse_all_11_level_2 = landuse_all_11_level_2 + area_no_11
                    landuse_all_11_level_3 = landuse_all_11_level_3 + area_no_11
                    #NO 12
                    landuse_area_12 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 60)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_12.area == None or landuse_area_12.area == 0:
                        area_no_12 = ''
                    else:
                        area_no_12 = round((landuse_area_12.area/10000),2)
                    worksheet.write(20, column, area_no_12,format)
                    if area_no_12 == '':
                        area_no_12 = 0
                    landuse_all_12_level_1 = landuse_all_12_level_1 + area_no_12
                    landuse_all_12_level_2 = landuse_all_12_level_2 + area_no_12
                    landuse_all_12_level_3 = landuse_all_12_level_3 + area_no_12
                    #NO 13 USE ALL
                    cell_up = xl_rowcol_to_cell(19, column)
                    cell_down = xl_rowcol_to_cell(20, column)
                    worksheet.write(21, column, '=SUM('+cell_up+':'+cell_down+')',format)

                    #ALL AREA
                    cell_1 = xl_rowcol_to_cell(9, column)
                    cell_2 = xl_rowcol_to_cell(10, column)
                    cell_3 = xl_rowcol_to_cell(14, column)
                    cell_4 = xl_rowcol_to_cell(18, column)
                    cell_5 = xl_rowcol_to_cell(21, column)
                    worksheet.write_formula(22,column,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                    all_landuse_count += 1
                    column_count_2 += 1
                    column_count_1 += 1
                else:
                    code2 = 0
                    if column_count_2 > 1:
                        worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                    else:
                        worksheet.write(6,column, u"Үүнээс",format)
                    #OWNERSHIP
                    #NO 1
                    if landuse_all_1_level_2 == 0:
                        landuse_all_1_level_2 = ''
                    else:
                        landuse_all_1_level_2 = (round(landuse_all_1_level_2,2))
                    worksheet.write(9, column-column_count_2, landuse_all_1_level_2,format)
                    landuse_all_1_level_2 = 0
                    #NO 2
                    if landuse_all_2_level_2 == 0:
                        landuse_all_2_level_2 = ''
                    else:
                        landuse_all_2_level_2 = (round(landuse_all_2_level_2,2))
                    worksheet.write(10, column-column_count_2, landuse_all_2_level_2,format)
                    landuse_all_2_level_2 = 0
                    #POSSESS
                    #NO 3
                    if landuse_all_3_level_2 == 0:
                        landuse_all_3_level_2 = ''
                    else:
                        landuse_all_3_level_2 = (round(landuse_all_3_level_2,2))
                    worksheet.write(11, column-column_count_2, landuse_all_3_level_2,format)
                    landuse_all_3_level_2 = 0
                    #NO 4
                    if landuse_all_4_level_2 == 0:
                        landuse_all_4_level_2 = ''
                    else:
                        landuse_all_4_level_2 = (round(landuse_all_4_level_2,2))
                    worksheet.write(12, column-column_count_2, landuse_all_4_level_2,format)
                    landuse_all_4_level_2 = 0
                    #NO 5
                    if landuse_all_5_level_2 == 0:
                        landuse_all_5_level_2 = ''
                    else:
                        landuse_all_5_level_2 = (round(landuse_all_5_level_2,2))
                    worksheet.write(13, column-column_count_2, landuse_all_5_level_2,format)
                    landuse_all_5_level_2 = 0
                    #NO 6
                    cell_up = xl_rowcol_to_cell(11, column-column_count_2)
                    cell_down = xl_rowcol_to_cell(13, column-column_count_2)
                    worksheet.write(14,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                    #NO 7
                    if landuse_all_7_level_2 == 0:
                        landuse_all_7_level_2 = ''
                    else:
                        landuse_all_7_level_2 = (round(landuse_all_7_level_2,2))
                    worksheet.write(15, column-column_count_2, landuse_all_7_level_2,format)
                    landuse_all_7_level_2 = 0
                    #NO 8
                    if landuse_all_8_level_2 == 0:
                        landuse_all_8_level_2 = ''
                    else:
                        landuse_all_8_level_2 = (round(landuse_all_8_level_2,2))
                    worksheet.write(16, column-column_count_2, landuse_all_8_level_2,format)
                    landuse_all_8_level_2 = 0
                    #NO 9
                    if landuse_all_9_level_2 == 0:
                        landuse_all_9_level_2 = ''
                    else:
                        landuse_all_9_level_2 = (round(landuse_all_9_level_2,2))
                    worksheet.write(17, column-column_count_2, landuse_all_9_level_2,format)
                    landuse_all_9_level_2 = 0
                    #NO 10
                    cell_up = xl_rowcol_to_cell(15, column-column_count_2)
                    cell_down = xl_rowcol_to_cell(17, column-column_count_2)
                    worksheet.write(18,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                    #NO 11
                    if landuse_all_11_level_2 == 0:
                        landuse_all_11_level_2 = ''
                    else:
                        landuse_all_11_level_2 = (round(landuse_all_11_level_2,2))
                    worksheet.write(19, column-column_count_2, landuse_all_11_level_2,format)
                    landuse_all_11_level_2 = 0
                    #NO 12
                    if landuse_all_12_level_2 == 0:
                        landuse_all_12_level_2 = ''
                    else:
                        landuse_all_12_level_2 = (round(landuse_all_12_level_2,2))
                    worksheet.write(20, column-column_count_2, landuse_all_12_level_2,format)
                    landuse_all_12_level_2 = 0
                    #NO 13
                    cell_up = xl_rowcol_to_cell(19, column-column_count_2)
                    cell_down = xl_rowcol_to_cell(20, column-column_count_2)
                    worksheet.write(21,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                    #ALL AREA
                    cell_1 = xl_rowcol_to_cell(9, column-column_count_2)
                    cell_2 = xl_rowcol_to_cell(10, column-column_count_2)
                    cell_3 = xl_rowcol_to_cell(14, column-column_count_2)
                    cell_4 = xl_rowcol_to_cell(18, column-column_count_2)
                    cell_5 = xl_rowcol_to_cell(21, column-column_count_2)
                    worksheet.write_formula(22,column-column_count_2,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                    column_count_2 = 0

                if code2 == 0:
                    #COUNTS AND HEADER
                    code2 = str(landuse.code)[:2]
                    column = column + 1
                    column_number = column_number + 1
                    worksheet.write(8,column, column_number,format)
                    worksheet.merge_range(6,column,7,column, landuse.description2,format_90)
                    column = column + 1
                    column_number = column_number + 1
                    worksheet.write(8,column, column_number,format)
                    all_landuse_count += 1
                    column_count_1 += 1
                    worksheet.write(7,column,landuse.description,format_90)
                    #NO 1
                    landuse_area_1 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 1)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.record_date < self.end_date)\
                                .filter(ParcelReport.record_status == 20)\
                                .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_1.area == None or landuse_area_1.area == 0:
                        area_no_1 = ''
                    else:
                        area_no_1 = round((landuse_area_1.area/10000),2)
                    worksheet.write(9, column, area_no_1,format)
                    if area_no_1 == '':
                        area_no_1 = 0
                    landuse_all_1_level_1 = landuse_all_1_level_1 + area_no_1
                    landuse_all_1_level_2 = landuse_all_1_level_2 + area_no_1
                    landuse_all_1_level_3 = landuse_all_1_level_3 + area_no_1
                    #NO 2
                    landuse_area_2 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 4)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.record_date < self.end_date)\
                                .filter(ParcelReport.record_status == 20)\
                                .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_2.area == None or landuse_area_2.area == 0:
                        area_no_2 = ''
                    else:
                        area_no_2 = round((landuse_area_2.area/10000), 2)
                    worksheet.write(10, column, area_no_2,format)
                    if area_no_2 == '':
                        area_no_2 = 0
                    landuse_all_2_level_1 = landuse_all_2_level_1 + area_no_2
                    landuse_all_2_level_2 = landuse_all_2_level_2 + area_no_2
                    landuse_all_2_level_3 = landuse_all_2_level_3 + area_no_2

                    #POSSESS
                    #NO 3
                    landuse_area_3 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_3.area == None or landuse_area_3.area == 0:
                        area_no_3 = ''
                    else:
                        area_no_3 = round((landuse_area_3.area/10000),2)
                    worksheet.write(11, column, area_no_3,format)
                    if area_no_3 == '':
                        area_no_3 = 0
                    landuse_all_3_level_1 = landuse_all_3_level_1 + area_no_3
                    landuse_all_3_level_2 = landuse_all_3_level_2 + area_no_3
                    landuse_all_3_level_3 = landuse_all_3_level_3 + area_no_3
                    #NO 4
                    landuse_area_4 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_4.area == None or landuse_area_4.area == 0:
                        area_no_4 = ''
                    else:
                        area_no_4 = round((landuse_area_4.area/10000),2)
                    worksheet.write(12, column, area_no_4,format)
                    if area_no_4 == '':
                        area_no_4 = 0
                    landuse_all_4_level_1 = landuse_all_4_level_1 + area_no_4
                    landuse_all_4_level_2 = landuse_all_4_level_2 + area_no_4
                    landuse_all_4_level_3 = landuse_all_4_level_3 + area_no_4
                    #NO 5
                    landuse_area_5 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_5.area == None or landuse_area_5.area == 0:
                        area_no_5 = ''
                    else:
                        area_no_5 = round((landuse_area_5.area/10000),2)
                    worksheet.write(13, column, area_no_5,format)
                    if area_no_5 == '':
                        area_no_5 = 0
                    landuse_all_5_level_1 = landuse_all_5_level_1 + area_no_5
                    landuse_all_5_level_2 = landuse_all_5_level_2 + area_no_5
                    landuse_all_5_level_3 = landuse_all_5_level_3 + area_no_5
                    #NO 6 ALL
                    cell_up = xl_rowcol_to_cell(11, column)
                    cell_down = xl_rowcol_to_cell(13, column)
                    worksheet.write(14, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #POSSESSION RIGHT TO BE USED BY OTHERS
                    #NO 7
                    landuse_area_7 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_7.area == None or landuse_area_7.area == 0:
                        area_no_7 = ''
                    else:
                        area_no_7 = round((landuse_area_7.area/10000),2)
                    worksheet.write(15, column, area_no_7,format)
                    if area_no_7 == '':
                        area_no_7 = 0
                    landuse_all_7_level_1 = landuse_all_7_level_1 + area_no_7
                    landuse_all_7_level_2 = landuse_all_7_level_2 + area_no_7
                    landuse_all_7_level_3 = landuse_all_7_level_3 + area_no_7
                    #NO 8
                    landuse_area_8 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_8.area == None or landuse_area_8.area == 0:
                        area_no_8 = ''
                    else:
                        area_no_8 = round((landuse_area_8.area/10000),2)
                    worksheet.write(16, column, area_no_8,format)
                    if area_no_8 == '':
                        area_no_8 = 0
                    landuse_all_8_level_1 = landuse_all_8_level_1 + area_no_8
                    landuse_all_8_level_2 = landuse_all_8_level_2 + area_no_8
                    landuse_all_8_level_3 = landuse_all_8_level_3 + area_no_8
                    #NO 9
                    landuse_area_9 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_9.area == None or landuse_area_9.area == 0:
                        area_no_9 = ''
                    else:
                        area_no_9 = round((landuse_area_9.area/10000),2)
                    worksheet.write(17, column, area_no_9,format)
                    if area_no_9 == '':
                        area_no_9 = 0
                    landuse_all_9_level_1 = landuse_all_9_level_1 + area_no_9
                    landuse_all_9_level_2 = landuse_all_9_level_2 + area_no_9
                    landuse_all_9_level_3 = landuse_all_9_level_3 + area_no_9
                    #NO 10
                    cell_up = xl_rowcol_to_cell(15, column)
                    cell_down = xl_rowcol_to_cell(17, column)
                    worksheet.write(18, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #USE
                    #NO 11
                    landuse_area_11 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 50)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_11.area == None or landuse_area_11.area == 0:
                        area_no_11 = ''
                    else:
                        area_no_11 = round((landuse_area_11.area/10000),2)
                    worksheet.write(19, column, area_no_11,format)
                    if area_no_11 == '':
                        area_no_11 = 0
                    landuse_all_11_level_1 = landuse_all_11_level_1 + area_no_11
                    landuse_all_11_level_2 = landuse_all_11_level_2 + area_no_11
                    landuse_all_11_level_3 = landuse_all_11_level_3 + area_no_11
                    #NO 12
                    landuse_area_12 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 60)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_12.area == None or landuse_area_12.area == 0:
                        area_no_12 = ''
                    else:
                        area_no_12 = round((landuse_area_12.area/10000),2)
                    worksheet.write(20, column, area_no_12,format)
                    if area_no_12 == '':
                        area_no_12 = 0
                    landuse_all_12_level_1 = landuse_all_12_level_1 + area_no_12
                    landuse_all_12_level_2 = landuse_all_12_level_2 + area_no_12
                    landuse_all_12_level_3 = landuse_all_12_level_3 + area_no_12
                    #NO 13 USE ALL
                    cell_up = xl_rowcol_to_cell(19, column)
                    cell_down = xl_rowcol_to_cell(20, column)
                    worksheet.write(21, column, '=SUM('+cell_up+':'+cell_down+')',format)

                    #ALL AREA
                    cell_1 = xl_rowcol_to_cell(9, column)
                    cell_2 = xl_rowcol_to_cell(10, column)
                    cell_3 = xl_rowcol_to_cell(14, column)
                    cell_4 = xl_rowcol_to_cell(18, column)
                    cell_5 = xl_rowcol_to_cell(21, column)
                    worksheet.write_formula(22,column,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)
                    #COUNTS
                    all_landuse_count += 1
                    column_count_2 += 1
                    column_count_1 += 1
            else:
                #HEADER
                worksheet.merge_range(5,column-column_count_1+1,5,column, u"Үүнээс",format)
                if code1 == '1':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_1,format)
                elif code1 == '2':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_2,format)
                elif code1 == '3':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_3,format)
                elif code1 == '4':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_4,format)
                elif code1 == '5':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_5,format)
                elif code1 == '6':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_6,format)
                if column_count_2 > 1:
                    worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                else:
                    worksheet.write(6,column, u"Үүнээс",format)
                #OWNERSHIP
                #NO 1
                if landuse_all_1_level_1 == 0:
                    landuse_all_1_level_1 = ''
                else:
                    landuse_all_1_level_1 = (round(landuse_all_1_level_1,2))
                worksheet.write(9, column-column_count_1, landuse_all_1_level_1,format)
                if landuse_all_1_level_2 == 0:
                    landuse_all_1_level_2 = ''
                else:
                    landuse_all_1_level_2 = (round(landuse_all_1_level_2,2))
                worksheet.write(9, column-column_count_2, landuse_all_1_level_2,format)
                landuse_all_1_level_1 = 0
                landuse_all_1_level_2 = 0
                #NO 2
                if landuse_all_2_level_1 == 0:
                    landuse_all_2_level_1 = ''
                else:
                    landuse_all_2_level_1 = (round(landuse_all_2_level_1,2))
                worksheet.write(10, column-column_count_1, landuse_all_2_level_1,format)
                if landuse_all_2_level_2 == 0:
                    landuse_all_2_level_2 = ''
                else:
                    landuse_all_2_level_2 = (round(landuse_all_2_level_2,2))
                worksheet.write(10, column-column_count_2, landuse_all_2_level_2,format)
                landuse_all_2_level_1 = 0
                landuse_all_2_level_2 = 0
                #POSSESS
                #NO 3
                if landuse_all_3_level_1 == 0:
                    landuse_all_3_level_1 = ''
                else:
                    landuse_all_3_level_1 = (round(landuse_all_3_level_1,2))
                worksheet.write(11, column-column_count_1, landuse_all_3_level_1,format)
                if landuse_all_3_level_2 == 0:
                    landuse_all_3_level_2 = ''
                else:
                    landuse_all_3_level_2 = (round(landuse_all_3_level_2,2))
                worksheet.write(11, column-column_count_2, landuse_all_3_level_2,format)
                landuse_all_3_level_1 = 0
                landuse_all_3_level_2 = 0
                #NO 4
                if landuse_all_4_level_1 == 0:
                    landuse_all_4_level_1 = ''
                else:
                    landuse_all_4_level_1 = (round(landuse_all_4_level_1,2))
                worksheet.write(12, column-column_count_1, landuse_all_4_level_1,format)
                if landuse_all_4_level_2 == 0:
                    landuse_all_4_level_2 = ''
                else:
                    landuse_all_4_level_2 = (round(landuse_all_4_level_2,2))
                worksheet.write(12, column-column_count_2, landuse_all_4_level_2,format)
                landuse_all_4_level_1 = 0
                landuse_all_4_level_2 = 0
                #NO 5
                if landuse_all_5_level_1 == 0:
                    landuse_all_5_level_1 = ''
                else:
                    landuse_all_5_level_1 = (round(landuse_all_5_level_1,2))
                worksheet.write(13, column-column_count_1, landuse_all_5_level_1,format)
                if landuse_all_5_level_2 == 0:
                    landuse_all_5_level_2 = ''
                else:
                    landuse_all_5_level_2 = (round(landuse_all_5_level_2,2))
                worksheet.write(13, column-column_count_2, landuse_all_5_level_2,format)
                landuse_all_5_level_1 = 0
                landuse_all_5_level_2 = 0
                #NO 6
                cell_up = xl_rowcol_to_cell(11, column-column_count_1)
                cell_down = xl_rowcol_to_cell(13, column-column_count_1)
                worksheet.write(14,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
                cell_up = xl_rowcol_to_cell(11, column-column_count_2)
                cell_down = xl_rowcol_to_cell(13, column-column_count_2)
                worksheet.write(14,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                #NO 7
                if landuse_all_7_level_1 == 0:
                    landuse_all_7_level_1 = ''
                else:
                    landuse_all_7_level_1 = (round(landuse_all_7_level_1,2))
                worksheet.write(15, column-column_count_1, landuse_all_7_level_1,format)
                if landuse_all_7_level_2 == 0:
                    landuse_all_7_level_2 = ''
                else:
                    landuse_all_7_level_2 = (round(landuse_all_7_level_2,2))
                worksheet.write(15, column-column_count_2, landuse_all_7_level_2,format)
                landuse_all_7_level_1 = 0
                landuse_all_7_level_2 = 0
                #NO 8
                if landuse_all_8_level_1 == 0:
                    landuse_all_8_level_1 = ''
                else:
                    landuse_all_8_level_1 = (round(landuse_all_8_level_1,2))
                worksheet.write(16, column-column_count_1, landuse_all_8_level_1,format)
                if landuse_all_8_level_2 == 0:
                    landuse_all_8_level_2 = ''
                else:
                    landuse_all_8_level_2 = (round(landuse_all_8_level_2,2))
                worksheet.write(16, column-column_count_2, landuse_all_8_level_2,format)
                landuse_all_8_level_1 = 0
                landuse_all_8_level_2 = 0
                #NO 9
                if landuse_all_9_level_1 == 0:
                    landuse_all_9_level_1 = ''
                else:
                    landuse_all_9_level_1 = (round(landuse_all_9_level_1,2))
                worksheet.write(17, column-column_count_1, landuse_all_9_level_1,format)
                if landuse_all_9_level_2 == 0:
                    landuse_all_9_level_2 = ''
                else:
                    landuse_all_9_level_2 = (round(landuse_all_9_level_2,2))
                worksheet.write(17, column-column_count_2, landuse_all_9_level_2,format)
                landuse_all_9_level_1 = 0
                landuse_all_9_level_2 = 0
                #NO 10
                cell_up = xl_rowcol_to_cell(15, column-column_count_1)
                cell_down = xl_rowcol_to_cell(17, column-column_count_1)
                worksheet.write(18,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
                cell_up = xl_rowcol_to_cell(15, column-column_count_2)
                cell_down = xl_rowcol_to_cell(17, column-column_count_2)
                worksheet.write(18,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                #NO 11
                if landuse_all_11_level_1 == 0:
                    landuse_all_11_level_1 = ''
                else:
                    landuse_all_11_level_1 = (round(landuse_all_11_level_1,2))
                worksheet.write(19, column-column_count_1, landuse_all_11_level_1,format)
                if landuse_all_11_level_2 == 0:
                    landuse_all_11_level_2 = ''
                else:
                    landuse_all_11_level_2 = (round(landuse_all_11_level_2,2))
                worksheet.write(19, column-column_count_2, landuse_all_11_level_2,format)
                landuse_all_11_level_1 = 0
                landuse_all_11_level_2 = 0
                #NO 12
                if landuse_all_12_level_1 == 0:
                    landuse_all_12_level_1 = ''
                else:
                    landuse_all_12_level_1 = (round(landuse_all_12_level_1,2))
                worksheet.write(20, column-column_count_1, landuse_all_12_level_1,format)
                if landuse_all_12_level_2 == 0:
                    landuse_all_12_level_2 = ''
                else:
                    landuse_all_12_level_2 = (round(landuse_all_12_level_2,2))
                worksheet.write(20, column-column_count_2, landuse_all_12_level_2,format)
                landuse_all_12_level_1 = 0
                landuse_all_12_level_2 = 0
                #NO 13
                cell_up = xl_rowcol_to_cell(19, column-column_count_1)
                cell_down = xl_rowcol_to_cell(20, column-column_count_1)
                worksheet.write(21,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
                cell_up = xl_rowcol_to_cell(19, column-column_count_2)
                cell_down = xl_rowcol_to_cell(20, column-column_count_2)
                worksheet.write(21,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)

                #ALL AREA
                cell_1 = xl_rowcol_to_cell(9, column-column_count_1)
                cell_2 = xl_rowcol_to_cell(10, column-column_count_1)
                cell_3 = xl_rowcol_to_cell(14, column-column_count_1)
                cell_4 = xl_rowcol_to_cell(18, column-column_count_1)
                cell_5 = xl_rowcol_to_cell(21, column-column_count_1)
                worksheet.write_formula(22,column-column_count_1,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                cell_1 = xl_rowcol_to_cell(9, column-column_count_2)
                cell_2 = xl_rowcol_to_cell(10, column-column_count_2)
                cell_3 = xl_rowcol_to_cell(14, column-column_count_2)
                cell_4 = xl_rowcol_to_cell(18, column-column_count_2)
                cell_5 = xl_rowcol_to_cell(21, column-column_count_2)
                worksheet.write_formula(22,column-column_count_2,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                code1 = 0
                code2 = 0
                column_count_1 = 0
                column_count_2 = 0

            if code1 == 0:
                code1 = str(landuse.code)[:1]
                code2 = str(landuse.code)[:2]
                #COUNTS AND HEADER
                column = column + 1
                column_number = column_number + 1
                worksheet.write(8,column, column_number,format)
                worksheet.merge_range(5,column,7,column, u'Бүгд',format)
                column = column + 1
                column_number = column_number + 1
                worksheet.write(8,column, column_number,format)
                all_landuse_count += 1
                worksheet.merge_range(6,column,7,column, landuse.description2,format_90)
                column_count_1 += 1
                all_landuse_count += 1
                column = column + 1
                column_number = column_number + 1
                worksheet.write(8,column, column_number,format)
                worksheet.write(7,column,landuse.description,format_90)

                #NO 1
                landuse_area_1 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 1)\
                            .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.record_date < self.end_date)\
                            .filter(ParcelReport.record_status == 20)\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_1.area == None or landuse_area_1.area == 0:
                    area_no_1 = ''
                else:
                    area_no_1 = round((landuse_area_1.area/10000),2)
                worksheet.write(9, column, area_no_1,format)
                if area_no_1 == '':
                    area_no_1 = 0
                landuse_all_1_level_1 = landuse_all_1_level_1 + area_no_1
                landuse_all_1_level_2 = landuse_all_1_level_2 + area_no_1
                landuse_all_1_level_3 = landuse_all_1_level_3 + area_no_1
                #NO 2
                landuse_area_2 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 4)\
                            .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.record_date < self.end_date)\
                            .filter(ParcelReport.record_status == 20)\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_2.area == None or landuse_area_2.area == 0:
                    area_no_2 = ''
                else:
                    area_no_2 = round((landuse_area_2.area/10000),2)
                worksheet.write(10, column, area_no_2,format)
                if area_no_2 == '':
                    area_no_2 = 0
                landuse_all_2_level_1 = landuse_all_2_level_1 + area_no_2
                landuse_all_2_level_2 = landuse_all_2_level_2 + area_no_2
                landuse_all_2_level_3 = landuse_all_2_level_3 + area_no_2
                #POSSESS
                #NO 3
                landuse_area_3 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                            ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                            ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                            .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_3.area == None or landuse_area_3.area == 0:
                    area_no_3 = ''
                else:
                    area_no_3 = round((landuse_area_3.area/10000),2)
                worksheet.write(11, column, area_no_3,format)
                if area_no_3 == '':
                    area_no_3 = 0
                landuse_all_3_level_1 = landuse_all_3_level_1 + area_no_3
                landuse_all_3_level_2 = landuse_all_3_level_2 + area_no_3
                landuse_all_3_level_3 = landuse_all_3_level_3 + area_no_3
                #NO 4
                landuse_area_4 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                            ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                            ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_4.area == None or landuse_area_4.area == 0:
                    area_no_4 = ''
                else:
                    area_no_4 = round((landuse_area_4.area/10000),2)
                worksheet.write(12, column, area_no_4,format)
                if area_no_4 == '':
                    area_no_4 = 0
                landuse_all_4_level_1 = landuse_all_4_level_1 + area_no_4
                landuse_all_4_level_2 = landuse_all_4_level_2 + area_no_4
                landuse_all_4_level_3 = landuse_all_4_level_3 + area_no_4
                #NO 5
                landuse_area_5 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                            ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                            ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_5.area == None or landuse_area_5.area == 0:
                    area_no_5 = ''
                else:
                    area_no_5 = round((landuse_area_5.area/10000),2)
                worksheet.write(13, column, area_no_5,format)
                if area_no_5 == '':
                    area_no_5 = 0
                landuse_all_5_level_1 = landuse_all_5_level_1 + area_no_5
                landuse_all_5_level_2 = landuse_all_5_level_2 + area_no_5
                landuse_all_5_level_3 = landuse_all_5_level_3 + area_no_5
                #NO 6 ALL
                cell_up = xl_rowcol_to_cell(11, column)
                cell_down = xl_rowcol_to_cell(13, column)
                worksheet.write(14, column, '=SUM('+cell_up+':'+cell_down+')',format)
                #POSSESSION RIGHT TO BE USED BY OTHERS
                #NO 7
                landuse_area_7 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                            .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_7.area == None or landuse_area_7.area == 0:
                    area_no_7 = ''
                else:
                    area_no_7 = round((landuse_area_7.area/10000),2)
                worksheet.write(15, column, area_no_7,format)
                if area_no_7 == '':
                    area_no_7 = 0
                landuse_all_7_level_1 = landuse_all_7_level_1 + area_no_7
                landuse_all_7_level_2 = landuse_all_7_level_2 + area_no_7
                landuse_all_7_level_3 = landuse_all_7_level_3 + area_no_7
                #NO 8
                landuse_area_8 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_8.area == None or landuse_area_8.area == 0:
                    area_no_8 = ''
                else:
                    area_no_8 = round((landuse_area_8.area/10000),2)
                worksheet.write(16, column, area_no_8,format)
                if area_no_8 == '':
                    area_no_8 = 0
                landuse_all_8_level_1 = landuse_all_8_level_1 + area_no_8
                landuse_all_8_level_2 = landuse_all_8_level_2 + area_no_8
                landuse_all_8_level_3 = landuse_all_8_level_3 + area_no_8
                #NO 9
                landuse_area_9 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_9.area == None or landuse_area_9.area == 0:
                    area_no_9 = ''
                else:
                    area_no_9 = round((landuse_area_9.area/10000),2)
                worksheet.write(17, column, area_no_9,format)
                if area_no_9 == '':
                    area_no_9 = 0
                landuse_all_9_level_1 = landuse_all_9_level_1 + area_no_9
                landuse_all_9_level_2 = landuse_all_9_level_2 + area_no_9
                landuse_all_9_level_3 = landuse_all_9_level_3 + area_no_9
                #NO 10
                cell_up = xl_rowcol_to_cell(15, column)
                cell_down = xl_rowcol_to_cell(17, column)
                worksheet.write(18,column,'=SUM('+cell_up+':'+cell_down+')',format)
                #USE
                #NO 11
                landuse_area_11 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 6)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 50)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_11.area == None or landuse_area_11.area == 0:
                    area_no_11 = ''
                else:
                    area_no_11 = round((landuse_area_11.area/10000),2)
                worksheet.write(19, column, area_no_11,format)
                if area_no_11 == '':
                    area_no_11 = 0
                landuse_all_11_level_1 = landuse_all_11_level_1 + area_no_11
                landuse_all_11_level_2 = landuse_all_11_level_2 + area_no_11
                landuse_all_11_level_3 = landuse_all_11_level_3 + area_no_11
                #NO 12
                landuse_area_12 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 6)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 60)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_12.area == None or landuse_area_12.area == 0:
                    area_no_12 = ''
                else:
                    area_no_12 = round((landuse_area_12.area/10000),2)
                worksheet.write(20, column, area_no_12,format)
                if area_no_12 == '':
                    area_no_12 = 0
                landuse_all_12_level_1 = landuse_all_12_level_1 + area_no_12
                landuse_all_12_level_2 = landuse_all_12_level_2 + area_no_12
                landuse_all_12_level_3 = landuse_all_12_level_3 + area_no_12
                #NO 13 USE ALL
                cell_up = xl_rowcol_to_cell(19, column)
                cell_down = xl_rowcol_to_cell(20, column)
                worksheet.write(21, column, '=SUM('+cell_up+':'+cell_down+')',format)

                #ALL AREA
                cell_1 = xl_rowcol_to_cell(9, column)
                cell_2 = xl_rowcol_to_cell(10, column)
                cell_3 = xl_rowcol_to_cell(14, column)
                cell_4 = xl_rowcol_to_cell(18, column)
                cell_5 = xl_rowcol_to_cell(21, column)
                worksheet.write_formula(22,column,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)
                #COUNTS
                all_landuse_count += 1
                column_count_1 += 1
                column_count_2 += 1

            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
        #HEADER
        worksheet.merge_range(5,column-column_count_1+1,5,column, u"Үүнээс",format)
        worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_6,format)
        worksheet.merge_range(3,5,3,column, u"Үүнээс газрын ангиаллын төрлөөр",format)
        if column_count_2 > 1:
            worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
        else:
            worksheet.write(6,column, u"Үүнээс",format)
        #OWNERSHIP
        #NO 1
        if landuse_all_1_level_1 == 0:
            landuse_all_1_level_1 = ''
        else:
            landuse_all_1_level_1 = (round(landuse_all_1_level_1,2))
        worksheet.write(9, column-column_count_1, landuse_all_1_level_1,format)
        if landuse_all_1_level_2 == 0:
            landuse_all_1_level_2 = ''
        else:
            landuse_all_1_level_2 = (round(landuse_all_1_level_2,2))
        worksheet.write(9, column-column_count_2, landuse_all_1_level_2,format)
        if landuse_all_1_level_3 == 0:
            landuse_all_1_level_3 = ''
        else:
            landuse_all_1_level_3 = (round(landuse_all_1_level_3,2))
        worksheet.write(9, column-all_landuse_count, landuse_all_1_level_3,format)
        #NO 2
        if landuse_all_2_level_1 == 0:
            landuse_all_2_level_1 = ''
        else:
            landuse_all_2_level_1 = (round(landuse_all_2_level_1,2))
        worksheet.write(10, column-column_count_1, landuse_all_2_level_1,format)
        if landuse_all_2_level_2 == 0:
            landuse_all_2_level_2 = ''
        else:
            landuse_all_2_level_2 = (round(landuse_all_2_level_2,2))
        worksheet.write(10, column-column_count_2, landuse_all_2_level_2,format)
        if landuse_all_2_level_3 == 0:
            landuse_all_2_level_3 = ''
        else:
            landuse_all_2_level_3 = (round(landuse_all_2_level_3,2))
        worksheet.write(10, column-all_landuse_count, landuse_all_2_level_3,format)
        #POSSESS
        #NO 3
        if landuse_all_3_level_1 == 0:
            landuse_all_3_level_1 = ''
        else:
            landuse_all_3_level_1 = (round(landuse_all_3_level_1,2))
        worksheet.write(11, column-column_count_1, landuse_all_3_level_1,format)
        if landuse_all_3_level_2 == 0:
            landuse_all_3_level_2 = ''
        else:
            landuse_all_3_level_2 = (round(landuse_all_3_level_2,2))
        worksheet.write(11, column-column_count_2, landuse_all_3_level_2,format)
        if landuse_all_3_level_3 == 0:
            landuse_all_3_level_3 = ''
        else:
            landuse_all_3_level_3 = (round(landuse_all_3_level_3,2))
        worksheet.write(11, column-all_landuse_count, landuse_all_3_level_3,format)
        #NO 4
        if landuse_all_4_level_1 == 0:
            landuse_all_4_level_1 = ''
        else:
            landuse_all_4_level_1 = (round(landuse_all_4_level_1,2))
        worksheet.write(12, column-column_count_1, landuse_all_4_level_1,format)
        if landuse_all_4_level_2 == 0:
            landuse_all_4_level_2 = ''
        else:
            landuse_all_4_level_2 = (round(landuse_all_4_level_2,2))
        worksheet.write(12, column-column_count_2, landuse_all_4_level_2,format)
        if landuse_all_4_level_3 == 0:
            landuse_all_4_level_3 = ''
        else:
            landuse_all_4_level_3 = (round(landuse_all_4_level_3,2))
        worksheet.write(12, column-all_landuse_count, landuse_all_4_level_3,format)
        #NO 5
        if landuse_all_5_level_1 == 0:
            landuse_all_5_level_1 = ''
        else:
            landuse_all_5_level_1 = (round(landuse_all_5_level_1,2))
        worksheet.write(13, column-column_count_1, landuse_all_5_level_1,format)
        if landuse_all_5_level_2 == 0:
            landuse_all_5_level_2 = ''
        else:
            landuse_all_5_level_2 = (round(landuse_all_5_level_2,2))
        worksheet.write(13, column-column_count_2, landuse_all_5_level_2,format)
        if landuse_all_5_level_3 == 0:
            landuse_all_5_level_3 = ''
        else:
            landuse_all_5_level_3 = (round(landuse_all_5_level_3,2))
        worksheet.write(13, column-all_landuse_count, landuse_all_5_level_3,format)
        #NO 6
        cell_up = xl_rowcol_to_cell(11, column-column_count_1)
        cell_down = xl_rowcol_to_cell(13, column-column_count_1)
        worksheet.write(14,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(11, column-column_count_2)
        cell_down = xl_rowcol_to_cell(13, column-column_count_2)
        worksheet.write(14,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(11, column-all_landuse_count)
        cell_down = xl_rowcol_to_cell(13, column-all_landuse_count)
        worksheet.write(14,column-all_landuse_count,'=SUM('+cell_up+':'+cell_down+')',format)
        #NO 7
        if landuse_all_7_level_1 == 0:
            landuse_all_7_level_1 = ''
        else:
            landuse_all_7_level_1 = (round(landuse_all_7_level_1,2))
        worksheet.write(15, column-column_count_1, landuse_all_7_level_1,format)
        if landuse_all_7_level_2 == 0:
            landuse_all_7_level_2 = ''
        else:
            landuse_all_7_level_2 = (round(landuse_all_7_level_2,2))
        worksheet.write(15, column-column_count_2, landuse_all_7_level_2,format)
        if landuse_all_7_level_3 == 0:
            landuse_all_7_level_3 = ''
        else:
            landuse_all_7_level_3 = (round(landuse_all_7_level_3,2))
        worksheet.write(15, column-all_landuse_count, landuse_all_7_level_3,format)
        #NO 8
        if landuse_all_8_level_1 == 0:
            landuse_all_8_level_1 = ''
        else:
            landuse_all_8_level_1 = (round(landuse_all_8_level_1,2))
        worksheet.write(16, column-column_count_1, landuse_all_8_level_1,format)
        if landuse_all_8_level_2 == 0:
            landuse_all_8_level_2 = ''
        else:
            landuse_all_8_level_2 = (round(landuse_all_8_level_2,2))
        worksheet.write(16, column-column_count_2, landuse_all_8_level_2,format)
        if landuse_all_8_level_3 == 0:
            landuse_all_8_level_3 = ''
        else:
            landuse_all_8_level_3 = (round(landuse_all_8_level_3,2))
        worksheet.write(16, column-all_landuse_count, landuse_all_8_level_3,format)
        #NO 9
        if landuse_all_9_level_1 == 0:
            landuse_all_9_level_1 = ''
        else:
            landuse_all_9_level_1 = (round(landuse_all_9_level_1,2))
        worksheet.write(17, column-column_count_1, landuse_all_9_level_1,format)
        if landuse_all_9_level_2 == 0:
            landuse_all_9_level_2 = ''
        else:
            landuse_all_9_level_2 = (round(landuse_all_9_level_2,2))
        worksheet.write(17, column-column_count_2, landuse_all_9_level_2,format)
        if landuse_all_9_level_3 == 0:
            landuse_all_9_level_3 = ''
        else:
            landuse_all_9_level_3 = (round(landuse_all_9_level_3,2))
        worksheet.write(17, column-all_landuse_count, landuse_all_9_level_3,format)
        #NO 10
        cell_up = xl_rowcol_to_cell(15, column-column_count_1)
        cell_down = xl_rowcol_to_cell(17, column-column_count_1)
        worksheet.write(18,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(15, column-column_count_2)
        cell_down = xl_rowcol_to_cell(17, column-column_count_2)
        worksheet.write(18,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(15, column-all_landuse_count)
        cell_down = xl_rowcol_to_cell(17, column-all_landuse_count)
        worksheet.write(18,column-all_landuse_count,'=SUM('+cell_up+':'+cell_down+')',format)
        #NO 11
        if landuse_all_11_level_1 == 0:
            landuse_all_11_level_1 = ''
        else:
            landuse_all_11_level_1 = (round(landuse_all_11_level_1,2))
        worksheet.write(19, column-column_count_1, landuse_all_11_level_1,format)
        if landuse_all_11_level_2 == 0:
            landuse_all_11_level_2 = ''
        else:
            landuse_all_11_level_2 = (round(landuse_all_11_level_2,2))
        worksheet.write(19, column-column_count_2, landuse_all_11_level_2,format)
        if landuse_all_11_level_3 == 0:
            landuse_all_11_level_3 = ''
        else:
            landuse_all_11_level_3 = (round(landuse_all_11_level_3,2))
        worksheet.write(19, column-all_landuse_count, landuse_all_11_level_3,format)
        #NO 12
        if landuse_all_12_level_1 == 0:
            landuse_all_12_level_1 = ''
        else:
            landuse_all_12_level_1 = (round(landuse_all_12_level_1,2))
        worksheet.write(20, column-column_count_1, landuse_all_12_level_1,format)
        if landuse_all_12_level_2 == 0:
            landuse_all_12_level_2 = ''
        else:
            landuse_all_12_level_2 = (round(landuse_all_12_level_2,2))
        worksheet.write(20, column-column_count_2, landuse_all_12_level_2,format)
        if landuse_all_12_level_3 == 0:
            landuse_all_12_level_3 = ''
        else:
            landuse_all_12_level_3 = (round(landuse_all_12_level_3,2))
        worksheet.write(20, column-all_landuse_count, landuse_all_12_level_3,format)
        #NO 13
        cell_up = xl_rowcol_to_cell(19, column-column_count_1)
        cell_down = xl_rowcol_to_cell(20, column-column_count_1)
        worksheet.write(21,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(19, column-column_count_2)
        cell_down = xl_rowcol_to_cell(20, column-column_count_2)
        worksheet.write(21,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(19, column-all_landuse_count)
        cell_down = xl_rowcol_to_cell(20, column-all_landuse_count)
        worksheet.write(21,column-all_landuse_count,'=SUM('+cell_up+':'+cell_down+')',format)

        #ALL AREA
        cell_1 = xl_rowcol_to_cell(9, column-column_count_1)
        cell_2 = xl_rowcol_to_cell(10, column-column_count_1)
        cell_3 = xl_rowcol_to_cell(14, column-column_count_1)
        cell_4 = xl_rowcol_to_cell(18, column-column_count_1)
        cell_5 = xl_rowcol_to_cell(21, column-column_count_1)
        worksheet.write_formula(22,column-column_count_1,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

        cell_1 = xl_rowcol_to_cell(9, column-column_count_2)
        cell_2 = xl_rowcol_to_cell(10, column-column_count_2)
        cell_3 = xl_rowcol_to_cell(14, column-column_count_2)
        cell_4 = xl_rowcol_to_cell(18, column-column_count_2)
        cell_5 = xl_rowcol_to_cell(21, column-column_count_2)
        worksheet.write_formula(22,column-column_count_2,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

        cell_1 = xl_rowcol_to_cell(9, column-all_landuse_count)
        cell_2 = xl_rowcol_to_cell(10, column-all_landuse_count)
        cell_3 = xl_rowcol_to_cell(14, column-all_landuse_count)
        cell_4 = xl_rowcol_to_cell(18, column-all_landuse_count)
        cell_5 = xl_rowcol_to_cell(21, column-all_landuse_count)
        worksheet.write_formula(22,column-all_landuse_count,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_2.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_3(self):

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return
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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_3.xlsx")
        worksheet = workbook.add_worksheet()

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)
        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        row = 9
        count = 1
        col = 0
        column = col+4
        code1 = 0
        code2 = 0

        worksheet.merge_range('D2:J2', u'ГАЗРЫН НЭГДМЭЛ САНГИЙН ЭРХ ЗҮЙН БАЙДЛЫН '+str(self.begin_year_sbox.value())+u' ОНЫ ТАЙЛАН',format_header)
        worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 3 дугаар хавсралт',format_header)
        worksheet.merge_range('K2:M2', u'/тоогоор/            Маягт ГТ-3 ',format_header)
        worksheet.merge_range('A4:A8', u'д/д', format)
        worksheet.merge_range('B4:C8', u'Газар өмчлөгч, эзэмшигч, ашиглагч',format)
        worksheet.merge_range('D4:D8', u'д/д',format)
        worksheet.merge_range('E4:E8', u'Нийт',format)
        worksheet.write(8,0, u'А',format)
        worksheet.merge_range(8,1,8,2, u'Б',format)
        worksheet.write(8,3, 0,format)
        worksheet.write(8,4, 1,format)
        worksheet.merge_range('B10:B11', u'Өмчлөгч',format_90)
        worksheet.merge_range('B12:B15', u'Эзэмшигч',format_90)
        worksheet.merge_range('B16:B19', u'Бусдын эзэмшил газрыг ашиглагч Монгол улсын',format_90)
        worksheet.merge_range('B20:B22', u'Ашиглагч',format_90)
        worksheet.write('A10', 1,format)
        worksheet.write('A11', 2,format)
        worksheet.write('A12', 1,format)
        worksheet.write('A13', 2,format)
        worksheet.write('A14', 3,format)
        worksheet.write('A15', 4,format)
        worksheet.write('A16', 5,format)
        worksheet.write('A17', 6,format)
        worksheet.write('A18', 7,format)
        worksheet.write('A19', 8,format)
        worksheet.write('A20', 9,format)
        worksheet.write('A21', 10,format)
        worksheet.write('A22', 11,format)

        worksheet.write('C10', u'а/гэр бүлийн хэрэгцээнд',format)
        worksheet.write('C11', u'б/аж ахуйн зориулалтаар',format)
        worksheet.write('C12', u'а/иргэн',format)
        worksheet.write('C13', u'б/төрийн байгууллага',format)
        worksheet.write('C14', u'в/аж ахуйн нэгж',format)
        worksheet.write('C15', u'Дүн',format)
        worksheet.write('C16', u'а/иргэн',format)
        worksheet.write('C17', u'б/төрийн байгууллага',format)
        worksheet.write('C18', u'в/аж ахуйн нэгж',format)
        worksheet.write('C19', u'Дүн',format)
        worksheet.write('C20', u'а/гадаадын иргэн болон харъялалгүй хүн',format)
        worksheet.write('C21', u'б/гадаадын хөрөнгө оруулалтай аж ахуйн нэгж, гадаадын хуулийн этгээд',format)
        worksheet.write('C22', u'Дүн',format)
        worksheet.write('C23', u'Нийт дүн',format)

        worksheet.write('D10', 1,format)
        worksheet.write('D11', 2,format)
        worksheet.write('D12', 3,format)
        worksheet.write('D13', 4,format)
        worksheet.write('D14', 5,format)
        worksheet.write('D15', 6,format)
        worksheet.write('D16', 7,format)
        worksheet.write('D17', 8,format)
        worksheet.write('D18', 9,format)
        worksheet.write('D19', 10,format)
        worksheet.write('D20', 11,format)
        worksheet.write('D21', 12,format)
        worksheet.write('D22', 13,format)
        worksheet.write('D23', 14,format)


        landuse_type = self.session.query(ClLanduseType).order_by(ClLanduseType.code.asc()).all()
        area_level_1 = 0
        area_level_2 = 0
        area_level_3 = 0
        column_count_1 = 0
        column_count_2 = 0
        all_landuse_count = 0
        all_area_landuse = 0
        column_number = 1
        area_no_1 = 0
        landuse_all_1_level_1 = 0
        landuse_all_1_level_2 = 0
        landuse_all_1_level_3 = 0
        area_no_2 = 0
        landuse_all_2_level_1 = 0
        landuse_all_2_level_2 = 0
        landuse_all_2_level_3 = 0
        area_no_3 = 0
        landuse_all_3_level_1 = 0
        landuse_all_3_level_2 = 0
        landuse_all_3_level_3 = 0
        area_no_4 = 0
        landuse_all_4_level_1 = 0
        landuse_all_4_level_2 = 0
        landuse_all_4_level_3 = 0
        area_no_5 = 0
        landuse_all_5_level_1 = 0
        landuse_all_5_level_2 = 0
        landuse_all_5_level_3 = 0
        area_no_6 = 0
        landuse_all_6_level_1 = 0
        landuse_all_6_level_2 = 0
        landuse_all_6_level_3 = 0
        area_no_7 = 0
        landuse_all_7_level_1 = 0
        landuse_all_7_level_2 = 0
        landuse_all_7_level_3 = 0
        area_no_8 = 0
        landuse_all_8_level_1 = 0
        landuse_all_8_level_2 = 0
        landuse_all_8_level_3 = 0
        area_no_9 = 0
        landuse_all_9_level_1 = 0
        landuse_all_9_level_2 = 0
        landuse_all_9_level_3 = 0
        area_no_10 = 0
        landuse_all_10_level_1 = 0
        landuse_all_10_level_2 = 0
        landuse_all_10_level_3 = 0
        area_no_11 = 0
        landuse_all_11_level_1 = 0
        landuse_all_11_level_2 = 0
        landuse_all_11_level_3 = 0
        area_no_12 = 0
        landuse_all_12_level_1 = 0
        landuse_all_12_level_2 = 0
        landuse_all_12_level_3 = 0
        area_no_13 = 0
        landuse_all_13_level_1 = 0
        landuse_all_13_level_2 = 0
        landuse_all_13_level_3 = 0

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        au2_count = 0
        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        au1_count = 0

        for au2 in au_level2_list:
            au2_count = au2_count + 1
        for au1 in au_level1_list:
            au1_count = au1_count + 1
        if au1_count > 1:
            self.work_level_lbl.setText(u'Улсын хэмжээнд ажиллах аймаг/нийслэлийн тоо:'+ str(au1_count))
            au_level2_string = '00000,00000'
        else:
            au_level1_string = '000,000'
            self.aimag_cbox.setDisabled(True)
            if au2_count > 1:
                self.work_level_lbl.setText(u'Аймаг/Нийслэлийн хэмжээнд ажиллах сум/дүүрэг-н тоо:'+ str(au2_count))
            else:
                self.work_level_lbl.setText(u'Зөвхөн нэг суманд ажиллах эрхтэй')

        progress_count = len(landuse_type)
        self.progressBar.setMaximum(progress_count)
        for landuse in landuse_type:
            area_ga = 0
            if code1 == str(landuse.code)[:1]:
                if code2 == str(landuse.code)[:2]:
                    column = column + 1
                    column_number = column_number + 1
                    worksheet.write(8,column, column_number,format)
                    worksheet.write(7,column,landuse.description,format_90)
                    #OWNERSHIP
                    #NO 1
                    landuse_area_1 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 1)\
                                    .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                    .filter(ParcelReport.valid_till == 'infinity')\
                                    .filter(ParcelReport.record_date < self.end_date)\
                                    .filter(ParcelReport.record_status == 20)\
                                    .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_1 == None or landuse_area_1 == 0:
                        area_no_1 = ''
                    else:
                        area_no_1 = round((landuse_area_1),2)
                    worksheet.write(9, column, area_no_1,format)
                    if area_no_1 == '':
                        area_no_1 = 0
                    landuse_all_1_level_1 = landuse_all_1_level_1 + area_no_1
                    landuse_all_1_level_2 = landuse_all_1_level_2 + area_no_1
                    landuse_all_1_level_3 = landuse_all_1_level_3 + area_no_1
                    #NO 2
                    landuse_area_2 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 4)\
                                    .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                    .filter(ParcelReport.valid_till == 'infinity')\
                                    .filter(ParcelReport.record_date < self.end_date)\
                                    .filter(ParcelReport.record_status == 20)\
                                    .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()

                    if landuse_area_2 == None or landuse_area_1 == 0:
                        area_no_2 = ''
                    else:
                        area_no_2 = round((landuse_area_2),2)
                    worksheet.write(10, column, area_no_2,format)
                    if area_no_2 == '':
                        area_no_2 = 0
                    landuse_all_2_level_1 = landuse_all_2_level_1 + area_no_2
                    landuse_all_2_level_2 = landuse_all_2_level_2 + area_no_2
                    landuse_all_2_level_3 = landuse_all_2_level_3 + area_no_2
                    #POSSESS
                    #NO 3
                    landuse_area_3 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_3 == None or landuse_area_3 == 0:
                        area_no_3 = ''
                    else:
                        area_no_3 = round((landuse_area_3),2)
                    worksheet.write(11, column, area_no_3,format)
                    if area_no_3 == '':
                        area_no_3 = 0
                    landuse_all_3_level_1 = landuse_all_3_level_1 + area_no_3
                    landuse_all_3_level_2 = landuse_all_3_level_2 + area_no_3
                    landuse_all_3_level_3 = landuse_all_3_level_3 + area_no_3
                    #NO 4
                    landuse_area_4 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_4 == None or landuse_area_4 == 0:
                        area_no_4 = ''
                    else:
                        area_no_4 = round((landuse_area_4),2)
                    worksheet.write(12, column, area_no_4,format)
                    if area_no_4 == '':
                        area_no_4 = 0
                    landuse_all_4_level_1 = landuse_all_4_level_1 + area_no_4
                    landuse_all_4_level_2 = landuse_all_4_level_2 + area_no_4
                    landuse_all_4_level_3 = landuse_all_4_level_3 + area_no_4
                    #NO 5
                    landuse_area_5 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_5 == None or landuse_area_5 == 0:
                        area_no_5 = ''
                    else:
                        area_no_5 = round((landuse_area_5),2)
                    worksheet.write(13, column, area_no_5,format)
                    if area_no_5 == '':
                        area_no_5 = 0
                    landuse_all_5_level_1 = landuse_all_5_level_1 + area_no_5
                    landuse_all_5_level_2 = landuse_all_5_level_2 + area_no_5
                    landuse_all_5_level_3 = landuse_all_5_level_3 + area_no_5
                    #NO 6 ALL
                    cell_up = xl_rowcol_to_cell(11, column)
                    cell_down = xl_rowcol_to_cell(13, column)
                    worksheet.write(14, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #POSSESSION RIGHT TO BE USED BY OTHERS
                    #NO 7
                    landuse_area_7 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_7 == None or landuse_area_7 == 0:
                        area_no_7 = ''
                    else:
                        area_no_7 = round((landuse_area_7),2)
                    worksheet.write(15, column, area_no_7,format)
                    if area_no_7 == '':
                        area_no_7 = 0
                    landuse_all_7_level_1 = landuse_all_7_level_1 + area_no_7
                    landuse_all_7_level_2 = landuse_all_7_level_2 + area_no_7
                    landuse_all_7_level_3 = landuse_all_7_level_3 + area_no_7
                    #NO 8
                    landuse_area_8 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_8 == None or landuse_area_8 == 0:
                        area_no_8 = ''
                    else:
                        area_no_8 = round((landuse_area_8),2)
                    worksheet.write(16, column, area_no_8,format)
                    if area_no_8 == '':
                        area_no_8 = 0
                    landuse_all_8_level_1 = landuse_all_8_level_1 + area_no_8
                    landuse_all_8_level_2 = landuse_all_8_level_2 + area_no_8
                    landuse_all_8_level_3 = landuse_all_8_level_3 + area_no_8
                    #NO 9
                    landuse_area_9 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_9 == None or landuse_area_9 == 0:
                        area_no_9 = ''
                    else:
                        area_no_9 = round((landuse_area_9),2)
                    worksheet.write(17, column, area_no_9,format)
                    if area_no_9 == '':
                        area_no_9 = 0
                    landuse_all_9_level_1 = landuse_all_9_level_1 + area_no_9
                    landuse_all_9_level_2 = landuse_all_9_level_2 + area_no_9
                    landuse_all_9_level_3 = landuse_all_9_level_3 + area_no_9
                    #NO 10
                    cell_up = xl_rowcol_to_cell(15, column)
                    cell_down = xl_rowcol_to_cell(17, column)
                    worksheet.write(18, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #USE
                    #NO 11
                    landuse_area_11 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 50)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_11 == None or landuse_area_11 == 0:
                        area_no_11 = ''
                    else:
                        area_no_11 = round((landuse_area_11),2)
                    worksheet.write(19, column, area_no_11,format)
                    if area_no_11 == '':
                        area_no_11 = 0
                    landuse_all_11_level_1 = landuse_all_11_level_1 + area_no_11
                    landuse_all_11_level_2 = landuse_all_11_level_2 + area_no_11
                    landuse_all_11_level_3 = landuse_all_11_level_3 + area_no_11
                    #NO 12
                    landuse_area_12 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 60)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_12 == None or landuse_area_12 == 0:
                        area_no_12 = ''
                    else:
                        area_no_12 = round((landuse_area_12),2)
                    worksheet.write(20, column, area_no_12,format)
                    if area_no_12 == '':
                        area_no_12 = 0
                    landuse_all_12_level_1 = landuse_all_12_level_1 + area_no_12
                    landuse_all_12_level_2 = landuse_all_12_level_2 + area_no_12
                    landuse_all_12_level_3 = landuse_all_12_level_3 + area_no_12
                    #NO 13 USE ALL
                    cell_up = xl_rowcol_to_cell(19, column)
                    cell_down = xl_rowcol_to_cell(20, column)
                    worksheet.write(21, column, '=SUM('+cell_up+':'+cell_down+')',format)

                    #ALL AREA
                    cell_1 = xl_rowcol_to_cell(9, column)
                    cell_2 = xl_rowcol_to_cell(10, column)
                    cell_3 = xl_rowcol_to_cell(14, column)
                    cell_4 = xl_rowcol_to_cell(18, column)
                    cell_5 = xl_rowcol_to_cell(21, column)
                    worksheet.write_formula(22,column,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                    all_landuse_count += 1
                    column_count_2 += 1
                    column_count_1 += 1
                else:
                    code2 = 0
                    if column_count_2 > 1:
                        worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                    else:
                        worksheet.write(6,column, u"Үүнээс",format)
                    #OWNERSHIP
                    #NO 1
                    if landuse_all_1_level_2 == 0:
                        landuse_all_1_level_2 = ''
                    else:
                        landuse_all_1_level_2 = (round(landuse_all_1_level_2,2))
                    worksheet.write(9, column-column_count_2, landuse_all_1_level_2,format)
                    landuse_all_1_level_2 = 0
                    #NO 2
                    if landuse_all_2_level_2 == 0:
                        landuse_all_2_level_2 = ''
                    else:
                        landuse_all_2_level_2 = (round(landuse_all_2_level_2,2))
                    worksheet.write(10, column-column_count_2, landuse_all_2_level_2,format)
                    landuse_all_2_level_2 = 0
                    #POSSESS
                    #NO 3
                    if landuse_all_3_level_2 == 0:
                        landuse_all_3_level_2 = ''
                    else:
                        landuse_all_3_level_2 = (round(landuse_all_3_level_2,2))
                    worksheet.write(11, column-column_count_2, landuse_all_3_level_2,format)
                    landuse_all_3_level_2 = 0
                    #NO 4
                    if landuse_all_4_level_2 == 0:
                        landuse_all_4_level_2 = ''
                    else:
                        landuse_all_4_level_2 = (round(landuse_all_4_level_2,2))
                    worksheet.write(12, column-column_count_2, landuse_all_4_level_2,format)
                    landuse_all_4_level_2 = 0
                    #NO 5
                    if landuse_all_5_level_2 == 0:
                        landuse_all_5_level_2 = ''
                    else:
                        landuse_all_5_level_2 = (round(landuse_all_5_level_2,2))
                    worksheet.write(13, column-column_count_2, landuse_all_5_level_2,format)
                    landuse_all_5_level_2 = 0
                    #NO 6
                    cell_up = xl_rowcol_to_cell(11, column-column_count_2)
                    cell_down = xl_rowcol_to_cell(13, column-column_count_2)
                    worksheet.write(14,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                    #NO 7
                    if landuse_all_7_level_2 == 0:
                        landuse_all_7_level_2 = ''
                    else:
                        landuse_all_7_level_2 = (round(landuse_all_7_level_2,2))
                    worksheet.write(15, column-column_count_2, landuse_all_7_level_2,format)
                    landuse_all_7_level_2 = 0
                    #NO 8
                    if landuse_all_8_level_2 == 0:
                        landuse_all_8_level_2 = ''
                    else:
                        landuse_all_8_level_2 = (round(landuse_all_8_level_2,2))
                    worksheet.write(16, column-column_count_2, landuse_all_8_level_2,format)
                    landuse_all_8_level_2 = 0
                    #NO 9
                    if landuse_all_9_level_2 == 0:
                        landuse_all_9_level_2 = ''
                    else:
                        landuse_all_9_level_2 = (round(landuse_all_9_level_2,2))
                    worksheet.write(17, column-column_count_2, landuse_all_9_level_2,format)
                    landuse_all_9_level_2 = 0
                    #NO 10
                    cell_up = xl_rowcol_to_cell(15, column-column_count_2)
                    cell_down = xl_rowcol_to_cell(17, column-column_count_2)
                    worksheet.write(18,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                    #NO 11
                    if landuse_all_11_level_2 == 0:
                        landuse_all_11_level_2 = ''
                    else:
                        landuse_all_11_level_2 = (round(landuse_all_11_level_2,2))
                    worksheet.write(19, column-column_count_2, landuse_all_11_level_2,format)
                    landuse_all_11_level_2 = 0
                    #NO 12
                    if landuse_all_12_level_2 == 0:
                        landuse_all_12_level_2 = ''
                    else:
                        landuse_all_12_level_2 = (round(landuse_all_12_level_2,2))
                    worksheet.write(20, column-column_count_2, landuse_all_12_level_2,format)
                    landuse_all_12_level_2 = 0
                    #NO 13
                    cell_up = xl_rowcol_to_cell(19, column-column_count_2)
                    cell_down = xl_rowcol_to_cell(20, column-column_count_2)
                    worksheet.write(21,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                    #ALL AREA
                    cell_1 = xl_rowcol_to_cell(9, column-column_count_2)
                    cell_2 = xl_rowcol_to_cell(10, column-column_count_2)
                    cell_3 = xl_rowcol_to_cell(14, column-column_count_2)
                    cell_4 = xl_rowcol_to_cell(18, column-column_count_2)
                    cell_5 = xl_rowcol_to_cell(21, column-column_count_2)
                    worksheet.write_formula(22,column-column_count_2,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                    column_count_2 = 0

                if code2 == 0:
                    #COUNTS AND HEADER
                    code2 = str(landuse.code)[:2]
                    column = column + 1
                    column_number = column_number + 1
                    worksheet.write(8,column, column_number,format)
                    worksheet.merge_range(6,column,7,column, landuse.description2,format_90)
                    column = column + 1
                    column_number = column_number + 1
                    worksheet.write(8,column, column_number,format)
                    all_landuse_count += 1
                    column_count_1 += 1
                    worksheet.write(7,column,landuse.description,format_90)
                    #NO 1
                    landuse_area_1 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 1)\
                                .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.record_date < self.end_date)\
                                .filter(ParcelReport.record_status == 20)\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_1 == None or landuse_area_1 == 0:
                        area_no_1 = ''
                    else:
                        area_no_1 = round((landuse_area_1),2)
                    worksheet.write(9, column, area_no_1,format)
                    if area_no_1 == '':
                        area_no_1 = 0
                    landuse_all_1_level_1 = landuse_all_1_level_1 + area_no_1
                    landuse_all_1_level_2 = landuse_all_1_level_2 + area_no_1
                    landuse_all_1_level_3 = landuse_all_1_level_3 + area_no_1
                    #NO 2
                    landuse_area_2 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 4)\
                                .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.record_date < self.end_date)\
                                .filter(ParcelReport.record_status == 20)\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_2 == None or landuse_area_2 == 0:
                        area_no_2 = ''
                    else:
                        area_no_2 = round((landuse_area_2),2)
                    worksheet.write(10, column, area_no_2,format)
                    if area_no_2 == '':
                        area_no_2 = 0
                    landuse_all_2_level_1 = landuse_all_2_level_1 + area_no_2
                    landuse_all_2_level_2 = landuse_all_2_level_2 + area_no_2
                    landuse_all_2_level_3 = landuse_all_2_level_3 + area_no_2

                    #POSSESS
                    #NO 3
                    landuse_area_3 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_3 == None or landuse_area_3 == 0:
                        area_no_3 = ''
                    else:
                        area_no_3 = round((landuse_area_3),2)
                    worksheet.write(11, column, area_no_3,format)
                    if area_no_3 == '':
                        area_no_3 = 0
                    landuse_all_3_level_1 = landuse_all_3_level_1 + area_no_3
                    landuse_all_3_level_2 = landuse_all_3_level_2 + area_no_3
                    landuse_all_3_level_3 = landuse_all_3_level_3 + area_no_3
                    #NO 4
                    landuse_area_4 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_4 == None or landuse_area_4 == 0:
                        area_no_4 = ''
                    else:
                        area_no_4 = round((landuse_area_4),2)
                    worksheet.write(12, column, area_no_4,format)
                    if area_no_4 == '':
                        area_no_4 = 0
                    landuse_all_4_level_1 = landuse_all_4_level_1 + area_no_4
                    landuse_all_4_level_2 = landuse_all_4_level_2 + area_no_4
                    landuse_all_4_level_3 = landuse_all_4_level_3 + area_no_4
                    #NO 5
                    landuse_area_5 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_5 == None or landuse_area_5 == 0:
                        area_no_5 = ''
                    else:
                        area_no_5 = round((landuse_area_5),2)
                    worksheet.write(13, column, area_no_5,format)
                    if area_no_5 == '':
                        area_no_5 = 0
                    landuse_all_5_level_1 = landuse_all_5_level_1 + area_no_5
                    landuse_all_5_level_2 = landuse_all_5_level_2 + area_no_5
                    landuse_all_5_level_3 = landuse_all_5_level_3 + area_no_5
                    #NO 6 ALL
                    cell_up = xl_rowcol_to_cell(11, column)
                    cell_down = xl_rowcol_to_cell(13, column)
                    worksheet.write(14, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #POSSESSION RIGHT TO BE USED BY OTHERS
                    #NO 7
                    landuse_area_7 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_7 == None or landuse_area_7 == 0:
                        area_no_7 = ''
                    else:
                        area_no_7 = round((landuse_area_7),2)
                    worksheet.write(15, column, area_no_7,format)
                    if area_no_7 == '':
                        area_no_7 = 0
                    landuse_all_7_level_1 = landuse_all_7_level_1 + area_no_7
                    landuse_all_7_level_2 = landuse_all_7_level_2 + area_no_7
                    landuse_all_7_level_3 = landuse_all_7_level_3 + area_no_7
                    #NO 8
                    landuse_area_8 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_8 == None or landuse_area_8 == 0:
                        area_no_8 = ''
                    else:
                        area_no_8 = round((landuse_area_8),2)
                    worksheet.write(16, column, area_no_8,format)
                    if area_no_8 == '':
                        area_no_8 = 0
                    landuse_all_8_level_1 = landuse_all_8_level_1 + area_no_8
                    landuse_all_8_level_2 = landuse_all_8_level_2 + area_no_8
                    landuse_all_8_level_3 = landuse_all_8_level_3 + area_no_8
                    #NO 9
                    landuse_area_9 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_9 == None or landuse_area_9 == 0:
                        area_no_9 = ''
                    else:
                        area_no_9 = round((landuse_area_9),2)
                    worksheet.write(17, column, area_no_9,format)
                    if area_no_9 == '':
                        area_no_9 = 0
                    landuse_all_9_level_1 = landuse_all_9_level_1 + area_no_9
                    landuse_all_9_level_2 = landuse_all_9_level_2 + area_no_9
                    landuse_all_9_level_3 = landuse_all_9_level_3 + area_no_9
                    #NO 10
                    cell_up = xl_rowcol_to_cell(15, column)
                    cell_down = xl_rowcol_to_cell(17, column)
                    worksheet.write(18, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #USE
                    #NO 11
                    landuse_area_11 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 50)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_11 == None or landuse_area_11 == 0:
                        area_no_11 = ''
                    else:
                        area_no_11 = round((landuse_area_11),2)
                    worksheet.write(19, column, area_no_11,format)
                    if area_no_11 == '':
                        area_no_11 = 0
                    landuse_all_11_level_1 = landuse_all_11_level_1 + area_no_11
                    landuse_all_11_level_2 = landuse_all_11_level_2 + area_no_11
                    landuse_all_11_level_3 = landuse_all_11_level_3 + area_no_11
                    #NO 12
                    landuse_area_12 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 60)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_12 == None or landuse_area_12 == 0:
                        area_no_12 = ''
                    else:
                        area_no_12 = round((landuse_area_12),2)
                    worksheet.write(20, column, area_no_12,format)
                    if area_no_12 == '':
                        area_no_12 = 0
                    landuse_all_12_level_1 = landuse_all_12_level_1 + area_no_12
                    landuse_all_12_level_2 = landuse_all_12_level_2 + area_no_12
                    landuse_all_12_level_3 = landuse_all_12_level_3 + area_no_12
                    #NO 13 USE ALL
                    cell_up = xl_rowcol_to_cell(19, column)
                    cell_down = xl_rowcol_to_cell(20, column)
                    worksheet.write(21, column, '=SUM('+cell_up+':'+cell_down+')',format)

                    #ALL AREA
                    all_area = self.session.query((ParcelReport.parcel_id).label("area"))\
                                .filter(or_(ParcelReport.contract_no != None, ParcelReport.record_no != None)).filter(ParcelReport.landuse == landuse.code)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(or_(ParcelReport.contract_date < self.end_date,ParcelReport.record_date < self.end_date))\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30,ParcelReport.record_status == 20))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if all_area == None:
                        area_ga = 0
                    else:
                        area_ga = (all_area)
                    worksheet.write(22, column, (round(area_ga,1)),format)
                    area_level_3 = area_level_3 + area_ga
                    area_level_2 = area_level_2 + area_ga
                    all_area_landuse = all_area_landuse + area_ga
                    #COUNTS
                    all_landuse_count += 1
                    column_count_2 += 1
                    column_count_1 += 1
            else:
                #HEADER
                worksheet.merge_range(5,column-column_count_1+1,5,column, u"Үүнээс",format)
                if code1 == '1':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_1,format)
                elif code1 == '2':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_2,format)
                elif code1 == '3':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_3,format)
                elif code1 == '4':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_4,format)
                elif code1 == '5':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_5,format)
                elif code1 == '6':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_6,format)
                if column_count_2 > 1:
                    worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                else:
                    worksheet.write(6,column, u"Үүнээс",format)
                #OWNERSHIP
                #NO 1
                if landuse_all_1_level_1 == 0:
                    landuse_all_1_level_1 = ''
                else:
                    landuse_all_1_level_1 = (round(landuse_all_1_level_1,2))
                worksheet.write(9, column-column_count_1, landuse_all_1_level_1,format)
                if landuse_all_1_level_2 == 0:
                    landuse_all_1_level_2 = ''
                else:
                    landuse_all_1_level_2 = (round(landuse_all_1_level_2,2))
                worksheet.write(9, column-column_count_2, landuse_all_1_level_2,format)
                landuse_all_1_level_1 = 0
                landuse_all_1_level_2 = 0
                #NO 2
                if landuse_all_2_level_1 == 0:
                    landuse_all_2_level_1 = ''
                else:
                    landuse_all_2_level_1 = (round(landuse_all_2_level_1,2))
                worksheet.write(10, column-column_count_1, landuse_all_2_level_1,format)
                if landuse_all_2_level_2 == 0:
                    landuse_all_2_level_2 = ''
                else:
                    landuse_all_2_level_2 = (round(landuse_all_2_level_2,2))
                worksheet.write(10, column-column_count_2, landuse_all_2_level_2,format)
                landuse_all_2_level_1 = 0
                landuse_all_2_level_2 = 0
                #POSSESS
                #NO 3
                if landuse_all_3_level_1 == 0:
                    landuse_all_3_level_1 = ''
                else:
                    landuse_all_3_level_1 = (round(landuse_all_3_level_1,2))
                worksheet.write(11, column-column_count_1, landuse_all_3_level_1,format)
                if landuse_all_3_level_2 == 0:
                    landuse_all_3_level_2 = ''
                else:
                    landuse_all_3_level_2 = (round(landuse_all_3_level_2,2))
                worksheet.write(11, column-column_count_2, landuse_all_3_level_2,format)
                landuse_all_3_level_1 = 0
                landuse_all_3_level_2 = 0
                #NO 4
                if landuse_all_4_level_1 == 0:
                    landuse_all_4_level_1 = ''
                else:
                    landuse_all_4_level_1 = (round(landuse_all_4_level_1,2))
                worksheet.write(12, column-column_count_1, landuse_all_4_level_1,format)
                if landuse_all_4_level_2 == 0:
                    landuse_all_4_level_2 = ''
                else:
                    landuse_all_4_level_2 = (round(landuse_all_4_level_2,2))
                worksheet.write(12, column-column_count_2, landuse_all_4_level_2,format)
                landuse_all_4_level_1 = 0
                landuse_all_4_level_2 = 0
                #NO 5
                if landuse_all_5_level_1 == 0:
                    landuse_all_5_level_1 = ''
                else:
                    landuse_all_5_level_1 = (round(landuse_all_5_level_1,2))
                worksheet.write(13, column-column_count_1, landuse_all_5_level_1,format)
                if landuse_all_5_level_2 == 0:
                    landuse_all_5_level_2 = ''
                else:
                    landuse_all_5_level_2 = (round(landuse_all_5_level_2,2))
                worksheet.write(13, column-column_count_2, landuse_all_5_level_2,format)
                landuse_all_5_level_1 = 0
                landuse_all_5_level_2 = 0
                #NO 6
                cell_up = xl_rowcol_to_cell(11, column-column_count_1)
                cell_down = xl_rowcol_to_cell(13, column-column_count_1)
                worksheet.write(14,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
                cell_up = xl_rowcol_to_cell(11, column-column_count_2)
                cell_down = xl_rowcol_to_cell(13, column-column_count_2)
                worksheet.write(14,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                #NO 7
                if landuse_all_7_level_1 == 0:
                    landuse_all_7_level_1 = ''
                else:
                    landuse_all_7_level_1 = (round(landuse_all_7_level_1,2))
                worksheet.write(15, column-column_count_1, landuse_all_7_level_1,format)
                if landuse_all_7_level_2 == 0:
                    landuse_all_7_level_2 = ''
                else:
                    landuse_all_7_level_2 = (round(landuse_all_7_level_2,2))
                worksheet.write(15, column-column_count_2, landuse_all_7_level_2,format)
                landuse_all_7_level_1 = 0
                landuse_all_7_level_2 = 0
                #NO 8
                if landuse_all_8_level_1 == 0:
                    landuse_all_8_level_1 = ''
                else:
                    landuse_all_8_level_1 = (round(landuse_all_8_level_1,2))
                worksheet.write(16, column-column_count_1, landuse_all_8_level_1,format)
                if landuse_all_8_level_2 == 0:
                    landuse_all_8_level_2 = ''
                else:
                    landuse_all_8_level_2 = (round(landuse_all_8_level_2,2))
                worksheet.write(16, column-column_count_2, landuse_all_8_level_2,format)
                landuse_all_8_level_1 = 0
                landuse_all_8_level_2 = 0
                #NO 9
                if landuse_all_9_level_1 == 0:
                    landuse_all_9_level_1 = ''
                else:
                    landuse_all_9_level_1 = (round(landuse_all_9_level_1,2))
                worksheet.write(17, column-column_count_1, landuse_all_9_level_1,format)
                if landuse_all_9_level_2 == 0:
                    landuse_all_9_level_2 = ''
                else:
                    landuse_all_9_level_2 = (round(landuse_all_9_level_2,2))
                worksheet.write(17, column-column_count_2, landuse_all_9_level_2,format)
                landuse_all_9_level_1 = 0
                landuse_all_9_level_2 = 0
                #NO 10
                cell_up = xl_rowcol_to_cell(15, column-column_count_1)
                cell_down = xl_rowcol_to_cell(17, column-column_count_1)
                worksheet.write(18,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
                cell_up = xl_rowcol_to_cell(15, column-column_count_2)
                cell_down = xl_rowcol_to_cell(17, column-column_count_2)
                worksheet.write(18,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                #NO 11
                if landuse_all_11_level_1 == 0:
                    landuse_all_11_level_1 = ''
                else:
                    landuse_all_11_level_1 = (round(landuse_all_11_level_1,2))
                worksheet.write(19, column-column_count_1, landuse_all_11_level_1,format)
                if landuse_all_11_level_2 == 0:
                    landuse_all_11_level_2 = ''
                else:
                    landuse_all_11_level_2 = (round(landuse_all_11_level_2,2))
                worksheet.write(19, column-column_count_2, landuse_all_11_level_2,format)
                landuse_all_11_level_1 = 0
                landuse_all_11_level_2 = 0
                #NO 12
                if landuse_all_12_level_1 == 0:
                    landuse_all_12_level_1 = ''
                else:
                    landuse_all_12_level_1 = (round(landuse_all_12_level_1,2))
                worksheet.write(20, column-column_count_1, landuse_all_12_level_1,format)
                if landuse_all_12_level_2 == 0:
                    landuse_all_12_level_2 = ''
                else:
                    landuse_all_12_level_2 = (round(landuse_all_12_level_2,2))
                worksheet.write(20, column-column_count_2, landuse_all_12_level_2,format)
                landuse_all_12_level_1 = 0
                landuse_all_12_level_2 = 0
                #NO 13
                cell_up = xl_rowcol_to_cell(19, column-column_count_1)
                cell_down = xl_rowcol_to_cell(20, column-column_count_1)
                worksheet.write(21,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
                cell_up = xl_rowcol_to_cell(19, column-column_count_2)
                cell_down = xl_rowcol_to_cell(20, column-column_count_2)
                worksheet.write(21,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)

                #ALL AREA
                cell_1 = xl_rowcol_to_cell(9, column-column_count_1)
                cell_2 = xl_rowcol_to_cell(10, column-column_count_1)
                cell_3 = xl_rowcol_to_cell(14, column-column_count_1)
                cell_4 = xl_rowcol_to_cell(18, column-column_count_1)
                cell_5 = xl_rowcol_to_cell(21, column-column_count_1)
                worksheet.write_formula(22,column-column_count_1,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                cell_1 = xl_rowcol_to_cell(9, column-column_count_2)
                cell_2 = xl_rowcol_to_cell(10, column-column_count_2)
                cell_3 = xl_rowcol_to_cell(14, column-column_count_2)
                cell_4 = xl_rowcol_to_cell(18, column-column_count_2)
                cell_5 = xl_rowcol_to_cell(21, column-column_count_2)
                worksheet.write_formula(22,column-column_count_2,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                code1 = 0
                code2 = 0
                column_count_1 = 0
                column_count_2 = 0
                area_level_2 = 0
                area_level_3 = 0

            if code1 == 0:
                code1 = str(landuse.code)[:1]
                code2 = str(landuse.code)[:2]
                #COUNTS AND HEADER
                column = column + 1
                column_number = column_number + 1
                worksheet.write(8,column, column_number,format)
                worksheet.merge_range(5,column,7,column, u'Бүгд',format)
                column = column + 1
                column_number = column_number + 1
                worksheet.write(8,column, column_number,format)
                all_landuse_count += 1
                worksheet.merge_range(6,column,7,column, landuse.description2,format_90)
                column_count_1 += 1
                all_landuse_count += 1
                column = column + 1
                column_number = column_number + 1
                worksheet.write(8,column, column_number,format)
                worksheet.write(7,column,landuse.description,format_90)

                #NO 1
                landuse_area_1 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 1)\
                            .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.record_date < self.end_date)\
                            .filter(ParcelReport.record_status == 20)\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_1 == None or landuse_area_1 == 0:
                    area_no_1 = ''
                else:
                    area_no_1 = round((landuse_area_1),2)
                worksheet.write(9, column, area_no_1,format)
                if area_no_1 == '':
                    area_no_1 = 0
                landuse_all_1_level_1 = landuse_all_1_level_1 + area_no_1
                landuse_all_1_level_2 = landuse_all_1_level_2 + area_no_1
                landuse_all_1_level_3 = landuse_all_1_level_3 + area_no_1
                #NO 2
                landuse_area_2 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 4)\
                            .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.record_date < self.end_date)\
                            .filter(ParcelReport.record_status == 20)\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_2 == None or landuse_area_2 == 0:
                    area_no_2 = ''
                else:
                    area_no_2 = round((landuse_area_2))
                worksheet.write(10, column, area_no_2,format)
                if area_no_2 == '':
                    area_no_2 = 0
                landuse_all_2_level_1 = landuse_all_2_level_1 + area_no_2
                landuse_all_2_level_2 = landuse_all_2_level_2 + area_no_2
                landuse_all_2_level_3 = landuse_all_2_level_3 + area_no_2
                #POSSESS
                #NO 3
                landuse_area_3 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                            ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                            ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                            .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_3 == None or landuse_area_3 == 0:
                    area_no_3 = ''
                else:
                    area_no_3 = round((landuse_area_3),2)
                worksheet.write(11, column, area_no_3,format)
                if area_no_3 == '':
                    area_no_3 = 0
                landuse_all_3_level_1 = landuse_all_3_level_1 + area_no_3
                landuse_all_3_level_2 = landuse_all_3_level_2 + area_no_3
                landuse_all_3_level_3 = landuse_all_3_level_3 + area_no_3
                #NO 4
                landuse_area_4 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                            ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                            ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_4 == None or landuse_area_4 == 0:
                    area_no_4 = ''
                else:
                    area_no_4 = round((landuse_area_4),2)
                worksheet.write(12, column, area_no_4,format)
                if area_no_4 == '':
                    area_no_4 = 0
                landuse_all_4_level_1 = landuse_all_4_level_1 + area_no_4
                landuse_all_4_level_2 = landuse_all_4_level_2 + area_no_4
                landuse_all_4_level_3 = landuse_all_4_level_3 + area_no_4
                #NO 5
                landuse_area_5 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                            ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                            ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_5 == None or landuse_area_5 == 0:
                    area_no_5 = ''
                else:
                    area_no_5 = round((landuse_area_5),2)
                worksheet.write(13, column, area_no_5,format)
                if area_no_5 == '':
                    area_no_5 = 0
                landuse_all_5_level_1 = landuse_all_5_level_1 + area_no_5
                landuse_all_5_level_2 = landuse_all_5_level_2 + area_no_5
                landuse_all_5_level_3 = landuse_all_5_level_3 + area_no_5
                #NO 6 ALL
                cell_up = xl_rowcol_to_cell(11, column)
                cell_down = xl_rowcol_to_cell(13, column)
                worksheet.write(14, column, '=SUM('+cell_up+':'+cell_down+')',format)
                #POSSESSION RIGHT TO BE USED BY OTHERS
                #NO 7
                landuse_area_7 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                            .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_7 == None or landuse_area_7 == 0:
                    area_no_7 = ''
                else:
                    area_no_7 = round((landuse_area_7),2)
                worksheet.write(15, column, area_no_7,format)
                if area_no_7 == '':
                    area_no_7 = 0
                landuse_all_7_level_1 = landuse_all_7_level_1 + area_no_7
                landuse_all_7_level_2 = landuse_all_7_level_2 + area_no_7
                landuse_all_7_level_3 = landuse_all_7_level_3 + area_no_7
                #NO 8
                landuse_area_8 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_8 == None or landuse_area_8 == 0:
                    area_no_8 = ''
                else:
                    area_no_8 = round((landuse_area_8),2)
                worksheet.write(16, column, area_no_8,format)
                if area_no_8 == '':
                    area_no_8 = 0
                landuse_all_8_level_1 = landuse_all_8_level_1 + area_no_8
                landuse_all_8_level_2 = landuse_all_8_level_2 + area_no_8
                landuse_all_8_level_3 = landuse_all_8_level_3 + area_no_8
                #NO 9
                landuse_area_9 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_9 == None or landuse_area_9 == 0:
                    area_no_9 = ''
                else:
                    area_no_9 = round((landuse_area_9),2)
                worksheet.write(17, column, area_no_9,format)
                if area_no_9 == '':
                    area_no_9 = 0
                landuse_all_9_level_1 = landuse_all_9_level_1 + area_no_9
                landuse_all_9_level_2 = landuse_all_9_level_2 + area_no_9
                landuse_all_9_level_3 = landuse_all_9_level_3 + area_no_9
                #NO 10
                cell_up = xl_rowcol_to_cell(15, column)
                cell_down = xl_rowcol_to_cell(17, column)
                worksheet.write(18,column,'=SUM('+cell_up+':'+cell_down+')',format)
                #USE
                #NO 11
                landuse_area_11 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 6)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 50)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_11 == None or landuse_area_11 == 0:
                    area_no_11 = ''
                else:
                    area_no_11 = round((landuse_area_11),2)
                worksheet.write(19, column, area_no_11,format)
                if area_no_11 == '':
                    area_no_11 = 0
                landuse_all_11_level_1 = landuse_all_11_level_1 + area_no_11
                landuse_all_11_level_2 = landuse_all_11_level_2 + area_no_11
                landuse_all_11_level_3 = landuse_all_11_level_3 + area_no_11
                #NO 12
                landuse_area_12 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 6)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 60)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_12 == None or landuse_area_12 == 0:
                    area_no_12 = ''
                else:
                    area_no_12 = round((landuse_area_12),2)
                worksheet.write(20, column, area_no_12,format)
                if area_no_12 == '':
                    area_no_12 = 0
                landuse_all_12_level_1 = landuse_all_12_level_1 + area_no_12
                landuse_all_12_level_2 = landuse_all_12_level_2 + area_no_12
                landuse_all_12_level_3 = landuse_all_12_level_3 + area_no_12
                #NO 13 USE ALL
                cell_up = xl_rowcol_to_cell(19, column)
                cell_down = xl_rowcol_to_cell(20, column)
                worksheet.write(21, column, '=SUM('+cell_up+':'+cell_down+')',format)

                #ALL AREA
                cell_1 = xl_rowcol_to_cell(9, column)
                cell_2 = xl_rowcol_to_cell(10, column)
                cell_3 = xl_rowcol_to_cell(14, column)
                cell_4 = xl_rowcol_to_cell(18, column)
                cell_5 = xl_rowcol_to_cell(21, column)
                worksheet.write_formula(22,column,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)
                #COUNTS
                all_landuse_count += 1
                column_count_1 += 1
                column_count_2 += 1

            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
        #HEADER
        worksheet.merge_range(5,column-column_count_1+1,5,column, u"Үүнээс",format)
        worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_6,format)
        worksheet.merge_range(3,5,3,column, u"Үүнээс газрын ангиаллын төрлөөр",format)
        if column_count_2 > 1:
            worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
        else:
            worksheet.write(6,column, u"Үүнээс",format)
        #OWNERSHIP
        #NO 1
        if landuse_all_1_level_1 == 0:
            landuse_all_1_level_1 = ''
        else:
            landuse_all_1_level_1 = (round(landuse_all_1_level_1,2))
        worksheet.write(9, column-column_count_1, landuse_all_1_level_1,format)
        if landuse_all_1_level_2 == 0:
            landuse_all_1_level_2 = ''
        else:
            landuse_all_1_level_2 = (round(landuse_all_1_level_2,2))
        worksheet.write(9, column-column_count_2, landuse_all_1_level_2,format)
        if landuse_all_1_level_3 == 0:
            landuse_all_1_level_3 = ''
        else:
            landuse_all_1_level_3 = (round(landuse_all_1_level_3,2))
        worksheet.write(9, column-all_landuse_count, landuse_all_1_level_3,format)
        #NO 2
        if landuse_all_2_level_1 == 0:
            landuse_all_2_level_1 = ''
        else:
            landuse_all_2_level_1 = (round(landuse_all_2_level_1,2))
        worksheet.write(10, column-column_count_1, landuse_all_2_level_1,format)
        if landuse_all_2_level_2 == 0:
            landuse_all_2_level_2 = ''
        else:
            landuse_all_2_level_2 = (round(landuse_all_2_level_2,2))
        worksheet.write(10, column-column_count_2, landuse_all_2_level_2,format)
        if landuse_all_2_level_3 == 0:
            landuse_all_2_level_3 = ''
        else:
            landuse_all_2_level_3 = (round(landuse_all_2_level_3,2))
        worksheet.write(10, column-all_landuse_count, landuse_all_2_level_3,format)
        #POSSESS
        #NO 3
        if landuse_all_3_level_1 == 0:
            landuse_all_3_level_1 = ''
        else:
            landuse_all_3_level_1 = (round(landuse_all_3_level_1,2))
        worksheet.write(11, column-column_count_1, landuse_all_3_level_1,format)
        if landuse_all_3_level_2 == 0:
            landuse_all_3_level_2 = ''
        else:
            landuse_all_3_level_2 = (round(landuse_all_3_level_2,2))
        worksheet.write(11, column-column_count_2, landuse_all_3_level_2,format)
        if landuse_all_3_level_3 == 0:
            landuse_all_3_level_3 = ''
        else:
            landuse_all_3_level_3 = (round(landuse_all_3_level_3,2))
        worksheet.write(11, column-all_landuse_count, landuse_all_3_level_3,format)
        #NO 4
        if landuse_all_4_level_1 == 0:
            landuse_all_4_level_1 = ''
        else:
            landuse_all_4_level_1 = (round(landuse_all_4_level_1,2))
        worksheet.write(12, column-column_count_1, landuse_all_4_level_1,format)
        if landuse_all_4_level_2 == 0:
            landuse_all_4_level_2 = ''
        else:
            landuse_all_4_level_2 = (round(landuse_all_4_level_2,2))
        worksheet.write(12, column-column_count_2, landuse_all_4_level_2,format)
        if landuse_all_4_level_3 == 0:
            landuse_all_4_level_3 = ''
        else:
            landuse_all_4_level_3 = (round(landuse_all_4_level_3,2))
        worksheet.write(12, column-all_landuse_count, landuse_all_4_level_3,format)
        #NO 5
        if landuse_all_5_level_1 == 0:
            landuse_all_5_level_1 = ''
        else:
            landuse_all_5_level_1 = (round(landuse_all_5_level_1,2))
        worksheet.write(13, column-column_count_1, landuse_all_5_level_1,format)
        if landuse_all_5_level_2 == 0:
            landuse_all_5_level_2 = ''
        else:
            landuse_all_5_level_2 = (round(landuse_all_5_level_2,2))
        worksheet.write(13, column-column_count_2, landuse_all_5_level_2,format)
        if landuse_all_5_level_3 == 0:
            landuse_all_5_level_3 = ''
        else:
            landuse_all_5_level_3 = (round(landuse_all_5_level_3,2))
        worksheet.write(13, column-all_landuse_count, landuse_all_5_level_3,format)
        #NO 6
        cell_up = xl_rowcol_to_cell(11, column-column_count_1)
        cell_down = xl_rowcol_to_cell(13, column-column_count_1)
        worksheet.write(14,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(11, column-column_count_2)
        cell_down = xl_rowcol_to_cell(13, column-column_count_2)
        worksheet.write(14,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(11, column-all_landuse_count)
        cell_down = xl_rowcol_to_cell(13, column-all_landuse_count)
        worksheet.write(14,column-all_landuse_count,'=SUM('+cell_up+':'+cell_down+')',format)
        #NO 7
        if landuse_all_7_level_1 == 0:
            landuse_all_7_level_1 = ''
        else:
            landuse_all_7_level_1 = (round(landuse_all_7_level_1,2))
        worksheet.write(15, column-column_count_1, landuse_all_7_level_1,format)
        if landuse_all_7_level_2 == 0:
            landuse_all_7_level_2 = ''
        else:
            landuse_all_7_level_2 = (round(landuse_all_7_level_2,2))
        worksheet.write(15, column-column_count_2, landuse_all_7_level_2,format)
        if landuse_all_7_level_3 == 0:
            landuse_all_7_level_3 = ''
        else:
            landuse_all_7_level_3 = (round(landuse_all_7_level_3,2))
        worksheet.write(15, column-all_landuse_count, landuse_all_7_level_3,format)
        #NO 8
        if landuse_all_8_level_1 == 0:
            landuse_all_8_level_1 = ''
        else:
            landuse_all_8_level_1 = (round(landuse_all_8_level_1,2))
        worksheet.write(16, column-column_count_1, landuse_all_8_level_1,format)
        if landuse_all_8_level_2 == 0:
            landuse_all_8_level_2 = ''
        else:
            landuse_all_8_level_2 = (round(landuse_all_8_level_2,2))
        worksheet.write(16, column-column_count_2, landuse_all_8_level_2,format)
        if landuse_all_8_level_3 == 0:
            landuse_all_8_level_3 = ''
        else:
            landuse_all_8_level_3 = (round(landuse_all_8_level_3,2))
        worksheet.write(16, column-all_landuse_count, landuse_all_8_level_3,format)
        #NO 9
        if landuse_all_9_level_1 == 0:
            landuse_all_9_level_1 = ''
        else:
            landuse_all_9_level_1 = (round(landuse_all_9_level_1,2))
        worksheet.write(17, column-column_count_1, landuse_all_9_level_1,format)
        if landuse_all_9_level_2 == 0:
            landuse_all_9_level_2 = ''
        else:
            landuse_all_9_level_2 = (round(landuse_all_9_level_2,2))
        worksheet.write(17, column-column_count_2, landuse_all_9_level_2,format)
        if landuse_all_9_level_3 == 0:
            landuse_all_9_level_3 = ''
        else:
            landuse_all_9_level_3 = (round(landuse_all_9_level_3,2))
        worksheet.write(17, column-all_landuse_count, landuse_all_9_level_3,format)
        #NO 10
        cell_up = xl_rowcol_to_cell(15, column-column_count_1)
        cell_down = xl_rowcol_to_cell(17, column-column_count_1)
        worksheet.write(18,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(15, column-column_count_2)
        cell_down = xl_rowcol_to_cell(17, column-column_count_2)
        worksheet.write(18,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(15, column-all_landuse_count)
        cell_down = xl_rowcol_to_cell(17, column-all_landuse_count)
        worksheet.write(18,column-all_landuse_count,'=SUM('+cell_up+':'+cell_down+')',format)
        #NO 11
        if landuse_all_11_level_1 == 0:
            landuse_all_11_level_1 = ''
        else:
            landuse_all_11_level_1 = (round(landuse_all_11_level_1,2))
        worksheet.write(19, column-column_count_1, landuse_all_11_level_1,format)
        if landuse_all_11_level_2 == 0:
            landuse_all_11_level_2 = ''
        else:
            landuse_all_11_level_2 = (round(landuse_all_11_level_2,2))
        worksheet.write(19, column-column_count_2, landuse_all_11_level_2,format)
        if landuse_all_11_level_3 == 0:
            landuse_all_11_level_3 = ''
        else:
            landuse_all_11_level_3 = (round(landuse_all_11_level_3,2))
        worksheet.write(19, column-all_landuse_count, landuse_all_11_level_3,format)
        #NO 12
        if landuse_all_12_level_1 == 0:
            landuse_all_12_level_1 = ''
        else:
            landuse_all_12_level_1 = (round(landuse_all_12_level_1,2))
        worksheet.write(20, column-column_count_1, landuse_all_12_level_1,format)
        if landuse_all_12_level_2 == 0:
            landuse_all_12_level_2 = ''
        else:
            landuse_all_12_level_2 = (round(landuse_all_12_level_2,2))
        worksheet.write(20, column-column_count_2, landuse_all_12_level_2,format)
        if landuse_all_12_level_3 == 0:
            landuse_all_12_level_3 = ''
        else:
            landuse_all_12_level_3 = (round(landuse_all_12_level_3,2))
        worksheet.write(20, column-all_landuse_count, landuse_all_12_level_3,format)
        #NO 13
        cell_up = xl_rowcol_to_cell(19, column-column_count_1)
        cell_down = xl_rowcol_to_cell(20, column-column_count_1)
        worksheet.write(21,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(19, column-column_count_2)
        cell_down = xl_rowcol_to_cell(20, column-column_count_2)
        worksheet.write(21,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(19, column-all_landuse_count)
        cell_down = xl_rowcol_to_cell(20, column-all_landuse_count)
        worksheet.write(21,column-all_landuse_count,'=SUM('+cell_up+':'+cell_down+')',format)

        #ALL AREA
        cell_1 = xl_rowcol_to_cell(9, column-column_count_1)
        cell_2 = xl_rowcol_to_cell(10, column-column_count_1)
        cell_3 = xl_rowcol_to_cell(14, column-column_count_1)
        cell_4 = xl_rowcol_to_cell(18, column-column_count_1)
        cell_5 = xl_rowcol_to_cell(21, column-column_count_1)
        worksheet.write_formula(22,column-column_count_1,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

        cell_1 = xl_rowcol_to_cell(9, column-column_count_2)
        cell_2 = xl_rowcol_to_cell(10, column-column_count_2)
        cell_3 = xl_rowcol_to_cell(14, column-column_count_2)
        cell_4 = xl_rowcol_to_cell(18, column-column_count_2)
        cell_5 = xl_rowcol_to_cell(21, column-column_count_2)
        worksheet.write_formula(22,column-column_count_2,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

        cell_1 = xl_rowcol_to_cell(9, column-all_landuse_count)
        cell_2 = xl_rowcol_to_cell(10, column-all_landuse_count)
        cell_3 = xl_rowcol_to_cell(14, column-all_landuse_count)
        cell_4 = xl_rowcol_to_cell(18, column-all_landuse_count)
        cell_5 = xl_rowcol_to_cell(21, column-all_landuse_count)
        worksheet.write_formula(22,column-all_landuse_count,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_3.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_4(self):

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")

        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")

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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_4.xlsx")
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 3.5)
        worksheet.set_column('B:B', 45)

        worksheet.set_landscape()
        # worksheet.set_margins([left=0.7,] right=0.7,] top=0.75,] bottom=0.75]]])
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)
        format.set_border(1)
        format.set_shrink()

        format_left = workbook.add_format()
        format_left.set_text_wrap()
        format_left.set_align('justify')
        format_left.set_font_name('Times New Roman')
        format_left.set_font_size(8)
        format_left.set_border(1)
        format_left.set_shrink()

        format_right = workbook.add_format()
        format_right.set_text_wrap()
        format_right.set_align('right')
        format_right.set_font_name('Times New Roman')
        format_right.set_font_size(8)
        format_right.set_border(1)
        format_right.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        # format_header.set_align('right')
        format_header.set_align('vcenter')
        format_header.set_align('justify')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        format_bold = workbook.add_format()
        format_bold.set_text_wrap()
        format_bold.set_align('center')
        format_bold.set_align('vcenter')
        format_bold.set_font_name('Times New Roman')
        format_bold.set_font_size(8)
        format_bold.set_border(1)
        format_bold.set_shrink()
        format_bold.set_bold()

        row = 5
        col = 0
        count = 1
        code1 = 0
        code2 = 0

        worksheet.merge_range('B2:G2', u'УЛСЫН ТУСГАЙ ХЭРЭГЦЭЭНИЙ ГАЗРЫН '+str(self.begin_year_sbox.value())+u' ОНЫ ӨӨРЧЛӨЛТИЙН ТАЙЛАН',format_header)
        # worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        # worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 4 дүгээр хавсралт',format_header)
        if len(au_level1_list) == 1 and len(au_level2_list) == 1:
            worksheet.write('E3', u'/га/',format_header)
        else:
            worksheet.write('E3', u'/мян.га/',format_header)
        worksheet.write('A4', u'',format_bold)
        worksheet.write('B4', u'Газрын нэгдмэл сангийн ангилал',format_bold)
        worksheet.write('C4', u'Өмнөх он',format_bold)
        worksheet.write('D4', u'Тайлант он',format_bold)
        worksheet.write('E4', u'Өөрчлөлт',format_bold)
        worksheet.write('A5', u'VI', format_bold)
        worksheet.write('B5', u'Улсын тусгай хэрэгцээний газар',format_bold)

        try:
            landuse = self.session.query(ClLanduseType.code2,ClLanduseType.description2).filter(or_(ClLanduseType.code2 == 61,\
                                    ClLanduseType.code2 == 62,ClLanduseType.code2 == 63,ClLanduseType.code2 == 64,ClLanduseType.code2 == 65,\
                                    ClLanduseType.code2 == 66,ClLanduseType.code2 == 67,ClLanduseType.code2 == 68,ClLanduseType.code2 == 69))\
                                    .group_by(ClLanduseType.code2,ClLanduseType.description2).order_by(ClLanduseType.code2.asc()).all()

            for code2, desc2 in landuse:
                area_now = 0
                area_before = 0
                area_sub = 0
                worksheet.write(row, col,count,format)
                worksheet.write(row,col+1,desc2,format_left)

                landuse_area_before_year = self.session.query(func.sum(ParcelGt1.area_m2).label("area"))\
                                    .filter(ParcelGt1.landuse_code2 == code2)\
                                    .filter(ParcelGt1.valid_till == 'infinity')\
                                    .filter(ParcelGt1.valid_from < self.before_date)\
                                    .filter(or_(ParcelGt1.au1_code.in_(au_level1_list), ParcelGt1.au2_code.in_(au_level2_list))).one()
                if landuse_area_before_year.area == None or landuse_area_before_year.area == 0:
                    area_before = ''
                else:
                    if len(au_level1_list) == 1 and len(au_level2_list) == 1:
                        area_before = round(landuse_area_before_year.area/10000,1)
                    else:
                        area_before = round(landuse_area_before_year.area/10000000,1)

                worksheet.write(row, col+2,area_before,format_right)

                landuse_area_now = self.session.query(func.sum(ParcelGt1.area_m2).label("area"))\
                                    .filter(ParcelGt1.landuse_code2 == code2)\
                                    .filter(ParcelGt1.valid_till == 'infinity')\
                                    .filter(ParcelGt1.valid_from < self.end_date)\
                                    .filter(or_(ParcelGt1.au1_code.in_(au_level1_list), ParcelGt1.au2_code.in_(au_level2_list))).one()

                if landuse_area_now.area == None or landuse_area_now.area == 0:
                    area_now = ''
                else:
                    if len(au_level1_list) == 1 and len(au_level2_list) == 1:
                        area_now = round(landuse_area_now.area/10000,1)
                    else:
                        area_now = round(landuse_area_now.area/10000000,1)
                worksheet.write(row, col+3,area_now,format_right)

                if area_now == '' and area_before == '':
                    area_sub = ''
                else:
                    if area_now == '':
                        area_now = 0
                    if area_before == '':
                        area_before = 0
                    area_sub = area_now-area_before

                worksheet.write(row, col+4,area_sub,format_right)

                cell_up = xl_rowcol_to_cell(5, col+2)
                cell_down = xl_rowcol_to_cell(row, col+2)
                worksheet.write(4,col+2,'=SUM('+cell_up+':'+cell_down+')',format_right)

                cell_up = xl_rowcol_to_cell(5, col+3)
                cell_down = xl_rowcol_to_cell(row, col+3)
                worksheet.write(4,col+3,'=SUM('+cell_up+':'+cell_down+')',format_right)

                cell_up = xl_rowcol_to_cell(5, col+4)
                cell_down = xl_rowcol_to_cell(row, col+4)
                worksheet.write(4,col+4,'=SUM('+cell_up+':'+cell_down+')',format_right)

                row += 1
                count +=1

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_4.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_5(self):

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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_5.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_landscape()
        worksheet.set_column('B:B', 33.5)
        worksheet.set_row(0,50)
        worksheet.set_row(7,50)
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)

        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        # format_header.set_align('right')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        row = 9
        count = 1
        code1 = 0

        worksheet.merge_range('D2:J2', u'ГАЗРЫН ШИЛЖИЛТ ХӨДӨЛГӨӨНИЙ ТЭНЦЭЛ /'+str(self.begin_year_sbox.value())+u' он/',format_header)
        worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 5 дугаар хавсралт',format_header)
        worksheet.merge_range('K2:M2', u'/га-гаар/            Маягт ГТ-5 ',format_header)
        worksheet.merge_range('A4:A8', u'д/д', format)
        worksheet.merge_range('B4:B8', u'Газрын төрөл',format)
        worksheet.merge_range('C4:C8', u'Нийт',format)
        worksheet.write(8,0, 0,format)
        worksheet.write(8,1, 1,format)
        worksheet.write(8,2, 2,format)

        special_needs = self.session.query(ClLanduseType.code2,ClLanduseType.description2).group_by(ClLanduseType.code2,ClLanduseType.description2)\
                                                    .order_by(ClLanduseType.code2.asc()).all()

        progress_count = len(special_needs)
        self.progressBar.setMaximum(progress_count)

        for code2, desc2 in special_needs:
            col = 0
            column = col+2
            is_first = 0
            worksheet.write(row, col, (count),format)
            worksheet.write(row, col+1, desc2,format)
            column_count_1 = 0
            column_count_2 = 0
            all_landuse_count = 0
            for code_2, desc_2 in special_needs:
                if code1 == str(code_2)[:1]:
                    is_first = 1
                    worksheet.write(8,column, column,format)
                    worksheet.merge_range(6,column,7,column, desc_2,format_90)
                    column = column + 1
                    all_landuse_count += 1
                    column_count_2 += 1
                    column_count_1 += 1
                else:
                    if is_first == 1:

                        if column_count_1 > 1:
                            worksheet.merge_range(5,column-column_count_1,5,column-1, u"Үүнээс",format)
                        else:
                            worksheet.write(5,column-1, u"Үүнээс",format)
                        if code1 == '1':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_1,format)
                        elif code1 == '2':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_2,format)
                        elif code1 == '3':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_3,format)
                        elif code1 == '4':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_4,format)
                        elif code1 == '5':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_5,format)
                        elif code1 == '6':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_6,format)
                        code1 = 0
                        column_count_1 = 0
                        column_count_2 = 0
                if code1 == 0:
                    code1 = str(code_2)[:1]
                    if is_first == 0:
                        column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.merge_range(5,column,7,column, u'Бүгд',format)
                    column = column + 1
                    worksheet.write(8,column, column,format)
                    all_landuse_count += 1
                    worksheet.merge_range(6,column,7,column, desc_2,format_90)
                    all_landuse_count += 1
                    column = column + 1
                    column_count_1 += 1
                    column_count_2 += 1
            code1 = 0
            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_6,format)
            worksheet.merge_range(3,3,3,column-1, u"Үүнээс газрын ангиаллын төрлөөр",format)
            if column_count_1 > 1:
                worksheet.merge_range(5,column-column_count_1,5,column-1, u"Үүнээс",format)
            else:
                worksheet.write(5,column-1, u"Үүнээс",format)
            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
            row += 1
            count +=1
        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_5.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_6(self):

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
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_6.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_landscape()
        worksheet.set_column('A:A', 3.5)
        worksheet.set_column('B:B', 15)
        worksheet.set_row(1,50)
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)

        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        worksheet.merge_range('D4:J4', u'ГАЗАРТ УЧРУУЛСАН ХОХИРЛЫН '+str(self.begin_year_sbox.value())+u' ОНЫ ТАЙЛАН',format_header)
        worksheet.merge_range('A2:G2', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('J2:P2', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 6 дугаар хавсралт',format_header)
        worksheet.merge_range('J6:L6', u'/га-гаар/        Маягт ГТ-6 ',format_header)
        worksheet.merge_range('A8:A9', u'Д/д', format)
        worksheet.merge_range('B8:B9', u'Аймаг, нийслэл, сум, дүүргийн нэр',format)
        worksheet.merge_range('C8:C9', u'Хохирол учирсан нийт талбай, га',format)
        worksheet.write(9,0, 0,format)
        worksheet.write(9,1, u'А',format)
        worksheet.write(9,2, 1,format)

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")

        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        if len(au_level1_list) > 1:
            admin_unit_1 = self.session.query(AuLevel1)\
                        .filter(AuLevel1.code.in_(au_level1_list)).all()
        elif len(au_level1_list) == 1 or len(au_level2_list) >= 1:
            admin_unit_1 = self.session.query(AuLevel2)\
                        .filter(AuLevel2.code.in_(au_level2_list)).all()
        conservation_type = self.session.query(ClPollutionType).order_by(ClPollutionType.code.asc()).all()

        progress_count = len(admin_unit_1)
        self.progressBar.setMaximum(progress_count)
        col = 0
        row = 10
        count = 1
        code1 = 0

        for au1 in admin_unit_1:
            worksheet.write(row, col, (count),format)
            worksheet.write(row, col+1, au1.name,format)
            col = 0
            column = col+2
            column_count_2 = 0
            all_landuse_count = 0
            area_level_3 = 0
            all_area_landuse = 0
            is_first = 0
            for con in conservation_type:
                code2 = str(con.code)[:2]
                landuse_count = self.session.query(ClLanduseType.description2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2).count()
                if landuse_count != 0:
                    landuse = self.session.query(ClLanduseType.description2,ClLanduseType.code2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2,ClLanduseType.code2).one()
                    if code1 == str(landuse.code2)[:2]:
                        is_first = 1
                        column = column + 1
                        worksheet.write(8,column,con.description,format)
                        worksheet.write(9,column, column,format)

                        srid_list = self.session.query((((((func.ST_X(func.ST_Centroid(CaParcelPollution.geometry))+186)/6)))).label("srid"))\
                                        .join(ParcelGt1, CaParcelPollution.geometry.ST_Intersects(ParcelGt1.geometry))\
                                        .join(AuLevel1, CaParcelPollution.geometry.ST_Within(AuLevel1.geometry))\
                                        .join(AuLevel2, CaParcelPollution.geometry.ST_Within(AuLevel2.geometry))\
                                        .filter(CaParcelPollution.pollution == con.code)\
                                        .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()
                        srid = 0
                        for a in srid_list:
                            srid = 32600 + int(a.srid)

                        area = self.session.query(func.sum(func.ST_Area(func.ST_Intersection(func.ST_Transform(func.ST_SetSRID(CaParcelPollution.geometry,4326),srid), func.ST_Transform(func.ST_SetSRID(ParcelGt1.geometry,4326),srid)))).label("area"))\
                                        .join(ParcelGt1, CaParcelPollution.geometry.ST_Intersects(ParcelGt1.geometry))\
                                        .join(AuLevel1, CaParcelPollution.geometry.ST_Within(AuLevel1.geometry))\
                                        .join(AuLevel2, CaParcelPollution.geometry.ST_Within(AuLevel2.geometry))\
                                        .filter(CaParcelPollution.pollution == con.code)\
                                        .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()
                        conservation_area = 0
                        for a in area:
                            if a.area == None or a.area == 0:
                                conservation_area = ''
                            else:
                                conservation_area = str(a.area)
                                conservation_area = float(conservation_area)
                                conservation_area = round(conservation_area,2)
                        worksheet.write(row,column, conservation_area,format)
                        if conservation_area == '':
                            conservation_area = 0
                        area_level_3 = area_level_3 + conservation_area
                        all_area_landuse = all_area_landuse + conservation_area
                        column_count_2 += 1
                        all_landuse_count += 1
                    else:
                        if is_first == 1:
                            code1 = 0
                            if area_level_3 == 0:
                                area_level_3 = ''
                            else:
                                area_level_3 = (round(area_level_3,2))
                            worksheet.write(row, column-column_count_2, area_level_3,format)
                            if column_count_2 > 1:
                                worksheet.merge_range(7,column-column_count_2+1,7,column, u"Үүнээс",format)
                            else:
                                worksheet.write(7,column, u"Үүнээс",format)
                            area_level_3 = 0
                            column_count_2 = 0
                    if code1 == 0:

                        column = column + 1
                        code1 = str(landuse.code2)[:2]
                        code2 = str(landuse.code2)[:2]
                        landuse_count = self.session.query(ClLanduseType.description2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2).count()
                        if landuse_count != 0:
                            landuse = self.session.query(ClLanduseType.description2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2).one()
                            worksheet.merge_range(7,column,8,column,landuse.description2+u' ,бүгд',format)

                            worksheet.write(9,column, column,format)
                            column = column + 1
                            worksheet.write(8,column,con.description,format)
                            worksheet.write(9,column, column,format)

                            srid_list = self.session.query((((((func.ST_X(func.ST_Centroid(CaParcelPollution.geometry))+186)/6)))).label("srid"))\
                                        .join(ParcelGt1, CaParcelPollution.geometry.ST_Intersects(ParcelGt1.geometry))\
                                        .join(AuLevel1, CaParcelPollution.geometry.ST_Within(AuLevel1.geometry))\
                                        .join(AuLevel2, CaParcelPollution.geometry.ST_Within(AuLevel2.geometry))\
                                        .filter(CaParcelPollution.pollution == con.code)\
                                        .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()
                            srid = 0
                            for a in srid_list:
                                srid = 32600 + int(a.srid)
                            area = self.session.query(func.sum(func.ST_Area(func.ST_Intersection(func.ST_Transform(func.ST_SetSRID(CaParcelPollution.geometry,4326),srid), func.ST_Transform(func.ST_SetSRID(ParcelGt1.geometry,4326),srid)))).label("area"))\
                                            .join(ParcelGt1, CaParcelPollution.geometry.ST_Intersects(ParcelGt1.geometry))\
                                            .join(AuLevel1, CaParcelPollution.geometry.ST_Within(AuLevel1.geometry))\
                                            .join(AuLevel2, CaParcelPollution.geometry.ST_Within(AuLevel2.geometry))\
                                            .filter(CaParcelPollution.pollution == con.code)\
                                            .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()

                            conservation_area = 0
                            for a in area:
                                if a.area == None or a.area == 0:
                                    conservation_area = ''
                                else:
                                    conservation_area = str(a.area)
                                    conservation_area = float(conservation_area)
                                    conservation_area = round(conservation_area,2)
                            worksheet.write(row,column, conservation_area,format)
                            if conservation_area == '':
                                conservation_area = 0
                            area_level_3 = area_level_3 + conservation_area
                            all_area_landuse = all_area_landuse + conservation_area
                            column_count_2 += 1
                            all_landuse_count += 1
            code1 = 0
            if area_level_3 == 0:
                area_level_3 = ''
            else:
                area_level_3 = (round(area_level_3,2))
            worksheet.write(row, column-column_count_2, area_level_3,format)
            if column_count_2 > 1:
                worksheet.merge_range(7,column-column_count_2+1,7,column, u"Үүнээс",format)
            else:
                worksheet.write(7,column, u"Үүнээс",format)
            if all_area_landuse == 0:
                all_area_landuse = ''
            else:
                all_area_landuse = (round(all_area_landuse,2))
            worksheet.write(row, 2, all_area_landuse,format)
            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
            row += 1
            count +=1
        worksheet.merge_range(row,0,row,1,u"ДҮН",format)
        for i in range(2,column+1):
            cell_up = xl_rowcol_to_cell(10, i)
            cell_down = xl_rowcol_to_cell(row-1, i)
            worksheet.write(row,i,'=SUM('+cell_up+':'+cell_down+')',format)

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_6.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_7(self):

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
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_7.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_landscape()
        worksheet.set_column('A:A', 3.5)
        worksheet.set_column('B:B', 15)
        worksheet.set_row(1,50)
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)

        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        worksheet.merge_range('D4:J4', u'ГАЗАР ХАМГААЛАХ АРГА ХЭМЖЭЭНИЙ '+str(self.begin_year_sbox.value())+u' ОНЫ ТАЙЛАН',format_header)
        worksheet.merge_range('A2:G2', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('J2:P2', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 7 дугаар хавсралт',format_header)
        worksheet.merge_range('J6:L6', u'/га-гаар/        Маягт ГТ-7 ',format_header)
        worksheet.merge_range('A8:A9', u'Д/д', format)
        worksheet.merge_range('B8:B9', u'Аймаг, нийслэл, сум, дүүргийн нэр',format)
        worksheet.merge_range('C8:C9', u'Хамгаалах арга хэмжээ авсан нийт талбай, га',format)
        worksheet.write(9,0, 0,format)
        worksheet.write(9,1, u'А',format)
        worksheet.write(9,2, 1,format)

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")

        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        if len(au_level1_list) > 1:
            admin_unit_1 = self.session.query(AuLevel1)\
                        .filter(AuLevel1.code.in_(au_level1_list)).all()
        elif len(au_level1_list) == 1 or len(au_level2_list) >= 1:
            admin_unit_1 = self.session.query(AuLevel2)\
                        .filter(AuLevel2.code.in_(au_level2_list)).all()
        conservation_type = self.session.query(ClConservationType).order_by(ClConservationType.code.asc()).all()

        progress_count = len(admin_unit_1)
        self.progressBar.setMaximum(progress_count)
        col = 0
        row = 10
        count = 1
        code1 = 0

        for au1 in admin_unit_1:
            worksheet.write(row, col, (count),format)
            worksheet.write(row, col+1, au1.name,format)
            col = 0
            column = col+2
            column_count_2 = 0
            all_landuse_count = 0
            area_level_3 = 0
            all_area_landuse = 0
            is_first = 0
            for con in conservation_type:
                code2 = str(con.code)[:2]
                landuse_count = self.session.query(ClLanduseType.description2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2).count()
                if landuse_count != 0:
                    landuse = self.session.query(ClLanduseType.description2,ClLanduseType.code2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2,ClLanduseType.code2).one()
                    if code1 == str(landuse.code2)[:2]:
                        is_first = 1
                        column = column + 1
                        worksheet.write(8,column,con.description,format)
                        worksheet.write(9,column, column,format)

                        srid_list = self.session.query((((((func.ST_X(func.ST_Centroid(CaParcelConservation.geometry))+186)/6)))).label("srid"))\
                                        .join(ParcelGt1, CaParcelConservation.geometry.ST_Intersects(ParcelGt1.geometry))\
                                        .join(AuLevel1, CaParcelConservation.geometry.ST_Within(AuLevel1.geometry))\
                                        .join(AuLevel2, CaParcelConservation.geometry.ST_Within(AuLevel2.geometry))\
                                        .filter(CaParcelConservation.conservation == con.code)\
                                        .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()
                        srid = 0
                        for a in srid_list:
                            srid = 32600 + int(a.srid)

                        area = self.session.query(func.sum(func.ST_Area(func.ST_Intersection(func.ST_Transform(func.ST_SetSRID(CaParcelConservation.geometry,4326),srid), func.ST_Transform(func.ST_SetSRID(ParcelGt1.geometry,4326),srid)))).label("area"))\
                                        .join(ParcelGt1, CaParcelConservation.geometry.ST_Intersects(ParcelGt1.geometry))\
                                        .join(AuLevel1, CaParcelConservation.geometry.ST_Within(AuLevel1.geometry))\
                                        .join(AuLevel2, CaParcelConservation.geometry.ST_Within(AuLevel2.geometry))\
                                        .filter(CaParcelConservation.conservation == con.code)\
                                        .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()
                        conservation_area = 0
                        for a in area:
                            if a.area == None or a.area == 0:
                                conservation_area = ''
                            else:
                                conservation_area = str(a.area)
                                conservation_area = float(conservation_area)
                                conservation_area = round(conservation_area,2)
                        worksheet.write(row,column, conservation_area,format)
                        if conservation_area == '':
                            conservation_area = 0
                        area_level_3 = area_level_3 + conservation_area
                        all_area_landuse = all_area_landuse + conservation_area
                        column_count_2 += 1
                        all_landuse_count += 1
                    else:
                        if is_first == 1:
                            code1 = 0
                            if area_level_3 == 0:
                                area_level_3 = ''
                            else:
                                area_level_3 = (round(area_level_3,2))
                            worksheet.write(row, column-column_count_2, area_level_3,format)
                            if column_count_2 > 1:
                                worksheet.merge_range(7,column-column_count_2+1,7,column, u"Үүнээс",format)
                            else:
                                worksheet.write(7,column, u"Үүнээс",format)
                            area_level_3 = 0
                            column_count_2 = 0
                    if code1 == 0:

                        column = column + 1
                        code1 = str(landuse.code2)[:2]
                        code2 = str(landuse.code2)[:2]
                        landuse_count = self.session.query(ClLanduseType.description2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2).count()
                        if landuse_count != 0:
                            landuse = self.session.query(ClLanduseType.description2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2).one()
                            worksheet.merge_range(7,column,8,column,landuse.description2+u' ,бүгд',format)

                            worksheet.write(9,column, column,format)
                            column = column + 1
                            worksheet.write(8,column,con.description,format)
                            worksheet.write(9,column, column,format)
                            srid_list = self.session.query((((((func.ST_X(func.ST_Centroid(CaParcelConservation.geometry))+186)/6)))).label("srid"))\
                                        .join(ParcelGt1, CaParcelConservation.geometry.ST_Intersects(ParcelGt1.geometry))\
                                        .join(AuLevel1, CaParcelConservation.geometry.ST_Within(AuLevel1.geometry))\
                                        .join(AuLevel2, CaParcelConservation.geometry.ST_Within(AuLevel2.geometry))\
                                        .filter(CaParcelConservation.conservation == con.code)\
                                        .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()
                            srid = 0
                            for a in srid_list:
                                srid = 32600 + int(a.srid)

                            area = self.session.query(func.sum(func.ST_Area(func.ST_Intersection(func.ST_Transform(func.ST_SetSRID(CaParcelConservation.geometry,4326),srid), func.ST_Transform(func.ST_SetSRID(ParcelGt1.geometry,4326),srid)))).label("area"))\
                                            .join(ParcelGt1, CaParcelConservation.geometry.ST_Intersects(ParcelGt1.geometry))\
                                            .join(AuLevel1, CaParcelConservation.geometry.ST_Within(AuLevel1.geometry))\
                                            .join(AuLevel2, CaParcelConservation.geometry.ST_Within(AuLevel2.geometry))\
                                            .filter(CaParcelConservation.conservation == con.code)\
                                            .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()

                            conservation_area = 0
                            for a in area:
                                if a.area == None or a.area == 0:
                                    conservation_area = ''
                                else:
                                    conservation_area = str(a.area)
                                    conservation_area = float(conservation_area)
                                    conservation_area = round(conservation_area,2)
                            worksheet.write(row,column, conservation_area,format)
                            if conservation_area == '':
                                conservation_area = 0
                            area_level_3 = area_level_3 + conservation_area
                            all_area_landuse = all_area_landuse + conservation_area
                            column_count_2 += 1
                            all_landuse_count += 1
            code1 = 0
            if area_level_3 == 0:
                area_level_3 = ''
            else:
                area_level_3 = (round(area_level_3,2))
            worksheet.write(row, column-column_count_2, area_level_3,format)
            if column_count_2 > 1:
                worksheet.merge_range(7,column-column_count_2+1,7,column, u"Үүнээс",format)
            else:
                worksheet.write(7,column, u"Үүнээс",format)
            if all_area_landuse == 0:
                all_area_landuse = ''
            else:
                all_area_landuse = (round(all_area_landuse,2))
            worksheet.write(row, 2, all_area_landuse,format)
            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
            row += 1
            count +=1
        worksheet.merge_range(row,0,row,1,u"ДҮН",format)
        for i in range(2,column+1):
            cell_up = xl_rowcol_to_cell(10, i)
            cell_down = xl_rowcol_to_cell(row-1, i)
            worksheet.write(row,i,'=SUM('+cell_up+':'+cell_down+')',format)

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_7.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_8(self):

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
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_8.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_row(0,50)
        worksheet.set_row(6,25)
        worksheet.set_paper(8)
        worksheet.set_landscape()
        worksheet.set_column('B:B', 20)
        worksheet.set_margins(left=0.3, right=0.3, top=0.3, bottom=0.3)
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)

        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        worksheet.merge_range('D2:J2', u'ГАЗРЫН ТӨЛБӨР НОГДУУЛАЛТ, ТӨЛӨЛТИЙН ТАЙЛАН /'+str(self.begin_year_sbox.value())+u' он/',format_header)
        worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 8 дугаар хавсралт',format_header)
        worksheet.merge_range('K2:M2', u'/мян.төг/            Маягт ГТ-8 ',format_header)
        worksheet.merge_range('A4:A8', u'д/д', format)
        worksheet.merge_range('B4:B8', u'Аймаг, нийслэл, сум, дүүргийн нэр',format)
        worksheet.merge_range('C4:C8', u'Газрын төлбөрийн төлөвлөгөө(мян.төг)',format)
        worksheet.merge_range('D4:D8', u'Төлбөл зохих нийт төлбөр/мян.төг/',format)
        worksheet.merge_range('E4:E8', u'Тайлангийн хугацаанд төлсөн төлбөр(мян.төг)',format)
        worksheet.merge_range('F4:F8', u'Нийт үлдэгдэл төлбөр(мян.төг)',format)
        worksheet.write(8,0, 0,format)
        worksheet.write(8,1, 1,format)
        worksheet.write(8,2, 2,format)
        worksheet.write(8,3, 3,format)
        worksheet.write(8,4, 4,format)
        worksheet.write(8,5, 5,format)

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")

        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        if len(au_level1_list) > 1:
            admin_unit_1 = self.session.query(AuLevel1)\
                        .filter(AuLevel1.code.in_(au_level1_list)).all()
        elif len(au_level1_list) == 1 or len(au_level2_list) >= 1:
            admin_unit_1 = self.session.query(AuLevel2)\
                        .filter(AuLevel2.code.in_(au_level2_list)).all()
        special_needs = self.session.query(ClLanduseType.code2,ClLanduseType.description2).group_by(ClLanduseType.code2,ClLanduseType.description2)\
                                                    .order_by(ClLanduseType.code2.asc()).all()
        progress_count = len(admin_unit_1)
        self.progressBar.setMaximum(progress_count)
        code1 = 0
        row = 9
        col = 0
        count = 1
        for au1 in admin_unit_1:
            worksheet.write(row, col, count,format)
            worksheet.write(row, col+1, au1.name,format)
            col = 0
            column = col+4
            is_first = 0
            column_count_1 = 0
            all_balance = 0
            all_fee = 0
            all_paymnet = 0

            for code_2, desc_2 in special_needs:

                if code1 == str(code_2)[:1]:
                    is_first = 1
                    worksheet.write(8,column, column,format)

                    worksheet.merge_range(6,column,6,column+4, desc_2,format)
                    if code_2 == 11:
                        worksheet.write(7,column,u'Төлбөр ногдох нийт хонин толгой',format)
                    else:
                        worksheet.write(7,column,u'Төлбөр ногдох нийт талбай/га/',format)
                    fee_all_area = self.session.query(func.sum(ParcelFeeReport.fee_area).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.contract_no != None).filter(ParcelFeeReport.landuse_code2 == code_2)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if fee_all_area.area == None or fee_all_area.area == 0:
                        all_area = ''
                    else:
                        all_area = float(fee_all_area.area)/10000
                        all_area = round(all_area, 2)
                    worksheet.write(row,column, all_area, format)
                    if all_area == '':
                        all_area = 0

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Төлбөрөөс чөлөөлсөн/га/',format)
                    subsidized_area = self.session.query(func.sum(ParcelFeeReport.subsidized_area).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.landuse_code2 == code_2).filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.area_m2 > ParcelFeeReport.subsidized_area)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if subsidized_area.area == None or subsidized_area.area == 0:
                        sub_area = ''
                    else:
                        sub_area = float(subsidized_area.area)/10000
                        sub_area = round(sub_area, 2)
                    worksheet.write(row,column, sub_area, format)
                    if sub_area == '':
                        sub_area = 0

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Төлбөл зохих төлбөр/мян.төг/',format)
                    fee_contract = self.session.query(func.sum(ParcelFeeReport.fee_contract).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.landuse_code2 == code_2).filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.fee_contract != None)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if fee_contract.area == None or fee_contract.area == 0:
                        fee = ''
                    else:
                        fee = float(fee_contract.area)/1000
                        fee = round(fee, 2)
                    worksheet.write(row,column, fee, format)
                    if fee == '':
                        fee = 0
                    all_fee = all_fee + fee

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Үүнээс төлсөн төлбөр/мян.төг/',format)
                    fee_payment = self.session.query(func.sum(ParcelFeeReport.amount_paid).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.landuse_code2 == code_2).filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.amount_paid != None)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if fee_payment.area == None or fee_payment.area == 0:
                        payment = ''
                    else:
                        payment = float(fee_payment.area)/1000
                        payment = round(payment, 2)
                    worksheet.write(row,column, payment, format)
                    if payment == '':
                        payment = 0
                    all_paymnet = all_paymnet + payment

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Үлдэгдэл төлбөр/мян.төг/',format)
                    balance = fee - payment
                    worksheet.write(row,column, balance, format)
                    all_balance = all_balance + balance

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    column_count_1 = column_count_1 + 5
                else:
                    if is_first == 1:

                        if column_count_1 > 1:
                            worksheet.merge_range(5,column-column_count_1-1,5,column-1, u"Үүнээс",format)
                        else:
                            worksheet.write(5,column-1, u"Үүнээс",format)
                        if code1 == '1':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_1,format)
                        elif code1 == '2':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_2,format)
                        elif code1 == '3':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_3,format)
                        elif code1 == '4':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_4,format)
                        elif code1 == '5':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_5,format)
                        elif code1 == '6':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_6,format)
                        code1 = 0
                        column_count_1 = 0
                if code1 == 0:
                    code1 = str(code_2)[:1]
                    if is_first == 0:
                        column = column + 2
                    worksheet.merge_range(6,column,6,column+4,desc_2,format)
                    if code_2 == 11:
                        worksheet.write(7,column,u'Төлбөр ногдох нийт хонин толгой',format)
                    else:
                        worksheet.write(7,column,u'Төлбөр ногдох нийт талбай/га/',format)
                    fee_all_area = self.session.query(func.sum(ParcelFeeReport.fee_area).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.contract_no != None).filter(ParcelFeeReport.landuse_code2 == code_2)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if fee_all_area.area == None or fee_all_area.area == 0:
                        all_area = ''
                    else:
                        all_area = float(fee_all_area.area)/10000
                        all_area = round(all_area, 2)
                    worksheet.write(row,column, all_area, format)
                    if all_area == '':
                        all_area = 0

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Төлбөрөөс чөлөөлсөн/га/',format)
                    subsidized_area = self.session.query(func.sum(ParcelFeeReport.subsidized_area).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.landuse_code2 == code_2).filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.area_m2 > ParcelFeeReport.subsidized_area)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if subsidized_area.area == None or subsidized_area.area == 0:
                        sub_area = ''
                    else:
                        sub_area = float(subsidized_area.area)/10000
                        sub_area = round(sub_area, 2)
                    worksheet.write(row,column, sub_area, format)
                    if sub_area == '':
                        sub_area = 0

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Төлбөл зохих төлбөр/мян.төг/',format)
                    fee_contract = self.session.query(func.sum(ParcelFeeReport.fee_contract).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.landuse_code2 == code_2).filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.fee_contract != None)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if fee_contract.area == None or fee_contract.area == 0:
                        fee = ''
                    else:
                        fee = float(fee_contract.area)/1000
                        fee = round(fee, 2)
                    worksheet.write(row,column, fee, format)
                    if fee == '':
                        fee = 0
                    all_fee = all_fee + fee

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Үүнээс төлсөн төлбөр/мян.төг/',format)
                    fee_payment = self.session.query(func.sum(ParcelFeeReport.amount_paid).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.landuse_code2 == code_2).filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.amount_paid != None)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if fee_payment.area == None or fee_payment.area == 0:
                        payment = ''
                    else:
                        payment = float(fee_payment.area)/1000
                        payment = round(payment, 2)
                    worksheet.write(row,column, payment, format)
                    if payment == '':
                        payment = 0
                    all_paymnet = all_paymnet + payment

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Үлдэгдэл төлбөр/мян.төг/',format)
                    balance = fee - payment
                    worksheet.write(row,column, balance, format)
                    all_balance = all_balance + balance

                    column = column + 1
                    column_count_1 = column_count_1 + 4
            code1 = 0
            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_6,format)
            worksheet.merge_range(3,6,3,column-1, u"Үүнээс газрын ангиаллын төрлөөр",format)
            if column_count_1 > 1:
                worksheet.merge_range(5,column-column_count_1-1,5,column-1, u"Үүнээс",format)
            else:
                worksheet.write(5,column-1, u"Үүнээс",format)

            worksheet.merge_range(3,column,7,column, u'Дараа оны төсвийн төлөвлөгөө(мян.төг)',format)
            worksheet.write(8,column, column,format)
            fee_report_year = self.session.query(func.sum(ParcelFeeReport.fee_contract).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.after_year_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.fee_contract != None)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
            if fee_report_year.area == None or fee_report_year.area == 0:
                fee = 0
            else:
                fee = float(fee_report_year.area)/1000
                fee = round(fee, 2)
            worksheet.write(row,column, fee+all_balance, format)

            worksheet.write(row,2,all_fee, format)
            worksheet.write(row,3,all_fee, format)
            worksheet.write(row,4,all_paymnet, format)
            worksheet.write(row,5,all_balance, format)

            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
            row += 1
            count +=1
        worksheet.merge_range(row,0,row,1, u'ДҮН',format)
        for i in range(2,column+1):
            cell_up = xl_rowcol_to_cell(9, i)
            cell_down = xl_rowcol_to_cell(row-1, i)
            worksheet.write(row,i,'=SUM('+cell_up+':'+cell_down+')',format)
        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_8.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_9(self):

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
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_9.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_row(0,50)
        worksheet.set_row(3,50)
        worksheet.set_column('A:A', 3)
        worksheet.set_column('B:B', 20)
        worksheet.set_paper(8)
        worksheet.set_landscape()
        worksheet.set_margins(left=0.3, right=0.3, top=0.3, bottom=0.3)
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)

        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        worksheet.merge_range('D2:J2', u'МОНГОЛ УЛСЫН ИРГЭНД ӨМЧЛҮҮЛСЭН ГАЗРЫН ТАЙЛАН '+str(self.begin_year_sbox.value())+u' ОН',format_header)
        worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 9 дүгээр хавсралт',format_header)
        worksheet.merge_range('K2:M2', u'/га-гаар/            Маягт ГТ-9 ',format_header)
        worksheet.merge_range('A4:A5', u'№', format)
        worksheet.merge_range('B4:B5', u'Аймаг, нийслэл, сум, дүүргийн нэр',format)
        worksheet.merge_range('C4:C5', u'Нийт газар өмчлөгч иргэдийн тоо',format_90)
        worksheet.merge_range('D4:D5', u'Өмчлөлд буй газрын нийт хэмжээ /га/',format_90)
        worksheet.merge_range('E4:F4', u'Гэр бүлийн хэрэгцээнд нэг удаа үнэгүй өмчилсөн',format)
        worksheet.merge_range('G4:H4', u'Гэр бүлийн хэрэгцээнд үнээр нь худалдаж авсан',format)
        worksheet.merge_range('I4:J4', u'Аж ахуйн зориулалтаар давуу эрхээр худалдаж авсан',format)
        worksheet.merge_range('K4:L4', u'Аж ахуйн зориулалтаар дуудлага худалдаагаар худалдаж авсан',format)
        worksheet.merge_range('M4:N4', u'Газар тариалангийн зориулалтаар давуу эрхээр худалдаж авсан',format)
        worksheet.merge_range('O4:P4', u'Газар тариалангийн зориулалтаар дуудлага худалдаагаар худалдаж авсан',format)
        worksheet.write('E5', u'Иргэдийн тоо',format_90)
        worksheet.write('F5', u'Газрын хэмжээ/га/',format_90)
        worksheet.write('G5', u'Иргэдийн тоо',format_90)
        worksheet.write('H5', u'Газрын хэмжээ/га/',format_90)
        worksheet.write('I5', u'Иргэдийн тоо',format_90)
        worksheet.write('J5', u'Газрын хэмжээ/га/',format_90)
        worksheet.write('K5', u'Иргэдийн тоо',format_90)
        worksheet.write('L5', u'Газрын хэмжээ/га/',format_90)
        worksheet.write('M5', u'Иргэдийн тоо',format_90)
        worksheet.write('N5', u'Газрын хэмжээ/га/',format_90)
        worksheet.write('O5', u'Иргэдийн тоо',format_90)
        worksheet.write('P5', u'Газрын хэмжээ/га/',format_90)
        worksheet.merge_range('Q4:Q5', u'Өмчилсөн газрын үл хөдлөх хөрөнгийн татвар ногдуулалт/мян.төг/',format_90)
        worksheet.merge_range('R4:R5', u'Өмчилсөн газрын үл хөдлөх хөрөнгийн татварын орлогын хэмжээ/мян.төг/',format_90)
        worksheet.write(5,0, u'А',format)
        worksheet.write(5,1, u'Б',format)
        worksheet.write(5,2, 1,format)
        worksheet.write(5,3, 2,format)
        worksheet.write(5,4, 3,format)
        worksheet.write(5,5, 4,format)
        worksheet.write(5,6, 5,format)
        worksheet.write(5,7, 6,format)
        worksheet.write(5,8, 7,format)
        worksheet.write(5,9, 8,format)
        worksheet.write(5,10, 9,format)
        worksheet.write(5,11, 10,format)
        worksheet.write(5,12, 11,format)
        worksheet.write(5,13, 12,format)
        worksheet.write(5,14, 13,format)
        worksheet.write(5,15, 14,format)
        worksheet.write(5,16, 15,format)
        worksheet.write(5,17, 16,format)

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")

        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        if len(au_level1_list) > 1:
            admin_unit_1 = self.session.query(AuLevel1)\
                        .filter(AuLevel1.code.in_(au_level1_list)).all()
        elif len(au_level1_list) == 1 or len(au_level2_list) >= 1:
            admin_unit_1 = self.session.query(AuLevel2)\
                        .filter(AuLevel2.code.in_(au_level2_list)).all()
        # admin_unit_1 = self.session.query(AuLevel1)\
        #         .filter(or_(AuLevel1.code == "021", AuLevel1.code == "022", AuLevel1.code == "023", AuLevel1.code == "041", AuLevel1.code == "042"\
        #                     , AuLevel1.code == "043", AuLevel1.code == "044", AuLevel1.code == "045", AuLevel1.code == "046", AuLevel1.code == "048"\
        #                     , AuLevel1.code == "061", AuLevel1.code == "062", AuLevel1.code == "063", AuLevel1.code == "064", AuLevel1.code == "065"\
        #                     , AuLevel1.code == "067", AuLevel1.code == "081", AuLevel1.code == "082", AuLevel1.code == "083", AuLevel1.code == "084", AuLevel1.code == "085")).order_by(AuLevel1.name.asc()).all()

        progress_count = len(admin_unit_1)
        self.progressBar.setMaximum(progress_count)
        row = 6
        col = 0
        count = 1

        for au1 in admin_unit_1:
            record_area_all = 0
            record_area_app_type1 = 0
            record_area_app_type4 = 0
            record_area_type16_economy = 0
            excess_area = 0
            record_area_app_landuse13 = 0
            record_area_app16_landuse = 0

            worksheet.write(row, col, count,format)
            worksheet.write(row, col+1, au1.name,format)

            person_count = self.session.query(ParcelReport.person_id).filter(ParcelReport.record_no != None).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_id).count()
            record_area_sum_all = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.record_no != None).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).one()

            person_count_app_type1 = self.session.query(ParcelReport.person_id).filter(ParcelReport.record_no != None).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(ParcelReport.app_type == 1).\
                            filter(or_(ParcelReport.landuse == 2204,ParcelReport.landuse == 2205,ParcelReport.landuse == 2206)).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_id).count()
            record_area_sum_all_app_type1 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.record_no != None).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(ParcelReport.app_type == 1).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(or_(ParcelReport.landuse == 2204,ParcelReport.landuse == 2205,ParcelReport.landuse == 2206)).one()

            person_count_app_type4 = self.session.query(ParcelReport.pers).filter(ParcelReport.record_no != None).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(ParcelReport.app_type == 4).\
                            filter(ParcelReport.right_type == 20).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_id).count()
            record_area_sum_all_app_type4 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.record_no != None).\
                            filter(ParcelReport.right_type == 20).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(ParcelReport.app_type == 4).one()

            person_count_app_type16_economy = self.session.query(ParcelReport.person_id).filter(ParcelReport.record_no != None).\
                            join(SetApplicationTypeLanduseType, ParcelReport.landuse == SetApplicationTypeLanduseType.landuse_type).\
                            filter(SetApplicationTypeLanduseType.application_type == 4).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).\
                            filter(ParcelReport.app_type == 16).\
                            filter(SetApplicationTypeLanduseType.landuse_type != None).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_id).count()
            record_area_sum_all_app_type16_economy = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.record_no != None).\
                            join(SetApplicationTypeLanduseType, ParcelReport.landuse == SetApplicationTypeLanduseType.landuse_type).\
                            filter(SetApplicationTypeLanduseType.application_type == 4).\
                            filter(ParcelReport.right_type == 20).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).\
                            filter(SetApplicationTypeLanduseType.landuse_type != None).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(ParcelReport.app_type == 16).one()

            person_count_app_landuse13 = self.session.query(ParcelReport.person_id).filter(ParcelReport.record_no != None).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(or_(ParcelReport.landuse == 1301,ParcelReport.landuse == 1302,\
                            ParcelReport.landuse == 1303,ParcelReport.landuse == 1304,ParcelReport.landuse == 1305,ParcelReport.landuse == 1306,\
                            ParcelReport.landuse == 1401,ParcelReport.landuse == 1402,ParcelReport.landuse == 1403,\
                            ParcelReport.landuse == 1404,ParcelReport.landuse == 1405,ParcelReport.landuse == 1406)).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_id).count()
            record_area_sum_all_app_landuse13 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.record_no != None).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(or_(ParcelReport.landuse == 1301,ParcelReport.landuse == 1302,\
                            ParcelReport.landuse == 1303,ParcelReport.landuse == 1304,ParcelReport.landuse == 1305,ParcelReport.landuse == 1306,\
                            ParcelReport.landuse == 1401,ParcelReport.landuse == 1402,ParcelReport.landuse == 1403,\
                            ParcelReport.landuse == 1404,ParcelReport.landuse == 1405,ParcelReport.landuse == 1406)).one()

            person_count_app16_landuse = self.session.query(ParcelReport.person_id).filter(ParcelReport.record_no != None).\
                            filter(ParcelReport.app_type == 16).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(or_(ParcelReport.landuse_code2 == 13, ParcelReport.landuse_code2 == 14, ParcelReport.landuse_code2 == 15)).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_id).count()
            record_area_sum_all_app16_landuse = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.record_no != None).\
                            filter(ParcelReport.app_type == 16).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(or_(ParcelReport.landuse_code2 == 13, ParcelReport.landuse_code2 == 14, ParcelReport.landuse_code2 == 15)).one()

            excess_person_count = self.session.query(ParcelReport.person_id).filter(ParcelReport.record_no != None).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(ParcelReport.excess_area != 0).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_id).count()

            excess_area_sum = self.session.query(func.sum(ParcelReport.excess_area * ParcelReport.share).label("excess_area"))\
                            .filter(ParcelReport.record_no != None).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(ParcelReport.excess_area != 0).one()

            tax = self.session.query(func.sum(ParcelTaxReport.land_tax).label("area"))\
                                .filter(ParcelTaxReport.valid_till == 'infinity')\
                                .filter(ParcelTaxReport.record_date < self.end_date)\
                                .filter(ParcelTaxReport.record_no != None)\
                                .filter(ParcelTaxReport.tax_area != None)\
                                .filter(ParcelTaxReport.parcel_id != None)\
                                .filter(ParcelTaxReport.land_tax != None)\
                                .filter(or_(ParcelTaxReport.au1_code == au1.code, ParcelTaxReport.au2_code == au1.code))\
                                .one()
            if tax.area == None or tax.area == 0:
                fee = ''
            else:
                fee = float(tax.area)/1000
                fee = round(fee, 2)
            worksheet.write(row,16, fee, format)

            tax_payment = self.session.query(func.sum(ParcelTaxReport.amount_paid).label("area"))\
                                .filter(ParcelTaxReport.valid_till == 'infinity')\
                                .filter(ParcelTaxReport.record_date < self.end_date)\
                                .filter(ParcelTaxReport.record_no != None)\
                                .filter(ParcelTaxReport.parcel_id != None)\
                                .filter(ParcelTaxReport.amount_paid != None)\
                                .filter(or_(ParcelTaxReport.au1_code == au1.code, ParcelTaxReport.au2_code == au1.code))\
                                .one()
            if tax_payment.area == None or tax_payment.area == 0:
                payment = ''
            else:
                payment = float(tax_payment.area)/1000
                payment = round(payment, 2)
            worksheet.write(row,17, payment, format)

            if record_area_sum_all.area != None:
                record_area_all = round(record_area_sum_all.area/10000, 2)
            else:
                record_area_all = ""
            if record_area_sum_all_app_type1.area != None:
                record_area_app_type1 = round(record_area_sum_all_app_type1.area/10000, 2)
            else:
                record_area_app_type1 = ""
            if record_area_sum_all_app_type4.area != None:
                record_area_app_type4 = round(record_area_sum_all_app_type4.area/10000, 2)
            else:
                record_area_app_type4 = ""
            if record_area_sum_all_app_type16_economy.area != None:
                record_area_type16_economy = round(record_area_sum_all_app_type16_economy.area/10000, 2)
            else:
                record_area_type16_economy = ""
            if record_area_sum_all_app_landuse13.area != None:
                record_area_app_landuse13 = round(record_area_sum_all_app_landuse13.area/10000, 2)
            else:
                record_area_app_landuse13 = ""
            if excess_area_sum.excess_area != None:
                excess_area = round(excess_area_sum.excess_area/10000, 2)
            else:
                excess_area = ""
            if record_area_sum_all_app16_landuse.area != None:
                record_area_app16_landuse = round(record_area_sum_all_app16_landuse.area/10000, 2)
            else:
                record_area_app16_landuse = ""
            worksheet.write(row, col+2,person_count,format)
            worksheet.write(row, col+3,record_area_all,format)
            worksheet.write(row, col+4,person_count_app_type1,format)
            worksheet.write(row, col+5,record_area_app_type1,format)
            worksheet.write(row, col+6,excess_person_count,format)
            worksheet.write(row, col+7,excess_area,format)
            worksheet.write(row, col+8,person_count_app_type4,format)
            worksheet.write(row, col+9,record_area_app_type4,format)
            worksheet.write(row, col+10,person_count_app_type16_economy, format)
            worksheet.write(row, col+11,record_area_type16_economy,format)
            worksheet.write(row, col+12,person_count_app_landuse13,format)
            worksheet.write(row, col+13,record_area_app_landuse13,format)
            worksheet.write(row, col+14,person_count_app16_landuse,format)
            worksheet.write(row, col+15,record_area_app16_landuse,format)

            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
            row += 1
            count +=1
        worksheet.merge_range(row,0,row,1, u'ДҮН',format)
        for i in range(2,18):
            cell_up = xl_rowcol_to_cell(6, i)
            cell_down = xl_rowcol_to_cell(row-1, i)
            worksheet.write(row,i,'=SUM('+cell_up+':'+cell_down+')',format)
        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_9.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    @pyqtSlot()
    def on_print_button_clicked(self):

        self.progressBar.setVisible(True)
        self.progressBar.setMinimum(1)
        self.progressBar.setValue(0)
        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        sql = ""

        itemsList = self.gts_lwidget.selectedItems()
        code = '0'
        for item in itemsList:
            code = str(item.text()[:2])

        if code == '01':
            self.__report_gt_1()
        elif code == '02':
            self.__report_gt_2()
        elif code == '03':
            self.__report_gt_3()
        elif code == '04':
            self.__report_gt_4()
        elif code == '05':
            self.__report_gt_5()
        elif code == '06':
            self.__report_gt_6()
        elif code == '07':
            self.__report_gt_7()
        elif code == '08':
            self.__report_gt_8()
        elif code == '09':
            self.__report_gt_9()

        self.progressBar.setVisible(False)

    @pyqtSlot()
    def on_layer_view_button_clicked(self):

        root = QgsProject.instance().layerTreeRoot()

        LayerUtils.refresh_layer()

        restrictions = DatabaseUtils.working_l2_code()
        itemsList = self.gts_lwidget.selectedItems()
        code = '0'
        for item in itemsList:
            code = str(item.text()[:2])
        if code == '01':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt1_report")
            if tmp_parcel_layer is None:
                 mygroup = root.findGroup(u"ГНСТайлан")
                 vlayer = LayerUtils.load_layer_by_name_report("view_gt1_report", "parcel_id", restrictions)
                 vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/gt1_report.qml")
                 vlayer.setLayerName(self.tr("Gt1 report layer"))
                 mygroup.addLayer(vlayer)
        elif code == '02':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt2_report")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"ГНСТайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_gt2_report", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/gt2_report.qml")
                vlayer.setLayerName(self.tr("Gt2 report layer"))
                mygroup.addLayer(vlayer)
        elif code == '03':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt2_report")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"ГНСТайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_gt2_report", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style\gt2_report.qml")
                vlayer.setLayerName(self.tr("Gt3 report layer"))
                mygroup.addLayer(vlayer)
        elif code == '04':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt4_report")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"ГНСТайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_gt4_report", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style\gt4_report.qml")
                vlayer.setLayerName(self.tr("Gt4 report layer"))
                mygroup.addLayer(vlayer)
        elif code == '06':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt6_report")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"ГНСТайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_gt6_report", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style\gt6_report.qml")
                vlayer.setLayerName(self.tr("Gt6 report layer"))
                mygroup.addLayer(vlayer)
        elif code == '07':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt7_report")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"ГНСТайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_gt7_report", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style\gt7_report.qml")
                vlayer.setLayerName(self.tr("Gt7 report layer"))
                mygroup.addLayer(vlayer)
        elif code == '08':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt8_report")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"ГНСТайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_gt8_report", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style\gt8_report.qml")
                vlayer.setLayerName(self.tr("Gt8 report layer"))
                mygroup.addLayer(vlayer)
        elif code == '09':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt9_report")
            if tmp_parcel_layer is None:
                mygroup = root.findGroup(u"ГНСТайлан")
                vlayer = LayerUtils.load_layer_by_name_report("view_gt9_report", "parcel_id", restrictions)
                vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style\gt9_report.qml")
                vlayer.setLayerName(self.tr("Gt9 report layer"))
                mygroup.addLayer(vlayer)

    @pyqtSlot()
    def on_qa_layer_button_clicked(self):

        root = QgsProject.instance().layerTreeRoot()

        LayerUtils.refresh_layer()

        restrictions = DatabaseUtils.working_l2_code()
        itemsList = self.qa_lwidget.selectedItems()
        code = '0'
        for item in itemsList:
            code = str(item.text()[:2])
        if code == '01':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "qa_buildings_overlapping_parcels")
            if tmp_parcel_layer is None:
                 mygroup = root.findGroup(u"Мэдээний хяналт")
                 vlayer = LayerUtils.load_layer_by_name_report("qa_buildings_overlapping_parcels", "building_id", restrictions)
                 # vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/gt1_report.qml")
                 vlayer.setLayerName(self.tr("Buildings Overlapping Parcels"))
                 mygroup.addLayer(vlayer)
        if code == '02':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "qa_overlapping_buildings")
            if tmp_parcel_layer is None:
                 mygroup = root.findGroup(u"Мэдээний хяналт")
                 vlayer = LayerUtils.load_layer_by_name_report("qa_overlapping_buildings", "building_id", restrictions)
                 # vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/gt1_report.qml")
                 vlayer.setLayerName(self.tr("Overlapping Buildings"))
                 mygroup.addLayer(vlayer)
        if code == '03':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "qa_overlapping_parcels")
            if tmp_parcel_layer is None:
                 mygroup = root.findGroup(u"Мэдээний хяналт")
                 vlayer = LayerUtils.load_layer_by_name_report("qa_overlapping_parcels", "parcel_id", restrictions)
                 # vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/gt1_report.qml")
                 vlayer.setLayerName(self.tr("Overlapping Parcels"))
                 mygroup.addLayer(vlayer)
        if code == '04':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "qa_parcels_overlapping_buildings")
            if tmp_parcel_layer is None:
                 mygroup = root.findGroup(u"Мэдээний хяналт")
                 vlayer = LayerUtils.load_layer_by_name_report("qa_parcels_overlapping_buildings", "parcel_id", restrictions)
                 # vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/gt1_report.qml")
                 vlayer.setLayerName(self.tr("Parcels Overlapping Buildings"))
                 mygroup.addLayer(vlayer)
        if code == '05':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "qa_parcels_overlapping_feezones")
            if tmp_parcel_layer is None:
                 mygroup = root.findGroup(u"Мэдээний хяналт")
                 vlayer = LayerUtils.load_layer_by_name_report("qa_parcels_overlapping_feezones", "parcel_id", restrictions)
                 # vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/gt1_report.qml")
                 vlayer.setLayerName(self.tr("Parcels Overlapping Fee zones"))
                 mygroup.addLayer(vlayer)
        if code == '06':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "qa_parcels_without_buildings")
            if tmp_parcel_layer is None:
                 mygroup = root.findGroup(u"Мэдээний хяналт")
                 vlayer = LayerUtils.load_layer_by_name_report("qa_parcels_without_buildings", "building_id", restrictions)
                 # vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/gt1_report.qml")
                 vlayer.setLayerName(self.tr("Parcels without Buildings"))
                 mygroup.addLayer(vlayer)
        if code == '07':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "qa_invalid_parcel_streetnames")
            if tmp_parcel_layer is None:
                 mygroup = root.findGroup(u"Мэдээний хяналт")
                 vlayer = LayerUtils.load_layer_by_name_report("qa_invalid_parcel_streetnames", "parcel_id", restrictions)
                 # vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/gt1_report.qml")
                 vlayer.setLayerName(self.tr("Incorrect Street names"))
                 mygroup.addLayer(vlayer)
        if code == '08':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "qa_invalid_parcel_khashaa_numbers")
            if tmp_parcel_layer is None:
                 mygroup = root.findGroup(u"Мэдээний хяналт")
                 vlayer = LayerUtils.load_layer_by_name_report("qa_invalid_parcel_khashaa_numbers", "parcel_id", restrictions)
                 # vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/gt1_report.qml")
                 vlayer.setLayerName(self.tr("Incorrect Khashaa numbers"))
                 mygroup.addLayer(vlayer)

    # Passive parcel delete
    @pyqtSlot()
    def on_delete_parcel_button_clicked(self):

        if not len(self.parcel_results_twidget.selectedItems()):
            return

        items = self.parcel_results_twidget.selectedItems()
        message_box = QMessageBox()

        if len(items) > 1:
            message_box.setText(self.tr("Do you want to delete {0} selected parcels?").format(len(items)))
        elif len(items) == 1:
            message_box.setText(self.tr("Do you want to delete the parcel {0}").format(str(items[0].data(Qt.UserRole))))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)

        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        for item in items:
            parcel_id = item.data(Qt.UserRole)
            try:

                self.create_savepoint()

                # app_no_soum = parcel_id.split("-")[0]
                DatabaseUtils.set_working_schema()
                maintenance_count = self.session.query(MaintenanceSearch).filter(MaintenanceSearch.parcel == parcel_id).count()
                if maintenance_count != 0:
                    maintenance = self.session.query(MaintenanceSearch).filter(MaintenanceSearch.parcel == parcel_id).all()
                    for case in maintenance:
                        case_no = case.id
                        self.session.query(CaMaintenanceCase).filter(CaMaintenanceCase.id == case_no).delete()

                self.session.query(CaParcel).filter(CaParcel.parcel_id == parcel_id).delete()

                self.commit()

            except SQLAlchemyError, e:
                self.rollback_to_savepoint()
                self.__passive_parcel_veiw()

                if e.__class__ == IntegrityError:
                    self.error_label.setText(self.tr("This application is still assigned. "
                                                     "Please remove the assignment in order to remove the application."))
                else:
                    PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
                DatabaseUtils.set_working_schema()
                return

        DatabaseUtils.set_working_schema()
        self.__clear_parcel()
        self.__passive_parcel_veiw()

    # Passive parcel view
    @pyqtSlot()
    def on_parcel_view_button_clicked(self):

        self.__passive_parcel_veiw()
        self.__view_inactive_parcel()

    def __view_inactive_parcel(self):

        restrictions = DatabaseUtils.working_l2_code()

        root = QgsProject.instance().layerTreeRoot()
        in_active_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_inactive_parcel")
        if in_active_parcel_layer is None:
             mygroup = root.findGroup(u"Мэдээний хяналт")
             vlayer = LayerUtils.load_layer_by_name_report("view_inactive_parcel", "parcel_id", restrictions)
             # vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"template\style/gt1_report.qml")
             vlayer.setLayerName(self.tr("In active parcels"))
             mygroup.addLayer(vlayer)

    def __passive_parcel_veiw(self):

         if self.is_parcel_checkbox.isChecked():
            applications = self.session.query(ApplicationSearch)
            filter_is_set = False
            sub = self.session.query(ApplicationSearch, func.row_number().over(partition_by = ApplicationSearch.app_no, order_by = (desc(ApplicationSearch.status_date), desc(ApplicationSearch.status))).label("row_number")).subquery()
            applications = applications.select_entity_from(sub).filter(sub.c.row_number == 1)

            applications = applications. \
                filter(and_(ApplicationSearch.app_type != ApplicationType.pasture_use,
                            ApplicationSearch.app_type != ApplicationType.right_land))

            applications = applications.filter(ApplicationSearch.status < 7)

            parcels = self.session.query(ParcelSearch).filter(ParcelSearch.app_no == None)

            count = 0
            for parcel in parcels.distinct(ParcelSearch.parcel_id).all():
                # geo_id = self.tr("n.a.") if not parcel.geo_id else parcel.geo_id
                address_khashaa = ''
                address_streetname = ''
                if parcel.address_khashaa:
                    address_khashaa = parcel.address_khashaa
                if parcel.address_streetname:
                    address_streetname = parcel.address_streetname
                item = QTableWidgetItem(parcel.parcel_id + " ("+address_khashaa+", "+ address_streetname+")")
                item.setIcon(QIcon(QPixmap(":/plugins/lm2/parcel.png")))
                item.setData(Qt.UserRole, parcel.parcel_id)
                self.parcel_results_twidget.insertRow(count)
                self.parcel_results_twidget.setItem(count, 0, item)
                count += 1

            self.error_label.setText("")
            self.parcel_results_label.setText(self.tr("Results: ") + str(count))

    # @pyqtSlot()
    # def on_p_button_clicked(self):
    #
    #     commercial = 'creative'
    #     beingPaidForIt = True
    #     renderer = Renderer('SimpleTest.odt', globals(), 'result.odt')
    #     renderer.run()

    @pyqtSlot(str)
    def on_parcel_streetname_edit_textChanged(self, text):

        self.parcel_streetname_edit.setStyleSheet(self.styleSheet())
        cap_value = self.__capitalize_first_letter(text)
        self.parcel_streetname_edit.setText(cap_value)
        if not self.__validate_street_name(cap_value):
            self.parcel_streetname_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    def __capitalize_first_letter(self, text):

        capital_letters = Constants.CAPITAL_MONGOLIAN
        first_letter = text[:1]

        if first_letter not in capital_letters:
            upper_letter = first_letter.upper()
            list_text = list(text)
            if len(list_text) == 0:
                return ""

            list_text[0] = upper_letter
            return "".join(list_text)

        return text

    def __validate_street_name(self, name):

        if name == "":
            return True

        for i in range(len(name)):

            if name[i].isdigit():

                if name[i - 1] != "-":
                    self.error_label.setText(self.tr("Street name can only end with a number, if a - is in front. "))
                return False

            if name[i] == "-":
                rest = name[i + 1:]

                if rest.isdigit():

                    return True
                else:

                    self.error_label.setText(self.tr("Street name can end with a number, if a - is in front. "))
                    return False
        return True

    def __setup_address_fill(self):

        khaskhaa_list = []
        street_list = []
        try:
            street_list = self.session.query(CaParcel.address_streetname).order_by(
                    CaParcel.address_streetname.desc()).all()

            khaskhaa_list = self.session.query(CaParcel.address_khashaa).order_by(
                    CaParcel.address_khashaa.desc()).all()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
            self.reject()

        khaskhaa_slist = []
        street_slist = []

        for street in street_list:
            if street[0]:
                street_slist.append(street[0])

        for khaskhaa in khaskhaa_list:
            if khaskhaa[0]:
                khaskhaa_slist.append(khaskhaa[0])

        street_model = QStringListModel(street_slist)
        self.streetProxyModel = QSortFilterProxyModel()
        self.streetProxyModel.setSourceModel(street_model)
        self.streetCompleter = QCompleter(self.streetProxyModel, self, activated=self.on_street_completer_activated)
        self.streetCompleter.setCompletionMode(QCompleter.PopupCompletion)
        self.parcel_streetname_edit.setCompleter(self.streetCompleter)

        khaskhaa_model = QStringListModel(khaskhaa_slist)
        self.khaskhaa_proxy_model = QSortFilterProxyModel()
        self.khaskhaa_proxy_model.setSourceModel(khaskhaa_model)
        self.khaskhaaCompleter = QCompleter(self.khaskhaa_proxy_model, self,
                                            activated=self.on_khaskhaa_completer_activated)
        self.khaskhaaCompleter.setCompletionMode(QCompleter.PopupCompletion)
        self.parcel_khashaa_edit.setCompleter(self.khaskhaaCompleter)

        self.parcel_streetname_edit.textEdited.connect(self.streetProxyModel.setFilterFixedString)
        self.parcel_khashaa_edit.textEdited.connect(self.khaskhaa_proxy_model.setFilterFixedString)

    @pyqtSlot(str)
    def on_street_completer_activated(self, text):

        if not text:
            return
        self.streetCompleter.activated[str].emit(text)

    @pyqtSlot(str)
    def on_khaskhaa_completer_activated(self, text):

        if not text:
            return
        self.khaskhaaCompleter.activated[str].emit(text)

    @pyqtSlot(QTableWidgetItem)
    def on_report_result_twidget_itemDoubleClicked(self, item):

        soum = DatabaseUtils.working_l2_code()
        layer = LayerUtils.layer_by_data_source("s" + soum, 'ca_parcel')

        selected_row = self.report_result_twidget.currentRow()
        parcel_id = person_id = self.report_result_twidget.item(selected_row, 0).data(Qt.UserRole+1)

        self.__select_feature(parcel_id, layer)


    def __select_feature(self, parcel_id, layer):

        expression = " parcel_id = \'" + parcel_id + "\'"
        request = QgsFeatureRequest()
        request.setFilterExpression(expression)
        feature_ids = []
        iterator = layer.getFeatures(request)

        for feature in iterator:
            feature_ids.append(feature.id())
        if len(feature_ids) == 0:
            self.error_label.setText(self.tr("No parcel assigned"))

        layer.setSelectedFeatures(feature_ids)
        self.plugin.iface.mapCanvas().zoomToSelected(layer)

    def __auto_find(self):

        time.sleep(15)