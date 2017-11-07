import os

__author__ = 'ankhbold'
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_, extract
from ..view.Ui_ParcelRecordDialog import *
from ..utils.PluginUtils import *
from ..utils.SessionHandler import SessionHandler
from ..model.CaParcel import *
from ..model.CtDecisionApplication import *
from ..model.CtDecision import *
from ..model.AuLevel3 import *
from ..model.CaBuilding import *
from ..model.VaTypeSource import *
from ..model.VaTypeLanduseBuilding import *
from ..model.VaTypeMaterial import *
from ..model.VaTypeHeat import *
from ..model.VaTypeStove import *
from ..model.VaTypeStatusBuilding import *
from ..model.VaInfoHomeParcel import *
from ..model.VaInfoHomePurchase import *
from ..model.VaTypePurchaseOrLease import *
from ..model.VaInfoHomeLease import *
from ..model.VaInfoHomeBuilding import *
from ..model.VaTypeCrop import *
from ..model.VaTypeDesign import *
from ..model.VaTypeESystem import *
from ..model.VaTypeIrrigation import *
from ..model.VaInfoAgriculture import *
from ..model.VaInfoAgricultureOther import *
from ..model.VaInfoIndustrialProduct import *
from ..model.VaTypeProduct import *
from ..model.VaTypeProductTime import *
from ..model.VaTypeIndustrialProcess import *

class ParcelRecordDialog(QDialog, Ui_ParcelRecordDialog):

    def __init__(self, parcel_type, register_no,parcel_id, record, parent=None):

        super(ParcelRecordDialog,  self).__init__(parent)
        self.setupUi(self)
        self.parcel_type = parcel_type
        self.parcel_id = parcel_id
        self.register_no = register_no
        self.record = record
        self.cancel_button.clicked.connect(self.reject)
        self.__setup_validators()
        self.__set_visible_tabs()
        self.__parcel_populate()
        self.home_purchase_rbutton.setChecked(True)
        self.b_status_good_rbutton.setChecked(True)
        self.__setup_validators()
        self.__setup_purchase_widget()
        self.session = SessionHandler().session_instance()
        self.year_sbox.setMinimum(1950)
        self.year_sbox.setMaximum(2200)
        self.year_sbox.setSingleStep(1)
        self.year_sbox.setValue(QDate.currentDate().year())
        self.cost_year_checkbox.setChecked(True)
        self.side_fence_1_2_rbutton.setChecked(True)
        self.quarter_gbox.setDisabled(True)
        self.electricity_yes_rbutton.setChecked(True)
        self.heating_yes_rbutton.setChecked(True)
        self.water_yes_rbutton.setChecked(True)
        self.sewage_yes_rbutton.setChecked(True)
        self.well_yes_rbutton.setChecked(True)
        self.finance_yes_rbutton.setChecked(True)
        self.phone_yes_rbutton.setChecked(True)
        self.flood_yes_rbutton.setChecked(True)
        self.plot_yes_rbutton.setChecked(True)
        self.slope_yes_rbutton.setChecked(True)
        if self.parcel_type == 10:
            self.__setup_mapping()
        elif self.parcel_type == 20:
            self.__setup_mapping_commercial()
        elif self.parcel_type == 30:
            self.__setup_mapping_industrial()
        elif self.parcel_type == 40:
            self.__setup_mapping_agriculture()

    @pyqtSlot(int)
    def on_cost_year_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.quarter_gbox.setEnabled(False)
            self.q1_checkbox.setChecked(False)
            self.q2_checkbox.setChecked(False)
            self.q3_checkbox.setChecked(False)
            self.q4_checkbox.setChecked(False)
        else:
            self.quarter_gbox.setEnabled(True)

    @pyqtSlot(int)
    def on_q1_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.q2_checkbox.setEnabled(True)
            self.q3_checkbox.setEnabled(False)
            self.q4_checkbox.setEnabled(False)
            self.q3_checkbox.setChecked(False)
            self.q4_checkbox.setChecked(False)
        else:
            self.q1_checkbox.setEnabled(True)
            self.q2_checkbox.setEnabled(True)
            self.q3_checkbox.setEnabled(True)
            self.q4_checkbox.setEnabled(True)

    @pyqtSlot(int)
    def on_q2_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.q1_checkbox.setEnabled(True)
            self.q3_checkbox.setEnabled(True)
            self.q4_checkbox.setEnabled(False)
            self.q4_checkbox.setChecked(False)
        else:
            self.q1_checkbox.setEnabled(True)
            self.q2_checkbox.setEnabled(True)
            self.q3_checkbox.setEnabled(True)
            self.q4_checkbox.setEnabled(True)

    @pyqtSlot(int)
    def on_q3_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.q2_checkbox.setEnabled(True)
            self.q4_checkbox.setEnabled(True)
            self.q1_checkbox.setEnabled(False)
            self.q1_checkbox.setChecked(False)
        else:
            self.q1_checkbox.setEnabled(True)
            self.q2_checkbox.setEnabled(True)
            self.q3_checkbox.setEnabled(True)
            self.q4_checkbox.setEnabled(True)

    @pyqtSlot(int)
    def on_q4_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.q3_checkbox.setEnabled(True)
            self.q2_checkbox.setEnabled(False)
            self.q1_checkbox.setEnabled(False)
            self.q2_checkbox.setChecked(False)
            self.q1_checkbox.setChecked(False)
        else:
            self.q1_checkbox.setEnabled(True)
            self.q2_checkbox.setEnabled(True)
            self.q3_checkbox.setEnabled(True)
            self.q4_checkbox.setEnabled(True)

    def __setup_purchase_widget(self):

        self.purchase_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.purchase_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.purchase_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.lease_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.lease_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lease_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.home_building_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.home_building_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.home_building_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        #commercial
        self.c_purchase_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.c_purchase_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.c_purchase_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.c_lease_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.c_lease_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.c_lease_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.c_building_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.c_building_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.c_building_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        #industrial
        self.i_purchase_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.i_purchase_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.i_purchase_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.i_lease_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.i_lease_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.i_lease_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.i_building_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.i_building_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.i_building_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        #agricalture
        self.a_purchase_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.a_purchase_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.a_purchase_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.a_lease_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.a_lease_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.a_lease_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.a_building_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.a_building_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.a_building_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.agriculture_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.agriculture_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.agriculture_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.a_other_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.a_other_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.a_other_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.i_product_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.i_product_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.i_product_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def __setup_validators(self):

        self.numbers_validator = QRegExpValidator(QRegExp("[1-9][0-9]+\\.[0-9]{3}"), None)
        self.int_validator = QRegExpValidator(QRegExp("[0-9][0-9]"), None)

        self.purchase_price_edit.setValidator(self.numbers_validator)
        self.lease_rent_edit.setValidator(self.numbers_validator)
        self.purchase_area_edit.setValidator(self.numbers_validator)
        self.lease_area_edit.setValidator(self.numbers_validator)
        self.building_area_edit.setValidator(self.numbers_validator)
        self.lease_duration_edit.setValidator(self.int_validator)
        self.lease_area_edit.setValidator(self.numbers_validator)
        self.lease_rent_edit.setValidator(self.numbers_validator)

        self.electricity_distancel_edit.setValidator(self.numbers_validator)
        self.electricity_connection_cost_edit.setValidator(self.numbers_validator)
        self.central_heat_distancel_edit.setValidator(self.numbers_validator)
        self.central_heat_connection_cost_edit.setValidator(self.numbers_validator)

        self.water_distancel_edit.setValidator(self.numbers_validator)
        self.water_connection_cost_edit.setValidator(self.numbers_validator)
        self.sewage_distancel_edit.setValidator(self.numbers_validator)
        self.sewage_connection_cost_edit.setValidator(self.numbers_validator)
        self.well_distancel_edit.setValidator(self.numbers_validator)
        self.phone_distancel_edit.setValidator(self.numbers_validator)
        self.flood_channel_distancel_edit.setValidator(self.numbers_validator)
        self.vegetable_plot_size_edit.setValidator(self.numbers_validator)

        self.a_area_edit.setValidator(self.numbers_validator)
        self.a_costs_edit.setValidator(self.numbers_validator)
        self.a_net_profit_edit.setValidator(self.numbers_validator)
        self.a_yield_edit.setValidator(self.numbers_validator)
        self.a_profit_edit.setValidator(self.numbers_validator)

        self.a_other_price_edit.setValidator(self.numbers_validator)

        self.i_cost_item_edit.setValidator(self.numbers_validator)
        self.i_income_item_edit.setValidator(self.numbers_validator)

    @pyqtSlot(str)
    def on_purchase_area_edit_textChanged(self, text):

        session = SessionHandler().session_instance()
        self.numbers_validator = QRegExpValidator(QRegExp("[1-9][0-9]+\\.[0-9]{3}"), None)
        self.purchase_area_edit.setValidator(self.numbers_validator)
        parcel = session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_id).one()
        if parcel.documented_area_m2 == None:
            area = parcel.area_m2
        else:
            area = parcel.documented_area_m2
        if text == "":
            self.purchase_area_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            return
        if float(text) > area:
            self.purchase_area_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            return
        else:
            self.purchase_area_edit.setStyleSheet(self.styleSheet())

    @pyqtSlot(str)
    def on_lease_area_edit_textChanged(self, text):

        session = SessionHandler().session_instance()
        self.numbers_validator = QRegExpValidator(QRegExp("[1-9][0-9]+\\.[0-9]{3}"), None)
        self.lease_area_edit.setValidator(self.numbers_validator)
        parcel = session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_id).one()
        if parcel.documented_area_m2 == None:
            area = parcel.area_m2
        else:
            area = parcel.documented_area_m2
        if text == "":
            self.lease_area_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            return
        if float(text) > area:
            self.lease_area_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            return
        else:
            self.lease_area_edit.setStyleSheet(self.styleSheet())

    @pyqtSlot(str)
    def on_building_area_edit_textChanged(self, text):

        session = SessionHandler().session_instance()
        self.numbers_validator = QRegExpValidator(QRegExp("[1-9][0-9]+\\.[0-9]{3}"), None)
        self.building_area_edit.setValidator(self.numbers_validator)
        building_id = self.building_no_cbox.itemData(self.building_no_cbox.currentIndex())
        building = session.query(CaBuilding).filter(CaBuilding.building_id == building_id).one()

        area = building.area_m2
        if text == "":
            self.building_area_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            return
        if float(text) > area:
            self.building_area_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            return
        else:
            self.building_area_edit.setStyleSheet(self.styleSheet())

    @pyqtSlot(str)
    def on_purchase_price_edit_textChanged(self, text):

         if text == "":
            self.purchase_price_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            return
         else:
            self.purchase_price_edit.setStyleSheet(self.styleSheet())
            value = round(float(self.purchase_price_edit.text())/float(self.purchase_area_edit.text()))
            self.purchase_price_if_m2.setText(str(value))

    @pyqtSlot(str)
    def on_lease_rent_edit_textChanged(self, text):

         if text == "":
            self.lease_rent_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            return
         else:
            self.lease_rent_edit.setStyleSheet(self.styleSheet())
            value = round(float(self.lease_rent_edit.text())/float(self.lease_area_edit.text()))
            self.lease_rent_of_m2.setText(str(value))

    #agricalture
    @pyqtSlot(str)
    def on_a_price_edit_textChanged(self, text):

        number = text
        try:
            number = float(number)
        except Exception:
            QtGui.QMessageBox.about(self, 'Error','Input can only be a number')
            return
        self.a_price_edit.setStyleSheet(self.styleSheet())
        value = round(float(self.a_price_edit.text())/float(self.a_purchase_area_edit.text()))
        self.a_purchase_price_if_m2.setText(str(value))

    @pyqtSlot(str)
    def on_a_lease_rent_edit_textChanged(self, text):

        number = text
        try:
            number = float(number)
        except Exception:
            QtGui.QMessageBox.about(self, 'Error','Input can only be a number')
            return
        self.a_lease_rent_edit.setStyleSheet(self.styleSheet())
        value = round(float(self.a_lease_rent_edit.text())/float(self.a_lease_area_edit.text()))
        self.a_lease_rent_of_m2.setText(str(value))

    #industrial
    @pyqtSlot(str)
    def on_i_purchase_price_edit_textChanged(self, text):

        number = text
        try:
            number = float(number)
        except Exception:
            QtGui.QMessageBox.about(self, 'Error','Input can only be a number')
            return
        self.i_purchase_price_edit.setStyleSheet(self.styleSheet())
        value = round(float(self.i_purchase_price_edit.text())/float(self.i_purchase_area_edit.text()))
        self.i_purchase_price_if_m2.setText(str(value))

    @pyqtSlot(str)
    def on_i_lease_month_edit_textChanged(self, text):

        number = text
        try:
            number = float(number)
        except Exception:
            QtGui.QMessageBox.about(self, 'Error','Input can only be a number')
            return
        self.i_lease_month_edit.setStyleSheet(self.styleSheet())
        value = round(float(self.i_lease_month_edit.text())/float(self.i_lease_area_edit.text()))
        self.i_lease_rent_of_m2.setText(str(value))

    #commercial
    @pyqtSlot(str)
    def on_c_purchase_price_edit_textChanged(self, text):

        number = text
        try:
            number = float(number)
        except Exception:
            QtGui.QMessageBox.about(self, 'Error','Input can only be a number')
            return
        self.c_purchase_price_edit.setStyleSheet(self.styleSheet())
        value = round(float(self.c_purchase_price_edit.text())/float(self.c_purchase_area_edit.text()))
        self.c_purchase_price_if_m2.setText(str(value))

    @pyqtSlot(str)
    def on_c_lease_expenses_edit_textChanged(self, text):

        number = text
        try:
            number = float(number)
        except Exception:
            QtGui.QMessageBox.about(self, 'Error','Input can only be a number')
            return
        self.c_lease_expenses_edit.setStyleSheet(self.styleSheet())
        value = round(float(self.c_lease_expenses_edit.text())/float(self.c_lease_area_edit.text()))
        self.c_lease_rent_of_m2.setText(str(value))

    def __setup_mapping_commercial(self):

        session = SessionHandler().session_instance()
        if self.record.register_no == None:
            return
        self.register_no = self.record.register_no
        #Detail
        self.c_cadastreId_edit.setText(self.record.parcel_id)
        self.c_registration_date.setDateTime(QDateTime.fromString(self.record.info_date.strftime(Constants.PYTHON_DATE_FORMAT),
                                                                Constants.DATABASE_DATE_FORMAT))

        if self.record.purchase_or_lease_type_ref:
            if self.record.purchase_or_lease_type_ref.code == 10:
                self.c_purchase_rbutton.setChecked(True)
            else:
                self.c_lease_rbutton.setChecked(True)
        self.c_calculated_area_edit.setText(str(self.record.area_m2))

        if self.record.app_type_ref:
            self.c_right_type_cbox.setCurrentIndex(self.c_right_type_cbox.findData(self.record.app_type_ref.code))
        if self.record.source_type_ref:
            self.c_source_cbox.setCurrentIndex(self.c_source_cbox.findData(self.record.source_type_ref.code))

        self.c_decision_date_edit.setText(self.record.decision_date)
        self.c_duration_edit.setText(str(self.record.approved_duration))

        register_no = self.record.register_no
        parts_register_no = register_no.split("-")

        self.commercial_num_first_edit.setText(parts_register_no[0])
        self.commercial_num_type_edit.setText(parts_register_no[1])
        self.commercial_num_middle_edit.setText(parts_register_no[2])
        self.commercial_num_last_edit.setText(parts_register_no[3])

        if self.record.other_info != None:
            self.c_other_info_edit.setText(self.record.other_info)

        #Purchase
        purchase_count = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.record.register_no).count()
        if self.c_purchase_rbutton.isChecked():
            if purchase_count != 0:

                purchase = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.record.register_no).one()
                if purchase.landuse_ref:
                    self.c_purchase_use_type_cbox.setCurrentIndex(self.c_purchase_use_type_cbox.findData(purchase.landuse_ref.code))
                self.c_purchase_area_edit.setText(str(purchase.area_m2))
                self.c_purchase_dateEdit.setDateTime(QDateTime.fromString(purchase.purchase_date.strftime(Constants.PYTHON_DATE_FORMAT),
                                                                        Constants.DATABASE_DATE_FORMAT))
                self.c_purchase_price_edit.setText(str(purchase.price))
                self.c_purchase_price_if_m2.setText(str(purchase.price_m2))

                self.__commercial_purchase_add()
        else:
        #lease
            lease_count = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.record.register_no).count()
            if lease_count != 0:

                lease = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.record.register_no).one()

                if lease.landuse_ref:
                    self.c_lease_use_type_cbox.setCurrentIndex(self.c_lease_use_type_cbox.findData(lease.landuse_ref.code))
                self.c_lease_area_edit.setText(str(lease.area_m2))
                self.c_lease_dateEdit.setDateTime(QDateTime.fromString(lease.lease_date.strftime(Constants.PYTHON_DATE_FORMAT),
                                                                     Constants.DATABASE_DATE_FORMAT))
                self.c_lease_duration_edit.setText(str(lease.duration_month))
                self.c_lease_expenses_edit.setText(str(lease.monthly_rent))
                self.c_lease_rent_of_m2.setText(str(lease.rent_m2))

                self.__commercial_lease_add()

        building_count = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.record.register_no).count()
        if building_count != 0:
            building = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.record.register_no).all()
            for build in building:
                landuse = session.query(VaTypeLanduseBuilding).filter(VaTypeLanduseBuilding.code == build.landuse_building).one()
                landuse_item = QTableWidgetItem(landuse.description)
                landuse_item.setData(Qt.UserRole, landuse.code)
                building_text = build.building_id[-3:]
                building_item = QTableWidgetItem(str(building_text))
                building_item.setData(Qt.UserRole, build.building_id)
                material = session.query(VaTypeMaterial).filter(VaTypeMaterial.code == build.material_type).one()
                material_item = QTableWidgetItem(material.description)
                material_item.setData(Qt.UserRole, material.code)
                design = session.query(VaTypeDesign).filter(VaTypeDesign.code == build.design_type).one()
                design_item = QTableWidgetItem(design.description)
                design_item.setData(Qt.UserRole, design.code)
                esystem = session.query(VaTypeESystem).filter(VaTypeESystem.code == build.building_esystem).one()
                esystem_item = QTableWidgetItem(esystem.description)
                esystem_item.setData(Qt.UserRole, esystem.code)
                status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == build.building_status).one()
                status_item = QTableWidgetItem(status.description)
                status_item.setData(Qt.UserRole, status.code)

                area_item = QTableWidgetItem(str(build.area_m2))
                area_item.setData(Qt.UserRole, build.area_m2)
                construction_item = QTableWidgetItem(str(build.construction_year))
                construction_item.setData(Qt.UserRole, build.construction_year)
                floor_item = QTableWidgetItem(str(build.floor))
                floor_item.setData(Qt.UserRole, build.floor)
                room_item = QTableWidgetItem(str(build.room))
                room_item.setData(Qt.UserRole, build.room)

                row = self.c_building_twidget.rowCount()
                self.c_building_twidget.insertRow(row)

                self.c_building_twidget.setItem(row, 0, building_item)
                self.c_building_twidget.setItem(row, 1, landuse_item)
                self.c_building_twidget.setItem(row, 2, area_item)
                self.c_building_twidget.setItem(row, 3, design_item)
                self.c_building_twidget.setItem(row, 4, material_item)
                self.c_building_twidget.setItem(row, 5, floor_item)
                self.c_building_twidget.setItem(row, 6, room_item)
                self.c_building_twidget.setItem(row, 7, construction_item)
                self.c_building_twidget.setItem(row, 8, esystem_item)
                self.c_building_twidget.setItem(row, 9, status_item)

    def __setup_mapping_industrial(self):

        session = SessionHandler().session_instance()
        if self.record.register_no == None:
            return
        self.register_no = self.record.register_no
        #Detail
        self.i_cadastreid_edit.setText(self.record.parcel_id)
        self.i_registration_date.setDateTime(QDateTime.fromString(self.record.info_date.strftime(Constants.PYTHON_DATE_FORMAT),
                                                                Constants.DATABASE_DATE_FORMAT))

        if self.record.purchase_or_lease_type_ref:
            if self.record.purchase_or_lease_type_ref.code == 10:
                self.i_purchase_rbutton.setChecked(True)
            else:
                self.i_lease_rbutton.setChecked(True)
        self.i_calculated_area_edit.setText(str(self.record.area_m2))

        if self.record.app_type_ref:
            self.i_right_type_cbox.setCurrentIndex(self.i_right_type_cbox.findData(self.record.app_type_ref.code))
        if self.record.source_type_ref:
            self.i_source_cbox.setCurrentIndex(self.i_source_cbox.findData(self.record.source_type_ref.code))

        self.i_decision_date_edit.setText(str(self.record.decision_date))
        self.i_duration_edit.setText(str(self.record.approved_duration))

        register_no = self.record.register_no
        parts_register_no = register_no.split("-")

        self.industrial_num_first_edit.setText(parts_register_no[0])
        self.industrial_num_type_edit.setText(parts_register_no[1])
        self.industrial_num_middle_edit.setText(parts_register_no[2])
        self.industrial_num_last_edit.setText(parts_register_no[3])

        if self.record.other_info != None:
            self.i_other_info_edit.setText(self.record.other_info)

        #Purchase
        purchase_count = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.record.register_no).count()
        if self.i_purchase_rbutton.isChecked():
            if purchase_count != 0:

                purchase = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.record.register_no).one()
                if purchase.landuse_ref:
                    self.i_purchase_use_type_cbox.setCurrentIndex(self.i_purchase_use_type_cbox.findData(purchase.landuse_ref.code))
                self.i_purchase_area_edit.setText(str(purchase.area_m2))
                self.i_purchase_date_edit.setDateTime(QDateTime.fromString(purchase.purchase_date.strftime(Constants.PYTHON_DATE_FORMAT),
                                                                        Constants.DATABASE_DATE_FORMAT))
                self.i_purchase_price_edit.setText(str(purchase.price))
                self.i_purchase_price_if_m2.setText(str(purchase.price_m2))

                self.__industrial_purchase_add()
        else:
        #lease
            lease_count = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.record.register_no).count()
            if lease_count != 0:
                lease = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.record.register_no).one()
                if lease.landuse_ref:
                    self.i_lease_use_type_cbox.setCurrentIndex(self.i_lease_use_type_cbox.findData(lease.landuse_ref.code))
                self.i_lease_area_edit.setText(str(lease.area_m2))
                self.i_lease_dateEdit.setDateTime(QDateTime.fromString(lease.lease_date.strftime(Constants.PYTHON_DATE_FORMAT),
                                                                     Constants.DATABASE_DATE_FORMAT))
                self.i_lease_duration_edit.setText(str(lease.duration_month))
                self.i_lease_month_edit.setText(str(lease.monthly_rent))
                self.i_lease_rent_of_m2.setText(str(lease.rent_m2))

                self.__industrial_lease_add()

        #building
        building_count = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.record.register_no).count()
        if building_count != 0:
            building = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.record.register_no).all()
            for build in building:
                landuse = session.query(VaTypeLanduseBuilding).filter(VaTypeLanduseBuilding.code == build.landuse_building).one()
                landuse_item = QTableWidgetItem(landuse.description)
                landuse_item.setData(Qt.UserRole, landuse.code)
                building_text = build.building_id[-3:]
                building_item = QTableWidgetItem(str(building_text))
                building_item.setData(Qt.UserRole, build.building_id)
                material = session.query(VaTypeMaterial).filter(VaTypeMaterial.code == build.material_type).one()
                material_item = QTableWidgetItem(material.description)
                material_item.setData(Qt.UserRole, material.code)
                status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == build.building_status).one()
                status_item = QTableWidgetItem(status.description)
                status_item.setData(Qt.UserRole, status.code)

                area_item = QTableWidgetItem(str(build.area_m2))
                area_item.setData(Qt.UserRole, build.area_m2)
                construction_item = QTableWidgetItem(str(build.construction_year))
                construction_item.setData(Qt.UserRole, build.construction_year)
                floor_item = QTableWidgetItem(str(build.floor))
                floor_item.setData(Qt.UserRole, build.floor)
                room_item = QTableWidgetItem(str(build.room))
                room_item.setData(Qt.UserRole, build.room)

                row = self.i_building_twidget.rowCount()
                self.i_building_twidget.insertRow(row)

                self.i_building_twidget.setItem(row, 0, building_item)
                self.i_building_twidget.setItem(row, 1, landuse_item)
                self.i_building_twidget.setItem(row, 2, area_item)
                self.i_building_twidget.setItem(row, 3, material_item)
                self.i_building_twidget.setItem(row, 4, construction_item)
                self.i_building_twidget.setItem(row, 5, floor_item)
                self.i_building_twidget.setItem(row, 6, status_item)

        #product
        product_count = session.query(VaInfoIndustrialProduct).filter(VaInfoIndustrialProduct.register_no == self.record.register_no).count()
        if product_count != 0:
            products = session.query(VaInfoIndustrialProduct).filter(VaInfoIndustrialProduct.register_no == self.record.register_no).all()
            for product in products:
                product_type = session.query(VaTypeProduct).filter(VaTypeProduct.code == product.product).one()
                product_item = QTableWidgetItem(product_type.description)
                product_item.setData(Qt.UserRole, product_type.code)
                time = session.query(VaTypeProductTime).filter(VaTypeProductTime.code == product.product_time).one()
                time_item = QTableWidgetItem(time.description)
                time_item.setData(Qt.UserRole, time.code)
                process = session.query(VaTypeIndustrialProcess).filter(VaTypeIndustrialProcess.code == product.industrial_process).one()
                process_item = QTableWidgetItem(process.description)
                process_item.setData(Qt.UserRole, process.code)

                come_item = QTableWidgetItem(str(product.come_per_item))
                come_item.setData(Qt.UserRole, product.come_per_item)
                cost_item = QTableWidgetItem(str(product.cost_per_item))
                cost_item.setData(Qt.UserRole, product.cost_per_item)
                count_item = QTableWidgetItem(str(product.count_product))
                count_item.setData(Qt.UserRole, product.count_product)
                row = self.i_product_twidget.rowCount()
                self.i_product_twidget.insertRow(row)

                self.i_product_twidget.setItem(row, 0, product_item)
                self.i_product_twidget.setItem(row, 1, come_item)
                self.i_product_twidget.setItem(row, 2, cost_item)
                self.i_product_twidget.setItem(row, 3, count_item)
                self.i_product_twidget.setItem(row, 4, time_item)
                self.i_product_twidget.setItem(row, 5, process_item)

    def __setup_mapping_agriculture(self):

        session = SessionHandler().session_instance()
        if self.record.register_no == None:
            return
        self.register_no = self.record.register_no
        #Detail
        self.a_cadastreId_edit.setText(self.record.parcel_id)
        self.a_registration_date.setDateTime(QDateTime.fromString(self.record.info_date.strftime(Constants.PYTHON_DATE_FORMAT),
                                                                Constants.DATABASE_DATE_FORMAT))

        if self.record.purchase_or_lease_type_ref:
            if self.record.purchase_or_lease_type_ref.code == 10:
                self.a_purchase_rbutton.setChecked(True)
            else:
                self.a_lease_rbutton.setChecked(True)
        self.a_calculated_area_edit.setText(str(self.record.area_m2))

        if self.record.app_type_ref:
            self.a_right_type_cbox.setCurrentIndex(self.a_right_type_cbox.findData(self.record.app_type_ref.code))
        if self.record.source_type_ref:
            self.a_source_cbox.setCurrentIndex(self.a_source_cbox.findData(self.record.source_type_ref.code))

        self.a_decision_date_edit.setText(str(self.record.decision_date))
        self.a_duration_edit.setText(str(self.record.approved_duration))

        register_no = self.record.register_no
        parts_register_no = register_no.split("-")

        self.agriculture_num_first_edit.setText(parts_register_no[0])
        self.agriculture_num_type_edit.setText(parts_register_no[1])
        self.agriculture_num_middle_edit.setText(parts_register_no[2])
        self.agriculture_num_last_edit.setText(parts_register_no[3])

        if self.record.other_info != None:
            self.a_other_info_edit.setText(self.record.other_info)

        #Purchase
        purchase_count = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.record.register_no).count()
        if self.a_purchase_rbutton.isChecked():
            if purchase_count != 0:

                purchase = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.record.register_no).one()

                self.a_purchase_area_edit.setText(str(purchase.area_m2))
                self.a_purchase_dateEdit.setDateTime(QDateTime.fromString(purchase.purchase_date.strftime(Constants.PYTHON_DATE_FORMAT),
                                                                        Constants.DATABASE_DATE_FORMAT))
                self.a_price_edit.setText(str(purchase.price))
                self.a_purchase_price_if_m2.setText(str(purchase.price_m2))

                self.__agricalture_purchase_add()
        else:
        #lease
            lease_count = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.record.register_no).count()
            if lease_count != 0:
                lease = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.record.register_no).one()

                self.a_lease_area_edit.setText(str(lease.area_m2))
                self.a_lease_dateEdit.setDateTime(QDateTime.fromString(lease.lease_date.strftime(Constants.PYTHON_DATE_FORMAT),
                                                                     Constants.DATABASE_DATE_FORMAT))
                self.a_lease_duration_edit.setText(str(lease.duration_month))
                self.a_lease_rent_edit.setText(str(lease.monthly_rent))
                self.a_lease_rent_of_m2.setText(str(lease.rent_m2))

                self.__agricalture_lease_add()

        building_count = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.record.register_no).count()
        if building_count != 0:
            building = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.record.register_no).all()
            for build in building:
                landuse = session.query(VaTypeLanduseBuilding).filter(VaTypeLanduseBuilding.code == build.landuse_building).one()
                landuse_item = QTableWidgetItem(landuse.description)
                landuse_item.setData(Qt.UserRole, landuse.code)
                building_text = build.building_id[-3:]
                building_item = QTableWidgetItem(str(building_text))
                building_item.setData(Qt.UserRole, build.building_id)
                material = session.query(VaTypeMaterial).filter(VaTypeMaterial.code == build.material_type).one()
                material_item = QTableWidgetItem(material.description)
                material_item.setData(Qt.UserRole, material.code)

                area_item = QTableWidgetItem(str(build.area_m2))
                area_item.setData(Qt.UserRole, build.area_m2)
                construction_item = QTableWidgetItem(str(build.construction_year))
                construction_item.setData(Qt.UserRole, build.construction_year)
                price_item = QTableWidgetItem(str(build.price))
                price_item.setData(Qt.UserRole, build.price)

                row = self.a_building_twidget.rowCount()
                self.a_building_twidget.insertRow(row)

                self.a_building_twidget.setItem(row, 0, building_item)
                self.a_building_twidget.setItem(row, 1, landuse_item)
                self.a_building_twidget.setItem(row, 2, area_item)
                self.a_building_twidget.setItem(row, 3, material_item)
                self.a_building_twidget.setItem(row, 4, construction_item)
                self.a_building_twidget.setItem(row, 5, price_item)

        #agriculture

        agriculture_count = session.query(VaInfoAgriculture).filter(VaInfoAgriculture.register_no == self.record.register_no).count()
        if agriculture_count != 0:
            agricultures = session.query(VaInfoAgriculture).filter(VaInfoAgriculture.register_no == self.record.register_no).all()
            for agriculture in agricultures:
                landuse = session.query(ClLanduseType).filter(ClLanduseType.code == agriculture.landuse).one()
                landuse_item = QTableWidgetItem(landuse.description)
                landuse_item.setData(Qt.UserRole, landuse.code)

                crop = session.query(VaTypeCrop).filter(VaTypeCrop.code == agriculture.crop_type).one()
                crop_item = QTableWidgetItem(crop.description)
                crop_item.setData(Qt.UserRole, crop.code)

                area_item = QTableWidgetItem(str(agriculture.area_m2))
                area_item.setData(Qt.UserRole, agriculture.area_m2)
                yield_item = QTableWidgetItem(str(agriculture.yield_ga))
                yield_item.setData(Qt.UserRole, agriculture.yield_ga)
                costs_item = QTableWidgetItem(str(agriculture.costs))
                costs_item.setData(Qt.UserRole, agriculture.costs)
                profit_item = QTableWidgetItem(str(agriculture.profit))
                profit_item.setData(Qt.UserRole, agriculture.profit)
                net_profit_item = QTableWidgetItem(str(agriculture.net_profit))
                net_profit_item.setData(Qt.UserRole, agriculture.net_profit)

                row = self.agriculture_twidget.rowCount()
                self.agriculture_twidget.insertRow(row)

                self.agriculture_twidget.setItem(row, 0, landuse_item)
                self.agriculture_twidget.setItem(row, 1, crop_item)
                self.agriculture_twidget.setItem(row, 2, area_item)
                self.agriculture_twidget.setItem(row, 3, yield_item)
                self.agriculture_twidget.setItem(row, 4, costs_item)
                self.agriculture_twidget.setItem(row, 5, profit_item)
                self.agriculture_twidget.setItem(row, 6, net_profit_item)

        #agriculture other
        agriculture_other_count = session.query(VaInfoAgricultureOther).filter(VaInfoAgricultureOther.register_no == self.record.register_no).count()
        if agriculture_other_count != 0:
            agricultures_other = session.query(VaInfoAgricultureOther).filter(VaInfoAgricultureOther.register_no == self.record.register_no).all()
            for agriculture in agricultures_other:
                irrigation = session.query(VaTypeIrrigation).filter(VaTypeIrrigation.code == agriculture.irrigation).one()
                irrigation_item = QTableWidgetItem(irrigation.description)
                irrigation_item.setData(Qt.UserRole, irrigation.code)

                other_price_item = QTableWidgetItem(str(agriculture.other_price))
                other_price_item.setData(Qt.UserRole, agriculture.other_price)
                other_item = QTableWidgetItem(agriculture.other)
                other_item.setData(Qt.UserRole, agriculture.other)

                row = self.a_other_twidget.rowCount()
                self.a_other_twidget.insertRow(row)

                self.a_other_twidget.setItem(row, 0, irrigation_item)
                self.a_other_twidget.setItem(row, 1, other_price_item)
                self.a_other_twidget.setItem(row, 2, other_item)

    def __setup_mapping(self):

        session = SessionHandler().session_instance()
        if self.record.register_no == None:
            return
        self.register_no = self.record.register_no
        #Detail
        self.cadastreId_edit.setText(self.record.parcel_id)
        self.registration_date.setDateTime(QDateTime.fromString(self.record.info_date.strftime(Constants.PYTHON_DATE_FORMAT),
                                                                Constants.DATABASE_DATE_FORMAT))

        if self.record.purchase_or_lease_type_ref:
            if self.record.purchase_or_lease_type_ref.code == 10:
                self.home_purchase_rbutton.setChecked(True)
            else:
                self.home_lease_rbutton.setChecked(True)
        self.calculated_area_edit.setText(str(self.record.area_m2))

        if self.record.app_type_ref:
            self.right_type_cbox.setCurrentIndex(self.right_type_cbox.findData(self.record.app_type_ref.code))
        if self.record.source_type_ref:
            self.source_cbox.setCurrentIndex(self.source_cbox.findData(self.record.source_type_ref.code))

        self.decision_date_edit.setText(self.record.decision_date)
        self.duration_year_edit.setText(str(self.record.approved_duration))

        register_no = self.record.register_no
        parts_register_no = register_no.split("-")

        self.home_num_first_edit.setText(parts_register_no[0])
        self.home_num_type_edit.setText(parts_register_no[1])
        self.home_num_middle_edit.setText(parts_register_no[2])
        self.home_num_last_edit.setText(parts_register_no[3])

        if self.record.is_electricity:
            self.electricity_yes_rbutton.setChecked(True)
        else:
            self.electricity_no_rbutton.setChecked(True)

        if self.record.electricity_distancel != None:
            self.electricity_distancel_edit.setText(str(float(self.record.electricity_distancel)))

        if self.record.electricity_conn_cost != None:
            self.electricity_connection_cost_edit.setText(str(float(self.record.electricity_conn_cost)))

        if self.record.is_central_heating:
            self.heating_yes_rbutton.setChecked(True)
        else:
            self.heating_no_rbutton.setChecked(False)

        if self.record.central_heating_distancel != None:
            self.central_heat_distancel_edit.setText(str(float(self.record.central_heating_distancel)))

        if self.record.central_heating_conn_cost != None:
            self.central_heat_connection_cost_edit.setText(str(float(self.record.central_heating_conn_cost)))

        if self.record.is_fresh_water:
            self.water_yes_rbutton.setChecked(True)
        else:
            self.water_no_rbutton.setChecked(True)

        if self.record.fresh_water_distancel != None:
            self.water_distancel_edit.setText(str(float(self.record.fresh_water_distancel)))

        if self.record.fresh_water_conn_cost != None:
            self.water_connection_cost_edit.setText(str(float(self.record.fresh_water_conn_cost)))

        if self.record.is_sewage:
            self.sewage_yes_rbutton.setChecked(True)
        else:
            self.sewage_no_rbutton.setChecked(True)

        if self.record.sewage_distancel != None:
            self.sewage_distancel_edit.setText(str(float(self.record.sewage_distancel)))

        if self.record.sewage_conn_cost != None:
            self.sewage_connection_cost_edit.setText(str(float(self.record.sewage_conn_cost)))

        if self.record.is_well:
            self.well_yes_rbutton.setChecked(True)
        else:
            self.water_no_rbutton.setChecked(True)

        if self.record.well_distancel != None:
            self.well_distancel_edit.setText(str(float(self.record.well_distancel)))

        if self.record.is_self_financed_system:
            self.finance_yes_rbutton.setChecked(True)
        else:
            self.finance_no_rbutton.setChecked(True)

        if self.record.is_telephone:
            self.phone_yes_rbutton.setChecked(True)
        else:
            self.phone_no_rbutton.setChecked(True)

        if self.record.telephone_distancel != None:
            self.phone_distancel_edit.setText(str(float(self.record.telephone_distancel)))

        if self.record.is_flood_channel:
            self.flood_yes_rbutton.setChecked(True)
        else:
            self.flood_no_rbutton.setChecked(True)

        if self.record.flood_channel_distancel != None:
            self.flood_channel_distancel_edit.setText(str(float(self.record.flood_channel_distancel)))

        if self.record.is_vegetable_plot:
            self.plot_yes_rbutton.setChecked(True)
        else:
            self.plot_no_rbutton.setChecked(True)

        if self.record.vegetable_plot_size != None:
            self.vegetable_plot_size_edit.setText(str(float(self.record.vegetable_plot_size)))

        if self.record.is_land_slope:
            self.slope_yes_rbutton.setChecked(True)
        else:
            self.slope_no_rbutton.setChecked(True)

        if self.record.other_info != None:
            self.other_information_edit.setText(self.record.other_info)

        #Purchase
        purchase_count = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.record.register_no).count()
        if self.home_purchase_rbutton.isChecked():
            if purchase_count != 0:

                purchase = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.record.register_no).one()
                if purchase.landuse_ref:
                    self.purchase_use_type_cbox.setCurrentIndex(self.purchase_use_type_cbox.findData(purchase.landuse_ref.code))
                self.purchase_area_edit.setText(str(purchase.area_m2))
                self.purchase_dateEdit.setDateTime(QDateTime.fromString(purchase.purchase_date.strftime(Constants.PYTHON_DATE_FORMAT),
                                                                        Constants.DATABASE_DATE_FORMAT))
                self.purchase_price_edit.setText(str(purchase.price))
                self.purchase_price_if_m2.setText(str(purchase.price_m2))

                self.__home_purchase_add()
        else:
        #lease
            lease_count = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.record.register_no).count()

            if lease_count != 0:

                lease = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.record.register_no).one()

                if lease.landuse_ref:
                    self.lease_use_type_cbox.setCurrentIndex(self.lease_use_type_cbox.findData(lease.landuse_ref.code))
                self.lease_area_edit.setText(str(lease.area_m2))
                self.lease_dateEdit.setDateTime(QDateTime.fromString(lease.lease_date.strftime(Constants.PYTHON_DATE_FORMAT),
                                                                     Constants.DATABASE_DATE_FORMAT))
                self.lease_duration_edit.setText(str(lease.duration_month))
                self.lease_rent_edit.setText(str(lease.monthly_rent))
                self.lease_rent_of_m2.setText(str(lease.rent_m2))

                self.__home_lease_add()

        building_count = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.record.register_no).count()
        if building_count != 0:
            building = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.record.register_no).all()

            for build in building:
                landuse = session.query(VaTypeLanduseBuilding).filter(VaTypeLanduseBuilding.code == build.landuse_building).one()
                landuse_item = QTableWidgetItem(landuse.description)
                landuse_item.setData(Qt.UserRole, landuse.code)
                building_text = build.building_id[-3:]
                building_item = QTableWidgetItem(str(building_text))
                building_item.setData(Qt.UserRole, build.building_id)
                stove = session.query(VaTypeStove).filter(VaTypeStove.code == build.stove_type).one()
                stove_item = QTableWidgetItem(stove.description)
                stove_item.setData(Qt.UserRole, stove.code)
                material = session.query(VaTypeMaterial).filter(VaTypeMaterial.code == build.material_type).one()
                material_item = QTableWidgetItem(material.description)
                material_item.setData(Qt.UserRole, material.code)
                design = session.query(VaTypeDesign).filter(VaTypeDesign.code == build.design_type).one()
                design_item = QTableWidgetItem(design.description)
                design_item.setData(Qt.UserRole, design.code)
                heat = session.query(VaTypeHeat).filter(VaTypeHeat.code == build.heat_type).one()
                heat_item = QTableWidgetItem(heat.description)
                heat_item.setData(Qt.UserRole, heat.code)
                status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == build.building_status).one()
                status_item = QTableWidgetItem(status.description)
                status_item.setData(Qt.UserRole, status.code)

                area_item = QTableWidgetItem(str(build.area_m2))
                area_item.setData(Qt.UserRole, build.area_m2)
                construction_item = QTableWidgetItem(str(build.construction_year))
                construction_item.setData(Qt.UserRole, build.construction_year)
                floor_item = QTableWidgetItem(str(build.floor))
                floor_item.setData(Qt.UserRole, build.floor)
                room_item = QTableWidgetItem(str(build.room))
                room_item.setData(Qt.UserRole, build.room)
                status_year_item = QTableWidgetItem(str(build.status_year))
                status_year_item.setData(Qt.UserRole, build.status_year)

                row = self.home_building_twidget.rowCount()
                self.home_building_twidget.insertRow(row)

                self.home_building_twidget.setItem(row, 0, building_item)
                self.home_building_twidget.setItem(row, 1, landuse_item)
                self.home_building_twidget.setItem(row, 2, area_item)
                self.home_building_twidget.setItem(row, 3, design_item)
                self.home_building_twidget.setItem(row, 4, material_item)
                self.home_building_twidget.setItem(row, 5, construction_item)
                self.home_building_twidget.setItem(row, 6, floor_item)
                self.home_building_twidget.setItem(row, 7, room_item)
                self.home_building_twidget.setItem(row, 8, stove_item)
                self.home_building_twidget.setItem(row, 9, heat_item)
                self.home_building_twidget.setItem(row, 10, status_item)
                self.home_building_twidget.setItem(row, 11, status_year_item)


    def __set_visible_tabs(self):

        self.parcel_record_tab_widget.removeTab(self.parcel_record_tab_widget.indexOf(self.home_info_tab))
        self.parcel_record_tab_widget.removeTab(self.parcel_record_tab_widget.indexOf(self.condominium_info_tab))
        self.parcel_record_tab_widget.removeTab(self.parcel_record_tab_widget.indexOf(self.condominium_other_tab))
        self.parcel_record_tab_widget.removeTab(self.parcel_record_tab_widget.indexOf(self.industrial_info_tab))
        self.parcel_record_tab_widget.removeTab(self.parcel_record_tab_widget.indexOf(self.industrial_other_tab))
        self.parcel_record_tab_widget.removeTab(self.parcel_record_tab_widget.indexOf(self.agriculture_info_tab))
        self.parcel_record_tab_widget.removeTab(self.parcel_record_tab_widget.indexOf(self.agriculture_other_tab))
        self.parcel_record_tab_widget.removeTab(self.parcel_record_tab_widget.indexOf(self.infrastructure_other_tab))

        if self.parcel_type == 10:
            self.parcel_record_tab_widget.insertTab(self.parcel_record_tab_widget.count(), self.home_info_tab,
                                                    self.tr("Home Parcel Information"))
            self.parcel_record_tab_widget.insertTab(self.parcel_record_tab_widget.count() + 1, self.infrastructure_other_tab,
                                                    self.tr("Infrastructure Other"))
            self.parcel_record_tab_widget.insertTab(self.parcel_record_tab_widget.count() - 1, self.specia_costs_tab,
                                                    self.tr("Special Costs"))
        elif self.parcel_type == 20:
            self.parcel_record_tab_widget.insertTab(self.parcel_record_tab_widget.count(), self.condominium_info_tab,
                                                    self.tr("Commercial Information"))
            self.parcel_record_tab_widget.insertTab(self.parcel_record_tab_widget.count() + 1, self.condominium_other_tab,
                                                    self.tr("Commercial Other"))
            self.parcel_record_tab_widget.insertTab(self.parcel_record_tab_widget.count() - 1, self.specia_costs_tab,
                                                    self.tr("Special Costs"))
        elif self.parcel_type == 30:
            self.parcel_record_tab_widget.insertTab(self.parcel_record_tab_widget.count() , self.industrial_info_tab,
                                                    self.tr("Industrial Information"))
            self.parcel_record_tab_widget.insertTab(self.parcel_record_tab_widget.count() + 1, self.industrial_other_tab,
                                                    self.tr("Industrial Other"))
            self.parcel_record_tab_widget.insertTab(self.parcel_record_tab_widget.count() - 1, self.specia_costs_tab,
                                                    self.tr("Special Costs"))
        elif self.parcel_type == 40:
            self.parcel_record_tab_widget.insertTab(self.parcel_record_tab_widget.count(), self.agriculture_info_tab,
                                                    self.tr("Agriculture Information"))
            self.parcel_record_tab_widget.insertTab(self.parcel_record_tab_widget.count() + 1, self.agriculture_other_tab,
                                                    self.tr("Agriculture Other"))
            self.parcel_record_tab_widget.insertTab(self.parcel_record_tab_widget.count() - 1, self.specia_costs_tab,
                                                    self.tr("Special Costs"))
    def __special_costs_populate(self):

        bag_working_list = []
        session = SessionHandler().session_instance()
        parcel = session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_id).one()
        aimag = session.query(AuLevel1).filter(AuLevel1.geometry.ST_Contains(parcel.geometry)).one()
        sum = session.query(AuLevel2).filter(AuLevel2.geometry.ST_Contains(parcel.geometry)).one()

        self.aimag_working_edit.setText(aimag.name)
        self.sum_working_edit.setText(sum.name)

        self.bag_working_cbox.addItem("*", -1)
        if sum.code == None:
            return
        else:
            try:
                PluginUtils.populate_au_level3_cbox(self.bag_working_cbox, sum.code)
            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("Sql Error"), e.message)

    def __home_combo_setup(self):

        applicationTypeList = []
        landuseTypeList = []
        sourceTypeList = []
        landuseBuildingList = []
        materialList = []
        stoveList = []
        heatList = []

        session = SessionHandler().session_instance()
        try:
            applicationTypeList = session.query(ClApplicationType.description, ClApplicationType.code).all()
            landuseTypeList = session.query(ClLanduseType.description, ClLanduseType.code).all()
            if self.parcel_type == 10:
                landuseTypeList = session.query(ClLanduseType.description, ClLanduseType.code)\
                    .filter(or_(ClLanduseType.code == 2204,ClLanduseType.code == 2205, ClLanduseType.code == 2206)).all()
            sourceTypeList = session.query(VaTypeSource.description, VaTypeSource.code).all()
            landuseBuildingList = session.query(VaTypeLanduseBuilding.description, VaTypeLanduseBuilding.code)
            materialList = session.query(VaTypeMaterial.description, VaTypeMaterial.code).all()
            stoveList = session.query(VaTypeStove.description, VaTypeStove.code).all()
            heatList = session.query(VaTypeHeat.description, VaTypeHeat.code).all()
            building_design_list = session.query(VaTypeDesign).all()

        except SQLAlchemyError, e:
            QMessageBox.information(self, QApplication.translate("LM2", "Sql Error"), e.message)

        self.building_use_type_cbox.addItem("*", -1)
        self.building_material_cbox.addItem("*", -1)
        self.building_stove_type_cbox.addItem("*", -1)
        self.building_heat_Insulation_cbox.addItem("*", -1)
        self.building_design_cbox.addItem("*", -1)

        if self.parcel_type == 10:
            for app_type in applicationTypeList:
                if app_type.code == 1 or app_type.code == 2 or app_type.code == 3 or app_type.code == 5 or app_type.code == 7 \
                    or app_type.code == 8 or app_type.code == 11 or app_type.code == 13 or app_type.code == 14 \
                    or app_type.code == 15:
                    self.right_type_cbox.addItem(app_type.description, app_type.code)

            for landuse in landuseTypeList:
                code = str(landuse.code)
                if code[:1] == '2':
                    self.purchase_use_type_cbox.addItem(landuse.description, str(landuse.code))
                    self.lease_use_type_cbox.addItem(landuse.description, str(landuse.code))

            for source in sourceTypeList:
                self.source_cbox.addItem(source.description, source.code)

            for landuse in landuseBuildingList:
                self.building_use_type_cbox.addItem(landuse.description, landuse.code)

            for material in materialList:
                self.building_material_cbox.addItem(material.description, material.code)

            for design in building_design_list:
                self.building_design_cbox.addItem(design.description, design.code)

            for stove in stoveList:
                self.building_stove_type_cbox.addItem(stove.description, stove.code)

            for heat in heatList:
                self.building_heat_Insulation_cbox.addItem(heat.description, heat.code)
        elif self.parcel_type == 20:
            for app_type in applicationTypeList:
                if app_type.code == 2 or app_type.code == 4 or app_type.code == 5 or app_type.code == 7 or \
                    app_type.code == 8 or app_type.code == 11 or app_type.code == 13 or app_type.code == 14:
                    self.c_right_type_cbox.addItem(app_type.description, app_type.code)
        elif self.parcel_type == 30:
            for app_type in applicationTypeList:
                if app_type.code == 5 or app_type.code == 7 or app_type.code == 8 or app_type.code == 11 or \
                    app_type.code == 13 or app_type.code == 14:
                    self.i_right_type_cbox.addItem(app_type.description, app_type.code)
        elif self.parcel_type == 40:
            for app_type in applicationTypeList:
                if app_type.code == 4 or app_type.code == 5 or app_type.code == 7 or app_type.code == 8 or \
                    app_type.code == 11 or app_type.code == 13 or app_type.code == 14 or app_type.code == 15:
                    self.a_right_type_cbox.addItem(app_type.description, app_type.code)

    #commercial
    def __condominium_combo_setup(self):

        applicationTypeList = []
        landuseTypeList = []
        sourceTypeList = []
        landuseBuildingList = []
        materialList = []

        session = SessionHandler().session_instance()
        try:
            applicationTypeList = session.query(ClApplicationType.description, ClApplicationType.code).all()
            landuseTypeList = session.query(ClLanduseType.description, ClLanduseType.code).all()
            if self.parcel_type == 20:
                landuseTypeList = session.query(ClLanduseType.description, ClLanduseType.code)\
                    .filter(ClLanduseType.code2 == 21).all()
            sourceTypeList = session.query(VaTypeSource.description, VaTypeSource.code).all()
            designList = session.query(VaTypeDesign).all()
            esystemList = session.query(VaTypeESystem).all()
            landuseBuildingList = session.query(VaTypeLanduseBuilding.description, VaTypeLanduseBuilding.code)
            materialList = session.query(VaTypeMaterial.description, VaTypeMaterial.code).all()

        except SQLAlchemyError, e:
            QMessageBox.information(self, QApplication.translate("LM2", "Sql Error"), e.message)

        self.c_building_use_type_cbox.addItem("*", -1)
        self.c_building_material_cbox.addItem("*", -1)
        self.c_building_design_cbox.addItem("*", -1)
        self.c_building_esystem_cbox.addItem("*", -1)

        if self.parcel_type == 20:
            for app_type in applicationTypeList:
                if app_type.code == 1 or app_type.code == 2 or app_type.code == 3 or app_type.code == 5 or app_type.code == 7 \
                    or app_type.code == 8 or app_type.code == 11 or app_type.code == 13 or app_type.code == 14 \
                    or app_type.code == 15:
                    self.c_right_type_cbox.addItem(app_type.description, app_type.code)

            for landuse in landuseTypeList:
                self.c_purchase_use_type_cbox.addItem(landuse.description, str(landuse.code))
                self.c_lease_use_type_cbox.addItem(landuse.description, str(landuse.code))

            for source in sourceTypeList:
                self.c_source_cbox.addItem(source.description, source.code)

            for landuse in landuseBuildingList:
                self.c_building_use_type_cbox.addItem(landuse.description, landuse.code)

            for material in materialList:
                self.c_building_material_cbox.addItem(material.description, material.code)

            for design in designList:
                self.c_building_design_cbox.addItem(design.description, design.code)

            for system in esystemList:
                self.c_building_esystem_cbox.addItem(system.description, system.code)


    def __industrial_combo_setup(self):

        applicationTypeList = []
        landuseTypeList = []
        sourceTypeList = []
        landuseBuildingList = []
        materialList = []
        stoveList = []
        heatList = []

        session = SessionHandler().session_instance()
        try:
            applicationTypeList = session.query(ClApplicationType.description, ClApplicationType.code).all()
            landuseTypeList = session.query(ClLanduseType).all()
            if self.parcel_type == 30:
                landuseTypeList = session.query(ClLanduseType)\
                    .filter(ClLanduseType.code2 == 23).all()
            sourceTypeList = session.query(VaTypeSource.description, VaTypeSource.code).all()
            landuseBuildingList = session.query(VaTypeLanduseBuilding.description, VaTypeLanduseBuilding.code)
            materialList = session.query(VaTypeMaterial.description, VaTypeMaterial.code).all()
            productList = session.query(VaTypeProduct.description, VaTypeProduct.code).all()

        except SQLAlchemyError, e:
            QMessageBox.information(self, QApplication.translate("LM2", "Sql Error"), e.message)

        self.i_building_use_type_cbox.addItem("*", -1)
        self.i_building_material_cbox.addItem("*", -1)
        self.i_product_type_cbox.addItem("*", -1)

        if self.parcel_type == 30:
            for app_type in applicationTypeList:
                if app_type.code == 1 or app_type.code == 2 or app_type.code == 3 or app_type.code == 5 or app_type.code == 7 \
                    or app_type.code == 8 or app_type.code == 11 or app_type.code == 13 or app_type.code == 14 \
                    or app_type.code == 15:
                    self.i_right_type_cbox.addItem(app_type.description, app_type.code)

            for landuse in landuseTypeList:
                self.i_purchase_use_type_cbox.addItem(landuse.description, str(landuse.code))
                self.i_lease_use_type_cbox.addItem(landuse.description, str(landuse.code))

            for source in sourceTypeList:
                self.i_source_cbox.addItem(source.description, source.code)

            for landuse in landuseBuildingList:
                self.i_building_use_type_cbox.addItem(landuse.description, landuse.code)

            for material in materialList:
                self.i_building_material_cbox.addItem(material.description, material.code)
            for product in productList:
                self.i_product_type_cbox.addItem(product.description, product.code)

    def __agricalture_combo_setup(self):

        applicationTypeList = []
        landuseTypeList = []
        sourceTypeList = []
        landuseBuildingList = []
        materialList = []

        session = SessionHandler().session_instance()
        try:
            applicationTypeList = session.query(ClApplicationType.description, ClApplicationType.code).all()
            landuseTypeList = session.query(ClLanduseType.description, ClLanduseType.code).all()
            if self.parcel_type == 40:
                landuseTypeList = session.query(ClLanduseType.description, ClLanduseType.code)\
                    .filter(or_(ClLanduseType.code2 == 11,ClLanduseType.code2 == 12, \
                                ClLanduseType.code2 == 13, ClLanduseType.code2 == 14, ClLanduseType.code2 == 15)).all()
            sourceTypeList = session.query(VaTypeSource.description, VaTypeSource.code).all()
            landuseBuildingList = session.query(VaTypeLanduseBuilding.description, VaTypeLanduseBuilding.code)
            irrigationList = session.query(VaTypeIrrigation.description, VaTypeIrrigation.code)
            cropList = session.query(VaTypeCrop.description, VaTypeCrop.code).all()
            materialList = session.query(VaTypeMaterial.description, VaTypeMaterial.code).all()

        except SQLAlchemyError, e:
            QMessageBox.information(self, QApplication.translate("LM2", "Sql Error"), e.message)

        self.a_building_use_type_cbox.addItem("*", -1)
        self.a_use_type_cbox.addItem("*", -1)
        self.a_crop_type_cbox.addItem("*", -1)
        self.a_building_material_cbox.addItem("*", -1)
        self.a_irrigation_type_cbox.addItem("*", -1)

        if self.parcel_type == 40:
            for app_type in applicationTypeList:
                if app_type.code == 1 or app_type.code == 2 or app_type.code == 3 or app_type.code == 4 or app_type.code == 5 or app_type.code == 7 \
                    or app_type.code == 8 or app_type.code == 11 or app_type.code == 13 or app_type.code == 14 \
                    or app_type.code == 15:
                    self.a_right_type_cbox.addItem(app_type.description, app_type.code)

            for source in sourceTypeList:
                self.a_source_cbox.addItem(source.description, source.code)

            for landuse in landuseBuildingList:
                self.a_building_use_type_cbox.addItem(landuse.description, landuse.code)

            for irrigation in irrigationList:
                self.a_irrigation_type_cbox.addItem(irrigation.description, irrigation.code)

            for landuse in landuseTypeList:
                self.a_use_type_cbox.addItem(landuse.description, landuse.code)

            for crops in cropList:
                self.a_crop_type_cbox.addItem(crops.description, crops.code)

            for material in materialList:
                self.a_building_material_cbox.addItem(material.description, material.code)

    def __parcel_home_populate(self):

        now = QDateTime.currentDateTime()
        self.purchase_dateEdit.setDateTime(now)
        self.lease_dateEdit.setDateTime(now)
        self.registration_date.setDateTime(now)
        self.__home_combo_setup()
        self.__special_costs_populate()
        session = SessionHandler().session_instance()
        count = session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_id).count()
        if count == 0:
            return
        parcel = session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_id).one()

        if session.query(CtApplication).filter(CtApplication.parcel == parcel.parcel_id).count() == 0:
            #PluginUtils.show_message(self, self.tr("no"), self.tr("no application"))
            self.decision_date_edit.setText("")
            self.duration_year_edit.setText("")
        else:
            application = session.query(CtApplication).filter(CtApplication.parcel == parcel.parcel_id).all()
            for application in application:
                self.duration_year_edit.setText(str(application.approved_duration))
                if session.query(CtDecisionApplication).filter(CtDecisionApplication.application == application.app_no).count() == 0:
                    PluginUtils.show_message(self, self.tr(""), self.tr("no decision"))
                    self.decision_date_edit.setText("")
                else:
                    decision_application = session.query(CtDecisionApplication).filter(CtDecisionApplication.application == application.app_no).one()
                    if session.query(CtDecision).filter(CtDecision.decision_no == decision_application.decision).count() == 0:
                        PluginUtils.show_message(self, self.tr("no"), self.tr("no decision"))
                        self.decision_date_edit.setText("")
                    else:
                        decision = session.query(CtDecision).filter(CtDecision.decision_no == decision_application.decision).one()
                        self.decision_date_edit.setText(str(decision.decision_date))

        self.cadastreId_edit.setText(self.parcel_id)
        self.calculated_area_edit.setText(str(parcel.area_m2))

        if parcel.documented_area_m2 == None:
            self.purchase_area_edit.setText(str(parcel.area_m2))
            self.lease_area_edit.setText(str(parcel.area_m2))
        else:
            self.purchase_area_edit.setText(str(parcel.documented_area_m2))
            self.lease_area_edit.setText(str(parcel.documented_area_m2))
        address_streetname = ""
        address_khashaa = ""
        bag_name = ""
        if parcel.address_streetname != None:
            address_streetname = parcel.address_streetname
        if parcel.address_khashaa != None:
            address_khashaa = parcel.address_khashaa
        bags = session.query(AuLevel3).filter(AuLevel3.geometry.ST_Overlaps((parcel.geometry))).all()
        for bag in bags:
            bag_name = bag.name
        # bag = session.query(AuLevel3).filter( AuLevel3.geometry.ST_Within(func.ST_Centroid(parcel.geometry))).one()
        address = bag_name +", "+ address_streetname +", "+ address_khashaa

        self.address_edit.setText(address)
        sum = session.query(AuLevel2).filter(AuLevel2.geometry.ST_Contains(parcel.geometry)).one()

        self.home_num_first_edit.setText(sum.code)
        self.home_num_type_edit.setText(str(self.parcel_type).zfill(2))
        self.home_num_last_edit.setText(QDate.currentDate().toString("yy"))

        parcel_type_filter = "%-" + str(self.parcel_type) + "-%"
        soum_filter = str(sum.code) + "-%"
        year_filter = "%-" + str(QDate.currentDate().toString("yy"))

        try:
            count = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no != self.register_no)\
                    .filter(VaInfoHomeParcel.register_no.like("%-%"))\
                    .filter(VaInfoHomeParcel.register_no.like(parcel_type_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(soum_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(year_filter))\
                .order_by(func.substr(VaInfoHomeParcel.register_no, 10, 13).desc()).count()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Error"), e.message)
            return

        if count > 0:
            try:
                maxRegisterNo = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no != self.register_no)\
                    .filter(VaInfoHomeParcel.register_no.like("%-%"))\
                    .filter(VaInfoHomeParcel.register_no.like(parcel_type_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(soum_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(year_filter))\
                .order_by(func.substr(VaInfoHomeParcel.register_no, 10, 13).desc()).first()
            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("Database Error"), e.message)
                return

            register_no = maxRegisterNo.register_no.split("-")
            self.home_num_middle_edit.setText(str(int(register_no[2]) + 1).zfill(4))
        else:
            self.home_num_middle_edit.setText("0001")
        self.register_no = self.home_num_first_edit.text()+'-'+self.home_num_type_edit.text()+'-'+\
                           self.home_num_middle_edit.text()+'-'+self.home_num_last_edit.text()
        if session.query(CaBuilding).filter(parcel.geometry.ST_Contains(CaBuilding.geometry)).count() != 0:
            building = session.query(CaBuilding).filter(parcel.geometry.ST_Contains(CaBuilding.geometry)).all()
            for build in building:
                build_no = build.building_id[-3:]
                self.building_no_cbox.addItem(build_no, build.building_id)

    @pyqtSlot(int)
    def on_building_no_cbox_currentIndexChanged(self, index):

        session = SessionHandler().session_instance()
        building_id = self.building_no_cbox.itemData(index)

        building = session.query(CaBuilding).filter(CaBuilding.building_id == building_id).one()
        self.building_area_edit.setText(str(building.area_m2))

    @pyqtSlot(int)
    def on_c_building_no_cbox_currentIndexChanged(self, index):

        session = SessionHandler().session_instance()
        building_id = self.c_building_no_cbox.itemData(index)

        building = session.query(CaBuilding).filter(CaBuilding.building_id == building_id).one()
        self.c_building_area_edit.setText(str(building.area_m2))

    @pyqtSlot(int)
    def on_i_building_no_cbox_currentIndexChanged(self, index):

        session = SessionHandler().session_instance()
        building_id = self.i_building_no_cbox.itemData(index)

        building = session.query(CaBuilding).filter(CaBuilding.building_id == building_id).one()
        self.i_building_area_edit.setText(str(building.area_m2))

    @pyqtSlot(int)
    def on_a_building_no_cbox_currentIndexChanged(self, index):

        session = SessionHandler().session_instance()
        building_id = self.a_building_no_cbox.itemData(index)

        building = session.query(CaBuilding).filter(CaBuilding.building_id == building_id).one()
        self.a_building_area_edit.setText(str(building.area_m2))

    def __parcel_condominium_populate(self):

        now = QDateTime.currentDateTime()
        self.c_purchase_dateEdit.setDateTime(now)
        self.c_lease_dateEdit.setDateTime(now)
        self.c_registration_date.setDateTime(now)
        self.__condominium_combo_setup()
        self.__special_costs_populate()
        session = SessionHandler().session_instance()
        count = session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_id).count()
        if count == 0:
            return
        parcel = session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_id).one()

        if session.query(CtApplication).filter(CtApplication.parcel == parcel.parcel_id).count() == 0:
            #PluginUtils.show_message(self, self.tr("no"), self.tr("no application"))
            self.c_decision_date_edit.setText("")
            self.c_duration_edit.setText("")
        else:
            application = session.query(CtApplication).filter(CtApplication.parcel == parcel.parcel_id).all()
            for application in application:
                self.c_duration_edit.setText(str(application.approved_duration))
                if session.query(CtDecisionApplication).filter(CtDecisionApplication.application == application.app_no).count() == 0:
                    PluginUtils.show_message(self, self.tr(""), self.tr("no decision"))
                    self.c_decision_date_edit.setText("")
                else:
                    decision_application = session.query(CtDecisionApplication).filter(CtDecisionApplication.application == application.app_no).one()
                    if session.query(CtDecision).filter(CtDecision.decision_no == decision_application.decision).count() == 0:
                        PluginUtils.show_message(self, self.tr("no"), self.tr("no decision"))
                        self.c_decision_date_edit.setText("")
                    else:
                        decision = session.query(CtDecision).filter(CtDecision.decision_no == decision_application.decision).one()
                        self.c_decision_date_edit.setText(str(decision.decision_date))

        self.c_cadastreId_edit.setText(self.parcel_id)
        self.c_calculated_area_edit.setText(str(parcel.area_m2))

        if parcel.documented_area_m2 == None:
            self.c_purchase_area_edit.setText(str(parcel.area_m2))
            self.c_lease_area_edit.setText(str(parcel.area_m2))
        else:
            self.c_purchase_area_edit.setText(str(parcel.documented_area_m2))
            self.c_lease_area_edit.setText(str(parcel.documented_area_m2))
        address_streetname = ""
        address_khashaa = ""
        bag_name = ""
        if parcel.address_streetname != None:
            address_streetname = parcel.address_streetname
        if parcel.address_khashaa != None:
            address_khashaa = parcel.address_khashaa
        bags = session.query(AuLevel3).filter(AuLevel3.geometry.ST_Overlaps((parcel.geometry))).all()
        for bag in bags:
            bag_name = bag.name
        # bag = session.query(AuLevel3).filter( AuLevel3.geometry.ST_Within(func.ST_Centroid(parcel.geometry))).one()
        address = bag_name +", "+ address_streetname +", "+ address_khashaa

        self.c_address_edit.setText(address)
        sum = session.query(AuLevel2).filter(AuLevel2.geometry.ST_Contains(parcel.geometry)).one()

        self.commercial_num_first_edit.setText(sum.code)
        self.commercial_num_type_edit.setText(str(self.parcel_type).zfill(2))
        self.commercial_num_last_edit.setText(QDate.currentDate().toString("yy"))

        parcel_type_filter = "%-" + str(self.parcel_type) + "-%"
        soum_filter = str(sum.code) + "-%"
        year_filter = "%-" + str(QDate.currentDate().toString("yy"))

        try:
            count = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no != self.register_no)\
                    .filter(VaInfoHomeParcel.register_no.like("%-%"))\
                    .filter(VaInfoHomeParcel.register_no.like(parcel_type_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(soum_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(year_filter))\
                .order_by(func.substr(VaInfoHomeParcel.register_no, 10, 13).desc()).count()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Error"), e.message)
            return

        if count > 0:
            try:
                maxRegisterNo = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no != self.register_no)\
                    .filter(VaInfoHomeParcel.register_no.like("%-%"))\
                    .filter(VaInfoHomeParcel.register_no.like(parcel_type_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(soum_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(year_filter))\
                .order_by(func.substr(VaInfoHomeParcel.register_no, 10, 13).desc()).first()
            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("Database Error"), e.message)
                return

            register_no = maxRegisterNo.register_no.split("-")
            self.commercial_num_middle_edit.setText(str(int(register_no[2]) + 1).zfill(4))
        else:
            self.commercial_num_middle_edit.setText("0001")

        if session.query(CaBuilding).filter(parcel.geometry.ST_Contains(CaBuilding.geometry)).count() != 0:
            building = session.query(CaBuilding).filter(parcel.geometry.ST_Contains(CaBuilding.geometry)).all()
            for build in building:
                build_no = build.building_id[-3:]
                self.c_building_no_cbox.addItem(build_no, build.building_id)

    def __parcel_industrial_populate(self):

        now = QDateTime.currentDateTime()
        self.i_purchase_date_edit.setDateTime(now)
        self.i_lease_dateEdit.setDateTime(now)
        self.i_registration_date.setDateTime(now)
        self.__industrial_combo_setup()
        self.__special_costs_populate()
        session = SessionHandler().session_instance()
        count = session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_id).count()
        if count == 0:
            return
        parcel = session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_id).one()

        if session.query(CtApplication).filter(CtApplication.parcel == parcel.parcel_id).count() == 0:
            #PluginUtils.show_message(self, self.tr("no"), self.tr("no application"))
            self.i_decision_date_edit.setText("")
            self.i_duration_edit.setText("")
        else:
            application = session.query(CtApplication).filter(CtApplication.parcel == parcel.parcel_id).all()
            for application in application:
                self.i_duration_edit.setText(str(application.approved_duration))
                if session.query(CtDecisionApplication).filter(CtDecisionApplication.application == application.app_no).count() == 0:
                    PluginUtils.show_message(self, self.tr(""), self.tr("no decision"))
                    self.i_decision_date_edit.setText("")
                else:
                    decision_application = session.query(CtDecisionApplication).filter(CtDecisionApplication.application == application.app_no).one()
                    if session.query(CtDecision).filter(CtDecision.decision_no == decision_application.decision).count() == 0:
                        PluginUtils.show_message(self, self.tr("no"), self.tr("no decision"))
                        self.i_decision_date_edit.setText("")
                    else:
                        decision = session.query(CtDecision).filter(CtDecision.decision_no == decision_application.decision).one()
                        self.i_decision_date_edit.setText(str(decision.decision_date))

        self.i_cadastreid_edit.setText(self.parcel_id)
        self.i_calculated_area_edit.setText(str(parcel.area_m2))

        if parcel.documented_area_m2 == None:
            self.i_purchase_area_edit.setText(str(parcel.area_m2))
            self.i_lease_area_edit.setText(str(parcel.area_m2))
        else:
            self.i_purchase_area_edit.setText(str(parcel.documented_area_m2))
            self.i_lease_area_edit.setText(str(parcel.documented_area_m2))
        address_streetname = ""
        address_khashaa = ""
        bag_name = ""
        if parcel.address_streetname != None:
            address_streetname = parcel.address_streetname
        if parcel.address_khashaa != None:
            address_khashaa = parcel.address_khashaa
        bags = session.query(AuLevel3).filter(AuLevel3.geometry.ST_Overlaps((parcel.geometry))).all()
        for bag in bags:
            bag_name = bag.name
        # bag = session.query(AuLevel3).filter( AuLevel3.geometry.ST_Within(func.ST_Centroid(parcel.geometry))).one()
        address = bag_name +", "+ address_streetname +", "+ address_khashaa

        self.i_address_edit.setText(address)
        sum = session.query(AuLevel2).filter(AuLevel2.geometry.ST_Contains(parcel.geometry)).one()

        self.industrial_num_first_edit.setText(sum.code)
        self.industrial_num_type_edit.setText(str(self.parcel_type).zfill(2))
        self.industrial_num_last_edit.setText(QDate.currentDate().toString("yy"))

        parcel_type_filter = "%-" + str(self.parcel_type) + "-%"
        soum_filter = str(sum.code) + "-%"
        year_filter = "%-" + str(QDate.currentDate().toString("yy"))

        try:
            count = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no != self.register_no)\
                    .filter(VaInfoHomeParcel.register_no.like("%-%"))\
                    .filter(VaInfoHomeParcel.register_no.like(parcel_type_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(soum_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(year_filter))\
                .order_by(func.substr(VaInfoHomeParcel.register_no, 10, 13).desc()).count()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Error"), e.message)
            return

        if count > 0:
            try:
                maxRegisterNo = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no != self.register_no)\
                    .filter(VaInfoHomeParcel.register_no.like("%-%"))\
                    .filter(VaInfoHomeParcel.register_no.like(parcel_type_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(soum_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(year_filter))\
                .order_by(func.substr(VaInfoHomeParcel.register_no, 10, 13).desc()).first()
            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("Database Error"), e.message)
                return

            register_no = maxRegisterNo.register_no.split("-")
            self.industrial_num_middle_edit.setText(str(int(register_no[2]) + 1).zfill(4))
        else:
            self.industrial_num_middle_edit.setText("0001")
        self.register_no = self.industrial_num_first_edit.text()+'-'+self.industrial_num_type_edit.text()+'-'+\
                           self.industrial_num_middle_edit.text()+'-'+self.industrial_num_last_edit.text()
        if session.query(CaBuilding).filter(parcel.geometry.ST_Contains(CaBuilding.geometry)).count() != 0:
            building = session.query(CaBuilding).filter(parcel.geometry.ST_Contains(CaBuilding.geometry)).all()
            for build in building:
                build_no = build.building_id[-3:]
                self.i_building_no_cbox.addItem(build_no, build.building_id)


    def __parcel_agriculture_populate(self):

        now = QDateTime.currentDateTime()
        self.a_purchase_dateEdit.setDateTime(now)
        self.a_lease_dateEdit.setDateTime(now)
        self.a_registration_date.setDateTime(now)
        self.__agricalture_combo_setup()
        self.__special_costs_populate()
        session = SessionHandler().session_instance()
        count = session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_id).count()
        if count == 0:
            return
        parcel = session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_id).one()
        if session.query(CtApplication).filter(CtApplication.parcel == parcel.parcel_id).count() == 0:
            #PluginUtils.show_message(self, self.tr("no"), self.tr("no application"))
            self.decision_date_edit.setText("")
            self.duration_year_edit.setText("")
        else:
            application = session.query(CtApplication).filter(CtApplication.parcel == parcel.parcel_id).all()
            for application in application:
                self.a_duration_edit.setText(str(application.approved_duration))
                if session.query(CtDecisionApplication).filter(CtDecisionApplication.application == application.app_no).count() == 0:
                    PluginUtils.show_message(self, self.tr(""), self.tr("no decision"))
                    self.a_decision_date_edit.setText("")
                else:
                    decision_application = session.query(CtDecisionApplication).filter(CtDecisionApplication.application == application.app_no).one()
                    if session.query(CtDecision).filter(CtDecision.decision_no == decision_application.decision).count() == 0:
                        PluginUtils.show_message(self, self.tr("no"), self.tr("no decision"))
                        self.a_decision_date_edit.setText("")
                    else:
                        decision = session.query(CtDecision).filter(CtDecision.decision_no == decision_application.decision).one()
                        self.a_decision_date_edit.setText(str(decision.decision_date))

        self.a_cadastreId_edit.setText(self.parcel_id)
        self.a_calculated_area_edit.setText(str(parcel.area_m2/10000))

        if parcel.documented_area_m2 == None:
            self.a_purchase_area_edit.setText(str(parcel.area_m2/10000))
            self.a_lease_area_edit.setText(str(parcel.area_m2/10000))
        else:
            self.a_purchase_area_edit.setText(str(parcel.documented_area_m2/10000))
            self.a_lease_area_edit.setText(str(parcel.documented_area_m2/10000))
        address_streetname = ""
        address_khashaa = ""
        bag_name = ""
        if parcel.address_streetname != None:
            address_streetname = parcel.address_streetname
        if parcel.address_khashaa != None:
            address_khashaa = parcel.address_khashaa
        bags = session.query(AuLevel3).filter(AuLevel3.geometry.ST_Overlaps((parcel.geometry))).all()
        for bag in bags:
            bag_name = bag.name
        # bag = session.query(AuLevel3).filter( AuLevel3.geometry.ST_Within(func.ST_Centroid(parcel.geometry))).one()
        address = bag_name +", "+ address_streetname +", "+ address_khashaa

        self.a_address_edit.setText(address)
        sum = session.query(AuLevel2).filter(AuLevel2.geometry.ST_Contains(parcel.geometry)).one()

        self.agriculture_num_first_edit.setText(sum.code)
        self.agriculture_num_type_edit.setText(str(self.parcel_type).zfill(2))
        self.agriculture_num_last_edit.setText(QDate.currentDate().toString("yy"))

        parcel_type_filter = "%-" + str(self.parcel_type) + "-%"
        soum_filter = str(sum.code) + "-%"
        year_filter = "%-" + str(QDate.currentDate().toString("yy"))
        try:
            count = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no != self.register_no)\
                    .filter(VaInfoHomeParcel.register_no.like("%-%"))\
                    .filter(VaInfoHomeParcel.register_no.like(parcel_type_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(soum_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(year_filter))\
                .order_by(func.substr(VaInfoHomeParcel.register_no, 10, 13).desc()).count()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Error"), e.message)
            return
        if count > 0:
            try:
                maxRegisterNo = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no != self.register_no)\
                    .filter(VaInfoHomeParcel.register_no.like("%-%"))\
                    .filter(VaInfoHomeParcel.register_no.like(parcel_type_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(soum_filter))\
                    .filter(VaInfoHomeParcel.register_no.like(year_filter))\
                .order_by(func.substr(VaInfoHomeParcel.register_no, 10, 13).desc()).first()
            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("Database Error"), e.message)
                return

            register_no = maxRegisterNo.register_no.split("-")
            self.agriculture_num_middle_edit.setText(str(int(register_no[2]) + 1).zfill(4))
        else:
            self.agriculture_num_middle_edit.setText("0001")

        if session.query(CaBuilding).filter(parcel.geometry.ST_Contains(CaBuilding.geometry)).count() != 0:
            building = session.query(CaBuilding).filter(parcel.geometry.ST_Contains(CaBuilding.geometry)).all()
            for build in building:
                build_no = build.building_id[-3:]
                self.a_building_no_cbox.addItem(build_no, build.building_id)

    @pyqtSlot(bool)
    def on_home_purchase_rbutton_toggled(self, state):

        if state:
            self.home_purchase_gbox.setEnabled(True)
            self.home_lease_gbox.setEnabled(False)
        else:
            self.home_purchase_gbox.setEnabled(False)
            self.home_lease_gbox.setEnabled(True)

    @pyqtSlot(bool)
    def on_home_lease_rbutton_toggled(self, state):

        if state:
            self.home_purchase_gbox.setEnabled(False)
            self.home_lease_gbox.setEnabled(True)
        else:
            self.home_purchase_gbox.setEnabled(True)
            self.home_lease_gbox.setEnabled(False)

    @pyqtSlot(bool)
    def on_a_purchase_rbutton_toggled(self, state):

        if state:
            self.a_purchase_gbox.setEnabled(True)
            self.a_lease_gbox.setEnabled(False)
        else:
            self.a_purchase_gbox.setEnabled(False)
            self.a_lease_gbox.setEnabled(True)

    @pyqtSlot(bool)
    def on_a_lease_rbutton_toggled(self, state):

        if state:
            self.a_purchase_gbox.setEnabled(False)
            self.a_lease_gbox.setEnabled(True)
        else:
            self.a_purchase_gbox.setEnabled(True)
            self.a_lease_gbox.setEnabled(False)

    #industrial
    @pyqtSlot(bool)
    def on_i_purchase_rbutton_toggled(self, state):

        if state:
            self.i_purchase_gbox.setEnabled(True)
            self.i_lease_gbox.setEnabled(False)
        else:
            self.i_purchase_gbox.setEnabled(False)
            self.i_lease_gbox.setEnabled(True)

    @pyqtSlot(bool)
    def on_i_lease_rbutton_toggled(self, state):

        if state:
            self.i_purchase_gbox.setEnabled(False)
            self.i_lease_gbox.setEnabled(True)
        else:
            self.i_purchase_gbox.setEnabled(True)
            self.i_lease_gbox.setEnabled(False)

    #commercial
    @pyqtSlot(bool)
    def on_c_purchase_rbutton_toggled(self, state):

        if state:
            self.c_purchase_gbox.setEnabled(True)
            self.c_lease_gbox.setEnabled(False)
        else:
            self.c_purchase_gbox.setEnabled(False)
            self.c_lease_gbox.setEnabled(True)

    @pyqtSlot(bool)
    def on_c_lease_rbutton_toggled(self, state):

        if state:
            self.c_purchase_gbox.setEnabled(False)
            self.c_lease_gbox.setEnabled(True)
        else:
            self.c_purchase_gbox.setEnabled(True)
            self.c_lease_gbox.setEnabled(False)

    def __home_purchase_add(self):

        landuse_code = self.purchase_use_type_cbox.itemData(self.purchase_use_type_cbox.currentIndex())
        landuse_text = self.purchase_use_type_cbox.currentText()

        if self.purchase_price_edit.text() == "" or self.purchase_price_edit.text() == None:
            self.purchase_price_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            PluginUtils.show_message(self, self.tr("No Price"), self.tr("No Price"))
            return
        if self.purchase_area_edit.text() == "" or self.purchase_area_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Area"))
            return
        if self.purchase_twidget.rowCount() != 0:
            PluginUtils.show_message(self, self.tr("Row"), self.tr("Already inserted row"))
            return
        usetype_item = QTableWidgetItem(landuse_text)
        usetype_item.setData(Qt.UserRole, landuse_code)
        date_item = QTableWidgetItem(self.purchase_dateEdit.text())
        date_item.setData(Qt.UserRole, self.purchase_dateEdit.text())
        area_item = QTableWidgetItem(self.purchase_area_edit.text())
        area_item.setData(Qt.UserRole, self.purchase_area_edit.text())
        price_item = QTableWidgetItem(self.purchase_price_edit.text())
        price_item.setData(Qt.UserRole, self.purchase_price_edit.text())
        price_m2_item = QTableWidgetItem(self.purchase_price_if_m2.text())
        price_m2_item.setData(Qt.UserRole, self.purchase_price_if_m2.text())

        row = self.purchase_twidget.rowCount()
        self.purchase_twidget.insertRow(row)

        self.purchase_twidget.setItem(row, 0, usetype_item)
        self.purchase_twidget.setItem(row, 1, date_item)
        self.purchase_twidget.setItem(row, 2, area_item)
        self.purchase_twidget.setItem(row, 3, price_item)
        self.purchase_twidget.setItem(row, 4, price_m2_item)

    def __commercial_purchase_add(self):

        landuse_code = self.c_purchase_use_type_cbox.itemData(self.c_purchase_use_type_cbox.currentIndex())
        landuse_text = self.c_purchase_use_type_cbox.currentText()

        if self.c_purchase_price_edit.text() == "" or self.c_purchase_price_edit.text() == None:
            self.c_purchase_price_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            PluginUtils.show_message(self, self.tr("No Price"), self.tr("No Price"))
            return
        if self.c_purchase_area_edit.text() == "" or self.c_purchase_area_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Area"))
            return
        if self.c_purchase_twidget.rowCount() != 0:
            PluginUtils.show_message(self, self.tr("Row"), self.tr("Already inserted row"))
            return
        usetype_item = QTableWidgetItem(landuse_text)
        usetype_item.setData(Qt.UserRole, landuse_code)
        date_item = QTableWidgetItem(self.c_purchase_dateEdit.text())
        date_item.setData(Qt.UserRole, self.c_purchase_dateEdit.text())
        area_item = QTableWidgetItem(self.c_purchase_area_edit.text())
        area_item.setData(Qt.UserRole, self.c_purchase_area_edit.text())
        price_item = QTableWidgetItem(self.c_purchase_price_edit.text())
        price_item.setData(Qt.UserRole, self.c_purchase_price_edit.text())
        price_m2_item = QTableWidgetItem(self.c_purchase_price_if_m2.text())
        price_m2_item.setData(Qt.UserRole, self.c_purchase_price_if_m2.text())

        row = self.c_purchase_twidget.rowCount()
        self.c_purchase_twidget.insertRow(row)

        self.c_purchase_twidget.setItem(row, 0, usetype_item)
        self.c_purchase_twidget.setItem(row, 1, date_item)
        self.c_purchase_twidget.setItem(row, 2, area_item)
        self.c_purchase_twidget.setItem(row, 3, price_item)
        self.c_purchase_twidget.setItem(row, 4, price_m2_item)

    def __industrial_purchase_add(self):

        landuse_code = self.i_purchase_use_type_cbox.itemData(self.i_purchase_use_type_cbox.currentIndex())
        landuse_text = self.i_purchase_use_type_cbox.currentText()

        if self.i_purchase_price_edit.text() == "" or self.i_purchase_price_edit.text() == None:
            self.i_purchase_price_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            PluginUtils.show_message(self, self.tr("No Price"), self.tr("No Price"))
            return
        if self.i_purchase_area_edit.text() == "" or self.i_purchase_area_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Area"))
            return
        if self.i_purchase_twidget.rowCount() != 0:
            PluginUtils.show_message(self, self.tr("Row"), self.tr("Already inserted row"))
            return
        usetype_item = QTableWidgetItem(landuse_text)
        usetype_item.setData(Qt.UserRole, landuse_code)
        date_item = QTableWidgetItem(self.i_purchase_date_edit.text())
        date_item.setData(Qt.UserRole, self.i_purchase_date_edit.dateTime())
        area_item = QTableWidgetItem(self.i_purchase_area_edit.text())
        area_item.setData(Qt.UserRole, self.i_purchase_area_edit.text())
        price_item = QTableWidgetItem(self.i_purchase_price_edit.text())
        price_item.setData(Qt.UserRole, self.i_purchase_price_edit.text())
        price_m2_item = QTableWidgetItem(self.i_purchase_price_if_m2.text())
        price_m2_item.setData(Qt.UserRole, self.i_purchase_price_if_m2.text())

        row = self.i_purchase_twidget.rowCount()
        self.i_purchase_twidget.insertRow(row)

        self.i_purchase_twidget.setItem(row, 0, usetype_item)
        self.i_purchase_twidget.setItem(row, 1, date_item)
        self.i_purchase_twidget.setItem(row, 2, area_item)
        self.i_purchase_twidget.setItem(row, 3, price_item)
        self.i_purchase_twidget.setItem(row, 4, price_m2_item)

    def __agricalture_purchase_add(self):

        if self.a_price_edit.text() == "" or self.a_price_edit.text() == None:
            self.a_price_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            PluginUtils.show_message(self, self.tr("No Price"), self.tr("No Price"))
            return
        if self.a_purchase_area_edit.text() == "" or self.a_purchase_area_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Area"))
            return
        if self.a_purchase_twidget.rowCount() != 0:
            PluginUtils.show_message(self, self.tr("Row"), self.tr("Already inserted row"))
            return
        date_item = QTableWidgetItem(self.a_purchase_dateEdit.text())
        date_item.setData(Qt.UserRole, self.a_purchase_dateEdit.text())
        area_item = QTableWidgetItem(self.a_purchase_area_edit.text())
        area_item.setData(Qt.UserRole, self.a_purchase_area_edit.text())
        price_item = QTableWidgetItem(self.a_price_edit.text())
        price_item.setData(Qt.UserRole, self.a_price_edit.text())
        price_m2_item = QTableWidgetItem(self.a_purchase_price_if_m2.text())
        price_m2_item.setData(Qt.UserRole, self.a_purchase_price_if_m2.text())

        row = self.a_purchase_twidget.rowCount()
        self.a_purchase_twidget.insertRow(row)

        self.a_purchase_twidget.setItem(row, 0, date_item)
        self.a_purchase_twidget.setItem(row, 1, area_item)
        self.a_purchase_twidget.setItem(row, 2, price_item)
        self.a_purchase_twidget.setItem(row, 3, price_m2_item)

    def __home_lease_add(self):

        landuse_code = self.lease_use_type_cbox.itemData(self.lease_use_type_cbox.currentIndex())
        landuse_text = self.lease_use_type_cbox.currentText()
        if self.lease_duration_edit.text() == "" or self.lease_duration_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Duration Month"))
            return
        if self.lease_rent_edit.text() == "" or self.lease_rent_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Rent"))
            return
        if self.lease_twidget.rowCount() != 0:
            PluginUtils.show_message(self, self.tr("Row"), self.tr("Already inserted row"))
            return

        usetype_item = QTableWidgetItem(landuse_text)
        usetype_item.setData(Qt.UserRole, landuse_code)
        date_item = QTableWidgetItem(self.lease_dateEdit.text())
        date_item.setData(Qt.UserRole, self.lease_dateEdit.text())
        duration_item = QTableWidgetItem(self.lease_duration_edit.text())
        duration_item.setData(Qt.UserRole, self.lease_duration_edit.text())
        area_item = QTableWidgetItem(self.lease_area_edit.text())
        area_item.setData(Qt.UserRole, self.lease_area_edit.text())
        rent_item = QTableWidgetItem(self.lease_rent_edit.text())
        rent_item.setData(Qt.UserRole, self.lease_rent_edit.text())
        rent_m2_item = QTableWidgetItem(self.lease_rent_of_m2.text())
        rent_m2_item.setData(Qt.UserRole, self.lease_rent_of_m2.text())

        row = self.lease_twidget.rowCount()
        self.lease_twidget.insertRow(row)

        self.lease_twidget.setItem(row, 0, usetype_item)
        self.lease_twidget.setItem(row, 1, date_item)
        self.lease_twidget.setItem(row, 2, duration_item)
        self.lease_twidget.setItem(row, 3, area_item)
        self.lease_twidget.setItem(row, 4, rent_item)
        self.lease_twidget.setItem(row, 5, rent_m2_item)

    def __commercial_lease_add(self):

        landuse_code = self.c_lease_use_type_cbox.itemData(self.c_lease_use_type_cbox.currentIndex())
        landuse_text = self.c_lease_use_type_cbox.currentText()
        if self.c_lease_duration_edit.text() == "" or self.c_lease_duration_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Duration Month"))
            return
        if self.c_lease_expenses_edit.text() == "" or self.c_lease_expenses_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Rent"))
            return
        if self.c_lease_twidget.rowCount() != 0:
            PluginUtils.show_message(self, self.tr("Row"), self.tr("Already inserted row"))
            return

        usetype_item = QTableWidgetItem(landuse_text)
        usetype_item.setData(Qt.UserRole, landuse_code)
        date_item = QTableWidgetItem(self.c_lease_dateEdit.text())
        date_item.setData(Qt.UserRole, self.c_lease_dateEdit.text())
        duration_item = QTableWidgetItem(self.c_lease_duration_edit.text())
        duration_item.setData(Qt.UserRole, self.c_lease_duration_edit.text())
        area_item = QTableWidgetItem(self.c_lease_area_edit.text())
        area_item.setData(Qt.UserRole, self.c_lease_area_edit.text())
        rent_item = QTableWidgetItem(self.c_lease_expenses_edit.text())
        rent_item.setData(Qt.UserRole, self.c_lease_expenses_edit.text())
        rent_m2_item = QTableWidgetItem(self.c_lease_rent_of_m2.text())
        rent_m2_item.setData(Qt.UserRole, self.c_lease_rent_of_m2.text())

        row = self.c_lease_twidget.rowCount()
        self.c_lease_twidget.insertRow(row)

        self.c_lease_twidget.setItem(row, 0, usetype_item)
        self.c_lease_twidget.setItem(row, 1, date_item)
        self.c_lease_twidget.setItem(row, 2, duration_item)
        self.c_lease_twidget.setItem(row, 3, area_item)
        self.c_lease_twidget.setItem(row, 4, rent_item)
        self.c_lease_twidget.setItem(row, 5, rent_m2_item)

    def __industrial_lease_add(self):

        landuse_code = self.i_lease_use_type_cbox.itemData(self.i_lease_use_type_cbox.currentIndex())
        landuse_text = self.i_lease_use_type_cbox.currentText()
        if self.i_lease_duration_edit.text() == "" or self.i_lease_duration_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Duration Month"))
            return
        if self.i_lease_month_edit.text() == "" or self.i_lease_month_edit.text() == None:
            PluginUtils.show_mesage(self, self.tr("Error"), self.tr("No Rent"))
            return
        if self.i_lease_twidget.rowCount() != 0:
            PluginUtils.show_message(self, self.tr("Row"), self.tr("Already inserted row"))
            return

        usetype_item = QTableWidgetItem(landuse_text)
        usetype_item.setData(Qt.UserRole, landuse_code)
        date_item = QTableWidgetItem(self.i_lease_dateEdit.text())
        date_item.setData(Qt.UserRole, self.i_lease_dateEdit.dateTime())
        duration_item = QTableWidgetItem(self.i_lease_duration_edit.text())
        duration_item.setData(Qt.UserRole, self.i_lease_duration_edit.text())
        area_item = QTableWidgetItem(self.i_lease_area_edit.text())
        area_item.setData(Qt.UserRole, self.i_lease_area_edit.text())
        rent_item = QTableWidgetItem(self.i_lease_month_edit.text())
        rent_item.setData(Qt.UserRole, self.i_lease_month_edit.text())
        rent_m2_item = QTableWidgetItem(self.i_lease_rent_of_m2.text())
        rent_m2_item.setData(Qt.UserRole, self.i_lease_rent_of_m2.text())

        row = self.i_lease_twidget.rowCount()
        self.i_lease_twidget.insertRow(row)

        self.i_lease_twidget.setItem(row, 0, usetype_item)
        self.i_lease_twidget.setItem(row, 1, date_item)
        self.i_lease_twidget.setItem(row, 2, duration_item)
        self.i_lease_twidget.setItem(row, 3, area_item)
        self.i_lease_twidget.setItem(row, 4, rent_item)
        self.i_lease_twidget.setItem(row, 5, rent_m2_item)

    def __agricalture_lease_add(self):

        if self.a_lease_duration_edit.text() == "" or self.a_lease_duration_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Duration Month"))
            return
        if self.a_lease_rent_edit.text() == "" or self.a_lease_rent_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Rent"))
            return
        if self.a_lease_twidget.rowCount() != 0:
            PluginUtils.show_message(self, self.tr("Row"), self.tr("Already inserted row"))
            return

        date_item = QTableWidgetItem(self.a_lease_dateEdit.text())
        date_item.setData(Qt.UserRole, self.a_lease_dateEdit.text())
        duration_item = QTableWidgetItem(self.a_lease_duration_edit.text())
        duration_item.setData(Qt.UserRole, self.a_lease_duration_edit.text())
        area_item = QTableWidgetItem(self.a_lease_area_edit.text())
        area_item.setData(Qt.UserRole, self.a_lease_area_edit.text())
        rent_item = QTableWidgetItem(self.a_lease_rent_edit.text())
        rent_item.setData(Qt.UserRole, self.a_lease_rent_edit.text())
        rent_m2_item = QTableWidgetItem(self.a_lease_rent_of_m2.text())
        rent_m2_item.setData(Qt.UserRole, self.a_lease_rent_of_m2.text())

        row = self.a_lease_twidget.rowCount()
        self.a_lease_twidget.insertRow(row)

        self.a_lease_twidget.setItem(row, 0, date_item)
        self.a_lease_twidget.setItem(row, 1, duration_item)
        self.a_lease_twidget.setItem(row, 2, area_item)
        self.a_lease_twidget.setItem(row, 3, rent_item)
        self.a_lease_twidget.setItem(row, 4, rent_m2_item)

    def __home_building_add(self):

        session = SessionHandler().session_instance()
        if self.building_use_type_cbox.itemData(self.building_use_type_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Use Type"))
            return
        if self.building_stove_type_cbox.itemData(self.building_stove_type_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Stove Type"))
            return
        if self.building_material_cbox.itemData(self.building_material_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Material Type"))
            return
        if self.building_heat_Insulation_cbox.itemData(self.building_heat_Insulation_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Heat Insulation Type"))
            return
        if self.no_floor_sbox.value() == 0:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Floor"))
            return
        all_rows = self.home_building_twidget.rowCount()
        for row in xrange(0,all_rows):
            building_id = self.home_building_twidget.item(row, 0)
            if building_id.text() == str(self.building_no_cbox.currentText()):
                PluginUtils.show_message(self, self.tr("Error"), self.tr("Already added"))
                return
        landuse_code = self.building_use_type_cbox.itemData(self.building_use_type_cbox.currentIndex())
        landuse_text = self.building_use_type_cbox.currentText()

        building_code = self.building_no_cbox.itemData(self.building_no_cbox.currentIndex())
        buidling_text = self.building_no_cbox.currentText()

        stove_code = self.building_stove_type_cbox.itemData(self.building_stove_type_cbox.currentIndex())
        stove_text = self.building_stove_type_cbox.currentText()

        material_code = self.building_material_cbox.itemData(self.building_material_cbox.currentIndex())
        material_text = self.building_material_cbox.currentText()

        design_code = self.building_design_cbox.itemData(self.building_design_cbox.currentIndex())
        design_text = self.building_design_cbox.currentText()

        heat_code = self.building_heat_Insulation_cbox.itemData(self.building_heat_Insulation_cbox.currentIndex())
        heat_text = self.building_heat_Insulation_cbox.currentText()

        if self.b_status_good_rbutton.isChecked():
            status_code = 10
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 10).one()
            status_text = status.description
        elif self.b_status_medium_rbutton.isChecked():
            status_code = 20
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 20).one()
            status_text = status.description
        elif self.b_status_bad_rbutton.isChecked():
            status_code = 30
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 30).one()
            status_text = status.description

        landuse_item = QTableWidgetItem(landuse_text)
        landuse_item.setData(Qt.UserRole, landuse_code)
        building_item = QTableWidgetItem(buidling_text)
        building_item.setData(Qt.UserRole, building_code)
        stove_item = QTableWidgetItem(stove_text)
        stove_item.setData(Qt.UserRole, stove_code)
        design_item = QTableWidgetItem(design_text)
        design_item.setData(Qt.UserRole, design_code)
        material_item = QTableWidgetItem(material_text)
        material_item.setData(Qt.UserRole, material_code)
        heat_item = QTableWidgetItem(heat_text)
        heat_item.setData(Qt.UserRole, heat_code)
        status_item = QTableWidgetItem(status_text)
        status_item.setData(Qt.UserRole, status_code)
        area_item = QTableWidgetItem(self.building_area_edit.text())
        area_item.setData(Qt.UserRole, self.building_area_edit.text())
        construction_item = QTableWidgetItem(self.building_construction_year_edit.text())
        construction_item.setData(Qt.UserRole, self.building_construction_year_edit.text())
        floor_item = QTableWidgetItem(str(self.no_floor_sbox.value()))
        floor_item.setData(Qt.UserRole, self.no_floor_sbox.value())
        room_item = QTableWidgetItem(str(self.no_room_sbox.value()))
        room_item.setData(Qt.UserRole, self.no_room_sbox.value())
        status_year_item = QTableWidgetItem(self.building_status_year_date.text())
        status_year_item.setData(Qt.UserRole, self.building_status_year_date.text())

        row = self.home_building_twidget.rowCount()
        self.home_building_twidget.insertRow(row)

        self.home_building_twidget.setItem(row, 0, building_item)
        self.home_building_twidget.setItem(row, 1, landuse_item)
        self.home_building_twidget.setItem(row, 2, area_item)
        self.home_building_twidget.setItem(row, 3, design_item)
        self.home_building_twidget.setItem(row, 4, material_item)
        self.home_building_twidget.setItem(row, 5, construction_item)
        self.home_building_twidget.setItem(row, 6, floor_item)
        self.home_building_twidget.setItem(row, 7, room_item)
        self.home_building_twidget.setItem(row, 8, stove_item)
        self.home_building_twidget.setItem(row, 9, heat_item)
        self.home_building_twidget.setItem(row, 10, status_item)
        self.home_building_twidget.setItem(row, 11, status_year_item)

    def __industrial_building_add(self):

        session = SessionHandler().session_instance()
        if self.i_building_use_type_cbox.itemData(self.i_building_use_type_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Use Type"))
            return
        if self.i_building_material_cbox.itemData(self.i_building_material_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Material Type"))
            return
        if self.i_building_no_floor_sbox.value() == 0:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Floor"))
            return
        all_rows = self.i_building_twidget.rowCount()
        for row in xrange(0,all_rows):
            building_id = self.i_building_twidget.item(row, 0)
            if building_id.text() == str(self.i_building_no_cbox.currentText()):
                PluginUtils.show_message(self, self.tr("Error"), self.tr("Already added"))
                return
        landuse_code = self.i_building_use_type_cbox.itemData(self.i_building_use_type_cbox.currentIndex())
        landuse_text = self.i_building_use_type_cbox.currentText()

        building_code = self.i_building_no_cbox.itemData(self.i_building_no_cbox.currentIndex())
        buidling_text = self.i_building_no_cbox.currentText()

        material_code = self.i_building_material_cbox.itemData(self.i_building_material_cbox.currentIndex())
        material_text = self.i_building_material_cbox.currentText()

        if self.i_building_good_rbutton.isChecked():
            status_code = 10
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 10).one()
            status_text = status.description
        elif self.i_building_medium_rbutton.isChecked():
            status_code = 20
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 20).one()
            status_text = status.description
        elif self.i_building_bad_rbutton.isChecked():
            status_code = 30
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 30).one()
            status_text = status.description
        else:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Select status"))
            return

        landuse_item = QTableWidgetItem(landuse_text)
        landuse_item.setData(Qt.UserRole, landuse_code)
        building_item = QTableWidgetItem(buidling_text)
        building_item.setData(Qt.UserRole, building_code)
        material_item = QTableWidgetItem(material_text)
        material_item.setData(Qt.UserRole, material_code)
        status_item = QTableWidgetItem(status_text)
        status_item.setData(Qt.UserRole, status_code)
        area_item = QTableWidgetItem(self.i_building_area_edit.text())
        area_item.setData(Qt.UserRole, self.i_building_area_edit.text())
        construction_item = QTableWidgetItem(self.i_building_year_construction_date.value())
        construction_item.setData(Qt.UserRole, self.i_building_year_construction_date.value())
        floor_item = QTableWidgetItem(str(self.i_building_no_floor_sbox.value()))
        floor_item.setData(Qt.UserRole, self.i_building_no_floor_sbox.value())

        row = self.i_building_twidget.rowCount()
        self.i_building_twidget.insertRow(row)

        self.i_building_twidget.setItem(row, 0, building_item)
        self.i_building_twidget.setItem(row, 1, landuse_item)
        self.i_building_twidget.setItem(row, 2, area_item)
        self.i_building_twidget.setItem(row, 3, material_item)
        self.i_building_twidget.setItem(row, 4, construction_item)
        self.i_building_twidget.setItem(row, 5, floor_item)
        self.i_building_twidget.setItem(row, 6, status_item)

    def __industrial_product_add(self):

        session = SessionHandler().session_instance()
        if self.i_product_type_cbox.itemData(self.i_product_type_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Product Type"))
            return

        all_rows = self.i_product_twidget.rowCount()
        for row in xrange(0,all_rows):
            product_id = self.i_product_twidget.item(row, 0)
            if product_id.text() == (self.i_product_type_cbox.currentText()):
                PluginUtils.show_message(self, self.tr("Error"), self.tr("Already added"))
                return
        product_code = self.i_product_type_cbox.itemData(self.i_product_type_cbox.currentIndex())
        product_text = self.i_product_type_cbox.currentText()

        if self.i_status_bad_rbutton.isChecked():
            status_code = 10
            status = session.query(VaTypeIndustrialProcess).filter(VaTypeIndustrialProcess.code == 10).one()
            status_text = status.description
        elif self.i_status_medium_rbutton.isChecked():
            status_code = 20
            status = session.query(VaTypeIndustrialProcess).filter(VaTypeIndustrialProcess.code == 20).one()
            status_text = status.description
        elif self.i_status_good_rbutton.isChecked():
            status_code = 30
            status = session.query(VaTypeIndustrialProcess).filter(VaTypeIndustrialProcess.code == 30).one()
            status_text = status.description
        else:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Select industrial process"))
            return

        if self.i_day_rbutton.isChecked():
            time_code = 10
            time = session.query(VaTypeProductTime).filter(VaTypeProductTime.code == 10).one()
            time_text = time.description
        elif self.i_month_rbutton.isChecked():
            time_code = 20
            time = session.query(VaTypeProductTime).filter(VaTypeProductTime.code == 20).one()
            time_text = time.description
        elif self.i_year_rbutton.isChecked():
            time_code = 30
            time = session.query(VaTypeProductTime).filter(VaTypeProductTime.code == 30).one()
            time_text = time.description
        else:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Select time"))
            return

        product_item = QTableWidgetItem(product_text)
        product_item.setData(Qt.UserRole, product_code)

        come_per_item = QTableWidgetItem(self.i_income_item_edit.text())
        come_per_item.setData(Qt.UserRole, self.i_income_item_edit.text())
        cost_per_item = QTableWidgetItem(self.i_cost_item_edit.text())
        cost_per_item.setData(Qt.UserRole, self.i_cost_item_edit.text())
        count_item = QTableWidgetItem(str(self.i_product_no_sbox.value()))
        count_item.setData(Qt.UserRole, self.i_product_no_sbox.value())
        time_item = QTableWidgetItem(time_text)
        time_item.setData(Qt.UserRole, time_code)
        process_item = QTableWidgetItem(status_text)
        process_item.setData(Qt.UserRole, status_code)

        row = self.i_product_twidget.rowCount()
        self.i_product_twidget.insertRow(row)

        self.i_product_twidget.setItem(row, 0, product_item)
        self.i_product_twidget.setItem(row, 1, come_per_item)
        self.i_product_twidget.setItem(row, 2, cost_per_item)
        self.i_product_twidget.setItem(row, 3, count_item)
        self.i_product_twidget.setItem(row, 4, time_item)
        self.i_product_twidget.setItem(row, 5, process_item)

    def __agriculture_building_add(self):

        session = SessionHandler().session_instance()
        if self.a_building_use_type_cbox.itemData(self.a_building_use_type_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Use Type"))
            return
        if self.a_building_material_cbox.itemData(self.a_building_material_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Material Type"))
            return
        all_rows = self.a_building_twidget.rowCount()
        for row in xrange(0,all_rows):
            building_id = self.a_building_twidget.item(row, 0)
            if building_id.text() == str(self.a_building_no_cbox.currentText()):
                PluginUtils.show_message(self, self.tr("Error"), self.tr("Already added"))
                return
        landuse_code = self.a_building_use_type_cbox.itemData(self.a_building_use_type_cbox.currentIndex())
        landuse_text = self.a_building_use_type_cbox.currentText()

        building_code = self.a_building_no_cbox.itemData(self.a_building_no_cbox.currentIndex())
        buidling_text = self.a_building_no_cbox.currentText()

        material_code = self.a_building_material_cbox.itemData(self.a_building_material_cbox.currentIndex())
        material_text = self.a_building_material_cbox.currentText()

        landuse_item = QTableWidgetItem(landuse_text)
        landuse_item.setData(Qt.UserRole, landuse_code)
        building_item = QTableWidgetItem(buidling_text)
        building_item.setData(Qt.UserRole, building_code)
        material_item = QTableWidgetItem(material_text)
        material_item.setData(Qt.UserRole, material_code)
        area_item = QTableWidgetItem(self.a_building_area_edit.text())
        area_item.setData(Qt.UserRole, self.a_building_area_edit.text())
        price_item = QTableWidgetItem(self.a_building_price_edit.text())
        price_item.setData(Qt.UserRole, self.a_building_price_edit.text())
        construction_item = QTableWidgetItem(self.a_building_year_construction_date.value())
        construction_item.setData(Qt.UserRole, self.a_building_year_construction_date.value())

        row = self.a_building_twidget.rowCount()
        self.a_building_twidget.insertRow(row)

        self.a_building_twidget.setItem(row, 0, building_item)
        self.a_building_twidget.setItem(row, 1, landuse_item)
        self.a_building_twidget.setItem(row, 2, area_item)
        self.a_building_twidget.setItem(row, 3, material_item)
        self.a_building_twidget.setItem(row, 4, construction_item)
        self.a_building_twidget.setItem(row, 5, price_item)

    def __agriculture_add(self):

        session = SessionHandler().session_instance()
        if self.a_use_type_cbox.itemData(self.a_use_type_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Use Type"))
            return
        if self.a_crop_type_cbox.itemData(self.a_crop_type_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Crop Type"))
            return
        all_rows = self.agriculture_twidget.rowCount()
        for row in xrange(0,all_rows):
            crop_id = self.agriculture_twidget.item(row, 1)
            if crop_id.data(Qt.UserRole) == (self.a_crop_type_cbox.currentIndex()):
                PluginUtils.show_message(self, self.tr("Error"), self.tr("Already added crop type"))
                return
        landuse_code = self.a_use_type_cbox.itemData(self.a_use_type_cbox.currentIndex())
        landuse_text = self.a_use_type_cbox.currentText()

        crop_code = self.a_crop_type_cbox.itemData(self.a_crop_type_cbox.currentIndex())
        crop_text = self.a_crop_type_cbox.currentText()

        landuse_item = QTableWidgetItem(landuse_text)
        landuse_item.setData(Qt.UserRole, landuse_code)
        crop_item = QTableWidgetItem(crop_text)
        crop_item.setData(Qt.UserRole, crop_code)

        if self.a_area_edit.text() == '':
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Empty area"))
            return
        area_item = QTableWidgetItem(self.a_area_edit.text())
        area_item.setData(Qt.UserRole, self.a_area_edit.text())

        if self.a_yield_edit.text() == '':
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Empty yield"))
            return
        yield_item = QTableWidgetItem(self.a_yield_edit.text())
        yield_item.setData(Qt.UserRole, self.a_yield_edit.text())

        if self.a_costs_edit.text() == '':
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Empty costs"))
            return
        costs_item = QTableWidgetItem(self.a_costs_edit.text())
        costs_item.setData(Qt.UserRole, self.a_costs_edit.text())

        if self.a_profit_edit.text() == '':
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Empty profit"))
            return
        profit_item = QTableWidgetItem(self.a_profit_edit.text())
        profit_item.setData(Qt.UserRole, self.a_profit_edit.text())

        net_profit_item = QTableWidgetItem(self.a_net_profit_edit.text())
        net_profit_item.setData(Qt.UserRole, self.a_net_profit_edit.text())

        row = self.agriculture_twidget.rowCount()
        self.agriculture_twidget.insertRow(row)

        self.agriculture_twidget.setItem(row, 0, landuse_item)
        self.agriculture_twidget.setItem(row, 1, crop_item)
        self.agriculture_twidget.setItem(row, 2, area_item)

        self.agriculture_twidget.setItem(row, 3, yield_item)
        self.agriculture_twidget.setItem(row, 4, costs_item)

        self.agriculture_twidget.setItem(row, 5, profit_item)
        self.agriculture_twidget.setItem(row, 6, net_profit_item)

    def __agriculture_other_add(self):

        session = SessionHandler().session_instance()
        if self.a_irrigation_type_cbox.itemData(self.a_irrigation_type_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Irrigation Type"))
            return

        all_rows = self.a_other_twidget.rowCount()
        for row in xrange(0,all_rows):
            irrigation_id = self.a_other_twidget.item(row, 0)
            if irrigation_id.data(Qt.UserRole) == (self.a_irrigation_type_cbox.currentIndex()):
                PluginUtils.show_message(self, self.tr("Error"), self.tr("Already added irrigation type"))
                return
        irrigation_code = self.a_irrigation_type_cbox.itemData(self.a_irrigation_type_cbox.currentIndex())
        irrigation_text = self.a_irrigation_type_cbox.currentText()

        irrigation_item = QTableWidgetItem(irrigation_text)
        irrigation_item.setData(Qt.UserRole, irrigation_code)

        if self.a_other_price_edit.text() == '':
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Empty price"))
            return
        price_item = QTableWidgetItem(self.a_other_price_edit.text())
        price_item.setData(Qt.UserRole, self.a_other_price_edit.text())

        other_item = QTableWidgetItem(self.a_other_comment_edit.toPlainText())
        other_item.setData(Qt.UserRole, self.a_other_comment_edit.toPlainText())

        row = self.a_other_twidget.rowCount()
        self.a_other_twidget.insertRow(row)

        self.a_other_twidget.setItem(row, 0, irrigation_item)
        self.a_other_twidget.setItem(row, 1, price_item)
        self.a_other_twidget.setItem(row, 2, other_item)

    def __commercial_building_add(self):

        session = SessionHandler().session_instance()
        if self.c_building_use_type_cbox.itemData(self.c_building_use_type_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Use Type"))
            return
        if self.c_building_esystem_cbox.itemData(self.c_building_esystem_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Engineering System Type"))
            return
        if self.c_building_material_cbox.itemData(self.building_material_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Material Type"))
            return
        if self.c_building_design_cbox.itemData(self.c_building_design_cbox.currentIndex()) == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Design Type"))
            return
        if self.c_no_floor_sbox.value() == 0:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Floor"))
            return
        if self.c_no_room_sbox.value() == 0:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Room"))
            return
        all_rows = self.c_building_twidget.rowCount()
        for row in xrange(0,all_rows):
            building_id = self.c_building_twidget.item(row, 0)
            if building_id.text() == str(self.c_building_no_cbox.currentText()):
                PluginUtils.show_message(self, self.tr("Error"), self.tr("Already added"))
                return
        landuse_code = self.c_building_use_type_cbox.itemData(self.c_building_use_type_cbox.currentIndex())
        landuse_text = self.c_building_use_type_cbox.currentText()

        building_code = self.c_building_no_cbox.itemData(self.c_building_no_cbox.currentIndex())
        buidling_text = self.c_building_no_cbox.currentText()

        esystem_code = self.c_building_esystem_cbox.itemData(self.c_building_esystem_cbox.currentIndex())
        esystem_text = self.c_building_esystem_cbox.currentText()

        material_code = self.c_building_material_cbox.itemData(self.c_building_material_cbox.currentIndex())
        material_text = self.c_building_material_cbox.currentText()

        design_code = self.c_building_design_cbox.itemData(self.c_building_design_cbox.currentIndex())
        design_text = self.c_building_design_cbox.currentText()

        if self.c_b_status_good_rbutton.isChecked():
            status_code = 10
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 10).one()
            status_text = status.description
        elif self.c_b_status_medium_rbutton.isChecked():
            status_code = 20
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 20).one()
            status_text = status.description
        elif self.c_b_status_bad_rbutton.isChecked():
            status_code = 30
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 30).one()
            status_text = status.description
        else:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("Select status"))
            return

        landuse_item = QTableWidgetItem(landuse_text)
        landuse_item.setData(Qt.UserRole, landuse_code)
        building_item = QTableWidgetItem(buidling_text)
        building_item.setData(Qt.UserRole, building_code)
        esystem_item = QTableWidgetItem(esystem_text)
        esystem_item.setData(Qt.UserRole, esystem_code)
        design_item = QTableWidgetItem(design_text)
        design_item.setData(Qt.UserRole, design_code)
        material_item = QTableWidgetItem(material_text)
        material_item.setData(Qt.UserRole, material_code)
        status_item = QTableWidgetItem(status_text)
        status_item.setData(Qt.UserRole, status_code)
        area_item = QTableWidgetItem(self.c_building_area_edit.text())
        area_item.setData(Qt.UserRole, self.c_building_area_edit.text())
        construction_item = QTableWidgetItem(self.c_building_year_construction_date.value())
        construction_item.setData(Qt.UserRole, self.c_building_year_construction_date.value())
        floor_item = QTableWidgetItem(str(self.c_no_floor_sbox.value()))
        floor_item.setData(Qt.UserRole, self.c_no_floor_sbox.value())
        room_item = QTableWidgetItem(str(self.c_no_room_sbox.value()))
        room_item.setData(Qt.UserRole, self.c_no_room_sbox.value())

        row = self.c_building_twidget.rowCount()
        self.c_building_twidget.insertRow(row)

        self.c_building_twidget.setItem(row, 0, building_item)
        self.c_building_twidget.setItem(row, 1, landuse_item)
        self.c_building_twidget.setItem(row, 2, area_item)
        self.c_building_twidget.setItem(row, 3, design_item)
        self.c_building_twidget.setItem(row, 4, material_item)
        self.c_building_twidget.setItem(row, 5, floor_item)
        self.c_building_twidget.setItem(row, 6, room_item)
        self.c_building_twidget.setItem(row, 7, construction_item)
        self.c_building_twidget.setItem(row, 8, esystem_item)
        self.c_building_twidget.setItem(row, 9, status_item)

    def __home_general_save(self):

        session = SessionHandler().session_instance()
        home_count = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no == self.register_no).count()
        if home_count > 0:
            home_info = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no == self.register_no).one()
        else:
            home_info = VaInfoHomeParcel()

        register_no = self.home_num_first_edit.text() + "-" + self.home_num_type_edit.text() \
                       + "-" + self.home_num_middle_edit.text() + "-" + self.home_num_last_edit.text()

        home_info.register_no = register_no
        home_info.parcel_id = self.cadastreId_edit.text()
        if self.home_purchase_rbutton.isChecked():
            ok = DatabaseUtils.class_instance_by_code(VaTypePurchaseOrLease, 10)
            home_info.purchase_or_lease_type_ref = ok
        else:
            ok = DatabaseUtils.class_instance_by_code(VaTypePurchaseOrLease, 20)
            home_info.purchase_or_lease_type_ref = ok
        home_info.area_m2 = float(self.calculated_area_edit.text())
        home_info.info_date = DatabaseUtils.convert_date(self.registration_date.date())
        if self.decision_date_edit.text() == "" or self.decision_date_edit.text() == None:
            home_info.decision_date = None
        else:
            home_info.decision_date = (self.decision_date_edit.text())
        if self.duration_year_edit.text() == "" or self.duration_year_edit.text() == None or self.duration_year_edit.text() == 'None':
            home_info.approved_duration = None
        else:
            if self.duration_year_edit.text() == 'None':
                home_info.approved_duration = 0
            else:
                home_info.approved_duration = int(self.duration_year_edit.text())

        app_type_code = self.right_type_cbox.itemData(self.right_type_cbox.currentIndex())
        if app_type_code == -1:
            home_info.app_type = None
        else:
            app = DatabaseUtils.class_instance_by_code(ClApplicationType, app_type_code)
            home_info.app_type_ref = app
        source_type_code = self.source_cbox.itemData(self.source_cbox.currentIndex())
        if source_type_code == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Source Type"))
            return
        else:
            source = DatabaseUtils.class_instance_by_code(VaTypeSource, source_type_code)
            home_info.source_type_ref = source

        if self.electricity_yes_rbutton.isChecked():
            home_info.is_electricity = True
        elif self.electricity_no_rbutton.isChecked():
            home_info.is_electricity = False

        if self.heating_yes_rbutton.isChecked():
            home_info.is_central_heating = True
        elif self.heating_no_rbutton.isChecked():
            home_info.is_central_heating = False

        if self.water_yes_rbutton.isChecked():
            home_info.is_fresh_water = True
        elif self.water_no_rbutton.isChecked():
            home_info.is_fresh_water = False

        if self.sewage_yes_rbutton.isChecked():
            home_info.is_sewage = True
        elif self.sewage_no_rbutton.isChecked():
            home_info.is_sewage = False

        if self.well_yes_rbutton.isChecked():
            home_info.is_well = True
        elif self.well_no_rbutton.isChecked():
            home_info.is_well = False

        if self.finance_yes_rbutton.isChecked():
            home_info.is_self_financed_system = True
        elif self.finance_no_rbutton.isChecked():
            home_info.is_self_financed_system = False

        if self.phone_yes_rbutton.isChecked():
            home_info.is_telephone = True
        elif self.phone_no_rbutton.isChecked():
            home_info.is_telephone = False

        if self.flood_yes_rbutton.isChecked():
            home_info.is_flood_channel = True
        elif self.flood_no_rbutton.isChecked():
            home_info.is_flood_channel = False

        if self.plot_yes_rbutton.isChecked():
            home_info.is_vegetable_plot = True
        elif self.plot_no_rbutton.isChecked():
            home_info.is_vegetable_plot = False

        if self.slope_yes_rbutton.isChecked():
            home_info.is_land_slope = True
        elif self.slope_no_rbutton.isChecked():
            home_info.is_land_slope = False

        if self.side_fence_1_2_rbutton.isChecked():
            home_info.side_fence_type = 10
        elif self.side_fence_3_rbutton.isChecked():
            home_info.side_fence_type = 20
        elif self.side_fence_4_rbutton.isChecked():
            home_info.side_fence_type = 30
        elif self.side_fence_5_rbutton.isChecked():
            home_info.side_fence_type = 40

        if self.electricity_distancel_edit.text() != '':
            home_info.electricity_distancel = float(self.electricity_distancel_edit.text())
        else:
            home_info.electricity_distancel = None

        if self.electricity_connection_cost_edit.text() != '':
            home_info.electricity_conn_cost = float(self.electricity_connection_cost_edit.text())
        else:
            home_info.electricity_conn_cost = None

        if self.central_heat_distancel_edit.text() != '':
            home_info.central_heating_distancel = float(self.central_heat_distancel_edit.text())
        else:
            home_info.central_heating_distancel = None

        if self.central_heat_connection_cost_edit.text() != '':
            home_info.central_heating_conn_cost = float(self.central_heat_connection_cost_edit.text())
        else:
            home_info.central_heating_conn_cost = None

        if self.water_distancel_edit.text() != '':
            home_info.fresh_water_distancel = float(self.water_distancel_edit.text())
        else:
            home_info.fresh_water_distancel = None

        if self.water_connection_cost_edit.text() != '':
            home_info.fresh_water_conn_cost = float(self.water_connection_cost_edit.text())
        else:
            home_info.fresh_water_conn_cost = None

        if self.sewage_distancel_edit.text() != '':
            home_info.sewage_distancel = float(self.sewage_distancel_edit.text())
        else:
            home_info.sewage_distancel = None

        if self.sewage_connection_cost_edit.text() != '':
            home_info.sewage_conn_cost = float(self.sewage_connection_cost_edit.text())
        else:
            home_info.sewage_conn_cost = None

        if self.well_distancel_edit.text() != '':
            home_info.well_distancel = float(self.well_distancel_edit.text())
        else:
            home_info.well_distancel = None

        if self.phone_distancel_edit.text() != '':
            home_info.telephone_distancel = float(self.phone_distancel_edit.text())
        else:
            home_info.telephone_distancel = None

        if self.flood_channel_distancel_edit.text() != '':
            home_info.flood_channel_distancel = float(self.flood_channel_distancel_edit.text())
        else:
            home_info.flood_channel_distancel = None

        if self.vegetable_plot_size_edit.text() != '':
            home_info.vegetable_plot_size = float(self.vegetable_plot_size_edit.text())
        else:
            home_info.vegetable_plot_size = None

        if self.other_information_edit.toPlainText() != '':
            home_info.other_info = self.other_information_edit.toPlainText()
        else:
            home_info.other_info = None

        session.add(home_info)

    def __commercial_general_save(self):

        session = SessionHandler().session_instance()
        home_count = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no == self.register_no).count()
        if home_count > 0:
            home_info = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no == self.register_no).one()
        else:
            home_info = VaInfoHomeParcel()

        register_no = self.commercial_num_first_edit.text() + "-" + self.commercial_num_type_edit.text() \
                       + "-" + self.commercial_num_middle_edit.text() + "-" + self.commercial_num_last_edit.text()

        home_info.register_no = register_no
        home_info.parcel_id = self.c_cadastreId_edit.text()
        if self.c_purchase_rbutton.isChecked():
            ok = DatabaseUtils.class_instance_by_code(VaTypePurchaseOrLease, 10)
            home_info.purchase_or_lease_type_ref = ok
        else:
            ok = DatabaseUtils.class_instance_by_code(VaTypePurchaseOrLease, 20)
            home_info.purchase_or_lease_type_ref = ok
        home_info.area_m2 = float(self.c_calculated_area_edit.text())
        home_info.info_date = DatabaseUtils.convert_date(self.c_registration_date.date())
        if self.c_decision_date_edit.text() == "" or self.c_decision_date_edit.text() == None:
            home_info.decision_date = None
        else:
            home_info.decision_date = (self.c_decision_date_edit.text())
        if self.c_duration_edit.text() == "" or self.c_duration_edit.text() == None or self.c_duration_edit.text() == 'None':
            home_info.approved_duration = None
        else:
            if self.c_duration_edit.text() == 'None':
                home_info.approved_duration = 0
            else:
                home_info.approved_duration = int(self.c_duration_edit.text())

        app_type_code = self.c_right_type_cbox.itemData(self.c_right_type_cbox.currentIndex())
        if app_type_code == -1:
            home_info.app_type = None
        else:
            app = DatabaseUtils.class_instance_by_code(ClApplicationType, app_type_code)
            home_info.app_type_ref = app
        source_type_code = self.c_source_cbox.itemData(self.c_source_cbox.currentIndex())
        if source_type_code == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Source Type"))
            return
        else:
            source = DatabaseUtils.class_instance_by_code(VaTypeSource, source_type_code)
            home_info.source_type_ref = source

        if self.c_other_info_edit.toPlainText() != '':
            home_info.other_info = self.c_other_info_edit.toPlainText()
        else:
            home_info.other_info = None

        session.add(home_info)

    def __industrial_general_save(self):

        session = SessionHandler().session_instance()
        home_count = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no == self.register_no).count()
        if home_count > 0:
            home_info = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no == self.register_no).one()
        else:
            home_info = VaInfoHomeParcel()

        register_no = self.industrial_num_first_edit.text() + "-" + self.industrial_num_type_edit.text() \
                       + "-" + self.industrial_num_middle_edit.text() + "-" + self.industrial_num_last_edit.text()

        home_info.register_no = register_no
        home_info.parcel_id = self.i_cadastreid_edit.text()
        if self.i_purchase_rbutton.isChecked():
            ok = DatabaseUtils.class_instance_by_code(VaTypePurchaseOrLease, 10)
            home_info.purchase_or_lease_type_ref = ok
        else:
            ok = DatabaseUtils.class_instance_by_code(VaTypePurchaseOrLease, 20)
            home_info.purchase_or_lease_type_ref = ok
        home_info.area_m2 = float(self.i_calculated_area_edit.text())
        home_info.info_date = DatabaseUtils.convert_date(self.i_registration_date.date())
        if self.i_decision_date_edit.text() == "" or self.i_decision_date_edit.text() == None:
            home_info.decision_date = None
        else:
            home_info.decision_date = (self.i_decision_date_edit.text())
        if self.i_duration_edit.text() == "" or self.i_duration_edit.text() == None or self.i_duration_edit.text() == 'None':
            home_info.approved_duration = None
        else:
            if self.i_duration_edit.text() == 'None':
                home_info.approved_duration = 0
            else:
                home_info.approved_duration = int(self.i_duration_edit.text())

        app_type_code = self.i_right_type_cbox.itemData(self.i_right_type_cbox.currentIndex())
        if app_type_code == -1:
            home_info.app_type = None
        else:
            app = DatabaseUtils.class_instance_by_code(ClApplicationType, app_type_code)
            home_info.app_type_ref = app
        source_type_code = self.i_source_cbox.itemData(self.i_source_cbox.currentIndex())
        if source_type_code == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Source Type"))
            return
        else:
            source = DatabaseUtils.class_instance_by_code(VaTypeSource, source_type_code)
            home_info.source_type_ref = source

        if self.i_other_info_edit.toPlainText() != '':
            home_info.other_info = self.i_other_info_edit.toPlainText()
        else:
            home_info.other_info = None

        session.add(home_info)

    def __agriculture_general_save(self):

        session = SessionHandler().session_instance()
        home_count = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no == self.register_no).count()
        if home_count > 0:
            home_info = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no == self.register_no).one()
        else:
            home_info = VaInfoHomeParcel()

        register_no = self.agriculture_num_first_edit.text() + "-" + self.agriculture_num_type_edit.text() \
                       + "-" + self.agriculture_num_middle_edit.text() + "-" + self.agriculture_num_last_edit.text()

        home_info.register_no = register_no
        home_info.parcel_id = self.a_cadastreId_edit.text()
        if self.a_purchase_rbutton.isChecked():
            ok = DatabaseUtils.class_instance_by_code(VaTypePurchaseOrLease, 10)
            home_info.purchase_or_lease_type_ref = ok
        else:
            ok = DatabaseUtils.class_instance_by_code(VaTypePurchaseOrLease, 20)
            home_info.purchase_or_lease_type_ref = ok
        home_info.area_m2 = float(self.a_calculated_area_edit.text())
        home_info.info_date = DatabaseUtils.convert_date(self.a_registration_date.date())
        if self.a_decision_date_edit.text() == "" or self.a_decision_date_edit.text() == None:
            home_info.decision_date = None
        else:
            home_info.decision_date = (self.a_decision_date_edit.text())
        if self.a_duration_edit.text() == "" or self.a_duration_edit.text() == None or self.a_duration_edit.text() == 'None':
            home_info.approved_duration = None
        else:
            if self.a_duration_edit.text() == 'None':
                home_info.approved_duration = 0
            else:
                home_info.approved_duration = int(self.a_duration_edit.text())

        app_type_code = self.a_right_type_cbox.itemData(self.a_right_type_cbox.currentIndex())
        if app_type_code == -1:
            home_info.app_type = None
        else:
            app = DatabaseUtils.class_instance_by_code(ClApplicationType, app_type_code)
            home_info.app_type_ref = app
        source_type_code = self.a_source_cbox.itemData(self.a_source_cbox.currentIndex())
        if source_type_code == -1:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Source Type"))
            return
        else:
            source = DatabaseUtils.class_instance_by_code(VaTypeSource, source_type_code)
            home_info.source_type_ref = source

        if self.a_other_info_edit.toPlainText() != '':
            home_info.other_info = self.a_other_info_edit.toPlainText()
        else:
            home_info.other_info = None

        session.add(home_info)

    def __home_purchase_save(self):

        session = SessionHandler().session_instance()
        row_count = self.purchase_twidget.rowCount()
        if row_count == 0:
            return
        purchase_count = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).count()
        if purchase_count > 0:
            purchase = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).one()
        else:
            purchase = VaInfoHomePurchase()
        landuse_code = self.purchase_use_type_cbox.itemData(self.purchase_use_type_cbox.currentIndex())
        purchase_date = DatabaseUtils.convert_date(self.purchase_dateEdit.date())
        if landuse_code == -1:
            purchase.landuse_ref = None
        else:
            landuse = DatabaseUtils.class_instance_by_code(ClLanduseType, landuse_code)
            purchase.landuse_ref = landuse

        register_no = self.home_num_first_edit.text() + "-" + self.home_num_type_edit.text() \
                       + "-" + self.home_num_middle_edit.text() + "-" + self.home_num_last_edit.text()

        purchase.register_no = register_no
        purchase.area_m2 = float(self.purchase_area_edit.text())
        purchase.purchase_date = purchase_date
        purchase.price = float(self.purchase_price_edit.text())
        purchase.price_m2 = float(self.purchase_price_if_m2.text())

        session.add(purchase)

    def __commercial_purchase_save(self):

        session = SessionHandler().session_instance()
        row_count = self.c_purchase_twidget.rowCount()
        if row_count == 0:
            return
        purchase_count = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).count()
        if purchase_count > 0:
            purchase = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).one()
        else:
            purchase = VaInfoHomePurchase()
        landuse_code = self.c_purchase_use_type_cbox.itemData(self.c_purchase_use_type_cbox.currentIndex())
        purchase_date = DatabaseUtils.convert_date(self.c_purchase_dateEdit.date())
        if landuse_code == -1:
            purchase.landuse_ref = None
        else:
            landuse = DatabaseUtils.class_instance_by_code(ClLanduseType, landuse_code)
            purchase.landuse_ref = landuse

        register_no = self.register_no

        purchase.register_no = register_no
        purchase.area_m2 = float(self.c_purchase_area_edit.text())
        purchase.purchase_date = purchase_date
        purchase.price = float(self.c_purchase_price_edit.text())
        purchase.price_m2 = float(self.c_purchase_price_if_m2.text())

        session.add(purchase)

    def __industrial_purchase_save(self):

        session = SessionHandler().session_instance()
        row_count = self.i_purchase_twidget.rowCount()
        if row_count == 0:
            return
        purchase_count = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).count()
        if purchase_count > 0:
            purchase = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).one()
        else:
            purchase = VaInfoHomePurchase()
        landuse_code = self.i_purchase_use_type_cbox.itemData(self.i_purchase_use_type_cbox.currentIndex())
        purchase_date = DatabaseUtils.convert_date(self.i_purchase_date_edit.date())
        if landuse_code == -1:
            purchase.landuse_ref = None
        else:
            landuse = DatabaseUtils.class_instance_by_code(ClLanduseType, landuse_code)
            purchase.landuse_ref = landuse

        register_no = self.register_no

        purchase.register_no = register_no
        purchase.area_m2 = float(self.i_purchase_area_edit.text())
        purchase.purchase_date = purchase_date
        purchase.price = float(self.i_purchase_price_edit.text())
        purchase.price_m2 = float(self.i_purchase_price_if_m2.text())

        session.add(purchase)

    def __agriculture_purchase_save(self):

        session = SessionHandler().session_instance()
        row_count = self.a_purchase_twidget.rowCount()
        if row_count == 0:
            return
        purchase_count = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).count()
        if purchase_count > 0:
            purchase = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).one()
        else:
            purchase = VaInfoHomePurchase()
        parcel = session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_id).one()
        landuse_code = parcel.landuse
        purchase_date = DatabaseUtils.convert_date(self.a_purchase_dateEdit.date())
        if landuse_code == -1:
            purchase.landuse_ref = None
        else:
            landuse = DatabaseUtils.class_instance_by_code(ClLanduseType, landuse_code)
            purchase.landuse_ref = landuse

        register_no = self.register_no

        purchase.register_no = register_no
        purchase.area_m2 = float(self.a_purchase_area_edit.text())
        purchase.purchase_date = purchase_date
        purchase.price = float(self.a_price_edit.text())
        purchase.price_m2 = float(self.a_purchase_price_if_m2.text())

        session.add(purchase)

    def __home_lease_save(self):

        session = SessionHandler().session_instance()
        lease_count = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).count()
        if lease_count > 0:
            lease = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).one()
        else:
            lease = VaInfoHomeLease()
        landuse_code = self.lease_use_type_cbox.itemData(self.lease_use_type_cbox.currentIndex())
        lease_date = DatabaseUtils.convert_date(self.lease_dateEdit.date())
        if landuse_code == -1:
            lease.landuse_ref = None
        else:
            landuse = DatabaseUtils.class_instance_by_code(ClLanduseType, landuse_code)
            lease.landuse_ref = landuse

        register_no = self.home_num_first_edit.text() + "-" + self.home_num_type_edit.text() \
                       + "-" + self.home_num_middle_edit.text() + "-" + self.home_num_last_edit.text()
        lease.register_no = register_no
        lease.area_m2 = float(self.lease_area_edit.text())
        lease.lease_date = lease_date
        lease.duration_month = int(self.lease_duration_edit.text())
        lease.monthly_rent = float(self.lease_rent_edit.text())
        lease.rent_m2 = float(self.lease_rent_of_m2.text())

        session.add(lease)

    def __commercial_lease_save(self):

        session = SessionHandler().session_instance()
        lease_count = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).count()
        if lease_count > 0:
            lease = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).one()
        else:
            lease = VaInfoHomeLease()
        landuse_code = self.c_lease_use_type_cbox.itemData(self.c_lease_use_type_cbox.currentIndex())
        lease_date = DatabaseUtils.convert_date(self.c_lease_dateEdit.date())
        if landuse_code == -1:
            lease.landuse_ref = None
        else:
            landuse = DatabaseUtils.class_instance_by_code(ClLanduseType, landuse_code)
            lease.landuse_ref = landuse

        register_no = self.commercial_num_first_edit.text() + "-" + self.commercial_num_type_edit.text() \
                       + "-" + self.commercial_num_middle_edit.text() + "-" + self.commercial_num_last_edit.text()
        lease.register_no = register_no
        lease.area_m2 = float(self.c_lease_area_edit.text())
        lease.lease_date = lease_date
        lease.duration_month = int(self.c_lease_duration_edit.text())
        lease.monthly_rent = float(self.c_lease_expenses_edit.text())
        lease.rent_m2 = float(self.c_lease_rent_of_m2.text())

        session.add(lease)

    def __industrial_lease_save(self):

        session = SessionHandler().session_instance()
        lease_count = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).count()
        if lease_count > 0:
            lease = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).one()
        else:
            lease = VaInfoHomeLease()
        landuse_code = self.i_lease_use_type_cbox.itemData(self.i_lease_use_type_cbox.currentIndex())
        lease_date = DatabaseUtils.convert_date(self.c_lease_dateEdit.date())
        if landuse_code == -1:
            lease.landuse_ref = None
        else:
            landuse = DatabaseUtils.class_instance_by_code(ClLanduseType, landuse_code)
            lease.landuse_ref = landuse

        register_no = self.register_no
        lease.register_no = register_no
        lease.area_m2 = float(self.i_lease_area_edit.text())
        lease.lease_date = lease_date
        lease.duration_month = int(self.i_lease_duration_edit.text())
        lease.monthly_rent = float(self.i_lease_month_edit.text())
        lease.rent_m2 = float(self.i_lease_rent_of_m2.text())

        session.add(lease)

    def __agriculture_lease_save(self):

        session = SessionHandler().session_instance()
        lease_count = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).count()
        if lease_count > 0:
            lease = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).one()
        else:
            lease = VaInfoHomeLease()
        parcel = session.query(CaParcel).filter(CaParcel.parcel_id == self.parcel_id).one()
        landuse_code = parcel.landuse
        lease_date = DatabaseUtils.convert_date(self.a_lease_dateEdit.date())
        if landuse_code == -1:
            lease.landuse_ref = None
        else:
            landuse = DatabaseUtils.class_instance_by_code(ClLanduseType, landuse_code)
            lease.landuse_ref = landuse

        register_no = self.register_no
        lease.register_no = register_no
        lease.area_m2 = float(self.a_lease_area_edit.text())
        lease.lease_date = lease_date
        lease.duration_month = int(self.a_lease_duration_edit.text())
        lease.monthly_rent = float(self.a_lease_rent_edit.text())
        lease.rent_m2 = float(self.a_lease_rent_of_m2.text())

        session.add(lease)

    def __home_building_save(self):

        if self.home_building_twidget.rowCount() == 0:
            return

        register_no = self.home_num_first_edit.text() + "-" + self.home_num_type_edit.text() \
                       + "-" + self.home_num_middle_edit.text() + "-" + self.home_num_last_edit.text()
        session = SessionHandler().session_instance()
        #loop save
        all_rows = self.home_building_twidget.rowCount()
        for row in xrange(0,all_rows):
            building_count = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).count()
            if building_count > 0:
                building = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).one()
            else:
                building = VaInfoHomeBuilding()
            id_item = self.home_building_twidget.item(row, 0)
            building_id = id_item.data(Qt.UserRole)

            landuse_item = self.home_building_twidget.item(row, 1)
            landuse_type = landuse_item.data(Qt.UserRole)

            area_item = self.home_building_twidget.item(row, 2)
            area = area_item.data(Qt.UserRole)

            design_item = self.home_building_twidget.item(row, 3)
            design = design_item.data(Qt.UserRole)

            material_item = self.home_building_twidget.item(row, 4)
            material = material_item.data(Qt.UserRole)

            constraction_item = self.home_building_twidget.item(row, 5)
            constraction = constraction_item.data(Qt.UserRole)

            floor_item = self.home_building_twidget.item(row, 6)
            floor = floor_item.data(Qt.UserRole)

            room_item = self.home_building_twidget.item(row, 7)
            room = room_item.data(Qt.UserRole)

            stove_item = self.home_building_twidget.item(row, 8)
            stove = stove_item.data(Qt.UserRole)

            heat_item = self.home_building_twidget.item(row, 9)
            heat = heat_item.data(Qt.UserRole)

            status_item = self.home_building_twidget.item(row, 10)
            status = status_item.data(Qt.UserRole)

            status_year_item = self.home_building_twidget.item(row, 11)
            status_year = status_year_item.data(Qt.UserRole)

            if landuse_type == -1:
                building.landuse_building_ref = None
            else:
                landuse = DatabaseUtils.class_instance_by_code(VaTypeLanduseBuilding, int(landuse_type))
                building.landuse_building_ref = landuse
            if stove == -1:
                building.stove_type_ref = None
            else:
                stove = DatabaseUtils.class_instance_by_code(VaTypeStove, int(stove))
                building.stove_type_ref = stove
            if material == -1:
                building.material_type_ref = None
            else:
                material = DatabaseUtils.class_instance_by_code(VaTypeMaterial, int(material))
                building.material_type_ref = material
            if design == -1:
                building.design_type_ref = None
            else:
                design = DatabaseUtils.class_instance_by_code(VaTypeDesign, int(design))
                building.design_type_ref = design
            if heat == -1:
                building.heat_type_ref = None
            else:
                heat = DatabaseUtils.class_instance_by_code(VaTypeHeat, int(heat))
                building.heat_type_ref = heat
            ok = DatabaseUtils.class_instance_by_code(VaTypeStatusBuilding, int(status))
            building.building_status_ref = ok

            building.building_id = building_id
            building.area_m2 = float(area)
            building.floor = float(floor)
            building.room = float(room)
            building.status_year = int(status_year)
            building.construction_year = int(constraction)
            building.register_no = register_no
            session.add(building)

    def __commercial_building_save(self):

        if self.c_building_twidget.rowCount() == 0:
            return

        register_no = self.register_no
        session = SessionHandler().session_instance()
        #loop save
        all_rows = self.c_building_twidget.rowCount()
        for row in xrange(0,all_rows):
            building_count = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).count()
            if building_count > 0:
                building = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).one()
            else:
                building = VaInfoHomeBuilding()
            id_item = self.c_building_twidget.item(row, 0)
            building_id = id_item.data(Qt.UserRole)

            landuse_item = self.c_building_twidget.item(row, 1)
            landuse_type = landuse_item.data(Qt.UserRole)

            area_item = self.c_building_twidget.item(row, 2)
            area = area_item.data(Qt.UserRole)

            design_item = self.c_building_twidget.item(row, 3)
            design = design_item.data(Qt.UserRole)

            material_item = self.c_building_twidget.item(row, 4)
            material = material_item.data(Qt.UserRole)

            floor_item = self.c_building_twidget.item(row, 5)
            floor = floor_item.data(Qt.UserRole)

            room_item = self.c_building_twidget.item(row, 6)
            room = room_item.data(Qt.UserRole)

            constraction_item = self.c_building_twidget.item(row, 7)
            constraction = constraction_item.data(Qt.UserRole)

            esystem_item = self.c_building_twidget.item(row, 8)
            esystem_type = esystem_item.data(Qt.UserRole)

            status_item = self.c_building_twidget.item(row, 9)
            status = status_item.data(Qt.UserRole)

            if landuse_type == -1:
                building.landuse_building_ref = None
            else:
                landuse = DatabaseUtils.class_instance_by_code(VaTypeLanduseBuilding, int(landuse_type))
                building.landuse_building_ref = landuse

            if esystem_type == -1:
                building.building_esystem_ref = None
            else:
                esystem = DatabaseUtils.class_instance_by_code(VaTypeESystem, int(esystem_type))
                building.building_esystem_ref = esystem
            if material == -1:
                building.material_type_ref = None
            else:
                material = DatabaseUtils.class_instance_by_code(VaTypeMaterial, int(material))
                building.material_type_ref = material
            if design == -1:
                building.design_type_ref = None
            else:
                design = DatabaseUtils.class_instance_by_code(VaTypeDesign, int(design))
                building.design_type_ref = design

            ok = DatabaseUtils.class_instance_by_code(VaTypeStatusBuilding, int(status))
            building.building_status_ref = ok

            building.building_id = building_id
            building.area_m2 = float(area)
            building.floor = float(floor)
            building.room = float(room)
            building.construction_year = int(constraction)
            building.register_no = register_no
            session.add(building)

    def __industrial_building_save(self):

        if self.i_building_twidget.rowCount() == 0:
            return

        register_no = self.register_no
        session = SessionHandler().session_instance()
        #loop save
        all_rows = self.i_building_twidget.rowCount()
        for row in xrange(0,all_rows):
            building_count = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).count()
            if building_count > 0:
                building = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).one()
            else:
                building = VaInfoHomeBuilding()
            id_item = self.i_building_twidget.item(row, 0)
            building_id = id_item.data(Qt.UserRole)

            landuse_item = self.i_building_twidget.item(row, 1)
            landuse_type = landuse_item.data(Qt.UserRole)

            area_item = self.i_building_twidget.item(row, 2)
            area = area_item.data(Qt.UserRole)

            material_item = self.i_building_twidget.item(row, 3)
            material = material_item.data(Qt.UserRole)

            constraction_item = self.i_building_twidget.item(row, 4)
            constraction = constraction_item.data(Qt.UserRole)

            floor_item = self.i_building_twidget.item(row, 5)
            floor = floor_item.data(Qt.UserRole)

            status_item = self.i_building_twidget.item(row, 6)
            status = status_item.data(Qt.UserRole)

            if landuse_type == -1:
                building.landuse_building_ref = None
            else:
                landuse = DatabaseUtils.class_instance_by_code(VaTypeLanduseBuilding, int(landuse_type))
                building.landuse_building_ref = landuse
            if material == -1:
                building.material_type_ref = None
            else:
                material = DatabaseUtils.class_instance_by_code(VaTypeMaterial, int(material))
                building.material_type_ref = material

            ok = DatabaseUtils.class_instance_by_code(VaTypeStatusBuilding, int(status))
            building.building_status_ref = ok

            building.building_id = building_id
            building.area_m2 = float(area)
            building.floor = float(floor)
            building.construction_year = int(constraction)
            building.register_no = register_no
            session.add(building)

    def __industrial_product_save(self):

        if self.i_product_twidget.rowCount() == 0:
            return

        register_no = self.register_no
        session = SessionHandler().session_instance()
        #loop save
        all_rows = self.i_product_twidget.rowCount()
        for row in xrange(0,all_rows):
            product_count = session.query(VaInfoIndustrialProduct).filter(VaInfoIndustrialProduct.register_no == self.register_no).count()
            if product_count > 0:
                product = session.query(VaInfoIndustrialProduct).filter(VaInfoIndustrialProduct.register_no == self.register_no).one()
            else:
                product = VaInfoIndustrialProduct()
            id_item = self.i_product_twidget.item(row, 0)
            product_id = id_item.data(Qt.UserRole)

            come_per_item = self.i_product_twidget.item(row, 1)
            come_per = come_per_item.data(Qt.UserRole)

            cost_per_item = self.i_product_twidget.item(row, 2)
            cost_per = cost_per_item.data(Qt.UserRole)

            count_item = self.i_product_twidget.item(row, 3)
            product_count = count_item.data(Qt.UserRole)

            time_item = self.i_product_twidget.item(row, 4)
            time = time_item.data(Qt.UserRole)

            process_item = self.i_product_twidget.item(row, 5)
            process = process_item.data(Qt.UserRole)

            if product_id == -1:
                product.product_ref = None
            else:
                product_type = DatabaseUtils.class_instance_by_code(VaTypeProduct, int(product_id))
                product.product_ref = product_type

            time = DatabaseUtils.class_instance_by_code(VaTypeProductTime, int(time))
            product.product_time_ref = time

            ok = DatabaseUtils.class_instance_by_code(VaTypeIndustrialProcess, int(process))
            product.industrial_process_ref = ok

            product.count_product = float(product_count)
            product.cost_per_item = float(cost_per)
            product.come_per_item = float(come_per)
            product.register_no = register_no
            session.add(product)

    def __agriculture_building_save(self):

        if self.a_building_twidget.rowCount() == 0:
            return

        register_no = self.register_no
        session = SessionHandler().session_instance()
        #loop save
        all_rows = self.a_building_twidget.rowCount()
        for row in xrange(0,all_rows):
            building_count = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).count()
            if building_count > 0:
                building = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).one()
            else:
                building = VaInfoHomeBuilding()
            id_item = self.a_building_twidget.item(row, 0)
            building_id = id_item.data(Qt.UserRole)

            landuse_item = self.a_building_twidget.item(row, 1)
            landuse_type = landuse_item.data(Qt.UserRole)

            area_item = self.a_building_twidget.item(row, 2)
            area = area_item.data(Qt.UserRole)

            material_item = self.a_building_twidget.item(row, 3)
            material = material_item.data(Qt.UserRole)

            constraction_item = self.a_building_twidget.item(row, 4)
            constraction = constraction_item.data(Qt.UserRole)

            price_item = self.a_building_twidget.item(row, 5)
            price = price_item.data(Qt.UserRole)

            if landuse_type == -1:
                building.landuse_building_ref = None
            else:
                landuse = DatabaseUtils.class_instance_by_code(VaTypeLanduseBuilding, int(landuse_type))
                building.landuse_building_ref = landuse
            if material == -1:
                building.material_type_ref = None
            else:
                material = DatabaseUtils.class_instance_by_code(VaTypeMaterial, int(material))
                building.material_type_ref = material

            building.building_id = building_id
            building.area_m2 = float(area)
            building.price = float(price)
            building.construction_year = int(constraction)
            building.register_no = register_no
            session.add(building)

    def __agriculture_save(self):

        if self.agriculture_twidget.rowCount() == 0:
            return

        register_no = self.register_no
        session = SessionHandler().session_instance()
        #loop save
        all_rows = self.agriculture_twidget.rowCount()
        for row in xrange(0,all_rows):
            acr_count = session.query(VaInfoAgriculture).filter(VaInfoAgriculture.register_no == self.register_no).count()
            if acr_count > 0:
                acriculture = session.query(VaInfoAgriculture).filter(VaInfoAgriculture.register_no == self.register_no).one()
            else:
                acriculture = VaInfoAgriculture()

            landuse_item = self.agriculture_twidget.item(row, 0)
            landuse_type = landuse_item.data(Qt.UserRole)

            crop_item = self.agriculture_twidget.item(row, 1)
            crop_type = crop_item.data(Qt.UserRole)

            area_item = self.agriculture_twidget.item(row, 2)
            area = area_item.data(Qt.UserRole)

            yield_item = self.agriculture_twidget.item(row, 3)
            yield_ga = yield_item.data(Qt.UserRole)

            cost_item = self.agriculture_twidget.item(row, 4)
            cost = cost_item.data(Qt.UserRole)

            profit_item = self.agriculture_twidget.item(row, 5)
            profit = profit_item.data(Qt.UserRole)

            net_profit_item = self.agriculture_twidget.item(row, 6)
            net_profit = net_profit_item.data(Qt.UserRole)

            if landuse_type == -1:
                acriculture.landuse_building_ref = None
            else:
                landuse = DatabaseUtils.class_instance_by_code(ClLanduseType, int(landuse_type))
                acriculture.landuse_ref = landuse

            if crop_type == -1:
                acriculture.crop_type_ref = None
            else:
                crop = DatabaseUtils.class_instance_by_code(VaTypeCrop, int(crop_type))
                acriculture.crop_type_ref = crop

            acriculture.area_m2 = float(area)
            acriculture.yield_ga = float(yield_ga)
            acriculture.costs = float(cost)
            acriculture.profit = float(profit)
            acriculture.net_profit = float(net_profit)
            acriculture.register_no = register_no
            session.add(acriculture)

    def __agriculture_other_save(self):

        if self.a_other_twidget.rowCount() == 0:
            return

        register_no = self.register_no
        session = SessionHandler().session_instance()
        #loop save
        all_rows = self.a_other_twidget.rowCount()
        for row in xrange(0,all_rows):
            acr_count = session.query(VaInfoAgricultureOther).filter(VaInfoAgricultureOther.register_no == self.register_no).count()
            if acr_count > 0:
                acriculture = session.query(VaInfoAgricultureOther).filter(VaInfoAgricultureOther.register_no == self.register_no).one()
            else:
                acriculture = VaInfoAgricultureOther()

            irrigation_item = self.a_other_twidget.item(row, 0)
            irrigation_type = irrigation_item.data(Qt.UserRole)

            price_item = self.a_other_twidget.item(row, 1)
            price = price_item.data(Qt.UserRole)

            comment_item = self.a_other_twidget.item(row, 2)
            comment = comment_item.data(Qt.UserRole)


            if irrigation_type == -1:
                acriculture.irrigation_ref = None
            else:
                irrigation = DatabaseUtils.class_instance_by_code(VaTypeIrrigation, int(irrigation_type))
                acriculture.irrigation_ref = irrigation

            acriculture.other_price = float(price)
            acriculture.other = comment
            acriculture.register_no = self.register_no
            session.add(acriculture)

    #home purchase
    @pyqtSlot()
    def on_purchase_add_button_clicked(self):

        self.__home_purchase_add()

    #commercial purchase
    @pyqtSlot()
    def on_c_purchase_add_button_clicked(self):

        self.__commercial_purchase_add()

    #industrial purchase
    @pyqtSlot()
    def on_i_purchase_add_button_clicked(self):

        self.__industrial_purchase_add()

    #agricalture purchase
    @pyqtSlot()
    def on_a_purchase_add_button_clicked(self):

        self.__agricalture_purchase_add()

    #home lease
    @pyqtSlot()
    def on_lease_add_button_clicked(self):

        self.__home_lease_add()

    #commercial lease
    @pyqtSlot()
    def on_c_lease_add_button_clicked(self):

        self.__commercial_lease_add()

    #industrial lease
    @pyqtSlot()
    def on_i_lease_add_button_clicked(self):

        self.__industrial_lease_add()

    #agricalture lease
    @pyqtSlot()
    def on_a_lease_add_button_clicked(self):

        self.__agricalture_lease_add()

    #home building
    @pyqtSlot()
    def on_building_add_button_clicked(self):

        self.__home_building_add()

    #commercial building
    @pyqtSlot()
    def on_c_buidling_add_button_clicked(self):

        self.__commercial_building_add()

    #industrial building
    @pyqtSlot()
    def on_i_buidling_add_button_clicked(self):

        self.__industrial_building_add()

    #industrial product
    @pyqtSlot()
    def on_i_product_add_button_clicked(self):

        self.__industrial_product_add()

    #agriculture building
    @pyqtSlot()
    def on_a_building_add_button_clicked(self):

        self.__agriculture_building_add()

    @pyqtSlot()
    def on_a_add_button_clicked(self):

        self.__agriculture_add()

    @pyqtSlot()
    def on_a_other_add_button_clicked(self):

        self.__agriculture_other_add()

    @pyqtSlot()
    def on_purchase_delete_button_clicked(self):

        selected_row = self.purchase_twidget.currentRow()
        self.purchase_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_c_purchase_delete_button_clicked(self):

        selected_row = self.c_purchase_twidget.currentRow()
        self.c_purchase_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_i_purchase_delete_button_clicked(self):

        selected_row = self.i_purchase_twidget.currentRow()
        self.i_purchase_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_a_purchase_delete_button_clicked(self):

        selected_row = self.a_purchase_twidget.currentRow()
        self.a_purchase_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_lease_delete_button_clicked(self):

        selected_row = self.lease_twidget.currentRow()
        self.lease_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_c_lease_delete_button_clicked(self):

        selected_row = self.c_lease_twidget.currentRow()
        self.c_lease_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_i_lease_delete_button_clicked(self):

        selected_row = self.i_lease_twidget.currentRow()
        self.i_lease_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_a_lease_delete_button_clicked(self):

        selected_row = self.a_lease_twidget.currentRow()
        self.a_lease_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_building_delete_button_clicked(self):

        selected_row = self.home_building_twidget.currentRow()
        self.home_building_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_c_building_delete_button_clicked(self):

        selected_row = self.c_building_twidget.currentRow()
        self.c_building_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_i_building_delete_button_clicked(self):

        selected_row = self.i_building_twidget.currentRow()
        self.i_building_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_a_building_delete_button_clicked(self):

        selected_row = self.a_building_twidget.currentRow()
        self.a_building_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_i_product_delete_button_clicked(self):

        selected_row = self.i_product_twidget.currentRow()
        self.i_product_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_a_delete_button_clicked(self):

        selected_row = self.agriculture_twidget.currentRow()
        self.agriculture_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_a_other_delete_button_clicked(self):

        selected_row = self.a_other_twidget.currentRow()
        self.a_other_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_purchase_update_button_clicked(self):

        selected_row = self.purchase_twidget.currentRow()

        use_item = self.purchase_twidget.item(selected_row, 0)
        date_item = self.purchase_twidget.item(selected_row, 1)
        area_item = self.purchase_twidget.item(selected_row, 2)
        price_item = self.purchase_twidget.item(selected_row, 3)
        price_m2_item = self.purchase_twidget.item(selected_row, 4)

        landuse_code = self.purchase_use_type_cbox.itemData(self.purchase_use_type_cbox.currentIndex())
        landuse_text = self.purchase_use_type_cbox.currentText()
        if use_item == None:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return
        use_item.setText(landuse_text)
        use_item.setData(Qt.UserRole, landuse_code)
        date_item.setText(self.purchase_dateEdit.text())
        date_item.setData(Qt.UserRole,self.purchase_dateEdit.text())
        area_item.setText(self.purchase_area_edit.text())
        area_item.setData(Qt.UserRole, self.purchase_area_edit.text())
        price_item.setText(self.purchase_price_edit.text())
        price_item.setData(Qt.UserRole, self.purchase_price_edit.text())
        price_m2_item.setText(self.purchase_price_if_m2.text())
        price_m2_item.setData(Qt.UserRole, self.purchase_price_if_m2.text())

    @pyqtSlot()
    def on_c_purchase_update_button_clicked(self):

        selected_row = self.c_purchase_twidget.currentRow()

        use_item = self.c_purchase_twidget.item(selected_row, 0)
        date_item = self.c_purchase_twidget.item(selected_row, 1)
        area_item = self.c_purchase_twidget.item(selected_row, 2)
        price_item = self.c_purchase_twidget.item(selected_row, 3)
        price_m2_item = self.c_purchase_twidget.item(selected_row, 4)

        landuse_code = self.c_purchase_use_type_cbox.itemData(self.c_purchase_use_type_cbox.currentIndex())
        landuse_text = self.c_purchase_use_type_cbox.currentText()
        if use_item == None:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return
        use_item.setText(landuse_text)
        use_item.setData(Qt.UserRole, landuse_code)
        date_item.setText(self.c_purchase_dateEdit.text())
        date_item.setData(Qt.UserRole,self.c_purchase_dateEdit.text())
        area_item.setText(self.c_purchase_area_edit.text())
        area_item.setData(Qt.UserRole, self.c_purchase_area_edit.text())
        price_item.setText(self.c_purchase_price_edit.text())
        price_item.setData(Qt.UserRole, self.c_purchase_price_edit.text())
        price_m2_item.setText(self.c_purchase_price_if_m2.text())
        price_m2_item.setData(Qt.UserRole, self.c_purchase_price_if_m2.text())

    @pyqtSlot()
    def on_i_purchase_update_button_clicked(self):

        selected_row = self.i_purchase_twidget.currentRow()

        use_item = self.i_purchase_twidget.item(selected_row, 0)
        date_item = self.i_purchase_twidget.item(selected_row, 1)
        area_item = self.i_purchase_twidget.item(selected_row, 2)
        price_item = self.i_purchase_twidget.item(selected_row, 3)
        price_m2_item = self.i_purchase_twidget.item(selected_row, 4)

        landuse_code = self.i_purchase_use_type_cbox.itemData(self.i_purchase_use_type_cbox.currentIndex())
        landuse_text = self.i_purchase_use_type_cbox.currentText()
        if use_item == None:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return
        use_item.setText(landuse_text)
        use_item.setData(Qt.UserRole, landuse_code)
        date_item.setText(self.i_purchase_date_edit.text())
        date_item.setData(Qt.UserRole,self.i_purchase_date_edit.dateTime())
        area_item.setText(self.i_purchase_area_edit.text())
        area_item.setData(Qt.UserRole, self.i_purchase_area_edit.text())
        price_item.setText(self.i_purchase_price_edit.text())
        price_item.setData(Qt.UserRole, self.i_purchase_price_edit.text())
        price_m2_item.setText(self.i_purchase_price_if_m2.text())
        price_m2_item.setData(Qt.UserRole, self.i_purchase_price_if_m2.text())

    @pyqtSlot()
    def on_a_purchase_update_button_clicked(self):

        selected_row = self.a_purchase_twidget.currentRow()

        area_item = self.a_purchase_twidget.item(selected_row, 0)
        date_item = self.a_purchase_twidget.item(selected_row, 1)
        price_item = self.a_purchase_twidget.item(selected_row, 2)
        price_m2_item = self.a_purchase_twidget.item(selected_row, 3)

        date_item.setText(self.a_purchase_dateEdit.text())
        date_item.setData(Qt.UserRole,self.a_purchase_dateEdit.text())
        area_item.setText(self.a_purchase_area_edit.text())
        area_item.setData(Qt.UserRole, self.a_purchase_area_edit.text())
        price_item.setText(self.a_price_edit.text())
        price_item.setData(Qt.UserRole, self.a_price_edit.text())
        price_m2_item.setText(self.a_purchase_price_if_m2.text())
        price_m2_item.setData(Qt.UserRole, self.a_purchase_price_if_m2.text())

    @pyqtSlot()
    def on_lease_update_button_clicked(self):

        selected_row = self.lease_twidget.currentRow()
        usetype_item = self.lease_twidget.item(selected_row, 0)
        date_item = self.lease_twidget.item(selected_row, 1)
        duration_item = self.lease_twidget.item(selected_row, 2)
        area_item = self.lease_twidget.item(selected_row, 3)
        rent_item = self.lease_twidget.item(selected_row, 4)
        rent_m2_item = self.lease_twidget.item(selected_row, 5)

        landuse_code = self.lease_use_type_cbox.itemData(self.lease_use_type_cbox.currentIndex())
        landuse_text = self.lease_use_type_cbox.currentText()
        if usetype_item == None:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return
        if self.lease_duration_edit.text() == "" or self.lease_duration_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Duration Month"))
            return
        if self.lease_rent_edit.text() == "" or self.lease_rent_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Rent"))
            return

        usetype_item.setText(landuse_text)
        usetype_item.setData(Qt.UserRole, landuse_code)
        date_item.setText(self.lease_dateEdit.text())
        date_item.setData(Qt.UserRole, self.lease_dateEdit.text())
        duration_item.setText(self.lease_duration_edit.text())
        duration_item.setData(Qt.UserRole, self.lease_duration_edit.text())
        area_item.setText(self.lease_area_edit.text())
        area_item.setData(Qt.UserRole, self.lease_area_edit.text())
        rent_item.setText(self.lease_rent_edit.text())
        rent_item.setData(Qt.UserRole, self.lease_rent_edit.text())
        rent_m2_item.setText(self.lease_rent_of_m2.text())
        rent_m2_item.setData(Qt.UserRole, self.lease_rent_of_m2.text())

    @pyqtSlot()
    def on_c_lease_update_button_clicked(self):

        selected_row = self.c_lease_twidget.currentRow()
        usetype_item = self.c_lease_twidget.item(selected_row, 0)
        date_item = self.c_lease_twidget.item(selected_row, 1)
        duration_item = self.c_lease_twidget.item(selected_row, 2)
        area_item = self.c_lease_twidget.item(selected_row, 3)
        rent_item = self.c_lease_twidget.item(selected_row, 4)
        rent_m2_item = self.c_lease_twidget.item(selected_row, 5)

        landuse_code = self.c_lease_use_type_cbox.itemData(self.c_lease_use_type_cbox.currentIndex())
        landuse_text = self.c_lease_use_type_cbox.currentText()
        if usetype_item == None:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return
        if self.c_lease_duration_edit.text() == "" or self.c_lease_duration_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Duration Month"))
            return
        if self.c_lease_expenses_edit.text() == "" or self.c_lease_expenses_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Rent"))
            return

        usetype_item.setText(landuse_text)
        usetype_item.setData(Qt.UserRole, landuse_code)
        date_item.setText(self.c_lease_dateEdit.text())
        date_item.setData(Qt.UserRole, self.c_lease_dateEdit.text())
        duration_item.setText(self.c_lease_duration_edit.text())
        duration_item.setData(Qt.UserRole, self.c_lease_duration_edit.text())
        area_item.setText(self.c_lease_area_edit.text())
        area_item.setData(Qt.UserRole, self.c_lease_area_edit.text())
        rent_item.setText(self.c_lease_expenses_edit.text())
        rent_item.setData(Qt.UserRole, self.c_lease_expenses_edit.text())
        rent_m2_item.setText(self.c_lease_rent_of_m2.text())
        rent_m2_item.setData(Qt.UserRole, self.c_lease_rent_of_m2.text())

    @pyqtSlot()
    def on_i_lease_update_button_clicked(self):

        selected_row = self.i_lease_twidget.currentRow()
        usetype_item = self.i_lease_twidget.item(selected_row, 0)
        date_item = self.i_lease_twidget.item(selected_row, 1)
        duration_item = self.i_lease_twidget.item(selected_row, 2)
        area_item = self.i_lease_twidget.item(selected_row, 3)
        rent_item = self.i_lease_twidget.item(selected_row, 4)
        rent_m2_item = self.i_lease_twidget.item(selected_row, 5)

        landuse_code = self.i_lease_use_type_cbox.itemData(self.i_lease_use_type_cbox.currentIndex())
        landuse_text = self.i_lease_use_type_cbox.currentText()
        if usetype_item == None:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return
        if self.i_lease_duration_edit.text() == "" or self.i_lease_duration_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Duration Month"))
            return
        if self.i_lease_month_edit.text() == "" or self.i_lease_month_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Rent"))
            return

        usetype_item.setText(landuse_text)
        usetype_item.setData(Qt.UserRole, landuse_code)
        date_item.setText(self.i_lease_dateEdit.text())
        date_item.setData(Qt.UserRole, self.i_lease_dateEdit.dateTime())
        duration_item.setText(self.i_lease_duration_edit.text())
        duration_item.setData(Qt.UserRole, self.i_lease_duration_edit.text())
        area_item.setText(self.i_lease_area_edit.text())
        area_item.setData(Qt.UserRole, self.i_lease_area_edit.text())
        rent_item.setText(self.i_lease_month_edit.text())
        rent_item.setData(Qt.UserRole, self.i_lease_month_edit.text())
        rent_m2_item.setText(self.i_lease_rent_of_m2.text())
        rent_m2_item.setData(Qt.UserRole, self.i_lease_rent_of_m2.text())

    @pyqtSlot()
    def on_a_lease_update_button_clicked(self):

        selected_row = self.a_lease_twidget.currentRow()
        date_item = self.a_lease_twidget.item(selected_row, 0)
        duration_item = self.a_lease_twidget.item(selected_row, 1)
        area_item = self.a_lease_twidget.item(selected_row, 2)
        rent_item = self.a_lease_twidget.item(selected_row, 3)
        rent_m2_item = self.a_lease_twidget.item(selected_row, 4)

        if self.a_lease_duration_edit.text() == "" or self.a_lease_duration_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Duration Month"))
            return
        if self.a_lease_rent_edit.text() == "" or self.a_lease_rent_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Error"), self.tr("No Rent"))
            return

        date_item.setText(self.a_lease_dateEdit.text())
        date_item.setData(Qt.UserRole, self.a_lease_dateEdit.text())
        duration_item.setText(self.a_lease_duration_edit.text())
        duration_item.setData(Qt.UserRole, self.a_lease_duration_edit.text())
        area_item.setText(self.a_lease_area_edit.text())
        area_item.setData(Qt.UserRole, self.a_lease_area_edit.text())
        rent_item.setText(self.a_lease_rent_edit.text())
        rent_item.setData(Qt.UserRole, self.a_lease_rent_edit.text())
        rent_m2_item.setText(self.a_lease_rent_of_m2.text())
        rent_m2_item.setData(Qt.UserRole, self.a_lease_rent_of_m2.text())

    @pyqtSlot()
    def on_building_update_button_clicked(self):

        session = SessionHandler().session_instance()

        selected_row = self.home_building_twidget.currentRow()

        building_item = self.home_building_twidget.item(selected_row, 0)
        landuse_item = self.home_building_twidget.item(selected_row, 1)
        area_item = self.home_building_twidget.item(selected_row, 2)
        design_item = self.home_building_twidget.item(selected_row, 3)
        material_item = self.home_building_twidget.item(selected_row, 4)
        construction_item = self.home_building_twidget.item(selected_row, 5)
        floor_item = self.home_building_twidget.item(selected_row, 6)
        room_item = self.home_building_twidget.item(selected_row, 7)
        stove_item = self.home_building_twidget.item(selected_row, 8)
        heat_item = self.home_building_twidget.item(selected_row, 9)
        status_item = self.home_building_twidget.item(selected_row, 10)
        status_year_item = self.home_building_twidget.item(selected_row, 11)

        landuse_code = self.building_use_type_cbox.itemData(self.building_use_type_cbox.currentIndex())
        landuse_text = self.building_use_type_cbox.currentText()

        building_code = self.building_no_cbox.itemData(self.building_no_cbox.currentIndex())
        buidling_text = self.building_no_cbox.currentText()

        stove_code = self.building_stove_type_cbox.itemData(self.building_stove_type_cbox.currentIndex())
        stove_text = self.building_stove_type_cbox.currentText()

        design_code = self.building_design_cbox.itemData(self.building_design_cbox.currentIndex())
        design_text = self.building_design_cbox.currentText()

        material_code = self.building_material_cbox.itemData(self.building_material_cbox.currentIndex())
        material_text = self.building_material_cbox.currentText()

        heat_code = self.building_heat_Insulation_cbox.itemData(self.building_heat_Insulation_cbox.currentIndex())
        heat_text = self.building_heat_Insulation_cbox.currentText()

        if self.b_status_good_rbutton.isChecked():
            status_code = 10
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 10).one()
            status_text = status.description
        elif self.b_status_medium_rbutton.isChecked():
            status_code = 20
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 20).one()
            status_text = status.description
        elif self.b_status_bad_rbutton.isChecked():
            status_code = 30
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 30).one()
            status_text = status.description

        if landuse_item == None:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return

        landuse_item.setText(landuse_text)
        landuse_item.setData(Qt.UserRole, landuse_code)
        building_item.setText(buidling_text)
        building_item.setData(Qt.UserRole, building_code)
        stove_item.setText(stove_text)
        stove_item.setData(Qt.UserRole, stove_code)
        design_item.setText(design_text)
        design_item.setData(Qt.UserRole, design_code)
        material_item.setText(material_text)
        material_item.setData(Qt.UserRole, material_code)
        heat_item.setText(heat_text)
        heat_item.setData(Qt.UserRole, heat_code)
        status_item.setText(status_text)
        status_item.setData(Qt.UserRole, status_code)
        area_item.setText(self.building_area_edit.text())
        area_item.setData(Qt.UserRole, self.building_area_edit.text())
        construction_item.setText(self.building_construction_year_edit.text())
        construction_item.setData(Qt.UserRole, self.building_construction_year_edit.text())
        floor_item.setText(str(self.no_floor_sbox.value()))
        floor_item.setData(Qt.UserRole, self.no_floor_sbox.value())
        room_item.setText(str(self.no_room_sbox.value()))
        room_item.setData(Qt.UserRole, self.no_room_sbox.value())
        status_year_item.setText(self.building_status_year_date.text())
        status_year_item.setData(Qt.UserRole, self.building_status_year_date.text())

    @pyqtSlot()
    def on_c_buidling_update_button_clicked(self):

        session = SessionHandler().session_instance()

        selected_row = self.c_building_twidget.currentRow()

        building_item = self.c_building_twidget.item(selected_row, 0)
        landuse_item = self.c_building_twidget.item(selected_row, 1)
        area_item = self.c_building_twidget.item(selected_row, 2)
        design_item = self.c_building_twidget.item(selected_row, 3)
        material_item = self.c_building_twidget.item(selected_row, 4)
        floor_item = self.c_building_twidget.item(selected_row, 5)
        room_item = self.c_building_twidget.item(selected_row, 6)
        construction_item = self.c_building_twidget.item(selected_row, 7)
        esystem_item = self.c_building_twidget.item(selected_row, 8)
        status_item = self.c_building_twidget.item(selected_row, 9)

        landuse_code = self.c_building_use_type_cbox.itemData(self.c_building_use_type_cbox.currentIndex())
        landuse_text = self.c_building_use_type_cbox.currentText()

        building_code = self.c_building_no_cbox.itemData(self.c_building_no_cbox.currentIndex())
        buidling_text = self.c_building_no_cbox.currentText()

        esystem_code = self.c_building_esystem_cbox.itemData(self.c_building_esystem_cbox.currentIndex())
        esystem_text = self.c_building_esystem_cbox.currentText()

        design_code = self.c_building_design_cbox.itemData(self.c_building_design_cbox.currentIndex())
        design_text = self.c_building_design_cbox.currentText()

        material_code = self.c_building_material_cbox.itemData(self.c_building_material_cbox.currentIndex())
        material_text = self.c_building_material_cbox.currentText()

        if self.c_b_status_good_rbutton.isChecked():
            status_code = 10
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 10).one()
            status_text = status.description
        elif self.c_b_status_medium_rbutton.isChecked():
            status_code = 20
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 20).one()
            status_text = status.description
        elif self.c_b_status_bad_rbutton.isChecked():
            status_code = 30
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 30).one()
            status_text = status.description

        if landuse_item == None:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return

        landuse_item.setText(landuse_text)
        landuse_item.setData(Qt.UserRole, landuse_code)
        building_item.setText(buidling_text)
        building_item.setData(Qt.UserRole, building_code)
        esystem_item.setText(esystem_text)
        esystem_item.setData(Qt.UserRole, esystem_code)
        design_item.setText(design_text)
        design_item.setData(Qt.UserRole, design_code)
        material_item.setText(material_text)
        material_item.setData(Qt.UserRole, material_code)
        status_item.setText(status_text)
        status_item.setData(Qt.UserRole, status_code)
        area_item.setText(self.c_building_area_edit.text())
        area_item.setData(Qt.UserRole, self.c_building_area_edit.text())
        construction_item.setText(str(self.c_building_year_construction_date.value()))
        construction_item.setData(Qt.UserRole, self.c_building_year_construction_date.value())
        floor_item.setText(str(self.c_no_floor_sbox.value()))
        floor_item.setData(Qt.UserRole, self.c_no_floor_sbox.value())
        room_item.setText(str(self.c_no_room_sbox.value()))
        room_item.setData(Qt.UserRole, self.c_no_room_sbox.value())

    @pyqtSlot()
    def on_i_building_update_button_clicked(self):

        session = SessionHandler().session_instance()

        selected_row = self.i_building_twidget.currentRow()

        building_item = self.i_building_twidget.item(selected_row, 0)
        landuse_item = self.i_building_twidget.item(selected_row, 1)
        area_item = self.i_building_twidget.item(selected_row, 2)
        material_item = self.i_building_twidget.item(selected_row, 3)
        construction_item = self.i_building_twidget.item(selected_row, 4)
        floor_item = self.i_building_twidget.item(selected_row, 5)
        status_item = self.i_building_twidget.item(selected_row, 6)

        landuse_code = self.i_building_use_type_cbox.itemData(self.i_building_use_type_cbox.currentIndex())
        landuse_text = self.i_building_use_type_cbox.currentText()

        building_code = self.i_building_no_cbox.itemData(self.i_building_no_cbox.currentIndex())
        buidling_text = self.i_building_no_cbox.currentText()

        material_code = self.i_building_material_cbox.itemData(self.i_building_material_cbox.currentIndex())
        material_text = self.i_building_material_cbox.currentText()

        if self.i_building_good_rbutton.isChecked():
            status_code = 10
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 10).one()
            status_text = status.description
        elif self.i_building_medium_rbutton.isChecked():
            status_code = 20
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 20).one()
            status_text = status.description
        elif self.i_building_bad_rbutton.isChecked():
            status_code = 30
            status = session.query(VaTypeStatusBuilding).filter(VaTypeStatusBuilding.code == 30).one()
            status_text = status.description

        if landuse_item == None:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return

        landuse_item.setText(landuse_text)
        landuse_item.setData(Qt.UserRole, landuse_code)
        building_item.setText(buidling_text)
        building_item.setData(Qt.UserRole, building_code)
        material_item.setText(material_text)
        material_item.setData(Qt.UserRole, material_code)
        status_item.setText(status_text)
        status_item.setData(Qt.UserRole, status_code)
        area_item.setText(self.i_building_area_edit.text())
        area_item.setData(Qt.UserRole, self.i_building_area_edit.text())
        construction_item.setText(str(self.i_building_year_construction_date.value()))
        construction_item.setData(Qt.UserRole, self.i_building_year_construction_date.value())
        floor_item.setText(str(self.i_building_no_floor_sbox.value()))
        floor_item.setData(Qt.UserRole, self.i_building_no_floor_sbox.value())

    @pyqtSlot()
    def on_i_product_update_button_clicked(self):

        session = SessionHandler().session_instance()

        selected_row = self.i_product_twidget.currentRow()

        product_item = self.i_product_twidget.item(selected_row, 0)
        come_per_item = self.i_product_twidget.item(selected_row, 1)
        cost_per_item = self.i_product_twidget.item(selected_row, 2)
        count_item = self.i_product_twidget.item(selected_row, 3)
        time_item = self.i_product_twidget.item(selected_row, 4)
        process_item = self.i_product_twidget.item(selected_row, 5)

        product_code = self.i_product_type_cbox.itemData(self.i_product_type_cbox.currentIndex())
        product_text = self.i_product_type_cbox.currentText()

        if self.i_status_bad_rbutton.isChecked():
            status_code = 10
            status = session.query(VaTypeIndustrialProcess).filter(VaTypeIndustrialProcess.code == 10).one()
            status_text = status.description
        elif self.i_status_medium_rbutton.isChecked():
            status_code = 20
            status = session.query(VaTypeIndustrialProcess).filter(VaTypeIndustrialProcess.code == 20).one()
            status_text = status.description
        elif self.i_status_good_rbutton.isChecked():
            status_code = 30
            status = session.query(VaTypeIndustrialProcess).filter(VaTypeIndustrialProcess.code == 30).one()
            status_text = status.description

        if self.i_day_rbutton.isChecked():
            time_code = 10
            time = session.query(VaTypeProductTime).filter(VaTypeProductTime.code == 10).one()
            time_text = time.description
        elif self.i_month_rbutton.isChecked():
            time_code = 20
            time = session.query(VaTypeProductTime).filter(VaTypeProductTime.code == 20).one()
            time_text = time.description
        elif self.i_year_rbutton.isChecked():
            time_code = 30
            time = session.query(VaTypeProductTime).filter(VaTypeProductTime.code == 30).one()
            time_text = time.description

        if product_item == None:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return

        product_item.setText(product_text)
        product_item.setData(Qt.UserRole, product_code)
        come_per_item.setText(self.i_income_item_edit.text())
        come_per_item.setData(Qt.UserRole, self.i_income_item_edit.text())
        cost_per_item.setText(self.i_cost_item_edit.text())
        cost_per_item.setData(Qt.UserRole, self.i_cost_item_edit.text())
        count_item.setText(str(self.i_product_no_sbox.value()))
        count_item.setData(Qt.UserRole, self.i_product_no_sbox.value())
        time_item.setText(time_text)
        time_item.setData(Qt.UserRole, time_code)
        process_item.setText(status_text)
        process_item.setData(Qt.UserRole, status_code)

    @pyqtSlot()
    def on_a_building_update_button_clicked(self):

        session = SessionHandler().session_instance()

        selected_row = self.a_building_twidget.currentRow()

        building_item = self.a_building_twidget.item(selected_row, 0)
        landuse_item = self.a_building_twidget.item(selected_row, 1)
        area_item = self.a_building_twidget.item(selected_row, 2)
        material_item = self.a_building_twidget.item(selected_row, 3)
        construction_item = self.a_building_twidget.item(selected_row, 4)
        price_item = self.a_building_twidget.item(selected_row, 5)

        landuse_code = self.a_building_use_type_cbox.itemData(self.a_building_use_type_cbox.currentIndex())
        landuse_text = self.a_building_use_type_cbox.currentText()

        building_code = self.a_building_no_cbox.itemData(self.a_building_no_cbox.currentIndex())
        buidling_text = self.a_building_no_cbox.currentText()

        material_code = self.a_building_material_cbox.itemData(self.a_building_material_cbox.currentIndex())
        material_text = self.a_building_material_cbox.currentText()

        if landuse_item == None:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return

        landuse_item.setText(landuse_text)
        landuse_item.setData(Qt.UserRole, landuse_code)
        building_item.setText(buidling_text)
        building_item.setData(Qt.UserRole, building_code)
        material_item.setText(material_text)
        material_item.setData(Qt.UserRole, material_code)
        area_item.setText(self.a_building_area_edit.text())
        area_item.setData(Qt.UserRole, self.a_building_area_edit.text())
        construction_item.setText(str(self.a_building_year_construction_date.value()))
        construction_item.setData(Qt.UserRole, self.a_building_year_construction_date.value())
        price_item.setText(self.a_building_price_edit.text())
        price_item.setData(Qt.UserRole, self.a_building_price_edit.text())

    @pyqtSlot()
    def on_a_update_button_clicked(self):

        session = SessionHandler().session_instance()

        selected_row = self.agriculture_twidget.currentRow()

        landuse_item = self.agriculture_twidget.item(selected_row, 0)
        crop_item = self.agriculture_twidget.item(selected_row, 1)
        area_item = self.agriculture_twidget.item(selected_row, 2)
        yield_item = self.agriculture_twidget.item(selected_row, 3)
        cost_item = self.agriculture_twidget.item(selected_row, 4)
        profit_item = self.agriculture_twidget.item(selected_row, 5)
        net_profit_item = self.agriculture_twidget.item(selected_row, 6)

        landuse_code = self.a_use_type_cbox.itemData(self.a_use_type_cbox.currentIndex())
        landuse_text = self.a_use_type_cbox.currentText()

        crop_code = self.a_crop_type_cbox.itemData(self.a_crop_type_cbox.currentIndex())
        crop_text = self.a_crop_type_cbox.currentText()

        if landuse_item == None:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return

        landuse_item.setText(landuse_text)
        landuse_item.setData(Qt.UserRole, landuse_code)
        crop_item.setText(crop_text)
        crop_item.setData(Qt.UserRole, crop_code)
        area_item.setText(self.a_area_edit.text())
        area_item.setData(Qt.UserRole, self.a_area_edit.text())
        yield_item.setText(self.a_yield_edit.text())
        yield_item.setData(Qt.UserRole, self.a_yield_edit.text())
        cost_item.setText(self.a_costs_edit.text())
        cost_item.setData(Qt.UserRole, self.a_costs_edit.text())
        profit_item.setText(self.a_profit_edit.text())
        profit_item.setData(Qt.UserRole, self.a_profit_edit.text())
        net_profit_item.setText(self.a_net_profit_edit.text())
        net_profit_item.setData(Qt.UserRole, self.a_net_profit_edit.text())

    @pyqtSlot()
    def on_a_other_update_button_clicked(self):

        session = SessionHandler().session_instance()

        selected_row = self.a_other_twidget.currentRow()

        irrigation_item = self.a_other_twidget.item(selected_row, 0)
        other_price_item = self.a_other_twidget.item(selected_row, 1)
        other_item = self.a_other_twidget.item(selected_row, 2)

        irrigation_code = self.a_irrigation_type_cbox.itemData(self.a_irrigation_type_cbox.currentIndex())
        irrigation_text = self.a_irrigation_type_cbox.currentText()

        if irrigation_item == None:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return

        irrigation_item.setText(irrigation_text)
        irrigation_item.setData(Qt.UserRole, irrigation_code)
        other_price_item.setText(self.a_other_price_edit.text())
        other_price_item.setData(Qt.UserRole, self.a_other_price_edit.text())
        other_item.setText(self.a_other_comment_edit.toPlainText())
        other_item.setData(Qt.UserRole, self.a_other_comment_edit.toPlainText())


    @pyqtSlot()
    def on_ok_button_clicked(self):

        session = SessionHandler().session_instance()
        msgBox = QMessageBox()
        msgBox.setText(self.tr("Do you want to finish?"))
        okButton = msgBox.addButton(self.tr("Yes"), QMessageBox.ActionRole)
        msgBox.addButton(self.tr("No"), QMessageBox.ActionRole)
        msgBox.setWindowFlags(Qt.WindowStaysOnTopHint)
        msgBox.exec_()
        if msgBox.clickedButton() == okButton:
            if self.parcel_type == 10:
                self.__home_general_save()
                if self.home_purchase_rbutton.isChecked():
                    self.__home_purchase_save()
                    self.__purchase_delete()
                elif self.home_lease_rbutton.isChecked():
                    self.__home_lease_save()
                    self.__lease_delete()
                self.__home_building_save()
                # self.__building_delete()
            elif self.parcel_type == 20:
                self.__commercial_general_save()
                if self.c_purchase_rbutton.isChecked():
                    self.__commercial_purchase_save()
                    self.__commercial_purchase_delete()
                elif self.c_lease_rbutton.isChecked():
                    self.__commercial_lease_save()
                    self.__commercial_lease_delete()
                self.__commercial_building_save()
                # self.__commercial_building_delete()
            elif self.parcel_type == 30:
                self.__industrial_general_save()
                if self.i_purchase_rbutton.isChecked():
                    self.__industrial_purchase_save()
                    self.__industrial_purchase_delete()
                elif self.i_lease_rbutton.isChecked():
                    self.__industrial_lease_save()
                    self.__industrial_lease_delete()
                self.__industrial_building_save()
                # self.__industrual_building_delete()
                self.__industrial_product_save()
                self.__industrual_product_delete()
            elif self.parcel_type == 40:
                self.__agriculture_general_save()
                if self.a_purchase_rbutton.isChecked():
                    self.__agriculture_purchase_save()
                    self.__agriculture_purchase_delete()
                elif self.a_lease_rbutton.isChecked():
                    self.__agriculture_lease_save()
                    self.__agriculture_lease_delete()
                self.__agriculture_building_save()
                # self.__industrual_building_delete()
                self.__agriculture_save()
                self.__agriculture_other_save()

            session.commit()
            self.accept()
            PluginUtils.show_message(self,self.tr("Successfully"),self.tr("Successfully inserted"))

    @pyqtSlot(QTableWidgetItem)
    def on_home_building_twidget_itemClicked(self, item):

        current_row = self.home_building_twidget.currentRow()

        building_item = self.home_building_twidget.item(current_row, 0)
        building_id = building_item.data(Qt.UserRole)

        use_item = self.home_building_twidget.item(current_row, 1)
        use_id = use_item.data(Qt.UserRole)

        area_item = self.home_building_twidget.item(current_row, 2)
        area = area_item.data(Qt.UserRole)

        design_item = self.home_building_twidget.item(current_row, 3)
        design_id = design_item.data(Qt.UserRole)

        material_item = self.home_building_twidget.item(current_row, 4)
        material_id = material_item.data(Qt.UserRole)

        const_item = self.home_building_twidget.item(current_row, 5)
        const_year = const_item.data(Qt.UserRole)

        floor_item = self.home_building_twidget.item(current_row, 6)
        floor = floor_item.data(Qt.UserRole)

        room_item = self.home_building_twidget.item(current_row, 7)
        room = room_item.data(Qt.UserRole)

        stove_item = self.home_building_twidget.item(current_row, 8)
        stove_id = stove_item.data(Qt.UserRole)

        heat_item = self.home_building_twidget.item(current_row, 9)
        heat_id = heat_item.data(Qt.UserRole)

        status_item = self.home_building_twidget.item(current_row, 10)
        status_id = status_item.data(Qt.UserRole)

        status_year_item = self.home_building_twidget.item(current_row, 11)
        status_year = status_year_item.data(Qt.UserRole)

        session = SessionHandler().session_instance()

        building_count = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.building_id == building_id).\
                                                 filter(VaInfoHomeBuilding.register_no == self.register_no).count()

        if building_count == 1:
            building = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.building_id == building_id).\
                                                            filter(VaInfoHomeBuilding.register_no == self.register_no).one()
            if building.building_id:
                self.building_no_cbox.setCurrentIndex(self.building_no_cbox.findData(building.building_id))

            if building.landuse_building_ref:
                self.building_use_type_cbox.setCurrentIndex(self.building_use_type_cbox.findData(building.landuse_building_ref.code))

            self.building_area_edit.setText(str(area))

            if building.material_type_ref:
                self.building_material_cbox.setCurrentIndex(self.building_material_cbox.findData(building.material_type_ref.code))
            if building.design_type_ref:
                self.building_design_cbox.setCurrentIndex(self.building_design_cbox.findData(building.design_type_ref.code))
            #self.building_construction_year_edit.setDateTime(building.construction_year)
            # self.building_construction_year_edit.setDateTime(QDateTime.fromTime_t(const_year))
            self.no_floor_sbox.setValue(floor)
            self.no_room_sbox.setValue(room)
            if building.stove_type_ref:
                self.building_stove_type_cbox.setCurrentIndex(self.building_stove_type_cbox.findData(building.stove_type_ref.code))
            if building.heat_type_ref:
                self.building_heat_Insulation_cbox.setCurrentIndex(self.building_heat_Insulation_cbox.findData(building.heat_type_ref.code))
            if building.building_status_ref:
                if building.building_status_ref.code == 10:
                    self.b_status_good_rbutton.setChecked(True)
                elif building.building_status_ref.code == 20:
                    self.b_status_medium_rbutton.setChecked(True)
                elif building.building_status_ref.code == 30:
                    self.b_status_bad_rbutton.setChecked(True)
            # self.building_status_year_date.setDate(QDateTime.fromString((str((building.status_year +"."+ 01 +"."+ 01))).strftime(Constants.PYTHON_DATE_FORMAT),
            #                                                             Constants.DATABASE_DATE_FORMAT))

    @pyqtSlot(QTableWidgetItem)
    def on_c_building_twidget_itemClicked(self, item):

        current_row = self.c_building_twidget.currentRow()

        building_item = self.c_building_twidget.item(current_row, 0)
        building_id = building_item.data(Qt.UserRole)

        use_item = self.c_building_twidget.item(current_row, 1)
        use_id = use_item.data(Qt.UserRole)

        area_item = self.c_building_twidget.item(current_row, 2)
        area = area_item.data(Qt.UserRole)

        design_item = self.c_building_twidget.item(current_row, 3)
        design_id = design_item.data(Qt.UserRole)

        material_item = self.c_building_twidget.item(current_row, 4)
        material_id = material_item.data(Qt.UserRole)

        floor_item = self.c_building_twidget.item(current_row, 5)
        floor = floor_item.data(Qt.UserRole)

        room_item = self.c_building_twidget.item(current_row, 6)
        room = room_item.data(Qt.UserRole)

        const_item = self.c_building_twidget.item(current_row, 7)
        const_year = const_item.data(Qt.UserRole)

        esystem_item = self.c_building_twidget.item(current_row, 8)
        esystem_id = esystem_item.data(Qt.UserRole)

        status_item = self.c_building_twidget.item(current_row, 9)
        status_id = status_item.data(Qt.UserRole)

        self.c_building_no_cbox.setCurrentIndex(self.c_building_no_cbox.findData(building_id))
        self.c_building_use_type_cbox.setCurrentIndex(self.c_building_use_type_cbox.findData(use_id))
        self.c_building_area_edit.setText(str(area))
        self.c_building_material_cbox.setCurrentIndex(self.c_building_material_cbox.findData(material_id))
        self.c_building_design_cbox.setCurrentIndex(self.c_building_design_cbox.findData(design_id))
        self.c_building_esystem_cbox.setCurrentIndex(self.c_building_esystem_cbox.findData(esystem_id))
        self.c_building_year_construction_date.setValue(const_year)
        self.c_no_floor_sbox.setValue(floor)
        self.c_no_room_sbox.setValue(room)
        if status_id == 10:
            self.c_b_status_good_rbutton.setChecked(True)
        elif status_id == 20:
            self.c_b_status_medium_rbutton.setChecked(True)
        elif status_id == 30:
            self.c_b_status_bad_rbutton.setChecked(True)

    @pyqtSlot(QTableWidgetItem)
    def on_i_building_twidget_itemClicked(self, item):

        current_row = self.i_building_twidget.currentRow()

        building_item = self.i_building_twidget.item(current_row, 0)
        building_id = building_item.data(Qt.UserRole)

        use_item = self.i_building_twidget.item(current_row, 1)
        use_id = use_item.data(Qt.UserRole)

        area_item = self.i_building_twidget.item(current_row, 2)
        area = area_item.data(Qt.UserRole)

        material_item = self.i_building_twidget.item(current_row, 3)
        material_id = material_item.data(Qt.UserRole)

        const_item = self.i_building_twidget.item(current_row, 4)
        const_year = const_item.data(Qt.UserRole)

        floor_item = self.i_building_twidget.item(current_row, 5)
        floor = floor_item.data(Qt.UserRole)

        status_item = self.i_building_twidget.item(current_row, 6)
        status_id = status_item.data(Qt.UserRole)

        self.i_building_no_cbox.setCurrentIndex(self.i_building_no_cbox.findData(building_id))
        self.i_building_use_type_cbox.setCurrentIndex(self.i_building_use_type_cbox.findData(use_id))
        self.i_building_area_edit.setText(str(area))
        self.i_building_material_cbox.setCurrentIndex(self.i_building_material_cbox.findData(material_id))
        self.i_building_year_construction_date.setValue(const_year)
        self.i_building_no_floor_sbox.setValue(floor)
        if status_id == 10:
            self.i_building_good_rbutton.setChecked(True)
        elif status_id == 20:
            self.i_building_medium_rbutton.setChecked(True)
        elif status_id == 30:
            self.i_building_bad_rbutton.setChecked(True)

    @pyqtSlot(QTableWidgetItem)
    def on_i_product_twidget_itemClicked(self, item):

        current_row = self.i_product_twidget.currentRow()

        product_item = self.i_product_twidget.item(current_row, 0)
        product_id = product_item.data(Qt.UserRole)

        come_per_item = self.i_product_twidget.item(current_row, 1)
        come_per = come_per_item.data(Qt.UserRole)

        cost_per_item = self.i_product_twidget.item(current_row, 2)
        cost_per = cost_per_item.data(Qt.UserRole)

        count_item = self.i_product_twidget.item(current_row, 3)
        count = count_item.data(Qt.UserRole)

        time_item = self.i_product_twidget.item(current_row, 4)
        time_id = time_item.data(Qt.UserRole)

        process_item = self.i_product_twidget.item(current_row, 5)
        process = process_item.data(Qt.UserRole)

        self.i_product_type_cbox.setCurrentIndex(self.i_product_type_cbox.findData(product_id))
        self.i_income_item_edit.setText(str(come_per))
        self.i_cost_item_edit.setText(str(cost_per))
        self.i_product_no_sbox.setValue(count)
        if process == 10:
            self.i_status_bad_rbutton.setChecked(True)
        elif process == 20:
            self.i_status_medium_rbutton.setChecked(True)
        elif process == 30:
            self.i_status_good_rbutton.setChecked(True)
        if time_id == 10:
            self.i_day_rbutton.setChecked(True)
        elif time_id == 20:
            self.i_month_rbutton.setChecked(True)
        elif time_id == 30:
            self.i_year_rbutton.setChecked(True)

    @pyqtSlot(QTableWidgetItem)
    def on_a_building_twidget_itemClicked(self, item):

        current_row = self.a_building_twidget.currentRow()

        building_item = self.a_building_twidget.item(current_row, 0)
        building_id = building_item.data(Qt.UserRole)

        use_item = self.a_building_twidget.item(current_row, 1)
        use_id = use_item.data(Qt.UserRole)

        area_item = self.a_building_twidget.item(current_row, 2)
        area = area_item.data(Qt.UserRole)

        material_item = self.a_building_twidget.item(current_row, 3)
        material_id = material_item.data(Qt.UserRole)

        const_item = self.a_building_twidget.item(current_row, 4)
        const_year = const_item.data(Qt.UserRole)

        price_item = self.a_building_twidget.item(current_row, 5)
        price = price_item.data(Qt.UserRole)

        self.a_building_no_cbox.setCurrentIndex(self.a_building_no_cbox.findData(building_id))
        self.a_building_use_type_cbox.setCurrentIndex(self.a_building_use_type_cbox.findData(use_id))
        self.a_building_area_edit.setText(str(area))
        self.a_building_material_cbox.setCurrentIndex(self.a_building_material_cbox.findData(material_id))
        self.a_building_year_construction_date.setValue(const_year)
        self.a_building_price_edit.setText(str(price))

    @pyqtSlot(QTableWidgetItem)
    def on_a_other_twidget_itemClicked(self, item):

        current_row = self.a_other_twidget.currentRow()

        irrigation_item = self.a_other_twidget.item(current_row, 0)
        irrigation_id = irrigation_item.data(Qt.UserRole)

        other_price_item = self.a_other_twidget.item(current_row, 1)
        other_price = other_price_item.data(Qt.UserRole)

        other_item = self.a_other_twidget.item(current_row, 2)
        other = other_item.data(Qt.UserRole)

        self.a_irrigation_type_cbox.setCurrentIndex(self.a_irrigation_type_cbox.findData(irrigation_id))
        self.a_other_price_edit.setText(other_price)
        self.a_other_comment_edit.setText(other)

    @pyqtSlot(QTableWidgetItem)
    def on_agriculture_twidget_itemClicked(self, item):

        current_row = self.agriculture_twidget.currentRow()

        landuse_item = self.agriculture_twidget.item(current_row, 0)
        landuse_id = landuse_item.data(Qt.UserRole)

        crop_item = self.agriculture_twidget.item(current_row, 1)
        crop_id = crop_item.data(Qt.UserRole)

        area_item = self.agriculture_twidget.item(current_row, 2)
        area = area_item.data(Qt.UserRole)

        yield_item = self.agriculture_twidget.item(current_row, 3)
        yeild = yield_item.data(Qt.UserRole)

        cost_item = self.agriculture_twidget.item(current_row, 4)
        cost = cost_item.data(Qt.UserRole)

        profit_item = self.agriculture_twidget.item(current_row, 5)
        profit = profit_item.data(Qt.UserRole)

        net_profit_item = self.agriculture_twidget.item(current_row, 6)
        net_profit = net_profit_item.data(Qt.UserRole)

        self.a_use_type_cbox.setCurrentIndex(self.a_use_type_cbox.findData(landuse_id))
        self.a_crop_type_cbox.setCurrentIndex(self.a_crop_type_cbox.findData(crop_id))
        self.a_area_edit.setText(str(area))
        self.a_yield_edit.setText(str(yeild))
        self.a_costs_edit.setText(str(cost))
        self.a_profit_edit.setText(str(profit))
        self.a_net_profit_edit.setText(str(net_profit))

    def __parcel_populate(self):

        if self.parcel_type == 10:
            self.__parcel_home_populate()
        elif self.parcel_type == 20:
            self.__parcel_condominium_populate()
        elif self.parcel_type == 30:
            self.__parcel_industrial_populate()
        elif self.parcel_type == 40:
            self.__parcel_agriculture_populate()

    def __purchase_delete(self):

        session = SessionHandler().session_instance()
        purchase_count = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).count()
        row_count = self.purchase_twidget.rowCount()
        if purchase_count != 0:
            if row_count == 0:
                session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).delete()

    def __commercial_purchase_delete(self):

        session = SessionHandler().session_instance()
        purchase_count = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).count()
        row_count = self.c_purchase_twidget.rowCount()
        if purchase_count != 0:
            if row_count == 0:
                session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).delete()

    def __industrial_purchase_delete(self):

        session = SessionHandler().session_instance()
        purchase_count = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).count()
        row_count = self.i_purchase_twidget.rowCount()
        if purchase_count != 0:
            if row_count == 0:
                session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).delete()

    def __agriculture_purchase_delete(self):

        session = SessionHandler().session_instance()
        purchase_count = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).count()
        row_count = self.a_purchase_twidget.rowCount()
        if purchase_count != 0:
            if row_count == 0:
                session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == self.register_no).delete()

    def __lease_delete(self):

        session = SessionHandler().session_instance()
        lease_count = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).count()
        row_count = self.lease_twidget.rowCount()
        if lease_count != 0:
            if row_count == 0:
                session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).delete()

    def __commercial_lease_delete(self):

        session = SessionHandler().session_instance()
        lease_count = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).count()
        row_count = self.c_lease_twidget.rowCount()
        if lease_count != 0:
            if row_count == 0:
                session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).delete()

    def __industrial_lease_delete(self):

        session = SessionHandler().session_instance()
        lease_count = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).count()
        row_count = self.i_lease_twidget.rowCount()
        if lease_count != 0:
            if row_count == 0:
                session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).delete()

    def __agriculture_lease_delete(self):

        session = SessionHandler().session_instance()
        lease_count = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).count()
        row_count = self.a_lease_twidget.rowCount()
        if lease_count != 0:
            if row_count == 0:
                session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == self.register_no).delete()

    def __building_delete(self):

        session = SessionHandler().session_instance()
        building_id = self.building_no_cbox.itemData(self.building_no_cbox.currentIndex())
        building_count = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).count()
        row_count = self.home_building_twidget.rowCount()
        if building_count != 0:
            if row_count == 0:
                session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).delete()

    def __commercial_building_delete(self):

        session = SessionHandler().session_instance()
        building_id = self.c_building_no_cbox.itemData(self.c_building_no_cbox.currentIndex())
        building_count = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).count()
        row_count = self.c_building_twidget.rowCount()
        if building_count != 0:
            if row_count == 0:
                session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).delete()

    def __industrual_building_delete(self):

        session = SessionHandler().session_instance()
        building_id = self.i_building_no_cbox.itemData(self.i_building_no_cbox.currentIndex())
        building_count = session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).count()
        row_count = self.i_building_twidget.rowCount()
        if building_count != 0:
            if row_count == 0:
                session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == self.register_no).delete()

    def __industrual_product_delete(self):

        session = SessionHandler().session_instance()
        building_count = session.query(VaInfoIndustrialProduct).filter(VaInfoIndustrialProduct.register_no == self.register_no).count()
        row_count = self.i_product_twidget.rowCount()
        if building_count != 0:
            if row_count == 0:
                session.query(VaInfoIndustrialProduct).filter(VaInfoIndustrialProduct.register_no == self.register_no).delete()

    @pyqtSlot()
    def on_help_button_clicked(self):

        os.system("hh.exe C:\Users\User\.qgis2\python\plugins\lm2\help\output\help_lm2.chm::/html/Create_New_Postgis_Connection.htm")

    @pyqtSlot()
    def on_calculate_button_clicked(self):

        parcel_area_max = 0
        parcel_area_min = 0
        parcel_area_avg = 0

        parcel_price_max = 0
        parcel_price_min = 0
        parcel_price_avg = 0

        if self.cost_purchase_rbutton.isChecked() == False and self.cost_lease_rbutton.isChecked() == False:
            PluginUtils.show_message(self, self.tr("Is Checked"), self.tr("Purchase or Lease ???"))
            return

        if self.cost_purchase_rbutton.isChecked():

            parcel_max_area = self.session.query(func.max(CaParcel.area_m2))\
                .join(VaInfoHomeParcel, CaParcel.parcel_id == VaInfoHomeParcel.parcel_id)\
                .join(VaInfoHomePurchase, VaInfoHomeParcel.register_no == VaInfoHomePurchase.register_no)\
                .filter(or_(CaParcel.landuse == 2205, CaParcel.landuse == 2204, CaParcel.landuse == 2206))\
                .filter(extract('year',VaInfoHomeParcel.info_date) == self.year_sbox.value())
            parcel_max = parcel_max_area.one()

            parcel_min_area = self.session.query(func.min(CaParcel.area_m2))\
                .join(VaInfoHomeParcel, CaParcel.parcel_id == VaInfoHomeParcel.parcel_id)\
                .join(VaInfoHomePurchase, VaInfoHomeParcel.register_no == VaInfoHomePurchase.register_no)\
                .filter(or_(CaParcel.landuse == 2205, CaParcel.landuse == 2204, CaParcel.landuse == 2206))\
                .filter(extract('year',VaInfoHomeParcel.info_date) == self.year_sbox.value())
            parcel_min = parcel_min_area.one()

            parcel_avg_area = self.session.query(func.avg(CaParcel.area_m2))\
                .join(VaInfoHomeParcel, CaParcel.parcel_id == VaInfoHomeParcel.parcel_id)\
                .join(VaInfoHomePurchase, VaInfoHomeParcel.register_no == VaInfoHomePurchase.register_no)\
                .filter(or_(CaParcel.landuse == 2205, CaParcel.landuse == 2204, CaParcel.landuse == 2206))\
                .filter(extract('year',VaInfoHomeParcel.info_date) == self.year_sbox.value())
            parcel_avg = parcel_avg_area.one()

            parcel_purchase_max_price = self.session.query(func.max(VaInfoHomePurchase.price))\
                .join(VaInfoHomeParcel, VaInfoHomePurchase.register_no == VaInfoHomeParcel.register_no)\
                .join(CaParcel, VaInfoHomeParcel.parcel_id == CaParcel.parcel_id)\
                .filter(extract('year',VaInfoHomePurchase.purchase_date) == self.year_sbox.value())\
                .filter(or_(VaInfoHomePurchase.landuse == 2205, VaInfoHomePurchase.landuse == 2204, VaInfoHomePurchase.landuse == 2206))
            parcel_purchase_max = parcel_purchase_max_price.one()


            parcel_purchase_min_price = self.session.query(func.min(VaInfoHomePurchase.price))\
                .join(VaInfoHomeParcel, VaInfoHomePurchase.register_no == VaInfoHomeParcel.register_no)\
                .join(CaParcel, VaInfoHomeParcel.parcel_id == CaParcel.parcel_id)\
                .filter(extract('year',VaInfoHomePurchase.purchase_date) == self.year_sbox.value())\
                .filter(or_(VaInfoHomePurchase.landuse == 2205, VaInfoHomePurchase.landuse == 2204, VaInfoHomePurchase.landuse == 2206))
            parcel_purchase_min = parcel_purchase_min_price.one()

            parcel_purchase_avg_price = self.session.query(func.avg(VaInfoHomePurchase.price))\
                .join(VaInfoHomeParcel, VaInfoHomePurchase.register_no == VaInfoHomeParcel.register_no)\
                .join(CaParcel, VaInfoHomeParcel.parcel_id == CaParcel.parcel_id)\
                .filter(extract('year',VaInfoHomePurchase.purchase_date) == self.year_sbox.value())\
                .filter(or_(VaInfoHomePurchase.landuse == 2205, VaInfoHomePurchase.landuse == 2204, VaInfoHomePurchase.landuse == 2206))
            parcel_purchase_avg = parcel_purchase_avg_price.one()

            if self.bag_working_cbox.currentIndex() > 0:
                au_code = self.bag_working_cbox.itemData(self.bag_working_cbox.currentIndex())
                parcel_max_area = parcel_max_area\
                    .filter(CaParcel.geometry.ST_Within(AuLevel3.geometry))\
                    .filter(AuLevel3.code == au_code)
                parcel_max = parcel_max_area.one()

                parcel_min_area = parcel_min_area\
                    .filter(CaParcel.geometry.ST_Within(AuLevel3.geometry))\
                    .filter(AuLevel3.code == au_code)
                parcel_min = parcel_min_area.one()

                parcel_avg_area = parcel_avg_area\
                    .filter(CaParcel.geometry.ST_Within(AuLevel3.geometry))\
                    .filter(AuLevel3.code == au_code)
                parcel_avg = parcel_avg_area.one()

                parcel_purchase_max_price = parcel_purchase_max_price\
                    .filter(CaParcel.geometry.ST_Within(AuLevel3.geometry))\
                    .filter(AuLevel3.code == au_code)
                parcel_purchase_max = parcel_purchase_max_price.one()

                parcel_purchase_min_price = parcel_purchase_min_price\
                    .filter(CaParcel.geometry.ST_Within(AuLevel3.geometry))\
                    .filter(AuLevel3.code == au_code)
                parcel_purchase_min = parcel_purchase_min_price.one()

                parcel_purchase_avg_price = parcel_purchase_avg_price\
                    .filter(CaParcel.geometry.ST_Within(AuLevel3.geometry))\
                    .filter(AuLevel3.code == au_code)
                parcel_purchase_avg = parcel_purchase_avg_price.one()
            if self.cost_year_checkbox.checkState() == False:
                if self.q1_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 1,extract('month',VaInfoHomeParcel.info_date) == 2,extract('month',VaInfoHomeParcel.info_date) == 3))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 1,extract('month',VaInfoHomeParcel.info_date) == 2,extract('month',VaInfoHomeParcel.info_date) == 3))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 1,extract('month',VaInfoHomeParcel.info_date) == 2,extract('month',VaInfoHomeParcel.info_date) == 3))
                    parcel_avg = parcel_avg_area.one()

                    parcel_purchase_max_price = parcel_purchase_max_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 1,extract('month',VaInfoHomePurchase.purchase_date) == 2,extract('month',VaInfoHomePurchase.purchase_date) == 3))
                    parcel_purchase_max = parcel_purchase_max_price.one()

                    parcel_purchase_min_price = parcel_purchase_min_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 1,extract('month',VaInfoHomePurchase.purchase_date) == 2,extract('month',VaInfoHomePurchase.purchase_date) == 3))
                    parcel_purchase_min = parcel_purchase_min_price.one()

                    parcel_purchase_avg_price = parcel_purchase_avg_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 1,extract('month',VaInfoHomePurchase.purchase_date) == 2,extract('month',VaInfoHomePurchase.purchase_date) == 3))
                    parcel_purchase_avg = parcel_purchase_avg_price.one()

                elif self.q1_checkbox.isChecked() and self.q2_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 1,extract('month',VaInfoHomeParcel.info_date) == 2,extract('month',VaInfoHomeParcel.info_date) == 3,\
                                    extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 1,extract('month',VaInfoHomeParcel.info_date) == 2,extract('month',VaInfoHomeParcel.info_date) == 3,\
                                    extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 1,extract('month',VaInfoHomeParcel.info_date) == 2,extract('month',VaInfoHomeParcel.info_date) == 3,\
                                    extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_avg = parcel_avg_area.one()

                    parcel_purchase_max_price = parcel_purchase_max_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 1,extract('month',VaInfoHomePurchase.purchase_date) == 2,extract('month',VaInfoHomePurchase.purchase_date) == 3,\
                                    extract('month',VaInfoHomePurchase.purchase_date) == 4,extract('month',VaInfoHomePurchase.purchase_date) == 5,extract('month',VaInfoHomePurchase.purchase_date) == 6))
                    parcel_purchase_max = parcel_purchase_max_price.one()

                    parcel_purchase_min_price = parcel_purchase_min_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 1,extract('month',VaInfoHomePurchase.purchase_date) == 2,extract('month',VaInfoHomePurchase.purchase_date) == 3,\
                                    extract('month',VaInfoHomePurchase.purchase_date) == 4,extract('month',VaInfoHomePurchase.purchase_date) == 5,extract('month',VaInfoHomePurchase.purchase_date) == 6))
                    parcel_purchase_min = parcel_purchase_min_price.one()

                    parcel_purchase_avg_price = parcel_purchase_avg_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 1,extract('month',VaInfoHomePurchase.purchase_date) == 2,extract('month',VaInfoHomePurchase.purchase_date) == 3,\
                                    extract('month',VaInfoHomePurchase.purchase_date) == 4,extract('month',VaInfoHomePurchase.purchase_date) == 5,extract('month',VaInfoHomePurchase.purchase_date) == 6))
                    parcel_purchase_avg = parcel_purchase_avg_price.one()

                elif self.q2_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_avg = parcel_avg_area.one()

                    parcel_purchase_max_price = parcel_purchase_max_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 4,extract('month',VaInfoHomePurchase.purchase_date) == 5,extract('month',VaInfoHomePurchase.purchase_date) == 6))
                    parcel_purchase_max = parcel_purchase_max_price.one()

                    parcel_purchase_min_price = parcel_purchase_min_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 4,extract('month',VaInfoHomePurchase.purchase_date) == 5,extract('month',VaInfoHomePurchase.purchase_date) == 6))
                    parcel_purchase_min = parcel_purchase_min_price.one()

                    parcel_purchase_avg_price = parcel_purchase_avg_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 4,extract('month',VaInfoHomePurchase.purchase_date) == 5,extract('month',VaInfoHomePurchase.purchase_date) == 6))
                    parcel_purchase_avg = parcel_purchase_avg_price.one()
                elif self.q2_checkbox.isChecked() and self.q3_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9,\
                                    extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9,\
                                    extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9,\
                                    extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_avg = parcel_avg_area.one()

                    parcel_purchase_max_price = parcel_purchase_max_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 7,extract('month',VaInfoHomePurchase.purchase_date) == 8,extract('month',VaInfoHomePurchase.purchase_date) == 9,\
                                    extract('month',VaInfoHomePurchase.purchase_date) == 4,extract('month',VaInfoHomePurchase.purchase_date) == 5,extract('month',VaInfoHomePurchase.purchase_date) == 6))
                    parcel_purchase_max = parcel_purchase_max_price.one()

                    parcel_purchase_min_price = parcel_purchase_min_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 7,extract('month',VaInfoHomePurchase.purchase_date) == 8,extract('month',VaInfoHomePurchase.purchase_date) == 9,\
                                    extract('month',VaInfoHomePurchase.purchase_date) == 4,extract('month',VaInfoHomePurchase.purchase_date) == 5,extract('month',VaInfoHomePurchase.purchase_date) == 6))
                    parcel_purchase_min = parcel_purchase_min_price.one()

                    parcel_purchase_avg_price = parcel_purchase_avg_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 7,extract('month',VaInfoHomePurchase.purchase_date) == 8,extract('month',VaInfoHomePurchase.purchase_date) == 9,\
                                    extract('month',VaInfoHomePurchase.purchase_date) == 4,extract('month',VaInfoHomePurchase.purchase_date) == 5,extract('month',VaInfoHomePurchase.purchase_date) == 6))
                    parcel_purchase_avg = parcel_purchase_avg_price.one()
                elif self.q3_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9))
                    parcel_avg = parcel_avg_area.one()

                    parcel_purchase_max_price = parcel_purchase_max_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 7,extract('month',VaInfoHomePurchase.purchase_date) == 8,extract('month',VaInfoHomePurchase.purchase_date) == 9))
                    parcel_purchase_max = parcel_purchase_max_price.one()

                    parcel_purchase_min_price = parcel_purchase_min_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 7,extract('month',VaInfoHomePurchase.purchase_date) == 8,extract('month',VaInfoHomePurchase.purchase_date) == 9))
                    parcel_purchase_min = parcel_purchase_min_price.one()

                    parcel_purchase_avg_price = parcel_purchase_avg_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 7,extract('month',VaInfoHomePurchase.purchase_date) == 8,extract('month',VaInfoHomePurchase.purchase_date) == 9))
                    parcel_purchase_avg = parcel_purchase_avg_price.one()
                elif self.q3_checkbox.isChecked() and self.q4_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9,\
                                    extract('month',VaInfoHomeParcel.info_date) == 10,extract('month',VaInfoHomeParcel.info_date) == 11,extract('month',VaInfoHomeParcel.info_date) == 12))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9,\
                                    extract('month',VaInfoHomeParcel.info_date) == 10,extract('month',VaInfoHomeParcel.info_date) == 11,extract('month',VaInfoHomeParcel.info_date) == 12))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9,\
                                    extract('month',VaInfoHomeParcel.info_date) == 10,extract('month',VaInfoHomeParcel.info_date) == 11,extract('month',VaInfoHomeParcel.info_date) == 12))
                    parcel_avg = parcel_avg_area.one()

                    parcel_purchase_max_price = parcel_purchase_max_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 7,extract('month',VaInfoHomePurchase.purchase_date) == 8,extract('month',VaInfoHomePurchase.purchase_date) == 9,\
                                    extract('month',VaInfoHomePurchase.purchase_date) == 10,extract('month',VaInfoHomePurchase.purchase_date) == 11,extract('month',VaInfoHomePurchase.purchase_date) == 12))
                    parcel_purchase_max = parcel_purchase_max_price.one()

                    parcel_purchase_min_price = parcel_purchase_min_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 7,extract('month',VaInfoHomePurchase.purchase_date) == 8,extract('month',VaInfoHomePurchase.purchase_date) == 9,\
                                    extract('month',VaInfoHomePurchase.purchase_date) == 10,extract('month',VaInfoHomePurchase.purchase_date) == 11,extract('month',VaInfoHomePurchase.purchase_date) == 12))
                    parcel_purchase_min = parcel_purchase_min_price.one()

                    parcel_purchase_avg_price = parcel_purchase_avg_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 7,extract('month',VaInfoHomePurchase.purchase_date) == 8,extract('month',VaInfoHomePurchase.purchase_date) == 9,\
                                    extract('month',VaInfoHomePurchase.purchase_date) == 10,extract('month',VaInfoHomePurchase.purchase_date) == 11,extract('month',VaInfoHomePurchase.purchase_date) == 12))
                    parcel_purchase_avg = parcel_purchase_avg_price.one()
                elif self.q4_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 10,extract('month',VaInfoHomeParcel.info_date) == 11,extract('month',VaInfoHomeParcel.info_date) == 12))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 10,extract('month',VaInfoHomeParcel.info_date) == 11,extract('month',VaInfoHomeParcel.info_date) == 12))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 10,extract('month',VaInfoHomeParcel.info_date) == 11,extract('month',VaInfoHomeParcel.info_date) == 12))
                    parcel_avg = parcel_avg_area.one()

                    parcel_purchase_max_price = parcel_purchase_max_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 10,extract('month',VaInfoHomePurchase.purchase_date) == 11,extract('month',VaInfoHomePurchase.purchase_date) == 12))
                    parcel_purchase_max = parcel_purchase_max_price.one()

                    parcel_purchase_min_price = parcel_purchase_min_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 10,extract('month',VaInfoHomePurchase.purchase_date) == 11,extract('month',VaInfoHomePurchase.purchase_date) == 12))
                    parcel_purchase_min = parcel_purchase_min_price.one()

                    parcel_purchase_avg_price = parcel_purchase_avg_price\
                        .filter(or_(extract('month',VaInfoHomePurchase.purchase_date) == 10,extract('month',VaInfoHomePurchase.purchase_date) == 11,extract('month',VaInfoHomePurchase.purchase_date) == 12))
                    parcel_purchase_avg = parcel_purchase_avg_price.one()

            for area in parcel_avg:
                if area == None:
                    parcel_area_avg = 0
                else:
                    parcel_area_avg = int(area)
            for area in parcel_max:
                if area == None:
                    parcel_area_max = 0
                else:
                    parcel_area_max = int(area)
            for area in parcel_min:
                if area == None:
                    parcel_area_min = 0
                else:
                    parcel_area_min = int(area)

            for price in parcel_purchase_max:
                if price == None:
                    parcel_price_max = 0
                else:
                    parcel_price_max = int(price)
            for price in parcel_purchase_min:
                if price == None:
                    parcel_price_min = 0
                else:
                    parcel_price_min = int(price)
            for price in parcel_purchase_avg:
                if price == None:
                    parcel_price_avg = 0
                else:
                    parcel_price_avg = int(price)
        elif self.cost_lease_rbutton.isChecked():
            parcel_max_area = self.session.query(func.max(CaParcel.area_m2))\
                .join(VaInfoHomeParcel, CaParcel.parcel_id == VaInfoHomeParcel.parcel_id)\
                .join(VaInfoHomeLease, VaInfoHomeParcel.register_no == VaInfoHomeLease.register_no)\
                .filter(extract('year',VaInfoHomeParcel.info_date) == self.year_sbox.value())\
                .filter(or_(CaParcel.landuse == 2205, CaParcel.landuse == 2204, CaParcel.landuse == 2206))
            parcel_max = parcel_max_area.one()

            parcel_min_area = self.session.query(func.min(CaParcel.area_m2))\
                .join(VaInfoHomeParcel, CaParcel.parcel_id == VaInfoHomeParcel.parcel_id)\
                .join(VaInfoHomeLease, VaInfoHomeParcel.register_no == VaInfoHomeLease.register_no)\
                .filter(extract('year',VaInfoHomeParcel.info_date) == self.year_sbox.value())\
                .filter(or_(CaParcel.landuse == 2205, CaParcel.landuse == 2204, CaParcel.landuse == 2206))
            parcel_min = parcel_min_area.one()

            parcel_avg_area = self.session.query(func.avg(CaParcel.area_m2))\
                .join(VaInfoHomeParcel, CaParcel.parcel_id == VaInfoHomeParcel.parcel_id)\
                .join(VaInfoHomeLease, VaInfoHomeParcel.register_no == VaInfoHomeLease.register_no)\
                .filter(extract('year',VaInfoHomeParcel.info_date) == self.year_sbox.value())\
                .filter(or_(CaParcel.landuse == 2205, CaParcel.landuse == 2204, CaParcel.landuse == 2206))
            parcel_avg = parcel_avg_area.one()

            parcel_lease_max_price = self.session.query(func.max(VaInfoHomeLease.monthly_rent))\
                .join(VaInfoHomeParcel, VaInfoHomeLease.register_no == VaInfoHomeParcel.register_no)\
                .join(CaParcel, VaInfoHomeParcel.parcel_id == CaParcel.parcel_id)\
                .filter(extract('year',VaInfoHomeLease.lease_date) == self.year_sbox.value())\
                .filter(or_(VaInfoHomeLease.landuse == 2205, VaInfoHomeLease.landuse == 2204, VaInfoHomeLease.landuse == 2206))
            parcel_lease_max = parcel_lease_max_price.one()

            parcel_lease_min_price = self.session.query(func.min(VaInfoHomeLease.monthly_rent))\
                .join(VaInfoHomeParcel, VaInfoHomeLease.register_no == VaInfoHomeParcel.register_no)\
                .join(CaParcel, VaInfoHomeParcel.parcel_id == CaParcel.parcel_id)\
                .filter(extract('year',VaInfoHomeLease.lease_date) == self.year_sbox.value())\
                .filter(or_(VaInfoHomeLease.landuse == 2205, VaInfoHomeLease.landuse == 2204, VaInfoHomeLease.landuse == 2206))
            parcel_lease_min = parcel_lease_min_price.one()

            parcel_lease_avg_price = self.session.query(func.avg(VaInfoHomeLease.monthly_rent))\
                .join(VaInfoHomeParcel, VaInfoHomeLease.register_no == VaInfoHomeParcel.register_no)\
                .join(CaParcel, VaInfoHomeParcel.parcel_id == CaParcel.parcel_id)\
                .filter(extract('year',VaInfoHomeLease.lease_date) == self.year_sbox.value())\
                .filter(or_(VaInfoHomeLease.landuse == 2205, VaInfoHomeLease.landuse == 2204, VaInfoHomeLease.landuse == 2206))
            parcel_lease_avg = parcel_lease_avg_price.one()

            if self.bag_working_cbox.currentIndex() > 0:
                au_code = self.bag_working_cbox.itemData(self.bag_working_cbox.currentIndex())
                parcel_max_area = parcel_max_area\
                    .filter(CaParcel.geometry.ST_Within(AuLevel3.geometry))\
                    .filter(AuLevel3.code == au_code)
                parcel_max = parcel_max_area.one()

                parcel_min_area = parcel_min_area\
                    .filter(CaParcel.geometry.ST_Within(AuLevel3.geometry))\
                    .filter(AuLevel3.code == au_code)
                parcel_min = parcel_min_area.one()

                parcel_avg_area = parcel_avg_area\
                    .filter(CaParcel.geometry.ST_Within(AuLevel3.geometry))\
                    .filter(AuLevel3.code == au_code)
                parcel_avg = parcel_avg_area.one()

                parcel_lease_max_price = parcel_lease_max_price\
                    .filter(CaParcel.geometry.ST_Within(AuLevel3.geometry))\
                    .filter(AuLevel3.code == au_code)
                parcel_lease_max = parcel_lease_max_price.one()

                parcel_lease_min_price = parcel_lease_min_price\
                    .filter(CaParcel.geometry.ST_Within(AuLevel3.geometry))\
                    .filter(AuLevel3.code == au_code)
                parcel_lease_min = parcel_lease_min_price.one()

                parcel_lease_avg_price = parcel_lease_avg_price\
                    .filter(CaParcel.geometry.ST_Within(AuLevel3.geometry))\
                    .filter(AuLevel3.code == au_code)
                parcel_lease_avg = parcel_lease_avg_price.one()

            if self.cost_year_checkbox.checkState() == False:
                if self.q1_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 1,extract('month',VaInfoHomeParcel.info_date) == 2,extract('month',VaInfoHomeParcel.info_date) == 3))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 1,extract('month',VaInfoHomeParcel.info_date) == 2,extract('month',VaInfoHomeParcel.info_date) == 3))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 1,extract('month',VaInfoHomeParcel.info_date) == 2,extract('month',VaInfoHomeParcel.info_date) == 3))
                    parcel_avg = parcel_avg_area.one()

                    parcel_lease_max_price = parcel_lease_max_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 1,extract('month',VaInfoHomeLease.lease_date) == 2,extract('month',VaInfoHomeLease.lease_date) == 3))
                    parcel_lease_max = parcel_lease_max_price.one()

                    parcel_lease_min_price = parcel_lease_min_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 1,extract('month',VaInfoHomeLease.lease_date) == 2,extract('month',VaInfoHomeLease.lease_date) == 3))
                    parcel_lease_min = parcel_lease_min_price.one()

                    parcel_lease_avg_price = parcel_lease_avg_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 1,extract('month',VaInfoHomeLease.lease_date) == 2,extract('month',VaInfoHomeLease.lease_date) == 3))
                    parcel_lease_avg = parcel_lease_avg_price.one()

                elif self.q1_checkbox.isChecked() and self.q2_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 1,extract('month',VaInfoHomeParcel.info_date) == 2,extract('month',VaInfoHomeParcel.info_date) == 3,\
                                    extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 1,extract('month',VaInfoHomeParcel.info_date) == 2,extract('month',VaInfoHomeParcel.info_date) == 3,\
                                    extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 1,extract('month',VaInfoHomeParcel.info_date) == 2,extract('month',VaInfoHomeParcel.info_date) == 3,\
                                    extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_avg = parcel_avg_area.one()

                    parcel_lease_max_price = parcel_lease_max_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 1,extract('month',VaInfoHomeLease.lease_date) == 2,extract('month',VaInfoHomeLease.lease_date) == 3,\
                                    extract('month',VaInfoHomeLease.lease_date) == 4,extract('month',VaInfoHomeLease.lease_date) == 5,extract('month',VaInfoHomeLease.lease_date) == 6))
                    parcel_lease_max = parcel_lease_max_price.one()

                    parcel_lease_min_price = parcel_lease_min_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 1,extract('month',VaInfoHomeLease.lease_date) == 2,extract('month',VaInfoHomeLease.lease_date) == 3,\
                                    extract('month',VaInfoHomeLease.lease_date) == 4,extract('month',VaInfoHomeLease.lease_date) == 5,extract('month',VaInfoHomeLease.lease_date) == 6))
                    parcel_lease_min = parcel_lease_min_price.one()

                    parcel_lease_avg_price = parcel_lease_avg_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 1,extract('month',VaInfoHomeLease.lease_date) == 2,extract('month',VaInfoHomeLease.lease_date) == 3,\
                                    extract('month',VaInfoHomeLease.lease_date) == 4,extract('month',VaInfoHomeLease.lease_date) == 5,extract('month',VaInfoHomeLease.lease_date) == 6))
                    parcel_lease_avg = parcel_lease_avg_price.one()

                elif self.q2_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_avg = parcel_avg_area.one()

                    parcel_lease_max_price = parcel_lease_max_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 4,extract('month',VaInfoHomeLease.lease_date) == 5,extract('month',VaInfoHomeLease.lease_date) == 6))
                    parcel_lease_max = parcel_lease_max_price.one()

                    parcel_lease_min_price = parcel_lease_min_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 4,extract('month',VaInfoHomeLease.lease_date) == 5,extract('month',VaInfoHomeLease.lease_date) == 6))
                    parcel_lease_min = parcel_lease_min_price.one()

                    parcel_lease_avg_price = parcel_lease_avg_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 4,extract('month',VaInfoHomeLease.lease_date) == 5,extract('month',VaInfoHomeLease.lease_date) == 6))
                    parcel_lease_avg = parcel_lease_avg_price.one()
                elif self.q2_checkbox.isChecked() and self.q3_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9,\
                                    extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9,\
                                    extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9,\
                                    extract('month',VaInfoHomeParcel.info_date) == 4,extract('month',VaInfoHomeParcel.info_date) == 5,extract('month',VaInfoHomeParcel.info_date) == 6))
                    parcel_avg = parcel_avg_area.one()

                    parcel_lease_max_price = parcel_lease_max_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 7,extract('month',VaInfoHomeLease.lease_date) == 8,extract('month',VaInfoHomeLease.lease_date) == 9,\
                                    extract('month',VaInfoHomeLease.lease_date) == 4,extract('month',VaInfoHomeLease.lease_date) == 5,extract('month',VaInfoHomeLease.lease_date) == 6))
                    parcel_lease_max = parcel_lease_max_price.one()

                    parcel_lease_min_price = parcel_lease_min_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 7,extract('month',VaInfoHomeLease.lease_date) == 8,extract('month',VaInfoHomeLease.lease_date) == 9,\
                                    extract('month',VaInfoHomeLease.lease_date) == 4,extract('month',VaInfoHomeLease.lease_date) == 5,extract('month',VaInfoHomeLease.lease_date) == 6))
                    parcel_lease_min = parcel_lease_min_price.one()

                    parcel_lease_avg_price = parcel_lease_avg_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 7,extract('month',VaInfoHomeLease.lease_date) == 8,extract('month',VaInfoHomeLease.lease_date) == 9,\
                                    extract('month',VaInfoHomeLease.lease_date) == 4,extract('month',VaInfoHomeLease.lease_date) == 5,extract('month',VaInfoHomeLease.lease_date) == 6))
                    parcel_lease_avg = parcel_lease_avg_price.one()
                elif self.q3_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9))
                    parcel_avg = parcel_avg_area.one()

                    parcel_lease_max_price = parcel_lease_max_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 7,extract('month',VaInfoHomeLease.lease_date) == 8,extract('month',VaInfoHomeLease.lease_date) == 9))
                    parcel_lease_max = parcel_lease_max_price.one()

                    parcel_lease_min_price = parcel_lease_min_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 7,extract('month',VaInfoHomeLease.lease_date) == 8,extract('month',VaInfoHomeLease.lease_date) == 9))
                    parcel_lease_min = parcel_lease_min_price.one()

                    parcel_lease_avg_price = parcel_lease_avg_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 7,extract('month',VaInfoHomeLease.lease_date) == 8,extract('month',VaInfoHomeLease.lease_date) == 9))
                    parcel_lease_avg = parcel_lease_avg_price.one()
                elif self.q3_checkbox.isChecked() and self.q4_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9,\
                                    extract('month',VaInfoHomeParcel.info_date) == 10,extract('month',VaInfoHomeParcel.info_date) == 11,extract('month',VaInfoHomeParcel.info_date) == 12))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9,\
                                    extract('month',VaInfoHomeParcel.info_date) == 10,extract('month',VaInfoHomeParcel.info_date) == 11,extract('month',VaInfoHomeParcel.info_date) == 12))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 7,extract('month',VaInfoHomeParcel.info_date) == 8,extract('month',VaInfoHomeParcel.info_date) == 9,\
                                    extract('month',VaInfoHomeParcel.info_date) == 10,extract('month',VaInfoHomeParcel.info_date) == 11,extract('month',VaInfoHomeParcel.info_date) == 12))
                    parcel_avg = parcel_avg_area.one()

                    parcel_lease_max_price = parcel_lease_max_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 7,extract('month',VaInfoHomeLease.lease_date) == 8,extract('month',VaInfoHomeLease.lease_date) == 9,\
                                    extract('month',VaInfoHomeLease.lease_date) == 10,extract('month',VaInfoHomeLease.lease_date) == 11,extract('month',VaInfoHomeLease.lease_date) == 12))
                    parcel_lease_max = parcel_lease_max_price.one()

                    parcel_lease_min_price = parcel_lease_min_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 7,extract('month',VaInfoHomeLease.lease_date) == 8,extract('month',VaInfoHomeLease.lease_date) == 9,\
                                    extract('month',VaInfoHomeLease.lease_date) == 10,extract('month',VaInfoHomeLease.lease_date) == 11,extract('month',VaInfoHomeLease.lease_date) == 12))
                    parcel_lease_min = parcel_lease_min_price.one()

                    parcel_lease_avg_price = parcel_lease_avg_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 7,extract('month',VaInfoHomeLease.lease_date) == 8,extract('month',VaInfoHomeLease.lease_date) == 9,\
                                    extract('month',VaInfoHomeLease.lease_date) == 10,extract('month',VaInfoHomeLease.lease_date) == 11,extract('month',VaInfoHomeLease.lease_date) == 12))
                    parcel_lease_avg = parcel_lease_avg_price.one()
                elif self.q4_checkbox.isChecked():
                    parcel_max_area = parcel_max_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 10,extract('month',VaInfoHomeParcel.info_date) == 11,extract('month',VaInfoHomeParcel.info_date) == 12))
                    parcel_max = parcel_max_area.one()

                    parcel_min_area = parcel_min_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 10,extract('month',VaInfoHomeParcel.info_date) == 11,extract('month',VaInfoHomeParcel.info_date) == 12))
                    parcel_min = parcel_min_area.one()

                    parcel_avg_area = parcel_avg_area\
                        .filter(or_(extract('month',VaInfoHomeParcel.info_date) == 10,extract('month',VaInfoHomeParcel.info_date) == 11,extract('month',VaInfoHomeParcel.info_date) == 12))
                    parcel_avg = parcel_avg_area.one()

                    parcel_lease_max_price = parcel_lease_max_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 10,extract('month',VaInfoHomeLease.lease_date) == 11,extract('month',VaInfoHomeLease.lease_date) == 12))
                    parcel_lease_max = parcel_lease_max_price.one()

                    parcel_lease_min_price = parcel_lease_min_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 10,extract('month',VaInfoHomeLease.lease_date) == 11,extract('month',VaInfoHomeLease.lease_date) == 12))
                    parcel_lease_min = parcel_lease_min_price.one()

                    parcel_lease_avg_price = parcel_lease_avg_price\
                        .filter(or_(extract('month',VaInfoHomeLease.lease_date) == 10,extract('month',VaInfoHomeLease.lease_date) == 11,extract('month',VaInfoHomeLease.lease_date) == 12))
                    parcel_lease_avg = parcel_lease_avg_price.one()

            for area in parcel_avg:
                if area == None:
                    parcel_area_avg = 0
                else:
                    parcel_area_avg = int(area)
            for area in parcel_max:
                if area == None:
                    parcel_area_max = 0
                else:
                    parcel_area_max = int(area)
            for area in parcel_min:
                if area == None:
                    parcel_area_min = 0
                else:
                    parcel_area_min = int(area)

            for price in parcel_lease_max:
                if price == None:
                    parcel_price_max = 0
                else:
                    parcel_price_max = int(price)
            for price in parcel_lease_min:
                if price == None:
                    parcel_price_max = 0
                else:
                    parcel_price_min = int(price)
            for price in parcel_lease_avg:
                if price == None:
                    parcel_price_max = 0
                else:
                    parcel_price_avg = int(price)

        if parcel_price_max != 0 and parcel_area_max != 0:
            price_max = int(parcel_price_max/parcel_area_max)
        else:
            price_max = 0
        if parcel_price_min != 0 and parcel_area_min != 0:
            price_min = int(parcel_price_min/parcel_area_min)
        else:
            price_min = 0
        if parcel_price_avg != 0 and parcel_area_avg != 0:
            price_avg = int(parcel_price_avg/parcel_area_avg)
        else:
            price_avg = 0

        item = QTableWidgetItem(str(parcel_area_max))
        item.setData(Qt.UserRole, parcel_area_max)
        self.calculate_twidget.setItem(1,1,item)

        item = QTableWidgetItem(str(parcel_area_min))
        item.setData(Qt.UserRole, parcel_area_min)
        self.calculate_twidget.setItem(2,1,item)

        item = QTableWidgetItem(str(parcel_area_avg))
        item.setData(Qt.UserRole, parcel_area_avg)
        self.calculate_twidget.setItem(0,1,item)

        #purchase
        item = QTableWidgetItem(str(parcel_price_max))
        item.setData(Qt.UserRole, parcel_price_max)
        self.calculate_twidget.setItem(1,2,item)

        item = QTableWidgetItem(str(parcel_price_min))
        item.setData(Qt.UserRole, parcel_price_min)
        self.calculate_twidget.setItem(2,2,item)

        item = QTableWidgetItem(str(parcel_price_avg))
        item.setData(Qt.UserRole, parcel_price_avg)
        self.calculate_twidget.setItem(0,2,item)

        #div
        item = QTableWidgetItem(str(price_max))
        item.setData(Qt.UserRole, price_max)
        self.calculate_twidget.setItem(1,0,item)

        item = QTableWidgetItem(str(price_min))
        item.setData(Qt.UserRole, price_min)
        self.calculate_twidget.setItem(2,0,item)

        item = QTableWidgetItem(str(price_avg))
        item.setData(Qt.UserRole, price_avg)
        self.calculate_twidget.setItem(0,0,item)

    @pyqtSlot(bool)
    def on_electricity_no_rbutton_toggled(self, state):

        if state:
            self.electricity_distancel_edit.setEnabled(False)
            self.electricity_connection_cost_edit.setEnabled(False)
            self.electricity_distancel_edit.setText(None)
            self.electricity_connection_cost_edit.setText(None)
        else:
            self.electricity_distancel_edit.setEnabled(True)
            self.electricity_connection_cost_edit.setEnabled(True)

    @pyqtSlot(bool)
    def on_heating_no_rbutton_toggled(self, state):

        if state:
            self.central_heat_distancel_edit.setEnabled(False)
            self.central_heat_connection_cost_edit.setEnabled(False)
            self.central_heat_distancel_edit.setText(None)
            self.central_heat_connection_cost_edit.setText(None)
        else:
            self.central_heat_distancel_edit.setEnabled(True)
            self.central_heat_connection_cost_edit.setEnabled(True)

    @pyqtSlot(bool)
    def on_water_no_rbutton_toggled(self, state):

        if state:
            self.water_distancel_edit.setEnabled(False)
            self.water_connection_cost_edit.setEnabled(False)
            self.water_distancel_edit.setText(None)
            self.water_connection_cost_edit.setText(None)
        else:
            self.water_distancel_edit.setEnabled(True)
            self.water_connection_cost_edit.setEnabled(True)

    @pyqtSlot(bool)
    def on_sewage_no_rbutton_toggled(self, state):

        if state:
            self.sewage_distancel_edit.setEnabled(False)
            self.sewage_connection_cost_edit.setEnabled(False)
            self.sewage_distancel_edit.setText(None)
            self.sewage_connection_cost_edit.setText(None)
        else:
            self.sewage_distancel_edit.setEnabled(True)
            self.sewage_connection_cost_edit.setEnabled(True)

    @pyqtSlot(bool)
    def on_well_no_rbutton_toggled(self, state):

        if state:
            self.well_distancel_edit.setEnabled(False)
            self.well_distancel_edit.setText(None)
        else:
            self.well_distancel_edit.setEnabled(True)

    @pyqtSlot(bool)
    def on_phone_no_rbutton_toggled(self, state):

        if state:
            self.phone_distancel_edit.setEnabled(False)
            self.phone_distancel_edit.setText(None)
        else:
            self.phone_distancel_edit.setEnabled(True)

    @pyqtSlot(bool)
    def on_flood_no_rbutton_toggled(self, state):

        if state:
            self.flood_channel_distancel_edit.setEnabled(False)
            self.flood_channel_distancel_edit.setText(None)
        else:
            self.flood_channel_distancel_edit.setEnabled(True)

    @pyqtSlot(bool)
    def on_plot_no_rbutton_toggled(self, state):

        if state:
            self.vegetable_plot_size_edit.setEnabled(False)
            self.vegetable_plot_size_edit.setText(None)
        else:
            self.vegetable_plot_size_edit.setEnabled(True)

    #industrial product time
    @pyqtSlot(bool)
    def on_i_day_rbutton_toggled(self, state):

        if state:
            self.i_month_rbutton.setChecked(False)
            self.i_year_rbutton.setChecked(False)

    #industrial product time
    @pyqtSlot(bool)
    def on_i_month_rbutton_toggled(self, state):

        if state:
            self.i_day_rbutton.setChecked(False)
            self.i_year_rbutton.setChecked(False)

    #industrial product time
    @pyqtSlot(bool)
    def on_i_year_rbutton_toggled(self, state):

        if state:
            self.i_day_rbutton.setChecked(False)
            self.i_month_rbutton.setChecked(False)