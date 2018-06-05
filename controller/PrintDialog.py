__author__ = 'anna'
# coding=utf8

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *
from qgis.core import *
from sqlalchemy.exc import SQLAlchemyError
from geoalchemy2.elements import WKTElement
from sqlalchemy import func, or_, and_, desc
from ..view.Ui_PrintDialog import Ui_PrintDialog
from ..utils.PluginUtils import PluginUtils
from ..utils.LayerUtils import LayerUtils
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.SessionHandler import SessionHandler
from ..utils.FileUtils import FileUtils
from ..model.CaBuilding import *
from ..model.CtApplication import *
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.AuLevel3 import *
from ..model import SettingsConstants
from ..model import Constants
from ..model.SetRightTypeApplicationType import *
from ..model.LM2Exception import LM2Exception
from ..model.ClPositionType import *
from ..model.CtCadastrePage import *
from ..model.Enumerations import ApplicationType, UserRight
from ..model.SetCadastrePage import *
import math
import locale
import os

class PrintDialog(QDialog, Ui_PrintDialog):

    CODEIDCARD, FAMILYNAME, MIDDLENAME, FIRSTNAME, DATEOFBIRTH, CONTRACTNO, CONTRACTDATE = range(7)

    STREET_NAME = 7
    KHASHAA_NAME = 6
    GEO_ID = 2
    OLD_PARCEL_ID = 1

    def __init__(self, plugin, crs_description, parent=None):

        super(PrintDialog,  self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.plugin = plugin
        self.crs_description = crs_description
        self.session = SessionHandler().session_instance()

        self.__parcel_no = None
        self.__building_id_list = None
        self.__geometry = None
        self.__building_area = None
        self.__building_hayag_no = None
        self.__feature = None
        self.__overview_map_scale = None
        self.__coord_transform = None
        self.__second_page_enabled = False
        self.setupUi(self)

        self.dpi_edit.setValidator(QIntValidator(150, 1200, self.dpi_edit))
        self.buffer_edit.setValidator(QIntValidator(1, 500, self.buffer_edit))
        self.grid_distance_edit.setValidator(QIntValidator(10, 1000, self.grid_distance_edit))
        self.grid_offset_x_edit.setValidator(QIntValidator(0, 50, self.grid_offset_x_edit))
        self.grid_offset_y_edit.setValidator(QIntValidator(0, 50, self.grid_offset_y_edit))

        self.__setup_table_widget()

        self.__load_settings()

    def __setup_table_widget(self):

        self.right_holder_twidget.setAlternatingRowColors(True)
        self.right_holder_twidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.right_holder_twidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.right_holder_twidget.setSelectionMode(QTableWidget.SingleSelection)

    def __update_ui(self):

        self.setWindowTitle(self.tr('Print map for parcel: <{0}>. Select the right holder.'.format(self.__parcel_no)))
        self.right_holder_twidget.clearContents()
        # self.session = SessionHandler().session_instance()
        ct_applications = self.session.query(CtApplication).filter(CtApplication.parcel == self.__parcel_no).all()

        for application in ct_applications:

            for contract_role in application.contracts:

                if contract_role.role == Constants.APPLICATION_ROLE_CREATES:

                    contract = contract_role.contract_ref
                    # if contract.cancellation_date is None:
                    for stakeholder in application.stakeholders:
                        person = stakeholder.person_ref

                        if stakeholder.role == Constants.APPLICANT_ROLE_CODE or stakeholder.role == Constants.REMAINING_OWNER_CODE or stakeholder.role == Constants.NEW_RIGHT_HOLDER_CODE:
                            # self.__add_contract_person(1,contract.status, contract.contract_no, contract.contract_date, application, person)
                                if application.app_type == 2:
                                   if stakeholder.role == Constants.REMAINING_OWNER_CODE:
                                        person = stakeholder.person_ref
                                        self.__add_contract_person(1, contract.status, contract.contract_no,
                                                                   contract.contract_date, application, person)
                                elif (application.app_type == 7 or application.app_type == 14 or application.app_type == 15):
                                    if stakeholder.role == Constants.NEW_RIGHT_HOLDER_CODE:
                                        person = stakeholder.person_ref
                                        self.__add_contract_person(1, contract.status, contract.contract_no,
                                                                   contract.contract_date, application, person)
                                else:
                                    person = stakeholder.person_ref
                                    self.__add_contract_person(1, contract.status, contract.contract_no,
                                                               contract.contract_date, application, person)

            for record_role in application.records:
                if record_role.role == Constants.APPLICATION_ROLE_CREATES:
                    record = record_role.record_ref
                    # if record.cancellation_date is None:
                    # if record.status == 20:
                    for stakeholder in application.stakeholders:
                        if stakeholder.role == Constants.APPLICANT_ROLE_CODE or stakeholder.role == Constants.NEW_RIGHT_HOLDER_CODE or stakeholder.role == Constants.REMAINING_OWNER_CODE:
                            person = stakeholder.person_ref

                            if application.app_type == ApplicationType.change_ownership or application.app_type == ApplicationType.giving_up_ownership:
                                if stakeholder.role == 40 or stakeholder.role == 70:
                                    self.__add_contract_person(0, record.status, record.record_no,
                                                               record.record_date, application, person)
                            else:
                                self.__add_contract_person(0,record.status, record.record_no, record.record_date, application, person)

        self.right_holder_twidget.resizeColumnsToContents()

        if self.right_holder_twidget.rowCount() > 0:
            self.right_holder_twidget.selectRow(0)

    def __add_contract_person(self, is_record, status, number, date, application, person):

        count = self.right_holder_twidget.rowCount()
        self.right_holder_twidget.insertRow(count)
        right_type = self.__right_type_description(application.app_type, person.type)
        is_active = False
        color = Qt.green
        if is_record == 1:
            if status == 10:
                color = Qt.yellow
            elif status == 20:
                color = Qt.green
            elif status == 30:
                color = Qt.red
            elif status == 40:
                color = Qt.red
        elif is_record == 0:
            if status == 10:
                color = Qt.yellow
            elif status == 20:
                color = Qt.green
            elif status == 30:
                color = Qt.red

        item = QTableWidgetItem(unicode(person.person_id))
        item.setData(Qt.UserRole, application.app_no)
        item.setData(Qt.UserRole + 1, person.person_id)
        item.setBackground(color)
        self.right_holder_twidget.setItem(count, self.CODEIDCARD, item)

        item = QTableWidgetItem(unicode(person.name))
        item.setData(Qt.UserRole, application.app_no)
        item.setData(Qt.UserRole + 1, person.type)
        item.setBackground(color)
        self.right_holder_twidget.setItem(count, self.FAMILYNAME, item)

        if person.type == 30 or person.type == 40 or person.type == 60:
            item = QTableWidgetItem(unicode(person.contact_surname))
            item.setData(Qt.UserRole, application.app_no)

            item.setData(Qt.UserRole + 1, person.person_id)
            item.setBackground(color)
            self.right_holder_twidget.setItem(count, self.MIDDLENAME, item)

            item = QTableWidgetItem(unicode(person.contact_first_name))
            item.setData(Qt.UserRole, right_type)
            item.setData(Qt.UserRole + 1, person.person_id)
            item.setBackground(color)
            self.right_holder_twidget.setItem(count, self.FIRSTNAME, item)
        else:
            item = QTableWidgetItem(unicode(person.middle_name))
            item.setData(Qt.UserRole, application.app_no)
            item.setData(Qt.UserRole + 1, person.person_id)
            item.setBackground(color)
            self.right_holder_twidget.setItem(count, self.MIDDLENAME, item)

            item = QTableWidgetItem(unicode(person.first_name))
            item.setData(Qt.UserRole, right_type)
            item.setData(Qt.UserRole + 1, person.person_id)
            item.setBackground(color)
            self.right_holder_twidget.setItem(count, self.FIRSTNAME, item)

            qt_date = PluginUtils.convert_python_date_to_qt(person.date_of_birth)
            if qt_date is not None:
                item = QTableWidgetItem(qt_date.toString(Constants.DATABASE_DATE_FORMAT))
                item.setBackground(color)
                self.right_holder_twidget.setItem(count, self.DATEOFBIRTH, item)

        item = QTableWidgetItem(unicode(number))
        item.setBackground(color)
        self.right_holder_twidget.setItem(count, self.CONTRACTNO, item)
        if date is not None:
            qt_date = PluginUtils.convert_python_date_to_qt(date)
            item = QTableWidgetItem(qt_date.toString(Constants.DATABASE_DATE_FORMAT))
            item.setBackground(color)
            self.right_holder_twidget.setItem(count, self.CONTRACTDATE, item)

    def set_parcel_data(self, parcel_no, feature):

        self.__parcel_no = parcel_no
        self.__geometry = QgsGeometry(feature.geometry())
        self.__feature = feature
        self.__update_ui()
        self.__setup_coord_transform()

    def set_building_data(self, building_id_list):

        self.__building_id_list = building_id_list

    @pyqtSlot()
    def on_close_button_clicked(self):

        self.reject()

    @pyqtSlot()
    def on_print_button_clicked(self):

        file_path = self.file_name_edit.text()

        if file_path is None or type(file_path) == QPyNullVariant or file_path == "":
            PluginUtils.show_error(self, self.tr("No file name set"), self.tr("Select a file name to save the map to!"))
            return

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        map_canvas = self.plugin.iface.mapCanvas()
        original_trafo = map_canvas.hasCrsTransformEnabled()
        original_crs = map_canvas.mapRenderer().destinationCrs()
        original_extent = map_canvas.extent()

        map_canvas.setDestinationCrs(self.__coord_transform.destCRS())
        map_canvas.setCrsTransformEnabled(True)

        path = FileUtils.map_file_path()

        point_layer = LayerUtils.layer_by_name('boundary_points')
        building_point_layer = LayerUtils.layer_by_name('building_points')


        if point_layer is None:
            return
        boundary_points_count = point_layer.featureCount()
        building_points_count = building_point_layer.featureCount()

        if boundary_points_count > 7 or building_points_count > 8:
            template = path + "cadastre_extract_extented.qpt"
            self.__second_page_enabled = True
        else:
            template = path + "cadastre_extract.qpt"

        templateDOM = QDomDocument()
        templateDOM.setContent(QFile(template), False)

        map_composition = QgsComposition(map_canvas.mapRenderer())
        map_composition.loadFromTemplate(templateDOM)

        composer_map = map_composition.getComposerMapById(0)

        if composer_map is None:
            PluginUtils.show_error(self, self.tr("No file name set"), self.tr("Error in template file - unable to load!"))
            return
        scale_denominator = self.__adjust_map_center_and_scale(composer_map, 200, 150)

        composer_map.storeCurrentLayerSet()
        composer_map.setKeepLayerSet(True)

        layer_set = []

        l_layer = LayerUtils.layer_by_name('boundary_outline')
        layer_set.append(l_layer.id())
        soum = DatabaseUtils.working_l2_code()
        layer = LayerUtils.layer_by_data_source("s" + soum, 'ca_parcel')
        if layer is None:
            restrictions = DatabaseUtils.working_l2_code()
            layer = LayerUtils.load_layer_by_name("ca_parcel", "parcel_id", restrictions)
        if layer is not None:
            layer_set.append(layer.id())
        layer = LayerUtils.layer_by_data_source("s" + soum, 'ca_building')
        if layer is None:
            restrictions = DatabaseUtils.working_l2_code()
            layer = LayerUtils.load_layer_by_name("ca_building", "building_id", restrictions)
            layer = QgsMapLayerRegistry.instance().addMapLayer(layer)

        if layer is not None:
            layer_set.append(layer.id())

        overview_map = map_composition.getComposerMapById(1)
        overview_map.setLayerSet(layer_set)
        overview_map.setKeepLayerSet(True)
        if boundary_points_count > 7 or building_points_count > 8:
            self.__add_parcel_h_numbers(map_composition)
            self.__add_aimag_name_h(map_composition)
            self.__add_admin_unit_l2_name_h(map_composition)
            self.__add_admin_unit_l3_name_h(map_composition)
            self.__add_cadastre_block_code_h(map_composition)
            self.__add_parcel_street_name_h(map_composition)
            self.__add_khashaa_name_h(map_composition)
        self.__adjust_map_center_and_scale(overview_map, 30, 30, scale_denominator)
        self.__set_north_arrow_position(map_composition)
        self.__add_labels(map_composition)
        self.__add_parcel_numbers(map_composition)
        self.__create_coordinate_list(map_composition)
        self.__create_parcel_distance_list(map_composition)
        self.__create_building_distance_list(map_composition)
        self.__create_building_polygon_area_list(map_composition)
        self.__add_grid(composer_map)
        self.__add_aimag_name(map_composition)
        self.__add_admin_unit_l2_name(map_composition)
        self.__add_admin_unit_l3_name(map_composition)
        self.__add_cadastre_block_code(map_composition)
        self.__add_parcel_street_name(map_composition)
        self.__add_khashaa_name(map_composition)
        self.__add_stamp(map_composition)
        self.__add_right_holder_information(map_composition)
        self.__addNorthArrow(map_composition)

        map_composition.exportAsPDF(file_path)
        QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))

        map_canvas.setDestinationCrs(original_crs)
        map_canvas.setCrsTransformEnabled(original_trafo)
        map_canvas.setExtent(original_extent)

        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def __print_pdf(self, map_composition, file_path):

        dpi = int(self.dpi_edit.text())

        map_composition.setPrintResolution(dpi)
        map_composition.refreshItems()
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        printer.setPaperSize(QSizeF(map_composition.paperWidth(), map_composition.paperHeight()), QPrinter.Millimeter)
        printer.setFullPage(True)
        printer.setColorMode(QPrinter.Color)
        printer.setResolution(map_composition.printResolution())

        #Resolution is better with export as
        map_composition.exportAsPDF(file_path)

    @pyqtSlot()
    def on_help_button_clicked(self):

        pass

    def __adjust_map_center_and_scale(self, composer_map, map_frame_width, map_frame_height, scale_denominator = None):

        bounding_box = self.__geometry.boundingBox()
        buffer = float(self.buffer_edit.text())
        width = bounding_box.width() + buffer
        height = bounding_box.height() + buffer

        if width / height > 1.0 * map_frame_width / map_frame_height:
            height = map_frame_height * width / map_frame_width
        else:
            width = map_frame_width * height / map_frame_height

        bbox_center_x = bounding_box.center().x()
        bbox_center_y = bounding_box.center().y()

        composer_map.setNewExtent(QgsRectangle(bbox_center_x - width / 2, bbox_center_y - height / 2, bbox_center_x + width / 2, bbox_center_y + height / 2))

        if scale_denominator is not None:
            composer_map.setNewScale(scale_denominator * 10)
            self.__overview_map_scale = scale_denominator * 10
            return None

        scale_denominator = composer_map.scale()

        if scale_denominator < 250:
            scale_denominator = 250
        elif 250 < scale_denominator < 500:
            scale_denominator = 500
        elif 500 < scale_denominator < 1000:
            scale_denominator = 1000
        elif 1000 < scale_denominator < 2500:
            scale_denominator = 2500
        elif 2500 < scale_denominator < 5000:
            scale_denominator = 5000
        elif scale_denominator > 5000:
            scale_denominator = math.ceil(scale_denominator / 5000) * 5000

        self.__map_scale = scale_denominator
        composer_map.setNewScale(scale_denominator)

        return scale_denominator

    def __add_labels(self, map_composition):

        # Headlines
        map_title = self.map_title_edit.text()
        item = map_composition.getComposerItemById("map_title")
        item.setText(map_title)
        item.adjustSizeToText()

        # Coordinate system
        item = map_composition.getComposerItemById("crs_description")

        soum = DatabaseUtils.working_l2_code()

        layer = LayerUtils.layer_by_data_source("s"+soum, "ca_parcel")
        if layer is None:
            layer = LayerUtils.load_layer_by_name("ca_parcel", "parcel_id", soum)

        request = QgsFeatureRequest()
        # request.setFilterExpression("maintenance_case = " + str(self.maintenance_case.id))

        iterator = layer.getFeatures(request)

        for feature in iterator:
            if feature.geometry() != None:
                point = feature.geometry().centroid()
                break

        srid = PluginUtils.utm_srid_from_point(point.asPoint())

        item.setText('EPSG: '+str(srid))

        # Zone No
        item = map_composition.getComposerItemById("zone_no")
        zone_no = str(srid)[3:]
        item.setText(zone_no+'N')
        # Scales
        scale_description = u" (1 сантиметрт " + "{0}".format(self.__map_scale/100) + u" метр багтана)"
        scale_final = u"Зургийн масштаб = 1:" + "{0}".format(self.__map_scale) + scale_description
        item = map_composition.getComposerItemById("scale_description")
        item.setText(scale_final)
        item.adjustSizeToText()
        scale = u"Масштаб = 1:" + str(self.__overview_map_scale)
        item = map_composition.getComposerItemById("scale")
        item.setText(scale)
        item.adjustSizeToText()

        #parcel area
        item = map_composition.getComposerItemById("area")
        parcel = self.session.query(CaParcel).filter(CaParcel.parcel_id == self.__parcel_no).one()
        item.setText(str(int(parcel.area_m2)))
        # item.setText(str((round(self.__geometry.area(), 2))))
        item.adjustSizeToText()

        #print print date
        item = map_composition.getComposerItemById("print_date")
        item.setText(QDate.currentDate().toString(Constants.DATE_FORMAT))
        item.adjustSizeToText()

    def __copy_label(self, label, text, map_composition):

        label_2 = QgsComposerLabel(map_composition)
        label_2.setText(text)
        map_composition.addItem(label_2)

        label_2.setItemPosition(label.x(), label.y() + 4)

        label_2.setFont(label.font())
        label_2.setFontColor(label.fontColor())
        label_2.setOpacity(label.opacity())
        label_2.setMargin(0)
        label_2.adjustSizeToText()
        return label_2

    def __add_label(self, map_composition, label_text, x, y, font_size, bold = False, font_color = Qt.black, opacity = 255, center_label_on_map = False):

        composer_label = QgsComposerLabel(map_composition)
        composer_label.setText(label_text)
        map_composition.addItem(composer_label)
        composer_label.setItemPosition(x, y)
        font = composer_label.font()
        font.setPointSize(font_size)
        font.setBold(bold)
        composer_label.setFontColor(font_color)
        composer_label.setFont(font)
        composer_label.adjustSizeToText()
        composer_label.setMargin(0)
        self.__set_item_opacity(composer_label, opacity)

        if center_label_on_map:
            text_width = composer_label.textWidthMillimeters(font, label_text)
            composer_label.setItemPosition((297-text_width)/2, y)

    def __add_logos(self, map_composition):

        flag_logo = QgsComposerPicture(map_composition)
        path = PluginUtils.get_map_path() + QDir.separator() + QString("flag.png")
        flag_logo.setPictureFile(path)
        flag_logo.setItemPosition(271, 2, 22.4, 11.2)
        map_composition.addItem(flag_logo)

        alacgac_logo = QgsComposerPicture(map_composition)
        path = PluginUtils.get_map_path() + QDir.separator() + QString("alacgac.png")
        alacgac_logo.setPictureFile(path)
        alacgac_logo.setItemPosition(5, 2, 33, 11.2)
        map_composition.addItem(alacgac_logo)

    def __create_coordinate_list(self, map_composition):

        self.__create_building_coordinate_list(map_composition)
        self.__create_parcel_coordinates_list(map_composition)

    def __create_building_coordinate_list(self, map_composition):

        point_layer = LayerUtils.layer_by_name('building_points')
        if point_layer is None:
            return

        no_start_label = map_composition.getComposerItemById("building_no")
        x_start_label = map_composition.getComposerItemById("building_x")
        y_start_label = map_composition.getComposerItemById("building_y")

        # retreive every feature with its geometry and attributes
        count = 0
        for feature in point_layer.getFeatures():
            count += 1

            # fetch geometry
            geom = feature.geometry()
            geom.transform(self.__coord_transform)
            point = geom.asPoint()

            attribute_map = feature.attributes()
            point_no = attribute_map[0]

            x_formatted = locale.format('%.2f', round(point.x(), 2), True)
            y_formatted = locale.format('%.2f', round(point.y(), 2), True)

            no_start_label = self.__copy_label(no_start_label, point_no, map_composition)
            x_start_label = self.__copy_label(x_start_label, x_formatted, map_composition)
            y_start_label = self.__copy_label(y_start_label, y_formatted, map_composition)

            #just one column for building coordinates
            if count == 37:
                break

    def __create_parcel_coordinates_list(self, map_composition):

        point_layer = LayerUtils.layer_by_name('boundary_points')
        if point_layer is None:
            return

        no_start_label = map_composition.getComposerItemById("no")
        x_start_label = map_composition.getComposerItemById("x")
        y_start_label = map_composition.getComposerItemById("y")

        # retreive every feature with its geometry and attributes
        for feature in point_layer.getFeatures():

            # fetch geometry
            geom = feature.geometry()
            geom.transform(self.__coord_transform)
            point = geom.asPoint()

            attribute_map = feature.attributes()
            point_no = attribute_map[0]
            point_no_int = int(attribute_map[0])

            if point_no_int == 38:
                no_start_label = map_composition.getComposerItemById("no_2")
                x_start_label = map_composition.getComposerItemById("x_2")
                y_start_label = map_composition.getComposerItemById("y_2")

            elif point_no_int == 75:
                break

            x_formatted = locale.format('%.2f', round(point.x(), 2), True)
            y_formatted = locale.format('%.2f', round(point.y(), 2), True)

            no_start_label = self.__copy_label(no_start_label, point_no, map_composition)
            x_start_label = self.__copy_label(x_start_label, x_formatted, map_composition)
            y_start_label = self.__copy_label(y_start_label, y_formatted, map_composition)

        if self.__second_page_enabled and point_no_int < 38:
            map_composition.removeComposerItem(map_composition.getComposerItemById("no_2"))
            map_composition.removeComposerItem(map_composition.getComposerItemById("x_2"))
            map_composition.removeComposerItem(map_composition.getComposerItemById("y_2"))
            map_composition.removeComposerItem(map_composition.getComposerItemById("distance_2"))

    def __create_parcel_distance_list(self, map_composition):

        line_layer = LayerUtils.layer_by_name('boundary_lines')
        if line_layer is None:
            return

        count = 1
        distance_start_label = map_composition.getComposerItemById("distance")
        for feature in line_layer.getFeatures():

            attribute_map = feature.attributes()
            distance = str(attribute_map[0])
            count += 1

            if count == 39:
                distance_start_label = map_composition.getComposerItemById("distance_2")

            elif count > 75:
                break

            dist_formatted = "{0}".format(distance)

            distance_start_label = self.__copy_label(distance_start_label, dist_formatted, map_composition)

    def __create_building_distance_list(self, map_composition):

        line_layer = LayerUtils.layer_by_name('building_lines')
        if line_layer is None:
            return

        count = 1
        distance_start_label = map_composition.getComposerItemById("building_distance")
        for feature in line_layer.getFeatures():

            attribute_map = feature.attributes()
            distance = str(attribute_map[0])
            count += 1

            if count == 39:
                break

            dist_formatted = "{0}".format(distance)

            distance_start_label = self.__copy_label(distance_start_label, dist_formatted, map_composition)

    def __create_building_polygon_area_list(self, map_composition):

        area_start_label = map_composition.getComposerItemById("building_area")
        building_no_area = ''
        building_no = u'Д.байхгүй'
        for building_id in self.__building_id_list:
            building = self.session.query(CaBuilding).filter(CaBuilding.building_id == building_id).one()
            if building.building_no != None:
                building_no = building.building_no
            building_no_area = building_no + '/ ' + str(int(building.area_m2))
            area_start_label = self.__copy_label(area_start_label, building_no_area, map_composition)

    def __set_north_arrow_position(self, map_composition):

        x, y = 185, 45
        if self.upper_left_rbutton.isChecked():
            x, y = 15, 45
        elif self.lower_left_rbutton.isChecked():
            x, y = 15, 170
        elif self.lower_right_rbutton.isChecked():
            x, y = 175, 170
        mapPath = os.path.join(os.path.dirname(__file__), "map")
        path = mapPath + QDir.separator() + "north_arrow.svg"
        north_arrow = map_composition.getComposerItemById("north_arrow")
        north_arrow.setPictureFile(path)
        north_arrow.setItemPosition(x, y, 20, 20)

    def __set_item_opacity(self, composer_item, opacity):

        # opacity 0 - 255
        item_brush = composer_item.brush()
        brush_color = item_brush.color()
        brush_color.setAlpha( opacity )
        composer_item.setBrush( QBrush( brush_color ) )
        composer_item.update()

    def __add_parcel_h_numbers(self, map_composition):

        item = map_composition.getComposerItemById("parcel_id_h")
        parcel_id = self.__parcel_no

        parcel_id = self.__cut_zeros_from_parcel_id(parcel_id)

        if self.geoid_chbox.isChecked():

            tmp_geoid = self.__feature.attributes()[self.GEO_ID]
            if tmp_geoid is None or type(tmp_geoid) == QPyNullVariant:
                parcel_id = ' '
            else:
                parcel_id = parcel_id + ' Geo ID: '+ tmp_geoid

        if self.old_parcel_id_chbox.isChecked():
            tmp_old_id = self.__feature.attributes()[self.OLD_PARCEL_ID]
            if tmp_old_id is None or type(tmp_old_id) == QPyNullVariant:
                parcel_id = ' '
            else:
                parcel_id = parcel_id + u' Х/Нэгж талбарын дугаар: ' + tmp_old_id

        item.setText(parcel_id)
        item.adjustSizeToText()

    def __add_parcel_numbers(self, map_composition):

        item = map_composition.getComposerItemById("parcel_id")
        parcel_id = self.__parcel_no

        parcel_id = self.__cut_zeros_from_parcel_id(parcel_id)

        if self.geoid_chbox.isChecked():

            tmp_geoid = self.__feature.attributes()[self.GEO_ID]
            if tmp_geoid is None or type(tmp_geoid) == QPyNullVariant:
                parcel_id = ' '
            else:
                parcel_id = parcel_id + u' Гео ID: ' + tmp_geoid

        if self.old_parcel_id_chbox.isChecked():
            tmp_old_id = self.__feature.attributes()[self.OLD_PARCEL_ID]
            if tmp_old_id is None or type(tmp_old_id) == QPyNullVariant:
                parcel_id = ' '
            else:
                parcel_id = parcel_id + u' ХНТ дугаар: ' + tmp_old_id

        item.setText(parcel_id)
        item.adjustSizeToText()

    def __cut_zeros_from_parcel_id(self, parcel_id):

        #Structure in LM2: AAACCCCPPPPP

        if len(parcel_id) <> 12:
            return parcel_id

        aimag = parcel_id[0:3]
        cadastre_block = parcel_id[4:7]
        parcel_no = parcel_id[7:12]

        aimag = aimag.lstrip("0")
        # cadastre_block = cadastre_block.lstrip("0")
        parcel_no = parcel_no#.lstrip("0")

        parcel_id = aimag + cadastre_block + parcel_no

        return parcel_id

    def __add_aimag_name_h(self, map_composition):

        aimag_code = DatabaseUtils.current_working_soum_schema()[:3]
        try:
            aimag_name = self.session.query(AuLevel1.name).filter(AuLevel1.code == aimag_code).one()

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        item = map_composition.getComposerItemById("aimag_name_h")
        item.setText(aimag_name[0])
        item.adjustSizeToText()

    def __add_aimag_name(self, map_composition):

        aimag_code =DatabaseUtils.current_working_soum_schema()[:3]

        try:
            aimag_name = self.session.query(AuLevel1.name).filter(AuLevel1.code == aimag_code).one()

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("aCould not execute: {0}").format(e.message))

        item = map_composition.getComposerItemById("aimag_name")
        item.setText(aimag_name[0])
        item.adjustSizeToText()

    def __add_admin_unit_l2_name_h(self, map_composition):

        try:
            parcel_geometry = self.session.query(CaParcel.geometry).filter(CaParcel.parcel_id == self.__parcel_no).one()
            admin_unit_l2_name = self.session.query(AuLevel2.name).filter(AuLevel2.geometry.ST_Intersects(parcel_geometry[0])).first()

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("bCould not execute: {0}").format(e.message))

        item = map_composition.getComposerItemById("soum_name_h")
        item.setText(admin_unit_l2_name[0])
        item.adjustSizeToText()

    def __add_admin_unit_l2_name(self, map_composition):

        try:
            parcel_geometry = self.session.query(CaParcel.geometry).filter(CaParcel.parcel_id == self.__parcel_no).one()
            admin_unit_l2_name = self.session.query(AuLevel2.name).filter(AuLevel2.geometry.ST_Intersects(parcel_geometry[0])).first()

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("Database Query Error"), self.tr("bCould not execute: {0}").format(e.message))

        item = map_composition.getComposerItemById("soum_name")
        item.setText(admin_unit_l2_name[0])
        item.adjustSizeToText()

    def __add_admin_unit_l3_name_h(self, map_composition):

        try:
            parcel_geometry = self.session.query(CaParcel.geometry).filter(CaParcel.parcel_id == self.__parcel_no).one()
            admin_unit_l3_name = self.session.query(AuLevel3.name).filter(AuLevel3.geometry.ST_Intersects(parcel_geometry[0])).first()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("cCould not execute: {0}").format(e.message))
            return

        item = map_composition.getComposerItemById("bag_name_h")
        item.setText(admin_unit_l3_name[0])
        item.adjustSizeToText()

    def __add_admin_unit_l3_name(self, map_composition):

        try:
            parcel_geometry = self.session.query(CaParcel.geometry).filter(CaParcel.parcel_id == self.__parcel_no).one()
            admin_unit_l3_name = self.session.query(AuLevel3.name).filter(AuLevel3.geometry.ST_Intersects(parcel_geometry[0])).first()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("cCould not execute: {0}").format(e.message))
            return

        item = map_composition.getComposerItemById("bag_name")
        item.setText(admin_unit_l3_name[0])
        item.adjustSizeToText()

    def __add_cadastre_block_code_h(self, map_composition):

        cadastre_block_number = self.__parcel_no[4:7]

        item = map_composition.getComposerItemById("cadastre_block_name_h")
        item.setText(cadastre_block_number)
        item.adjustSizeToText()

    def __add_cadastre_block_code(self, map_composition):

        cadastre_block_number = self.__parcel_no[4:7]
        item = map_composition.getComposerItemById("cadastre_block_name")
        item.setText(cadastre_block_number)
        item.adjustSizeToText()

    def __add_parcel_street_name_h(self, map_composition):

        tmp_street_name = self.__feature.attributes()[self.STREET_NAME]

        if tmp_street_name is None or type(tmp_street_name) == QPyNullVariant:
            street_name = ''
        else:
            street_name = tmp_street_name

        item = map_composition.getComposerItemById("street_name_h")
        item.setText(street_name)
        item.adjustSizeToText()

    def __add_parcel_street_name(self, map_composition):

        tmp_street_name = self.__feature.attributes()[self.STREET_NAME]

        if tmp_street_name is None or type(tmp_street_name) == QPyNullVariant:
            street_name = ''
        else:
            street_name = tmp_street_name

        item = map_composition.getComposerItemById("street_name")
        item.setText(street_name)
        item.adjustSizeToText()

    def __add_khashaa_name_h(self, map_composition):

        tmp_khashaa_name = self.__feature.attributes()[self.KHASHAA_NAME]

        if tmp_khashaa_name is None or type(tmp_khashaa_name) == QPyNullVariant:
            khashaa_name = ''
        else:
            khashaa_name = tmp_khashaa_name

        item = map_composition.getComposerItemById("khashaa_name_h")
        item.setText(khashaa_name)
        item.adjustSizeToText()

    def __add_khashaa_name(self, map_composition):

        tmp_khashaa_name = self.__feature.attributes()[self.KHASHAA_NAME]

        if tmp_khashaa_name is None or type(tmp_khashaa_name) == QPyNullVariant:
            khashaa_name = ''
        else:
            khashaa_name = tmp_khashaa_name

        item = map_composition.getComposerItemById("khashaa_name")
        item.setText(khashaa_name)
        item.adjustSizeToText()

    def __add_right_holder_information(self, map_composition):

        selected_items = self.right_holder_twidget.selectedItems()
        if len(selected_items) == 0:
            return

        selected_row = self.right_holder_twidget.row(selected_items[0])

        twidget_item = self.right_holder_twidget.item(selected_row, self.FAMILYNAME)
        if twidget_item is None:
            return

        right_holder_name = twidget_item.text()

        twidget_item = self.right_holder_twidget.item(selected_row, self.FIRSTNAME)
        first_name = twidget_item.text()
        right_holder_name += '' if first_name is None or type(first_name) == QPyNullVariant else ' ' + first_name

        twidget_item = self.right_holder_twidget.item(selected_row, self.FIRSTNAME)
        right_type = twidget_item.data(Qt.UserRole)

        twidget_item = self.right_holder_twidget.item(selected_row, self.CODEIDCARD)
        code_id_card = twidget_item.text()
        item = map_composition.getComposerItemById("right_holder_name")
        item.setText(right_holder_name)
        item = map_composition.getComposerItemById("id_card_code")
        item.setText(code_id_card)
        item = map_composition.getComposerItemById("right_type")
        item.setText(right_type)

    def __right_type_description(self, application_type, person_type):

        right_type_desc = None
        try:
            set_right_type = self.session.query(SetRightTypeApplicationType)\
                .filter(SetRightTypeApplicationType.application_type == application_type).one()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("dCould not execute: {0}").format(e.message))
            return None

        if person_type == 50 or person_type == 60:
            right_type = self.session.query(ClRightType).filter(ClRightType.code == 1).one()
            right_type_desc = right_type.description
        else:
            right_type_desc = set_right_type.right_type_ref.description
        return right_type_desc

    def __add_parcel_size(self, map_composition):

        area = self.__geometry.area()

        self.__add_label(map_composition, u'Талбайн хэмжээ:                     квадрат метр', 213, 175, 10, True, Qt.black, 0)
        self.__add_label(map_composition, "{0}".format(area), 245, 175, 10, True, Qt.black)

    def __add_print_date(self, map_composition):

        today = QDate.currentDate()
        self.__add_label(map_composition, u'Хэвлэсэн огноо:   ' + today.toString(Constants.DATABASE_DATE_FORMAT), 140, 198, 11)

    def __add_stamp(self, map_composition):

        land_officer_name = DatabaseUtils.current_user()
        officer_position = land_officer_name.position
        officer_position_text = self.session.query(ClPositionType).filter(ClPositionType.code == officer_position).one()
        item = map_composition.getComposerItemById("land_officer_name")
        # land_officer_name = u"{0}, {1}".format(land_officer_name.surname[:1], land_officer_name.first_name)
        land_officer_name = '............................' + land_officer_name.surname[:1] + '.' + land_officer_name.first_name
        item.setText(land_officer_name)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("organisation_department_name")
        department_name = self.department_edit.text()
        land_organisation_department_name = '('+ officer_position_text.description + u' )'
        item.setText(land_organisation_department_name)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("department_head")
        department_head = '.................................' + self.department_head_edit.text()
        item.setText(department_head)
        item.adjustSizeToText()

        item = map_composition.getComposerItemById("department_name")
        item.setText('(' + department_name + u')')
        item.adjustSizeToText()

    @pyqtSlot()
    def on_choose_file_button_clicked(self):

        default_path = r'D:/TM_LM2/cad_maps'
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

        # path = QSettings().value(SettingsConstants.LAST_FILE_PATH, QDir.homePath())
        #
        # default_path = path + QDir.separator()

        file_dialog = QFileDialog(self, Qt.WindowStaysOnTopHint)
        file_dialog.setFilter('PDF (*.pdf)')
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setDirectory(default_path)
        file_dialog.selectFile('parcel_' + self.__parcel_no + ".pdf")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            if file_path is None or type(file_path) == QPyNullVariant:
                return
            f_info = QFileInfo(file_path)

            if file_path[-4:] != ".pdf":
                file_path += '.pdf'

            QSettings().setValue(SettingsConstants.LAST_FILE_PATH, f_info.dir().path())

            self.file_name_edit.setText(file_path)

    @pyqtSlot()
    def on_load_settings_button_clicked(self):

        self.__load_settings()

    def __load_settings(self):

        s = QSettings()

        dpi = s.value(SettingsConstants.DPI, "300")
        self.dpi_edit.setText(dpi)

        buffer = s.value(SettingsConstants.BUFFER, "5")
        self.buffer_edit.setText(buffer)

        grid_distance = s.value(SettingsConstants.GRID_DISTANCE, "50")
        self.grid_distance_edit.setText(grid_distance)

        grid_offset_x = s.value(SettingsConstants.GRID_OFFSET_X, "0")
        self.grid_offset_x_edit.setText(grid_offset_x)

        grid_offset_y = s.value(SettingsConstants.GRID_OFFSET_Y, "0")
        self.grid_offset_y_edit.setText(grid_offset_y)

        parcel_id_field = s.value(SettingsConstants.PARCEL_ID_FIELD, "cadastreId")

        if parcel_id_field == 'cadastreId':
            self.cadastreid_chbox.setChecked(True)
        elif parcel_id_field == 'geoId':
            self.geoid_chbox.setChecked(True)
        elif parcel_id_field == 'oldParcelId':
            self.old_parcel_id_chbox.setChecked(True)

        map_title = s.value(SettingsConstants.MAP_TITLE, u'Дархан-Уул аймгийн Газрын Харилцаа Барилга Хот Байгуулалтын Газар')
        self.map_title_edit.setText(map_title)

        department_head = s.value(SettingsConstants.DEPARTMENT_HEAD, u'Хэлтсийн дарга')
        self.department_head_edit.setText(department_head)

        department = s.value(SettingsConstants.DEPARTMENT, u'Хэлтсийн нэр')
        self.department_edit.setText(department)

        north_arrow_position = s.value(SettingsConstants.NORTH_ARROW_POSITION, "ur")

        if north_arrow_position == 'ul':
            self.upper_left_rbutton.setChecked(True)
        elif north_arrow_position == 'ur':
            self.upper_right_rbutton.setChecked(True)
        elif north_arrow_position == 'll':
            self.lower_left_rbutton.setChecked(True)
        elif north_arrow_position == 'lr':
            self.lower_right_rbutton.setChecked(True)

    def __setup_coord_transform(self):

        line_layer = LayerUtils.layer_by_name('boundary_lines')
        if line_layer is None:
            return

        source_crs = line_layer.crs()
        proj4 = PluginUtils.utm_proj4def_from_point(self.__geometry.centroid().asPoint())
        destination_crs = QgsCoordinateReferenceSystem()
        destination_crs.createFromProj4(proj4)
        self.__coord_transform = QgsCoordinateTransform(source_crs, destination_crs)
        self.__geometry.transform(self.__coord_transform)

    @pyqtSlot()
    def on_save_settings_button_clicked(self):

        self.__save_settings()

    def __save_settings(self):

        s = QSettings()

        dpi = self.dpi_edit.text()
        s.setValue(SettingsConstants.DPI, dpi)

        buffer = self.buffer_edit.text()
        s.setValue(SettingsConstants.BUFFER, buffer)

        grid_distance = self.grid_distance_edit.text()
        s.setValue(SettingsConstants.GRID_DISTANCE, grid_distance)

        offset_x = self.grid_offset_x_edit.text()
        s.setValue(SettingsConstants.GRID_OFFSET_X, offset_x)

        offset_y = self.grid_offset_y_edit.text()
        s.setValue(SettingsConstants.GRID_OFFSET_Y, offset_y)

        parcel_id_field = 'cadastreId'

        if self.geoid_chbox.isChecked():
            parcel_id_field = 'geoId'
        if self.old_parcel_id_chbox.isChecked():
            parcel_id_field = 'oldParcelId'

        s.setValue(SettingsConstants.PARCEL_ID_FIELD, parcel_id_field)

        map_title = self.map_title_edit.text()
        s.setValue(SettingsConstants.MAP_TITLE, map_title)

        department_head = self.department_head_edit.text()
        s.setValue(SettingsConstants.DEPARTMENT_HEAD, department_head)

        department = self.department_edit.text()
        s.setValue(SettingsConstants.DEPARTMENT, department)

        north_arrow_position = 'ur'

        if self.upper_left_rbutton.isChecked():
            north_arrow_position = 'ul'
        elif self.lower_left_rbutton.isChecked():
            north_arrow_position = 'll'
        elif self.lower_right_rbutton.isChecked():
            north_arrow_position = 'lr'

        s.setValue(SettingsConstants.NORTH_ARROW_POSITION, north_arrow_position)

    @pyqtSlot()
    def on_loadDefaultsButton_clicked(self):

        self.dpi_edit.setText("300")

        self.buffer_edit.setText("5")
        
        self.grid_distance_edit.setText("50")

        self.grid_offset_x_edit.setText("0")

        self.grid_offset_y_edit.setText("0")

        self.cadastreid_chbox.setChecked(True)

        self.map_title_edit.setText(u'Дархан-Уул аймгийн Газрын Харилцаа Барилга Хот Байгуулалтын Газар')

        self.department_head_edit.setText(u'Хэлтсийн дарга')

        self.department_edit.setText(u'Хэлтсийн нэр')

        self.upper_right_rbutton.setChecked(True)

    @pyqtSlot(str)
    def on_dpi_edit_textEdited(self, new_text):
        try:
            int(self.dpi_edit.text())
        except ValueError:
            self.dpi_edit.setText("300")

    @pyqtSlot(str)
    def on_buffer_edit_textEdited(self, new_text):

        try:
            int(self.buffer_edit.text())
        except ValueError:
            self.buffer_edit.setText("5")

    @pyqtSlot(str)
    def on_grid_distance_edit_textEdited(self, new_text):

        try:
            int(self.grid_distance_edit.text())
        except ValueError:
            self.grid_distance_edit.setText("50")

    @pyqtSlot(str)
    def on_grid_offset_x_edit_textEdited(self, new_text):

        try:
            int(self.grid_offset_x_edit.text())
        except ValueError:
            self.grid_offset_x_edit.setText("0")

    @pyqtSlot(str)
    def on_grid_offset_y_edit_textEdited(self, new_text):
        try:
            int(self.grid_offset_y_edit.text())
        except ValueError:
            self.grid_offset_y_edit.setText("0")

    def __add_grid(self, composer_map):

        composer_map.setGridEnabled(True)
        composer_map.setGridStyle(QgsComposerMap.Cross)
        grid_distance = int(self.grid_distance_edit.text())
        composer_map.setGridIntervalX(grid_distance)
        composer_map.setGridIntervalY(grid_distance)
        offset_x = int(self.grid_offset_x_edit.text())
        offset_y = int(self.grid_offset_y_edit.text())
        composer_map.setGridOffsetX(offset_x)
        composer_map.setGridOffsetY(offset_y)
        composer_map.setCrossLength(1.5)
        composer_map.setShowGridAnnotation(True)
        composer_map.setGridAnnotationPosition(QgsComposerMap.OutsideMapFrame, QgsComposerMap.Left)
        composer_map.setGridAnnotationDirection(QgsComposerMap.BoundaryDirection, QgsComposerMap.Left)
        composer_map.setGridAnnotationDirection(QgsComposerMap.BoundaryDirection, QgsComposerMap.Right)
        composer_map.setGridAnnotationPrecision(0)
        font = composer_map.gridAnnotationFont()
        font.setPointSize(6)
        composer_map.setGridAnnotationFont(font)
        composer_map.setAnnotationFrameDistance(1)

    @pyqtSlot()
    def on_help_button_clicked(self):

        os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/print_cadastral_map.htm")

    def __addNorthArrow(self, mapComposition):

        mapPath = os.path.join(os.path.dirname(__file__), "map")

        x, y = 185, 45
        if self.upper_left_rbutton.isChecked():
            x, y = 15, 45
        elif self.lower_left_rbutton.isChecked():
            x, y = 15, 170
        elif self.lower_right_rbutton.isChecked():
            x, y = 175, 170

        northArrow = QgsComposerPicture(mapComposition)
        path = mapPath + QDir.separator() + str("north_arrow.svg")

        northArrow.setPictureFile(path)
        northArrow.setItemPosition(x, y, 20, 20)
        # northArrow.setFrame(False)

        self.__setItemOpacity(northArrow, 0)

        mapComposition.addItem(northArrow)

    def __setItemOpacity(self, composerItem, opacity):

        # opacity 0 - 255
        itemBrush = composerItem.brush()
        brushColor = itemBrush.color()
        brushColor.setAlpha( opacity )
        composerItem.setBrush( QBrush( brushColor ) )
        composerItem.update()

    # Cadastre page

    def __cadastre_page_settings(self):

        soum = DatabaseUtils.working_l2_code()
        soum_filter = str(soum) + "-%"
        count = self.session.query(SetCadastrePage.range_first_no,
                                                           SetCadastrePage.range_last_no,
                                                           SetCadastrePage.current_no) \
            .filter(SetCadastrePage.id.like(soum_filter)) \
            .order_by(SetCadastrePage.register_date.desc()).limit(1).count()
        if count == 1:
            first_no, last_no, current_no = self.session.query(SetCadastrePage.range_first_no, SetCadastrePage.range_last_no,
                                                               SetCadastrePage.current_no) \
                .filter(SetCadastrePage.id.like(soum_filter)) \
                .order_by(SetCadastrePage.register_date.desc()).limit(1).one()

            return {Constants.CADASTRE_PAGE_FIRST_NUMBER: first_no, Constants.CADASTRE_PAGE_LAST_NUMBER: last_no,
                    Constants.CADASTRE_PAGE_CURRENT_NUMBER: current_no}
        else:
            return 0

    def __cadastre_page_interval_settings(self, id):

        soum = DatabaseUtils.working_l2_code()
        count = self.session.query(SetCadastrePage.range_first_no,
                                   SetCadastrePage.range_last_no,
                                   SetCadastrePage.current_no) \
            .filter(SetCadastrePage.id == id).count()
        if count == 1:
            first_no, last_no, current_no = self.session.query(SetCadastrePage.range_first_no,
                                                               SetCadastrePage.range_last_no,
                                                               SetCadastrePage.current_no) \
                .filter(SetCadastrePage.id==id).one()

            return {Constants.CADASTRE_PAGE_FIRST_NUMBER: first_no, Constants.CADASTRE_PAGE_LAST_NUMBER: last_no,
                    Constants.CADASTRE_PAGE_CURRENT_NUMBER: current_no}
        else:
            return 0

    def __calculate_cadastre_page_no(self):

        cadastre_page_settings = self.__cadastre_page_settings()
        if cadastre_page_settings == 0:
            self.error_label.setText(self.tr("The cadastre page number is out of range. Change the Admin Settings."))
            return
        max_page_no = cadastre_page_settings[Constants.CADASTRE_PAGE_CURRENT_NUMBER] + 1

        if cadastre_page_settings[Constants.CADASTRE_PAGE_FIRST_NUMBER] <= max_page_no \
                <= cadastre_page_settings[Constants.CADASTRE_PAGE_LAST_NUMBER]:
            return max_page_no
        else:
            self.error_label.setText(self.tr("The cadastre page number is out of range. Change the Admin Settings."))
            self.error_label.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            return 0

    def __calculate_interval_cadastre_page_no(self, cadastre_page_id):

        cadastre_page_settings = self.__cadastre_page_interval_settings(cadastre_page_id)
        if cadastre_page_settings == 0:
            self.error_label.setText(self.tr("The cadastre page number is out of range. Change the Admin Settings."))
            return
        max_page_no = cadastre_page_settings[Constants.CADASTRE_PAGE_CURRENT_NUMBER] + 1

        if cadastre_page_settings[Constants.CADASTRE_PAGE_FIRST_NUMBER] <= max_page_no \
                <= cadastre_page_settings[Constants.CADASTRE_PAGE_LAST_NUMBER]:
            return max_page_no
        else:
            self.error_label.setText(self.tr("The cadastre page number is out of range. Change the Admin Settings."))
            self.error_label.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            return 0

    @pyqtSlot(int)
    def on_cadastre_checkbox_stateChanged(self, state):

        self.cadastre_page_interval_cbox.clear()
        soum = DatabaseUtils.working_l2_code()
        soum_filter = str(soum) + "-%"

        set_cadastre_pages = self.session.query(SetCadastrePage.range_first_no,
                                   SetCadastrePage.range_last_no,
                                   SetCadastrePage.id,
                                   SetCadastrePage.current_no) \
            .filter(SetCadastrePage.id.like(soum_filter)) \
            .order_by(SetCadastrePage.range_first_no.asc()).all()

        for set_cadastre_page in set_cadastre_pages:
            self.cadastre_page_interval_cbox.addItem(str(set_cadastre_page.range_first_no) + "-" + str(set_cadastre_page.range_last_no) + '/' + str(set_cadastre_page.current_no) + '/', set_cadastre_page.id)

        if self.__calculate_cadastre_page_no() == 0:
            self.error_label.setText(self.tr("The cadastre page number is out of range. Change the Admin Settings."))
            return
        # cadastre_page_number = self.__calculate_cadastre_page_no()
        # if cadastre_page_number == None:
        #     cadastre_page_number = 0
        # if cadastre_page_number != -1:
        #     self.cadastre_page_sbox.setValue(cadastre_page_number)

        self.cpage_print_date.setDate(QDate().currentDate())
        if state == Qt.Checked:
            self.cadastre_page_interval_cbox.setEnabled(True);
            self.cadastre_page_sbox.setEnabled(True)
            self.cpage_save_button.setEnabled(True)
            self.cpage_print_date.setEnabled(True)
        else:
            self.cadastre_page_interval_cbox.setEnabled(False);
            self.cadastre_page_sbox.setEnabled(False)
            self.cpage_save_button.setEnabled(False)
            self.cpage_print_date.setEnabled(False)

    @pyqtSlot(int)
    def on_cadastre_page_interval_cbox_currentIndexChanged(self, index):

        cadastre_page_id = self.cadastre_page_interval_cbox.itemData(index)
        cadastre_page_number = self.__calculate_interval_cadastre_page_no(cadastre_page_id)
        if cadastre_page_number == None:
            cadastre_page_number = 0
        if cadastre_page_number != -1:
            self.cadastre_page_sbox.setValue(cadastre_page_number)

    @pyqtSlot()
    def on_cpage_save_button_clicked(self):

        cadastre_page_id = self.cadastre_page_interval_cbox.itemData(self.cadastre_page_interval_cbox.currentIndex())
        # self.__save_cadastre_page()
        self.__save_interval_cadastre_page(cadastre_page_id);

    def __save_interval_cadastre_page(self, cadastre_page_id):

        if self.__cadastre_page_interval_settings(cadastre_page_id) == -1:
            return

        cadastre_page_settings = self.__cadastre_page_interval_settings(cadastre_page_id)
        max_page_no = self.cadastre_page_sbox.value()

        if not cadastre_page_settings[Constants.CADASTRE_PAGE_FIRST_NUMBER] <= max_page_no \
                <= cadastre_page_settings[Constants.CADASTRE_PAGE_LAST_NUMBER]:
            self.error_label.setText(self.tr("The certificate number is out of range. Change the Admin Settings."))
            self.error_label.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            return

        selected_items = self.right_holder_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("No right holder information!!!"))
            return

        if self.cadastre_page_sbox.value() == 0:
            PluginUtils.show_message(self, self.tr("Value"), self.tr("Please enter cadasre page number!!!"))
            return

        parcel_id = self.__parcel_no
        current_row = self.right_holder_twidget.currentRow()
        person_id = self.right_holder_twidget.item(current_row, 0).data(Qt.UserRole + 1)
        cadastre_page_number = self.cadastre_page_sbox.value()

        cadastre_page_count = self.session.query(CtCadastrePage) \
            .filter(CtCadastrePage.cadastre_page_number == cadastre_page_number).count()

        if cadastre_page_count > 0:
            PluginUtils.show_message(self, self.tr("Value"), self.tr("This cadastre page already saved!"))
            return

        print_date_qt = PluginUtils.convert_qt_date_to_python(self.cpage_print_date.date())

        cadastre_page = CtCadastrePage()
        cadastre_page.print_date = print_date_qt
        cadastre_page.person_id = person_id
        cadastre_page.parcel_id = parcel_id
        cadastre_page.cadastre_page_number = cadastre_page_number
        self.session.add(cadastre_page)

        set_cadastre_page = self.session.query(SetCadastrePage) \
            .filter(SetCadastrePage.id == cadastre_page_id).one()

        set_cadastre_page.current_no = cadastre_page_number

        self.session.commit()
        PluginUtils.show_message(self, self.tr("Success"), self.tr("Successfully save"))

    def __save_cadastre_page(self):

        if self.__cadastre_page_settings() == -1:
            return

        cadastre_page_settings = self.__cadastre_page_settings()
        max_page_no = self.cadastre_page_sbox.value()

        if not cadastre_page_settings[Constants.CADASTRE_PAGE_FIRST_NUMBER] <= max_page_no \
                <= cadastre_page_settings[Constants.CADASTRE_PAGE_LAST_NUMBER]:

            self.error_label.setText(self.tr("The certificate number is out of range. Change the Admin Settings."))
            self.error_label.setStyleSheet(Constants.ERROR_TWIDGET_STYLESHEET)
            return

        selected_items = self.right_holder_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("No right holder information!!!"))
            return

        if self.cadastre_page_sbox.value() == 0:
            PluginUtils.show_message(self, self.tr("Value"), self.tr("Please enter cadasre page number!!!"))
            return

        parcel_id = self.__parcel_no
        current_row = self.right_holder_twidget.currentRow()
        person_id = self.right_holder_twidget.item(current_row, 0).data(Qt.UserRole+1)
        cadastre_page_number = self.cadastre_page_sbox.value()

        cadastre_page_count = self.session.query(CtCadastrePage) \
            .filter(CtCadastrePage.cadastre_page_number == cadastre_page_number).count()

        if cadastre_page_count > 0:
            PluginUtils.show_message(self, self.tr("Value"), self.tr("This cadastre page already saved!"))
            return

        print_date_qt = PluginUtils.convert_qt_date_to_python(self.cpage_print_date.date())

        cadastre_page = CtCadastrePage()
        cadastre_page.print_date = print_date_qt
        cadastre_page.person_id = person_id
        cadastre_page.parcel_id = parcel_id
        cadastre_page.cadastre_page_number = cadastre_page_number
        self.session.add(cadastre_page)

        soum = DatabaseUtils.working_l2_code()
        soum_filter = str(soum) + "-%"

        set_cadastre_page = self.session.query(SetCadastrePage) \
            .filter(SetCadastrePage.id.like(soum_filter)) \
            .order_by(SetCadastrePage.register_date.desc()).limit(1).one()

        set_cadastre_page.current_no = cadastre_page_number

        self.session.commit()
        PluginUtils.show_message(self, self.tr("Success"), self.tr("Successfully save"))