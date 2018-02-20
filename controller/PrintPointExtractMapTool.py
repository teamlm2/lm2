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

        print "asdasaaa"

    def activate(self):

        self.__add_layers()

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
        layer = LayerUtils.layer_by_data_source("pasture", 'ca_pasture_monitoring')
        result_feature = None

        features = QgsMapToolIdentify(self.plugin.iface.mapCanvas()).identify(event.x(), event.y(), [layer],
                                                            QgsMapToolIdentify.TopDownStopAtFirst)
        print len(features)
        if len(features) > 0:
            # here you get the selected feature
            feature = features[0].mFeature
            # And here you get the attribute's value
            point_id = feature['point_id']
            print point_id
            self.current_dialog = PrintPointDialog(self.plugin, point_id, self.plugin.iface.mainWindow())
            self.current_dialog.show()

            # if self.current_dialog is not None:
            #     self.dialog_position = self.current_dialog.pos()
            #     # self.current_dialog.set_parcel_data(parcel_no, result_feature)
            # else:
            #     self.current_dialog = PrintPointDialog(self.plugin, self.plugin.iface.mainWindow())
            #     self.current_dialog.setModal(False)
            #     self.connect(self.current_dialog, SIGNAL("rejected()"), self.__clean_up)
            #     # self.current_dialog.set_parcel_data(parcel_no, result_feature)
            #
            # if self.current_dialog.isHidden():
            #     self.current_dialog.show()
            #     if self.dialog_position is not None:
            #         self.current_dialog.move(self.dialog_position)
        else:
            if self.current_dialog is not None:
                self.current_dialog.hide()
                self.dialog_position = self.current_dialog.pos()

    def deactivate(self):

        self.plugin.iface.mainWindow().statusBar().showMessage("")
        self.double_click = False
        # if self.plugin.activeAction:
        #     self.plugin.activeAction.setChecked(False)
        self.plugin.activeAction = None
        if self.current_dialog is not None:
            self.current_dialog.reject()

        registry = QgsMapLayerRegistry.instance()
        if self.__is_active_boundary_lines():
            registry.removeMapLayer(self.__boundaryLinesLayer.id())
        if self.__is_active_boundary_outline():
            registry.removeMapLayer(self.__boundaryOutlineLayer.id())
        if self.__is_active_boundary_points():
            registry.removeMapLayer(self.__boundaryPointsLayer.id())
        if self.__is_active_boundary_polygon():
            registry.removeMapLayer(self.__boundaryPolygonLayer.id())
        if self.__is_active_building_polygon():
            registry.removeMapLayer(self.__buildingPolygonLayer.id())
        if self.__is_active_building_points():
            registry.removeMapLayer(self.__buildingPointsLayer.id())
        if self.__is_active_building_lines():
            registry.removeMapLayer(self.__buildingLinesLayer.id())

    def __clean_up(self):

        self.current_dialog = None
        self.dialog_position = None
        self.__remove_features()

    def __add_boundary_points_layer(self):

        soum = DatabaseUtils.working_l2_code()
        layer = LayerUtils.layer_by_data_source("s" + soum, 'ca_parcel')
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

    def __add_building_points_layer(self):

        soum = DatabaseUtils.working_l2_code()
        layer = LayerUtils.layer_by_data_source("s" + soum, 'ca_parcel')
        crs = layer.crs()

        boundary_points_layer = QgsVectorLayer("Point?crs=" + str(crs.authid()), "building_points", "memory")
        # add fields
        boundary_points_layer.startEditing()
        boundary_points_layer.addAttribute(QgsField("label", QVariant.String))
        boundary_points_layer.commitChanges()
        boundary_points_layer.setReadOnly(True)

        renderer_v2 = boundary_points_layer.rendererV2()
        symbol = renderer_v2.symbol()
        symbol.setColor(QColor(Qt.white))
        symbol.setSize(1)

        boundary_points_layer.enableLabels(True)
        label = boundary_points_layer.label()
        label.setLabelField( QgsLabel.Text, 0)
        label_attributes = label.labelAttributes()
        label_attributes.setOffset(10, 10, 1)
        label_attributes.setSize(8, 1)

        self.__add_map_layer(boundary_points_layer)
        self.__buildingPointsLayer = boundary_points_layer


    def __add_building_lines_layer(self):

        soum = DatabaseUtils.working_l2_code()
        layer = LayerUtils.layer_by_data_source("s" + soum, 'ca_building')
        crs = layer.crs()

        building_lines_layer = QgsVectorLayer("LineString?crs=" + str(crs.authid()), "building_lines", "memory")
        building_lines_layer.setCrs(crs)
        # add fields
        building_lines_layer.startEditing()
        building_lines_layer.addAttribute(QgsField("label", QVariant.String))
        building_lines_layer.addAttribute(QgsField("angle", QVariant.Double))

        building_lines_layer.commitChanges()
        building_lines_layer.setReadOnly(True)

        renderer_v2 = building_lines_layer.rendererV2()
        symbol = renderer_v2.symbol()
        symbol.setColor(QColor(Qt.black))
        symbol.setWidth(1)

        self.__add_map_layer(building_lines_layer)

        self.__buildingLinesLayer = building_lines_layer

    def __add_boundary_lines_layer(self):

        soum = DatabaseUtils.working_l2_code()
        layer = LayerUtils.layer_by_data_source("s" + soum, 'ca_parcel')
        crs = layer.crs()

        boundary_lines_layer = QgsVectorLayer("LineString?crs=" + str(crs.authid()), "boundary_lines", "memory")
        boundary_lines_layer.setCrs(crs)
        # add fields
        boundary_lines_layer.startEditing()
        boundary_lines_layer.addAttribute(QgsField("label", QVariant.String))
        boundary_lines_layer.addAttribute(QgsField("angle", QVariant.Double))

        boundary_lines_layer.commitChanges()
        boundary_lines_layer.setReadOnly(True)

        renderer_v2 = boundary_lines_layer.rendererV2()
        symbol = renderer_v2.symbol()
        symbol.setColor(QColor(Qt.black))
        symbol.setWidth(1)

        boundary_lines_layer.enableLabels(True)
        label = boundary_lines_layer.label()
        label.setLabelField(QgsLabel.Text, 0)
        label.setLabelField(QgsLabel.Angle, 1)
        label_attributes = label.labelAttributes()
        label_attributes.setAlignment(4)
        label_attributes.setOffset(0, 6, 1)
        label_attributes.setColor(QColor(0, 0, 0))
        label_attributes.setSize(8, 1)

        self.__add_map_layer(boundary_lines_layer)

        self.__boundaryLinesLayer = boundary_lines_layer

    def __draw_boundary_lines(self, geometry):

        boundary_lines_layer = self.__boundaryLinesLayer
        boundary_lines_layer.startEditing()

        d = QgsDistanceArea()
        proj4 = PluginUtils.utm_proj4def_from_point(geometry.centroid().asPoint())
        crs = QgsCoordinateReferenceSystem()
        crs.createFromProj4(proj4)

        d.setSourceCrs(crs.postgisSrid())
        d.setEllipsoid(crs.ellipsoidAcronym())
        d.setEllipsoidalMode(True)

        # add a feature
        for polyline in geometry.asPolygon():
            for i in range(0, len(polyline)-1):
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPolyline([polyline[i], polyline[i+1]]))
                distance = d.measureLine(polyline[i], polyline[i+1])
                angle = d.bearing(polyline[i], polyline[i+1])
                angle = angle * 180 / math.pi
                if angle < 0:
                    angle = math.fabs(angle) + 90
                else:
                    angle = 90 - angle

                if angle > 90 and angle < 270:
                    angle = angle + 180
                elif angle < -90 and angle > -270:
                    angle = angle + 180

                feature.initAttributes(2)
                formatted_distance = locale.format('%.2f', round(float(distance), 2), True)
                feature.setAttribute(0, "{0}".format(str(formatted_distance)))
                feature.setAttribute(1, angle)
                boundary_lines_layer.dataProvider().addFeatures([feature])

        boundary_lines_layer.commitChanges()

    def __draw_building_lines(self, building_geometry):

        building_lines_layer = self.__buildingLinesLayer
        building_lines_layer.startEditing()

        d = QgsDistanceArea()
        proj4 = PluginUtils.utm_proj4def_from_point(building_geometry.centroid().asPoint())
        crs = QgsCoordinateReferenceSystem()
        crs.createFromProj4(proj4)

        d.setSourceCrs(crs.postgisSrid())
        d.setEllipsoid(crs.ellipsoidAcronym())
        d.setEllipsoidalMode(True)

        # add a feature
        for polyline in building_geometry.asPolygon():
            for i in range(0, len(polyline)-1):
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPolyline([polyline[i], polyline[i+1]]))
                distance = d.measureLine(polyline[i], polyline[i+1])
                angle = d.bearing(polyline[i], polyline[i+1])
                angle = angle * 180 / math.pi
                if angle < 0:
                    angle = math.fabs(angle) + 90
                else:
                    angle = 90 - angle

                if angle > 90 and angle < 270:
                    angle = angle + 180
                elif angle < -90 and angle > -270:
                    angle = angle + 180

                feature.initAttributes(2)
                formatted_distance = locale.format('%.2f', round(float(distance), 2), True)
                feature.setAttribute(0, "{0}".format(str(formatted_distance)))
                feature.setAttribute(1, angle)
                building_lines_layer.dataProvider().addFeatures([feature])

        building_lines_layer.commitChanges()

    def __add_layers(self):

        #those layers must be in WGS84 because it could be that the user didn't enable the on the fly transformaton
        self.__add_boundary_outline_layer()
        self.__add_boundary_lines_layer()
        self.__add_building_lines_layer()
        self.__add_boundary_polygon_layer()
        self.__add_building_polygon_layer()
        self.__add_boundary_points_layer()
        self.__add_building_points_layer()


    def __draw_features(self, geometry, oldParcelNo):

        self.__draw_boundary_outline(geometry)
        self.__draw_boundary_polygon(geometry, oldParcelNo)
        self.__draw_boundary_lines(geometry)
        self.__draw_boundary_points(geometry)
        self.__draw_building_points(geometry)

        self.plugin.iface.mapCanvas().refresh()

    def __add_boundary_outline_layer(self):

        soum = DatabaseUtils.working_l2_code()
        layer = LayerUtils.layer_by_data_source("s" + soum, 'ca_parcel')
        crs = layer.crs()

        boundary_outline_layer = QgsVectorLayer("LineString?crs=" + str(crs.authid()), "boundary_outline", "memory")
        boundary_outline_layer.setCrs(crs)
        boundary_outline_layer.setReadOnly(True)

        renderer_v2 = boundary_outline_layer.rendererV2()
        symbol = renderer_v2.symbol()
        symbol.setColor(QColor(Qt.red))
        symbol.setWidth(1)

        self.__add_map_layer(boundary_outline_layer)

        self.__boundaryOutlineLayer = boundary_outline_layer

    def __draw_boundary_outline(self, geometry):

        boundary_outline_layer = self.__boundaryOutlineLayer
        boundary_outline_layer.startEditing()

        # add a feature
        for polyline in geometry.asPolygon():
            for i in range(0, len(polyline)-1):
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPolyline([polyline[i], polyline[i+1]]))
                boundary_outline_layer.dataProvider().addFeatures([feature])

        boundary_outline_layer.commitChanges()

    def __add_building_polygon_layer(self):

        soum = DatabaseUtils.working_l2_code()
        layer = LayerUtils.layer_by_data_source("s" + soum, 'ca_building')
        crs = layer.crs()

        building_polygon_layer = QgsVectorLayer("MultiPolygon?crs=" + str(crs.authid()), "building_polygon", "memory")
        building_polygon_layer.setCrs(crs)

        # add fields
        building_polygon_layer.startEditing()
        building_polygon_layer.addAttribute(QgsField("label", QVariant.String))
        building_polygon_layer.commitChanges()
        building_polygon_layer.setReadOnly(True)

        renderer_v2 = building_polygon_layer.rendererV2()

        symbol = renderer_v2.symbol()
        symbol.setAlpha(0)
        symbol_layer = symbol.symbolLayer(0)
        symbol_layer.setColor(QColor(Qt.white))

        building_polygon_layer.enableLabels(True)
        label = building_polygon_layer.label()
        label.setLabelField(QgsLabel.Text, 0)
        label_attributes = label.labelAttributes()
        label_attributes.setSize(22, 1)

        self.__add_map_layer(building_polygon_layer)

        self.__buildingPolygonLayer = building_polygon_layer

    def __draw_building_polygon(self, geometry, building_no):

        building_polygon_layer = self.__buildingPolygonLayer
        building_polygon_layer.startEditing()

        feature = QgsFeature()
        if geometry.isMultipart():
            geometry_converted = QgsGeometry().fromMultiPolygon(geometry.asMultiPolygon())
        else:
            geometry_converted = QgsGeometry().fromPolygon(geometry.asPolygon())

        feature.setGeometry(geometry_converted)
        feature.initAttributes(1)
        feature.setAttribute(0, building_no)
        building_polygon_layer.dataProvider().addFeatures([feature])

        building_polygon_layer.commitChanges()

    def __add_boundary_polygon_layer(self):

        soum = DatabaseUtils.working_l2_code()
        layer = LayerUtils.layer_by_data_source("s" + soum, 'ca_parcel')
        crs = layer.crs()

        boundary_polygon_layer = QgsVectorLayer("MultiPolygon?crs=" + str(crs.authid()), "boundary_polygon", "memory")
        boundary_polygon_layer.setCrs(crs)

        # add fields
        boundary_polygon_layer.startEditing()
        boundary_polygon_layer.addAttribute(QgsField("label", QVariant.String))
        boundary_polygon_layer.commitChanges()
        boundary_polygon_layer.setReadOnly(True)

        renderer_v2 = boundary_polygon_layer.rendererV2()

        symbol = renderer_v2.symbol()
        symbol.setAlpha(0)
        symbol_layer = symbol.symbolLayer(0)
        symbol_layer.setColor(QColor(Qt.white))

        boundary_polygon_layer.enableLabels(True)
        label = boundary_polygon_layer.label()
        label.setLabelField(QgsLabel.Text, 0)
        label_attributes = label.labelAttributes()
        label_attributes.setSize(24, 1)

        self.__add_map_layer(boundary_polygon_layer)

        self.__boundaryPolygonLayer = boundary_polygon_layer

    def __draw_boundary_polygon(self, geometry, old_parcel_no):

        boundary_polygon_layer = self.__boundaryPolygonLayer
        boundary_polygon_layer.startEditing()

        feature = QgsFeature()
        if geometry.isMultipart():
            geometry_converted = QgsGeometry().fromMultiPolygon(geometry.asMultiPolygon())
        else:
            geometry_converted = QgsGeometry().fromPolygon(geometry.asPolygon())

        feature.setGeometry(geometry_converted)
        feature.initAttributes(1)
        feature.setAttribute(0, str(old_parcel_no))
        boundary_polygon_layer.dataProvider().addFeatures([feature])

        boundary_polygon_layer.commitChanges()

    def __add_map_layer(self, map_layer):

        QgsMapLayerRegistry.instance().addMapLayer(map_layer,  False)

        root = QgsProject.instance().layerTreeRoot()
        mygroup = root.findGroup(u"Кадастр")
        mygroup.addLayer(map_layer)

    def __is_active_building_points(self):

        layers = self.plugin.iface.legendInterface().layers()
        is_layer_active = False
        for layer in layers:
            if layer.name() == "building_points":
                is_layer_active = True

        return is_layer_active

    def __is_active_boundary_points(self):

        layers = self.plugin.iface.legendInterface().layers()
        is_layer_active = False
        for layer in layers:
            if layer.name() == "boundary_points":
                is_layer_active = True
        return is_layer_active

    def __is_active_boundary_outline(self):

        layers = self.plugin.iface.legendInterface().layers()
        is_layer_active = False
        for layer in layers:
            if layer.name() == "boundary_outline":
                is_layer_active = True
        return is_layer_active

    def __is_active_boundary_lines(self):

        layers = self.plugin.iface.legendInterface().layers()
        is_layer_active = False
        for layer in layers:
            if layer.name() == "boundary_lines":
                is_layer_active = True
        return is_layer_active

    def __is_active_building_lines(self):

        layers = self.plugin.iface.legendInterface().layers()
        is_layer_active = False
        for layer in layers:
            if layer.name() == "building_lines":
                is_layer_active = True
        return is_layer_active

    def __is_active_boundary_polygon(self):

        layers = self.plugin.iface.legendInterface().layers()
        is_layer_active = False
        for layer in layers:
            if layer.name() == "boundary_polygon":
                is_layer_active = True
        return is_layer_active

    def __is_active_building_polygon(self):

        layers = self.plugin.iface.legendInterface().layers()
        is_layer_active = False
        for layer in layers:
            if layer.name() == "building_polygon":
                is_layer_active = True
        return is_layer_active

    def __remove_features(self):

        if self.__is_active_boundary_points():
            self.__delete_features(self.__boundaryPointsLayer)
        if self.__is_active_boundary_lines():
            self.__delete_features(self.__boundaryLinesLayer)
        if self.__is_active_boundary_polygon():
            self.__delete_features(self.__boundaryPolygonLayer)
        if self.__is_active_boundary_outline():
            self.__delete_features(self.__boundaryOutlineLayer)
        if self.__is_active_building_points():
            self.__delete_features(self.__buildingPointsLayer)
        if self.__is_active_building_polygon():
            self.__delete_features(self.__buildingPolygonLayer)
        if self.__is_active_building_lines():
            self.__delete_features(self.__buildingLinesLayer)

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