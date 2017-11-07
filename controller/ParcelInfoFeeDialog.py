# coding=utf8
import os

__author__ = 'ankhbold'
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_, extract
from ..view.Ui_ParcelInfoFeeDialog import *
from ..utils.SessionHandler import SessionHandler
from ..utils.PluginUtils import *
from ..model.BsPerson import *
from ..model.CtFee import *
from ..model.DatabaseHelper import *
from ..model.SetPayment import *
from ..model.FeeUnified import *
from ..model.ContractSearch import *
from ..model.ClContractStatus import *
from ..model.ClLanduseType import *
from ..model.SetFeeZone import *

class ParcelInfoFeeDialog(QDialog, Ui_ParcelInfoFeeDialog):

    def __init__(self, old_parcel_id, person_id, is_find, parent=None):

        super(ParcelInfoFeeDialog, self).__init__(parent)
        self.setupUi(self)
        self.session = SessionHandler().session_instance()
        self.old_parcel_id = old_parcel_id
        self.person_id = person_id

        self.close_button.clicked.connect(self.reject)

        self.old_parcel_id_edit.setText(self.old_parcel_id)
        self.person_id_edit.setText(self.person_id)

        self.__setup_table_widget()

        if is_find:
            self.__load_fee(self.person_id, self.old_parcel_id)
        else:
            self.find_gbox.setEnabled(True)
            self.old_parcel_id_edit.setEnabled(True)
            self.person_id_edit.setEnabled(True)

    def __setup_table_widget(self):

        self.fee_info_twidget.setAlternatingRowColors(True)
        self.fee_info_twidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.fee_info_twidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.fee_info_twidget.setSelectionMode(QTableWidget.SingleSelection)
        self.fee_info_twidget.horizontalHeader().setResizeMode(QHeaderView.ResizeToContents)

    def __load_fee(self, person_id, old_parcel_id):


        self.fee_info_twidget.setRowCount(0)
        soum_code = DatabaseUtils.working_l2_code()

        sql = "select fee_year, year_fee, m2_fee, subsidized_fee_rate, left_previous_year, surplus_previous_year, payable_year, offset_fee, control_1, " \
              "quarterly1_fee, quarterly2_fee, quarterly3_fee, quarterly4_fee, payment_year, fee.objectid " \
              "from ub_fee fee " \
              "join s"+soum_code+".ub_fee_person person on fee.pid = person.pid::text " \
              "where fee.pid::text like :pid and person.register like :person_id " \
              "group by fee_year, year_fee, m2_fee, subsidized_fee_rate, left_previous_year, surplus_previous_year, payable_year, offset_fee, control_1, " \
              "quarterly1_fee, quarterly2_fee, quarterly3_fee, quarterly4_fee, payment_year, fee.objectid "

        result = self.session.execute(sql, {'pid': old_parcel_id,
                                            'person_id': person_id})
        row = 0
        for item_row in result:

            fee_year = item_row[0]

            row = self.fee_info_twidget.rowCount()
            self.fee_info_twidget.insertRow(row)

            item = QTableWidgetItem()
            item.setText(fee_year)
            item.setData(Qt.UserRole, item_row[14])
            self.fee_info_twidget.setItem(row, 0, item)

            item = QTableWidgetItem()
            item.setText(item_row[1])
            item.setData(Qt.UserRole, item_row[1])
            self.fee_info_twidget.setItem(row, 1, item)

            item = QTableWidgetItem()
            item.setText(item_row[2])
            item.setData(Qt.UserRole, item_row[2])
            self.fee_info_twidget.setItem(row, 2, item)

            item = QTableWidgetItem()
            item.setText(item_row[3])
            item.setData(Qt.UserRole, item_row[3])
            self.fee_info_twidget.setItem(row, 3, item)

            item = QTableWidgetItem()
            item.setText(item_row[3])
            item.setData(Qt.UserRole, item_row[3])
            self.fee_info_twidget.setItem(row, 3, item)

            item = QTableWidgetItem()
            item.setText(item_row[4])
            item.setData(Qt.UserRole, item_row[4])
            self.fee_info_twidget.setItem(row, 4, item)

            item = QTableWidgetItem()
            item.setText(item_row[5])
            item.setData(Qt.UserRole, item_row[5])
            self.fee_info_twidget.setItem(row, 5, item)

            item = QTableWidgetItem()
            item.setText(item_row[6])
            item.setData(Qt.UserRole, item_row[6])
            self.fee_info_twidget.setItem(row, 6, item)

            item = QTableWidgetItem()
            item.setText(item_row[7])
            item.setData(Qt.UserRole, item_row[7])
            self.fee_info_twidget.setItem(row, 7, item)

            item = QTableWidgetItem()
            item.setText(item_row[8])
            item.setData(Qt.UserRole, item_row[8])
            self.fee_info_twidget.setItem(row, 8, item)

            item = QTableWidgetItem()
            item.setText(item_row[9])
            item.setData(Qt.UserRole, item_row[9])
            self.fee_info_twidget.setItem(row, 9, item)

            item = QTableWidgetItem()
            item.setText(item_row[10])
            item.setData(Qt.UserRole, item_row[10])
            self.fee_info_twidget.setItem(row, 10, item)

            item = QTableWidgetItem()
            item.setText(item_row[11])
            item.setData(Qt.UserRole, item_row[11])
            self.fee_info_twidget.setItem(row, 11, item)

            item = QTableWidgetItem()
            item.setText(item_row[12])
            item.setData(Qt.UserRole, item_row[12])
            self.fee_info_twidget.setItem(row, 12, item)

            item = QTableWidgetItem()
            item.setText(item_row[13])
            item.setData(Qt.UserRole, item_row[13])
            self.fee_info_twidget.setItem(row, 13, item)

            row =+ 1

    @pyqtSlot(QTableWidgetItem)
    def on_fee_info_twidget_itemClicked(self, item):

        selected_row = self.fee_info_twidget.currentRow()
        person_id = self.fee_info_twidget.item(selected_row, 0).text()
        object_id = self.fee_info_twidget.item(selected_row, 0).data(Qt.UserRole)
        soum_code = DatabaseUtils.working_l2_code()

        sql = "select quarterly1_paid, quarterly2_paid, quarterly3_paid, quarterly4_paid, all_paid, " \
              "left_previous_year_paid, payment_year_paid, offset_paid, frequency_paid, fine_paid, city_all_paid, district_all_paid, " \
              "cancel_paid, cancel_other_paid, left_paid, surplus_paid, transfer_decision, decsription, " \
              "decision_date, decision_no, fee.pid, landuse_desc, landuse_code, area_m2 " \
              "from ub_fee fee " \
              "join s"+soum_code+".ub_fee_person person on fee.pid = person.pid::text " \
              "where fee.objectid = :object_id "

        result = self.session.execute(sql, {'object_id': object_id})
        row = 0
        for item_row in result:

            self.quarterly1_paid_edit.setText(item_row[0])
            self.quarterly2_paid_edit.setText(item_row[1])
            self.quarterly3_paid_edit.setText(item_row[2])
            self.quarterly4_paid_edit.setText(item_row[3])
            self.all_paid_edit.setText(item_row[4])

            self.left_previous_year_paid_edit.setText(item_row[5])
            self.payment_year_paid_edit.setText(item_row[6])
            self.offset_paid_edit.setText(item_row[7])
            self.frequency_paid_edit.setText(item_row[8])
            self.fine_paid_edit.setText(item_row[9])

            self.city_all_paid_edit.setText(item_row[10])
            self.district_all_paid_edit.setText(item_row[11])
            self.cancel_paid_edit.setText(item_row[12])
            self.cancel_other_paid_edit.setText(item_row[13])
            self.left_paid_edit.setText(item_row[14])
            self.surplus_paid_edit.setText(item_row[15])

            self.transfer_decision_txt.setText(item_row[16])
            self.decsription_txt.setText(item_row[17])

            self.decision_date_edit.setText(str(item_row[18]))
            self.decision_no_edit.setText(item_row[19])
            self.old_parcel_id_edit.setText(item_row[20])
            self.old_parcel_id = item_row[20]

            if item_row[22] != None and item_row[21] != None:
                self.landuse_edit.setText(item_row[22]+': '+item_row[21])
            self.area_m2_edit.setText(item_row[23])

        self.__parcel_fee(self.old_parcel_id)

    def __parcel_fee(self, old_parcel_id):

        parcel_count = self.session.query(CaParcel).filter(CaParcel.old_parcel_id == self.old_parcel_id).count()
        if parcel_count != 1:
            return
        soum = DatabaseUtils.working_l2_code()
        parcel = self.session.query(CaParcel).filter(CaParcel.old_parcel_id == self.old_parcel_id).one()
        parcel_id = parcel.parcel_id
        self.parcel_area_edit.setText(str(parcel.area_m2))
        landuse = self.session.query(ClLanduseType).filter(ClLanduseType.code == parcel.landuse).one()
        self.parcel_landuse_edit.setText(str(landuse.code)+':'+landuse.description)
        zone_count = self.session.query(SetFeeZone).filter(parcel.geometry.ST_Within(SetFeeZone.geometry)).\
            filter(SetFeeZone.code == soum).count()
        if zone_count == 1:
            zone = self.session.query(SetFeeZone).filter(parcel.geometry.ST_Within(SetFeeZone.geometry)). \
                filter(SetFeeZone.code == soum).one()
            self.parcel_zone_edit.setText(str(zone.zone_no)+u'-р бүс')
        contracts = self.session.query(ContractSearch.contract_no).filter(ContractSearch.parcel_id == parcel_id).all()

        for contract in contracts:
            self.contract_cbox.addItem(contract.contract_no, contract.contract_no)

    @pyqtSlot(int)
    def on_contract_cbox_currentIndexChanged(self, idx):

        self.__clear_controls()
        if idx == -1:
            return

        contract_no = self.contract_cbox.itemData(self.contract_cbox.currentIndex())
        contract = self.session.query(CtContract).filter(CtContract.contract_no == contract_no).one()
        contract_status = self.session.query(ClContractStatus).filter(ClContractStatus.code == contract.status).one()
        self.contract_status_edit.setText(contract_status.description)
        self.__update_payment_summary(contract)

    def __update_payment_summary(self, contract):

        count = contract.fees.count()
        if count == 0:
            return

        fees = contract.fees.all()
        # self.grace_period_edit.setText(str(fee.grace_period))
        # self.payment_frequency_edit.setText(fee.payment_frequency_ref.description)
        for fee in fees:
            self.__set_fee_summary(fee, contract)
        # self.__set_fine_summary(fee)
        # self.__update_payment_status(fee)

    def __set_fee_summary(self, fee, contract):

        if not len(self.fee_info_twidget.selectedItems()):
            return

        # payment_year = self.year_sbox.value()
        selected_row = self.fee_info_twidget.currentRow()
        payment_year = int(self.fee_info_twidget.item(selected_row, 0).text())

        fee_to_pay_for_current_year = \
            self.__fee_to_pay_per_period(fee, date(payment_year, 1, 1), date(payment_year+1, 1, 1))

        paid_for_current_year = self.session.query(func.sum(CtFeePayment.amount_paid))\
            .filter(CtFeePayment.contract == fee.contract).filter(CtFeePayment.person == fee.person)\
            .filter(CtFeePayment.year_paid_for == payment_year).scalar()

        if paid_for_current_year is None:
            paid_for_current_year = 0

        surplus = self.__surplus_from_previous_years(fee, contract)

        fee_left_to_pay = fee_to_pay_for_current_year - (paid_for_current_year + surplus)
        if fee_left_to_pay < 0:
            fee_left_to_pay = 0

        # set for display
        self.fee_per_year_edit.setText(str(fee_to_pay_for_current_year))
        self.fee_paid_edit.setText(str(paid_for_current_year))
        self.surplus_from_last_years_edit.setText(str(surplus))
        self.fee_to_pay_edit.setText(str(fee_left_to_pay))
        if fee_left_to_pay > 0:
            self.__change_text_color(self.fee_to_pay_edit)
        else:
            self.__reset_text_color(self.fee_to_pay_edit)

    def __surplus_from_previous_years(self, fee, contract):

        # year_to_pay_for = self.year_sbox.value()
        selected_row = self.fee_info_twidget.currentRow()
        year_to_pay_for = int(self.fee_info_twidget.item(selected_row, 0).text())
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

    @pyqtSlot()
    def on_clear_button_clicked(self):

        self.find_gbox.setEnabled(True)

        self.__clear_all()

    def __clear_all(self):

        self.fee_info_twidget.setRowCount(0)
        self.old_parcel_id_edit.setEnabled(True)
        self.person_id_edit.setEnabled(True)

        self.old_parcel_id_edit.clear()
        self.person_id_edit.clear()

    @pyqtSlot()
    def on_find_button_clicked(self):

        self.fee_info_twidget.setRowCount(0)

        person_id = "%" + self.person_id_edit.text() + "%"
        old_parcel_id = "%" + self.old_parcel_id_edit.text() + "%"

        self.__load_fee(person_id, old_parcel_id)

    def __clear_controls(self):

        # self.grace_period_edit.setText('0')
        # self.payment_frequency_edit.setText('0')
        self.fee_per_year_edit.setText('0')
        self.fee_paid_edit.setText('0')
        self.surplus_from_last_years_edit.setText('0')
        self.fee_to_pay_edit.setText('0')
        # self.potential_fine_edit.setText('0')
        # self.effective_fine_edit.setText('0')
        # self.fine_paid_edit.setText('0')
        # self.fine_to_pay_edit.setText('0')
        # self.payment_twidget.setRowCount(0)
        # self.fine_payment_twidget.setRowCount(0)
        # self.quarter_1_check_box.setChecked(False)
        # self.quarter_2_check_box.setChecked(False)
        # self.quarter_3_check_box.setChecked(False)
        # self.quarter_4_check_box.setChecked(False)

        self.__reset_text_color(self.fee_to_pay_edit)
        # self.__reset_text_color(self.fine_to_pay_edit)

    def __change_text_color(self, line_edit):

        style_sheet = "QLineEdit {color:rgb(255, 0, 0);}"
        line_edit.setStyleSheet(style_sheet)

    def __reset_text_color(self, line_edit):

        line_edit.setStyleSheet(None)