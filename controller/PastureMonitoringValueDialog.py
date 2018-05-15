__author__ = 'B.Ankhbold'
# -*- encoding: utf-8 -*-
from PyQt4.QtXml import *
from geoalchemy2.elements import WKTElement
from PyQt4.QtXml import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import *
from qgis.core import *
from qgis.gui import *
from sqlalchemy import exc, or_
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_, extract
from datetime import date, datetime, timedelta
from ..view.Ui_PastureMonitoringValueDialog import *
from ..model.DatabaseHelper import *
from ..model.LM2Exception import LM2Exception
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.SessionHandler import SessionHandler
from ..utils.PluginUtils import PluginUtils
from ..model import Constants
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.AuLevel3 import *
from ..model.AuNaturalZone import *
from ..model.PsApplicationTypePastureType import *
from ..model.EnumerationsPasture import ApplicationType, UserRight
from ..model.PsApplicationTypeDocType import *
from ..model.PsContractDocType import *
from ..model.CaPastureParcel import *
from ..model.CaPastureMonitoring import *
from ..model.CaPUGBoundary import *
from ..model.ClApplicationType import *
from ..utils.PluginUtils import *
from ..model import Constants
from ..model.DatabaseHelper import *
from ..model.ClNaturalZone import *
from ..model.ClliveStock import *
from ..model.ClLandForm import *
from ..model.PsNaturalZoneLandForm import *
from ..model.PsParcel import *
from ..model.PsRecoveryClass import *
from ..model.ClPastureType import *
from ..model.AuReserveZone import *
from ..model.ClPastureValues import *
from ..model.PsPointDetail import *
from ..model.PsPointDetailPoints import *
from ..model.PsPointPastureValue import *
from ..model.PsNaturalZonePlants import *
from ..model.PsPointLiveStockValue import *
from ..model.PsLiveStockConvert import *
from ..model.PsPointUrgatsValue import *
from ..model.PsPastureStatusFormula import *
from ..model.PsNZSheepFood import *
from ..model.PsPointDaatsValue import *
from ..model.PsMissedEvaluation import *
from ..model.PsSoilEvaluation import *
from ..model.PsPastureMissedEvaluation import *
from ..model.PsPastureSoilEvaluation import *
from ..model.PsFormulaTypeLandForm import *
from ..model.PsPastureComparisonFormula import *
from ..model.PsPastureEvaluationFormula import *
from ..model.CtApplicationParcelPasture import *
from ..model.CtContract import *
from ..model.CtContractApplicationRole import *
from ..model.AllPastureParcel import *
from ..model.AllPUGBoundary import *
from inspect import currentframe
from ..utils.FileUtils import FileUtils
from ..utils.LayerUtils import LayerUtils
from ..utils.PasturePath import *
from .qt_classes.DoubleSpinBoxDelegate import *
from .qt_classes.PasturePhotosDelegate import PasturePhotosDelegate
import os
import locale
from collections import defaultdict
import collections
from xlsxwriter.utility import xl_rowcol_to_cell, xl_col_to_name
import xlsxwriter

DOC_PROVIDED_COLUMN = 0
DOC_TYPE_COLUMN = 1
DOC_NAME_COLUMN = 2
DOC_OPEN_COLUMN = 3
DOC_REMOVE_COLUMN = 4
DOC_VIEW_COLUMN = 5


class PastureMonitoringValueDialog(QDialog, Ui_PastureMonitoringValueDialog, DatabaseHelper):
    def __init__(self, plugin, parent=None):

        super(PastureMonitoringValueDialog, self).__init__(parent)
        DatabaseHelper.__init__(self)

        self.setupUi(self)
        self.time_counter = None
        self.setWindowTitle(self.tr("Pasture Monitoring Value"))
        self.close_button.clicked.connect(self.reject)
        self.session = SessionHandler().session_instance()
        self.plugin = plugin
        self.point_detail_id = None
        self.x_point_utm = None
        self.y_point_utm = None
        self.point_year = None
        self.point_detail_id = None
        self.__setup_twidget()
        self.__setup_combo_boxes()
        self.__setup_validators()
        self.__new_detail_id_generate()
        self.d1 = defaultdict(list)
        self.JArray = []

        self.begin_year_sbox.setMinimum(1950)
        self.begin_year_sbox.setMaximum(2200)
        self.begin_year_sbox.setSingleStep(1)
        self.begin_year_sbox.setValue(QDate.currentDate().year())

        self.end_year_sbox.setMinimum(1950)
        self.end_year_sbox.setMaximum(2200)
        self.end_year_sbox.setSingleStep(1)
        self.end_year_sbox.setValue(QDate.currentDate().year() + 5)

        self.print_year_sbox.setMinimum(1950)
        self.print_year_sbox.setMaximum(2200)
        self.print_year_sbox.setSingleStep(1)
        self.print_year_sbox.setValue(QDate.currentDate().year())
        self.point_detail_date.setDate(QDate.currentDate())

        year = self.print_year_sbox.value()
        self.calc_date_edit.setDate(QDate(year, 8, 10))
        # self.calc_date_edit.setDate(QDate.currentDate())

        # self.begin_month_date.setDisplayFormat('%m, %d')
        self.begin_month_date.setDisplayFormat("MM-dd")
        self.end_month_date.setDisplayFormat("MM-dd")

        self.zone_id = None
        self.is_cover_value_load = True

    def __setup_twidget(self):

        self.point_detail_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.point_detail_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.point_detail_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.point_detail_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        self.point_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.point_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.point_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.point_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        self.point_twidget.itemClicked.connect(self.__point_item_clicked)

        self.urgats_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.urgats_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.urgats_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.urgats_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        # self.pasture_values_twidget.cellChanged.connect(self.on_pasture_values_twidget_cellChanged)

    def __setup_photos_twidget(self, point_detail_id):

        self.photos_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.photos_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.photos_twidget.horizontalHeader().resizeSection(0, 70)
        self.photos_twidget.horizontalHeader().resizeSection(1, 100)
        self.photos_twidget.horizontalHeader().resizeSection(2, 120)
        self.photos_twidget.horizontalHeader().resizeSection(3, 50)
        self.photos_twidget.horizontalHeader().resizeSection(4, 50)
        self.photos_twidget.horizontalHeader().resizeSection(5, 50)

        delegate = PasturePhotosDelegate(self.photos_twidget, self)
        self.photos_twidget.setItemDelegate(delegate)

    def __setup_validators(self):

        self.numbers_validator = QRegExpValidator(QRegExp("[0-9]+\\.[0-9]{3}"), None)
        self.int_validator_2 = QRegExpValidator(QRegExp("[0-9]{2}"), None)
        self.int_validator_3 = QRegExpValidator(QRegExp("[0-9]{3}"), None)

        self.x_gradus_edit.setValidator(self.int_validator_3)
        self.x_minute_edit.setValidator(self.int_validator_2)
        self.x_second_edit.setValidator(self.numbers_validator)

        self.y_gradus_edit.setValidator(self.int_validator_3)
        self.y_minute_edit.setValidator(self.int_validator_2)
        self.y_second_edit.setValidator(self.numbers_validator)

        self.area_ga_edit.setValidator(self.numbers_validator)
        self.duration_days_edit.setValidator(self.int_validator_3)

        # @pyqtSlot(int, int)
        # def on_pasture_values_twidget_cellChanged(self, row, column):
        #
        #     if self.is_cover_value_load:
        #         return
        #     print 'change'
        #
        #     row_count = range(self.pasture_values_twidget.rowCount())
        #     cover_value = 0
        #     for row in row_count:
        #         is_cover = False
        #         pasture_item = self.pasture_values_twidget.item(row, 0)
        #         if pasture_item.checkState() == Qt.Checked:
        #             is_cover = True
        #         year_item = self.pasture_values_twidget.item(row, column).data(Qt.UserRole + 1)
        #         value_item = self.pasture_values_twidget.item(row, column)
        #         value = (value_item.text())
        #         if is_cover:
        #             cover_value = cover_value + value
        #
        #     item = QTableWidgetItem(str(cover_value))
        #     item.setData(Qt.UserRole, cover_value)
        #     item.setData(Qt.UserRole+1, year_item)
        #     self.pasture_values_twidget.setItem(0, column, item)


        # if column == APPLICANT_MAIN:
        #     changed_item = self.owners_remaining_twidget.item(row, column)
        #     if changed_item.checkState() == Qt.Checked:
        #
        #         for cu_row in range(self.owners_remaining_twidget.rowCount()):
        #             item = self.owners_remaining_twidget.item(cu_row, column)
        #             if item.checkState() == Qt.Checked and row != cu_row:
        #                 item.setCheckState(Qt.Unchecked)
        #
        # if column == APPLICANT_SHARE:
        #
        #     item = self.applicant_twidget.item(row, APPLICANT_MAIN)
        #     item_share = self.applicant_twidget.item(row, APPLICANT_SHARE)
        #
        #     person_id = item.data(Qt.UserRole)
        #     for applicant in self.application.stakeholders:
        #         if person_id == applicant.person_ref.person_id:
        #             applicant.share = Decimal(item_share.text())

    def __setup_combo_boxes(self):

        try:
            pasture_groups = self.session.query(CaPUGBoundary).all()
            land_forms = self.session.query(ClLandForm).all()
            biomass_types = self.session.query(ClBioMass).all()
        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("Sql Error"), e.message)
            return
        self.pug_boundary_cbox.addItem("*", -1)
        self.parcel_cbox.addItem("*", -1)

        if pasture_groups is not None:
            for pasture_group in pasture_groups:
                self.pug_boundary_cbox.addItem(pasture_group.group_name, pasture_group.code)

        if land_forms:
            for land_form in land_forms:
                self.land_form_cbox.addItem(land_form.description, land_form.code)

        if biomass_types:
            for biomass_type in biomass_types:
                self.biomass_type_cbox.addItem(biomass_type.description, biomass_type.code)

    @pyqtSlot(int)
    def on_otor_find_chbox_stateChanged(self, state):

        self.pug_boundary_cbox.clear()
        self.parcel_cbox.clear()

        try:
            reserve_zones = self.session.query(AuReserveZone).all()
        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("Sql Error"), e.message)
            return

        if state == Qt.Checked:
            self.pug_boundary_cbox.addItem("*", -1)
            self.parcel_cbox.addItem("*", -1)
            if reserve_zones is not None:
                for reserve_zone in reserve_zones:
                    self.pug_boundary_cbox.addItem(reserve_zone.name, reserve_zone.code)
        else:
            self.__setup_combo_boxes()

    @pyqtSlot(int)
    def on_pug_boundary_cbox_currentIndexChanged(self, index):

        self.parcel_cbox.clear()
        if not self.otor_find_chbox.isChecked():
            pug_id = self.pug_boundary_cbox.itemData(self.pug_boundary_cbox.currentIndex(), Qt.UserRole)
            if not pug_id:
                return
            if pug_id != -1:
                pug = self.session.query(CaPUGBoundary).filter(CaPUGBoundary.code == pug_id).one()
                parcels = self.session.query(CaPastureParcel).filter(
                    CaPastureParcel.geometry.ST_Intersects(pug.geometry)).all()
                if parcels is not None:
                    for parcel in parcels:
                        pasture_type = ''
                        if parcel.pasture_type:
                            pasture_type = parcel.pasture_type
                        self.parcel_cbox.addItem(parcel.parcel_id + ' | ' + pasture_type, parcel.parcel_id)
        else:
            otor_zone_id = self.pug_boundary_cbox.itemData(self.pug_boundary_cbox.currentIndex(), Qt.UserRole)
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
                        self.parcel_cbox.addItem(parcel.parcel_id + ' | ' + address_neighbourhood, parcel.parcel_id)

    def __is_number(self, s):

        try:
            float(s)  # for int, long and float
        except ValueError:
            try:
                complex(s)  # for complex
            except ValueError:
                return False

        return True

    @pyqtSlot()
    def on_add_point_button_clicked(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            return

        point_detail_id = self.point_detail_id

        point_detail_point_count = self.session.query(PsPointDetailPoints). \
            filter(PsPointDetailPoints.point_detail_id == point_detail_id).count()
        if point_detail_point_count >= 2:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Point limited!!!"))
            return
        if not self.__is_number(self.x_gradus_edit.text()):
            return
        if not self.__is_number(self.x_minute_edit.text()):
            return
        if not self.__is_number(self.x_second_edit.text()):
            return

        if not self.__is_number(self.y_gradus_edit.text()):
            return
        if not self.__is_number(self.y_minute_edit.text()):
            return
        if not self.__is_number(self.y_second_edit.text()):
            return

        x_gradus = float(self.x_gradus_edit.text())
        x_minute = float(self.x_minute_edit.text())
        x_second = float(self.x_second_edit.text())

        y_gradus = float(self.y_gradus_edit.text())
        y_minute = float(self.y_minute_edit.text())
        y_second = float(self.y_second_edit.text())

        if not x_gradus:
            PluginUtils.show_message(self, self.tr("Coordinate"), self.tr("X coordinate gradus!!!"))
            return
        # if not x_minute:
        #     PluginUtils.show_message(self, self.tr("Coordinate"), self.tr("X coordinate minute!!!"))
        #     return
        # if not x_second:
        #     PluginUtils.show_message(self, self.tr("Coordinate"), self.tr("X coordinate second!!!"))
        #     return

        if not y_gradus:
            PluginUtils.show_message(self, self.tr("Coordinate"), self.tr("Y coordinate gradus!!!"))
            return
        # if not y_minute:
        #     PluginUtils.show_message(self, self.tr("Coordinate"), self.tr("Y coordinate minute!!!"))
        #     return
        # if not y_second:
        #     PluginUtils.show_message(self, self.tr("Coordinate"), self.tr("Y coordinate second!!!"))
        #     return

        x_coordinate = x_gradus + x_minute / 60 + x_second / 3600
        y_coordinate = y_gradus + y_minute / 60 + y_second / 3600
        geom_spot4 = QgsPoint(x_coordinate, y_coordinate)
        geometry = QgsGeometry.fromPoint(geom_spot4)

        geometry = WKTElement(geometry.exportToWkt(), srid=4326)
        is_coordinate = False
        for row in range(self.point_twidget.rowCount()):
            x_item = self.point_twidget.item(row, 1)
            x = x_item.data(Qt.UserRole)

            y_item = self.point_twidget.item(row, 2)
            y = y_item.data(Qt.UserRole)

            if x_coordinate == x and y_coordinate == y:
                is_coordinate = True

        soum_code = DatabaseUtils.working_l2_code()
        soum_point_count = self.session.query(AuLevel2). \
            filter(geometry.ST_Intersects(AuLevel2.geometry)). \
            filter(AuLevel2.code == soum_code).count()
        if soum_point_count == 0:
            PluginUtils.show_message(self, self.tr("Coordinate"),
                                     self.tr("This point without working soum boundary!!!"))
            return

        if is_coordinate:
            PluginUtils.show_message(self, self.tr("Coordinate"),
                                     self.tr("This point already registered coordinate!!!"))
            return

        point_id = self.point_id_edit.text()

        point_count = self.session.query(CaPastureMonitoring).filter(CaPastureMonitoring.point_id == point_id).count()

        if point_count > 0:
            PluginUtils.show_message(self, self.tr("Coordinate"), self.tr("This point id already registered!!!"))
            return

        row = self.point_twidget.rowCount()
        self.point_twidget.insertRow(row)

        item = QTableWidgetItem((point_id))
        item.setData(Qt.UserRole, point_id)
        item.setCheckState(Qt.Checked)

        self.point_twidget.setItem(row, 0, item)

        item = QTableWidgetItem(str(x_coordinate))
        item.setData(Qt.UserRole, x_coordinate)

        self.point_twidget.setItem(row, 1, item)

        item = QTableWidgetItem(str(y_coordinate))
        item.setData(Qt.UserRole, y_coordinate)

        self.point_twidget.setItem(row, 2, item)

        monitoring_point = CaPastureMonitoring()
        monitoring_point.point_id = point_id
        monitoring_point.x_coordinate = x_coordinate
        monitoring_point.y_coordinate = y_coordinate
        monitoring_point.geometry = geometry
        self.session.add(monitoring_point)

        self.plugin.iface.mapCanvas().refresh()

        point_detail_point_count = self.session.query(PsPointDetailPoints). \
            filter(PsPointDetailPoints.point_detail_id == point_detail_id). \
            filter(PsPointDetailPoints.point_id == point_id).count()
        if point_detail_point_count == 0:
            point_detail_point = PsPointDetailPoints()
            point_detail_point.point_detail_id = point_detail_id
            point_detail_point.point_id = point_id

            self.session.add(point_detail_point)

        if self.__load_natural_zone(point_detail_id):
            zone = self.__load_natural_zone(point_detail_id)
            self.zone_id = zone.code
            self.natural_zone_edit.setText(zone.name)

            self.land_form_cbox.clear()
            zone_land_forms = self.session.query(PsNaturalZoneLandForm).filter(
                PsNaturalZoneLandForm.natural_zone == zone.code).all()
            for zone_land_form in zone_land_forms:
                land_form = self.session.query(ClLandForm).filter(ClLandForm.code == zone_land_form.land_form).one()
                self.land_form_cbox.addItem(land_form.description, land_form.code)

    @pyqtSlot(QTableWidgetItem)
    def on_point_twidget_itemClicked(self, item):

        current_row = self.point_twidget.currentRow()
        if current_row == -1:
            return
        point_item = self.point_twidget.item(current_row, 0)
        point_id = point_item.data(Qt.UserRole)

        x_item = self.point_twidget.item(current_row, 1)
        x_coordinate = x_item.data(Qt.UserRole)

        y_item = self.point_twidget.item(current_row, 2)
        y_coordinate = y_item.data(Qt.UserRole)

        feature_ids = []

        layer = LayerUtils.layer_by_data_source("pasture", "ca_pasture_monitoring")

        exp_string = "point_id = \'" + point_id + "\'"

        request = QgsFeatureRequest()
        request.setFilterExpression(exp_string)
        if layer:
            iterator = layer.getFeatures(request)
            for feature in iterator:
                feature_ids.append(feature.id())
                geom = feature.geometry()
                self.__geometry = geom
                self.__setup_coord_transform()
                point = self.__geometry.asPoint()
                x = locale.format('%.2f', round(point.x(), 2), True)
                y = locale.format('%.2f', round(point.y(), 2), True)
                self.x_point_utm = x
                self.y_point_utm = y

            i, d = divmod(float(x_coordinate), 1)
            x_gradus = i
            i, d = divmod(d * 60, 1)
            x_minute = i
            x_second = d * 60

            self.point_id_edit.setText(point_id)
            if self.x_point_utm:
                self.x_utm_edit.setText(self.x_point_utm)
            if self.y_point_utm:
                self.y_utm_edit.setText(self.y_point_utm)

            self.x_gradus_edit.setText(str(int(x_gradus)))
            self.x_minute_edit.setText(str(int(x_minute)))
            self.x_second_edit.setText(str(x_second))

            i, d = divmod(float(y_coordinate), 1)
            y_gradus = i
            i, d = divmod(d * 60, 1)
            y_minute = i
            y_second = d * 60

            self.y_gradus_edit.setText(str(int(y_gradus)))
            self.y_minute_edit.setText(str(int(y_minute)))
            self.y_second_edit.setText(str(y_second))

            self.new_point_button.setEnabled(True)

    @pyqtSlot()
    def on_single_point_zoom_button_clicked(self):

        current_row = self.point_twidget.currentRow()
        if current_row == -1:
            return
        point_item = self.point_twidget.item(current_row, 0)
        point_id = point_item.data(Qt.UserRole)

        layer = LayerUtils.layer_by_data_source("pasture",
                                                "ca_pasture_monitoring")

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"),
                                     self.tr("Please connect to database!!!"))
            return
        if layer is None:
            layer = LayerUtils.load_layer_by_name("ca_pasture_monitoring", "point_id", restrictions)

        feature_ids = []

        layer = LayerUtils.layer_by_data_source("pasture", "ca_pasture_monitoring")

        exp_string = "point_id = \'" + point_id + "\'"

        request = QgsFeatureRequest()
        request.setFilterExpression(exp_string)
        if layer:
            iterator = layer.getFeatures(request)
            for feature in iterator:
                feature_ids.append(feature.id())
                geom = feature.geometry()
                self.__geometry = geom
                self.__setup_coord_transform()
                point = self.__geometry.asPoint()
                x = locale.format('%.2f', round(point.x(), 2), True)
                y = locale.format('%.2f', round(point.y(), 2), True)
                self.x_point_utm = x
                self.y_point_utm = y

                if len(feature_ids) == 0:
                    PluginUtils.show_message(self, self.tr("Connection Error"),
                                             self.tr("No point assigned!!!"))

                scale = self.single_point_scale_sbox.value()

                # scale = self.point_scale_sbox.value()
                rect = QgsRectangle(
                    float(x) - scale,
                    float(y) - scale,
                    float(x) + scale,
                    float(y) + scale)

                mc = self.plugin.iface.mapCanvas()
                # Set the extent to our new rectangle
                mc.setExtent(rect)
                # Refresh the map
                mc.refresh()

            layer.setSelectedFeatures(feature_ids)
            map_canvas = self.plugin.iface.mapCanvas()
            map_canvas.zoomToSelected(layer)

    @pyqtSlot()
    def on_point_zoom_button_clicked(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            return

        point_detail_id = self.point_detail_id

        layer = LayerUtils.layer_by_data_source("pasture",
                                                "ca_pasture_monitoring")

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"),
                                     self.tr("Please connect to database!!!"))
            return
        if layer is None:
            layer = LayerUtils.load_layer_by_name("ca_pasture_monitoring", "point_id", restrictions)

        feature_ids = []

        point_detail_points = self.session.query(PsPointDetailPoints) \
            .filter(PsPointDetailPoints.point_detail_id == point_detail_id).all()

        for point_detail_point in point_detail_points:
            point_id = point_detail_point.point_id

            layer = LayerUtils.layer_by_data_source("pasture", "ca_pasture_monitoring")

            exp_string = "point_id = \'" + point_id + "\'"

            request = QgsFeatureRequest()
            request.setFilterExpression(exp_string)
            if layer:
                iterator = layer.getFeatures(request)
                for feature in iterator:
                    feature_ids.append(feature.id())
                    geom = feature.geometry()
                    self.__geometry = geom
                    self.__setup_coord_transform()
                    point = self.__geometry.asPoint()
                    x = locale.format('%.2f', round(point.x(), 2), True)
                    y = locale.format('%.2f', round(point.y(), 2), True)
                    self.x_point_utm = x
                    self.y_point_utm = y

                    if len(feature_ids) == 0:
                        PluginUtils.show_message(self, self.tr("Connection Error"),
                                                 self.tr("No point assigned!!!"))

                    scale = self.point_scale_sbox.value()

                    # scale = self.point_scale_sbox.value()
                    rect = QgsRectangle(
                        float(x) - scale,
                        float(y) - scale,
                        float(x) + scale,
                        float(y) + scale)

                    mc = self.plugin.iface.mapCanvas()
                    # Set the extent to our new rectangle
                    mc.setExtent(rect)
                    # Refresh the map
                    mc.refresh()

                layer.setSelectedFeatures(feature_ids)
                map_canvas = self.plugin.iface.mapCanvas()
                map_canvas.zoomToSelected(layer)

    def __setup_coord_transform(self):

        line_layer = LayerUtils.layer_by_name('ca_pasture_monitoring')
        if line_layer is None:
            return

        source_crs = line_layer.crs()
        proj4 = PluginUtils.utm_proj4def_from_point(self.__geometry.centroid().asPoint())
        destination_crs = QgsCoordinateReferenceSystem()
        destination_crs.createFromProj4(proj4)
        self.__coord_transform = QgsCoordinateTransform(source_crs, destination_crs)
        self.__geometry.transform(self.__coord_transform)

    @pyqtSlot()
    def on_value_load_button_clicked(self):

        self.point_detail_twidget.clearContents()
        self.point_detail_twidget.setRowCount(0)

        self.point_twidget.clearContents()
        self.point_twidget.setRowCount(0)

        if self.otor_find_chbox.isChecked():
            self.__load_point_detail_otor_search()
        else:
            self.__load_point_detail_search()

    def __load_point_detail_otor_search(self):

        try:
            point_details = self.session.query(PsPointDetail) \
                .join(PsPointDetailPoints, PsPointDetail.point_detail_id == PsPointDetailPoints.point_detail_id) \
                .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
                .filter(CaPastureMonitoring.geometry.ST_Intersects(AuReserveZone.geometry))
            if self.pug_boundary_cbox.currentIndex() != -1:
                if not self.pug_boundary_cbox.itemData(self.pug_boundary_cbox.currentIndex()) == -1:
                    otor_zone_id = self.pug_boundary_cbox.itemData(self.pug_boundary_cbox.currentIndex(), Qt.UserRole)
                    otor_zone = self.session.query(AuReserveZone).filter(AuReserveZone.code == otor_zone_id).one()
                    point_details = self.session.query(PsPointDetail) \
                        .join(PsPointDetailPoints, PsPointDetail.point_detail_id == PsPointDetailPoints.point_detail_id) \
                        .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
                        .filter(CaPastureMonitoring.geometry.ST_Intersects(otor_zone.geometry))

            if self.parcel_cbox.currentIndex() != -1:
                if not self.parcel_cbox.itemData(self.parcel_cbox.currentIndex()) == -1:
                    parcel_id = self.parcel_cbox.itemData(self.parcel_cbox.currentIndex(), Qt.UserRole)
                    parcel = self.session.query(PsParcel).filter(
                        PsParcel.parcel_id == parcel_id).one()

                    point_details = self.session.query(PsPointDetail) \
                        .join(PsPointDetailPoints, PsPointDetail.point_detail_id == PsPointDetailPoints.point_detail_id) \
                        .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
                        .filter(CaPastureMonitoring.geometry.ST_Intersects(parcel.geometry))

            count = 0
            for point_detail in point_details:
                self.point_detail_twidget.insertRow(count)

                item = QTableWidgetItem(point_detail.point_detail_id)
                item.setData(Qt.UserRole, point_detail.point_detail_id)

                self.point_detail_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(str(point_detail.register_date))
                item.setData(Qt.UserRole, point_detail.register_date)

                self.point_detail_twidget.setItem(count, 1, item)

                item = QTableWidgetItem(unicode(point_detail.land_name))
                item.setData(Qt.UserRole, point_detail.land_name)

                self.point_detail_twidget.setItem(count, 2, item)

                land_form = self.session.query(ClLandForm).filter(ClLandForm.code == point_detail.land_form).one()

                item = QTableWidgetItem(unicode(land_form.description))
                item.setData(Qt.UserRole, land_form.code)

                self.point_detail_twidget.setItem(count, 3, item)

                item = QTableWidgetItem(str(point_detail.elevation))
                item.setData(Qt.UserRole, point_detail.elevation)

                self.point_detail_twidget.setItem(count, 4, item)

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    def __load_point_detail_search(self):

        soum_code = DatabaseUtils.working_l2_code()
        value = soum_code + '%'
        try:
            point_details = self.session.query(PsPointDetail). \
                filter(PsPointDetail.point_detail_id.ilike(value))
            if self.pug_boundary_cbox.currentIndex() != -1:
                if not self.pug_boundary_cbox.itemData(self.pug_boundary_cbox.currentIndex()) == -1:
                    pug_id = self.pug_boundary_cbox.itemData(self.pug_boundary_cbox.currentIndex(), Qt.UserRole)
                    pug = self.session.query(CaPUGBoundary).filter(CaPUGBoundary.code == pug_id).one()

                    point_details = self.session.query(PsPointDetail) \
                        .join(PsPointDetailPoints, PsPointDetail.point_detail_id == PsPointDetailPoints.point_detail_id) \
                        .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
                        .filter(CaPastureMonitoring.geometry.ST_Intersects(pug.geometry))
            if self.parcel_cbox.currentIndex() != -1:
                if not self.parcel_cbox.itemData(self.parcel_cbox.currentIndex()) == -1:
                    parcel_id = self.parcel_cbox.itemData(self.parcel_cbox.currentIndex(), Qt.UserRole)
                    parcel = self.session.query(CaPastureParcel).filter(
                        CaPastureParcel.parcel_id == parcel_id).one()

                    point_details = self.session.query(PsPointDetail) \
                        .join(PsPointDetailPoints, PsPointDetail.point_detail_id == PsPointDetailPoints.point_detail_id) \
                        .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
                        .filter(CaPastureMonitoring.geometry.ST_Intersects(parcel.geometry))

            count = 0
            for point_detail in point_details:
                self.point_detail_twidget.insertRow(count)

                item = QTableWidgetItem(point_detail.point_detail_id)
                item.setData(Qt.UserRole, point_detail.point_detail_id)

                self.point_detail_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(str(point_detail.register_date))
                item.setData(Qt.UserRole, point_detail.register_date)

                self.point_detail_twidget.setItem(count, 1, item)

                item = QTableWidgetItem(unicode(point_detail.land_name))
                item.setData(Qt.UserRole, point_detail.land_name)

                self.point_detail_twidget.setItem(count, 2, item)

                land_form = self.session.query(ClLandForm).filter(ClLandForm.code == point_detail.land_form).one()

                item = QTableWidgetItem(unicode(land_form.description))
                item.setData(Qt.UserRole, land_form.code)

                self.point_detail_twidget.setItem(count, 3, item)

                item = QTableWidgetItem(str(point_detail.elevation))
                item.setData(Qt.UserRole, point_detail.elevation)

                self.point_detail_twidget.setItem(count, 4, item)

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    def __load_reserve_all_points(self):

        self.point_twidget.clearContents()
        self.point_twidget.setRowCount(0)
        soum_code = DatabaseUtils.working_l2_code()
        # try:
        subquery = self.session.query(PsPointDetailPoints.point_id)
        monitoring_points = self.session.query(CaPastureMonitoring). \
            join(AuReserveZone, CaPastureMonitoring.geometry.ST_Within(AuReserveZone.geometry)). \
            filter(CaPastureMonitoring.point_id.notin_(subquery)).all()

        for monitoring_point in monitoring_points:
            count = self.point_twidget.rowCount()
            self.point_twidget.insertRow(count)

            restrictions = DatabaseUtils.working_l2_code()
            if not restrictions:
                PluginUtils.show_message(self, self.tr("Connection Error"),
                                         self.tr("Please connect to database!!!"))
                return

            layer = LayerUtils.layer_by_data_source("pasture", "ca_pasture_monitoring")

            exp_string = "point_id = \'" + monitoring_point.point_id + "\'"

            request = QgsFeatureRequest()
            request.setFilterExpression(exp_string)
            if layer:
                iterator = layer.getFeatures(request)
                x = None
                y = None
                for feature in iterator:
                    geom = (feature.geometry())
                    self.__geometry = geom
                    point = geom.asPoint()
                    x = point.x()
                    y = point.y()

                item = QTableWidgetItem((monitoring_point.point_id))
                item.setData(Qt.UserRole, (monitoring_point.point_id))
                item.setCheckState(Qt.Unchecked)
                self.point_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(str(x))
                item.setData(Qt.UserRole, x)
                self.point_twidget.setItem(count, 1, item)

                item = QTableWidgetItem(str(y))
                item.setData(Qt.UserRole, y)
                self.point_twidget.setItem(count, 2, item)

                # except SQLAlchemyError, e:
                #     PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
                #     return

    def __load_all_points(self):

        self.point_twidget.clearContents()
        self.point_twidget.setRowCount(0)
        soum_code = DatabaseUtils.working_l2_code()
        # try:
        subquery = self.session.query(PsPointDetailPoints.point_id)
        monitoring_points = self.session.query(CaPastureMonitoring). \
            join(AuLevel2, CaPastureMonitoring.geometry.ST_Within(AuLevel2.geometry)). \
            filter(CaPastureMonitoring.point_id.notin_(subquery)). \
            filter(AuLevel2.code == soum_code).all()
        if self.pug_boundary_cbox.currentIndex() != -1:
            pug_id = self.pug_boundary_cbox.itemData(self.pug_boundary_cbox.currentIndex(), Qt.UserRole)
            if pug_id != -1:
                pug_count = self.session.query(CaPUGBoundary).filter(CaPUGBoundary.code == pug_id).count()
                if pug_count == 1:
                    pug = self.session.query(CaPUGBoundary).filter(CaPUGBoundary.code == pug_id).one()
                monitoring_points = self.session.query(CaPastureMonitoring). \
                    join(AuLevel2, CaPastureMonitoring.geometry.ST_Within(AuLevel2.geometry)). \
                    join(CaPUGBoundary, CaPastureMonitoring.geometry.ST_Within(CaPUGBoundary.geometry)). \
                    filter(CaPastureMonitoring.point_id.notin_(subquery)). \
                    filter(CaPUGBoundary.code == pug_id). \
                    filter(AuLevel2.code == soum_code).all()

        for monitoring_point in monitoring_points:
            count = self.point_twidget.rowCount()
            self.point_twidget.insertRow(count)

            restrictions = DatabaseUtils.working_l2_code()
            if not restrictions:
                PluginUtils.show_message(self, self.tr("Connection Error"),
                                         self.tr("Please connect to database!!!"))
                return

            layer = LayerUtils.layer_by_data_source("pasture", "ca_pasture_monitoring")

            exp_string = "point_id = \'" + monitoring_point.point_id + "\'"

            request = QgsFeatureRequest()
            request.setFilterExpression(exp_string)
            if layer:
                iterator = layer.getFeatures(request)
                x = None
                y = None
                for feature in iterator:
                    geom = (feature.geometry())
                    self.__geometry = geom
                    point = geom.asPoint()
                    x = point.x()
                    y = point.y()

                item = QTableWidgetItem((monitoring_point.point_id))
                item.setData(Qt.UserRole, (monitoring_point.point_id))
                item.setCheckState(Qt.Unchecked)
                self.point_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(str(x))
                item.setData(Qt.UserRole, x)
                self.point_twidget.setItem(count, 1, item)

                item = QTableWidgetItem(str(y))
                item.setData(Qt.UserRole, y)
                self.point_twidget.setItem(count, 2, item)

                # except SQLAlchemyError, e:
                #     PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
                #     return

    @pyqtSlot()
    def on_new_detail_button_clicked(self):

        self.__new_detail_id_generate()

    def __new_detail_id_generate(self):

        soum_code = DatabaseUtils.working_l2_code()
        value = soum_code + "%"

        point_detail_count = self.session.query(PsPointDetail). \
            filter(PsPointDetail.point_detail_id.ilike(value)).count()
        point_detail_id = None

        if point_detail_count == 0:
            point_detail_id = soum_code + '001'
        else:

            cu_max_number = self.session.query(PsPointDetail.point_detail_id) \
                .filter(PsPointDetail.point_detail_id.ilike(value)) \
                .order_by(PsPointDetail.point_detail_id.desc()).first()
            cu_max_number = cu_max_number[0]

            if len(cu_max_number) == 8:
                point_end_id = cu_max_number[-3:]
                point_end_id = int(point_end_id) + 1
            else:
                point_end_id = '001'

            point_detail_id = soum_code + str(point_end_id).zfill(3)

        self.point_detail_id_edit.setText(point_detail_id)
        self.add_detail_button.setEnabled(True)

    @pyqtSlot()
    def on_add_detail_button_clicked(self):

        if not self.land_name_text_edit.toPlainText():
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Group name null."))
            return

        row = self.point_detail_twidget.rowCount()
        self.point_detail_twidget.insertRow(row)

        point_detail_id = self.point_detail_id_edit.text()
        point_detail_date = self.point_detail_date.date()
        point_detail_date_text = self.point_detail_date.text()
        point_detail_date_qt = PluginUtils.convert_qt_date_to_python(point_detail_date)
        point_land_name = self.land_name_text_edit.toPlainText()
        elevation = self.elevation_sbox.value()

        land_form_code = self.land_form_cbox.itemData(self.land_form_cbox.currentIndex(), Qt.UserRole)
        land_form = self.session.query(ClLandForm).filter(ClLandForm.code == land_form_code).one()

        item = QTableWidgetItem((point_detail_id))
        item.setData(Qt.UserRole, point_detail_id)

        self.point_detail_twidget.setItem(row, 0, item)

        item = QTableWidgetItem(str(point_detail_date_text))
        item.setData(Qt.UserRole, point_detail_date)

        self.point_detail_twidget.setItem(row, 1, item)

        item = QTableWidgetItem(unicode(point_land_name))
        item.setData(Qt.UserRole, point_land_name)

        self.point_detail_twidget.setItem(row, 2, item)

        item = QTableWidgetItem(unicode(land_form.description))
        item.setData(Qt.UserRole, land_form.code)

        self.point_detail_twidget.setItem(row, 3, item)

        item = QTableWidgetItem(str(elevation))
        item.setData(Qt.UserRole, elevation)

        self.point_detail_twidget.setItem(row, 4, item)

        ps_point_detail = PsPointDetail()
        ps_point_detail.point_detail_id = point_detail_id
        ps_point_detail.register_date = point_detail_date_qt
        ps_point_detail.land_form = land_form_code
        ps_point_detail.land_name = point_land_name
        ps_point_detail.elevation = elevation

        self.session.add(ps_point_detail)

    def __pasture_evaluation(self):

        missed_evaluations = self.session.query(PsMissedEvaluation).all()
        soil_evaluations = self.session.query(PsSoilEvaluation).all()

        self.missed_evaluation_cbox.clear()
        self.soil_evaluation_cbox.clear()

        if missed_evaluations:
            for missed_evaluation in missed_evaluations:
                self.missed_evaluation_cbox.addItem(str(missed_evaluation.ball) + ':' + missed_evaluation.description,
                                                    missed_evaluation.code)

        if soil_evaluations:
            for soil_evaluation in soil_evaluations:
                self.soil_evaluation_cbox.addItem(str(soil_evaluation.ball) + ':' + soil_evaluation.description,
                                                  soil_evaluation.code)

    def __set_twidgets_row(self):

        self.photos_twidget.setRowCount(0)
        self.pasture_values_twidget.setRowCount(0)
        self.live_stock_twidget.setRowCount(0)
        self.sheep_unit_twidget.setRowCount(0)
        self.urgats_twidget.setRowCount(0)

    def __clear_calc(self):

        self.calc_rc_edit.clear()
        self.calc_rc_precent_sbox.clear()
        self.calc_biomass_sbox.clear()
        self.biomass_present_edit.clear()
        self.calc_area_sbox.clear()
        self.calc_duration_sbox.clear()
        self.calc_sheep_unit_plant_sbox.clear()
        self.calc_sheep_unit_sbox.clear()

        self.calc_d1_edit.clear()
        self.calc_d1_100ga_edit.clear()
        self.calc_d2_edit.clear()
        self.calc_d3_edit.clear()
        self.calc_unelgee_edit.clear()

    @pyqtSlot(QTableWidgetItem)
    def on_point_detail_twidget_itemClicked(self, item):

        self.all_point_chbox.setChecked(False)

        self.add_detail_button.setEnabled(False)
        current_row = self.point_detail_twidget.currentRow()

        item = self.point_detail_twidget.item(current_row, 0)
        point_detail_id = item.data(Qt.UserRole)

        self.point_detail_id = point_detail_id
        self.point_detail_id_edit.setText(point_detail_id)

        self.__clear_calc();
        year = self.session.query(PsPointDaatsValue).filter(PsPointDaatsValue.point_detail_id == self.point_detail_id)

        if self.__load_natural_zone(point_detail_id):
            zone = self.__load_natural_zone(point_detail_id)
            self.zone_id = zone.code
            self.natural_zone_edit.setText(zone.name)

            self.land_form_cbox.clear()
            zone_land_forms = self.session.query(PsNaturalZoneLandForm).filter(
                PsNaturalZoneLandForm.natural_zone == zone.code).all()
            for zone_land_form in zone_land_forms:
                land_form = self.session.query(ClLandForm).filter(ClLandForm.code == zone_land_form.land_form).one()
                self.land_form_cbox.addItem(land_form.description, land_form.code)

        item = self.point_detail_twidget.item(current_row, 1)
        point_detail_date = item.data(Qt.UserRole)

        self.point_detail_date.setDate(point_detail_date)
        # self.calc_date_edit.setDate(point_detail_date)
        item = self.point_detail_twidget.item(current_row, 2)
        point_land_name = item.data(Qt.UserRole)

        self.land_name_text_edit.setText(point_land_name)

        item = self.point_detail_twidget.item(current_row, 3)
        land_form_code = item.data(Qt.UserRole)
        point_detail = self.session.query(PsPointDetail).filter(PsPointDetail.point_detail_id == point_detail_id).one()

        self.land_form_cbox.setCurrentIndex(self.land_form_cbox.findData(point_detail.land_form))

        item = self.point_detail_twidget.item(current_row, 4)
        point_detail_elevation = item.data(Qt.UserRole)

        self.elevation_sbox.setValue(point_detail_elevation)

        self.add_point_button.setEnabled(True)
        self.new_point_button.setEnabled(True)

        self.__new_point_id_generate()
        self.__load_detail_points()

        self.parcel_id_edit.setText(str(0))
        self.duration_days_edit.setText(str(0))

        if self.__load_pug(point_detail_id):
            pug_boundary = self.__load_pug(point_detail_id)
            self.pug_boundary_cbox.setCurrentIndex(self.pug_boundary_cbox.findData(pug_boundary.code))

        if self.__load_parcel(point_detail_id):
            parcel = self.__load_parcel(point_detail_id)
            self.parcel_id_edit.setText(parcel.parcel_id)
            self.area_ga_edit.setText(str(parcel.area_ga))
            self.calc_area_sbox.setValue(parcel.area_ga)

            self.parcel_cbox.setCurrentIndex(self.parcel_cbox.findData(parcel.parcel_id))
            if parcel.address_neighbourhood:
                self.parcel_neighbourhood_edit.setText(parcel.address_neighbourhood)

            app_parcel_count = self.session.query(CtApplicationParcelPasture). \
                filter(CtApplicationParcelPasture.parcel == parcel.parcel_id).count()
            if app_parcel_count > 0:
                parcel_app = self.session.query(CtApplicationParcelPasture). \
                    filter(CtApplicationParcelPasture.parcel == parcel.parcel_id).first()
                days_sum = 0
                # for parcel_app in parcel_apps:
                #     app_parcels = self.session.query(CtApplicationParcelPasture). \
                #         filter(CtApplicationParcelPasture.application == parcel_app.application). \
                #         filter(CtApplicationParcelPasture.parcel == parcel.parcel_id).all()
                #     for app_parcel in app_parcels:
                #         if app_parcel.days:
                #             days_sum = days_sum + app_parcel.days

                app_parcels = self.session.query(CtApplicationParcelPasture). \
                    filter(CtApplicationParcelPasture.application == parcel_app.application). \
                    filter(CtApplicationParcelPasture.parcel == parcel.parcel_id).all()
                for app_parcel in app_parcels:
                    if app_parcel.days:
                        days_sum = days_sum + app_parcel.days
                self.duration_days_edit.setText(str(days_sum))
                self.calc_duration_sbox.setValue(days_sum)

                self.duration_days_edit.setEnabled(False)
            else:
                self.duration_days_edit.setEnabled(True)
        else:
            self.area_ga_edit.setEnabled(True)
            self.duration_days_edit.setEnabled(True)

        self.__pasture_evaluation()
        self.__set_twidgets_row()

        self.__load_pasture_evaluations()

    @pyqtSlot(int)
    def on_print_year_sbox_valueChanged(self, sbox_value):

        year = sbox_value
        self.calc_date_edit.setDate(QDate(year, 8, 10))

    def __load_pasture_evaluations(self):

        current_year = self.print_year_sbox.value()
        point_datail_id = self.point_detail_id
        pasture_soil_evaluation_count = self.session.query(PsPastureSoilEvaluation). \
            filter(PsPastureSoilEvaluation.current_year == current_year). \
            filter(PsPastureSoilEvaluation.point_detail_id == point_datail_id).count()

        if pasture_soil_evaluation_count == 1:
            pasture_soil_evaluation = self.session.query(PsPastureSoilEvaluation). \
                filter(PsPastureSoilEvaluation.current_year == current_year). \
                filter(PsPastureSoilEvaluation.point_detail_id == point_datail_id).one()
            self.soil_evaluation_cbox.setCurrentIndex(
                self.soil_evaluation_cbox.findData(pasture_soil_evaluation.soil_evaluation))

        pasture_missed_evaluation_count = self.session.query(PsPastureMissedEvaluation). \
            filter(PsPastureMissedEvaluation.current_year == current_year). \
            filter(PsPastureMissedEvaluation.point_detail_id == point_datail_id).count()

        if pasture_missed_evaluation_count == 1:
            pasture_missed_evaluation = self.session.query(PsPastureMissedEvaluation). \
                filter(PsPastureMissedEvaluation.current_year == current_year). \
                filter(PsPastureMissedEvaluation.point_detail_id == point_datail_id).one()
            self.missed_evaluation_cbox.setCurrentIndex(
                self.missed_evaluation_cbox.findData(pasture_missed_evaluation.missed_evaluation))

    def __load_natural_zone(self, point_detail_id):

        point_id = None
        points = self.session.query(PsPointDetailPoints).filter(
            PsPointDetailPoints.point_detail_id == point_detail_id).all()
        for point in points:
            point_id = point.point_id
        point_count = self.session.query(CaPastureMonitoring).filter(CaPastureMonitoring.point_id == point_id).count()
        if point_count == 1:
            point = self.session.query(CaPastureMonitoring).filter(CaPastureMonitoring.point_id == point_id).one()
            zone = self.session.query(AuNaturalZone).filter(point.geometry.ST_Within(AuNaturalZone.geometry)).one()
            return zone

    def __load_detail_points(self):

        self.point_twidget.clearContents()
        self.point_twidget.setRowCount(0)

        point_detail_id = self.point_detail_id

        point_detail_points = self.session.query(PsPointDetailPoints) \
            .filter(PsPointDetailPoints.point_detail_id == point_detail_id).all()

        for point_detail_point in point_detail_points:
            count = self.point_twidget.rowCount()
            self.point_twidget.insertRow(count)

            point_id = point_detail_point.point_id

            restrictions = DatabaseUtils.working_l2_code()
            if not restrictions:
                PluginUtils.show_message(self, self.tr("Connection Error"),
                                         self.tr("Please connect to database!!!"))
                return
            layer = LayerUtils.layer_by_data_source("pasture", "ca_pasture_monitoring")

            exp_string = "point_id = \'" + point_id + "\'"

            request = QgsFeatureRequest()
            request.setFilterExpression(exp_string)
            if layer:
                iterator = layer.getFeatures(request)
                x = 0
                y = 0
                for feature in iterator:
                    geom = (feature.geometry())
                    self.__geometry = geom
                    point = geom.asPoint()
                    x = point.x()
                    y = point.y()

                item = QTableWidgetItem((point_id))
                item.setData(Qt.UserRole, (point_id))
                item.setCheckState(Qt.Checked)
                self.point_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(str(x))
                item.setData(Qt.UserRole, x)
                self.point_twidget.setItem(count, 1, item)

                item = QTableWidgetItem(str(y))
                item.setData(Qt.UserRole, y)
                self.point_twidget.setItem(count, 2, item)

    def __load_pug(self, point_detail_id):

        pug_boundary = None
        point_id = None
        point_detail_points = self.session.query(PsPointDetailPoints) \
            .filter(PsPointDetailPoints.point_detail_id == point_detail_id).all()

        for point_detail_point in point_detail_points:
            point_id = point_detail_point.point_id

        if not point_id:
            return
        point = self.session.query(CaPastureMonitoring).filter(CaPastureMonitoring.point_id == point_id).one()

        pug_boundaries = self.session.query(CaPUGBoundary).filter(
            point.geometry.ST_Within(CaPUGBoundary.geometry)).all()

        for pug_bound in pug_boundaries:
            pug_boundary = pug_bound

        return pug_boundary

    def __load_parcel(self, point_detail_id):

        parcel = None
        point_id = None
        point_detail_points = self.session.query(PsPointDetailPoints) \
            .filter(PsPointDetailPoints.point_detail_id == point_detail_id).all()

        for point_detail_point in point_detail_points:
            point_id = point_detail_point.point_id

        if not point_id:
            return
        point = self.session.query(CaPastureMonitoring).filter(CaPastureMonitoring.point_id == point_id).one()

        parcel_count = self.session.query(CaPastureParcel).filter(
            point.geometry.ST_Within(CaPastureParcel.geometry)).count()

        if parcel_count == 1:
            parcel = self.session.query(CaPastureParcel).filter(
                point.geometry.ST_Within(CaPastureParcel.geometry)).one()
        else:
            parcel_count = self.session.query(PsParcel).filter(
                point.geometry.ST_Within(PsParcel.geometry)).count()

            if parcel_count == 1:
                parcel = self.session.query(PsParcel).filter(
                    point.geometry.ST_Within(PsParcel.geometry)).one()

        return parcel

    def __new_point_id_generate(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            return

        point_detail_id = self.point_detail_id

        point_detail_id_filter = point_detail_id + "%"

        point_count = self.session.query(PsPointDetailPoints) \
            .filter(PsPointDetailPoints.point_detail_id == point_detail_id).count()
        point_id = None
        if point_count == 0:
            point_id = point_detail_id + '01'
        else:
            cu_max_number = self.session.query(PsPointDetailPoints.point_id) \
                .filter(PsPointDetailPoints.point_detail_id == point_detail_id) \
                .order_by(PsPointDetailPoints.point_id.desc()).first()
            cu_max_number = cu_max_number[0]
            if len(cu_max_number) == 10:
                point_end_id = cu_max_number[-2:]
                point_end_id = int(point_end_id) + 1
            else:
                point_end_id = '01'
            point_id = point_detail_id + str(point_end_id).zfill(2)

        self.point_id_edit.setText(point_id)
        self.add_point_button.setEnabled(True)

    @pyqtSlot()
    def on_apply_button_clicked(self):

        if not self.__save_settings():
            return
        self.commit()
        self.__start_fade_out_timer()

    def __save_settings(self):

        # try:
        self.__save_point_detail_points()
        self.__save_point()
        self.__save_pasture_values()
        self.__save_live_stock()
        self.__daats_value_save()
        self.__pasture_evaluation_save()
        return True

        # except LM2Exception, e:
        #     PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

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

    @pyqtSlot()
    def on_new_point_button_clicked(self):

        self.__new_point_id_generate()
        self.add_point_button.setEnabled(True)

    def __load_reserve_point_detail(self):

        soum_code = DatabaseUtils.working_l2_code()
        value = soum_code + '%'

        point_details = self.session.query(PsPointDetail) \
            .join(PsPointDetailPoints, PsPointDetail.point_detail_id == PsPointDetailPoints.point_detail_id) \
            .join(CaPastureMonitoring, PsPointDetailPoints.point_id == CaPastureMonitoring.point_id) \
            .filter(CaPastureMonitoring.geometry.ST_Intersects(AuReserveZone.geometry))

        count = 0
        for point_detail in point_details:
            self.point_detail_twidget.insertRow(count)

            item = QTableWidgetItem(point_detail.point_detail_id)
            item.setData(Qt.UserRole, point_detail.point_detail_id)

            self.point_detail_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(str(point_detail.register_date))
            item.setData(Qt.UserRole, point_detail.register_date)

            self.point_detail_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(unicode(point_detail.land_name))
            item.setData(Qt.UserRole, point_detail.land_name)

            self.point_detail_twidget.setItem(count, 2, item)

            land_form = self.session.query(ClLandForm).filter(ClLandForm.code == point_detail.land_form).one()

            item = QTableWidgetItem(unicode(land_form.description))
            item.setData(Qt.UserRole, land_form.code)

            self.point_detail_twidget.setItem(count, 3, item)

            item = QTableWidgetItem(str(point_detail.elevation))
            item.setData(Qt.UserRole, point_detail.elevation)

            self.point_detail_twidget.setItem(count, 4, item)

    def __load_point_detail(self):

        soum_code = DatabaseUtils.working_l2_code()
        value = soum_code + '%'

        point_details = self.session.query(PsPointDetail). \
            filter(PsPointDetail.point_detail_id.ilike(value)).order_by(PsPointDetail.point_detail_id.asc())

        count = 0
        for point_detail in point_details:
            self.point_detail_twidget.insertRow(count)

            item = QTableWidgetItem(point_detail.point_detail_id)
            item.setData(Qt.UserRole, point_detail.point_detail_id)

            self.point_detail_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(str(point_detail.register_date))
            item.setData(Qt.UserRole, point_detail.register_date)

            self.point_detail_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(unicode(point_detail.land_name))
            item.setData(Qt.UserRole, point_detail.land_name)

            self.point_detail_twidget.setItem(count, 2, item)

            land_form = self.session.query(ClLandForm).filter(ClLandForm.code == point_detail.land_form).one()

            item = QTableWidgetItem(unicode(land_form.description))
            item.setData(Qt.UserRole, land_form.code)

            self.point_detail_twidget.setItem(count, 3, item)

            item = QTableWidgetItem(str(point_detail.elevation))
            item.setData(Qt.UserRole, point_detail.elevation)

            self.point_detail_twidget.setItem(count, 4, item)

    def __load_all_point_detail(self):

        aimag_code = DatabaseUtils.working_l1_code()
        value = aimag_code + '%'

        point_details = self.session.query(PsPointDetail). \
            filter(PsPointDetail.point_detail_id.ilike(value)).order_by(PsPointDetail.point_detail_id.asc())

        count = 0
        for point_detail in point_details:
            self.point_detail_twidget.insertRow(count)

            item = QTableWidgetItem(point_detail.point_detail_id)
            item.setData(Qt.UserRole, point_detail.point_detail_id)

            self.point_detail_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(str(point_detail.register_date))
            item.setData(Qt.UserRole, point_detail.register_date)

            self.point_detail_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(unicode(point_detail.land_name))
            item.setData(Qt.UserRole, point_detail.land_name)

            self.point_detail_twidget.setItem(count, 2, item)

            land_form_c = self.session.query(ClLandForm).filter(ClLandForm.code == point_detail.land_form).count()
            if land_form_c == 1:
                land_form = self.session.query(ClLandForm).filter(ClLandForm.code == point_detail.land_form).one()

                item = QTableWidgetItem(unicode(land_form.description))
                item.setData(Qt.UserRole, land_form.code)

            self.point_detail_twidget.setItem(count, 3, item)

            item = QTableWidgetItem(str(point_detail.elevation))
            item.setData(Qt.UserRole, point_detail.elevation)

            self.point_detail_twidget.setItem(count, 4, item)

    @pyqtSlot(int)
    def on_all_point_chbox_stateChanged(self, state):

        if state == Qt.Checked:
            if self.otor_find_chbox.isChecked():
                self.__load_reserve_all_points()
            else:
                self.__load_all_points()

    @pyqtSlot(int)
    def on_all_point_details_chbox_stateChanged(self, state):

        self.point_detail_twidget.clearContents()
        self.point_detail_twidget.setRowCount(0)

        if self.otor_find_chbox.isChecked():
            self.__load_reserve_point_detail()
        else:
            if state == Qt.Checked:
                self.__load_all_point_detail()
            else:
                self.__load_point_detail()

    def __point_item_clicked(self, item):

        current_row = self.point_detail_twidget.currentRow()
        if not item:
            return

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            return

        item_detail = self.point_detail_twidget.item(current_row, 0)
        point_detail_id = item_detail.data(Qt.UserRole)

        _list = []
        old_point_id = item.data(Qt.UserRole)

        if item.checkState() == QtCore.Qt.Checked:

            _list.append(item.row())
            # if not old_point_id.startswith(point_detail_id):
            self.__new_point_id_generate()
            point_count = self.session.query(CaPastureMonitoring).filter(
                CaPastureMonitoring.point_id == old_point_id).count()
            if point_count == 1:
                point_id = self.point_id_edit.text()
                point = self.session.query(CaPastureMonitoring).filter(
                    CaPastureMonitoring.point_id == old_point_id).one()
                point_new_count = self.session.query(CaPastureMonitoring). \
                    filter(CaPastureMonitoring.point_id == point_id).count()
                if point_new_count == 0:
                    point.point_id = point_id
                    self.session.flush()
                    self.d1[point_id] = []
                    self.d1[point_id].append(old_point_id)
                    item.setText(point_id)
                    item.setData(Qt.UserRole, point_id)
        else:
            if item.checkState() == Qt.Unchecked:
                for k, v in self.d1.iteritems():
                    point_id = str(v[0])
                    if old_point_id == k and old_point_id != point_id:
                        point_count = self.session.query(CaPastureMonitoring).filter(
                            CaPastureMonitoring.point_id == old_point_id).count()
                        if point_count == 1:
                            point = self.session.query(CaPastureMonitoring).filter(
                                CaPastureMonitoring.point_id == old_point_id).one()
                            point_new_count = self.session.query(CaPastureMonitoring). \
                                filter(CaPastureMonitoring.point_id == point_id).count()
                            if point_new_count == 0:
                                point.point_id = point_id
                                self.session.flush()
                                item.setText(point_id)
                                item.setData(Qt.UserRole, point_id)

    def __save_point_detail_points(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            return

        point_detail_id = self.point_detail_id
        for row in range(self.point_twidget.rowCount()):
            check_item = self.point_twidget.item(row, 0)
            point_id = self.point_twidget.item(row, 0).data(Qt.UserRole)
            if point_id:
                is_count = self.session.query(PsPointDetailPoints) \
                    .filter(PsPointDetailPoints.point_detail_id == point_detail_id) \
                    .filter(PsPointDetailPoints.point_id == point_id).count()
                if check_item.checkState() == Qt.Checked:
                    if is_count == 0:
                        point_detail_points = PsPointDetailPoints()
                        point_detail_points.point_detail_id = point_detail_id
                        point_detail_points.point_id = point_id
                        self.session.add(point_detail_points)
                else:
                    if is_count == 1:
                        self.session.query(PsPointDetailPoints) \
                            .filter(PsPointDetailPoints.point_detail_id == point_detail_id) \
                            .filter(PsPointDetailPoints.point_id == point_id).delete()

    def __pasture_evaluation_save(self):

        # self.session.rollback()
        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            return

        point_detail_id = self.point_detail_id
        current_year = self.print_year_sbox.value()

        point_detail_count = self.session.query(PsPointDetail).filter(
            PsPointDetail.point_detail_id == point_detail_id).count()
        if point_detail_count == 1:

            soil_evaluation_code = self.soil_evaluation_cbox.itemData(self.soil_evaluation_cbox.currentIndex())
            soil_evaluation_c = self.session.query(PsSoilEvaluation).filter(
                PsSoilEvaluation.code == soil_evaluation_code).count()

            if soil_evaluation_c == 1:
                pasture_soil_count = self.session.query(PsPastureSoilEvaluation). \
                    filter(PsPastureSoilEvaluation.current_year == current_year). \
                    filter(PsPastureSoilEvaluation.point_detail_id == point_detail_id).count()
                if pasture_soil_count == 1:
                    pasture_soil = self.session.query(PsPastureSoilEvaluation). \
                        filter(PsPastureSoilEvaluation.current_year == current_year). \
                        filter(PsPastureSoilEvaluation.point_detail_id == point_detail_id).one()
                    pasture_soil.soil_evaluation = soil_evaluation_code
                else:
                    pasture_soil = PsPastureSoilEvaluation()
                    pasture_soil.point_detail_id = point_detail_id
                    pasture_soil.current_year = current_year
                    pasture_soil.soil_evaluation = soil_evaluation_code
                    self.session.add(pasture_soil)

            missed_evaluation_code = self.missed_evaluation_cbox.itemData(self.missed_evaluation_cbox.currentIndex())
            missed_evaluation_c = self.session.query(PsMissedEvaluation).filter(
                PsMissedEvaluation.code == missed_evaluation_code).count()

            if missed_evaluation_c == 1:
                pasture_missed_count = self.session.query(PsPastureMissedEvaluation). \
                    filter(PsPastureMissedEvaluation.current_year == current_year). \
                    filter(PsPastureMissedEvaluation.point_detail_id == point_detail_id).count()
                if pasture_missed_count == 1:
                    pasture_missed = self.session.query(PsPastureMissedEvaluation). \
                        filter(PsPastureMissedEvaluation.current_year == current_year). \
                        filter(PsPastureMissedEvaluation.point_detail_id == point_detail_id).one()
                    pasture_missed.missed_evaluation = missed_evaluation_code
                else:
                    pasture_missed = PsPastureMissedEvaluation()
                    pasture_missed.point_detail_id = point_detail_id
                    pasture_missed.current_year = current_year
                    pasture_missed.missed_evaluation = missed_evaluation_code
                    self.session.add(pasture_missed)

    def __save_point(self):

        for row in range(self.point_twidget.rowCount()):

            point_id = self.point_twidget.item(row, 0).data(Qt.UserRole)
            x = self.point_twidget.item(row, 1).data(Qt.UserRole)
            y = self.point_twidget.item(row, 2).data(Qt.UserRole)
            point_count = self.session.query(CaPastureMonitoring).filter(
                CaPastureMonitoring.point_id == point_id).count()
            if point_count == 1:
                point = self.session.query(CaPastureMonitoring).filter(CaPastureMonitoring.point_id == point_id).one()
                point.x_coordinate = x
                point.y_coordinate = y
                self.session.flush()

    def __load_pasture_values(self):

        self.pasture_values_twidget.setRowCount(0)

        pasture_plants = self.session.query(PsNaturalZonePlants). \
            filter(PsNaturalZonePlants.natural_zone == self.zone_id). \
            order_by(PsNaturalZonePlants.plants).all()
        self.pasture_values_twidget.setColumnCount(self.end_year_sbox.value() - self.begin_year_sbox.value() + 1)
        header_label = 'Value Name;'
        parcel_id = self.parcel_id_edit.text()

        current_row = self.point_detail_twidget.currentRow()
        item_detail = self.point_detail_twidget.item(current_row, 0)
        point_detail_id = item_detail.data(Qt.UserRole)

        for pasture_plant in pasture_plants:
            pasture_value = self.session.query(ClPastureValues).filter(
                ClPastureValues.code == pasture_plant.plants).one()

            item_name = QTableWidgetItem(pasture_value.description)
            item_name.setData(Qt.UserRole, pasture_value.code)
            count = self.pasture_values_twidget.rowCount()
            self.pasture_values_twidget.insertRow(count)

            self.pasture_values_twidget.setItem(count, 0, item_name)
            column = 1
            header = self.begin_year_sbox.value()
            for col in range(self.end_year_sbox.value() - self.begin_year_sbox.value()):
                p_value = 0
                is_cover = False
                value_count = self.session.query(PsPointPastureValue). \
                    filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                    filter(PsPointPastureValue.pasture_value == pasture_value.code). \
                    filter(PsPointPastureValue.value_year == header).count()
                if value_count == 1:
                    value = self.session.query(PsPointPastureValue). \
                        filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                        filter(PsPointPastureValue.pasture_value == pasture_value.code). \
                        filter(PsPointPastureValue.value_year == header).one()
                    p_value = value.current_value
                    if value.is_cover:
                        is_cover = True
                if is_cover:
                    item_name.setCheckState(Qt.Checked)
                else:
                    item_name.setCheckState(Qt.Unchecked)
                item = QTableWidgetItem(str(p_value))
                item.setData(Qt.UserRole, p_value)
                item.setData(Qt.UserRole + 1, header)
                self.pasture_values_twidget.setColumnWidth(column, 75)
                header_label = header_label + '' + str(header) + ';'
                header += 1
                delegate = DoubleSpinBoxDelegate(column, -100000, 1000000.0000, 0.0001, 0.001,
                                                 self.pasture_values_twidget)
                self.pasture_values_twidget.setItemDelegateForColumn(column, delegate)
                self.pasture_values_twidget.setItem(count, column, item)
                column += 1
        self.pasture_values_twidget.setHorizontalHeaderLabels(header_label.split(";"))
        self.pasture_values_twidget.setColumnWidth(0, 220)

    def __load_live_stock_values(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            return

        self.live_stock_twidget.setRowCount(0)

        live_stocks = self.session.query(ClliveStock).all()
        self.live_stock_twidget.setColumnCount(self.end_year_sbox.value() - self.begin_year_sbox.value() + 1)
        header_label = 'Value Name;'

        current_row = self.point_detail_twidget.currentRow()
        item_detail = self.point_detail_twidget.item(current_row, 0)
        point_detail_id = item_detail.data(Qt.UserRole)

        for live_stock in live_stocks:

            count = self.live_stock_twidget.rowCount()
            self.live_stock_twidget.insertRow(count)

            item_name = QTableWidgetItem(live_stock.description)
            item_name.setData(Qt.UserRole, live_stock.code)
            self.live_stock_twidget.setItem(count, 0, item_name)

            column = 1
            header = self.begin_year_sbox.value()
            for col in range(self.end_year_sbox.value() - self.begin_year_sbox.value()):
                p_value = 0
                value_count = self.session.query(PsPointLiveStockValue). \
                    filter(PsPointLiveStockValue.point_detail_id == point_detail_id). \
                    filter(PsPointLiveStockValue.live_stock_type == live_stock.code). \
                    filter(PsPointLiveStockValue.value_year == header).count()
                if value_count == 1:
                    value = self.session.query(PsPointLiveStockValue). \
                        filter(PsPointLiveStockValue.point_detail_id == point_detail_id). \
                        filter(PsPointLiveStockValue.live_stock_type == live_stock.code). \
                        filter(PsPointLiveStockValue.value_year == header).one()
                    p_value = value.current_value

                item = QTableWidgetItem(str(p_value))
                item.setData(Qt.UserRole, p_value)
                item.setData(Qt.UserRole + 1, header)
                self.live_stock_twidget.setColumnWidth(column, 75)
                header_label = header_label + '' + str(header) + ';'
                header += 1
                delegate = DoubleSpinBoxDelegate(column, -100000, 1000000.0000, 0.0001, 0.001,
                                                 self.live_stock_twidget)
                self.live_stock_twidget.setItemDelegateForColumn(column, delegate)
                self.live_stock_twidget.setItem(count, column, item)
                column += 1
        self.live_stock_twidget.setHorizontalHeaderLabels(header_label.split(";"))
        self.live_stock_twidget.setColumnWidth(0, 150)

    def __load_sheep_unit_values(self):

        self.sheep_unit_twidget.setRowCount(0)

        self.sheep_unit_twidget.setColumnCount(self.end_year_sbox.value() - self.begin_year_sbox.value() + 1)
        header_label = 'Value Name;'

        current_row = self.point_detail_twidget.currentRow()
        item_detail = self.point_detail_twidget.item(current_row, 0)
        point_detail_id = item_detail.data(Qt.UserRole)

        count = self.sheep_unit_twidget.rowCount()
        self.sheep_unit_twidget.insertRow(count)

        item_name = QTableWidgetItem(u'Хонин Толгой')
        item_name.setData(Qt.UserRole, 1)
        self.sheep_unit_twidget.setItem(count, 0, item_name)

        live_stocks = self.session.query(ClliveStock).all()

        column = 1
        header = self.begin_year_sbox.value()
        for col in range(self.end_year_sbox.value() - self.begin_year_sbox.value()):
            p_value = 0

            item = QTableWidgetItem(str(p_value))
            item.setData(Qt.UserRole, p_value)
            item.setData(Qt.UserRole + 1, header)
            self.sheep_unit_twidget.setColumnWidth(column, 75)
            header_label = header_label + '' + str(header) + ';'
            header += 1

            self.sheep_unit_twidget.setItem(count, column, item)
            column += 1
        self.sheep_unit_twidget.setHorizontalHeaderLabels(header_label.split(";"))
        self.sheep_unit_twidget.setColumnWidth(0, 150)

    def __load_urgats_values(self, point_detail_id):

        self.urgats_twidget.setRowCount(0)

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            return

        begin_year = self.begin_year_sbox.value()
        end_year = self.end_year_sbox.value()
        biomass_values = self.session.query(PsPointUrgatsValue). \
            filter(PsPointUrgatsValue.point_detail_id == point_detail_id). \
            filter(PsPointUrgatsValue.value_year >= begin_year). \
            filter(PsPointUrgatsValue.value_year <= end_year).all()

        count = 0
        for biomass_value in biomass_values:
            self.urgats_twidget.insertRow(count)

            item = QTableWidgetItem(str(biomass_value.value_year))
            item.setData(Qt.UserRole, biomass_value.value_year)
            self.urgats_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(unicode(biomass_value.biomass_type_ref.description))
            item.setData(Qt.UserRole, biomass_value.biomass_type)
            self.urgats_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(str(biomass_value.biomass_kg_ga))
            item.setData(Qt.UserRole, biomass_value.biomass_kg_ga)
            self.urgats_twidget.setItem(count, 2, item)

            item = QTableWidgetItem(str(biomass_value.m_1))
            item.setData(Qt.UserRole, biomass_value.m_1)
            self.urgats_twidget.setItem(count, 3, item)

            item = QTableWidgetItem(str(biomass_value.m_1_value))
            item.setData(Qt.UserRole, biomass_value.m_1_value)
            self.urgats_twidget.setItem(count, 4, item)

            item = QTableWidgetItem(str(biomass_value.m_2))
            item.setData(Qt.UserRole, biomass_value.m_2)
            self.urgats_twidget.setItem(count, 5, item)

            item = QTableWidgetItem(str(biomass_value.m_2_value))
            item.setData(Qt.UserRole, biomass_value.m_2_value)
            self.urgats_twidget.setItem(count, 6, item)

            item = QTableWidgetItem(str(biomass_value.m_3))
            item.setData(Qt.UserRole, biomass_value.m_3)
            self.urgats_twidget.setItem(count, 7, item)

            item = QTableWidgetItem(str(biomass_value.m_3_value))
            item.setData(Qt.UserRole, biomass_value.m_3_value)
            self.urgats_twidget.setItem(count, 8, item)

    def __refresh_sheep_unit_values(self):

        value_row = self.live_stock_twidget.rowCount()
        if value_row == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please load live stock values!!!"))
            return

        self.sheep_unit_twidget.setRowCount(0)
        self.sheep_unit_twidget.setColumnCount(self.end_year_sbox.value() - self.begin_year_sbox.value() + 1)
        header_label = 'Value Name;'
        column_count = range(self.live_stock_twidget.columnCount())
        row_count = range(self.live_stock_twidget.rowCount())

        count = self.sheep_unit_twidget.rowCount()
        self.sheep_unit_twidget.insertRow(count)

        item_name = QTableWidgetItem(u'Хонин Толгой')
        item_name.setData(Qt.UserRole, 1)
        self.sheep_unit_twidget.setItem(count, 0, item_name)

        for column in column_count:
            if column == 0:
                pass
            all_value = 0
            live_stock_convert_value = 0
            if column + 1 <= (self.live_stock_twidget.columnCount() - 1):
                year_item = self.live_stock_twidget.item(0, column + 1).data(Qt.UserRole + 1)
                for row in row_count:
                    live_stock_item = self.live_stock_twidget.item(row, 0)
                    live_stock_type = live_stock_item.data(Qt.UserRole)

                    value_item = self.live_stock_twidget.item(row, column + 1).text()

                    value = float(value_item)
                    live_stock_convert = self.session.query(PsLiveStockConvert). \
                        filter(PsLiveStockConvert.live_stock_type == live_stock_type).one()
                    sheep_convert_value = live_stock_convert.convert_value
                    live_stock_convert_value = value * float(sheep_convert_value)

                    all_value = all_value + live_stock_convert_value

                item = QTableWidgetItem(str(all_value))
                item.setData(Qt.UserRole, all_value)
                header_label = header_label + '' + str(year_item) + ';'
                self.sheep_unit_twidget.setItem(0, column + 1, item)
        self.sheep_unit_twidget.setHorizontalHeaderLabels(header_label.split(";"))
        self.sheep_unit_twidget.setColumnWidth(0, 150)

    def __refresh_cover_values(self):

        value_row = self.pasture_values_twidget.rowCount()
        if value_row == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please load pasture plants values!!!"))
            return

        column_count = range(self.pasture_values_twidget.columnCount())
        row_count = range(self.pasture_values_twidget.rowCount())

        for column in column_count:
            if column == 0:
                pass
            cover_value = 0
            if column + 1 <= (self.pasture_values_twidget.columnCount() - 1):
                for row in row_count:
                    is_cover = False
                    pasture_item = self.pasture_values_twidget.item(row, 0)
                    if pasture_item.checkState() == Qt.Checked:
                        is_cover = True
                    year_item = self.pasture_values_twidget.item(row, column + 1).data(Qt.UserRole + 1)
                    value_item = self.pasture_values_twidget.item(row, column + 1)
                    value = round(float(value_item.text()), 2)
                    if is_cover:
                        cover_value = cover_value + value

                item = QTableWidgetItem(str(cover_value))
                item.setData(Qt.UserRole, cover_value)
                item.setData(Qt.UserRole + 1, year_item)
                self.pasture_values_twidget.setItem(0, column + 1, item)

    @pyqtSlot()
    def on_cover_calc_button_clicked(self):

        self.__refresh_cover_values()

    @pyqtSlot()
    def on_sheep_unit_button_clicked(self):

        self.__refresh_sheep_unit_values()

    @pyqtSlot()
    def on_plant_value_load_button_clicked(self):

        self.is_cover_value_load = True
        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            return

        current_row = self.point_detail_twidget.currentRow()
        item_detail = self.point_detail_twidget.item(current_row, 0)
        point_detail_id = item_detail.data(Qt.UserRole)

        self.__load_pasture_values()
        self.__load_live_stock_values()
        # self.__load_sheep_unit_values()
        self.__load_urgats_values(point_detail_id)
        self.is_cover_value_load = False

    def __save_pasture_values(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            return

        column_count = range(self.pasture_values_twidget.columnCount())
        row_count = range(self.pasture_values_twidget.rowCount())

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            return

        current_row = self.point_detail_twidget.currentRow()
        item_detail = self.point_detail_twidget.item(current_row, 0)
        point_detail_id = item_detail.data(Qt.UserRole)

        for row in row_count:
            is_cover = False
            pasture_item = self.pasture_values_twidget.item(row, 0)
            pasture_code = pasture_item.data(Qt.UserRole)
            if pasture_item.checkState() == Qt.Checked:
                is_cover = True
            for column in column_count:
                if column + 1 <= (self.pasture_values_twidget.columnCount() - 1):
                    year_item = self.pasture_values_twidget.item(row, column + 1).data(Qt.UserRole + 1)
                    value_item = self.pasture_values_twidget.item(row, column + 1).text()
                    value_count = self.session.query(PsPointPastureValue). \
                        filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                        filter(PsPointPastureValue.pasture_value == pasture_code). \
                        filter(PsPointPastureValue.value_year == year_item).count()
                    if value_count == 1:
                        pasture_value = self.session.query(PsPointPastureValue). \
                            filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                            filter(PsPointPastureValue.pasture_value == pasture_code). \
                            filter(PsPointPastureValue.value_year == year_item).one()

                        pasture_value.current_value = float(value_item)
                        pasture_value.is_cover = is_cover
                    elif value_count == 0:
                        pasture_value = PsPointPastureValue()

                        pasture_value.point_detail_id = point_detail_id
                        pasture_value.current_value = float(value_item)
                        pasture_value.value_year = year_item
                        pasture_value.pasture_value = pasture_code
                        pasture_value.is_cover = is_cover

                        self.session.add(pasture_value)

    def __save_live_stock(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            return

        column_count = range(self.live_stock_twidget.columnCount())
        row_count = range(self.live_stock_twidget.rowCount())

        current_row = self.point_detail_twidget.currentRow()
        item_detail = self.point_detail_twidget.item(current_row, 0)
        point_detail_id = item_detail.data(Qt.UserRole)

        for row in row_count:
            live_stock_item = self.live_stock_twidget.item(row, 0)
            live_stock_type = live_stock_item.data(Qt.UserRole)
            for column in column_count:
                if column + 1 <= (self.live_stock_twidget.columnCount() - 1):
                    year_item = self.live_stock_twidget.item(row, column + 1).data(Qt.UserRole + 1)
                    value_item = self.live_stock_twidget.item(row, column + 1).text()
                    value_count = self.session.query(PsPointLiveStockValue). \
                        filter(PsPointLiveStockValue.point_detail_id == point_detail_id). \
                        filter(PsPointLiveStockValue.live_stock_type == live_stock_type). \
                        filter(PsPointLiveStockValue.value_year == year_item).count()
                    if value_count == 1:
                        live_stock_value = self.session.query(PsPointLiveStockValue). \
                            filter(PsPointLiveStockValue.point_detail_id == point_detail_id). \
                            filter(PsPointLiveStockValue.live_stock_type == live_stock_type). \
                            filter(PsPointLiveStockValue.value_year == year_item).one()

                        live_stock_value.current_value = float(value_item)

                    elif value_count == 0:
                        live_stock_value = PsPointLiveStockValue()

                        live_stock_value.point_detail_id = point_detail_id
                        live_stock_value.current_value = float(value_item)
                        live_stock_value.value_year = year_item
                        live_stock_value.live_stock_type = live_stock_type

                        self.session.add(live_stock_value)

    @pyqtSlot(QTableWidgetItem)
    def on_urgats_twidget_itemClicked(self, item):

        current_row = self.urgats_twidget.currentRow()
        if current_row == -1:
            return

        item = self.urgats_twidget.item(current_row, 0)
        biomass_year = item.data(Qt.UserRole)

        item = self.urgats_twidget.item(current_row, 1)
        biomass_type = item.data(Qt.UserRole)

        item = self.urgats_twidget.item(current_row, 2)
        biomass_kg_ga = item.data(Qt.UserRole)

        item = self.urgats_twidget.item(current_row, 3)
        m_1 = item.data(Qt.UserRole)

        item = self.urgats_twidget.item(current_row, 4)
        m_1_value = item.data(Qt.UserRole)

        item = self.urgats_twidget.item(current_row, 5)
        m_2 = item.data(Qt.UserRole)

        item = self.urgats_twidget.item(current_row, 6)
        m_2_value = item.data(Qt.UserRole)

        item = self.urgats_twidget.item(current_row, 7)
        m_3 = item.data(Qt.UserRole)

        item = self.urgats_twidget.item(current_row, 8)
        m_3_value = item.data(Qt.UserRole)

        self.print_year_sbox.setValue(biomass_year)
        self.biomass_type_cbox.setCurrentIndex(self.biomass_type_cbox.findData(biomass_type))
        self.m_1_sbox.setValue(m_1)
        self.m_1_value_sbox.setValue(m_1_value)
        self.m_2_sbox.setValue(m_2)
        self.m_2_value_sbox.setValue(m_2_value)
        self.m_3_sbox.setValue(m_3)
        self.m_3_value_sbox.setValue(m_3_value)

    @pyqtSlot()
    def on_edit_detail_button_clicked(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            return
        land_form_code = self.land_form_cbox.itemData(self.land_form_cbox.currentIndex())
        land_form_text = self.land_form_cbox.currentText()
        # land_form = self.session.query(ClLandForm).filter(ClLandForm.code == land_form_code).one()

        current_row = self.point_detail_twidget.currentRow()
        id_item = self.point_detail_twidget.item(current_row, 0)

        date_item = self.point_detail_twidget.item(current_row, 1)
        land_name_item = self.point_detail_twidget.item(current_row, 2)
        land_form_item = self.point_detail_twidget.item(current_row, 3)
        elevation_item = self.point_detail_twidget.item(current_row, 4)

        id_item.setData(Qt.UserRole, self.point_detail_id_edit.text())

        date_item.setText(str(self.point_detail_date.text()))
        date_item.setData(Qt.UserRole, self.point_detail_date.date())

        land_name_item.setText(self.land_name_text_edit.toPlainText())
        land_name_item.setData(Qt.UserRole, self.land_name_text_edit.toPlainText())

        land_form_item.setText(unicode(land_form_text))
        land_form_item.setData(Qt.UserRole, land_form_code)

        elevation_item.setText(str(self.elevation_sbox.value()))
        elevation_item.setData(Qt.UserRole, self.elevation_sbox.value())

        point_detail_date_qt = PluginUtils.convert_qt_date_to_python(self.point_detail_date.date())
        point_detail_count = self.session.query(PsPointDetail). \
            filter(PsPointDetail.point_detail_id == self.point_detail_id_edit.text()).count()
        if point_detail_count == 1:
            point_detail = self.session.query(PsPointDetail). \
                filter(PsPointDetail.point_detail_id == self.point_detail_id_edit.text()).one()

            point_detail.register_date = point_detail_date_qt
            point_detail.land_form = land_form_code
            # point_detail.land_from_ref = land_form
            point_detail.land_name = self.land_name_text_edit.toPlainText()
            point_detail.elevation = self.elevation_sbox.value()
        else:
            point_detail = PsPointDetail()
            point_detail.point_detail_id = self.point_detail_id_edit.text()
            point_detail.register_date = point_detail_date_qt
            point_detail.land_form = land_form_code
            # point_detail.land_from_ref = land_form
            point_detail.land_name = self.land_name_text_edit.toPlainText()
            point_detail.elevation = self.elevation_sbox.value()
            self.session.add(point_detail)

    @pyqtSlot()
    def on_edit_point_button_clicked(self):

        selected_items = self.point_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose bio mass!!!"))
            return

        x_gradus = float(self.x_gradus_edit.text())
        x_minute = float(self.x_minute_edit.text())
        x_second = float(self.x_second_edit.text())

        y_gradus = float(self.y_gradus_edit.text())
        y_minute = float(self.y_minute_edit.text())
        y_second = float(self.y_second_edit.text())

        if not x_gradus:
            PluginUtils.show_message(self, self.tr("Coordinate"), self.tr("X coordinate gradus!!!"))
            return
        if not x_minute:
            PluginUtils.show_message(self, self.tr("Coordinate"), self.tr("X coordinate minute!!!"))
            return
        if not x_second:
            PluginUtils.show_message(self, self.tr("Coordinate"), self.tr("X coordinate second!!!"))
            return

        if not y_gradus:
            PluginUtils.show_message(self, self.tr("Coordinate"), self.tr("Y coordinate gradus!!!"))
            return
        if not y_minute:
            PluginUtils.show_message(self, self.tr("Coordinate"), self.tr("Y coordinate minute!!!"))
            return
        if not y_second:
            PluginUtils.show_message(self, self.tr("Coordinate"), self.tr("Y coordinate second!!!"))
            return

        x_coordinate = x_gradus + x_minute / 60 + x_second / 3600
        y_coordinate = y_gradus + y_minute / 60 + y_second / 3600
        geom_spot4 = QgsPoint(x_coordinate, y_coordinate)
        geometry = QgsGeometry.fromPoint(geom_spot4)
        geometry = WKTElement(geometry.exportToWkt(), srid=4326)

        soum_code = DatabaseUtils.working_l2_code()
        soum_point_count = self.session.query(AuLevel2). \
            filter(geometry.ST_Intersects(AuLevel2.geometry)). \
            filter(AuLevel2.code == soum_code).count()
        if soum_point_count == 0:
            PluginUtils.show_message(self, self.tr("Coordinate"),
                                     self.tr("This point without working soum boundary!!!"))
            return

        selected_row = self.point_twidget.currentRow()

        point_id_item = self.point_twidget.item(selected_row, 0)
        x_item = self.point_twidget.item(selected_row, 1)
        y_item = self.point_twidget.item(selected_row, 2)

        point_id_item.setData(Qt.UserRole, self.point_id_edit.text())

        x_item.setText(str(x_coordinate))
        x_item.setData(Qt.UserRole, x_coordinate)

        y_item.setText(str(y_coordinate))
        y_item.setData(Qt.UserRole, y_coordinate)

        point_count = self.session.query(CaPastureMonitoring). \
            filter(CaPastureMonitoring.point_id == self.point_id_edit.text()).count()
        if point_count == 1:
            point = self.session.query(CaPastureMonitoring). \
                filter(CaPastureMonitoring.point_id == self.point_id_edit.text()).one()
            point.x_coordinate = x_coordinate
            point.y_coordinate = y_coordinate
            point.geometry = geometry
        else:
            point = CaPastureMonitoring()
            point.point_id = self.point_id_edit.text()
            point.x_coordinate = x_coordinate
            point.y_coordinate = y_coordinate
            point.geometry = geometry
            self.session.add(point)

            self.plugin.iface.mapCanvas().refresh()

        current_row = self.point_detail_twidget.currentRow()
        if current_row == -1:
            return
        item_detail = self.point_detail_twidget.item(current_row, 0)
        point_detail_id = item_detail.data(Qt.UserRole)

        if self.__load_natural_zone(point_detail_id):
            zone = self.__load_natural_zone(point_detail_id)
            self.zone_id = zone.code
            self.natural_zone_edit.setText(zone.name)

            self.land_form_cbox.clear()
            zone_land_forms = self.session.query(PsNaturalZoneLandForm).filter(
                PsNaturalZoneLandForm.natural_zone == zone.code).all()
            for zone_land_form in zone_land_forms:
                land_form = self.session.query(ClLandForm).filter(ClLandForm.code == zone_land_form.land_form).one()
                self.land_form_cbox.addItem(land_form.description, land_form.code)

    @pyqtSlot()
    def on_edit_biomass_button_clicked(self):

        selected_items = self.urgats_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose bio mass!!!"))
            return

        biomass_type_code = self.biomass_type_cbox.itemData(self.biomass_type_cbox.currentIndex())
        biomass_type_text = self.biomass_type_cbox.currentText()
        biomass_type = self.session.query(ClBioMass).filter(ClBioMass.code == biomass_type_code).one()

        selected_row = self.urgats_twidget.currentRow()

        point_detail_id = self.point_detail_id

        biomass_kg_ga = 0
        biomass_avg_m2_gr = 0
        biomass_avg_gr = (self.m_1_value_sbox.value() + self.m_2_value_sbox.value() + self.m_3_value_sbox.value()) / 3
        if biomass_type_code == 1:
            biomass_avg_m2_gr = biomass_avg_gr * 2
        else:
            biomass_avg_m2_gr = biomass_avg_gr

        biomass_kg_ga = biomass_avg_m2_gr * 10000 / 1000

        year_item = self.urgats_twidget.item(selected_row, 0)
        type_item = self.urgats_twidget.item(selected_row, 1)
        biomass_gk_ga_item = self.urgats_twidget.item(selected_row, 2)
        m_1_item = self.urgats_twidget.item(selected_row, 3)
        m_1_value_item = self.urgats_twidget.item(selected_row, 4)
        m_2_item = self.urgats_twidget.item(selected_row, 5)
        m_2_value_item = self.urgats_twidget.item(selected_row, 6)
        m_3_item = self.urgats_twidget.item(selected_row, 7)
        m_3_value_item = self.urgats_twidget.item(selected_row, 8)

        year_item.setText(str(self.print_year_sbox.value()))
        year_item.setData(Qt.UserRole, self.print_year_sbox.value())
        year_item.setData(Qt.UserRole + 1, point_detail_id)

        type_item.setText(unicode(biomass_type_text))
        type_item.setData(Qt.UserRole, biomass_type_code)

        biomass_gk_ga_item.setText(str(biomass_kg_ga))
        biomass_gk_ga_item.setData(Qt.UserRole, biomass_kg_ga)

        m_1_item.setText(str(self.m_1_sbox.value()))
        m_1_item.setData(Qt.UserRole, self.m_1_sbox.value())

        m_1_value_item.setText(str(self.m_1_value_sbox.value()))
        m_1_value_item.setData(Qt.UserRole, self.m_1_value_sbox.value())

        m_2_item.setText(str(self.m_2_sbox.value()))
        m_2_item.setData(Qt.UserRole, self.m_2_sbox.value())

        m_2_value_item.setText(str(self.m_2_value_sbox.value()))
        m_2_value_item.setData(Qt.UserRole, self.m_2_value_sbox.value())

        m_3_item.setText(str(self.m_3_sbox.value()))
        m_3_item.setData(Qt.UserRole, self.m_3_sbox.value())

        m_3_value_item.setText(str(self.m_3_value_sbox.value()))
        m_3_value_item.setData(Qt.UserRole, self.m_3_value_sbox.value())

        point_biomass_count = self.session.query(PsPointUrgatsValue). \
            filter(PsPointUrgatsValue.point_detail_id == point_detail_id). \
            filter(PsPointUrgatsValue.value_year == self.print_year_sbox.value()).count()
        if point_biomass_count == 1:
            point_biomass = self.session.query(PsPointUrgatsValue). \
                filter(PsPointUrgatsValue.point_detail_id == point_detail_id). \
                filter(PsPointUrgatsValue.value_year == self.print_year_sbox.value()).one()

            point_biomass.biomass_type = biomass_type_code
            point_biomass.biomass_type_ref = biomass_type
            point_biomass.biomass_kg_ga = biomass_kg_ga
            point_biomass.m_1 = self.m_1_sbox.value()
            point_biomass.m_1_value = self.m_1_value_sbox.value()
            point_biomass.m_2 = self.m_2_sbox.value()
            point_biomass.m_2_value = self.m_2_value_sbox.value()
            point_biomass.m_3 = self.m_3_sbox.value()
            point_biomass.m_3_value = self.m_3_value_sbox.value()
        else:
            point_biomass = PsPointUrgatsValue()
            point_biomass.point_detail_id = point_detail_id
            point_biomass.value_year = self.print_year_sbox.value()
            point_biomass.biomass_type = biomass_type_code
            point_biomass.biomass_type_ref = biomass_type
            point_biomass.biomass_kg_ga = biomass_kg_ga
            point_biomass.m_1 = self.m_1_sbox.value()
            point_biomass.m_1_value = self.m_1_value_sbox.value()
            point_biomass.m_2 = self.m_2_sbox.value()
            point_biomass.m_2_value = self.m_2_value_sbox.value()
            point_biomass.m_3 = self.m_3_sbox.value()
            point_biomass.m_3_value = self.m_3_value_sbox.value()
            self.session.add(point_biomass)

    @pyqtSlot()
    def on_delete_detail_button_clicked(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            return

        point_detail_id = self.point_detail_id

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to delete the all information for point ?"))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        point_detail_point_count = self.session.query(PsPointDetailPoints). \
            filter(PsPointDetailPoints.point_detail_id == point_detail_id).count()
        if point_detail_point_count > 0:
            point_detail_points = self.session.query(PsPointDetailPoints). \
                filter(PsPointDetailPoints.point_detail_id == point_detail_id).all()
            for point_detail_point in point_detail_points:
                self.session.query(PsPointDetailPoints). \
                    filter(PsPointDetailPoints.point_detail_id == point_detail_id). \
                    filter(PsPointDetailPoints.point_id == point_detail_point.point_id).delete()

        point_detail_cover_count = self.session.query(PsPointPastureValue). \
            filter(PsPointPastureValue.point_detail_id == point_detail_id).count()
        if point_detail_cover_count > 0:
            point_detail_covers = self.session.query(PsPointPastureValue). \
                filter(PsPointPastureValue.point_detail_id == point_detail_id).all()
            for point_detail_cover in point_detail_covers:
                self.session.query(PsPointPastureValue). \
                    filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                    filter(PsPointPastureValue.value_year == point_detail_cover.value_year). \
                    filter(PsPointPastureValue.pasture_value == point_detail_cover.pasture_value).delete()

        point_detail_live_stock_count = self.session.query(PsPointLiveStockValue). \
            filter(PsPointLiveStockValue.point_detail_id == point_detail_id).count()
        if point_detail_live_stock_count > 0:
            point_detail_live_stocks = self.session.query(PsPointLiveStockValue). \
                filter(PsPointLiveStockValue.point_detail_id == point_detail_id).all()
            for point_detail_live_stock in point_detail_live_stocks:
                self.session.query(PsPointLiveStockValue). \
                    filter(PsPointLiveStockValue.point_detail_id == point_detail_id). \
                    filter(PsPointLiveStockValue.value_year == point_detail_live_stock.value_year). \
                    filter(PsPointLiveStockValue.live_stock_type == point_detail_live_stock.live_stock_type).delete()

        point_detail_biomass_count = self.session.query(PsPointUrgatsValue). \
            filter(PsPointUrgatsValue.point_detail_id == point_detail_id).count()
        if point_detail_biomass_count > 0:
            point_detail_biomasses = self.session.query(PsPointUrgatsValue). \
                filter(PsPointUrgatsValue.point_detail_id == point_detail_id).all()
            for point_detail_biomass in point_detail_biomasses:
                self.session.query(PsPointUrgatsValue). \
                    filter(PsPointUrgatsValue.point_detail_id == point_detail_id). \
                    filter(PsPointUrgatsValue.value_year == point_detail_biomass.value_year).delete()

        point_detail_count = self.session.query(PsPointDetail). \
            filter(PsPointDetail.point_detail_id == point_detail_id).count()

        pasture_misseds = self.session.query(PsPastureMissedEvaluation). \
            filter(PsPastureMissedEvaluation.point_detail_id == point_detail_id).all()

        for pasture_missed in pasture_misseds:
            self.session.query(PsPastureMissedEvaluation). \
                filter(PsPastureMissedEvaluation.missed_evaluation == pasture_missed.missed_evaluation). \
                filter(PsPastureMissedEvaluation.point_detail_id == point_detail_id).delete()

        pasture_soils = self.session.query(PsPastureSoilEvaluation). \
            filter(PsPastureSoilEvaluation.point_detail_id == point_detail_id).all()

        for pasture_soil in pasture_soils:
            self.session.query(PsPastureSoilEvaluation). \
                filter(PsPastureSoilEvaluation.soil_evaluation == pasture_soil.soil_evaluation). \
                filter(PsPastureSoilEvaluation.point_detail_id == point_detail_id).delete()

        if point_detail_count == 1:
            self.session.query(PsPointDetail). \
                filter(PsPointDetail.point_detail_id == point_detail_id).delete()

            selected_row = self.point_detail_twidget.currentRow()
            self.point_detail_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_delet_point_button_clicked(self):

        selected_items = self.point_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            return

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to delete selected point ?"))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        current_row = self.point_twidget.currentRow()
        item = self.point_twidget.item(current_row, 0)
        point_id = item.data(Qt.UserRole)

        point_detail_point_count = self.session.query(PsPointDetailPoints). \
            filter(PsPointDetailPoints.point_id == point_id).count()

        if point_detail_point_count > 0:
            point_detail_points = self.session.query(PsPointDetailPoints). \
                filter(PsPointDetailPoints.point_id == point_id).all()
            for point_detail_point in point_detail_points:
                self.session.query(PsPointDetailPoints). \
                    filter(PsPointDetailPoints.point_detail_id == point_detail_point.point_detail_id). \
                    filter(PsPointDetailPoints.point_id == point_id).delete()

        point_count = self.session.query(CaPastureMonitoring). \
            filter(CaPastureMonitoring.point_id == point_id).count()
        if point_count == 1:
            self.session.query(CaPastureMonitoring). \
                filter(CaPastureMonitoring.point_id == point_id).delete()

            selected_row = self.point_twidget.currentRow()
            self.point_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_delete_biomass_button_clicked(self):

        selected_items = self.urgats_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose bio mass!!!"))
            return

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to delete bio mass for point ?"))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        current_row = self.urgats_twidget.currentRow()
        item = self.urgats_twidget.item(current_row, 0)
        biomass_year = item.data(Qt.UserRole)
        point_detail_id = item.data(Qt.UserRole + 1)

        point_biomass_count = self.session.query(PsPointUrgatsValue). \
            filter(PsPointUrgatsValue.value_year == biomass_year). \
            filter(PsPointUrgatsValue.point_detail_id == point_detail_id).count()
        if point_biomass_count == 1:
            self.session.query(PsPointUrgatsValue). \
                filter(PsPointUrgatsValue.value_year == biomass_year). \
                filter(PsPointUrgatsValue.point_detail_id == point_detail_id).delete()

            selected_row = self.urgats_twidget.currentRow()
            self.urgats_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_add_biomass_button_clicked(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            return

        point_detail_id = self.point_detail_id

        point_biomass_count = self.session.query(PsPointUrgatsValue). \
            filter(PsPointUrgatsValue.point_detail_id == point_detail_id). \
            filter(PsPointUrgatsValue.value_year == self.print_year_sbox.value()).count()
        if point_biomass_count == 1:
            PluginUtils.show_message(self, self.tr("Registered"), self.tr("This biomass already register."))
            return

        biomass_code = self.biomass_type_cbox.itemData(self.biomass_type_cbox.currentIndex(), Qt.UserRole)
        biomass = self.session.query(ClBioMass).filter(ClBioMass.code == biomass_code).one()

        biomass_kg_ga = 0
        biomass_avg_m2_gr = 0
        biomass_avg_gr = (self.m_1_value_sbox.value() + self.m_2_value_sbox.value() + self.m_3_value_sbox.value()) / 3
        if biomass_code == 1:
            biomass_avg_m2_gr = biomass_avg_gr * 2
        else:
            biomass_avg_m2_gr = biomass_avg_gr

        biomass_kg_ga = biomass_avg_m2_gr * 10000 / 1000

        row = self.urgats_twidget.rowCount()
        self.urgats_twidget.insertRow(row)

        item = QTableWidgetItem(str(self.print_year_sbox.value()))
        item.setData(Qt.UserRole, self.print_year_sbox.value())
        item.setData(Qt.UserRole + 1, point_detail_id)
        self.urgats_twidget.setItem(row, 0, item)

        item = QTableWidgetItem(unicode(biomass.description))
        item.setData(Qt.UserRole, biomass.code)
        self.urgats_twidget.setItem(row, 1, item)

        item = QTableWidgetItem(str(biomass_kg_ga))
        item.setData(Qt.UserRole, biomass_kg_ga)
        self.urgats_twidget.setItem(row, 2, item)

        item = QTableWidgetItem(str(self.m_1_sbox.value()))
        item.setData(Qt.UserRole, self.m_1_sbox.value())
        self.urgats_twidget.setItem(row, 3, item)

        item = QTableWidgetItem(str(self.m_1_value_sbox.value()))
        item.setData(Qt.UserRole, self.m_1_value_sbox.value())
        self.urgats_twidget.setItem(row, 4, item)

        item = QTableWidgetItem(str(self.m_2_sbox.value()))
        item.setData(Qt.UserRole, self.m_2_sbox.value())
        self.urgats_twidget.setItem(row, 5, item)

        item = QTableWidgetItem(str(self.m_2_value_sbox.value()))
        item.setData(Qt.UserRole, self.m_2_value_sbox.value())
        self.urgats_twidget.setItem(row, 6, item)

        item = QTableWidgetItem(str(self.m_3_sbox.value()))
        item.setData(Qt.UserRole, self.m_3_sbox.value())
        self.urgats_twidget.setItem(row, 7, item)

        item = QTableWidgetItem(str(self.m_3_value_sbox.value()))
        item.setData(Qt.UserRole, self.m_3_value_sbox.value())
        self.urgats_twidget.setItem(row, 8, item)

        ps_point_biomass = PsPointUrgatsValue()
        ps_point_biomass.point_detail_id = point_detail_id
        ps_point_biomass.value_year = self.print_year_sbox.value()
        ps_point_biomass.biomass_type = biomass_code
        ps_point_biomass.biomass_type_ref = biomass
        ps_point_biomass.biomass_kg_ga = biomass_kg_ga
        ps_point_biomass.m_1 = self.m_1_sbox.value()
        ps_point_biomass.m_1_value = self.m_1_value_sbox.value()
        ps_point_biomass.m_2 = self.m_2_sbox.value()
        ps_point_biomass.m_2_value = self.m_2_value_sbox.value()
        ps_point_biomass.m_3 = self.m_3_sbox.value()
        ps_point_biomass.m_3_value = self.m_3_value_sbox.value()

        self.session.add(ps_point_biomass)

    # @pyqtSlot(int)
    # def on_land_form_cbox_currentIndexChanged(self, index):
    #
    #     # selected_items = self.point_detail_twidget.selectedItems()
    #     # if len(selected_items) == 0:
    #     #     PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
    #     #     return
    #     land_form_code = self.land_form_cbox.itemData(self.land_form_cbox.currentIndex())
    #     land_form_text = self.land_form_cbox.currentText()
    #     if land_form_code:
    #         land_form = self.session.query(ClLandForm).filter(ClLandForm.code == land_form_code).one()
    #
    #         current_row = self.point_detail_twidget.currentRow()
    #         if current_row != -1:
    #             land_form_item = self.point_detail_twidget.item(current_row, 3)
    #
    #             land_form_item.setText(unicode(land_form_text))
    #             land_form_item.setData(Qt.UserRole, land_form_code)
    #
    #
    #             point_detail_count = self.session.query(PsPointDetail). \
    #                 filter(PsPointDetail.point_detail_id == self.point_detail_id_edit.text()).count()
    #             if point_detail_count == 1:
    #                 point_detail = self.session.query(PsPointDetail). \
    #                     filter(PsPointDetail.point_detail_id == self.point_detail_id_edit.text()).one()
    #
    #                 point_detail.land_form = land_form_code
    #                 point_detail.land_from_ref = land_form

    def current_parent_object_no(self):

        return self.point_detail_id

    def current_parent_year(self):

        return self.point_year

    @pyqtSlot()
    def on_photo_load_button_clicked(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            return

        current_row = self.point_detail_twidget.currentRow()
        item_detail = self.point_detail_twidget.item(current_row, 0)
        point_detail_id = item_detail.data(Qt.UserRole)

        point_year = self.print_year_sbox.value()
        self.point_detail_id = point_detail_id
        self.point_year = str(point_year)

        self.__setup_photos_twidget(point_detail_id)

        self.__load_photos_twidget(point_detail_id)

    def __load_photos_twidget(self, point_detail_id):

        self.photos_twidget.setRowCount(0)

        if self.around_photo_rbutton.isChecked():

            for i in range(4):
                desc = 'around_' + str(i + 1)
                name = 'around_' + str(i + 1) + '_' + point_detail_id

                row = self.photos_twidget.rowCount()
                self.photos_twidget.insertRow(row)

                item_provided = QTableWidgetItem()
                item_provided.setCheckState(Qt.Unchecked)
                self.photos_twidget.setItem(row, 0, item_provided)

                item_desc = QTableWidgetItem(desc)
                item_desc.setData(Qt.UserRole, desc)
                item_desc.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.photos_twidget.setItem(i, 1, item_desc)

                item_name = QTableWidgetItem("")
                item_name.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.photos_twidget.setItem(i, 2, item_name)

                item_view = QTableWidgetItem("")
                item_delete = QTableWidgetItem("")
                item_open = QTableWidgetItem("")

                self.photos_twidget.setItem(row, 3, item_view)
                self.photos_twidget.setItem(row, 4, item_open)
                self.photos_twidget.setItem(row, 5, item_delete)

            self.__update_around_photo_twidget()

        if self.cover_photo_rbutton.isChecked():
            for i in range(9):
                desc = 'cover_' + str(i + 1)
                name = 'cover_' + str(i + 1) + '_' + point_detail_id

                row = self.photos_twidget.rowCount()
                self.photos_twidget.insertRow(row)

                item_provided = QTableWidgetItem()
                item_provided.setCheckState(Qt.Unchecked)
                self.photos_twidget.setItem(row, 0, item_provided)

                item_desc = QTableWidgetItem(desc)
                item_desc.setData(Qt.UserRole, desc)
                item_desc.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.photos_twidget.setItem(i, 1, item_desc)

                item_name = QTableWidgetItem("")
                item_name.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.photos_twidget.setItem(i, 2, item_name)

                item_view = QTableWidgetItem("")
                item_delete = QTableWidgetItem("")
                item_open = QTableWidgetItem("")

                self.photos_twidget.setItem(row, 3, item_view)
                self.photos_twidget.setItem(row, 4, item_open)
                self.photos_twidget.setItem(row, 5, item_delete)

            self.__update_cover_photo_twidget()

    def __update_around_photo_twidget(self):

        file_path = PasturePath.pasture_photo_file_path()
        point_detail_id = self.point_detail_id
        point_year = self.point_year
        file_path = file_path + '/' + point_year + '/' + point_detail_id + '/image'
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        for file in os.listdir(file_path):
            os.listdir(file_path)

            if file.endswith(".JPG") or file.endswith(".jpg"):

                file_name_split = file.split('_')
                photo_type = file_name_split[0] + '_' + file_name_split[1]
                file_name = file
                file_point_detail_id = file_name_split[2]
                file_point_detail_id = file_point_detail_id.split('.')[0]
                for i in range(4):
                    photo_type_item = self.photos_twidget.item(i, DOC_TYPE_COLUMN)
                    photo_type_code = str(photo_type_item.data(Qt.UserRole))

                    if photo_type == photo_type_code and point_detail_id == file_point_detail_id:
                        item_name = self.photos_twidget.item(i, DOC_NAME_COLUMN)
                        item_name.setText(file_name)

                        item_provided = self.photos_twidget.item(i, DOC_PROVIDED_COLUMN)
                        item_provided.setCheckState(Qt.Checked)

                        item_open = self.photos_twidget.item(i, DOC_OPEN_COLUMN)
                        item_remove = self.photos_twidget.item(i, DOC_REMOVE_COLUMN)
                        item_view = self.photos_twidget.item(i, DOC_VIEW_COLUMN)

                        self.photos_twidget.setItem(i, DOC_PROVIDED_COLUMN, item_provided)
                        self.photos_twidget.setItem(i, DOC_OPEN_COLUMN, item_open)
                        self.photos_twidget.setItem(i, DOC_REMOVE_COLUMN, item_remove)
                        self.photos_twidget.setItem(i, DOC_VIEW_COLUMN, item_view)
                        self.photos_twidget.setItem(i, DOC_NAME_COLUMN, item_name)

    def __update_cover_photo_twidget(self):

        file_path = PasturePath.pasture_photo_file_path()
        point_detail_id = self.point_detail_id
        point_year = self.point_year
        file_path = file_path + '/' + point_year + '/' + point_detail_id + '/image'
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        for file in os.listdir(file_path):
            os.listdir(file_path)
            if file.endswith(".JPG") or file.endswith(".jpg"):
                file_name_split = file.split('_')
                photo_type = file_name_split[0] + '_' + file_name_split[1]
                file_name = file
                file_point_detail_id = file_name_split[2]
                file_point_detail_id = file_point_detail_id.split('.')[0]
                for i in range(9):
                    photo_type_item = self.photos_twidget.item(i, DOC_TYPE_COLUMN)
                    photo_type_code = str(photo_type_item.data(Qt.UserRole))
                    if photo_type == photo_type_code and point_detail_id == file_point_detail_id:
                        item_name = self.photos_twidget.item(i, DOC_NAME_COLUMN)
                        item_name.setText(file_name)

                        item_provided = self.photos_twidget.item(i, DOC_PROVIDED_COLUMN)
                        item_provided.setCheckState(Qt.Checked)

                        item_open = self.photos_twidget.item(i, DOC_OPEN_COLUMN)
                        item_remove = self.photos_twidget.item(i, DOC_REMOVE_COLUMN)
                        item_view = self.photos_twidget.item(i, DOC_VIEW_COLUMN)

                        self.photos_twidget.setItem(i, DOC_PROVIDED_COLUMN, item_provided)
                        self.photos_twidget.setItem(i, DOC_OPEN_COLUMN, item_open)
                        self.photos_twidget.setItem(i, DOC_REMOVE_COLUMN, item_remove)
                        self.photos_twidget.setItem(i, DOC_VIEW_COLUMN, item_view)
                        self.photos_twidget.setItem(i, DOC_NAME_COLUMN, item_name)

    @pyqtSlot()
    def on_print_button_clicked(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            return

        restrictions = DatabaseUtils.working_l2_code()
        if not restrictions:
            PluginUtils.show_message(self, self.tr("Connection Error"), self.tr("Please connect to database!!!"))
            return

        point_id = self.point_detail_id_edit.text()
        default_path = r'D:/TM_LM2/pasture/' + point_id
        default_parent_path = r'D:/TM_LM2'
        if not os.path.exists(default_parent_path):
            os.makedirs('D:/TM_LM2')

        if not os.path.exists(default_path):
            os.makedirs(default_path)

        workbook = xlsxwriter.Workbook(default_path + "/" + point_id + ".xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 9)
        worksheet.set_column('H:H', 9)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 30)
        worksheet.set_column('K:K', 50)
        worksheet.set_column('L:L', 11)
        worksheet.set_column('M:M', 15)
        worksheet.set_column('N:N', 15)
        worksheet.set_column('O:O', 15)
        worksheet.set_column('P:P', 15)
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

        worksheet.set_row(3, 25)
        worksheet.set_row(4, 25)
        worksheet.set_row(5, 50)
        worksheet.set_landscape()
        worksheet.set_paper(8)
        worksheet.set_margins(left=0.3, right=0.3)

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(9)
        format.set_border(1)
        format.set_shrink()

        format_data = workbook.add_format()
        format_data.set_text_wrap()
        format_data.set_align('center')
        format_data.set_align('vcenter')
        format_data.set_font_name('Times New Roman')
        format_data.set_font_size(9)
        format_data.set_border(1)
        format_data.set_shrink()
        format_data.set_bg_color('#C0C0C0')

        format_null_data = workbook.add_format()
        format_null_data.set_text_wrap()
        format_null_data.set_align('center')
        format_null_data.set_align('vcenter')
        format_null_data.set_font_name('Times New Roman')
        format_null_data.set_font_size(9)
        format_null_data.set_border(1)
        format_null_data.set_shrink()
        format_null_data.set_bg_color('#D14B25')

        self.format_photo = workbook.add_format()
        self.format_photo.set_text_wrap()
        self.format_photo.set_align('center')
        self.format_photo.set_align('vcenter')
        self.format_photo.set_font_name('Times New Roman')
        self.format_photo.set_font_size(9)
        self.format_photo.set_border(1)
        self.format_photo.set_shrink()
        self.format_photo.set_bg_color('#1EC93D')

        self.format_photo_yellow = workbook.add_format()
        self.format_photo_yellow.set_text_wrap()
        self.format_photo_yellow.set_align('center')
        self.format_photo_yellow.set_align('vcenter')
        self.format_photo_yellow.set_font_name('Times New Roman')
        self.format_photo_yellow.set_font_size(9)
        self.format_photo_yellow.set_border(1)
        self.format_photo_yellow.set_shrink()
        self.format_photo_yellow.set_bg_color('#FCFC15')

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

        format_year = workbook.add_format()
        format_year.set_text_wrap()
        format_year.set_align('center')
        format_year.set_align('vcenter')
        format_year.set_font_name('Times New Roman')
        format_year.set_font_size(10)

        worksheet.merge_range('B3:D3', self.__load_year(), format_year)

        worksheet.merge_range('D2:L2', u'Фото мониторингийн мэдээ', format_header)
        worksheet.merge_range('A4:A6', u'Д/д', format)
        worksheet.merge_range('B4:F4', u'Байршил', format)
        worksheet.merge_range('B5:B6', u'Аймаг', format)
        worksheet.merge_range('C5:C6', u'Сум', format)
        worksheet.merge_range('D5:D6', u'Баг', format)
        worksheet.merge_range('E5:E6', u'БАХ', format)
        worksheet.merge_range('F5:F6', u'Улирал', format)
        worksheet.merge_range('G5:G6', u'Газрын нэр', format)

        worksheet.merge_range('G4:P4', u'Газрын мэдээлэл', format)
        worksheet.merge_range('H5:H6', u'Цэгийн дугаар', format)
        worksheet.merge_range('I5:I6', u'Мониторинг хийсэн огноо', format)
        worksheet.merge_range('J5:J6', u'Байгалийн бүс, бүслүүр', format)
        worksheet.merge_range('K5:K6', u'Бэлчээрийн төлөв байдал, өөрчлөлтийн загвар', format)
        worksheet.merge_range('L5:L6', u'Өндөршил', format)

        worksheet.merge_range('M5:N5', u'Эхлэл', format)
        worksheet.write('M6', u'Өргөрөг', format)
        worksheet.write('N6', u'Уртраг', format)

        worksheet.merge_range('O5:P5', u'Төгсгөл', format)
        worksheet.write('O6', u'Өргөрөг', format)
        worksheet.write('P6', u'Уртраг', format)

        pasture_plants = self.session.query(PsNaturalZonePlants).filter(
            PsNaturalZonePlants.natural_zone == self.zone_id).all()

        self.__load_zone_header(worksheet, pasture_plants, format, format_null_data)
        self.__load_data(worksheet, pasture_plants, format_data, format_null_data)
        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/" + point_id + ".xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"),
                                   self.tr("This file is already opened. Please close re-run"))

    def __load_data(self, worksheet, pasture_plants, format, format_null_data):

        row_num = self.point_detail_twidget.rowCount()

        data_row = 6
        col = 0
        row_number = 1

        for row in range(row_num):
            item = self.point_detail_twidget.item(row, 0)
            point_detail_id = item.data(Qt.UserRole)

            point_detail = self.session.query(PsPointDetail).filter(
                PsPointDetail.point_detail_id == point_detail_id).one()

            land_form = self.session.query(ClLandForm).filter(ClLandForm.code == point_detail.land_form).one()
            point_id = None
            points = self.session.query(PsPointDetailPoints).filter(
                PsPointDetailPoints.point_detail_id == point_detail_id).all()

            first_point_x = 0
            first_point_y = 0

            second_point_x = 0
            second_point_y = 0

            point_count = 1
            for point in points:
                point = self.session.query(CaPastureMonitoring).filter(
                    CaPastureMonitoring.point_id == point.point_id).one()
                if point_count == 1:
                    first_point_x = point.x_coordinate
                    first_point_y = point.y_coordinate
                if point_count == 2:
                    second_point_x = point.x_coordinate
                    second_point_y = point.y_coordinate
                point_id = point.point_id
                point_count += 1
            pug_name = ''
            pasture_type = ''
            if point_id:
                point = self.session.query(CaPastureMonitoring).filter(CaPastureMonitoring.point_id == point_id).one()
                zone = self.session.query(AuNaturalZone).filter(point.geometry.ST_Within(AuNaturalZone.geometry)).one()
                au3 = self.session.query(AuLevel3).filter(point.geometry.ST_Within(AuLevel3.geometry)).one()
                au2 = self.session.query(AuLevel2).filter(point.geometry.ST_Within(AuLevel2.geometry)).one()
                au1 = self.session.query(AuLevel1).filter(point.geometry.ST_Within(AuLevel1.geometry)).one()

                pasture_parcel_count = self.session.query(CaPastureParcel).filter(
                    point.geometry.ST_Within(CaPastureParcel.geometry)).count()
                if pasture_parcel_count == 1:
                    pasture_parcel = self.session.query(CaPastureParcel).filter(
                        point.geometry.ST_Within(CaPastureParcel.geometry)).one()
                    pasture_type = pasture_parcel.pasture_type
                pug_boundary_count = self.session.query(CaPUGBoundary).filter(
                    point.geometry.ST_Within(CaPUGBoundary.geometry)).count()
                if pug_boundary_count == 1:
                    pug_boundary = self.session.query(CaPUGBoundary).filter(
                        point.geometry.ST_Within(CaPUGBoundary.geometry)).one()
                    pug_name = pug_boundary.group_name
                zone_id = zone.code

                monitoring_year = self.print_year_sbox.value()
                monitoring_date = ''
                d_value_count = self.session.query(PsPointDaatsValue). \
                    filter(PsPointDaatsValue.point_detail_id == point_detail_id). \
                    filter(PsPointDaatsValue.monitoring_year == monitoring_year).count()
                if d_value_count == 1:
                    d_value = self.session.query(PsPointDaatsValue). \
                        filter(PsPointDaatsValue.point_detail_id == point_detail_id). \
                        filter(PsPointDaatsValue.monitoring_year == monitoring_year).one()
                    if d_value.register_date:
                        monitoring_date = str(d_value.register_date)
                worksheet.write(data_row, col, row_number, format)
                worksheet.write(data_row, col + 1, au1.name, self.__check_null(au1.name, format, format_null_data))
                worksheet.write(data_row, col + 2, au2.name, self.__check_null(au2.name, format, format_null_data))
                worksheet.write(data_row, col + 3, au3.name, self.__check_null(au3.name, format, format_null_data))
                worksheet.write(data_row, col + 4, pug_name, self.__check_null(pug_name, format, format_null_data))
                worksheet.write(data_row, col + 5, pasture_type,
                                self.__check_null(pasture_type, format, format_null_data))
                worksheet.write(data_row, col + 6, point_detail.land_name,
                                self.__check_null(point_detail.land_name, format, format_null_data))
                worksheet.write(data_row, col + 7, str(point_detail_id),
                                self.__check_null(str(point_detail_id), format, format_null_data))
                worksheet.write(data_row, col + 8, monitoring_date,
                                self.__check_null(monitoring_date, format, format_null_data))
                worksheet.write(data_row, col + 9, (zone.name),
                                self.__check_null((zone.name), format, format_null_data))
                worksheet.write(data_row, col + 10, (land_form.description),
                                self.__check_null((land_form.description), format, format_null_data))
                worksheet.write(data_row, col + 11, str(point_detail.elevation),
                                self.__check_null(str(point_detail.elevation), format, format_null_data))

                worksheet.write(data_row, col + 12, str(first_point_x),
                                self.__check_null(str(first_point_x), format, format_null_data))
                worksheet.write(data_row, col + 13, str(first_point_y),
                                self.__check_null(str(first_point_y), format, format_null_data))
                worksheet.write(data_row, col + 14, str(second_point_x),
                                self.__check_null(str(second_point_x), format, format_null_data))
                worksheet.write(data_row, col + 15, str(second_point_y),
                                self.__check_null(str(second_point_y), format, format_null_data))

                print_year = self.print_year_sbox.value()
                self.__load_cover_plants_data(zone_id, point_detail_id, data_row, print_year, pasture_plants, worksheet,
                                              format, format_null_data)

                data_row += 1
                row_number += 1

    def __load_cover_plants_data(self, zone_id, point_detail_id, data_row, print_year, pasture_plants, worksheet,
                                 format, format_null_data):

        col = 16
        zone = self.session.query(AuNaturalZone).filter((AuNaturalZone.code == 1)).one()
        pasture_plants = self.session.query(PsNaturalZonePlants).filter(
            PsNaturalZonePlants.natural_zone == zone.code).all()
        for i in pasture_plants:
            if zone_id == 1 or zone_id == 6 or zone_id == 7:
                pasture_value_count = self.session.query(PsPointPastureValue). \
                    filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                    filter(PsPointPastureValue.value_year == print_year). \
                    filter(PsPointPastureValue.pasture_value == i.plants).count()
                cover_value = 0
                if pasture_value_count == 1:
                    pasture_value = self.session.query(PsPointPastureValue). \
                        filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                        filter(PsPointPastureValue.value_year == print_year). \
                        filter(PsPointPastureValue.pasture_value == i.plants).one()
                    cover_value = pasture_value.current_value
                if i.plants == 1:
                    if cover_value == 0:
                        worksheet.write(data_row, col, str(cover_value), format_null_data)
                    else:
                        worksheet.write(data_row, col, str(cover_value), format)
                else:
                    worksheet.write(data_row, col, str(cover_value), format)
            else:

                worksheet.write(data_row, col, '', format)

            col = col + 1

        zone = self.session.query(AuNaturalZone).filter((AuNaturalZone.code == 2)).one()
        pasture_plants = self.session.query(PsNaturalZonePlants).filter(
            PsNaturalZonePlants.natural_zone == zone.code).all()
        for i in pasture_plants:
            if zone_id == 2:
                pasture_value_count = self.session.query(PsPointPastureValue). \
                    filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                    filter(PsPointPastureValue.value_year == print_year). \
                    filter(PsPointPastureValue.pasture_value == i.plants).count()
                cover_value = 0
                if pasture_value_count == 1:
                    pasture_value = self.session.query(PsPointPastureValue). \
                        filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                        filter(PsPointPastureValue.value_year == print_year). \
                        filter(PsPointPastureValue.pasture_value == i.plants).one()
                    cover_value = pasture_value.current_value
                if i.plants == 1:
                    if cover_value == 0:
                        worksheet.write(data_row, col, str(cover_value), format_null_data)
                    else:
                        worksheet.write(data_row, col, str(cover_value), format)
                else:
                    worksheet.write(data_row, col, str(cover_value), format)
            else:

                worksheet.write(data_row, col, '', format)
            col = col + 1

        zone = self.session.query(AuNaturalZone).filter((AuNaturalZone.code == 3)).one()
        pasture_plants = self.session.query(PsNaturalZonePlants).filter(
            PsNaturalZonePlants.natural_zone == zone.code).all()
        for i in pasture_plants:
            if zone_id == 3 or zone_id == 4:
                pasture_value_count = self.session.query(PsPointPastureValue). \
                    filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                    filter(PsPointPastureValue.value_year == print_year). \
                    filter(PsPointPastureValue.pasture_value == i.plants).count()
                cover_value = 0
                if pasture_value_count == 1:
                    pasture_value = self.session.query(PsPointPastureValue). \
                        filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                        filter(PsPointPastureValue.value_year == print_year). \
                        filter(PsPointPastureValue.pasture_value == i.plants).one()
                    cover_value = pasture_value.current_value

                if i.plants == 1:
                    if cover_value == 0:
                        worksheet.write(data_row, col, str(cover_value), format_null_data)
                    else:
                        worksheet.write(data_row, col, str(cover_value), format)
                else:
                    worksheet.write(data_row, col, str(cover_value), format)
            else:

                worksheet.write(data_row, col, '', format)
            col = col + 1

        zone = self.session.query(AuNaturalZone).filter((AuNaturalZone.code == 5)).one()
        pasture_plants = self.session.query(PsNaturalZonePlants).filter(
            PsNaturalZonePlants.natural_zone == zone.code).all()
        for i in pasture_plants:
            if zone_id == 5:
                pasture_value_count = self.session.query(PsPointPastureValue). \
                    filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                    filter(PsPointPastureValue.value_year == print_year). \
                    filter(PsPointPastureValue.pasture_value == i.plants).count()
                cover_value = 0
                if pasture_value_count == 1:
                    pasture_value = self.session.query(PsPointPastureValue). \
                        filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                        filter(PsPointPastureValue.value_year == print_year). \
                        filter(PsPointPastureValue.pasture_value == i.plants).one()
                    cover_value = pasture_value.current_value
                if i.plants == 1:
                    if cover_value == 0:
                        worksheet.write(data_row, col, str(cover_value), format_null_data)
                    else:
                        worksheet.write(data_row, col, str(cover_value), format)
                else:
                    worksheet.write(data_row, col, str(cover_value), format)


            else:

                worksheet.write(data_row, col, '', format)
            col = col + 1

        live_stocks = self.session.query(ClliveStock).all()
        self.__load_live_stock_data(point_detail_id, col, data_row, print_year, worksheet, format, live_stocks,
                                    pasture_plants, format_null_data)

    def __load_live_stock_data(self, point_detail_id, col, data_row, print_year, worksheet, format, live_stocks,
                               pasture_plants, format_null_data):

        convert_sum_value = 0
        convert_value = 0
        converted_count_value = 0
        for live_stock in live_stocks:

            live_stock_convert = self.session.query(PsLiveStockConvert). \
                filter(PsLiveStockConvert.live_stock_type == live_stock.code).one()
            convert_value = live_stock_convert.convert_value
            live_stock_value_count = self.session.query(PsPointLiveStockValue). \
                filter(PsPointLiveStockValue.live_stock_type == live_stock.code). \
                filter(PsPointLiveStockValue.value_year == print_year). \
                filter(PsPointLiveStockValue.point_detail_id == point_detail_id).count()
            current_value = 0
            if live_stock_value_count == 1:
                live_stock_value = self.session.query(PsPointLiveStockValue). \
                    filter(PsPointLiveStockValue.live_stock_type == live_stock.code). \
                    filter(PsPointLiveStockValue.value_year == print_year). \
                    filter(PsPointLiveStockValue.point_detail_id == point_detail_id).one()
                current_value = live_stock_value.current_value
                converted_count_value = current_value * convert_value

                convert_sum_value = convert_sum_value + converted_count_value

            worksheet.write(data_row, col, str(current_value), format)
            col = col + 1

        if convert_sum_value == 0:
            worksheet.write(data_row, col, str(convert_sum_value), format_null_data)
        else:
            worksheet.write(data_row, col, convert_sum_value, format)

        parcel_area_ga = 0
        if self.__load_parcel(point_detail_id):
            parcel = self.__load_parcel(point_detail_id)
            parcel_area_ga = parcel.area_ga
        col = col + 1
        worksheet.write(data_row, col, str(parcel_area_ga), format)

        self.__load_d_data(point_detail_id, col, data_row, print_year, worksheet, format, format_null_data)

    def __load_d_data(self, point_detail_id, col, data_row, print_year, worksheet, format, format_null_data):

        data_value_count = self.session.query(PsPointDaatsValue).filter(
            PsPointDaatsValue.monitoring_year == print_year). \
            filter(PsPointDaatsValue.point_detail_id == point_detail_id).count()

        if data_value_count == 1:
            data_value = self.session.query(PsPointDaatsValue).filter(PsPointDaatsValue.monitoring_year == print_year). \
                filter(PsPointDaatsValue.point_detail_id == point_detail_id).one()

            worksheet.write(data_row, col, str(round(data_value.area_ga, 2)), format)
            worksheet.write(data_row, col + 1, str(round(data_value.biomass, 2)), format)
            worksheet.write(data_row, col + 2, str(''), format)
            worksheet.write(data_row, col + 3, str(data_value.rc), format)
            worksheet.write(data_row, col + 4, str(''), format)
            worksheet.write(data_row, col + 5, str(data_value.duration), format)
            worksheet.write(data_row, col + 6, str(round(data_value.d1, 2)), format)
            worksheet.write(data_row, col + 7, str(round(data_value.d1_100ga, 2)), format)
            worksheet.write(data_row, col + 8, str(round(data_value.d2, 2)), format)
            worksheet.write(data_row, col + 9, str(round(data_value.d3, 2)), format)
            worksheet.write(data_row, col + 10, str(round(data_value.unelgee, 2)), format)
        else:
            worksheet.write(data_row, col, '', format_null_data)
            worksheet.write(data_row, col + 1, '', format_null_data)
            worksheet.write(data_row, col + 2, '', format_null_data)
            worksheet.write(data_row, col + 3, '', format_null_data)
            worksheet.write(data_row, col + 4, '', format_null_data)
            worksheet.write(data_row, col + 5, '', format_null_data)
            worksheet.write(data_row, col + 6, '', format_null_data)
            worksheet.write(data_row, col + 7, '', format_null_data)
            worksheet.write(data_row, col + 8, '', format_null_data)
            worksheet.write(data_row, col + 9, '', format_null_data)
            worksheet.write(data_row, col + 10, '', format_null_data)

        photo_count = self.__photo_count(point_detail_id)
        if photo_count == 0:
            worksheet.write(data_row, col + 11, str(self.__photo_count(point_detail_id)), format_null_data)
        elif photo_count > 0 and photo_count < 10:
            worksheet.write(data_row, col + 11, str(self.__photo_count(point_detail_id)), self.format_photo_yellow)
        else:
            worksheet.write(data_row, col + 11, str(self.__photo_count(point_detail_id)), self.format_photo)

    def __load_zone_header(self, worksheet, pasture_plants, format, format_null_data):

        point_detail_id = self.point_detail_id_edit.text()

        if self.__load_natural_zone(point_detail_id):
            zone = self.__load_natural_zone(point_detail_id)
            zone_id = zone.code

        col = 15
        row = 5
        row_0 = 3
        row_1 = 4
        first_col = 16
        merge_zone_col = 16
        last_col = 25

        zone = self.session.query(AuNaturalZone).filter((AuNaturalZone.code == 1)).one()
        pasture_plants = self.session.query(PsNaturalZonePlants).filter(
            PsNaturalZonePlants.natural_zone == zone.code).all()
        for i in pasture_plants:
            plants = self.session.query(ClPastureValues).filter(ClPastureValues.code == i.plants).one()
            col = col + 1
            last_col = col
            worksheet.write(row, col, plants.description, format)

        worksheet.merge_range(row_1, first_col, row_1, last_col, u"Өндөр уул, Ойт хээр, Нугын хээр", format)

        first_col = last_col + 1
        zone = self.session.query(AuNaturalZone).filter((AuNaturalZone.code == 2)).one()
        pasture_plants = self.session.query(PsNaturalZonePlants).filter(
            PsNaturalZonePlants.natural_zone == zone.code).all()
        for i in pasture_plants:
            plants = self.session.query(ClPastureValues).filter(ClPastureValues.code == i.plants).one()
            col = col + 1
            last_col = col
            worksheet.write(row, col, plants.description, format)

        worksheet.merge_range(row_1, first_col, row_1, last_col, zone.name, format)

        first_col = last_col + 1
        zone = self.session.query(AuNaturalZone).filter((AuNaturalZone.code == 3)).one()
        pasture_plants = self.session.query(PsNaturalZonePlants).filter(
            PsNaturalZonePlants.natural_zone == zone.code).all()
        for i in pasture_plants:
            plants = self.session.query(ClPastureValues).filter(ClPastureValues.code == i.plants).one()
            col = col + 1
            last_col = col
            worksheet.write(row, col, plants.description, format)

        worksheet.merge_range(row_1, first_col, row_1, last_col, u"Цөлжүү хээр, Цөлийн хээр", format)

        first_col = last_col + 1
        zone = self.session.query(AuNaturalZone).filter((AuNaturalZone.code == 5)).one()
        pasture_plants = self.session.query(PsNaturalZonePlants).filter(
            PsNaturalZonePlants.natural_zone == zone.code).all()
        for i in pasture_plants:
            plants = self.session.query(ClPastureValues).filter(ClPastureValues.code == i.plants).one()
            col = col + 1
            last_col = col
            worksheet.write(row, col, plants.description, format)

        worksheet.merge_range(row_1, first_col, row_1, last_col, zone.name, format)

        worksheet.merge_range(row_0, merge_zone_col, row_0, last_col, u'Байгалийн бүс', format)

        live_stocks = self.session.query(ClliveStock).all()
        self.__load_live_stock_header(col, worksheet, format, live_stocks)

    def __load_live_stock_header(self, col, worksheet, format, live_stocks):

        row = 5
        row_0 = 3
        row_1 = 4
        first_col = col + 1
        last_col = col + 5
        for live_stock in live_stocks:
            col = col + 1
            last_col = col
            worksheet.write(row, col, live_stock.description, format)

        col = col + 1
        last_col = col
        worksheet.write(row, col, u'Хонин толгой', format)

        worksheet.merge_range(row_0, first_col, row_1, last_col, u'Мал тоо', format)

        col = col + 1
        first_col = col
        worksheet.write(row, col, u'Бэлчээрийн талбай', format)
        worksheet.write(row - 1, col, u'talbai', format)
        col = col + 1
        worksheet.write(row, col, u'Бэлчээрийн ургац кг/га', format)
        worksheet.write(row - 1, col, u'urgats', format)
        col = col + 1
        worksheet.write(row, col, u'Төлөв байдлын код', format)
        worksheet.write(row - 1, col, u'tb_code', format)
        col = col + 1
        worksheet.write(row, col, u'Сэргэх чадварын ангилал', format)
        worksheet.write(row - 1, col, u'RC', format)
        col = col + 1
        worksheet.write(row, col, u'Хугацаа', format)
        worksheet.write(row - 1, col, u'hugatsaa', format)
        col = col + 1
        worksheet.write(row, col, u'Бэлчээрлэх хоног', format)
        worksheet.write(row - 1, col, u'honog', format)
        col = col + 1
        worksheet.write(row, col, u'1 га-д бэлчих ХТ D1', format)
        worksheet.write(row - 1, col, u'd1', format)
        col = col + 1
        worksheet.write(row, col, u'100 га-д бэлчих ХТ D1-100га', format)
        worksheet.write(row - 1, col, u'd1_1_100', format)
        col = col + 1
        worksheet.write(row, col, u'1 ХТ-д шаардлагатай талбай', format)
        worksheet.write(row - 1, col, u'd_2', format)
        col = col + 1
        worksheet.write(row, col, u'Боломжит даац', format)
        worksheet.write(row - 1, col, u'd_3', format)

        col = col + 1
        worksheet.write(row, col, u'Боломжит ХТ - Одоо байгаа ХТ = Үнэлгээ', format)
        worksheet.write(row - 1, col, u'unelgee', format)

        col = col + 1
        worksheet.write(row, col, u'Photo Count', format)
        worksheet.write(row - 1, col, u'Зургын тоо', format)

        last_col = col
        worksheet.merge_range(row_0, first_col, row_1 - 1, last_col, u'Бэлчээрийн даац, үнэлгээ', format)

    @pyqtSlot(int)
    def on_input_area_chbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.area_ga_edit.setEnabled(True)
        else:
            self.area_ga_edit.setEnabled(False)

    @pyqtSlot(int)
    def on_input_duration_chbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.duration_days_edit.setEnabled(True)
        else:
            self.duration_days_edit.setEnabled(False)

    def __load_rc(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            is_valid = False
            return

        print_year = self.print_year_sbox.value()

        point_detail_id = self.point_detail_id

        point_detail = self.session.query(PsPointDetail).filter(PsPointDetail.point_detail_id == point_detail_id).one()
        land_form_code = point_detail.land_form

        formula_types = self.session.query(PsFormulaTypeLandForm.formula_type). \
            filter(PsFormulaTypeLandForm.land_form == land_form_code).group_by(PsFormulaTypeLandForm.formula_type).all()
        recover_class = None
        for formula_type in formula_types:
            if self.calc_present_rbutton.isChecked():
                if formula_type.formula_type == 1:
                    rc_id = None
                    rc_code = None
                    is_stop = False
                    is_row_rc = True
                    rcs = self.session.query(PsRecoveryClass).order_by(PsRecoveryClass.id.desc()).all()
                    for rc in rcs:
                        if is_stop:
                            break

                        status_plants_count = self.session.query(PsPastureStatusFormula). \
                            filter(PsPastureStatusFormula.natural_zone == self.zone_id). \
                            filter(PsPastureStatusFormula.rc_id == rc.id). \
                            filter(PsPastureStatusFormula.land_form == land_form_code).count()

                        if not status_plants_count == 0:
                            status_plants = self.session.query(PsPastureStatusFormula). \
                                filter(PsPastureStatusFormula.natural_zone == self.zone_id). \
                                filter(PsPastureStatusFormula.rc_id == rc.id). \
                                filter(PsPastureStatusFormula.land_form == land_form_code).all()
                            is_row_rc = True
                            for status_plant in status_plants:
                                plants_year_count = self.session.query(PsPointPastureValue). \
                                    filter(PsPointPastureValue.value_year == print_year). \
                                    filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                                    filter(PsPointPastureValue.pasture_value == status_plant.plants).count()
                                if plants_year_count == 1:
                                    pasture_value = self.session.query(PsPointPastureValue). \
                                        filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                                        filter(PsPointPastureValue.value_year == print_year). \
                                        filter(PsPointPastureValue.pasture_value == status_plant.plants).one()

                                    status_plants = self.session.query(PsPastureStatusFormula). \
                                        filter(PsPastureStatusFormula.natural_zone == self.zone_id). \
                                        filter(PsPastureStatusFormula.rc_id == rc.id). \
                                        filter(PsPastureStatusFormula.plants == pasture_value.pasture_value). \
                                        filter(PsPastureStatusFormula.land_form == land_form_code).one()

                                    if status_plants.symbol_id == 1:
                                        if not pasture_value.current_value > status_plants.cover_precent:
                                            is_row_rc = False
                                    if status_plants.symbol_id == 2:
                                        if not pasture_value.current_value < status_plants.cover_precent:
                                            is_row_rc = False
                                    if status_plants.symbol_id == 3:
                                        if not pasture_value.current_value >= status_plants.cover_precent:
                                            is_row_rc = False
                                    if status_plants.symbol_id == 4:
                                        if not pasture_value.current_value <= status_plants.cover_precent:
                                            is_row_rc = False
                                    if status_plants.symbol_id == 5:
                                        if not pasture_value.current_value == status_plants.cover_precent:
                                            is_row_rc = False
                            if is_row_rc:
                                is_stop = True
                                recover_class = rc
            if self.calc_comparison_rbutton.isChecked():
                if formula_type.formula_type == 2:
                    is_row_rc = True
                    is_stop = False
                    rcs = self.session.query(PsRecoveryClass).order_by(PsRecoveryClass.id.desc()).all()
                    for rc in rcs:
                        if is_stop:
                            break
                        pasture_comp_formula_count = self.session.query(PsPastureComparisonFormula). \
                            filter(PsPastureComparisonFormula.land_form == land_form_code). \
                            filter(PsPastureComparisonFormula.natural_zone == self.zone_id). \
                            filter(PsPastureComparisonFormula.rc_id == rc.id).count()
                        if not pasture_comp_formula_count == 0:
                            pasture_comp_formulas = self.session.query(PsPastureComparisonFormula). \
                                filter(PsPastureComparisonFormula.land_form == land_form_code). \
                                filter(PsPastureComparisonFormula.natural_zone == self.zone_id). \
                                filter(PsPastureComparisonFormula.rc_id == rc.id).all()
                            more_value = 0
                            less_value = 0
                            is_row_rc = True
                            for pasture_comp_formula in pasture_comp_formulas:
                                plants_year_count = self.session.query(PsPointPastureValue). \
                                    filter(PsPointPastureValue.value_year == print_year). \
                                    filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                                    filter(PsPointPastureValue.pasture_value == pasture_comp_formula.plants).count()
                                if plants_year_count == 1:
                                    pasture_value = self.session.query(PsPointPastureValue). \
                                        filter(PsPointPastureValue.point_detail_id == point_detail_id). \
                                        filter(PsPointPastureValue.value_year == print_year). \
                                        filter(PsPointPastureValue.pasture_value == pasture_comp_formula.plants).one()
                                    if pasture_comp_formula.symbol_id == 1:
                                        more_value = more_value + pasture_value.current_value
                                    if pasture_comp_formula.symbol_id == 2:
                                        less_value = less_value + pasture_value.current_value
                            if not more_value > less_value:
                                is_row_rc = False

                            if is_row_rc:
                                is_stop = True
                                recover_class = rc
                        else:
                            evaluation_formulas_count = self.session.query(PsPastureEvaluationFormula). \
                                filter(PsPastureEvaluationFormula.natural_zone == self.zone_id). \
                                filter(PsPastureEvaluationFormula.land_form == land_form_code). \
                                filter(PsPastureEvaluationFormula.rc_id == rc.id).count()
                            if not evaluation_formulas_count == 0:
                                evaluation_formulas = self.session.query(PsPastureEvaluationFormula). \
                                    filter(PsPastureEvaluationFormula.natural_zone == self.zone_id). \
                                    filter(PsPastureEvaluationFormula.land_form == land_form_code). \
                                    filter(PsPastureEvaluationFormula.rc_id == rc.id).all()

                                point_detail_id = self.point_detail_id
                                current_year = self.print_year_sbox.value()
                                is_row_rc = True
                                for evaluation_formula in evaluation_formulas:
                                    formula_ball = evaluation_formula.soil_evaluation_ref.ball
                                    pasture_soil_evaluation_count = self.session.query(PsPastureSoilEvaluation). \
                                        filter(PsPastureSoilEvaluation.point_detail_id == point_detail_id). \
                                        filter(PsPastureSoilEvaluation.current_year == current_year).count()
                                    if pasture_soil_evaluation_count == 1:
                                        pasture_soil_evaluation = self.session.query(PsPastureSoilEvaluation). \
                                            filter(PsPastureSoilEvaluation.point_detail_id == point_detail_id). \
                                            filter(PsPastureSoilEvaluation.current_year == current_year).one()
                                        ball = pasture_soil_evaluation.soil_evaluation_ref.ball
                                        if not ball >= formula_ball:
                                            is_row_rc = False
                                if is_row_rc:
                                    is_stop = True
                                    recover_class = rc

        return recover_class

    def __load_urgats(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            is_valid = False
            return

        print_year = self.print_year_sbox.value()

        point_detail_id = self.point_detail_id

        current_value = 0
        urgats_count = self.session.query(PsPointUrgatsValue). \
            filter(PsPointUrgatsValue.point_detail_id == point_detail_id). \
            filter(PsPointUrgatsValue.value_year == print_year).count()
        if urgats_count == 1:
            urgats = self.session.query(PsPointUrgatsValue). \
                filter(PsPointUrgatsValue.point_detail_id == point_detail_id). \
                filter(PsPointUrgatsValue.value_year == print_year).one()
            current_value = urgats.biomass_kg_ga

        return current_value

    def __load_sheep_unit_biomass(self):

        sheep_unit_food = None
        if not self.zone_id:
            return
        duration = int(self.calc_duration_sbox.value())
        nz_sheep_food = self.session.query(PsNZSheepFood).filter(PsNZSheepFood.natural_zone == self.zone_id).one()
        sheep_unit_food = nz_sheep_food.current_value

        duration_sheep_unit_food = round((float(sheep_unit_food) * float(duration) / 365), 2)
        return duration_sheep_unit_food

    def __load_live_stock_convert(self):

        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            is_valid = False
            return

        print_year = self.print_year_sbox.value()

        point_detail_id = self.point_detail_id

        convert_sum_value = 0
        convert_value = 0
        converted_count_value = 0
        live_stocks = self.session.query(ClliveStock).all()
        for live_stock in live_stocks:

            live_stock_convert = self.session.query(PsLiveStockConvert). \
                filter(PsLiveStockConvert.live_stock_type == live_stock.code).one()
            convert_value = live_stock_convert.convert_value
            live_stock_value_count = self.session.query(PsPointLiveStockValue). \
                filter(PsPointLiveStockValue.live_stock_type == live_stock.code). \
                filter(PsPointLiveStockValue.value_year == print_year). \
                filter(PsPointLiveStockValue.point_detail_id == point_detail_id).count()
            current_value = 0
            if live_stock_value_count == 1:
                live_stock_value = self.session.query(PsPointLiveStockValue). \
                    filter(PsPointLiveStockValue.live_stock_type == live_stock.code). \
                    filter(PsPointLiveStockValue.value_year == print_year). \
                    filter(PsPointLiveStockValue.point_detail_id == point_detail_id).one()
                current_value = live_stock_value.current_value
                converted_count_value = current_value * convert_value

                convert_sum_value = convert_sum_value + converted_count_value

        return convert_sum_value

    def __calc_validate(self):

        is_valid = True
        selected_items = self.point_detail_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose point detail!!!"))
            is_valid = False
            return
        #
        # if float(self.area_ga_edit.text()) == 0:
        #     PluginUtils.show_message(self, self.tr("Can't"), self.tr("Area zero!!!"))
        #     is_valid = False
        #     return

        if float(self.calc_area_sbox.value()) == 0:
            PluginUtils.show_message(self, self.tr("Can't"), self.tr("Duration zero!!!"))
            is_valid = False
            return

        if not self.calc_area_sbox.value():
            PluginUtils.show_message(self, self.tr("Can't"), self.tr("Duration zero!!!"))
            is_valid = False
            return

        if float(self.calc_duration_sbox.value()) == 0:
            PluginUtils.show_message(self, self.tr("Can't"), self.tr("Duration zero!!!"))
            is_valid = False
            return

        if not self.calc_duration_sbox.value():
            PluginUtils.show_message(self, self.tr("Can't"), self.tr("Duration zero!!!"))
            is_valid = False
            return

        if self.__load_urgats() == 0:
            PluginUtils.show_message(self, self.tr("Can't"), self.tr("Bio mass value zero!!!"))
            is_valid = False
            return

        if not self.__load_rc():
            PluginUtils.show_message(self, self.tr("Can't"), self.tr("Can not calculate RC!!!"))
            is_valid = False
            return
        return is_valid

    def __calc_validate_save(self):

        is_valid = True

        if float(self.calc_area_sbox.value()) == 0:
            is_valid = False
            return

        if float(self.calc_duration_sbox.value()) == 0:
            is_valid = False
            return

        if self.__load_urgats() == 0:
            is_valid = False
            return

        if not self.__load_rc():
            is_valid = False
            return
        return is_valid

    @pyqtSlot()
    def on_calc_load_button_clicked(self):

        monitoring_year = self.print_year_sbox.value()
        daats_value_count = self.session.query(PsPointDaatsValue).filter(
            PsPointDaatsValue.monitoring_year == monitoring_year). \
            filter(PsPointDaatsValue.point_detail_id == self.point_detail_id).count()
        if daats_value_count == 1:
            daats_value = self.session.query(PsPointDaatsValue).filter(
                PsPointDaatsValue.monitoring_year == monitoring_year). \
                filter(PsPointDaatsValue.point_detail_id == self.point_detail_id).one()

            self.calc_area_sbox.setValue(daats_value.area_ga)
            self.calc_biomass_sbox.setValue(daats_value.biomass)
            self.calc_rc_edit.setText(daats_value.rc)
            self.calc_rc_precent_sbox.setValue(daats_value.rc_precent)
            self.calc_duration_sbox.setValue(daats_value.duration)
            self.calc_sheep_unit_sbox.setValue(daats_value.sheep_unit)
            self.calc_sheep_unit_plant_sbox.setValue(daats_value.sheep_unit_plant)
            self.calc_date_edit.setDate(daats_value.register_date)
            # self.biomass_present_edit.setText(str(daats_value.biomass_present))

            self.calc_d1_edit.setText(str(round(daats_value.d1, 2)))
            self.calc_d1_100ga_edit.setText(str(round(daats_value.d1_100ga, 2)))
            self.calc_d2_edit.setText(str(round(daats_value.d2, 2)))
            self.calc_d3_edit.setText(str(round(daats_value.d3, 2)))
            self.calc_unelgee_edit.setText(str(round(daats_value.unelgee, 2)))

    @pyqtSlot()
    def on_calc_refresh_button_clicked(self):

        if not self.__calc_validate():
            return

        area_ga = None
        biomass = None
        rc_code = None
        rc_precent = None
        duration = None
        sheep_unit_plant = None
        sheep_unit = None
        monitoring_Date = None

        area_ga = float(self.area_ga_edit.text())
        biomass = self.__load_urgats()
        rc_id = self.__load_rc().id
        rc_code = self.__load_rc().rc_code
        rc_precent = self.__load_rc().rc_precent
        duration = int(self.duration_days_edit.text())
        sheep_unit_plant = self.__load_sheep_unit_biomass()
        sheep_unit = self.__load_live_stock_convert()
        if area_ga > 0:
            self.calc_area_sbox.setValue(area_ga)
        else:
            area_ga = self.calc_area_sbox.value()
        self.calc_biomass_sbox.setValue(biomass)
        self.calc_rc_edit.setText(rc_code)
        self.calc_rc_precent_sbox.setValue(rc_precent)
        if duration > 0:
            self.calc_duration_sbox.setValue(duration)
        else:
            duration = self.calc_duration_sbox.value()
        self.calc_sheep_unit_sbox.setValue(sheep_unit)
        self.calc_sheep_unit_plant_sbox.setValue(sheep_unit_plant)

        rc_precent = float(rc_precent) / 100
        biomass_present = float(biomass) * rc_precent
        d1 = (float(biomass) / float(sheep_unit_plant)) * (rc_precent)
        d1_100ga = d1 * 100
        d2 = ((1 / d1))
        d3 = float(area_ga * biomass_present) / float(sheep_unit_plant)
        unelgee = d3 - float(sheep_unit)

        self.biomass_present_edit.setText(str(biomass_present))

        self.calc_d1_edit.setText(str(round(d1, 2)))
        self.calc_d1_100ga_edit.setText(str(round(d1_100ga, 2)))
        self.calc_d2_edit.setText(str(round(d2, 2)))
        self.calc_d3_edit.setText(str(round(d3, 2)))
        self.calc_unelgee_edit.setText(str(round(unelgee, 2)))

    def __daats_value_save(self):

        if not self.__calc_validate_save():
            return

        area_ga = float(self.calc_area_sbox.value())
        biomass = self.__load_urgats()
        rc_id = self.__load_rc().id
        rc_code = self.__load_rc().rc_code
        rc_precent = self.__load_rc().rc_precent
        duration = int(self.calc_duration_sbox.value())
        sheep_unit_plant = self.__load_sheep_unit_biomass()
        sheep_unit = self.__load_live_stock_convert()
        rc_precent_d = rc_precent

        rc_precent = float(rc_precent) / 100
        biomass_present = float(biomass) * rc_precent
        d1 = (float(biomass) / float(sheep_unit_plant)) * (rc_precent)
        d1_100ga = d1 * 100
        d2 = ((1 / d1))
        d3 = float(area_ga * biomass_present) / float(sheep_unit_plant)
        unelgee = d3 - float(sheep_unit)

        self.calc_d1_edit.setText(str(round(d1, 2)))
        self.calc_d1_100ga_edit.setText(str(round(d1_100ga, 2)))
        self.calc_d2_edit.setText(str(round(d2, 2)))
        self.calc_d3_edit.setText(str(round(d3, 2)))
        self.calc_unelgee_edit.setText(str(round(unelgee, 2)))

        monitoring_date_qt = PluginUtils.convert_qt_date_to_python(self.calc_date_edit.date())

        begin_month_text = self.begin_month_date.text()
        end_month_text = self.end_month_date.text()

        daats_count = self.session.query(PsPointDaatsValue). \
            filter(PsPointDaatsValue.point_detail_id == self.point_detail_id). \
            filter(PsPointDaatsValue.monitoring_year == self.print_year_sbox.value()).count()
        print daats_count
        if daats_count == 0:
            daats = PsPointDaatsValue()
            daats.point_detail_id = self.point_detail_id
            daats.monitoring_year = self.print_year_sbox.value()
            daats.register_date = monitoring_date_qt
            daats.area_ga = area_ga
            daats.duration = duration
            daats.rc = rc_code
            daats.rc_precent = rc_precent_d
            daats.sheep_unit = sheep_unit
            daats.sheep_unit_plant = sheep_unit_plant
            daats.biomass = biomass
            daats.d1 = d1
            daats.d1_100ga = d1_100ga
            daats.d2 = d2
            daats.d3 = d3
            daats.unelgee = unelgee
            daats.rc_id = rc_id
            daats.begin_month = begin_month_text
            daats.end_month = end_month_text

            self.session.add(daats)
        elif daats_count == 1:
            daats = self.session.query(PsPointDaatsValue). \
                filter(PsPointDaatsValue.point_detail_id == self.point_detail_id). \
                filter(PsPointDaatsValue.monitoring_year == self.print_year_sbox.value()).one()
            print monitoring_date_qt
            daats.register_date = monitoring_date_qt
            daats.area_ga = area_ga
            daats.duration = duration
            daats.rc = rc_code
            daats.rc_precent = rc_precent_d
            daats.sheep_unit = sheep_unit
            daats.sheep_unit_plant = sheep_unit_plant
            daats.biomass = biomass
            daats.d1 = d1
            daats.d1_100ga = d1_100ga
            daats.d2 = d2
            daats.d3 = d3
            daats.unelgee = unelgee
            daats.rc_id = rc_id
            daats.begin_month = begin_month_text
            daats.end_month = end_month_text

    def __photo_count(self, point_detail_id):

        file_path = PasturePath.pasture_photo_file_path()
        point_year = str(self.print_year_sbox.value())
        file_path = file_path + '/' + point_year + '/' + point_detail_id + '/image'
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        count = 0
        for file in os.listdir(file_path):
            count = count + 1

        return count

    def __load_year(self):

        year = u'Мониторинг хийсэн жил : ' + str(self.print_year_sbox.value())
        return year

    def __check_null(self, type, format, format_null_data):
        if type > '':
            return format
        else:
            return format_null_data



