__author__ = 'B.Ankhbold'
# -*- encoding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sqlalchemy import exc, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_, extract
from datetime import date, datetime, timedelta
from ..view.Ui_MemberGroupDialog import *
from ..model.DatabaseHelper import *
from ..model.LM2Exception import LM2Exception
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.SessionHandler import SessionHandler
from ..utils.PluginUtils import PluginUtils
from ..model import Constants
from ..model.AuLevel1 import AuLevel1
from ..model.AuLevel2 import AuLevel2
from ..model.AuLevel3 import AuLevel3
from ..model.CtPersonGroup import *
from ..model.PersonSearch import *
from ..model.BsPerson import *
from ..model.CtGroupMember import *
from ..model.ClMemberRole import *
import os

class MemberGroupDialog(QDialog, Ui_MemberGroupDialog, DatabaseHelper):
    def __init__(self, group_id, attribute_update, parent=None):

        super(MemberGroupDialog, self).__init__(parent)
        DatabaseHelper.__init__(self)

        self.setupUi(self)
        self.time_counter = None
        self.setWindowTitle(self.tr("Member group dialog"))
        self.session = SessionHandler().session_instance()
        self.group_id = group_id
        self.attribute_update = attribute_update

        self.__setup_validators()
        self.__setup_ui()

    def __setup_twidget(self):

        self.bag_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.bag_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.bag_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.group_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.group_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.group_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.person_twidget.setColumnCount(1)
        self.person_twidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.person_twidget.horizontalHeader().setVisible(False)
        self.person_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.person_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.person_twidget.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.person_twidget.customContextMenuRequested.connect(self.on_custom_context_menu_requested)
        self.person_twidget.setDragEnabled(True)

        self.member_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.member_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.member_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def __setup_ui(self):

        self.__setup_twidget()
        self.__read_pug_group()

        if self.attribute_update:
            self.__setup_mapping()
        else:
            self.__setup_new_member()

    def __setup_mapping(self):

        for row in range(self.group_twidget.rowCount()):

            item = self.group_twidget.item(row, 0)
            group_no = item.data(Qt.UserRole)
            if group_no == self.group_id:
                self.group_twidget.selectRow(row)
                item.setCheckState(Qt.Checked)

        self.bag_cbox.clear()
        l2_code = DatabaseUtils.working_l2_code()

        if l2_code == -1 or not l2_code:
            return
        else:
            try:
                PluginUtils.populate_au_level3_cbox(self.bag_cbox, l2_code)
            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("Sql Error"), e.message)

        if self.group_id != -1:
            group_id = self.group_id
            pug = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == group_id).one()
            group_name = pug.group_name
            self.group_id_edit.setText(str(group_id))
            self.group_name_edit.setText(group_name)

            bags = pug.bags
            count = 0
            self.bag_twidget.setRowCount(0)
            for au3 in bags:
                code = au3.code
                name = au3.name
                item = QTableWidgetItem((name))
                item.setIcon(QIcon(QPixmap(":/plugins/lm2_pasture/bag.png")))
                item.setData(Qt.UserRole, code)
                self.bag_twidget.insertRow(count)
                self.bag_twidget.setItem(count, 0, item)
                count += 1

                self.bag_cbox.removeItem(self.bag_cbox.findData(code))

        pug_member = self.session.query(CtGroupMember).filter(CtGroupMember.group_no == group_id).all()

        self.member_twidget.setRowCount(0)
        count = 0
        for member in pug_member:
            person = member.person_ref
            if not person.person_id:
                person_id = self.tr(" (Id: n.a. )")
            else:
                person_id = self.tr(" (Id: ") + person.person_id + ")"

            first_name = self.tr(" n.a. ") if not person.first_name else person.first_name

            item = QTableWidgetItem(person.name + ", " + first_name + person_id)
            if member.role == 10:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setIcon(QIcon(QPixmap(":/plugins/lm2/person.png")))
            item.setData(Qt.UserRole, person.person_id)
            self.member_twidget.insertRow(count)

            self.member_twidget.setItem(count, 0, item)

            group_item = QTableWidgetItem(group_name)
            group_item.setData(Qt.UserRole, group_id)
            self.member_twidget.setItem(count, 1, group_item)

            count += 1

    def __setup_new_member(self):

        self.group_id_edit.setText(str(self.group_id))

        l2_code = DatabaseUtils.working_l2_code()

        if l2_code == -1 or not l2_code:
            return
        else:
            try:
                PluginUtils.populate_au_level3_cbox(self.bag_cbox, l2_code)
            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("Sql Error"), e.message)

    @pyqtSlot()
    def on_group_new_button_clicked(self):

        self.__new_id_generate()

    def __new_id_generate(self):

        pug_max_id = self.session.query(CtPersonGroup). \
            order_by(CtPersonGroup.group_no.desc()).first()

        l2_code = DatabaseUtils.working_l2_code()

        if not pug_max_id:
            member_group_new_id = 1
        else:
            if len(str(pug_max_id.group_no)) < 5:
                member_group_new_id = pug_max_id.group_no + 1
            else:
                member_group_new_id = int(str(pug_max_id.group_no)[4:]) + 1
        member_group_new_id = int(str(int(l2_code)) + '' + str(member_group_new_id))

        self.group_id_edit.setText(str(member_group_new_id))

    def __setup_validators(self):

        self.capital_asci_letter_validator = QRegExpValidator(QRegExp("[A-Z]"), None)
        self.lower_case_asci_letter_validator = QRegExpValidator(QRegExp("[a-z]"), None)
        self.int_validator = QRegExpValidator(QRegExp("[0-9]+"), None)

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

    def __auto_correct_person_name(self, text):

        # Private Member:
        # 1st: replace spaces
        # 2cnd: remove numbers
        new_text = self.__capitalize_first_letter(text)
        new_text = self.__replace_spaces(new_text)
        new_text = self.__remove_numbers(new_text)
        new_text = self.__capitalize_after_minus(new_text)
        return new_text

    @pyqtSlot(str)
    def on_group_name_edit_textChanged(self, text):

        self.group_name_edit.setStyleSheet(self.styleSheet())

        new_text = self.__auto_correct_person_name(text)
        if new_text != text:
            self.group_name_edit.setText(new_text)
            return

        if not self.__validate_person_name(text):
            self.group_name_edit.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
        else:
            self.error_label.clear()

    @pyqtSlot()
    def on_bag_add_button_clicked(self):

        selected_items = self.group_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please select person group."))
            return None

        # self.__save_pug()
        row = self.group_twidget.currentRow()
        group_no = self.group_twidget.item(row, 0).text()
        pug = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == group_no).one()
        bag_item = self.bag_cbox.itemData(self.bag_cbox.currentIndex())
        l2_code = DatabaseUtils.working_l2_code()

        if l2_code == -1 or not l2_code:
            return
        else:
            try:
                if bag_item == -1:
                    count = 0
                    self.bag_twidget.setRowCount(0)
                    for au3 in self.session.query(AuLevel3).filter(
                            AuLevel3.code.startswith(l2_code)).order_by(AuLevel3.name):
                        code = au3.code
                        name = au3.name
                        item = QTableWidgetItem((name))
                        item.setIcon(QIcon(QPixmap(":/plugins/lm2_pasture/bag.png")))
                        item.setData(Qt.UserRole, code)
                        self.bag_twidget.insertRow(count)
                        self.bag_twidget.setItem(count, 0, item)
                        count += 1

                    self.bag_cbox.clear()
                    self.bag_cbox.addItem("*", -1)
                else:
                    count = 0
                    au3 = self.session.query(AuLevel3.code, AuLevel3.name).filter(AuLevel3.code == bag_item).one()
                    item = QTableWidgetItem((au3.name))
                    item.setIcon(QIcon(QPixmap(":/plugins/lm2_pasture/bag.png")))
                    item.setData(Qt.UserRole, au3.code)
                    self.bag_twidget.insertRow(count)
                    self.bag_twidget.setItem(count, 0, item)
                    count += 1
                    self.bag_cbox.removeItem(self.bag_cbox.currentIndex())

                for row in range(self.bag_twidget.rowCount()):
                    bag_code = self.bag_twidget.item(row, 0).data(Qt.UserRole)
                    au3 = self.session.query(AuLevel3).filter(AuLevel3.code == bag_code).one()

                    pug.bags.append(au3)
                # self.__read_pug_group()
            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("Sql Error"), e.message)

    @pyqtSlot()
    def on_bag_remove_button_clicked(self):

        if not len(self.bag_twidget.selectedItems()) == 1:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return

        selectedItem = self.bag_twidget.selectedItems()[0]
        bag_code = selectedItem.data(Qt.UserRole)
        bag_text = selectedItem.text()

        row  = self.bag_twidget.currentRow()
        self.bag_twidget.removeRow(row)

        self.bag_cbox.addItem(bag_text, bag_code)

        row = self.group_twidget.currentRow()
        group_no = self.group_twidget.item(row, 0).text()
        pug = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == group_no).one()

        row = self.bag_twidget.currentRow()
        code = self.bag_twidget.item(row, 0).data(Qt.UserRole)
        bag = self.session.query(AuLevel3).filter(AuLevel3.code == code).one()

        pug.bags.remove(bag)

    @pyqtSlot()
    def on_group_add_button_clicked(self):

        if not self.group_name_edit.text():
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Group name null."))
            return

        is_register = False
        for row in range(self.group_twidget.rowCount()):
            group_id = self.group_twidget.item(row, 0).text()
            group_name = self.group_twidget.item(row, 1).text()
            if group_id == self.group_id_edit.text() or group_name == self.group_name_edit.text():
                is_register = True
        group_count = self.session.query(CtPersonGroup). \
            filter(CtPersonGroup.group_no == int(self.group_id_edit.text())).count()
        if group_count > 0:
            PluginUtils.show_message(self, self.tr("Group Duplicate"), self.tr("This group already registered"))
            return

        if is_register:
            PluginUtils.show_message(self, self.tr("Group Duplicate"), self.tr("This group already registered"))
            return

        group_id = -1
        row = self.group_twidget.rowCount()
        self.group_twidget.insertRow(row)

        item = QTableWidgetItem((self.group_id_edit.text()))
        item.setCheckState(Qt.Checked)
        item.setIcon(QIcon(QPixmap(":/plugins/lm2_pasture/group.png")))
        item.setData(Qt.UserRole, group_id)

        self.group_twidget.setItem(row, 0, item)

        item = QTableWidgetItem((self.group_name_edit.text()))
        item.setData(Qt.UserRole, (self.group_name_edit.text()))

        self.group_twidget.setItem(row, 1, item)


        item = QTableWidgetItem(('No Contract'))
        item.setData(Qt.UserRole, ('No Contract'))

        self.group_twidget.setItem(row, 2, item)

        self.group_twidget.selectRow(row)

        new_id = int(self.group_id_edit.text())+1
        self.group_id_edit.setText(str(new_id))

        self.bag_twidget.clearContents()
        self.bag_twidget.setRowCount(0)

        self.__save_pug()

    @pyqtSlot()
    def on_group_edit_button_clicked(self):

        row = self.group_twidget.currentRow()
        if row == -1:
            return

        item = self.group_twidget.item(row, 1)
        item.setText(self.group_name_edit.text())
        item.setData(Qt.UserRole, self.group_name_edit.text())

        self.__save_pug()

    @pyqtSlot(QTableWidgetItem)
    def on_group_twidget_itemClicked(self, item):

        row = self.group_twidget.currentRow()
        id_item  = self.group_twidget.item(row, 0)
        group_id = id_item.data(Qt.UserRole)
        group_name = self.group_twidget.item(row, 1).data(Qt.UserRole)
        for row in range(self.group_twidget.rowCount()):
            item_dec = self.group_twidget.item(row, 0)
            item_dec.setCheckState(Qt.Unchecked)
        id_item.setCheckState(Qt.Checked)
        self.bag_cbox.clear()
        l2_code = DatabaseUtils.working_l2_code()

        if l2_code == -1 or not l2_code:
            return
        else:
            try:
                PluginUtils.populate_au_level3_cbox(self.bag_cbox, l2_code)
            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("Sql Error"), e.message)

        if group_id != -1:
            self.group_id_edit.setText(str(group_id))
            self.group_name_edit.setText(group_name)
            pug = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == group_id).one()
            bags = pug.bags
            count = 0
            self.bag_twidget.setRowCount(0)
            for au3 in bags:
                code = au3.code
                name = au3.name
                item = QTableWidgetItem((name))
                item.setIcon(QIcon(QPixmap(":/plugins/lm2_pasture/bag.png")))
                item.setData(Qt.UserRole, code)
                self.bag_twidget.insertRow(count)
                self.bag_twidget.setItem(count, 0, item)
                count += 1

                self.bag_cbox.removeItem(self.bag_cbox.findData(code))

        pug_member = self.session.query(CtGroupMember).filter(CtGroupMember.group_no == group_id).all()

        self.member_twidget.setRowCount(0)
        count = 0
        for member in pug_member:
            person = member.person_ref
            if not person.person_id:
                person_id = self.tr(" (Id: n.a. )")
            else:
                person_id = self.tr(" (Id: ") + person.person_id + ")"

            first_name = self.tr(" n.a. ") if not person.first_name else person.first_name

            item = QTableWidgetItem(person.name + ", " + first_name + person_id)
            if member.role == 10:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            item.setIcon(QIcon(QPixmap(":/plugins/lm2/person.png")))
            item.setData(Qt.UserRole, person.person_id)
            self.member_twidget.insertRow(count)

            self.member_twidget.setItem(count, 0, item)

            group_item = QTableWidgetItem(group_name)
            group_item.setData(Qt.UserRole, group_id)
            self.member_twidget.setItem(count, 1, group_item)

            count += 1


    def __fade_status_message(self):

        opacity = int(self.time_counter * 0.5)
        self.status_label.setStyleSheet("QLabel {color: rgba(255,0,0," + str(opacity) + ");}")
        self.status_label.setText(self.tr('Changes applied successfully.'))
        if self.time_counter == 0:
            self.timer.stop()
        self.time_counter -= 1

    def __start_fade_out_timer(self):

        self.timer = QTimer()
        self.timer.timeout.connect(self.__fade_status_message)
        self.time_counter = 500
        self.timer.start(10)

    @pyqtSlot()
    def on_apply_button_clicked(self):

        # if not self.__save_pug():
        #     return
        self.__save_member()
        self.commit()
        self.__read_pug_group()
        self.__start_fade_out_timer()

    def __save_pug(self):

        try:

            self.__save_pug_group()

            return True

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
            return False

    def __save_pug_group(self):

        try:
            for row in range(self.group_twidget.rowCount()):
                new_row = False
                id = self.group_twidget.item(row, 0).data(Qt.UserRole)
                if id == -1:
                    new_row = True
                    pug_group = CtPersonGroup()
                else:
                    pug_group = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == id).one()

                pug_group.group_no = int(self.group_twidget.item(row, 0).text())
                pug_group.group_name = self.group_twidget.item(row, 1).text()
                pug_group.is_contract = self.group_twidget.item(row, 2).text()
                created_date = PluginUtils.convert_qt_date_to_python(QDate().currentDate())
                pug_group.created_date = created_date

                if new_row:
                    self.session.add(pug_group)

                item = self.group_twidget.item(row, 0)
                item.setData(Qt.UserRole, int(self.group_twidget.item(row, 0).text()))

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
            raise

    def __read_pug_group(self):

        self.group_twidget.clearContents()
        self.group_twidget.setRowCount(0)

        self.bag_twidget.clearContents()
        self.bag_twidget.setRowCount(0)

        row = 0
        group_count = self.session.query(CtPersonGroup).count()
        if group_count > 0:
            self.group_twidget.setRowCount(group_count)
            pug_groups = self.session.query(CtPersonGroup).all()
            for group in pug_groups:
                item  = QTableWidgetItem(str(group.group_no))
                item.setIcon(QIcon(QPixmap(":/plugins/lm2_pasture/group.png")))
                item.setData(Qt.UserRole, group.group_no)
                item.setCheckState(Qt.Unchecked)
                self.group_twidget.setItem(row, 0, item)

                item  = QTableWidgetItem(group.group_name)
                item.setData(Qt.UserRole, group.group_name)
                self.group_twidget.setItem(row, 1, item)

                item  = QTableWidgetItem(group.is_contract)
                self.group_twidget.setItem(row, 2, item)

                row += 1

    def __remove_person_items(self):

        self.person_twidget.setRowCount(0)

    @pyqtSlot()
    def on_person_find_button_clicked(self):

        self.__search_persons()

    def __search_persons(self):

        try:
            persons = self.session.query(PersonSearch)
            filter_is_set = False
            if self.firstname_edit.text():
                filter_is_set = True
                right_holder = "%" + self.firstname_edit.text() + "%"
                persons = persons.filter(or_(func.lower(PersonSearch.name).like(func.lower(right_holder)),
                                             func.lower(PersonSearch.first_name).ilike(func.lower(right_holder)),
                                             func.lower(PersonSearch.middle_name).ilike(func.lower(right_holder))))

            if self.person_id_edit.text():
                filter_is_set = True
                value = "%" + self.person_id_edit.text() + "%"
                persons = persons.filter(PersonSearch.person_id.ilike(value))

            count = 0

            self.__remove_person_items()

            if persons.distinct(PersonSearch.person_id).count() == 0:
                self.error_label.setText(self.tr("No persons found for this search filter."))
                return
            elif filter_is_set is False:
                self.error_label.setText(self.tr("Please specify a search filter."))
                return

            for person in persons.distinct(PersonSearch.name, PersonSearch.person_id).order_by(PersonSearch.name.asc(), PersonSearch.person_id.asc()).all():

                if not person.person_id:
                    person_id = self.tr(" (Id: n.a. )")
                else:
                    person_id = self.tr(" (Id: ") + person.person_id + ")"

                first_name = self.tr(" n.a. ") if not person.first_name else person.first_name

                item = QTableWidgetItem(person.name + ", " + first_name + person_id)
                item.setIcon(QIcon(QPixmap(":/plugins/lm2/person.png")))
                item.setData(Qt.UserRole, person.person_id)
                self.person_twidget.insertRow(count)
                self.person_twidget.setItem(count, 0, item)
                count += 1

            self.error_label.setText("")

        except SQLAlchemyError, e:
            PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
            return

    @pyqtSlot()
    def on_pug_add_person_button_clicked(self):

        selected_items = self.person_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please select person."))
            return

        selected_items = self.group_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please select person group."))
            return None

        row = self.group_twidget.currentRow()
        group_no = self.group_twidget.item(row, 0).data(Qt.UserRole)
        group_name = self.group_twidget.item(row, 1).text()

        items = self.person_twidget.selectedItems()
        count = 0
        for item in items:
            person_id = item.data(Qt.UserRole)

            is_register = False
            for row in range(self.member_twidget.rowCount()):
                id = self.member_twidget.item(row, 0).data(Qt.UserRole)
                if id == person_id:
                    is_register = True

            if is_register:
                PluginUtils.show_message(self, self.tr("Group Duplicate"), self.tr("This group already registered"))
                return

            person = self.session.query(BsPerson).filter(BsPerson.person_id == person_id).one()
            if not person.person_id:
                person_id = self.tr(" (Id: n.a. )")
            else:
                person_id = self.tr(" (Id: ") + person.person_id + ")"

            first_name = self.tr(" n.a. ") if not person.first_name else person.first_name

            item = QTableWidgetItem(person.name + ", " + first_name + person_id)
            item.setCheckState(Qt.Unchecked)
            item.setIcon(QIcon(QPixmap(":/plugins/lm2/person.png")))
            item.setData(Qt.UserRole, person.person_id)
            self.member_twidget.insertRow(count)

            self.member_twidget.setItem(count, 0, item)

            group_item = item = QTableWidgetItem(group_name)
            group_item.setData(Qt.UserRole, group_no)
            self.member_twidget.setItem(count, 1, group_item)

            count += 1

    def __save_member(self):

        row = self.group_twidget.currentRow()
        if row == -1:
            return
        group_no = self.group_twidget.item(row, 0).data(Qt.UserRole)

        for row in range(self.member_twidget.rowCount()):
            person_id = self.member_twidget.item(row, 0).data(Qt.UserRole)

            pug = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == group_no).one()
            person = self.session.query(BsPerson).filter(BsPerson.person_id == person_id).one()
            changed_item = self.member_twidget.item(row, 0)
            if changed_item.checkState() == Qt.Checked:
                role_ref = self.session.query(ClMemberRole).filter_by(
                    code=10).one()
                role = 10
            else:
                role_ref = self.session.query(ClMemberRole).filter_by(
                    code=20).one()
                role = 20

            member_count = self.session.query(CtGroupMember).filter(CtGroupMember.person == person_id).\
                filter(CtGroupMember.group_no == group_no).count()
            if member_count == 1:
                pug_member = self.session.query(CtGroupMember).filter(CtGroupMember.person == person_id).\
                    filter(CtGroupMember.group_no == group_no).one()
                pug_member.group_no = group_no
                pug_member.person = person_id
                pug_member.person_ref = person
                pug_member.role = role
                pug_member.role_ref = role_ref
            else:
                pug_member = CtGroupMember()
                pug_member.group_no = group_no
                pug_member.person = person_id
                pug_member.person_ref = person
                pug_member.role = role
                pug_member.role_ref = role_ref

                pug.members.append(pug_member)

        self.member_twidget.clearContents()
        self.member_twidget.setRowCount(0)

    @pyqtSlot(QTableWidgetItem)
    def on_member_twidget_itemClicked(self, item):

        row = self.member_twidget.currentRow()
        id_item = self.member_twidget.item(row, 0)
        for row in range(self.member_twidget.rowCount()):
            item_dec = self.member_twidget.item(row, 0)
            item_dec.setCheckState(Qt.Unchecked)
        if id_item:
            id_item.setCheckState(Qt.Checked)

    @pyqtSlot()
    def on_group_delete_button_clicked(self):

        selected_items = self.group_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please select person group."))
            return None

        row = self.group_twidget.currentRow()
        id_item = self.group_twidget.item(row, 0)
        group_id = id_item.data(Qt.UserRole)

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to delete person group ?"))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        group_members = self.session.query(CtGroupMember).filter(CtGroupMember.group_no == group_id).all()

        for group_member in group_members:
            self.session.query(CtGroupMember).filter(CtGroupMember.group_no == group_id).\
                filter(CtGroupMember.person == group_member.person).delete()

        group_count = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == group_id).count()
        if group_count == 1:
            self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == group_id).delete()

        self.group_twidget.removeRow(row)

    @pyqtSlot()
    def on_pug_remove_person_button_clicked(self):

        selected_items = self.member_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please select person."))
            return None

        row = self.group_twidget.currentRow()
        id_item = self.group_twidget.item(row, 0)
        group_id = id_item.data(Qt.UserRole)

        row = self.member_twidget.currentRow()
        id_item = self.member_twidget.item(row, 0)
        person_id = id_item.data(Qt.UserRole)

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to remove person?"))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        self.session.query(CtGroupMember).\
            filter(CtGroupMember.group_no == group_id).\
            filter(CtGroupMember.person == person_id).delete()

        self.member_twidget.removeRow(row)