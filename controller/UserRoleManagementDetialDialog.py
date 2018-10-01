__author__ = 'ankhaa'

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from sqlalchemy.exc import DatabaseError, SQLAlchemyError
from sqlalchemy import func, or_, and_, desc,extract
from sqlalchemy.orm.exc import NoResultFound
from inspect import currentframe
from ..view.Ui_UserRoleManagementDetialDialog import *
from ..model.SetRole import *
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.LM2Exception import LM2Exception
from ..model.DialogInspector import DialogInspector
from ..model.ClPositionType import *
from ..utils.PluginUtils import *
from uuid import getnode as get_mac

import datetime

class UserRoleManagementDetialDialog(QDialog, Ui_UserRoleManagementDetialDialog):

    GROUP_SEPARATOR = '-----'
    PW_PLACEHOLDER = '0123456789'

    def __init__(self, username, parent=None):

        super(UserRoleManagementDetialDialog, self).__init__(parent)
        self.setupUi(self)

        self.close_button.clicked.connect(self.reject)
        self.session = SessionHandler().session_instance()
        self.username = username
        self.extend_date.setDate(QDate.currentDate())
        self.begin_edit_date.setDate(QDate.currentDate())
        self.end_edit_date.setDate(QDate.currentDate())

        self.__setup_combo_boxes()
        self.__user_active_employee()

    def __setup_combo_boxes(self):

        try:
            cl_reason = self.session.query(ClUserCancelReason).order_by(ClUserCancelReason.code).all()
            cl_employee_type = self.session.query(ClEmployeeType).order_by(ClEmployeeType.code).all()
            cl_employee = self.session.query(SetRole.surname, SetRole.user_name, SetRole.first_name, SetRole.user_register).\
                filter(SetRole.user_name == self.username).group_by(SetRole.surname, SetRole.user_name, SetRole.first_name, SetRole.user_register).all()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"),
                                   self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        for item in cl_reason:
            self.cancel_reason_cbox.addItem(item.description, item.code)

        for item in cl_employee_type:
            self.employee_select_type.addItem(item.description, item.code)

        for item in cl_employee:
            self.employee_cbox.addItem(item.surname+'-'+item.first_name, item.user_register)

    def __user_active_employee(self):

        try:
            employee = self.session.query(SetRole).\
                filter(SetRole.user_name == self.username).\
                filter(SetRole.is_active == True).one()
            user_name_real = ''
            if employee.user_name_real:
                user_name_real = employee.user_name_real
            self.user_detial_name_label.setText(self.username +': '+ user_name_real)
            self.user_name_real_lbl.setText(user_name_real)
            self.surname_edit.setText(employee.surname)
            self.firstname_edit.setText(employee.first_name)
            self.register_edit.setText(employee.user_register)
            self.phone_edit.setText(employee.phone)
            self.position_edit.setText(employee.position_ref.name)

            if employee.employee_type:
                # employee_type = self.session.query(ClEmployeeType).filter(ClEmployeeType.code == employee.employee_type).one()
                self.employee_type_cbox.addItem(employee.employee_type_ref.description, employee.employee_type_ref.code)
            self.begin_date.setDate(employee.pa_from)
            self.end_date.setDate(employee.pa_till)
        except DatabaseError, e:
            self.db_session.rollback()
            PluginUtils.show_error(self, self.tr("Database Query Error"),
                                   self.tr("Could not execute: {0}").format(e.message))

    @pyqtSlot(int)
    def on_is_extend_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.extend_date.setEnabled(True)
            self.extend_button.setEnabled(True)
            self.is_cancel_checkbox.setChecked(False)
        else:
            self.extend_date.setEnabled(False)
            self.extend_button.setEnabled(False)

    @pyqtSlot(int)
    def on_is_cancel_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.cancel_reason_cbox.setEnabled(True)
            self.disable_button.setEnabled(True)
            self.is_extend_checkbox.setChecked(False)
        else:
            self.cancel_reason_cbox.setEnabled(False)
            self.disable_button.setEnabled(False)

    @pyqtSlot()
    def on_extend_button_clicked(self):

        message_box = QMessageBox()
        message_box.setText(
            self.tr("Do you want to extend user?"))
        yes_button = message_box.addButton(self.tr("Yes"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)

        message_box.exec_()

        if not message_box.clickedButton() == yes_button:
            return
        set_role = self.session.query(SetRole).\
            filter(SetRole.user_name == self.username).\
            filter(SetRole.is_active == True).one()
        python_date = PluginUtils.convert_qt_date_to_python(self.extend_date.date())

        set_role.pa_till = python_date

        self.session.flush()

    @pyqtSlot()
    def on_disable_button_clicked(self):

        set_role = self.session.query(SetRole). \
            filter(SetRole.user_name == self.username). \
            filter(SetRole.is_active == True).one()

        set_role.cancel_reason = self.cancel_reason_cbox.itemData(self.cancel_reason_cbox.currentIndex())
        set_role.is_active = False
        python_date = PluginUtils.convert_qt_date_to_python(QDate.currentDate())
        set_role.pa_till = python_date

        self.session.flush()
        self.new_employee_gbox.setEnabled(True)

    @pyqtSlot()
    def on_enable_button_clicked(self):

        if not self.begin_edit_date.date() < self.end_edit_date.date():
            PluginUtils.show_message(self, self.tr("Date Validate"), self.tr("End date must be backword!"))
            return
        new_user_number = '01'
        message_box = QMessageBox()
        message_box.setText(
            self.tr("Do you want to enable user?"))
        yes_button = message_box.addButton(self.tr("Yes"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)

        message_box.exec_()

        if not message_box.clickedButton() == yes_button:
            return

        try:
            count = self.session.query(SetRole) \
                .filter(SetRole.user_name == self.username) \
                .order_by(func.substr(SetRole.user_name_real, 11, 12).desc()).count()
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("File Error"),
                                   self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        if count > 0:
            try:
                max_number_user = self.session.query(SetRole) \
                    .filter(SetRole.user_name == self.username) \
                    .order_by(func.substr(SetRole.user_name_real, 11, 12).desc()).first()
            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"),
                                       self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                return

            user_numbers = max_number_user.user_name_real[-2:]
            print str(int(user_numbers[1]))
            new_user_number = (str(int(user_numbers) + 1).zfill(2))
            print new_user_number
            print self.user_name_real_lbl.text()[:10]
        last_user_name = self.user_name_real_lbl.text()[:10]+new_user_number
        print last_user_name
        old_roles = self.session.query(SetRole).filter(SetRole.user_name == self.username).all()
        for user in old_roles:
            user.is_active = False

        user_name = self.username
        surname = ''
        first_name = ''
        user_register = self.employee_cbox.itemData(self.employee_cbox.currentIndex())
        phone = ''
        mac_address = ''
        email = ''
        restriction_au_level1 = ''
        restriction_au_level2 = ''
        restriction_au_level3 = ''
        position = ''
        working_au_level1 = ''
        working_au_level2 = ''

        set_role = self.session.query(SetRole). \
            filter(SetRole.user_name == self.username). \
            filter(SetRole.user_register == self.employee_cbox.itemData(self.employee_cbox.currentIndex())).\
                order_by(SetRole.user_name_real.asc()).all()
        for role in set_role:
            surname = role.surname
            first_name = role.first_name
            phone = role.phone
            mac_address = role.mac_addresses
            email = role.email
            restriction_au_level1 = role.restriction_au_level1
            restriction_au_level2 = role.restriction_au_level2
            restriction_au_level3 = role.restriction_au_level3
            position = role.position
            working_au_level1 = role.working_au_level1
            working_au_level2 = role.working_au_level2

        new_employee = SetRole()
        new_employee.user_name = user_name
        new_employee.surname = surname
        new_employee.user_name_real = last_user_name
        new_employee.first_name = first_name
        new_employee.user_register = user_register
        new_employee.phone = phone
        new_employee.mac_addresses = mac_address
        new_employee.email = email
        new_employee.restriction_au_level1 = restriction_au_level1
        new_employee.restriction_au_level2 = restriction_au_level2
        new_employee.restriction_au_level3 = restriction_au_level3

        begin_date = PluginUtils.convert_qt_date_to_python(self.begin_edit_date.date())
        end_date = PluginUtils.convert_qt_date_to_python(self.end_edit_date.date())
        new_employee.pa_from = begin_date
        new_employee.pa_till = end_date

        new_employee.is_active = True
        new_employee.position = position
        new_employee.employee_type = self.employee_select_type.itemData(self.employee_select_type.currentIndex())

        new_employee.working_au_level1 = working_au_level1
        new_employee.working_au_level2 = working_au_level2

        self.session.add(new_employee)
        self.session.flush()

    @pyqtSlot()
    def on_apply_button_clicked(self):

        self.session.commit()
        PluginUtils.show_message(self, self.tr("User Role Management"), self.tr('New user success is now active.'))