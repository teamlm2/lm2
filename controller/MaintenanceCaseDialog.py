__author__ = 'anna'

from qgis.core import *
from geoalchemy2.elements import WKTElement
from inspect import currentframe

from ..view.Ui_MaintenanceCaseDialog import *
from ..utils.LayerUtils import LayerUtils
from ..model.CaTmpParcel import *
from ..model.CaMaintenanceCase import *
from ..model.CaBuilding import *
from ..model.CaTmpBuilding import *
from ..controller.ApplicationsDialog import *


class MaintenanceCaseDialog(QDialog, Ui_MaintenanceCaseDialog):

    def __init__(self, plugin, maintenance_soum, maintenance_case, parent=None):

        super(MaintenanceCaseDialog, self).__init__(parent)
        self.maintenance_case = maintenance_case
        self.maintenance_soum = maintenance_soum
        self.plugin = plugin

        self.setupUi(self)
        self.close_button.clicked.connect(self.reject)
        self.session = SessionHandler().session_instance()

        self.__setup_twidgets()
        self.__setup_mapping()
        self.__setup_context_menu()

    def __setup_mapping(self):

        try:

            completion_date = PluginUtils.convert_python_date_to_qt(self.maintenance_case.completion_date)
            if completion_date:
                converted_date = completion_date.toString(completion_date.toString(Constants.DATABASE_DATE_FORMAT))
                self.completion_date_edit.setText(converted_date)

            survey_date = PluginUtils.convert_python_date_to_qt(self.maintenance_case.survey_date)
            if survey_date:
                self.survey_date_edit.setText(survey_date.toString(Constants.DATABASE_DATE_FORMAT))

            creation_date = PluginUtils.convert_python_date_to_qt(self.maintenance_case.creation_date)
            if creation_date:
                self.creation_date_edit.setText(creation_date.toString(Constants.DATABASE_DATE_FORMAT))

            if self.maintenance_case.created_by is not None:
                created_by_role = self.session.query(SetRole)\
                                        .filter(SetRole.user_name_real == self.maintenance_case.created_by).one()
                self.created_by_edit.setText((created_by_role.first_name +" "+ created_by_role.surname))

            if self.maintenance_case.surveyed_by_land_office is not None:
                surveyed_land_office_role = self.session.query(SetRole)\
                                                .filter(SetRole.user_name_real == self.maintenance_case.surveyed_by_land_office)\
                                                .one()
                self.surveyed_by_land_office_edit.setText((surveyed_land_office_role.first_name +" "+
                                                                  surveyed_land_office_role.surname))

            if self.maintenance_case.surveyed_by_surveyor is not None:
                surveyed_by_surveyor_role = self.session.query(SetSurveyor)\
                                                .filter(SetSurveyor.id == self.maintenance_case.surveyed_by_surveyor)\
                                                .one()
                self.surveyed_by_surveyor_edit.setText((surveyed_by_surveyor_role.first_name+" "+
                                                               surveyed_by_surveyor_role.surname))

            if self.maintenance_case.completed_by:
                completed_by_role = self.session.query(SetRole)\
                                                    .filter(SetRole.user_name_real == self.maintenance_case.completed_by).one()
                self.completed_by_edit.setText((completed_by_role.first_name +" "+ completed_by_role.surname))

            if self.maintenance_case.landuse:
                landuse = self.session.query(ClLanduseType.description)\
                                            .filter(ClLanduseType.code == self.maintenance_case.landuse).one()
                self.landuse_edit.setText(landuse[0])

            for application in self.maintenance_case.applications:
                row = self.application_twidget.rowCount()
                self.application_twidget.insertRow(row)
                item = QTableWidgetItem()
                item.setText(application.app_no)
                self.application_twidget.setItem(row, 0, item)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        self.buildings_item = QTreeWidgetItem()
        self.buildings_item.setExpanded(True)
        self.buildings_item.setText(0, self.tr("Buildings"))

        self.parcels_item = QTreeWidgetItem()
        self.parcels_item.setExpanded(True)
        self.parcels_item.setText(0, self.tr("Parcels"))

        self.maintenance_objects_twidget.addTopLevelItem(self.parcels_item)
        self.maintenance_objects_twidget.addTopLevelItem(self.buildings_item)

        for parcel in self.maintenance_case.parcels:
            main_parcel_item = QTreeWidgetItem()
            main_parcel_item.setText(0, parcel.parcel_id)
            main_parcel_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2/parcel_red.png")))
            main_parcel_item.setData(0, Qt.UserRole, parcel.parcel_id)
            main_parcel_item.setData(0, Qt.UserRole + 1, Constants.CASE_PARCEL_IDENTIFIER)
            self.parcels_item.addChild(main_parcel_item)

        for building in self.maintenance_case.buildings:
            building_item = QTreeWidgetItem()
            building_item.setText(0, building.building_id)
            building_item.setData(0, Qt.UserRole, building.building_id)
            building_item.setData(0, Qt.UserRole + 1, Constants.CASE_BUILDING_IDENTIFIER)
            building_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2/building.gif")))
            self.buildings_item.addChild(building_item)

    def __setup_twidgets(self):

        self.maintenance_objects_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.maintenance_objects_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.maintenance_objects_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.maintenance_objects_twidget.setContextMenuPolicy(Qt.CustomContextMenu)


        self.application_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.application_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.application_twidget.horizontalHeader().resizeSection(0, 320)

    def reject(self):

        QDialog.reject(self)

    def __setup_context_menu(self):

        self.menu = QMenu()
        self.zoom_to_selected = QAction(QIcon("zoom.png"), "Zoom to item", self)
        self.menu.addAction(self.zoom_to_selected)
        self.zoom_to_selected.triggered.connect(self.zoom_to_selected_clicked)

    @pyqtSlot()
    def zoom_to_selected_clicked(self):

        selected_item = self.maintenance_objects_twidget.selectedItems()[0]

        if selected_item is None:
            return

        if selected_item.data(0, Qt.UserRole + 1) == Constants.CASE_PARCEL_IDENTIFIER:
            parcel_layer = LayerUtils.layer_by_data_source("s" + self.maintenance_soum, "ca_parcel")
            selection_features = []

            for f in LayerUtils.where(parcel_layer, "parcel_id={0}".format(selected_item.data(0, Qt.UserRole))):
                selection_features.append(f.id())

            parcel_layer.setSelectedFeatures(selection_features)

            self.plugin.iface.mapCanvas().zoomToSelected(parcel_layer)

        elif selected_item.data(0, Qt.UserRole + 1) == Constants.CASE_BUILDING_IDENTIFIER:
            building_layer = LayerUtils.layer_by_data_source("s" + self.maintenance_soum, "ca_building")
            selection_features = []

            for f in LayerUtils.where(building_layer, "building_id={0}".format(selected_item.data(0, Qt.UserRole))):
                selection_features.append(f.id())

            building_layer.setSelectedFeatures(selection_features)

            self.plugin.iface.mapCanvas().zoomToSelected(building_layer)

    @pyqtSlot(QPoint)
    def on_maintenance_objects_twidget_customContextMenuRequested(self, point):

        point = self.maintenance_objects_twidget.viewport().mapToGlobal(point)
        self.menu.exec_(point)

    @pyqtSlot()
    def on_help_button_clicked(self):

        os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/cadastre_maintenance.htm")