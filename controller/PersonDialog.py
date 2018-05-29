import os

__author__ = 'anna'
# -*- encoding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_, extract
from datetime import date, datetime, timedelta
from ..view.Ui_PersonDialog import *
from ..model.BsPerson import *
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.AuLevel3 import *
from ..model.ClBank import *
from ..model.AuKhoroolol import *
from ..model.ClGender import *
from ..model.ClPersonType import *
from ..model.ClCountryList import *
from ..model import Constants
from ..model.Enumerations import PersonType, UserRight
from ..model import SettingsConstants
from ..model.DatabaseHelper import *
from ..model.LM2Exception import LM2Exception
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.SessionHandler import SessionHandler
from ..utils.PluginUtils import PluginUtils


class PersonDialog(QDialog, Ui_PersonDialog, DatabaseHelper):
    def __init__(self, person, parent=None):

        super(PersonDialog, self).__init__(parent)
        DatabaseHelper.__init__(self)

        self.setupUi(self)
        self.time_counter = None
        self.person = person
        self.setWindowTitle(self.tr("Person Dialog"))
        self.session = SessionHandler().session_instance()
        self.is_age_18 = None

        self.__setup_validators()
        self.__setup_combo_boxes()
        self.__setup_mapping()
        self.__setup_permissions()

    def __setup_validators(self):

        self.capital_asci_letter_validator = QRegExpValidator(QRegExp("[A-Z]"), None)
        self.lower_case_asci_letter_validator = QRegExpValidator(QRegExp("[a-z]"), None)

        self.email_validator = QRegExpValidator(QRegExp("[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,4}"), None)

        self.www_validator = QRegExpValidator(QRegExp("www\\.[a-z0-9._%+-]+\\.[a-z]{2,4}"), None)

        self.numbers_validator = QRegExpValidator(QRegExp("[1-9][0-9]+( *,*[1-9][0-9]+)*"), None)
        self.mobile_phone_edit.setValidator(self.numbers_validator)
        self.phone_edit.setValidator(self.numbers_validator)
        self.account_edit.setValidator(self.numbers_validator)

        self.int_validator = QRegExpValidator(QRegExp("[0-9]+"), None)
        self.state_register_edit.setValidator(self.int_validator)

    def __setup_combo_boxes(self):

        aimag_list = []
        khoroolol_list = []
        bank_list = []
        persontype_list = []
        town_list = []
        khaskhaa_list = []
        street_list = []

        try:
            aimag_list = self.session.query(AuLevel1.name, AuLevel1.code).\
                filter(AuLevel1.code != '013').filter(AuLevel1.code != '012').order_by(AuLevel1.name.desc()).all()
            khoroolol_list = self.session.query(AuKhoroolol.fid, AuKhoroolol.name).order_by(
                AuKhoroolol.name.desc()).all()
            bank_list = self.session.query(ClBank).all()
            persontype_list = self.session.query(ClPersonType).all()
            country_list = self.session.query(ClCountryList).all()
            # street_list = self.session.query(BsPerson.address_street_name).order_by(
            #     BsPerson.address_street_name.desc()).all()
            # town_list = self.session.query(BsPerson.address_town_or_local_name).order_by(
            #     BsPerson.address_town_or_local_name.desc()).all()
            # khaskhaa_list = self.session.query(BsPerson.address_khaskhaa).order_by(
            #     BsPerson.address_khaskhaa.desc()).all()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
            self.reject()
        #
        # self.aimag_cbox.addItem("*", -1)
        # self.khoroolol_cbox.addItem("*", -1)
        # self.bank_cbox.addItem("*", -1)
        #
        for auLevel1 in aimag_list:
            self.aimag_cbox.addItem(auLevel1.name, auLevel1.code)
        #
        for bank in bank_list:
            self.bank_cbox.addItem(bank.description, bank.code)
        #
        for khoroolol in khoroolol_list:
            self.khoroolol_cbox.addItem(khoroolol.name, khoroolol.fid)
        #
        for personType in persontype_list:
            self.person_type_cbox.addItem(personType.description, personType.code)
        person_type = self.person_type_cbox.itemData(self.person_type_cbox.currentIndex())
        for countryList in country_list:
            if person_type == 50 or person_type == 60:
                if countryList.code != 1:
                    self.country_cbox.addItem(countryList.description, countryList.code)
            else:
                self.country_cbox.addItem(countryList.description, countryList.code)
        #
        self.person_type_cbox.setCurrentIndex(0)
        working_aimag = DatabaseUtils.working_l1_code()
        working_soum = DatabaseUtils.working_l2_code()
        self.aimag_cbox.setCurrentIndex(self.aimag_cbox.findData(working_aimag))
        self.soum_cbox.setCurrentIndex(self.soum_cbox.findData(working_soum))
        #
        # khaskhaa_slist = []
        # town_slist = []
        # street_slist = []
        #
        # for street in street_list:
        #     if street[0]:
        #         street_slist.append(street[0])
        #
        # for town in town_list:
        #     if town[0]:
        #         town_slist.append(town[0])
        #
        # for khaskhaa in khaskhaa_list:
        #     if khaskhaa[0]:
        #         khaskhaa_slist.append(khaskhaa[0])
        #
        # street_model = QStringListModel(street_slist)
        # self.streetProxyModel = QSortFilterProxyModel()
        # self.streetProxyModel.setSourceModel(street_model)
        # self.streetCompleter = QCompleter(self.streetProxyModel, self, activated=self.on_street_completer_activated)
        # self.streetCompleter.setCompletionMode(QCompleter.PopupCompletion)
        # self.street_name_edit.setCompleter(self.streetCompleter)
        #
        # town_model = QStringListModel(town_slist)
        # self.townProxyModel = QSortFilterProxyModel()
        # self.townProxyModel.setSourceModel(town_model)
        # self.townCompleter = QCompleter(self.townProxyModel, self, activated=self.on_town_completer_activated)
        # self.townCompleter.setCompletionMode(QCompleter.PopupCompletion)
        # self.town_edit.setCompleter(self.townCompleter)
        #
        # khaskhaa_model = QStringListModel(khaskhaa_slist)
        # self.khaskhaa_proxy_model = QSortFilterProxyModel()
        # self.khaskhaa_proxy_model.setSourceModel(khaskhaa_model)
        # self.khaskhaaCompleter = QCompleter(self.khaskhaa_proxy_model, self,
        #                                     activated=self.on_khaskhaa_completer_activated)
        # self.khaskhaaCompleter.setCompletionMode(QCompleter.PopupCompletion)
        # self.khashaa_edit.setCompleter(self.khaskhaaCompleter)
        #
        # self.street_name_edit.textEdited.connect(self.streetProxyModel.setFilterFixedString)
        # self.town_edit.textEdited.connect(self.townProxyModel.setFilterFixedString)
        # self.khashaa_edit.textEdited.connect(self.khaskhaa_proxy_model.setFilterFixedString)

    def __setup_permissions(self):

        user_name = QSettings().value(SettingsConstants.USER)
        user_rights = DatabaseUtils.userright_by_name(user_name)

        if UserRight.application_update in user_rights:
            self.apply_button.setEnabled(True)
        else:
            self.apply_button.setEnabled(False)

    def __fade_status_message(self):

        opacity = int(self.time_counter * 0.5)
        self.status_label.setStyleSheet("QLabel {color: rgba(255,0,0," + str(opacity) + ");}")
        self.status_label.setText(self.tr('Changes applied successfully.'))
        if self.time_counter == 0:
            self.timer.stop()
        self.time_counter -= 1

    def __start_fade_out_timer(self):

        self.error_label.setVisible(False)
        self.status_label.setVisible(True)
        self.timer = QTimer()
        self.timer.timeout.connect(self.__fade_status_message)
        self.time_counter = 500
        self.timer.start(10)

    @pyqtSlot(str)
    def on_surname_company_edit_textChanged(self, text):

        self.surname_company_edit.setStyleSheet(self.styleSheet())
        person_type = self.person_type_cbox.itemData(self.person_type_cbox.currentIndex())

        # type of Company/state organisation:
        if person_type == PersonType.mongolian_state_org \
                or person_type == PersonType.mongolian_buisness \
                or person_type == PersonType.legal_entity_foreign \
                or person_type == PersonType.foreign_citizen:
            new_text = self.__auto_correct_company_name(text)

            if new_text != text:
                self.surname_company_edit.setText(new_text)
                return

            if not self.__validate_company_name(text):
                self.surname_company_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

        # type of private person
        else:

            new_text = self.__auto_correct_person_name(text)
            if new_text != text:
                self.surname_company_edit.setText(new_text)
                return

            if not self.__validate_person_name(new_text):
                self.surname_company_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    @pyqtSlot(str)
    def on_town_edit_textChanged(self, text):

        cap_value = self.__capitalize_first_letter(text)
        self.town_edit.setText(cap_value)

    @pyqtSlot(str)
    def on_contact_first_name_edit_textChanged(self, text):

        self.contact_first_name_edit.setStyleSheet(self.styleSheet())

        new_text = self.__auto_correct_person_name(text)
        if new_text != text:
            self.contact_first_name_edit.setText(new_text)
            return

        if not self.__validate_person_name(new_text):
            self.contact_first_name_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    @pyqtSlot(str)
    def on_contact_surname_edit_textChanged(self, text):

        self.contact_surname_edit.setStyleSheet(self.styleSheet())

        new_text = self.__auto_correct_person_name(text)
        if new_text != text:
            self.contact_surname_edit.setText(new_text)
            return

        if not self.__validate_person_name(new_text):
            self.contact_surname_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    @pyqtSlot(str)
    def on_first_name_edit_textChanged(self, text):

        self.first_name_edit.setStyleSheet(self.styleSheet())
        person_type = self.person_type_cbox.itemData(self.person_type_cbox.currentIndex())

        # type of Company/state organisation:
        if person_type == PersonType.mongolian_state_org \
                or person_type == PersonType.mongolian_buisness \
                or person_type == PersonType.legal_entity_foreign \
                or person_type == PersonType.foreign_citizen:
            new_text = self.__auto_correct_company_name(text)

            if new_text != text:
                self.first_name_edit.setText(new_text)
                return

            if not self.__validate_company_name(text):
                self.first_name_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

        # type of private person
        else:

            new_text = self.__auto_correct_person_name(text)
            if new_text != text:
                self.first_name_edit.setText(new_text)
                return

            if not self.__validate_person_name(new_text):
                self.first_name_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    @pyqtSlot(str)
    def on_middle_name_edit_textChanged(self, text):

        self.middle_name_edit.setStyleSheet(self.styleSheet())
        person_type = self.person_type_cbox.itemData(self.person_type_cbox.currentIndex())

        # type of Company/state organisation:
        if person_type == PersonType.mongolian_state_org \
                or person_type == PersonType.mongolian_buisness \
                or person_type == PersonType.legal_entity_foreign \
                or person_type == PersonType.foreign_citizen:
            new_text = self.__auto_correct_company_name(text)

            if new_text != text:
                self.middle_name_edit.setText(new_text)
                return

            if not self.__validate_company_name(text):
                self.middle_name_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

        # type of private person
        else:

            new_text = self.__auto_correct_person_name(text)
            if new_text != text:
                self.middle_name_edit.setText(new_text)
                return

            if not self.__validate_person_name(new_text):
                self.middle_name_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    @pyqtSlot(str)
    def on_khashaa_edit_textChanged(self, text):

        self.khashaa_edit.setStyleSheet(self.styleSheet())
        if not self.__validate_apartment_number(text, self.tr("Khashaa")):
            self.khashaa_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    @pyqtSlot(str)
    def on_contact_position_edit_textChanged(self, text):

        cap_value = self.__capitalize_first_letter(text)
        self.contact_position_edit.setText(cap_value)

    @pyqtSlot(str)
    def on_street_name_edit_textChanged(self, text):

        self.street_name_edit.setStyleSheet(self.styleSheet())
        cap_value = self.__capitalize_first_letter(text)
        self.street_name_edit.setText(cap_value)
        if not self.__validate_street_name(cap_value):
            self.street_name_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    @pyqtSlot(int)
    def on_aimag_cbox_currentIndexChanged(self, index):

        aimag = self.aimag_cbox.itemData(index)
        self.soum_cbox.clear()
        self.bag_cbox.clear()

        self.soum_cbox.addItem("*", -1)
        self.bag_cbox.addItem("*", -1)

        soum_list = []
        bag_list = []

        if aimag == -1:
            soum_list = self.session.query(AuLevel2).all()
            for au_level2 in soum_list:
                if au_level2.code[:2] == '01':
                    self.soum_cbox.addItem(au_level2.name, au_level2.code)

        else:
            try:

                soum_list = self.session.query(AuLevel2.name, AuLevel2.code).filter(
                    AuLevel2.code.like(aimag + "%")).all()
                bag_list = self.session.query(AuLevel3.name, AuLevel3.code).filter(
                    AuLevel3.code.like(aimag + "%")).all()

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
                self.reject()

            for au_level2 in soum_list:
                self.soum_cbox.addItem(au_level2.name, au_level2.code)

            for au_level3 in bag_list:
                self.bag_cbox.addItem(au_level3.name, au_level3.code)

    @pyqtSlot(int)
    def on_soum_cbox_currentIndexChanged(self, index):

        soum = self.soum_cbox.itemData(index)

        self.bag_cbox.clear()
        self.bag_cbox.addItem("*", -1)
        bag_list = []

        if soum == -1 or not soum:
            return
        else:
            try:
                bag_list = self.session.query(AuLevel3.code, AuLevel3.name).filter(AuLevel3.code.like(soum + "%")).all()
            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
                self.reject()

        for au_level3 in bag_list:
            self.bag_cbox.addItem(au_level3.name, au_level3.code)

    @pyqtSlot(int)
    def on_person_type_cbox_currentIndexChanged(self, current_index):

        self.country_cbox.clear()
        person_type = self.person_type_cbox.itemData(current_index)

        if person_type == 50 or person_type == 60:
            self.country_cbox.setEnabled(True)
            self.country_cbox.removeItem(self.country_cbox.findData(1))
            country_list = self.session.query(ClCountryList).filter(ClCountryList.code != 1).all()
            for countryList in country_list:
                self.country_cbox.addItem(countryList.description, countryList.code)
        else:
            self.country_cbox.setEnabled(False)
            if self.country_cbox.setCurrentIndex(self.country_cbox.findData(1)) == None:
                country_list = self.session.query(ClCountryList).filter(ClCountryList.code == 1).all()
                for countryList in country_list:
                    self.country_cbox.addItem(countryList.description, countryList.code)
            self.country_cbox.setCurrentIndex(self.country_cbox.findData(1))

        company_list = Constants.COMPANY_TYPES
        # self.__clear(False)

        if self.person_type_cbox.itemData(current_index) in company_list:
            self.contact_person_group_box.setEnabled(True)
            self.first_name_edit.setEnabled(False)
            self.middle_name_edit.setEnabled(False)
            self.male_rbutton.setEnabled(False)
            self.female_rbutton.setEnabled(False)
            self.state_register_edit.setEnabled(True)
            self.date_of_birth_date.setEnabled(False)
        else:
            self.contact_person_group_box.setEnabled(False)
            self.first_name_edit.setEnabled(True)
            self.middle_name_edit.setEnabled(True)
            self.male_rbutton.setEnabled(True)
            self.female_rbutton.setEnabled(True)
            self.date_of_birth_date.setEnabled(True)
            self.state_register_edit.setEnabled(False)

    @pyqtSlot(str)
    def on_street_completer_activated(self, text):

        if not text:
            return
        self.streetCompleter.activated[str].emit(text)

    @pyqtSlot(str)
    def on_state_register_edit_textChanged(self, text):

        self.state_register_edit.setStyleSheet(self.styleSheet())
        if not self.__validate_state_reg_number(text):
            self.state_register_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    @pyqtSlot(str)
    def on_town_completer_activated(self, text):

        if not text:
            return
        self.townCompleter.activated[str].emit(text)

    @pyqtSlot(str)
    def on_khaskhaa_completer_activated(self, text):

        if not text:
            return
        self.khaskhaaCompleter.activated[str].emit(text)

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

    def __setup_mapping(self):

        if self.person.address_entrance_no is None:
            self.entrance_edit.setText(Constants.ENTRANCE_DEFAULT_VALUE)
        else:
            self.entrance_edit.setText(self.person.address_entrance_no)

        if self.person.type:
            self.person_type_cbox.setCurrentIndex(self.person_type_cbox.findData(self.person.type))

        if self.person.country:
            self.country_cbox.setCurrentIndex(self.country_cbox.findData(self.person.country))

        if self.person.gender_ref:
            if self.person.gender_ref.code == 1:
                self.female_rbutton.setChecked(True)
            else:
                self.male_rbutton.setChecked(True)

        self.first_name_edit.setText(self.person.first_name)
        self.middle_name_edit.setText(self.person.middle_name)
        self.surname_company_edit.setText(self.person.name)
        self.contact_surname_edit.setText(self.person.contact_surname)
        self.contact_first_name_edit.setText(self.person.contact_first_name)
        self.contact_position_edit.setText(self.person.contact_position)
        self.personal_id_edit.setText(self.person.person_id)
        self.state_register_edit.setText(self.person.state_registration_no)
        self.account_edit.setText(self.person.bank_account_no)
        self.phone_edit.setText(self.person.phone)
        self.mobile_phone_edit.setText(self.person.mobile_phone)
        self.email_edit.setText(self.person.email_address)
        self.website_edit.setText(self.person.website)
        self.building_edit.setText(self.person.address_building_no)
        self.apartment_edit.setText(self.person.address_apartment_no)

        if self.person.date_of_birth:
            self.date_of_birth_date.setDate(self.person.date_of_birth)
        if self.person.bank_ref:
            self.bank_cbox.setCurrentIndex(self.bank_cbox.findData(self.person.bank_ref.code))
        if self.person.au_level1_ref:
            self.aimag_cbox.setCurrentIndex(self.aimag_cbox.findData(self.person.au_level1_ref.code))
        if self.person.au_level2_ref:
            self.soum_cbox.setCurrentIndex(self.soum_cbox.findData(self.person.au_level2_ref.code))
        if self.person.au_level3_ref:
            self.bag_cbox.setCurrentIndex(self.bag_cbox.findData(self.person.au_level3_ref.code))
        if self.person.address_town_or_local_name:
            self.town_edit.setText(self.person.address_town_or_local_name)
        if self.person.address_au_khoroolol_ref:
            self.khoroolol_cbox.setCurrentIndex(self.khoroolol_cbox.findData(self.person.address_au_khoroolol_ref.fid))
        if self.person.address_street_name:
            self.street_name_edit.setText(self.person.address_street_name)
        if self.person.address_khaskhaa:
            self.khashaa_edit.setText(self.person.address_khaskhaa)

    @pyqtSlot()
    def on_apply_button_clicked(self):

        self.__save_person()

    def __save_person(self):

        if not self.__validate():
            self.error_label.setVisible(True)
            self.status_label.setVisible(False)
            return False

        self.create_savepoint()

        try:
            person_type = self.person_type_cbox.itemData(self.person_type_cbox.currentIndex())

            if person_type == -1:
                self.person.type_ref = None
            else:
                type_ref = DatabaseUtils.class_instance_by_code(ClPersonType, person_type)
                self.person.type_ref = type_ref

            if self.female_rbutton.isChecked():
                gender = DatabaseUtils.class_instance_by_code(ClGender, 1)
                self.person.gender_ref = gender
            else:
                gender = DatabaseUtils.class_instance_by_code(ClGender, 2)
                self.person.gender_ref = gender

            if person_type == PersonType.mongolian_buisness \
                    or person_type == PersonType.mongolian_state_org \
                    or person_type == PersonType.legal_entity_foreign:

                self.person.name = self.surname_company_edit.text()
                self.person.contact_surname = self.contact_surname_edit.text()
                self.person.contact_first_name = self.contact_first_name_edit.text()
                self.person.contact_position = self.contact_position_edit.text()
            else:
                self.person.name = self.surname_company_edit.text()
                self.person.first_name = self.first_name_edit.text()
                self.person.middle_name = self.middle_name_edit.text()
                self.person.date_of_birth = DatabaseUtils.convert_date(self.date_of_birth_date.date())

            self.person.person_id = self.personal_id_edit.text()
            self.person.state_registration_no = self.state_register_edit.text()
            self.person.address_building_no = self.building_edit.text()
            self.person.address_entrance_no = self.entrance_edit.text()
            self.person.address_apartment_no = self.apartment_edit.text()

            bank_id = self.bank_cbox.itemData(self.bank_cbox.currentIndex())
            if bank_id == -1:
                self.person.bank_ref = None
            else:
                bank = DatabaseUtils.class_instance_by_code(ClBank, bank_id)
                self.person.bank_ref = bank

            country_id = self.country_cbox.itemData(self.country_cbox.currentIndex())
            if country_id == -1:
                self.person.country_ref = None
            else:
                country = DatabaseUtils.class_instance_by_code(ClCountryList, country_id)
                self.person.country_ref = country

            self.person.bank_account_no = self.account_edit.text()
            self.person.phone = self.phone_edit.text()
            self.person.mobile_phone = self.mobile_phone_edit.text()
            self.person.email_address = self.email_edit.text()
            self.person.website = self.website_edit.text()
            self.person.address_street_name = self.street_name_edit.text()
            self.person.address_town_or_local_name = self.town_edit.text()
            self.person.address_khaskhaa = self.khashaa_edit.text()

            aimag = self.aimag_cbox.itemData(self.aimag_cbox.currentIndex())
            if aimag == -1:
                self.person.au_level1_ref = None
            else:
                self.person.address_au_level1 = aimag

            soum = self.soum_cbox.itemData(self.soum_cbox.currentIndex())
            if soum == -1:
                self.person.address_au_level2 = None
            else:
                self.person.address_au_level2 = soum

            bag = self.bag_cbox.itemData(self.bag_cbox.currentIndex())
            if bag == -1:
                self.person.address_au_level3 = None
            else:
                self.person.address_au_level3 = bag

            self.session.add(self.person)
            self.commit()

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
            return False

        self.__start_fade_out_timer()
        return True

    def __clear(self, restart=True):

        if restart:
            person = BsPerson()
            self.person = person
            self.person_type_cbox.setCurrentIndex(0)

        self.first_name_edit.setText("")
        self.middle_name_edit.setText("")
        self.surname_company_edit.setText("")
        self.date_of_birth_date.setDate(QDate.currentDate())
        self.contact_surname_edit.setText("")
        self.contact_first_name_edit.setText("")
        self.contact_first_name_edit.setText("")
        self.contact_position_edit.setText("")
        self.personal_id_edit.setText("")
        self.state_register_edit.setText("")
        self.bank_cbox.setCurrentIndex(0)
        self.account_edit.setText("")
        self.phone_edit.setText("")
        self.mobile_phone_edit.setText("")
        self.email_edit.setText("")
        self.website_edit.setText("")
        self.town_edit.setText("")
        self.street_name_edit.setText("")
        self.khashaa_edit.setText("")
        self.building_edit.setText("")
        self.entrance_edit.setText("")
        self.apartment_edit.setText("")

        self.personal_id_edit.setStyleSheet(self.styleSheet())
        self.first_name_edit.setStyleSheet(self.styleSheet())
        self.surname_company_edit.setStyleSheet(self.styleSheet())

    @pyqtSlot()
    def on_apply_clear_button_clicked(self):

        if self.__save_person():

            self.__clear()

    @pyqtSlot()
    def on_close_button_clicked(self):

        self.reject()

    def __validate_person_id(self, person_type, text):

        try:
            count = self.session.query(BsPerson.person_id).filter_by(person_id=text).filter(
                BsPerson.person_id != self.person.person_id).count()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))
            return

        if not self.is_age_18 and person_type == PersonType.legally_capable_mongolian:
            self.error_label.setText(self.tr("Person under the age of 18."))
            return False

        if count > 0:
            self.error_label.setText(self.tr("This person id is already registered."))
            return False

        if person_type == PersonType.legally_capable_mongolian or person_type == PersonType.legally_uncapable_mongolian:
            count = len(text)
            if count > 10:
                self.error_label.setText(self.tr("The person id can't be longer than 10."))
                return False

            if count < 10:
                self.error_label.setText(self.tr("The person id can't be shorter than 10."))
                return False

            if not self.__validate_private_person_id(text):
                return False

        elif person_type == PersonType.mongolian_buisness \
                or person_type == PersonType.mongolian_state_org:

            if not self.__validate_entity_id(text):
                self.personal_id_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                self.error_label.setText(
                    "Mongolian business and mongolian state organisation ids should contain only numbers.")
                return False

        elif person_type == person_type == PersonType.foreign_citizen \
                or person_type == PersonType.legal_entity_foreign:
            return True

        return True

    @pyqtSlot(str)
    def on_apartment_edit_textChanged(self, text):

        self.apartment_edit.setStyleSheet(self.styleSheet())
        if not self.__validate_apartment_number(text, self.tr("Apartment")):
            self.apartment_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    @pyqtSlot(str)
    def on_building_edit_textChanged(self, text):

        self.building_edit.setStyleSheet(self.styleSheet())

        if not self.__validate_apartment_number(text, self.tr("Building")):
            self.building_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    @pyqtSlot(str)
    def on_entrance_edit_textChanged(self, text):

        self.entrance_edit.setStyleSheet(self.styleSheet())
        if not self.__validate_entrance_no(text):
            self.entrance_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    @pyqtSlot(str)
    def on_personal_id_edit_textChanged(self, text):

        self.personal_id_edit.setStyleSheet(self.styleSheet())
        person_type = self.person_type_cbox.itemData(self.person_type_cbox.currentIndex())

        if person_type == PersonType.legally_capable_mongolian or person_type == PersonType.legally_uncapable_mongolian:
            new_text = self.__auto_correct_private_person_id(text)
            if new_text is not text:
                self.personal_id_edit.setText(new_text)
                return

            if not self.__validate_private_person_id(text):
                self.personal_id_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                return

        elif person_type == PersonType.mongolian_buisness or person_type == PersonType.mongolian_state_org:

            if not self.__validate_entity_id(text):
                self.personal_id_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)

    def __validate(self):

        valid = True

        self.__reset_styles()
        person_type = self.person_type_cbox.itemData(self.person_type_cbox.currentIndex())
        text = self.surname_company_edit.text()

        if person_type == PersonType.mongolian_buisness or person_type == PersonType.mongolian_state_org \
                or person_type == PersonType.legal_entity_foreign:

            if not self.__validate_company_name(text):
                self.surname_company_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                valid = False

            if not self.contact_first_name_edit.text():
                self.contact_first_name_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                valid = False
            if not self.contact_surname_edit.text():
                self.contact_surname_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                valid = False

        elif person_type == PersonType.foreign_citizen:

            if not self.__validate_company_name(text):
                self.surname_company_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                valid = False

            if not self.first_name_edit.text():
                self.surname_company_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                valid = False

        else:

            if not self.__validate_person_name(text):
                self.surname_company_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                valid = False

            if not self.first_name_edit.text():
                self.first_name_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                valid = False

        if not self.__validate_apartment_number(self.building_edit.text(), self.tr("Building")):
            self.building_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            valid = False

        if not self.__validate_apartment_number(self.khashaa_edit.text(), self.tr("Khashaa")):
            self.khashaa_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            valid = False

        if not self.__validate_apartment_number(self.apartment_edit.text(), self.tr("Apartment")):
            self.building_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            valid = False

        if not self.bank_cbox.itemData(self.bank_cbox.currentIndex()) == -1:
            if self.account_edit.text() == "":
                self.account_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                valid = False

        if not self.__validate_person_id(person_type, self.personal_id_edit.text()):
            self.personal_id_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            valid = False

        if not self.__validate_entrance_no(self.entrance_edit.text(), True):
            self.entrance_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            valid = False

        if not self.__validate_street_name(self.street_name_edit.text()):
            self.street_name_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            valid = False

        if not self.mobile_phone_edit.text() == "":
            current_phone = self.mobile_phone_edit.text()
            phone_numbers = current_phone.split(",")

            for number in phone_numbers:
                if len(number) != 8:
                    self.mobile_phone_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                    valid = False

        if not self.email_edit.text() == "":
            result = self.email_validator.regExp().exactMatch(self.email_edit.text())
            if not result:
                self.email_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                valid = False

        if not self.website_edit.text() == "":
            website_result = self.www_validator.regExp().exactMatch(self.website_edit.text())
            if not website_result:
                self.website_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                valid = False

        if not self.phone_edit.text() == "":
            current_phone = self.phone_edit.text()
            phone_numbers = current_phone.split(",")

            for number in phone_numbers:
                if len(number) != 8 and len(number) != 6:
                    self.phone_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
                    valid = False

        if not self.__validate_state_reg_number(self.state_register_edit.text()):
            self.state_register_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            valid = False

        return valid

    def __validate_entity_id(self, text):

        valid = self.int_validator.regExp().exactMatch(text)

        if not valid:
            self.error_label.setText(self.tr("Company id should be with numbers only."))
            return False
        if len(text) > 7:
            cut = text[:7]
            self.personal_id_edit.setText(cut)

        return True

    def __validate_private_person_id(self, text):

        original_text = text
        first_letters = text[:2]
        rest = text[2:]
        first_large_letters = first_letters.upper()

        reg = QRegExp("[0-9][0-9]+")
        is_valid = True

        if first_large_letters[0:1] not in Constants.CAPITAL_MONGOLIAN \
                and first_large_letters[1:2] not in Constants.CAPITAL_MONGOLIAN:
            self.error_label.setText(
                self.tr("First letters of the person id should be capital letters and in mongolian."))
            is_valid = False

        if len(original_text) > 2:
            if not reg.exactMatch(rest):
                self.error_label.setText(
                    self.tr("After the first two capital letters, the person id should contain only numbers."))
                is_valid = False

        if len(original_text) > 10:
            self.error_label.setText(self.tr("The person id shouldn't be longer than 10 characters."))
            is_valid = False

        return is_valid

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

    def __validate_state_reg_number(self, number):

        if len(number) == 0:
            return True

        if len(number) == 10:
            return True
        else:
            self.error_label.setText(self.tr("The state registration number should have a length of 10 numbers."))
            return False

    def __replace_spaces(self, text):

        if len(text) == 0:
            return text

        if " " in text:
            text_new = text.replace(" ", "-")
            return text_new

        return text

    def __remove_numbers(self, text):

        if self.int_validator.regExp().indexIn(text) != -1:
            new_text = "".join([i for i in text if not i.isdigit()])
            return new_text

        return text

    def __capitalize_after_minus(self, text):

        new_text = text
        if len(text) < 1:
            return

        for i in range(len(text)):
            if i == len(text) - 1:
                return new_text
            if text[i] == "-":
                if not text[i + 1] in Constants.CAPITAL_MONGOLIAN:
                    new_text = text.replace("-" + text[i + 1], "-" + text[i + 1].upper())

        return new_text

    def __auto_correct_company_name(self, text):

        cap_value = self.__capitalize_first_letter(text)
        return cap_value

    def __auto_correct_person_name(self, text):

        # Private Persons:
        # 1st: replace spaces
        # 2cnd: remove numbers
        new_text = self.__capitalize_first_letter(text)
        new_text = self.__replace_spaces(new_text)
        new_text = self.__remove_numbers(new_text)
        new_text = self.__capitalize_after_minus(new_text)
        return new_text

    def __auto_correct_private_person_id(self, text):

        original_text = text
        first_letters = text[:2]
        rest = text[2:]

        first_large_letters = first_letters.upper()

        reg = QRegExp("[0-9]+")

        new_text = first_large_letters + rest

        if len(rest) > 0:

            if not reg.exactMatch(rest):
                for i in rest:
                    if not i.isdigit():
                        rest = rest.replace(i, "")

                new_text = first_large_letters + rest

        if len(original_text) > 7:
            self.__update_date_of_birth(original_text)

        if len(new_text) > 10:
            new_text = new_text[:10]

        return new_text

    def __update_date_of_birth(self, original_text):

        if len(original_text) > 7:

            year = original_text[2:4]
            month = original_text[4:6]
            day = original_text[6:8]
            reg = QRegExp("[0-9]+")

            if reg.exactMatch(year) \
                    and reg.exactMatch(month) \
                    and reg.exactMatch(day):

                current_year = str(QDate().currentDate().year())[2:]

                if int(year) == 0 or int(year) <= int(current_year):
                    year = "20" + year
                else:
                    year = "19" + year
                date = QDate(int(year), int(month), int(day))
                self.date_of_birth_date.setDate(date)

            if not self.__check_age_applicants(original_text):
                self.error_label.clear()
                self.error_label.setText("Person under the age of 18.")
                return
            else:
                self.error_label.clear()

    def __is_number(self, s):

        try:
            float(s)  # for int, long and float
        except ValueError:
            try:
                complex(s)  # for complex
            except ValueError:
                return False

        return True

    def __check_age_applicants(self, original_text):

        self.is_age_18 = None

        today = date.today()
        t_y = today.year
        t_m = today.month
        t_d = today.day

        year = original_text[2:4]
        if self.__is_number(year):
            year = original_text[2:4]
        else:
            year = '00'
        current_year = str(QDate().currentDate().year())[2:]
        if int(year) == 0 or int(year) <= int(current_year):
            year = "20" + year
        else:
            year = "19" + year
        month = original_text[4:6]
        day = original_text[6:8]

        b_y = int(year)
        b_m = int(month)
        b_d = int(day)
        age_y = int(t_y) - int(b_y)
        if age_y == 18:
            age_m = t_m - b_m
            if age_m == 0:
                age_d = int(b_d) - int(t_d)
                if age_d == 0:
                    self.is_age_18 = True
                elif age_d > 0:
                    self.is_age_18 = False
                else:
                    self.is_age_18 = True
            elif age_m > 0:
                self.is_age_18 = True
            else:
                self.is_age_18 = False
        elif age_y > 18:
            self.is_age_18 = True
        elif age_y < 18:
            self.is_age_18 = False

        if self.is_age_18 == True:
            return True
        else:
            return False

    def __validate_person_name(self, text):

        if len(text) <= 0:
            return False

        first_letter = text[0]
        rest = text[1:]
        result_capital = self.capital_asci_letter_validator.regExp().indexIn(rest)
        result_lower = self.lower_case_asci_letter_validator.regExp().indexIn(rest)

        if first_letter not in Constants.CAPITAL_MONGOLIAN:
            self.error_label.setText(self.tr("The first letter and the letter after of a "
                                             "name and the letter after a \"-\"  should be a capital letters."))
            return False

        if len(rest) > 0:

            if result_capital != -1 or result_lower != -1:
                self.error_label.setText(self.tr("Only mongolian characters are allowed."))
                return False

            for i in range(len(rest)):
                if rest[i] not in Constants.LOWER_CASE_MONGOLIAN and rest[i] != "-":
                    if len(rest) - 1 == i:
                        return True

                    if rest[i - 1] != "-":
                        self.error_label.setText(
                            self.tr("Capital letters are only allowed at the beginning of a name or after a \"-\". "))
                        return False

        return True

    def __validate_company_name(self, text):

        # no validation so far
        if text == "":
            return False

        return True

    def __validate_entrance_no(self, text, reset_if_empty=False):

        if reset_if_empty:
            if self.entrance_edit.text() == Constants.ENTRANCE_DEFAULT_VALUE:
                self.entrance_edit.setText("")

        entrance_default_value = Constants.ENTRANCE_DEFAULT_VALUE
        numbers_only = text.replace(entrance_default_value, "")

        if numbers_only == "":
            return True

        result = self.int_validator.regExp().exactMatch(numbers_only)

        if not result:
            self.error_label.setText(self.tr("The entrance number consists of numbers only."))
            return False
        elif " " in numbers_only:
            self.error_label.setText(self.tr("The first character of an entrance number shouldn't be a space."))
            return False
        else:
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

    def __validate_building_number(self, text):

        if len(text) == 0:
            return True

        first_char = text[0]
        last_char = text[:-1]

        if not first_char.isdigit():
            self.error_label.setText(self.tr("Building number must start with a number."))
            return False

        if last_char in Constants.CAPITAL_MONGOLIAN:
            self.error_label.setText(self.tr("Building number should have only numbers and lower case characters."))
            return False

        count = 0
        reg = QRegExp("[a-z]")

        for i in range(len(text)):
            if text[i] in Constants.CAPITAL_MONGOLIAN or text[i] in Constants.LOWER_CASE_MONGOLIAN:
                count += 1

            if reg.exactMatch(text[i]):
                self.error_label.setText(self.tr("Building number can only contain mongolian characters."))
                return False

        if count > 1:
            self.error_label.setText(self.tr("Building number can only contain one lower case character."))
            return False

        return True

    def __reset_styles(self):

        self.surname_company_edit.setStyleSheet(self.styleSheet())
        self.middle_name_edit.setStyleSheet(self.styleSheet())
        self.first_name_edit.setStyleSheet(self.styleSheet())
        self.contact_first_name_edit.setStyleSheet(self.styleSheet())
        self.contact_surname_edit.setStyleSheet(self.styleSheet())
        self.contact_position_edit.setStyleSheet(self.styleSheet())
        self.personal_id_edit.setStyleSheet(self.styleSheet())
        self.state_register_edit.setStyleSheet(self.styleSheet())
        self.account_edit.setStyleSheet(self.styleSheet())
        self.website_edit.setStyleSheet(self.styleSheet())
        self.email_edit.setStyleSheet(self.styleSheet())
        self.phone_edit.setStyleSheet(self.styleSheet())
        self.mobile_phone_edit.setStyleSheet(self.styleSheet())
        self.town_edit.setStyleSheet(self.styleSheet())
        self.street_name_edit.setStyleSheet(self.styleSheet())
        self.apartment_edit.setStyleSheet(self.styleSheet())
        self.entrance_edit.setStyleSheet(self.styleSheet())
        self.building_edit.setStyleSheet(self.styleSheet())
        self.khashaa_edit.setStyleSheet(self.styleSheet())

    @pyqtSlot()
    def on_help_button_clicked(self):

        os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/person.htm")