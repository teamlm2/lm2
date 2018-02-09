__author__ = 'B.Ankhbold'
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
from ..view.Ui_PastureWidget import Ui_PastureWidget
from ..model.ClPastureType import *
from ..controller.PastureMonitoringValueDialog import PastureMonitoringValueDialog
from ..controller.MemberGroupDialog import *
from PastureSettings import PastureSettings
from ApplicationsPastureDialog import ApplicationsPastureDialog
from SentToGovernorPastureDialog import SentToGovernorPastureDialog
from LandFeePaymentsDialog import *
from ContractPastureDialog import *
from ..model.DialogInspector import DialogInspector
from ..model.ApplicationPastureSearch import *
from ..model.PClPastureDaatsLevel import *
from ..model.PsPointDetail import *
from ..model.PsPointDaatsValue import *
from ..model.PsPointDetailPoints import *
from ..model.PsPastureBoundary import *
from ..model.PsAvgDaats import *
from ..model.AuReserveZone import *
from ..model.PsParcel import *
from ..model.PClReserveDaatsLevel import *
from ..model.PsAvgReserveDaats import *
from ..utils.LayerUtils import LayerUtils
from ..utils.SessionHandler import SessionHandler
from ..model.Enumerations import ApplicationType
from ..model.PsRecoveryClass import *
from ..model.PsParcelDuration import *
from ..model.CtAppGroupBoundary import *
from datetime import timedelta
from xlsxwriter.utility import xl_rowcol_to_cell, xl_col_to_name
import xlsxwriter

LANDUSE_1 = u'Хөдөө аж ахуйн газар'
LANDUSE_2 = u'Хот, тосгон, бусад суурины газар'
LANDUSE_3 = u'Зам, шугам сүлжээний газар'
LANDUSE_4 = u'Ойн сан бүхий газар'
LANDUSE_5 = u'Усны сан бүхий газар'
LANDUSE_6 = u'Улсын тусгай хэрэгцээний газар'

DAATS_LEVEL_1 = 1
DAATS_LEVEL_2 = 2
DAATS_LEVEL_3 = 3
DAATS_LEVEL_4 = 4
DAATS_LEVEL_5 = 5
DAATS_LEVEL_6 = 6

RESERVE_DAATS_LEVEL_1 = 1
RESERVE_DAATS_LEVEL_2 = 2
RESERVE_DAATS_LEVEL_3 = 3

class PastureWidget(QDockWidget, Ui_PastureWidget, DatabaseHelper):

    def __init__(self,  plugin, parent=None):

        super(PastureWidget, self).__init__(parent)
        DatabaseHelper.__init__(self)

        self.setupUi(self)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.plugin = plugin

        self.session = SessionHandler().session_instance()

        self.userSettings = None

        self.pasture_app_date_edit.setDate(QDate.currentDate())
        self.__setup_twidgets()
        self.__load_role_settings()
        self.__setup_combo_boxes()
        self.__setup_validators()

        self.working_l1_cbox.currentIndexChanged.connect(self.__working_l1_changed)
        self.working_l2_cbox.currentIndexChanged.connect(self.__working_l2_changed)

    def __setup_validators(self):

        self.numbers_validator = QRegExpValidator(QRegExp("[0-9]+\\.[0-9]{3}"), None)
        self.int_validator_2 = QRegExpValidator(QRegExp("[0-9]{3}"), None)
        self.int_validator_3 = QRegExpValidator(QRegExp("[0-9]{10}"), None)

        self.pasture_duration_edit.setValidator(self.int_validator_2)
        self.avg_sheep_unit_edit.setValidator(self.int_validator_3)
    def __setup_twidgets(self):

        self.zoom_to_parcel_action = QAction(QIcon(":/plugins/lm2/parcel.png"), self.tr("Zoom to parcel"), self)
        self.copy_number_action = QAction(QIcon(":/plugins/lm2/copy.png"), self.tr("Copy number"), self)
        self.copy_number_action.triggered.connect(self.on_copy_number_action_clicked)
        self.zoom_to_parcel_action.triggered.connect(self.on_zoom_to_parcel_action_clicked)

        self.contract_context_menu = QMenu()
        self.contract_action = QAction(QIcon(":/plugins/lm2/landfeepayment.png"),
                                                self.tr("Create and View Contract"), self)
        self.contract_action.triggered.connect(self.__show_contract_dialog)
        self.contract_context_menu.addAction(self.contract_action)
        self.contract_context_menu.addAction(self.zoom_to_parcel_action)
        self.contract_context_menu.addSeparator()
        self.contract_context_menu.addAction(self.copy_number_action)

        self.pasture_results_twidget.setColumnCount(1)
        self.pasture_results_twidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.pasture_results_twidget.horizontalHeader().setVisible(False)
        self.pasture_results_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.pasture_results_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.pasture_results_twidget.setDragEnabled(True)
        self.pasture_results_twidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pasture_results_twidget.customContextMenuRequested.connect(self.on_custom_context_menu_requested)

    @pyqtSlot(QTableWidgetItem)
    def on_zoom_to_parcel_action_clicked(self):

        app = self.__selected_application()
        app_parcels = self.session.query(CtApplicationPUGParcel).\
            filter(CtApplicationPUGParcel.application == app.app_no).all()

        if app is None:
            return

        parcels = []

        for app_parcel in app_parcels:
            if app_parcel.parcel is not None:
                parcels.append(app_parcel.parcel)

        self.__zoom_to_parcel_ids(parcels)

    def __zoom_to_parcel_ids(self, parcel_ids, layer_name = None):

        LayerUtils.deselect_all()
        if layer_name is None:
            for parcel_id in parcel_ids:
                if len(parcel_id) == 12:
                    layer_name = "ca_pasture_parcel"

        layer = LayerUtils.layer_by_data_source("s" + DatabaseUtils.current_working_soum_schema(), layer_name)

        restrictions = DatabaseUtils.working_l2_code()
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

    @pyqtSlot()
    def on_copy_number_action_clicked(self):

        if self.tabWidget.currentWidget() == self.pasture_tab:
            app = self.__selected_application()
            QApplication.clipboard().setText(app.app_no)

    @pyqtSlot()
    def on_pasture_contract_view_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        app_instance = self.__selected_application()
        app_contract_count = self.session.query(CtContractApplicationRole). \
            filter(CtContractApplicationRole.application == app_instance.app_no).count()

        if app_contract_count == 0:
            DatabaseUtils.set_working_schema()
            contract = PluginUtils.create_new_contract()
            self.current_dialog = ContractPastureDialog(self.plugin, contract, self, False, self.plugin.iface.mainWindow())
            self.current_dialog.rejected.connect(self.on_current_dialog_closed)
            DialogInspector().set_dialog_visible(True)
            self.current_dialog.setModal(False)
            self.current_dialog.show()
        elif app_contract_count == 1:
            app_contract = self.session.query(CtContractApplicationRole). \
                filter(CtContractApplicationRole.application == app_instance.app_no).one()
            contract = self.session.query(CtContract).filter_by(contract_no=app_contract.contract).one()

            self.current_dialog = ContractPastureDialog(self.plugin, contract, self, True, self.plugin.iface.mainWindow())
            self.current_dialog.rejected.connect(self.on_current_dialog_closed)
            DialogInspector().set_dialog_visible(True)
            self.current_dialog.setModal(False)
            self.current_dialog.show()

    def __show_contract_dialog(self):

        if DialogInspector().dialog_visible():
            return

        app_instance = self.__selected_application()
        app_contract_count = self.session.query(CtContractApplicationRole).\
            filter(CtContractApplicationRole.application == app_instance.app_no).count()

        if app_contract_count == 0:
            DatabaseUtils.set_working_schema()
            contract = PluginUtils.create_new_contract()

            self.current_dialog = ContractPastureDialog(self.plugin, contract, self, False, self.plugin.iface.mainWindow())
            self.current_dialog.rejected.connect(self.on_current_dialog_closed)
            DialogInspector().set_dialog_visible(True)
            self.current_dialog.setModal(False)
            self.current_dialog.show()
        elif app_contract_count == 1:
            app_contract = self.session.query(CtContractApplicationRole). \
                filter(CtContractApplicationRole.application == app_instance.app_no).one()
            contract = self.session.query(CtContract).filter_by(contract_no=app_contract.contract).one()

            self.current_dialog = ContractPastureDialog(self.plugin, contract, self, True, self.plugin.iface.mainWindow())
            self.current_dialog.rejected.connect(self.on_current_dialog_closed)
            DialogInspector().set_dialog_visible(True)
            self.current_dialog.setModal(False)
            self.current_dialog.show()

    @pyqtSlot(QPoint)
    def on_custom_context_menu_requested(self, point):

        if self.tabWidget.currentWidget() == self.pasture_tab:
            item = self.pasture_results_twidget.itemAt(point)
            if item is None: return
            self.contract_context_menu.exec_(self.pasture_results_twidget.mapToGlobal(point))

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

    def __load_role_settings(self):

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)

        self.__create_pasture_app_view()
        self.__create_pug_view()
        self.__create_parcel_duration_view()
        # self.__create_pasture_monitoring_point_view()

    def __create_parcel_duration_view(self):

        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        sql = ""

        for au_level2 in au_level2_list:

            au_level2 = au_level2.strip()
            if not sql:
                sql = "Create temp view ps_parcel_duration as" + "\n"
            else:
                sql = sql + "UNION" + "\n"

            select = "SELECT * " \
                     "FROM s{0}.ct_application_parcel_pasture pasture_parcel ".format(au_level2) + "\n"

            sql = sql + select
        sql = "{0} order by parcel;".format(sql)

        # try:
        self.session.execute(sql)
        self.commit()
        # except SQLAlchemyError, e:
        #     PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
        #     return

    def __create_pug_view(self):

        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        sql = ""

        for au_level2 in au_level2_list:

            au_level2 = au_level2.strip()
            if not sql:
                sql = "Create temp view ps_pasture_boundary as" + "\n"
            else:
                sql = sql + "UNION" + "\n"

            select = "SELECT pasture_parcel.parcel_id, pasture_parcel.address_neighbourhood pasture_land_name, pasture_parcel.pasture_type, pasture_parcel.area_ga pasture_area, " \
                     "pug.code pug_code, pug.area_ga pug_area, pug.group_name pug_name, au2.code as au2_code, au3.code as au3_code, " \
                     "pasture_parcel.geometry parcel_geom, pug.geometry as pug_geom " \
                     "FROM s{0}.ca_pasture_parcel pasture_parcel " \
                     "left join s{0}.ca_pug_boundary pug on st_intersects(pasture_parcel.geometry, pug.geometry) " \
                     "left join admin_units.au_level2 au2 on st_intersects(pasture_parcel.geometry, au2.geometry) " \
                     "left join admin_units.au_level3 au3 on st_intersects(pasture_parcel.geometry, au3.geometry) ".format(au_level2) + "\n"

            sql = sql + select
        sql = "{0} order by parcel_id;".format(sql)

        # try:
        self.session.execute(sql)
        self.commit()
        # except SQLAlchemyError, e:
        #     PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
        #     return

    def __create_pasture_app_view(self):

        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        sql = ""

        for au_level2 in au_level2_list:

            au_level2 = au_level2.strip()
            if not sql:
                sql = "Create temp view pasture_app_search as" + "\n"
            else:
                sql = sql + "UNION" + "\n"

            select = "SELECT application.app_no, group_member.group_no, parcel.pasture_type ,application.app_timestamp, application.app_type, status.status, status.status_date, status.officer_in_charge, status.next_officer_in_charge, decision.decision_no, " \
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
                     "left join s{0}.ct_group_member group_member on group_member.person = app_pers.person " \
                     "left join base.bs_person person on person.person_id = app_pers.person " \
                     "left join s{0}.ca_tmp_parcel tmp_parcel on application.tmp_parcel = tmp_parcel.parcel_id " \
                     "left join s{0}.ca_pasture_parcel parcel on parcel.parcel_id = application.parcel ".format(au_level2) + "\n"

            sql = sql + select

        sql = "{0} where app_type = 26 or app_type = 27 order by app_no;".format(sql)

        try:
            self.session.execute(sql)
            self.commit()
        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    def __create_pasture_monitoring_point_view(self):

        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        sql = ""

        for au_level2 in au_level2_list:

            au_level2 = au_level2.strip()
            if not sql:
                sql = "Create temp view ca_pasture_monitoring_search as" + "\n"
            else:
                sql = sql + "UNION" + "\n"

            select = "SELECT * " \
                     "FROM s{0}.ca_pasture_monitoring monitoring ".format(au_level2) + "\n"

            sql = sql + select

        try:
            self.session.execute(sql)
            self.commit()
        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    def __working_l2_changed(self, index):

        l2_code = self.working_l2_cbox.itemData(index)

        self.create_savepoint()

        try:
            role = DatabaseUtils.current_user()
            if not l2_code:
                role.working_au_level2 = None
            else:
                role.working_au_level2 = l2_code
            self.__change_workig_soum_list()
            self.commit()

            user = DatabaseUtils.current_user().user_name
            setRole = self.session.query(SetRole).filter(SetRole.user_name == user).filter(
                SetRole.is_active == True).one()
            auLevel2List = setRole.restriction_au_level2.split(",")
            schemaList = []

            for auLevel2 in auLevel2List:
                auLevel2 = auLevel2.strip()
                schemaList.append("s" + auLevel2)

            schema_string = ",".join(schemaList)

            self.session.execute(
                "SET search_path to base, codelists, admin_units, settings, pasture, public" + ", " + schema_string)

            self.session.commit()
        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_message(self,  self.tr("Sql Error"), e.message)
            return

    def __change_workig_soum_list(self):

        role = DatabaseUtils.current_user()
        first_code = None
        l1_working_code = DatabaseUtils.working_l1_code()
        working_l2_code = DatabaseUtils.working_l2_code()
        # in case of districts - sort after l1 code
        if l1_working_code[:2] == "01":
            search_path_array = DatabaseUtils.l2_restriction_array()
        else:
            search_path_array = DatabaseUtils.l2_restriction_array()

        found_code = False
        schema_string = ''
        schema_list = []
        if not working_l2_code:
            return
        first_schema = working_l2_code
        schema_list.append(first_schema)
        for item in search_path_array:
            au_level2 = item.strip()

            if item != working_l2_code:
                schema_list.append(au_level2)
        schema_string = ",".join(schema_list)

        role.restriction_au_level2 = schema_string

    def __setup_combo_boxes(self):

        try:
            PluginUtils.populate_au_level1_cbox(self.working_l1_cbox, False)

            l1_code = self.working_l1_cbox.itemData(self.working_l1_cbox.currentIndex(), Qt.UserRole)
            PluginUtils.populate_au_level2_cbox(self.working_l2_cbox, l1_code, False)

            cl_landusetype = self.session.query(ClLanduseType).all()
            cl_pasturetype = self.session.query(ClApplicationType).\
                filter(or_(ClApplicationType.code == ApplicationType.pasture_use, ClApplicationType.code == ApplicationType.right_land)).all()
            ct_member_group = self.session.query(CtPersonGroup).all()

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("Sql Error"), e.message)
            return


        self.pasture_group_cbox.addItem("*", -1)
        self.pasture_landuse_cbox.addItem("*", -1)
        self.app_type_cbox.addItem("*", -1)

        if ct_member_group is not None:
            for member in ct_member_group:
                self.pasture_group_cbox.addItem(member.group_name, member.group_no)

        if cl_landusetype is not None:
            for landuse in cl_landusetype:
                self.pasture_landuse_cbox.addItem(str(landuse.code)+':'+landuse.description, landuse.code)

        if cl_pasturetype is not None:
            for pasture in cl_pasturetype:
                self.app_type_cbox.addItem(str(pasture.code)+':'+pasture.description, pasture.code)

    @pyqtSlot()
    def on_current_dialog_closed(self):

        DialogInspector().set_dialog_visible(False)

    @pyqtSlot()
    def on_pug_register_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        pug_max_id = self.session.query(CtPersonGroup). \
            order_by(CtPersonGroup.group_no.desc()).first()

        l2_code = self.working_l2_cbox.itemData(self.working_l2_cbox.currentIndex(), Qt.UserRole)
        member_code = self.pasture_group_cbox.itemData(self.pasture_group_cbox.currentIndex())
        if member_code == -1:
            if not pug_max_id:
                member_group_new_id = 1
            else:
                if len(str(pug_max_id.group_no)) < 5:
                    member_group_new_id = pug_max_id.group_no + 1
                else:
                    member_group_new_id = int(str(pug_max_id.group_no)[4:]) + 1
            member_group_new_id = int(str(int(l2_code))+''+str(member_group_new_id))
            DatabaseUtils.set_working_schema()
            self.current_dialog = MemberGroupDialog(member_group_new_id, False, self.plugin.iface.mainWindow())
            self.current_dialog.setModal(False)
            self.current_dialog.rejected.connect(self.on_current_dialog_closed)
            DialogInspector().set_dialog_visible(True)
            self.current_dialog.show()
        else:
            member_group_new_id = self.pasture_group_cbox.itemData(self.pasture_group_cbox.currentIndex())
            self.current_dialog = MemberGroupDialog(member_group_new_id, True, self.plugin.iface.mainWindow())
            self.current_dialog.rejected.connect(self.on_current_dialog_closed)
            DialogInspector().set_dialog_visible(True)
            self.current_dialog.setModal(False)
            self.current_dialog.show()

            DatabaseUtils.set_working_schema()

    @pyqtSlot()
    def on_pasture_app_add_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        DatabaseUtils.set_working_schema()
        application = PluginUtils.create_new_application()
        self.current_dialog = ApplicationsPastureDialog(self.plugin, application, self, False, self.plugin.iface.mainWindow())
        self.current_dialog.setModal(False)
        self.current_dialog.rejected.connect(self.on_current_dialog_closed)
        DialogInspector().set_dialog_visible(True)
        self.current_dialog.show()

    @pyqtSlot()
    def on_pasture_clear_button_clicked(self):

        self.__remove_pasture_items()
        self.__clear_pasture()

    def __remove_pasture_items(self):

        self.pasture_results_twidget.setRowCount(0)
        self.pasture_results_label.setText("")

    def __clear_pasture(self):

        self.pasture_parcel_id_edit.clear()
        self.member_register_edit.clear()
        self.pasture_app_no_edit.clear()
        self.member_name_edit.clear()
        self.pasture_contract_no_edit.clear()
        self.pasture_app_date_edit.setDate(QDate.currentDate())
        self.pasture_app_date_edit.setEnabled(False)
        self.pasture_date_cbox.setChecked(False)
        self.pasture_group_cbox.setCurrentIndex(self.pasture_group_cbox.findData(-1))
        self.pasture_landuse_cbox.setCurrentIndex(self.pasture_landuse_cbox.findData(-1))
        self.app_type_cbox.setCurrentIndex(self.app_type_cbox.findData(-1))

    @pyqtSlot(int)
    def on_pasture_date_cbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.pasture_app_date_edit.setEnabled(True)
        else:
            self.pasture_app_date_edit.setEnabled(False)

    @pyqtSlot()
    def on_pasture_find_button_clicked(self):

        self.__pasture_applications()

    def __pasture_applications(self):

        # try:
        applications = self.session.query(ApplicationPastureSearch)
        filter_is_set = False
        # sub = self.session.query(ApplicationPastureSearch, func.row_number().over(partition_by=ApplicationPastureSearch.app_no,
        #                                                                    order_by=(
        #                                                                    desc(ApplicationPastureSearch.status_date),
        #                                                                    desc(ApplicationPastureSearch.status))).label("row_number")).subquery()
        # applications = applications.select_entity_from(sub).filter(sub.c.row_number == 1)
        applications = applications.filter(or_(ApplicationPastureSearch.app_type == ApplicationType.right_land,
                   ApplicationPastureSearch.app_type == ApplicationType.pasture_use))
        if self.pasture_group_cbox.currentIndex() != -1:
            if not self.pasture_group_cbox.itemData(self.pasture_group_cbox.currentIndex()) == -1:
                filter_is_set = True
                group_no = self.pasture_group_cbox.itemData(self.pasture_group_cbox.currentIndex())

                applications = applications.filter(ApplicationPastureSearch.group_no == group_no)

        if self.app_type_cbox.currentIndex() != -1:
            if not self.app_type_cbox.itemData(self.app_type_cbox.currentIndex()) == -1:
                filter_is_set = True
                app_type = self.app_type_cbox.itemData(self.app_type_cbox.currentIndex())
                applications = applications.filter(ApplicationPastureSearch.app_type == app_type)

        if self.pasture_app_no_edit.text():
            filter_is_set = True
            app_no = "%" + self.pasture_app_no_edit.text() + "%"
            applications = applications.filter(ApplicationPastureSearch.app_no.ilike(app_no))

        if self.member_name_edit.text():
            filter_is_set = True
            right_holder = self.member_name_edit.text()
            if "," in right_holder:
                right_holder_strings = right_holder.split(",")
                surname = "%" + right_holder_strings[0].strip() + "%"
                first_name = "%" + right_holder_strings[1].strip() + "%"
                applications = applications.filter(and_(func.lower(ApplicationPastureSearch.name).ilike(func.lower(surname)), func.lower(ApplicationPastureSearch.first_name).ilike(func.lower(first_name))))
            else:
                right_holder = "%" + self.member_name_edit.text() + "%"
                applications = applications.filter(or_(func.lower(ApplicationPastureSearch.name).ilike(func.lower(right_holder)), func.lower(ApplicationPastureSearch.first_name).ilike(func.lower(right_holder)), func.lower(ApplicationPastureSearch.middle_name).ilike(func.lower(right_holder))))

        if self.pasture_parcel_id_edit.text():
            filter_is_set = True
            parcel_no = "%" + self.pasture_parcel_id_edit.text() + "%"

            applications = applications.filter(ApplicationPastureSearch.parcel_id.ilike(parcel_no))

        if self.member_register_edit.text():
            filter_is_set = True
            register_no = "%" + self.member_register_edit.text() + "%"
            applications = applications.filter(ApplicationPastureSearch.person_id.ilike(register_no))

        if self.pasture_contract_no_edit.text():
            filter_is_set = True
            contract_num = "%" + self.pasture_contract_no_edit.text() + "%"
            applications = applications.filter(or_(ApplicationPastureSearch.contract_no.ilike(contract_num), ApplicationPastureSearch.record_no.ilike(contract_num)))


        if self.pasture_date_cbox.isChecked():
            filter_is_set = True
            qt_date = self.pasture_app_date_edit.date().toString(Constants.DATABASE_DATE_FORMAT)
            python_date = datetime.strptime(str(qt_date), Constants.PYTHON_DATE_FORMAT)

            applications = applications.filter(ApplicationPastureSearch.app_timestamp >= python_date)

        count = 0

        self.__remove_pasture_items()

        # if applications.distinct(ApplicationPastureSearch.app_no).count() == 0:
        #     self.error_label.setText(self.tr("No applications found for this search filter."))
        #     return

        if filter_is_set is False:
            self.error_label.setText(self.tr("Please specify a search filter."))
            return

        for application in applications.distinct(ApplicationPastureSearch.app_no, ApplicationPastureSearch.status).all():

            app_type = "" if not application.app_type_ref else application.app_type_ref.description
            item = QTableWidgetItem(str(application.app_no) + " ( " + unicode(app_type) + " )")
            if application.status == 9:
                item.setBackground(QtGui.QColor(133, 193, 233 ))
            elif application.status == 7:
                item.setBackground(QtGui.QColor(88, 214, 141))
            elif application.status == 6:
                item.setBackground(QtGui.QColor(213, 219, 219))
            else:
                item.setBackground(QtGui.QColor(249, 231, 159))
            item.setIcon(QIcon(QPixmap(":/plugins/lm2/application.png")))
            item.setData(Qt.UserRole, application.app_no)
            self.pasture_results_twidget.insertRow(count)
            self.pasture_results_twidget.setItem(count, 0, item)
            count += 1

        self.error_label.setText("")
        self.pasture_results_label.setText(self.tr("Results: ") + str(count))

        # except SQLAlchemyError, e:
        #     PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
        #     return

    @pyqtSlot(QTableWidgetItem)
    def on_pasture_results_twidget_itemDoubleClicked(self, item):

        if DialogInspector().dialog_visible():
            return

        app_instance = self.__selected_application()

        if app_instance is not None:
            self.current_dialog = ApplicationsPastureDialog(self.plugin,app_instance, self, True, self.plugin.iface.mainWindow())
            DialogInspector().set_dialog_visible(True)
            self.current_dialog.rejected.connect(self.on_current_dialog_closed)
            self.current_dialog.setModal(False)
            self.current_dialog.show()

    def __selected_application(self):

        selected_items = self.pasture_results_twidget.selectedItems()

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

    @pyqtSlot()
    def on_draft_decision_button_clicked(self):

        self.dlg = SentToGovernorPastureDialog(False, self.plugin.iface.mainWindow())
        self.dlg.show()

    @pyqtSlot()
    def on_pasture_app_view_button_clicked(self):

        if DialogInspector().dialog_visible():
            return

        app_instance = self.__selected_application()

        if app_instance is not None:
            self.current_dialog = ApplicationsPastureDialog(self.plugin, app_instance, self, True, self.plugin.iface.mainWindow())
            DialogInspector().set_dialog_visible(True)
            self.current_dialog.rejected.connect(self.on_current_dialog_closed)
            self.current_dialog.setModal(False)
            self.current_dialog.show()

    @pyqtSlot(QTableWidgetItem)
    def on_pasture_results_twidget_itemClicked(self, item):

        id = item.data(Qt.UserRole)
        soum_code = id.split("-")[0]
        aimag_code = soum_code[:3]
        self.working_l1_cbox.setCurrentIndex(self.working_l1_cbox.findData(aimag_code))
        self.working_l2_cbox.setCurrentIndex(self.working_l2_cbox.findData(soum_code))
        try:
            app_result = self.session.query(ApplicationPastureSearch).filter(ApplicationPastureSearch.app_no == id).one()
            self.pasture_app_no_edit.setText(app_result.app_no)
            self.member_name_edit.setText(app_result.first_name)
            self.pasture_parcel_id_edit.setText(app_result.parcel_id)
            self.member_register_edit.setText(app_result.person_id)
            if app_result.contract_no != None:
                self.pasture_contract_no_edit.setText(app_result.contract_no)
                self.pasture_contract_no_edit.setStyleSheet(self.styleSheet())
            else:
                self.pasture_contract_no_edit.setText(self.tr('No Contract'))
                self.pasture_contract_no_edit.setStyleSheet("color: rgb(189, 21, 38)")

            self.pasture_group_cbox.setCurrentIndex(self.pasture_group_cbox.findData(app_result.group_no))
            self.app_type_cbox.setCurrentIndex(self.app_type_cbox.findData(app_result.pasture_type))

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"),
                                   self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    @pyqtSlot()
    def on_pasture_layer_view_button_clicked(self):

        root = QgsProject.instance().layerTreeRoot()

        restrictions = DatabaseUtils.working_l2_code()

        mygroup = root.findGroup("PUG")
        if mygroup is None:
            mygroup = root.insertGroup(7, "PUG")
        is_layer = False
        is_eco_layer = False
        is_pug_parcel = False
        is_pug_building = False
        is_monitoring_layer = False
        is_natural_zone_layer = False

        monitoring_layer = LayerUtils.load_layer_by_name_pasture_monitoring("ca_pasture_monitoring", "point_id", restrictions)
        natural_zone_layaer = LayerUtils.load_layer_by_name_pasture_monitoring("au_natural_zone", "code",
                                                                            restrictions)
        vlayer = LayerUtils.load_layer_by_name_report("ca_pug_boundary", "code", restrictions)
        vlayer_eco = LayerUtils.load_layer_by_name_report("ca_pug_eco", "code", restrictions)
        vlayer_parcel = LayerUtils.load_layer_by_name_report("ca_pasture_parcel", "parcel_id", restrictions)
        vlayer_building = LayerUtils.load_layer_by_name_report("ca_pasture_building", "building_id", restrictions)
        # vlayer_monitoring_point = LayerUtils.load_layer_by_name_report("ca_pasture_monitoring", "point_id", restrictions)

        layers = self.plugin.iface.legendInterface().layers()

        for layer in layers:
            if layer.name() == "PUGBuilding"+'_' + restrictions or layer.name() == u"БАХ байшин"+'_' + restrictions:
                is_pug_building = True
        if not is_pug_building:
            mygroup.addLayer(vlayer_building)

        for layer in layers:
            if layer.name() == "PUGParcel"+'_' + restrictions or layer.name() == u"БАХ нэгж талбар"+'_' + restrictions:
                is_pug_parcel = True
        if not is_pug_parcel:
            mygroup.addLayer(vlayer_parcel)

        for layer in layers:
            if layer.name() == "PUGBoundary"+'_' + restrictions or layer.name() == u"БАХ-ийн хил"+'_' + restrictions:
                is_layer = True
        if not is_layer:
            mygroup.addLayer(vlayer)

        for layer in layers:
            if layer.name() == "PUGEcological"+'_' + restrictions or layer.name() == u"БАХ экологийн чадавхи"+'_' + restrictions:
                is_eco_layer = True
        if not is_eco_layer:
            mygroup.addLayer(vlayer_eco)

        for layer in layers:
            if layer.name() == "PastureMonitoringPoint" or layer.name() == u"Мониторингийн Цэг":
                is_monitoring_layer = True
        if not is_monitoring_layer:
            mygroup.addLayer(monitoring_layer)

        for layer in layers:
            if layer.name() == "NaturalZone" or layer.name() == u"Байгалийн бүс, бүслүүр":
                is_natural_zone_layer = True
        if not is_natural_zone_layer:
            mygroup.addLayer(natural_zone_layaer)

        vlayer.setLayerName(QApplication.translate("Plugin", "PUGBoundary") + '_' + restrictions)
        vlayer.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) + "template\style/pug_boundary.qml")
        vlayer_eco.setLayerName(QApplication.translate("Plugin", "PUGEcological") + '_' + restrictions)
        vlayer_eco.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) + "template\style/pug_eco.qml")
        vlayer_parcel.setLayerName(QApplication.translate("Plugin", "PUGParcel") + '_' + restrictions)
        vlayer_parcel.loadNamedStyle(str(os.path.dirname(os.path.realpath(__file__))[:-10]) + "template\style/pug_parcel.qml")
        vlayer_building.setLayerName(QApplication.translate("Plugin", "PUGBuilding") + '_' + restrictions)

        monitoring_layer.setLayerName(QApplication.translate("Plugin", "PastureMonitoringPoint"))
        monitoring_layer.loadNamedStyle(
            str(os.path.dirname(os.path.realpath(__file__))[:-10]) + "template\style/ca_monitoring_point.qml")

        natural_zone_layaer.setLayerName(QApplication.translate("Plugin", "NaturalZone"))
        natural_zone_layaer.loadNamedStyle(
            str(os.path.dirname(os.path.realpath(__file__))[:-10]) + "template\style/ca_nat_zone_marged.qml")

        legend = self.plugin.iface.legendInterface()  # access the legend
        legend.setLayerVisible(vlayer, False)
        legend.setLayerVisible(vlayer_eco, False)

    @pyqtSlot()
    def on_settings_button_clicked(self):

        self.current_dialog = PastureSettings(self.plugin.iface.mainWindow())
        self.current_dialog.setModal(False)
        self.current_dialog.rejected.connect(self.on_current_dialog_closed)
        DialogInspector().set_dialog_visible(True)
        self.current_dialog.show()

    @pyqtSlot()
    def on_monitoring_load_button_clicked(self):

        self.current_dialog = PastureMonitoringValueDialog(self.plugin, self.plugin.iface.mainWindow())
        self.current_dialog.setModal(False)
        self.current_dialog.rejected.connect(self.on_current_dialog_closed)
        DialogInspector().set_dialog_visible(True)
        self.current_dialog.show()

    # Daats level

    def __aimag_changed(self, index):

        l1_code = self.aimag_cbox.itemData(index)
        try:

            PluginUtils.populate_au_level2_cbox(self.soum_cbox, l1_code, False)

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_message(self,  self.tr("Sql Error"), e.message)
            return

    def __soum_changed(self, index):

        l2_code = self.soum_cbox.itemData(index)
        self.pug_cbox.clear()
        self.bag_cbox.clear()
        try:
            if l2_code:
                pug_boundaries = self.session.query(PsPastureBoundary.pug_name, PsPastureBoundary.pug_code).filter(
                    PsPastureBoundary.au2_code == l2_code).group_by(PsPastureBoundary.pug_name, PsPastureBoundary.pug_code).all()
                PluginUtils.populate_au_level3_cbox(self.bag_cbox, l2_code, False)

                for pug_boundary in pug_boundaries:
                    pug_name = ''
                    if pug_boundary.pug_name:
                        pug_name = pug_boundary.pug_name
                    if pug_boundary.pug_code:
                        self.pug_cbox.addItem(pug_boundary.pug_code + ':' + pug_name, pug_boundary.pug_code)

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_message(self,  self.tr("Sql Error"), e.message)
            return

    def __daats_twidget_setup(self):

        self.points_results_twidget.setColumnCount(1)
        self.points_results_twidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.points_results_twidget.horizontalHeader().setVisible(False)
        self.points_results_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.points_results_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.points_results_twidget.setDragEnabled(True)
        self.points_results_twidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.points_results_twidget.customContextMenuRequested.connect(self.on_custom_context_menu_requested)

        self.reserve_points_results_twidget.setColumnCount(1)
        self.reserve_points_results_twidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.reserve_points_results_twidget.horizontalHeader().setVisible(False)
        self.reserve_points_results_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.reserve_points_results_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.reserve_points_results_twidget.setDragEnabled(True)
        self.reserve_points_results_twidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.reserve_points_results_twidget.customContextMenuRequested.connect(self.on_custom_context_menu_requested)

    def __pasture_cbox_setup(self):

        self.daats_level_cbox.clear()
        daats_levels = self.session.query(PClPastureDaatsLevel).order_by(PClPastureDaatsLevel.code.asc()).all()

        self.aimag_cbox.currentIndexChanged.connect(self.__aimag_changed)
        self.soum_cbox.currentIndexChanged.connect(self.__soum_changed)

        PluginUtils.populate_au_level1_cbox(self.aimag_cbox, False)
        l1_code = self.aimag_cbox.itemData(self.aimag_cbox.currentIndex(), Qt.UserRole)
        PluginUtils.populate_au_level2_cbox(self.soum_cbox, l1_code, False)

        l2_code = self.soum_cbox.itemData(self.soum_cbox.currentIndex(), Qt.UserRole)
        PluginUtils.populate_au_level3_cbox(self.bag_cbox, l2_code, False)

        for daats_level in daats_levels:
            self.daats_level_cbox.addItem(daats_level.description, daats_level.code)

    @pyqtSlot(int)
    def on_daats_level_chbox_stateChanged(self, state):

        self.__daats_twidget_setup()

        if state == Qt.Checked:
            self.__pasture_cbox_setup()
            self.point_find_button.setEnabled(True)
            self.daats_level_cbox.setEnabled(True)
        else:
            self.daats_level_cbox.setEnabled(False)

    @pyqtSlot(int)
    def on_pug_cbox_currentIndexChanged(self, index):

        self.pug_parcel_cbox.clear()
        l2_code = self.soum_cbox.itemData(self.soum_cbox.currentIndex(), Qt.UserRole)

        pug_code = self.pug_cbox.itemData(self.pug_cbox.currentIndex(), Qt.UserRole)
        pasture_parcels = self.session.query(PsPastureBoundary.pasture_land_name, PsPastureBoundary.parcel_id) \
            .filter(PsPastureBoundary.au2_code == l2_code) \
            .filter(PsPastureBoundary.pug_code == pug_code) \
            .group_by(PsPastureBoundary.pasture_land_name, PsPastureBoundary.parcel_id).all()

        for pasture_parcel in pasture_parcels:
            pasture_land_name = ''
            if pasture_parcel.pasture_land_name:
                pasture_land_name = pasture_parcel.pasture_land_name
            self.pug_parcel_cbox.addItem(pasture_parcel.parcel_id +':'+ pasture_land_name, pasture_parcel.parcel_id)

    @pyqtSlot(int)
    def on_daats_level_cbox_currentIndexChanged(self, index):

        level = self.daats_level_cbox.itemData(index)
        if level == DAATS_LEVEL_1:
            self.aimag_cbox.setEnabled(False)
            self.soum_cbox.setEnabled(False)
            self.bag_cbox.setEnabled(False)
            self.pug_cbox.setEnabled(False)
            self.pug_parcel_cbox.setEnabled(False)
        if level == DAATS_LEVEL_2:
            self.aimag_cbox.setEnabled(True)
            self.soum_cbox.setEnabled(False)
            self.bag_cbox.setEnabled(False)
            self.pug_cbox.setEnabled(False)
            self.pug_parcel_cbox.setEnabled(False)
        if level == DAATS_LEVEL_3:
            self.aimag_cbox.setEnabled(True)
            self.soum_cbox.setEnabled(True)
            self.bag_cbox.setEnabled(False)
            self.pug_cbox.setEnabled(False)
            self.pug_parcel_cbox.setEnabled(False)
        if level == DAATS_LEVEL_4:
            self.aimag_cbox.setEnabled(True)
            self.soum_cbox.setEnabled(True)
            self.bag_cbox.setEnabled(True)
            self.pug_cbox.setEnabled(False)
            self.pug_parcel_cbox.setEnabled(False)
        if level == DAATS_LEVEL_5:
            self.aimag_cbox.setEnabled(True)
            self.soum_cbox.setEnabled(True)
            self.bag_cbox.setEnabled(True)
            self.pug_cbox.setEnabled(True)
            self.pug_parcel_cbox.setEnabled(False)
        if level == DAATS_LEVEL_6:
            self.aimag_cbox.setEnabled(True)
            self.soum_cbox.setEnabled(True)
            self.bag_cbox.setEnabled(True)
            self.pug_cbox.setEnabled(True)
            self.pug_parcel_cbox.setEnabled(True)

    @pyqtSlot()
    def on_point_find_button_clicked(self):

        self.avg_d3_edit.setText(str(0))
        self.avg_sheep_unit_edit.setText(str(0))
        self.avg_unelgee_edit.setText(str(0))

        pasture_area = 0
        pasture_duration = 0

        daats_points = self.session.query(PsPointDaatsValue)
        level = self.daats_level_cbox.itemData(self.daats_level_cbox.currentIndex())
        daats_year = self.daats_year_sbox.value()
        daats_points = daats_points.filter(PsPointDaatsValue.monitoring_year == daats_year)
        if level == DAATS_LEVEL_2:

            if self.aimag_cbox.currentIndex() != -1:
                pasture_duration = 180
                au1_code = self.aimag_cbox.itemData(self.aimag_cbox.currentIndex(), Qt.UserRole)
                aimag = self.session.query(AuLevel1).filter(AuLevel1.code == au1_code).one()
                pasture_area = round(float(aimag.area_m2 / 10000), 2)
                daats_points = daats_points\
                    .join(PsPointDetail, PsPointDaatsValue.point_detail_id == PsPointDetail.point_detail_id)\
                    .join(PsPointDetailPoints, PsPointDaatsValue.point_detail_id == PsPointDetailPoints.point_detail_id) \
                    .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
                    .filter(CaPastureMonitoring.geometry.ST_Intersects(AuLevel1.geometry)) \
                    .filter(AuLevel1.code == au1_code).all()

        if level == DAATS_LEVEL_3:

            if self.soum_cbox.currentIndex() != -1:
                pasture_duration = 180
                au2_code = self.soum_cbox.itemData(self.soum_cbox.currentIndex(), Qt.UserRole)
                soum = self.session.query(AuLevel2).filter(AuLevel2.code == au2_code).one()
                pasture_area = round(float(soum.area_m2 / 10000), 2)
                daats_points = daats_points\
                    .join(PsPointDetail, PsPointDaatsValue.point_detail_id == PsPointDetail.point_detail_id)\
                    .join(PsPointDetailPoints, PsPointDaatsValue.point_detail_id == PsPointDetailPoints.point_detail_id) \
                    .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
                    .filter(CaPastureMonitoring.geometry.ST_Intersects(AuLevel2.geometry)) \
                    .filter(AuLevel2.code == au2_code).all()

        if level == DAATS_LEVEL_4:

            if self.bag_cbox.currentIndex() != -1:
                pasture_duration = 180
                au3_code = self.bag_cbox.itemData(self.bag_cbox.currentIndex(), Qt.UserRole)
                bag = self.session.query(AuLevel3).filter(AuLevel3.code == au3_code).one()
                pasture_area = round(float(bag.area_m2 / 10000), 2)
                daats_points = daats_points\
                    .join(PsPointDetail, PsPointDaatsValue.point_detail_id == PsPointDetail.point_detail_id)\
                    .join(PsPointDetailPoints, PsPointDaatsValue.point_detail_id == PsPointDetailPoints.point_detail_id) \
                    .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
                    .filter(CaPastureMonitoring.geometry.ST_Intersects(AuLevel3.geometry)) \
                    .filter(AuLevel3.code == au3_code).all()

        if level == DAATS_LEVEL_5:

            if self.pug_cbox.currentIndex() != -1:
                pasture_duration = 180
                pug_code = self.pug_cbox.itemData(self.pug_cbox.currentIndex(), Qt.UserRole)
                pug = self.session.query(PsPastureBoundary.pug_code, PsPastureBoundary.pug_area).filter(
                    PsPastureBoundary.pug_code == pug_code). \
                    group_by(PsPastureBoundary.pug_code, PsPastureBoundary.pug_area).one()
                pasture_area = round(float(pug.pug_area), 2)
                daats_points = daats_points\
                    .join(PsPointDetail, PsPointDaatsValue.point_detail_id == PsPointDetail.point_detail_id)\
                    .join(PsPointDetailPoints, PsPointDaatsValue.point_detail_id == PsPointDetailPoints.point_detail_id) \
                    .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
                    .filter(CaPastureMonitoring.geometry.ST_Intersects(PsPastureBoundary.pug_geom)) \
                    .filter(PsPastureBoundary.pug_code == pug_code).all()

        if level == DAATS_LEVEL_6:

            if self.pug_parcel_cbox.currentIndex() != -1:
                pug_parcel_id = self.pug_parcel_cbox.itemData(self.pug_parcel_cbox.currentIndex(), Qt.UserRole)
                pug_parcel = self.session.query(PsPastureBoundary.parcel_id, PsPastureBoundary.pasture_area).filter(
                    PsPastureBoundary.parcel_id == pug_parcel_id).\
                    group_by(PsPastureBoundary.parcel_id, PsPastureBoundary.pasture_area).one()

                pasture_duration = self.session.query(PsParcelDuration).filter(PsParcelDuration.parcel == pug_parcel_id).first()
                pasture_duration = pasture_duration.days
                pasture_area = round(float(pug_parcel.pasture_area), 2)
                daats_points = daats_points\
                    .join(PsPointDetail, PsPointDaatsValue.point_detail_id == PsPointDetail.point_detail_id)\
                    .join(PsPointDetailPoints, PsPointDaatsValue.point_detail_id == PsPointDetailPoints.point_detail_id) \
                    .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
                    .filter(CaPastureMonitoring.geometry.ST_Intersects(PsPastureBoundary.parcel_geom)) \
                    .filter(PsPastureBoundary.parcel_id == pug_parcel_id).all()

        self.points_results_twidget.setRowCount(0)

        pasture_rc = 0
        pasture_biomass = 0
        count = 0
        all_sheep_unit = 0
        all_d3 = 0
        all_unelgee = 0
        all_present = 0
        for daats_point in daats_points:
            rc = self.session.query(PsRecoveryClass).filter(PsRecoveryClass.id == daats_point.rc_id).one()
            point_detail = self.session.query(PsPointDetail).filter(PsPointDetail.point_detail_id == daats_point.point_detail_id).one()
            # text_value = str(daats_point.point_detail_id) + " ( " + unicode(point_detail.land_name) + " )" + \
            #              '(' + str(round(daats_point.d3, 2)) + '-' +str(round(daats_point.sheep_unit, 2)) + '='+ str(round(daats_point.unelgee, 2)) +')'
            text_value = str(daats_point.point_detail_id) + " ( " + unicode(point_detail.land_name) + " )"
            item = QTableWidgetItem(text_value)
            item.setBackground(Qt.gray)
            item.setIcon(QIcon(QPixmap(":/plugins/lm2/application.png")))
            item.setData(Qt.UserRole, daats_point.point_detail_id)
            self.points_results_twidget.insertRow(count)
            self.points_results_twidget.setItem(count, 0, item)
            count += 1

            pasture_rc = pasture_rc + rc.rc_code_number
            pasture_biomass = pasture_biomass + daats_point.biomass

            all_sheep_unit = all_sheep_unit + daats_point.sheep_unit
            all_d3 = all_d3 + daats_point.d3
            all_unelgee = all_unelgee + daats_point.unelgee
            all_present = all_present + daats_point.rc_precent

        self.point_results_label.setText(self.tr("Results: ") + str(count))

        avg_sheep_unit = 0
        if count == 0:
            self.pasture_duration_edit.setText(str(0))
            self.pasture_duration_edit.setEnabled(False)
            self.pasture_biomass_eidt.setText('')
            self.pasture_biomass_eidt.setEnabled(False)
            self.pasture_rc_edit.setText('')
            self.pasture_rc_edit.setEnabled(False)

            self.avg_d3_edit.setText(str(0))
            self.avg_d3_edit.setEnabled(False)
            self.avg_sheep_unit_edit.setText(str(0))
            self.avg_sheep_unit_edit.setEnabled(False)
            self.avg_unelgee_edit.setText(str(0))
            self.avg_unelgee_edit.setEnabled(False)
            self.avg_value_save_button.setEnabled(False)
            return
        else:
            self.pasture_duration_edit.setText(str(0))
            self.pasture_duration_edit.setEnabled(True)
            self.pasture_biomass_eidt.setText('')
            self.pasture_biomass_eidt.setEnabled(True)
            self.pasture_rc_edit.setText('')
            self.pasture_rc_edit.setEnabled(True)

            self.avg_d3_edit.setText(str(0))
            self.avg_d3_edit.setEnabled(True)
            self.avg_sheep_unit_edit.setText(str(0))
            self.avg_sheep_unit_edit.setEnabled(True)
            self.avg_unelgee_edit.setText(str(0))
            self.avg_unelgee_edit.setEnabled(True)
            self.avg_value_save_button.setEnabled(True)

        avg_rc = int(pasture_rc / count)

        rc = self.session.query(PsRecoveryClass).filter(PsRecoveryClass.rc_code_number == avg_rc).first()
        rc_precent = rc.rc_precent
        avg_present = all_present/count
        self.pasture_area_edit.setText(str(pasture_area))
        self.pasture_duration_edit.setText(str(pasture_duration))
        self.pasture_rc_edit.setText(str(avg_present))

        avg_biomass = round(float(pasture_biomass / count), 2)
        self.pasture_biomass_eidt.setText(str(avg_biomass))
        biomass_present = avg_biomass*avg_present/100
        self.pasture_biomass_present_edit.setText(str(biomass_present))

        rc_precent = float(rc_precent) / 100

        d3 = self.__calculate_capacity(pasture_area, biomass_present, pasture_duration)

        self.avg_d3_edit.setText(str(d3))

    def __calculate_capacity(self, area, biomass_present, duration):

        if duration > 0:
            d3 = int(float(area) * biomass_present / float(duration * 1.4))
        else:
            d3 = int(float(area) * biomass_present / float(1 * 1.4))
        return d3

    @pyqtSlot()
    def on_avg_value_save_button_clicked(self):

        level1_all = None
        level2_au1 = None
        level3_au2 = None
        level4_au3 = None
        level5_pug = None
        level6_parcel = None

        current_year = self.daats_year_sbox.value()
        avg_d3 = float(self.avg_d3_edit.text())
        avg_sheep_unit = float(self.avg_sheep_unit_edit.text())
        avg_unelgee = float(self.avg_unelgee_edit.text())

        level = self.daats_level_cbox.itemData(self.daats_level_cbox.currentIndex())

        count = None
        if level == DAATS_LEVEL_1:
            count = self.session.query(PsAvgDaats).filter(PsAvgDaats.daats_level_type == level)\
            .filter(PsAvgDaats.current_year == current_year).count()
        if level == DAATS_LEVEL_2:
            level2_au1 = self.aimag_cbox.itemData(self.aimag_cbox.currentIndex())
            count = self.session.query(PsAvgDaats).filter(PsAvgDaats.daats_level_type == level) \
                .filter(PsAvgDaats.level1 == level2_au1)\
                .filter(PsAvgDaats.current_year == current_year).count()
        if level == DAATS_LEVEL_3:
            level3_au2 = self.soum_cbox.itemData(self.soum_cbox.currentIndex())
            count = self.session.query(PsAvgDaats).filter(PsAvgDaats.daats_level_type == level) \
                .filter(PsAvgDaats.level2 == level3_au2) \
                .filter(PsAvgDaats.current_year == current_year).count()
        if level == DAATS_LEVEL_4:
            level4_au3 = self.bag_cbox.itemData(self.bag_cbox.currentIndex())
            count = self.session.query(PsAvgDaats).filter(PsAvgDaats.daats_level_type == level) \
                .filter(PsAvgDaats.level3 == level4_au3) \
                .filter(PsAvgDaats.current_year == current_year).count()
        if level == DAATS_LEVEL_5:
            level5_pug = self.pug_cbox.itemData(self.pug_cbox.currentIndex())
            count = self.session.query(PsAvgDaats).filter(PsAvgDaats.daats_level_type == level) \
                .filter(PsAvgDaats.pasture_group == level5_pug) \
                .filter(PsAvgDaats.current_year == current_year).count()
        if level == DAATS_LEVEL_6:
            level6_parcel = self.pug_parcel_cbox.itemData(self.pug_parcel_cbox.currentIndex())
            count = self.session.query(PsAvgDaats).filter(PsAvgDaats.daats_level_type == level) \
                .filter(PsAvgDaats.pasture_parcel == level6_parcel) \
                .filter(PsAvgDaats.current_year == current_year).count()

        # if not count:
        #     return

        if count == 0:
            avg_daats = PsAvgDaats()
            avg_daats.current_year = current_year
            avg_daats.avg_sheep_unit = avg_sheep_unit
            avg_daats.avg_d3 = avg_d3
            avg_daats.avg_unelgee = avg_unelgee
            avg_daats.daats_level_type = level
            avg_daats.level1 = level2_au1
            avg_daats.level2 = level3_au2
            avg_daats.level3 = level4_au3
            avg_daats.pasture_group = level5_pug
            avg_daats.pasture_parcel = level6_parcel

            self.session.add(avg_daats)
            PluginUtils.show_message(self, self.tr("success"), self.tr("Successfully"))
        else:
            message_box = QMessageBox()
            message_box.setText(self.tr("Do you want to edit the information for daats ?"))

            update_button = message_box.addButton(self.tr("Update"), QMessageBox.ActionRole)
            message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
            message_box.exec_()

            if message_box.clickedButton() == update_button:
                if level == DAATS_LEVEL_1:
                    avg_daats = self.session.query(PsAvgDaats).filter(PsAvgDaats.daats_level_type == level) \
                        .filter(PsAvgDaats.current_year == current_year).one()
                    avg_daats.avg_sheep_unit = avg_sheep_unit
                    avg_daats.avg_d3 = avg_d3
                    avg_daats.avg_unelgee = avg_unelgee
                if level == DAATS_LEVEL_2:
                    avg_daats = self.session.query(PsAvgDaats).filter(PsAvgDaats.daats_level_type == level) \
                        .filter(PsAvgDaats.level1 == level2_au1)\
                        .filter(PsAvgDaats.current_year == current_year).one()
                    avg_daats.avg_sheep_unit = avg_sheep_unit
                    avg_daats.avg_d3 = avg_d3
                    avg_daats.avg_unelgee = avg_unelgee
                if level == DAATS_LEVEL_3:
                    avg_daats = self.session.query(PsAvgDaats).filter(PsAvgDaats.daats_level_type == level) \
                        .filter(PsAvgDaats.level2 == level3_au2) \
                        .filter(PsAvgDaats.current_year == current_year).one()
                    avg_daats.avg_sheep_unit = avg_sheep_unit
                    avg_daats.avg_d3 = avg_d3
                    avg_daats.avg_unelgee = avg_unelgee
                if level == DAATS_LEVEL_4:
                    avg_daats = self.session.query(PsAvgDaats).filter(PsAvgDaats.daats_level_type == level) \
                        .filter(PsAvgDaats.level3 == level4_au3)\
                        .filter(PsAvgDaats.current_year == current_year).one()
                    avg_daats.avg_sheep_unit = avg_sheep_unit
                    avg_daats.avg_d3 = avg_d3
                    avg_daats.avg_unelgee = avg_unelgee
                if level == DAATS_LEVEL_5:
                    avg_daats = self.session.query(PsAvgDaats).filter(PsAvgDaats.daats_level_type == level) \
                        .filter(PsAvgDaats.pasture_group == level5_pug)\
                        .filter(PsAvgDaats.current_year == current_year).one()
                    avg_daats.avg_sheep_unit = avg_sheep_unit
                    avg_daats.avg_d3 = avg_d3
                    avg_daats.avg_unelgee = avg_unelgee
                if level == DAATS_LEVEL_6:
                    avg_daats = self.session.query(PsAvgDaats).filter(PsAvgDaats.daats_level_type == level) \
                        .filter(PsAvgDaats.pasture_parcel == level6_parcel)\
                        .filter(PsAvgDaats.current_year == current_year).one()
                    avg_daats.avg_sheep_unit = avg_sheep_unit
                    avg_daats.avg_d3 = avg_d3
                    avg_daats.avg_unelgee = avg_unelgee
        self.session.commit()

    # reserve daats

    def __reserve_cbox_setup(self):

        reserve_daats_levels = self.session.query(PClReserveDaatsLevel).all()

        reserve_zones = self.session.query(AuReserveZone).all()

        for reserve_zone in reserve_zones:
            self.reserve_zone_cbox.addItem(reserve_zone.name, reserve_zone.code)

        for reserve_daats_level in reserve_daats_levels:
            self.reserve_daats_level_cbox.addItem(reserve_daats_level.description, reserve_daats_level.code)

    @pyqtSlot(int)
    def on_reserve_daats_chbox_stateChanged(self, state):

        self.__daats_twidget_setup()

        if state == Qt.Checked:
            self.__reserve_cbox_setup()
            self.reserve_point_find_button.setEnabled(True)
            self.reserve_daats_level_cbox.setEnabled(True)
        else:
            self.reserve_daats_level_cbox.setEnabled(False)
            self.reserve_point_find_button.setEnabled(False)

    @pyqtSlot(int)
    def on_reserve_zone_cbox_currentIndexChanged(self, index):

        self.reserve_parcel_cbox.clear()
        otor_zone_id = self.reserve_zone_cbox.itemData(self.reserve_zone_cbox.currentIndex(), Qt.UserRole)
        if not otor_zone_id:
            return
        if otor_zone_id != -1:
            otor_zones = self.session.query(AuReserveZone).filter(AuReserveZone.code == otor_zone_id).one()
            otor_parcels = self.session.query(PsParcel).filter(
                PsParcel.geometry.ST_Intersects(otor_zones.geometry)).all()

            if otor_parcels is not None:
                for parcel in otor_parcels:
                    address_neighbourhood = ''
                    if parcel.address_neighbourhood:
                        address_neighbourhood = parcel.address_neighbourhood
                    self.reserve_parcel_cbox.addItem(parcel.parcel_id + ' | ' + address_neighbourhood, parcel.parcel_id)

    @pyqtSlot()
    def on_reserve_point_find_button_clicked(self):

        self.reserve_avg_d3_edit.setText(str(0))
        self.reserve_avg_sheep_unit_edit.setText(str(0))
        self.reserve_avg_unelgee_edit.setText(str(0))

        level = self.reserve_daats_level_cbox.itemData(self.reserve_daats_level_cbox.currentIndex())
        daats_year = self.reserver_daats_year_sbox.value()

        daats_points = self.session.query(PsPointDaatsValue) \
            .join(PsPointDetail, PsPointDaatsValue.point_detail_id == PsPointDetail.point_detail_id) \
            .join(PsPointDetailPoints, PsPointDaatsValue.point_detail_id == PsPointDetailPoints.point_detail_id) \
            .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
            .filter(PsPointDaatsValue.monitoring_year == daats_year)\
            .filter(CaPastureMonitoring.geometry.ST_Intersects(AuReserveZone.geometry)).all()

        if level == RESERVE_DAATS_LEVEL_2:
            zone_code = self.reserve_zone_cbox.itemData(self.reserve_zone_cbox.currentIndex(), Qt.UserRole)
            if self.reserve_zone_cbox.currentIndex() != -1:
                daats_points = self.session.query(PsPointDaatsValue) \
                    .join(PsPointDetail, PsPointDaatsValue.point_detail_id == PsPointDetail.point_detail_id) \
                    .join(PsPointDetailPoints, PsPointDaatsValue.point_detail_id == PsPointDetailPoints.point_detail_id) \
                    .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
                    .filter(CaPastureMonitoring.geometry.ST_Intersects(AuReserveZone.geometry))\
                    .filter(AuReserveZone.code == zone_code).all()
        if level == RESERVE_DAATS_LEVEL_3:
            zone_code = self.reserve_zone_cbox.itemData(self.reserve_zone_cbox.currentIndex(), Qt.UserRole)
            reserve_parcel_id = self.reserve_parcel_cbox.itemData(self.reserve_parcel_cbox.currentIndex(), Qt.UserRole)
            if self.reserve_zone_cbox.currentIndex() != -1:
                daats_points = self.session.query(PsPointDaatsValue) \
                    .join(PsPointDetail, PsPointDaatsValue.point_detail_id == PsPointDetail.point_detail_id) \
                    .join(PsPointDetailPoints, PsPointDaatsValue.point_detail_id == PsPointDetailPoints.point_detail_id) \
                    .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
                    .filter(CaPastureMonitoring.geometry.ST_Intersects(AuReserveZone.geometry))\
                    .filter(CaPastureMonitoring.geometry.ST_Intersects(PsParcel.geometry)) \
                    .filter(AuReserveZone.code == zone_code) \
                    .filter(PsParcel.parcel_id == reserve_parcel_id).all()

        self.reserve_points_results_twidget.setRowCount(0)
        count = 0
        all_sheep_unit = 0
        all_d3 = 0
        all_unelgee = 0
        for daats_point in daats_points:

            point_detail = self.session.query(PsPointDetail).filter(
                PsPointDetail.point_detail_id == daats_point.point_detail_id).one()
            # text_value = str(daats_point.point_detail_id) + " ( " + unicode(point_detail.land_name) + " )" + \
            #              '(' + str(round(daats_point.d3, 2)) + '-' + str(round(daats_point.sheep_unit, 2)) + '=' + str(
            #     round(daats_point.unelgee, 2)) + ')'
            text_value = str(daats_point.point_detail_id) + " ( " + unicode(point_detail.land_name) + " )"
            item = QTableWidgetItem(text_value)
            item.setBackground(Qt.gray)
            item.setIcon(QIcon(QPixmap(":/plugins/lm2/application.png")))
            item.setData(Qt.UserRole, daats_point.point_detail_id)
            self.reserve_points_results_twidget.insertRow(count)
            self.reserve_points_results_twidget.setItem(count, 0, item)
            count += 1

            all_sheep_unit = all_sheep_unit + daats_point.sheep_unit
            all_d3 = all_d3 + daats_point.d3
            all_unelgee = all_unelgee + daats_point.unelgee

        self.reserve_point_results_label.setText(self.tr("Results: ") + str(count))
        avg_sheep_unit = 0
        if count == 0:
            return
        if all_sheep_unit > 0:
            avg_sheep_unit = round(all_sheep_unit / count, 2)
        avg_d3 = 0
        if all_d3 > 0:
            avg_d3 = round(all_d3 / count, 2)
        # avg_unelgee = 0
        # if all_unelgee > 0:
        avg_unelgee = round(all_unelgee / count, 2)

        self.reserve_avg_d3_edit.setText(str(avg_d3))
        self.reserve_avg_sheep_unit_edit.setText(str(avg_sheep_unit))
        self.reserve_avg_unelgee_edit.setText(str(avg_unelgee))

        if count > 0:
            self.reserve_avg_value_save_button.setEnabled(True)
        else:
            self.reserve_avg_value_save_button.setEnabled(False)


    @pyqtSlot(int)
    def on_reserve_daats_level_cbox_currentIndexChanged(self, index):

        level = self.reserve_daats_level_cbox.itemData(index)
        if level == RESERVE_DAATS_LEVEL_1:
            self.reserve_zone_cbox.setEnabled(False)
            self.reserve_parcel_cbox.setEnabled(False)
        if level == RESERVE_DAATS_LEVEL_2:
            self.reserve_zone_cbox.setEnabled(True)
            self.reserve_parcel_cbox.setEnabled(False)
        if level == RESERVE_DAATS_LEVEL_3:
            self.reserve_zone_cbox.setEnabled(True)
            self.reserve_parcel_cbox.setEnabled(True)

    @pyqtSlot()
    def on_reserve_avg_value_save_button_clicked(self):

        zone_code = None
        parcel_id = None

        current_year = self.reserver_daats_year_sbox.value()
        avg_d3 = float(self.reserve_avg_d3_edit.text())
        avg_sheep_unit = float(self.reserve_avg_sheep_unit_edit.text())
        avg_unelgee = float(self.reserve_avg_unelgee_edit.text())

        level = self.reserve_daats_level_cbox.itemData(self.reserve_daats_level_cbox.currentIndex())

        count = None
        if level == RESERVE_DAATS_LEVEL_1:
            count = self.session.query(PsAvgReserveDaats).filter(PsAvgReserveDaats.reserve_level_type == level) \
                .filter(PsAvgReserveDaats.current_year == current_year).count()
        if level == RESERVE_DAATS_LEVEL_2:
            zone_code = self.reserve_zone_cbox.itemData(self.reserve_zone_cbox.currentIndex())
            count = self.session.query(PsAvgReserveDaats).filter(PsAvgReserveDaats.reserve_level_type == level) \
                .filter(PsAvgReserveDaats.reserve_zone == zone_code) \
                .filter(PsAvgReserveDaats.current_year == current_year).count()
        if level == RESERVE_DAATS_LEVEL_3:
            zone_code = self.reserve_zone_cbox.itemData(self.reserve_zone_cbox.currentIndex())
            parcel_id = self.reserve_parcel_cbox.itemData(self.reserve_parcel_cbox.currentIndex())
            count = self.session.query(PsAvgReserveDaats).filter(PsAvgReserveDaats.reserve_level_type == level) \
                .filter(PsAvgReserveDaats.reserve_parcel == parcel_id) \
                .filter(PsAvgReserveDaats.current_year == current_year).count()

        # if not count:
        #     return

        if count == 0:
            avg_daats = PsAvgReserveDaats()
            avg_daats.current_year = current_year
            avg_daats.avg_sheep_unit = avg_sheep_unit
            avg_daats.avg_d3 = avg_d3
            avg_daats.avg_unelgee = avg_unelgee
            avg_daats.reserve_level_type = level
            avg_daats.reserve_zone = zone_code
            avg_daats.reserve_parcel = parcel_id

            self.session.add(avg_daats)
            PluginUtils.show_message(self, self.tr("success"), self.tr("Successfully"))
        else:
            message_box = QMessageBox()
            message_box.setText(self.tr("Do you want to edit the information for daats ?"))

            update_button = message_box.addButton(self.tr("Update"), QMessageBox.ActionRole)
            message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
            message_box.exec_()

            if message_box.clickedButton() == update_button:
                if level == RESERVE_DAATS_LEVEL_1:
                    avg_daats = self.session.query(PsAvgReserveDaats).filter(PsAvgReserveDaats.reserve_level_type == level) \
                        .filter(PsAvgReserveDaats.current_year == current_year).one()
                    avg_daats.avg_sheep_unit = avg_sheep_unit
                    avg_daats.avg_d3 = avg_d3
                    avg_daats.avg_unelgee = avg_unelgee
                if level == RESERVE_DAATS_LEVEL_2:
                    avg_daats = self.session.query(PsAvgReserveDaats).filter(PsAvgReserveDaats.reserve_level_type == level) \
                        .filter(PsAvgReserveDaats.reserve_zone == zone_code) \
                        .filter(PsAvgReserveDaats.current_year == current_year).one()
                    avg_daats.avg_sheep_unit = avg_sheep_unit
                    avg_daats.avg_d3 = avg_d3
                    avg_daats.avg_unelgee = avg_unelgee
                if level == RESERVE_DAATS_LEVEL_3:
                    avg_daats = self.session.query(PsAvgReserveDaats).filter(PsAvgReserveDaats.reserve_level_type == level) \
                        .filter(PsAvgReserveDaats.reserve_parcel == parcel_id) \
                        .filter(PsAvgReserveDaats.current_year == current_year).one()
                    avg_daats.avg_sheep_unit = avg_sheep_unit
                    avg_daats.avg_d3 = avg_d3
                    avg_daats.avg_unelgee = avg_unelgee

        self.session.commit()

    def __is_number(self, s):

        try:
            float(s)  # for int, long and float
        except ValueError:
            try:
                complex(s)  # for complex
            except ValueError:
                return False

        return True

    @pyqtSlot(str)
    def on_pasture_duration_edit_textChanged(self, text):

        if not self.__is_number(text):
            return

        if not self.__is_number(self.pasture_area_edit.text()):
            return

        if not self.__is_number(self.pasture_biomass_present_edit.text()):
            return

        pasture_area = float(self.pasture_area_edit.text())
        pasture_duration = int(text)
        biomass_present = float(self.pasture_biomass_present_edit.text())
        d3 = self.__calculate_capacity(pasture_area, biomass_present, pasture_duration)
        self.avg_d3_edit.setText(str(d3))

    @pyqtSlot(str)
    def on_avg_sheep_unit_edit_textChanged(self, text):

        if not self.__is_number(text):
            return

        if not self.__is_number(self.avg_d3_edit.text()):
            return

        d3 = int(self.avg_d3_edit.text())

        unelgee = d3-int(text)
        self.avg_unelgee_edit.setText(str(unelgee))

    @pyqtSignature("")
    def on_delete_button_clicked(self):

        selected_items = self.pasture_results_twidget.selectedItems()

        if len(selected_items) != 1:
            self.error_label.setText(self.tr("Only single selection allowed."))
            return None

        selected_item = selected_items[0]
        app_no = selected_item.data(Qt.UserRole)

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to delete the all information for application ?"))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        app_pugs = self.session.query(CtApplicationPUG).\
            filter(CtApplicationPUG.application == app_no).all()

        for app_pug in app_pugs:
            self.session.query(CtApplicationPUG). \
                filter(CtApplicationPUG.group_no == app_pug.group_no).\
                filter(CtApplicationPUG.application == app_no).delete()

        app_pug_parcels = self.session.query(CtApplicationPUGParcel).\
            filter(CtApplicationPUGParcel.application == app_no).all()

        for app_pug_parcel in app_pug_parcels:
            self.session.query(CtApplicationPUGParcel). \
                filter(CtApplicationPUGParcel.parcel == app_pug_parcel.parcel).\
                filter(CtApplicationPUGParcel.application == app_no).delete()

        app_persons = self.session.query(CtApplicationPersonRole).\
            filter(CtApplicationPersonRole.application == app_no).all()

        for app_person in app_persons:
            self.session.query(CtApplicationPersonRole). \
                filter(CtApplicationPersonRole.person == app_person.person). \
                filter(CtApplicationPersonRole.role == 10). \
                filter(CtApplicationPersonRole.application == app_no).delete()

        app_parcels = self.session.query(CtApplicationParcelPasture).\
            filter(CtApplicationParcelPasture.application == app_no).all()

        for app_parcel in app_parcels:
            self.session.query(CtApplicationParcelPasture). \
                filter(CtApplicationParcelPasture.pasture == app_parcel.pasture). \
                filter(CtApplicationParcelPasture.parcel == app_parcel.parcel).\
                filter(CtApplicationParcelPasture.application == app_no).delete()

        app_statuses = self.session.query(CtApplicationStatus).\
            filter(CtApplicationStatus.application == app_no).all()

        for app_status in app_statuses:
            self.session.query(CtApplicationStatus). \
                filter(CtApplicationStatus.status == app_status.status).\
                filter(CtApplicationStatus.application == app_no).delete()

        app_group_boundaries = self.session.query(CtAppGroupBoundary).\
            filter(CtAppGroupBoundary.application == app_no).all()

        for app_group_boundary in app_group_boundaries:
            self.session.query(CtAppGroupBoundary). \
                filter(CtAppGroupBoundary.boundary_code == app_group_boundary.boundary_code). \
                filter(CtAppGroupBoundary.group_no == app_group_boundary.group_no).\
                filter(CtAppGroupBoundary.application == app_no).delete()

        self.session.query(CtApplication).filter(CtApplication.app_no == app_no).delete()

        selected_row = self.pasture_results_twidget.currentRow()
        self.pasture_results_twidget.removeRow(selected_row)

        self.session.commit()
