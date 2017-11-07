__author__ = 'mwagner'

from ..view.Ui_LandTaxPaymentsDialog import *
from ..utils.PluginUtils import *
from ..model.BsPerson import *
from ..model.CtTaxAndPrice import *
from ..model.DatabaseHelper import *
from sqlalchemy.sql import func
from ..model.SetPayment import *

PAYMENT_DATE = 0
AMOUNT_PAID = 1
PAYMENT_TYPE = 2


class LandTaxPaymentsDialog(QDialog, Ui_LandTaxPaymentsDialog, DatabaseHelper):

    def __init__(self, record, parent=None):

        super(LandTaxPaymentsDialog,  self).__init__(parent)
        DatabaseHelper.__init__(self)
        self.setupUi(self)
        self.__setup_twidgets()
        self.close_button.clicked.connect(self.reject)
        self.record = record
        self.session = SessionHandler().session_instance()
        self.payment_date_edit.setDate(QDate.currentDate())
        self.amount_paid_sbox.setMinimum(0)
        self.amount_paid_sbox.setMaximum(25000000)
        self.amount_paid_sbox.setSingleStep(1000)
        self.fine_payment_date_edit.setDate(QDate.currentDate())
        self.fine_amount_paid_sbox.setMinimum(0)
        self.fine_amount_paid_sbox.setMaximum(25000000)
        self.fine_amount_paid_sbox.setSingleStep(200)
        self.year_sbox.setMinimum(1950)
        self.year_sbox.setMaximum(2200)
        self.year_sbox.setSingleStep(1)
        self.year_sbox.setValue(QDate.currentDate().year())
        self.status_label.clear()

        self.__load_data()

    def __setup_twidgets(self):

        self.payment_twidget.setAlternatingRowColors(True)
        self.payment_twidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.payment_twidget.setSelectionMode(QTableWidget.SingleSelection)

        self.fine_payment_twidget.setAlternatingRowColors(True)
        self.fine_payment_twidget.setSelectionBehavior(QTableWidget.SelectRows)
        self.fine_payment_twidget.setSelectionMode(QTableWidget.SingleSelection)

    def __load_data(self):

        self.record_number_edit.setText(self.record.record_no)
        begin = PluginUtils.convert_python_date_to_qt(self.record.record_begin)
        self.record_begin_edit.setText(begin.toString(Constants.DATE_FORMAT))
        self.record_status_edit.setText(self.record.status_ref.description)

        self.__populate_payment_type_cboxes()
        self.__populate_owner_cbox()

    def __populate_payment_type_cboxes(self):

        self.__populate_payment_type_cbox(self.payment_type_cbox)
        self.__populate_payment_type_cbox(self.fine_payment_type_cbox)

    def __populate_payment_type_cbox(self, cbox):

        for payment_type in self.session.query(ClPaymentType).order_by(ClPaymentType.code).all():

            cbox.addItem(u"{0}".format(payment_type.description), payment_type.code)

    def __populate_owner_cbox(self):

        for tax in self.record.taxes:

            person_id = tax.person
            for name, first_name in self.session.query(BsPerson.name, BsPerson.first_name)\
                    .filter(BsPerson.person_id == person_id):
                if first_name is None:
                    self.select_owner_cbox.addItem(u"{0}".format(name), person_id)
                else:
                    self.select_owner_cbox.addItem(u"{0}, {1}".format(name, first_name), person_id)

    @pyqtSlot(int)
    def on_select_owner_cbox_currentIndexChanged(self, idx):

        self.__clear_controls()

        if idx == -1:
            return

        person_id = self.select_owner_cbox.itemData(idx, Qt.UserRole)
        self.__load_tax_payments(person_id)
        self.__load_fine_payments(person_id)
        self.__update_payment_summary(person_id)

    def reject(self):

        self.rollback()
        QDialog.reject(self)

    def __load_tax_payments(self, person_id):

        self.payment_twidget.setRowCount(0)
        count = self.record.taxes.filter(CtTaxAndPrice.person == person_id).count()
        if count == 0:
            return

        payment_year = self.year_sbox.value()
        tax = self.record.taxes.filter(CtTaxAndPrice.person == person_id).one()
        count = tax.payments.filter(CtTaxAndPricePayment.year_paid_for == payment_year).count()
        self.payment_twidget.setRowCount(count)
        row = 0

        for payment in tax.payments.filter(CtTaxAndPricePayment.year_paid_for == payment_year).order_by(CtTaxAndPricePayment.date_paid):

            self.__add_payment_row(row, payment, self.payment_twidget)
            row += 1

        if row > 0:
            self.payment_twidget.resizeColumnToContents(PAYMENT_DATE)
            self.payment_twidget.resizeColumnToContents(AMOUNT_PAID)
            self.payment_twidget.horizontalHeader().setResizeMode(PAYMENT_TYPE, QHeaderView.Stretch)

    def __load_fine_payments(self, person_id):

        self.fine_payment_twidget.setRowCount(0)
        count = self.record.taxes.filter(CtTaxAndPrice.person == person_id).count()
        if count == 0:
            return

        payment_year = self.year_sbox.value()
        tax = self.record.taxes.filter(CtTaxAndPrice.person == person_id).one()
        count = tax.fine_payments.filter(CtFineForTaxPayment.year_paid_for == payment_year).count()
        self.fine_payment_twidget.setRowCount(count)
        row = 0

        for payment in tax.fine_payments.filter(CtFineForTaxPayment.year_paid_for == payment_year)\
                .order_by(CtFineForTaxPayment.date_paid):

            self.__add_payment_row(row, payment, self.fine_payment_twidget)
            row += 1

        if row > 0:
            self.fine_payment_twidget.resizeColumnToContents(PAYMENT_DATE)
            self.fine_payment_twidget.resizeColumnToContents(AMOUNT_PAID)
            self.fine_payment_twidget.horizontalHeader().setResizeMode(PAYMENT_TYPE, QHeaderView.Stretch)

    def __add_payment_row(self, row, payment, twidget):

        item = QTableWidgetItem('{0}'.format(PluginUtils.convert_python_date_to_qt(payment.date_paid)
                                             .toString(Constants.DATE_FORMAT)))
        item.setData(Qt.UserRole, payment.id)
        self.__lock_item(item)
        twidget.setItem(row, PAYMENT_DATE, item)

        item = QTableWidgetItem('{0}'.format(payment.amount_paid))
        self.__lock_item(item)
        twidget.setItem(row, AMOUNT_PAID, item)

        item = QTableWidgetItem(u'{0}'.format(payment.payment_type_ref.description))
        item.setData(Qt.UserRole, payment.payment_type_ref.code)
        self.__lock_item(item)
        twidget.setItem(row, PAYMENT_TYPE, item)

    def __lock_item(self, item):

        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    @pyqtSlot()
    def on_register_payment_button_clicked(self):

        # Validate
        person_id = self.select_owner_cbox.itemData(self.select_owner_cbox.currentIndex(), Qt.UserRole)
        count = self.record.taxes.filter(CtTaxAndPrice.person == person_id).count()
        if count == 0:
            PluginUtils.show_message(self, self.tr("Register Payment"),
                                     self.tr("No tax is registered for the selected owner!"))
            return

        if self.record.status != 20:
            PluginUtils.show_message(self, self.tr("Register Payment"),
                                     self.tr("Payments can be registered for active ownership records only!"))
            return

        ownership_begin_year = self.record.record_begin.year

        effective_fine = int(self.effective_fine_edit.text())
        if effective_fine > 0:
            PluginUtils.show_message(self, self.tr("Register Payment"),
                                     self.tr("No more payments can be registered for this payment year!"))
            return

        payment_year = self.year_sbox.value()
        if payment_year < ownership_begin_year:
            PluginUtils.show_message(self, self.tr("Register Payment"),
                                     self.tr("Payments cannot be registered for years outside the ownership period!"))
            return

        tax = self.record.taxes.filter(CtTaxAndPrice.person == person_id).one()
        payment_date = self.payment_date_edit.date()
        amount_paid = self.amount_paid_sbox.value()
        payment_type = self.payment_type_cbox.itemData(self.payment_type_cbox.currentIndex(), Qt.UserRole)

        if amount_paid == 0:
            PluginUtils.show_message(self, self.tr("Register Payment"),
                                     self.tr("The amount paid must be greater than 0!"))
            return

        payment = CtTaxAndPricePayment()
        payment.date_paid = PluginUtils.convert_qt_date_to_python(payment_date)
        payment.amount_paid = amount_paid
        payment.payment_type = payment_type
        payment.paid_total = 0
        payment.year_paid_for = payment_year

        tax.payments.append(payment)
        self.session.flush()
        self.__load_tax_payments(person_id)
        self.__calculate_fines(tax, payment_year)
        self.__update_payment_summary(person_id)

    @pyqtSlot()
    def on_remove_button_clicked(self):

        selected_row = self.payment_twidget.currentRow()
        if selected_row == -1:
            PluginUtils.show_message(self, self.tr("Select Tax"),
                                     self.tr("Please select tax!"))
            return
        date_item = self.payment_twidget.item(selected_row, 0)
        payment_id = date_item.data(Qt.UserRole)
        amount_item = self.payment_twidget.item(selected_row, 1)
        type_item = self.payment_twidget.item(selected_row, 2)
        self.payment_twidget.removeRow(selected_row)

        person_id = self.select_owner_cbox.itemData(self.select_owner_cbox.currentIndex(), Qt.UserRole)
        count = self.record.taxes.filter(CtTaxAndPrice.person == person_id).count()
        if count == 0:
            PluginUtils.show_message(self, self.tr("Register Payment"),
                                     self.tr("No tax is registered for the selected owner!"))
            return

        tax = self.record.taxes.filter(CtTaxAndPrice.person == person_id).one()
        payment_year = self.year_sbox.value()
        payment = self.session.query(CtTaxAndPricePayment).filter(CtTaxAndPricePayment.id == payment_id).one()

        tax.payments.remove(payment)
        self.session.flush()
        self.__load_tax_payments(person_id)
        self.__calculate_fines(tax, payment_year)
        self.__update_payment_summary(person_id)

    @pyqtSlot(QTableWidgetItem)
    def on_payment_twidget_itemClicked(self, item):

        current_row = self.payment_twidget.currentRow()

        date_item = self.payment_twidget.item(current_row, 0)
        payment_id = date_item.data(Qt.UserRole)
        payment = self.session.query(CtTaxAndPricePayment).filter(CtTaxAndPricePayment.id == payment_id).one()
        qt_date = PluginUtils.convert_python_date_to_qt(payment.date_paid)

        amount_item = self.payment_twidget.item(current_row, 1)
        type_item = self.payment_twidget.item(current_row, 2)
        payment_type = type_item.data(Qt.UserRole)

        self.payment_date_edit.setDate(qt_date)
        self.amount_paid_sbox.setValue(int(amount_item.text()))
        self.payment_type_cbox.setCurrentIndex(self.payment_type_cbox.findData(payment_type))

    @pyqtSlot()
    def on_edit_button_clicked(self):

        person_id = self.select_owner_cbox.itemData(self.select_owner_cbox.currentIndex(), Qt.UserRole)
        count = self.record.taxes.filter(CtTaxAndPrice.person == person_id).count()
        if count == 0:
            PluginUtils.show_message(self, self.tr("Register Payment"),
                                     self.tr("No tax is registered for the selected owner!"))
            return

        tax = self.record.taxes.filter(CtTaxAndPrice.person == person_id).one()

        current_row = self.payment_twidget.currentRow()

        date_item = self.payment_twidget.item(current_row, 0)
        if date_item == None:
            PluginUtils.show_message(self, self.tr("Select Payment"),
                                     self.tr("Please select payment!"))
            return
        payment_id = date_item.data(Qt.UserRole)

        payment_date = self.payment_date_edit.date()
        amount_paid = self.amount_paid_sbox.value()
        payment_type = self.payment_type_cbox.itemData(self.payment_type_cbox.currentIndex(), Qt.UserRole)
        payment_year = self.year_sbox.value()

        payment = self.session.query(CtTaxAndPricePayment).filter(CtTaxAndPricePayment.id == payment_id).one()
        payment.date_paid = PluginUtils.convert_qt_date_to_python(payment_date)
        payment.amount_paid = amount_paid
        payment.payment_type = payment_type
        payment.paid_total = 0
        payment.year_paid_for = payment_year

        # fee.payments.extend(payment)
        self.session.flush()

        date_item = self.payment_twidget.item(current_row, 0)
        amount_item = self.payment_twidget.item(current_row, 1)
        type_item = self.payment_twidget.item(current_row, 2)

        date_item.setText(str(self.payment_date_edit.text()))
        date_item.setData(Qt.UserRole,payment_id)
        amount_item.setText(str(self.amount_paid_sbox.value()))
        amount_item.setData(Qt.UserRole, self.amount_paid_sbox.value())
        type_item.setText(self.payment_type_cbox.currentText())
        type_item.setData(Qt.UserRole, payment_type)

        self.__load_tax_payments(person_id)
        self.__calculate_fines(tax, payment_year)
        self.__update_payment_summary(person_id)

    def __calculate_fines(self, tax, payment_year):

        fine_rate = self.session.query(SetPayment.landtax_fine_rate_per_day).first()[0]
        surplus_from_previous_years = self.__surplus_from_previous_years(tax)

        payments = tax.payments.filter(CtTaxAndPricePayment.year_paid_for == payment_year)\
            .order_by(CtTaxAndPricePayment.date_paid)

        paid_total = surplus_from_previous_years

        grace_period = int(self.grace_period_edit.text())

        for payment in payments:

            delay_to_dl1 = QDate(payment_year, 1, 25).addDays(grace_period)\
                .daysTo(QDate(payment.date_paid.year, payment.date_paid.month, payment.date_paid.day))
            if delay_to_dl1 > 0:
                payment.delay_to_dl1 = delay_to_dl1
            else:
                delay_to_dl1 = 0
            delay_to_dl2 = QDate(payment_year, 4, 25).addDays(grace_period)\
                .daysTo(QDate(payment.date_paid.year, payment.date_paid.month, payment.date_paid.day))
            if delay_to_dl2 > 0:
                payment.delay_to_dl2 = delay_to_dl2
            else:
                delay_to_dl2 = 0
            delay_to_dl3 = QDate(payment_year, 7, 25).addDays(grace_period)\
                .daysTo(QDate(payment.date_paid.year, payment.date_paid.month, payment.date_paid.day))
            if delay_to_dl3 > 0:
                payment.delay_to_dl3 = delay_to_dl3
            else:
                delay_to_dl3 = 0
            delay_to_dl4 = QDate(payment_year, 10, 25).addDays(grace_period)\
                .daysTo(QDate(payment.date_paid.year, payment.date_paid.month, payment.date_paid.day))
            if delay_to_dl4 > 0:
                payment.delay_to_dl4 = delay_to_dl4
            else:
                delay_to_dl4 = 0

            left_to_pay = self.__left_to_pay(tax, paid_total)

            fine_for_q1 = delay_to_dl1 * left_to_pay['Q1'] * fine_rate / 100
            fine_for_q2 = delay_to_dl2 * left_to_pay['Q2'] * fine_rate / 100
            fine_for_q3 = delay_to_dl3 * left_to_pay['Q3'] * fine_rate / 100
            fine_for_q4 = delay_to_dl4 * left_to_pay['Q4'] * fine_rate / 100

            if fine_for_q1 > left_to_pay['Q1'] / 2:
                fine_for_q1 = left_to_pay['Q1'] / 2
            if fine_for_q2 > left_to_pay['Q2'] / 2:
                fine_for_q2 = left_to_pay['Q2'] / 2
            if fine_for_q3 > left_to_pay['Q3'] / 2:
                fine_for_q3 = left_to_pay['Q3'] / 2
            if fine_for_q4 > left_to_pay['Q4'] / 2:
                fine_for_q4 = left_to_pay['Q4'] / 2

            payment.fine_for_q1 = fine_for_q1
            payment.fine_for_q2 = fine_for_q2
            payment.fine_for_q3 = fine_for_q3
            payment.fine_for_q4 = fine_for_q4

            payment.paid_total = payment.amount_paid + paid_total
            paid_total += payment.amount_paid

            left_to_pay = self.__left_to_pay(tax, paid_total)

            payment.left_to_pay_for_q1 = left_to_pay['Q1']
            payment.left_to_pay_for_q2 = left_to_pay['Q2']
            payment.left_to_pay_for_q3 = left_to_pay['Q3']
            payment.left_to_pay_for_q4 = left_to_pay['Q4']

        self.session.flush()

    def __left_to_pay(self, tax, paid_total):

        payment_year = self.year_sbox.value()

        tax_to_pay_for_q1 = self.__tax_to_pay_per_period(tax, date(payment_year, 1, 1), date(payment_year, 4, 1))
        tax_to_pay_for_q2 = self.__tax_to_pay_per_period(tax, date(payment_year, 4, 1), date(payment_year, 7, 1))
        tax_to_pay_for_q3 = self.__tax_to_pay_per_period(tax, date(payment_year, 7, 1), date(payment_year, 10, 1))
        tax_to_pay_for_q4 = self.__tax_to_pay_per_period(tax, date(payment_year, 10, 1), date(payment_year+1, 1, 1))

        left_to_pay_for_q1 = tax_to_pay_for_q1 - paid_total
        if left_to_pay_for_q1 < 0:
            left_to_pay_for_q1 = 0
        surplus = paid_total - tax_to_pay_for_q1
        if surplus < 0:
            surplus = 0
        left_to_pay_for_q2 = tax_to_pay_for_q2 - surplus
        if left_to_pay_for_q2 < 0:
            left_to_pay_for_q2 = 0
        surplus = paid_total - (tax_to_pay_for_q1 + tax_to_pay_for_q2)
        if surplus < 0:
            surplus = 0
        left_to_pay_for_q3 = tax_to_pay_for_q3 - surplus
        if left_to_pay_for_q3 < 0:
            left_to_pay_for_q3 = 0
        surplus = paid_total - (tax_to_pay_for_q1 + tax_to_pay_for_q2 + tax_to_pay_for_q3)
        if surplus < 0:
            surplus = 0
        left_to_pay_for_q4 = tax_to_pay_for_q4 - surplus
        if left_to_pay_for_q4 < 0:
            left_to_pay_for_q4 = 0

        left_to_pay = dict()
        left_to_pay['Q1'] = left_to_pay_for_q1
        left_to_pay['Q2'] = left_to_pay_for_q2
        left_to_pay['Q3'] = left_to_pay_for_q3
        left_to_pay['Q4'] = left_to_pay_for_q4

        return left_to_pay

    @pyqtSlot()
    def on_fine_register_payment_button_clicked(self):

        # Validate
        person_id = self.select_owner_cbox.itemData(self.select_owner_cbox.currentIndex(), Qt.UserRole)
        count = self.record.taxes.filter(CtTaxAndPrice.person == person_id).count()
        if count == 0:
            PluginUtils.show_message(self, self.tr("Register Fine Payment"),
                                     self.tr("No tax is registered for the selected owner!"))
            return

        if self.record.status != 20:
            PluginUtils.show_message(self, self.tr("Register Fine Payment"),
                                     self.tr("Payments can be registered for active ownership records only!"))
            return

        record_begin_year = self.record.record_begin.year

        payment_year = self.year_sbox.value()
        if payment_year < record_begin_year:
            PluginUtils.show_message(self, self.tr("Register Fine Payment"),
                                     self.tr("Payments cannot be registered for years outside the ownership period!"))
            return

        effective_fine = int(self.effective_fine_edit.text())
        if effective_fine == 0:
            PluginUtils.show_message(self, self.tr("Register Fine Payment"),
                                     self.tr("A fine payment cannot be registered without an effective fine!"))
            return

        tax = self.record.taxes.filter(CtTaxAndPrice.person == person_id).one()
        payment_date = self.fine_payment_date_edit.date()
        amount_paid = self.fine_amount_paid_sbox.value()
        payment_type = self.fine_payment_type_cbox.itemData(self.payment_type_cbox.currentIndex(), Qt.UserRole)

        if amount_paid == 0:
            PluginUtils.show_message(self, self.tr("Register Fine Payment"),
                                     self.tr("The amount paid must be greater than 0!"))
            return

        payment = CtFineForTaxPayment()
        payment.date_paid = PluginUtils.convert_qt_date_to_python(payment_date)
        payment.amount_paid = amount_paid
        payment.payment_type = payment_type
        payment.year_paid_for = payment_year

        tax.fine_payments.append(payment)
        self.session.flush()
        self.__load_fine_payments(person_id)
        self.__update_payment_summary(person_id)

    def __update_payment_summary(self, person_id):

        count = self.record.taxes.filter(CtTaxAndPrice.person == person_id).count()
        if count == 0:
            return

        tax = self.record.taxes.filter(CtTaxAndPrice.person == person_id).one()
        self.grace_period_edit.setText(str(tax.grace_period))
        self.payment_frequency_edit.setText(tax.payment_frequency_ref.description)

        self.__set_tax_summary(tax)
        self.__set_fine_summary(tax)
        self.__update_payment_status(tax)

    def __tax_to_pay_per_period(self, tax, period_begin, period_end):

        # Intersect record duration with payment period
        sql = "select lower(daterange(record_begin, 'infinity', '[)') * daterange(:from, :to, '[)'))," \
              " upper(daterange(record_begin, 'infinity', '[)') * daterange(:from, :to, '[)')) " \
              "from ct_ownership_record where record_no = :record_no"

        result = self.session.execute(sql, {'from': period_begin,
                                            'to': period_end,
                                            'record_no': tax.record})
        for row in result:
            effective_begin = row[0]
            effective_end = row[1]

        if effective_begin is None and effective_end is None:
            return 0

        # Intersect the effective payment period with the archived taxes
        sql = "select upper(daterange(valid_from, valid_till, '[)') * daterange(:begin, :end, '[)')) - "\
                 "lower(daterange(valid_from, valid_till, '[)') * daterange(:begin, :end, '[)')) as days, "\
                 "land_tax from ct_archived_tax_and_price where record = :record and person = :person"

        result = self.session.execute(sql, {'begin': effective_begin,
                                            'end': effective_end,
                                            'record': tax.record,
                                            'person': tax.person})
        tax_for_period = 0
        total_days = 0

        for row in result:
            days = row[0]

            if days is None:
                continue
            annual_tax = row[1]
            adjusted_tax = (annual_tax / 365) * days
            tax_for_period += adjusted_tax
            total_days += days

        effective_days = (effective_end-effective_begin).days

        if effective_days - total_days > 0:
            tax_for_period += (effective_days-total_days) * tax.land_tax / 365

        return int(round(tax_for_period))

    def __set_tax_summary(self, tax):

        payment_year = self.year_sbox.value()

        tax_to_pay_for_current_year = \
            self.__tax_to_pay_per_period(tax, date(payment_year, 1, 1), date(payment_year+1, 1, 1))

        paid_for_current_year = self.session.query(func.sum(CtTaxAndPricePayment.amount_paid))\
            .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
            .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()

        if paid_for_current_year is None:
            paid_for_current_year = 0

        surplus = self.__surplus_from_previous_years(tax)

        tax_left_to_pay = tax_to_pay_for_current_year - (paid_for_current_year + surplus)
        if tax_left_to_pay < 0:
            tax_left_to_pay = 0

        # set for display
        self.tax_per_year_edit.setText(str(tax_to_pay_for_current_year))
        self.tax_paid_edit.setText(str(paid_for_current_year))
        self.surplus_from_last_years_edit.setText(str(surplus))
        self.tax_to_pay_edit.setText(str(tax_left_to_pay))
        if tax_left_to_pay > 0:
            self.__change_text_color(self.tax_to_pay_edit)
        else:
            self.__reset_text_color(self.tax_to_pay_edit)

    def __set_fine_summary(self, tax):

        payment_year = self.year_sbox.value()

        effective_fine_for_current_year = self.__effective_fine_for_year(tax, payment_year)
        potential_fine_for_current_year = self.__potential_fine_for_year(tax, payment_year)

        paid_for_current_year = self.session.query(func.sum(CtFineForTaxPayment.amount_paid))\
            .filter(CtFineForTaxPayment.record == tax.record).filter(CtFineForTaxPayment.person == tax.person)\
            .filter(CtFineForTaxPayment.year_paid_for == payment_year).scalar()

        if paid_for_current_year is None:
            paid_for_current_year = 0

        self.effective_fine_edit.setText(str(effective_fine_for_current_year))
        self.potential_fine_edit.setText(str(potential_fine_for_current_year))
        self.fine_paid_edit.setText(str(paid_for_current_year))
        fine_to_pay = effective_fine_for_current_year - paid_for_current_year
        if fine_to_pay < 0:
            fine_to_pay = 0
        self.fine_to_pay_edit.setText(str(fine_to_pay))
        if fine_to_pay > 0:
            self.__change_text_color(self.fine_to_pay_edit)
        else:
            self.__reset_text_color(self.fine_to_pay_edit)

    def __effective_fine_for_year(self, tax, payment_year):

        return self.__total_fine(tax, payment_year)

    def __potential_fine_for_year(self, tax, payment_year):

        return self.__total_fine(tax, payment_year, False)

    def __total_fine(self, tax, payment_year, effective_fine=True):

        count = self.session.query(CtTaxAndPricePayment)\
            .filter(CtTaxAndPricePayment.record == tax.record)\
            .filter(CtTaxAndPricePayment.person == tax.person)\
            .filter(CtTaxAndPricePayment.year_paid_for == payment_year)\
            .filter(CtTaxAndPricePayment.left_to_pay_for_q1 == 0)\
            .filter(CtTaxAndPricePayment.left_to_pay_for_q2 == 0)\
            .filter(CtTaxAndPricePayment.left_to_pay_for_q3 == 0)\
            .filter(CtTaxAndPricePayment.left_to_pay_for_q4 == 0).count()

        if effective_fine:
            if count == 0:
                return 0
        else:
            if count != 0:
                return 0

        payment_frequency = tax.payment_frequency
        total_fine = 0
        fine = self.session.query(func.sum(CtTaxAndPricePayment.fine_for_q1))\
            .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
            .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()
        if fine is not None and payment_frequency == 20:
            total_fine += fine
        fine = self.session.query(func.sum(CtTaxAndPricePayment.fine_for_q2))\
            .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
            .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()
        if fine is not None and payment_frequency == 20:
            total_fine += fine
        fine = self.session.query(func.sum(CtTaxAndPricePayment.fine_for_q3))\
            .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
            .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()
        if fine is not None and payment_frequency == 20:
            total_fine += fine
        fine = self.session.query(func.sum(CtTaxAndPricePayment.fine_for_q4))\
            .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
            .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()
        if fine is not None:
            total_fine += fine

        return int(round(total_fine))

    def __surplus_from_previous_years(self, tax):

        year_to_pay_for = self.year_sbox.value()

        surplus_last_year = 0

        for payment_year in range(self.record.record_begin.year, year_to_pay_for):

            amount_paid = self.session.query(func.sum(CtTaxAndPricePayment.amount_paid))\
                .filter(CtTaxAndPricePayment.record == tax.record).filter(CtTaxAndPricePayment.person == tax.person)\
                .filter(CtTaxAndPricePayment.year_paid_for == payment_year).scalar()
            if amount_paid is None:
                amount_paid = 0

            tax_to_pay = self.__tax_to_pay_per_period(tax, date(payment_year, 1, 1), date(payment_year+1, 1, 1))
            if (amount_paid + surplus_last_year) - tax_to_pay > 0:
                surplus_last_year = (amount_paid + surplus_last_year) - tax_to_pay
            else:
                surplus_last_year = 0

        return surplus_last_year

    @pyqtSlot()
    def on_apply_button_clicked(self):

        self.commit()
        self.__start_fade_out_timer()

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

    @pyqtSlot(int)
    def on_year_sbox_valueChanged(self, sbox_value):

        self.__clear_controls()
        person_id = self.select_owner_cbox.itemData(self.select_owner_cbox.currentIndex(), Qt.UserRole)

        count = self.record.taxes.filter(CtTaxAndPrice.person == person_id).count()
        if count == 0:
            return

        self.__load_tax_payments(person_id)
        self.__load_fine_payments(person_id)
        self.__update_payment_summary(person_id)

    def __update_payment_status(self, tax):

        amount_paid = int(self.tax_paid_edit.text()) + int(self.surplus_from_last_years_edit.text())

        payment_year = self.year_sbox.value()

        tax_to_pay_for_q1 = self.__tax_to_pay_per_period(tax, date(payment_year, 1, 1), date(payment_year, 4, 1))
        tax_to_pay_for_q2 = self.__tax_to_pay_per_period(tax, date(payment_year, 4, 1), date(payment_year, 7, 1))
        tax_to_pay_for_q3 = self.__tax_to_pay_per_period(tax, date(payment_year, 7, 1), date(payment_year, 10, 1))
        tax_to_pay_for_q4 = self.__tax_to_pay_per_period(tax, date(payment_year, 10, 1), date(payment_year+1, 1, 1))

        if 0 < tax_to_pay_for_q1 <= amount_paid:
            self.quarter_1_check_box.setChecked(True)

        if tax_to_pay_for_q2 > 0 and amount_paid >= tax_to_pay_for_q1+tax_to_pay_for_q2:
            self.quarter_2_check_box.setChecked(True)

        if tax_to_pay_for_q3 > 0 and amount_paid >= tax_to_pay_for_q1+tax_to_pay_for_q2+tax_to_pay_for_q3:
            self.quarter_3_check_box.setChecked(True)

        if tax_to_pay_for_q4 > 0 and \
                amount_paid >= tax_to_pay_for_q1+tax_to_pay_for_q2+tax_to_pay_for_q3+tax_to_pay_for_q4:
            self.quarter_4_check_box.setChecked(True)

    def __clear_controls(self):

        self.grace_period_edit.setText('0')
        self.payment_frequency_edit.setText('0')
        self.tax_per_year_edit.setText('0')
        self.tax_paid_edit.setText('0')
        self.surplus_from_last_years_edit.setText('0')
        self.tax_to_pay_edit.setText('0')
        self.potential_fine_edit.setText('0')
        self.effective_fine_edit.setText('0')
        self.fine_paid_edit.setText('0')
        self.fine_to_pay_edit.setText('0')
        self.payment_twidget.setRowCount(0)
        self.fine_payment_twidget.setRowCount(0)
        self.quarter_1_check_box.setChecked(False)
        self.quarter_2_check_box.setChecked(False)
        self.quarter_3_check_box.setChecked(False)
        self.quarter_4_check_box.setChecked(False)

        self.__reset_text_color(self.tax_to_pay_edit)
        self.__reset_text_color(self.fine_to_pay_edit)

    def __change_text_color(self, line_edit):

        style_sheet = "QLineEdit {color:rgb(255, 0, 0);}"
        line_edit.setStyleSheet(style_sheet)

    def __reset_text_color(self, line_edit):

        line_edit.setStyleSheet(None)

    @pyqtSlot()
    def on_help_button_clicked(self):

        if self.tabWidget.currentIndex() == 0:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/summary1.htm")
        elif self.tabWidget.currentIndex() == 1:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/taxes1.htm")
        elif self.tabWidget.currentIndex() == 2:
                os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/fines1.htm")
