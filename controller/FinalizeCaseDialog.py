__author__ = 'Ankhaa'
from inspect import currentframe

from ..view.Ui_FinalizeCaseDialog import *
from ..model.CaTmpParcel import *
from ..model.CaBuilding import *
from ..model.CaTmpBuilding import *
from ..model.AuCadastreBlock import *
from ..model.SetSurveyCompany import SetSurveyCompany
from ..model.DatabaseHelper import DatabaseHelper
from ..utils.PluginUtils import *
from ..utils.LayerUtils import *
from ..model.Enumerations import UserRight


class FinalizeCaseDialog(QDialog, Ui_FinalizeCaseDialog, DatabaseHelper):
    def __init__(self, maintenance_case, maintenance_soum, plugin, parent=None):

        super(FinalizeCaseDialog, self).__init__(parent)
        DatabaseHelper.__init__(self)

        self.maintenance_case = maintenance_case
        self.maintenance_soum = maintenance_soum
        self.plugin = plugin
        self.setupUi(self)

        self.session = SessionHandler().session_instance()
        self.cancel_button.clicked.connect(self.reject)
        self.__setup_address_fill()
        try:
            self.__setup_twidgets()
            self.__setup_combo_boxes()
            self.__setup_mapping()
            self.__setup_context_menu()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            self.reject()

    def __setup_twidgets(self):

        self.maintenance_objects_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.maintenance_objects_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.maintenance_objects_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.buildings_item = QTreeWidgetItem()
        self.buildings_item.setExpanded(True)
        self.buildings_item.setData(Qt.UserRole, 1, self.buildings_item)
        self.buildings_item.setText(0, self.tr("Buildings"))

        self.parcels_item = QTreeWidgetItem()
        self.parcels_item.setExpanded(True)
        self.buildings_item.setData(Qt.UserRole, 2, self.parcels_item)
        self.parcels_item.setText(0, self.tr("Parcels"))

        self.maintenance_objects_twidget.addTopLevelItem(self.parcels_item)
        self.maintenance_objects_twidget.addTopLevelItem(self.buildings_item)
        self.maintenance_objects_twidget.setContextMenuPolicy(Qt.CustomContextMenu)

    def __setup_mapping(self):

        user = DatabaseUtils.current_user()

        self.user_name_edit.setText(user.surname + " - " + user.first_name)
        self.survey_date_edit.setDateTime(QDateTime().currentDateTime())
        self.completion_date_edit.setDateTime(QDateTime().currentDateTime())

        self.created_by_edit.setText(self.maintenance_case.created_by)
        qt_date = PluginUtils.convert_python_date_to_qt(self.maintenance_case.creation_date)
        if qt_date:
            self.creation_date_line_edit.setText(qt_date.toString(Constants.DATE_FORMAT))

        parcels = self.session.query(CaTmpParcel) \
            .filter(CaTmpParcel.maintenance_case == self.maintenance_case.id).all()

        buildings = self.session.query(CaTmpBuilding) \
            .filter(CaTmpBuilding.maintenance_case == self.maintenance_case.id).all()

        parcel_count = 0
        for parcel in parcels:
            main_parcel_item = QTreeWidgetItem()
            main_parcel_item.setText(0, parcel.parcel_id)
            main_parcel_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2/parcel_red.png")))
            main_parcel_item.setData(0, Qt.UserRole, parcel.parcel_id)
            main_parcel_item.setData(0, Qt.UserRole + 1, "parcel")
            self.parcels_item.addChild(main_parcel_item)
            parcel_count += 1

        building_count = 0
        for building in buildings:
            building_item = QTreeWidgetItem()
            building_item.setText(0, building.building_id)
            building_item.setData(0, Qt.UserRole, building.building_id)
            building_item.setData(0, Qt.UserRole + 1, "building")
            building_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2/building.gif")))
            self.buildings_item.addChild(building_item)
            building_count += 1

        self.number_of_parcel_lbl.setText(str(parcel_count))
        self.number_of_building_lbl.setText(str(building_count))
        self.maintenance_objects_twidget.expandAll()

    def __setup_combo_boxes(self):

        user_name = QSettings().value(SettingsConstants.USER)
        user_rights = DatabaseUtils.userright_by_name(user_name)

        land_offices = self.session.query(SetRole).all()
        companies = self.session.query(SetSurveyCompany).all()

        self.land_office_cbox.addItem("*", -1)

        for company in companies:
            self.company_cbox.addItem(company.name, company.id)

        for land_office in land_offices:
            session = SessionHandler().session_instance()
            try:
                sql = "select rolname from pg_user join pg_auth_members on (pg_user.usesysid=pg_auth_members.member) " \
                      "join pg_roles on (pg_roles.oid=pg_auth_members.roleid) where pg_user.usename=:bindName;"

                result = session.execute(sql, {'bindName': land_office.user_name}).fetchall()

                for right_result in result:

                    if right_result[0] == UserRight.cadastre_update:
                        self.land_office_cbox.addItem(land_office.user_name_real, land_office.user_name_real)


            except exc.SQLAlchemyError, e:
                session.rollback()
                raise LM2Exception(QApplication.translate("LM2", "Database Query Error"),
                                   QApplication.translate("LM2", "Could not execute: {0}").format(e.message))

    def __setup_context_menu(self):

        self.menu = QMenu()
        self.zoom_to_selected = QAction(QIcon("zoom.png"), "Zoom to item", self)
        self.menu.addAction(self.zoom_to_selected)
        self.zoom_to_selected.triggered.connect(self.zoom_to_selected_clicked)

    @pyqtSlot(int)
    def on_company_cbox_currentIndexChanged(self, index):

        surveyors = []
        self.surveyor_cbox.clear()
        current_company = self.company_cbox.itemData(index)

        if current_company == -1:
            return

        try:
            surveyors = self.session.query(SetSurveyor).filter(SetSurveyor.company == current_company).all()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        for surveyor in surveyors:
            self.surveyor_cbox.addItem((surveyor.surname +'-'+ surveyor.first_name), surveyor.id)

    @pyqtSlot(bool)
    def on_company_rbutton_toggled(self, state):

        if state:
            self.company_cbox.setEnabled(True)
            self.surveyor_cbox.setEnabled(True)
            self.survey_date_edit.setEnabled(True)
            self.land_office_cbox.setEnabled(False)
        else:
            self.company_cbox.setEnabled(False)
            self.surveyor_cbox.setEnabled(False)
            self.land_office_cbox.setEnabled(True)

    @pyqtSlot(bool)
    def on_land_office_rbutton_toggled(self, state):

        if state:
            self.company_cbox.setEnabled(False)
            self.surveyor_cbox.setEnabled(False)
            self.survey_date_edit.setEnabled(True)
            self.land_office_cbox.setEnabled(True)
        else:
            self.company_cbox.setEnabled(True)
            self.surveyor_cbox.setEnabled(True)
            self.land_office_cbox.setEnabled(False)

    def reject(self):

        QDialog.reject(self)

    @pyqtSlot()
    def on_ok_button_clicked(self):

        message_box = QMessageBox()
        message_box.setText(self.tr("street name check. You want continue?"))

        yes_button = message_box.addButton(self.tr("Yes"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("No"), QMessageBox.ActionRole)
        message_box.exec_()
        is_street_name_validator = True
        if message_box.clickedButton() == yes_button:
            try:
                num_rows = self.parcels_item.childCount()
                for row in range(num_rows):
                    item = self.parcels_item.child(row)
                    object_id = item.data(0, Qt.UserRole)
                    if object_id != None:
                        if len(object_id) == 12:
                            tmp_parcel = self.session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == object_id).one()
                            street_name_text = tmp_parcel.address_streetname

                            first_letter = ''

                            if street_name_text != None and street_name_text != '':
                                first_letter = street_name_text[0]
                                if tmp_parcel.address_streetname != '':
                                    first_letter = street_name_text[0]

                                if len(street_name_text) <= 0:
                                    is_street_name_validator = False
                            if first_letter not in Constants.CAPITAL_MONGOLIAN:
                                is_street_name_validator = False
                            if is_street_name_validator == False:
                                PluginUtils.show_message(self, self.tr("Street Name"), self.tr(object_id + " parcel street name is incorrect.You want to continue?"))

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return
        else:
            return

        user = DatabaseUtils.current_user()

        if not self.__valid_case():
            return

        self.maintenance_case.completion_date = DatabaseUtils.convert_date(self.completion_date_edit.date())
        self.maintenance_case.completed_by = user.user_name_real
        self.maintenance_case.survey_date = DatabaseUtils.convert_date(self.survey_date_edit.date())

        if self.land_office_rbutton.isChecked():
            idx = self.land_office_cbox.currentIndex()
            self.maintenance_case.surveyed_by_land_office = self.land_office_cbox.itemData(idx)
        else:
            idx = self.surveyor_cbox.currentIndex()
            self.maintenance_case.surveyed_by_surveyor = self.surveyor_cbox.itemData(idx)

        self.__write_changes()
        self.reject()

    def __valid_case(self):

        #check if the parcel&building geometries are within the restriction

        parcel_within = self.session.query(CaTmpParcel). \
                filter(CaTmpParcel.geometry.ST_Within(AuCadastreBlock.geometry)). \
                filter(CaTmpParcel.maintenance_case == self.maintenance_case.id).count()
        parcel_count = self.session.query(CaTmpParcel). \
                filter(CaTmpParcel.maintenance_case == self.maintenance_case.id).count()

        building_within = self.session.query(CaTmpBuilding). \
                filter(CaTmpBuilding.geometry.ST_Within(AuCadastreBlock.geometry)). \
                filter(CaTmpBuilding.maintenance_case == self.maintenance_case.id).count()

        building_count = self.session.query(CaTmpBuilding). \
                filter(CaTmpBuilding.maintenance_case == self.maintenance_case.id).count()

        if (parcel_within != parcel_count and parcel_count > 0) and (building_within != building_count and building_count > 0):
            PluginUtils.show_message(self, self.tr("Invalid case"), self.tr("The parcel and building geometries are outside the restrictions."))
            return False
        elif parcel_within == parcel_count and (building_within != building_count and building_count > 0):
            PluginUtils.show_message(self, self.tr("Invalid case"), self.tr("The building geometries are outside the restrictions."))
            return False
        elif parcel_within != parcel_count and (building_within == building_count and building_count > 0):
            PluginUtils.show_message(self, self.tr("Invalid case"), self.tr("The parcel geometries are outside the restrictions."))
            return False

        return True

    def __write_changes(self):

        try:
            soum = DatabaseUtils.working_l2_code()

            layer = LayerUtils.layer_by_data_source("s"+soum, "ca_tmp_parcel")
            if layer is None:
                layer = LayerUtils.load_layer_by_name("ca_tmp_parcel", "parcel_id", soum)

            request = QgsFeatureRequest()
            request.setFilterExpression("maintenance_case = " + str(self.maintenance_case.id))
            iterator = layer.getFeatures(request)

            for feature in iterator:
                point = feature.geometry().centroid()
                break

            srid = PluginUtils.utm_srid_from_point(point.asPoint())

            parcels_to_replace_geometry = self.session.query(CaTmpParcel). \
                filter(CaTmpParcel.parcel_id == CaParcel.parcel_id). \
                filter(CaTmpParcel.maintenance_case == self.maintenance_case.id).all()

            for tmp_parcel in parcels_to_replace_geometry:
                parcel_replace = self.session.query(CaParcel).get(tmp_parcel.parcel_id)
                # parcel_replace.geometry = tmp_parcel.geometry

                #buildings that intersect
                buildings_to_be_inserted_c = self.session.query(CaTmpBuilding)\
                    .filter(CaTmpBuilding.geometry.ST_Intersects(tmp_parcel.geometry)).count()
                if buildings_to_be_inserted_c != 0:
                    buildings_to_be_inserted = self.session.query(CaTmpBuilding)\
                        .filter(CaTmpBuilding.geometry.ST_Intersects(tmp_parcel.geometry)).all()

                    for building in buildings_to_be_inserted:

                        building_insert = CaBuilding()
                        building_insert.building_no = building.building_no
                        building_insert.geo_id = building.geo_id
                        building_insert.area_m2 = building.area_m2
                        building_insert.address_khashaa = building.address_khashaa
                        building_insert.address_streetname = building.address_streetname
                        building_insert.address_neighbourhood = building.address_neighbourhood
                        building_insert.valid_from = DatabaseUtils.convert_date(self.completion_date_edit.date())
                        building_insert.geometry = building.geometry

                        building_update = self.session.query(CaBuilding).get(building.building_id)
                        if building_update:
                            building_update.valid_till = DatabaseUtils.convert_date(self.completion_date_edit.date())

                        self.session.add(building_insert)

                self.session.query(CaTmpParcel). \
                    filter(CaTmpParcel.maintenance_case == self.maintenance_case.id). \
                    filter(CaTmpParcel.parcel_id == tmp_parcel.parcel_id).delete()

            buildings_to_replace_geometry = self.session.query(CaTmpBuilding) \
                .filter(CaTmpBuilding.building_id == CaBuilding.building_id) \
                .filter(CaTmpBuilding.maintenance_case == self.maintenance_case.id).all()

            for tmp_building in buildings_to_replace_geometry:
                building_replace = self.session.query(CaBuilding).get(tmp_building.building_id)
                building_replace.geometry = tmp_building.geometry

                self.session.query(CaTmpBuilding). \
                    filter(CaTmpBuilding.maintenance_case == self.maintenance_case.id). \
                    filter(CaTmpBuilding.building_id == tmp_building.building_id).delete()

            historical_buildings = self.session.query(CaBuilding) \
                .filter(CaBuilding.geometry.ST_Contains(CaTmpBuilding.geometry.ST_Buffer(-0.005))) \
                .filter(CaTmpBuilding.maintenance_case == self.maintenance_case.id) \
                .filter(CaBuilding.geometry.ST_Area() != CaTmpBuilding.geometry.ST_Area()).all()

            for building in historical_buildings:
                building.valid_till = DatabaseUtils.convert_date(self.completion_date_edit.date())

            buildings_to_be_inserted_count = self.session.query(CaTmpBuilding) \
                .filter(CaTmpBuilding.maintenance_case == self.maintenance_case.id).count()

            if buildings_to_be_inserted_count != 0:
                print self.maintenance_case.id

                buildings_to_be_inserted_c = self.session.query(CaTmpBuilding) \
                    .filter(CaTmpBuilding.maintenance_case == self.maintenance_case.id) \
                    .filter(CaTmpParcel.geometry.ST_Intersects(CaTmpBuilding.geometry)).count()
                print buildings_to_be_inserted_c

                buildings_to_be_inserted = self.session.query(CaTmpBuilding) \
                    .filter(CaTmpBuilding.maintenance_case == self.maintenance_case.id) \
                    .filter(CaTmpParcel.geometry.ST_Intersects(CaTmpBuilding.geometry)).all()
                    # .filter(CaTmpBuilding.building_id.startswith(str(self.maintenance_case.id) + "-"))\
                    # .filter(~CaTmpParcel.parcel_id.startswith(str(self.maintenance_case.id) + '-'))

                for tmp_building in buildings_to_be_inserted:
                    building_insert = CaBuilding()
                    building_insert.geo_id = tmp_building.geo_id
                    building_insert.area_m2 = tmp_building.area_m2
                    building_insert.address_khashaa = tmp_building.address_khashaa
                    building_insert.address_streetname = tmp_building.address_streetname
                    building_insert.address_neighbourhood = tmp_building.address_neighbourhood
                    building_insert.valid_from = DatabaseUtils.convert_date(self.completion_date_edit.date())
                    building_insert.geometry = tmp_building.geometry
                    # self.maintenance_case.buildings.append(building_insert)

                    # self.session.add(building_insert)

            # delete tmp parcels

            applications = self.session.query(CtApplication).filter(CtApplication.maintenance_case == self.maintenance_case.id).all()

            for application in applications:

                count = application.statuses.filter(CtApplicationStatus.status == Constants.APP_STATUS_UPDATED).count()
                if count > 0:
                    continue

                app_status = CtApplicationStatus()
                app_status.status = Constants.APP_STATUS_UPDATED
                user = DatabaseUtils.current_user()
                app_status.next_officer_in_charge = user.user_name_real
                app_status.officer_in_charge = user.user_name_real
                current_date = QDate.currentDate()
                app_status.status_date = PluginUtils.convert_qt_date_to_python(current_date)
                app_status.application_ref = application

            self.commit()

        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    @pyqtSlot()
    def zoom_to_selected_clicked(self):

        selected_item = self.maintenance_objects_twidget.selectedItems()[0]

        parcel_id = selected_item.data(0, Qt.UserRole)
        if selected_item is None:
            return

        if selected_item.data(0, Qt.UserRole + 1) == Constants.CASE_PARCEL_IDENTIFIER:
            # parcel_layer = LayerUtils.layer_by_data_source("s" + self.maintenance_soum, "ca_tmp_parcel")
            selection_features = []

            # for f in LayerUtils.where(parcel_layer, "parcel_id={0}".format(selected_item.data(0, Qt.UserRole))):
            #     selection_features.append(f.id())
            #
            # parcel_layer.setSelectedFeatures(selection_features)
            #
            # self.plugin.iface.mapCanvas().zoomToSelected(parcel_layer)


            parcel_layer = LayerUtils.layer_by_data_source("s" + DatabaseUtils.current_working_soum_schema(), "ca_tmp_parcel")

            restrictions = DatabaseUtils.working_l2_code()
            if parcel_layer is None:
                parcel_layer = LayerUtils.load_layer_by_name("ca_tmp_parcel", "parcel_id", restrictions)

            exp_string = ""

            if exp_string == "":
                exp_string = "parcel_id = \'" + parcel_id + "\'"
            else:
                exp_string += " or parcel_id = \'" + parcel_id + "\'"

            request = QgsFeatureRequest()
            request.setFilterExpression(exp_string)

            feature_ids = []
            iterator = parcel_layer.getFeatures(request)

            for feature in iterator:
                feature_ids.append(feature.id())

            if len(feature_ids) == 0:
                self.error_label.setText(self.tr("No parcel assigned"))

            parcel_layer.setSelectedFeatures(feature_ids)
            self.plugin.iface.mapCanvas().zoomToSelected(parcel_layer)

        elif selected_item.data(0, Qt.UserRole + 1) == Constants.CASE_BUILDING_IDENTIFIER:
            # building_layer = LayerUtils.layer_by_data_source("s" + self.maintenance_soum, "ca_tmp_building")
            # selection_features = []
            #
            # for f in LayerUtils.where(building_layer, "building_id={0}".format(selected_item.data(0, Qt.UserRole))):
            #     selection_features.append(f.id())
            #
            # building_layer.setSelectedFeatures(selection_features)
            #
            # self.plugin.iface.mapCanvas().zoomToSelected(building_layer)
            building_id = selected_item.data(0, Qt.UserRole)

            building_layer = LayerUtils.layer_by_data_source("s" + DatabaseUtils.current_working_soum_schema(), "ca_tmp_building")

            restrictions = DatabaseUtils.working_l2_code()
            if building_layer is None:
                building_layer = LayerUtils.load_layer_by_name("ca_tmp_building", "building_id", restrictions)

            exp_string = ""

            if exp_string == "":
                exp_string = "building_id = \'" + building_id + "\'"
            else:
                exp_string += " or building_id = \'" + building_id + "\'"

            request = QgsFeatureRequest()
            request.setFilterExpression(exp_string)

            feature_ids = []
            iterator = building_layer.getFeatures(request)

            for feature in iterator:
                feature_ids.append(feature.id())

            if len(feature_ids) == 0:
                self.error_label.setText(self.tr("No building assigned"))

                building_layer.setSelectedFeatures(feature_ids)
            self.plugin.iface.mapCanvas().zoomToSelected(building_layer)

    @pyqtSlot(QPoint)
    def on_maintenance_objects_twidget_customContextMenuRequested(self, point):

        point = self.maintenance_objects_twidget.viewport().mapToGlobal(point)
        self.menu.exec_(point)

    @pyqtSlot()
    def on_help_button_clicked(self):

        os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/finalize_case.htm")

    @pyqtSlot(QTableWidgetItem)
    def on_maintenance_objects_twidget_itemClicked(self, item):

        print item

    @pyqtSlot()
    def on_maintenance_objects_twidget_itemSelectionChanged(self):

        self.street_name_edit.clear()
        self.khashaa_edit.clear()
        current_item = self.maintenance_objects_twidget.selectedItems()[0]
        object_id = current_item.data(0, Qt.UserRole)
        object_type = current_item.data(0, Qt.UserRole + 1)
        try:
            if object_id != None:
                if object_type == "parcel":
                    tmp_parcel = self.session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == object_id).one()
                    self.street_name_edit.setText(tmp_parcel.address_streetname)
                    self.khashaa_edit.setText(tmp_parcel.address_khashaa)
                elif object_type == "building":
                    tmp_parcel = self.session.query(CaTmpBuilding).filter(CaTmpBuilding.building_id == object_id).one()
                    self.street_name_edit.setText(tmp_parcel.address_streetname)
                    self.khashaa_edit.setText(tmp_parcel.address_khashaa)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    @pyqtSlot()
    def on_address_insert_button_clicked(self):

        session = SessionHandler().session_instance()
        current_item = self.maintenance_objects_twidget.selectedItems()[0]
        object_id = current_item.data(0, Qt.UserRole)
        object_type = current_item.data(0, Qt.UserRole + 1)
        try:
            if object_id != None:
                if object_type == "parcel":
                    tmp_parcel = session.query(CaTmpParcel).filter(CaTmpParcel.parcel_id == object_id).one()
                    tmp_parcel.address_streetname = self.street_name_edit.text()
                    tmp_parcel.address_khashaa = self.khashaa_edit.text()
                    session.add(tmp_parcel)
                elif object_type == "building":
                    tmp_building = session.query(CaTmpBuilding).filter(CaTmpBuilding.building_id == object_id).one()
                    tmp_building.address_streetname = self.street_name_edit.text()
                    tmp_building.address_khashaa = self.khashaa_edit.text()
                    session.add(tmp_building)
            session.commit()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    @pyqtSlot(str)
    def on_street_name_edit_textChanged(self, text):

        self.street_name_edit.setStyleSheet(self.styleSheet())
        cap_value = self.__capitalize_first_letter(text)
        self.street_name_edit.setText(cap_value)
        if not self.__validate_street_name(cap_value):
            self.street_name_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    @pyqtSlot(str)
    def on_khashaa_edit_textChanged(self, text):

        self.khashaa_edit.setStyleSheet(self.styleSheet())
        if not self.__validate_apartment_number(text, self.tr("Khashaa")):
            self.khashaa_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

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

    def __validate_apartment_number(self, number, object_name):

        if len(number) == 0:
            return True

        # Apartment-number should start with a number and contain only one letter
        first_number = number[0]
        letter = number[-1]
        reg = QRegExp("[0-9]")
        result = reg.exactMatch(first_number)

        if not result:
            self.error_label.setText(self.tr("{0} string contains not just numbers.").format(object_name))
            return False

        if letter not in Constants.LOWER_CASE_MONGOLIAN and not letter.isdigit():
            self.error_label.setText(self.tr("{0} number contains wrong letters.").format(object_name))
            return False

        count = 0
        for letter in number:
            if letter in Constants.LOWER_CASE_MONGOLIAN:
                count += 1

        if count > 1:
            self.error_label.setText(self.tr("{0} number contains more than one letter.").format(object_name))
            return False

        return True

    def __setup_address_fill(self):

        khaskhaa_list = []
        street_list = []
        try:
            street_list = self.session.query(CaTmpParcel.address_streetname).order_by(
                    CaTmpParcel.address_streetname.desc()).all()

            khaskhaa_list = self.session.query(CaTmpParcel.address_khashaa).order_by(
                    CaTmpParcel.address_khashaa.desc()).all()
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
        self.street_name_edit.setCompleter(self.streetCompleter)

        khaskhaa_model = QStringListModel(khaskhaa_slist)
        self.khaskhaa_proxy_model = QSortFilterProxyModel()
        self.khaskhaa_proxy_model.setSourceModel(khaskhaa_model)
        self.khaskhaaCompleter = QCompleter(self.khaskhaa_proxy_model, self,
                                            activated=self.on_khaskhaa_completer_activated)
        self.khaskhaaCompleter.setCompletionMode(QCompleter.PopupCompletion)
        self.khashaa_edit.setCompleter(self.khaskhaaCompleter)

        self.street_name_edit.textEdited.connect(self.streetProxyModel.setFilterFixedString)
        self.khashaa_edit.textEdited.connect(self.khaskhaa_proxy_model.setFilterFixedString)

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