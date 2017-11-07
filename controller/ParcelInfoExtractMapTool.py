import os

__author__ = 'anna'
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import *
from qgis.core import *
from qgis.gui import *
from ..model import SettingsConstants
from ..utils.LayerUtils import LayerUtils
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.PluginUtils import PluginUtils
from ..utils.SessionHandler import SessionHandler
from .ParcelInfoDialog import ParcelInfoDialog
from ..model.CaBuilding import *

import math
import locale

class ParcelInfoExtractMapTool(QgsMapTool):

    def __init__(self, plugin):
        """The constructor.
        Initializes the map tool.

        @param canvas map canvas
        @param dockWidget pointer to the main widget (OSM Feature widget) of OSM Plugin
        @param dbManager pointer to instance of OsmDatabaseManager for communication with sqlite3 database
        """

        QgsMapTool.__init__(self, plugin.iface.mapCanvas())

        self.plugin = plugin
        self.double_click = False

        self.plugin.iface.mainWindow().statusBar().showMessage(self.tr("Click on a parcel!"))

        self.current_dialog = None
        self.dialog_position = None
        self.area = 0
    # def activate(self):
    #
    #     self.__add_layers()

    def canvasDoubleClickEvent(self, event):

        self.double_click = True

    def canvasReleaseEvent(self, event):
        """This function is called after mouse button is released on map when using this map tool.

        It finds out all features that are currently at place where releasing was done.

        OSM Plugin then marks the first of them. User can repeat right-clicking to mark
        the next one, the next one, the next one... periodically...
        Note that only one feature is marked at a time.

        Each marked feature is also loaded into OSM Feature widget.

        @param event event that occured when button releasing
        """
        if self.double_click:
            self.double_click = False
            return

        # we are interested only in left button clicking
        if event.button() != Qt.LeftButton:
            return
        soum = DatabaseUtils.working_l2_code()
        layer = LayerUtils.layer_by_data_source("s" + soum, 'ca_ub_parcel')
        result_feature = None

        if layer is None:
            result = None
        else:
            # find out map coordinates from mouse click
            map_point = self.toMapCoordinates(event.pos())
            tolerance = self.searchRadiusMU(self.plugin.iface.mapCanvas())
            self.area = QgsRectangle(map_point.x() - tolerance, map_point.y() - tolerance, map_point.x() + tolerance, map_point.y() + tolerance)
            area = self.area

            feature_request = QgsFeatureRequest()
            layerRect = self.toLayerCoordinates(layer, area)
            feature_request.setFilterRect(layerRect)
            feature_request.setFlags(QgsFeatureRequest.ExactIntersect)

            idx_parcel_id = layer.dataProvider().fieldNameIndex("old_parcel_id")

            for feature in layer.getFeatures(feature_request):
                result_feature = feature

        if result_feature is not None:

            attribute_map = result_feature.attributes()

            parcel_no = attribute_map[idx_parcel_id]

            self.__select_feature(parcel_no, layer)

            self.plugin.parcelInfoWidget.set_parcel_data(parcel_no, result_feature)

    # def deactivate(self):
    #
    #     self.plugin.iface.mainWindow().statusBar().showMessage("")
    #     self.double_click = False
        # self.plugin.activeAction.setChecked(False)
        # self.plugin.activeAction = None

    def __clean_up(self):

        self.current_dialog = None
        self.dialog_position = None

    def __select_feature(self, parcel_id, layer):

        expression = " old_parcel_id = \'" + parcel_id + "\'"
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
