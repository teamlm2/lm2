__author__ = 'B.Ankhbold'
# -*- encoding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import *
from qgis.core import *
from qgis.gui import *
# from QgsMapToolIdentify import *
from ..model import SettingsConstants
from ..utils.LayerUtils import LayerUtils
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.PluginUtils import PluginUtils
from ..utils.SessionHandler import SessionHandler
from .PrintPointDialog import PrintPointDialog
from .PrintDialog import PrintDialog
from ..model.CaBuilding import *

import math
import locale
import os

class PrintPointExtractMapTool(QgsMapTool):

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

    def activate(self):

        self.__add_layers()

    def canvasDoubleClickEvent(self, event):

        self.double_click = True

    def canvasReleaseEvent(self, event):

        if self.double_click:
            self.double_click = False
            return

        # we are interested only in left button clicking
        if event.button() != Qt.LeftButton:
            return
        layer = LayerUtils.layer_by_data_source("pasture", 'ca_pasture_monitoring')

        features = QgsMapToolIdentify(self.plugin.iface.mapCanvas()).identify(event.x(), event.y(), [layer],
                                                            QgsMapToolIdentify.TopDownStopAtFirst)
        self.__remove_features()
        if len(features) > 0:
            # here you get the selected feature
            feature = features[0].mFeature
            # And here you get the attribute's value
            point_id = feature['point_id']
            if not self.__is_active_boundary_points():
                return
            self.__draw_features(feature.geometry(), point_id)
            if self.current_dialog is not None:
                self.dialog_position = self.current_dialog.pos()
            else:
                self.current_dialog = PrintPointDialog(self.plugin, point_id, self.plugin.iface.mainWindow())
                self.current_dialog.setModal(False)
                self.connect(self.current_dialog, SIGNAL("rejected()"), self.__clean_up)

            if self.current_dialog.isHidden():
                self.current_dialog.show()
                if self.dialog_position is not None:
                    self.current_dialog.move(self.dialog_position)
        else:
            if self.current_dialog is not None:
                self.current_dialog.hide()
                self.dialog_position = self.current_dialog.pos()

    def deactivate(self):

        self.plugin.iface.mainWindow().statusBar().showMessage("")
        self.double_click = False
        self.plugin.activeAction = None
        if self.current_dialog is not None:
            self.current_dialog.reject()

        registry = QgsMapLayerRegistry.instance()
        if self.__is_active_boundary_points():
            registry.removeMapLayer(self.__boundaryPointsLayer.id())

    def __clean_up(self):

        self.current_dialog = None
        self.dialog_position = None
        self.__remove_features()

    def __add_boundary_points_layer(self):

        soum = DatabaseUtils.working_l2_code()
        layer = LayerUtils.layer_by_data_source("pasture", 'ca_pasture_monitoring')
        crs = layer.crs()

        boundary_points_layer = QgsVectorLayer("Point?crs=" + str(crs.authid()), "boundary_points", "memory")
        # add fields
        boundary_points_layer.startEditing()
        boundary_points_layer.addAttribute(QgsField("label", QVariant.Int))
        boundary_points_layer.commitChanges()
        boundary_points_layer.setReadOnly(True)

        renderer_v2 = boundary_points_layer.rendererV2()
        symbol = renderer_v2.symbol()
        symbol.setColor(QColor(Qt.white))
        symbol.setSize(3)

        boundary_points_layer.enableLabels(True)
        label = boundary_points_layer.label()
        label.setLabelField(QgsLabel.Text, 0)
        label_attributes = label.labelAttributes()
        label_attributes.setOffset(10, 10, 1)
        label_attributes.setSize(8, 1)

        self.__add_map_layer(boundary_points_layer)
        self.__boundaryPointsLayer = boundary_points_layer

    def __draw_boundary_points(self, geometry, point_id):

        boundary_points_layer = self.__boundaryPointsLayer
        boundary_points_layer.startEditing()
        # add a feature
        feature = QgsFeature()
        feature.setGeometry(geometry)
        feature.initAttributes(1)
        feature.setAttribute(0, str(point_id))
        boundary_points_layer.dataProvider().addFeatures([feature])

        boundary_points_layer.commitChanges()

    def __add_layers(self):

        #those layers must be in WGS84 because it could be that the user didn't enable the on the fly transformaton
        self.__add_boundary_points_layer()

    def __draw_features(self, geometry, point_id):

        self.__draw_boundary_points(geometry, point_id)

        self.plugin.iface.mapCanvas().refresh()

    def __add_map_layer(self, map_layer):

        QgsMapLayerRegistry.instance().addMapLayer(map_layer,  False)

        root = QgsProject.instance().layerTreeRoot()
        mygroup = root.findGroup("PUG")
        mygroup.insertLayer(0, map_layer)

    def __is_active_boundary_points(self):

        layers = self.plugin.iface.legendInterface().layers()
        is_layer_active = False
        for layer in layers:
            if layer.name() == "boundary_points":
                is_layer_active = True
        return is_layer_active

    def __remove_features(self):

        if self.__is_active_boundary_points():
            self.__delete_features(self.__boundaryPointsLayer)

        self.plugin.iface.mapCanvas().refresh()

    def __delete_features(self, vector_layer):

        if vector_layer is None:
            return

        vector_layer.startEditing()

        ids = list()
        vector_layer.selectAll()

        for feature in vector_layer.getFeatures():
            ids.append(feature.id())

        vector_layer.dataProvider().deleteFeatures(ids)
        vector_layer.commitChanges()



    @pyqtSlot()
    def on_help_button_clicked(self):

        os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/print_cadastral_map.htm")