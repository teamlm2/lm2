__author__ = 'ankhaa'

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from sqlalchemy import exc, or_
from sqlalchemy.exc import DatabaseError, SQLAlchemyError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import func, or_, and_, desc,extract
from inspect import currentframe
from ..view.Ui_UserRoleManagementDialog import *
from ..model.SetRole import *
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.LM2Exception import LM2Exception
from ..model.DialogInspector import DialogInspector
from ..model.ClPositionType import *
from ..model.ClGroupRole import *
from ..model.SetPositionGroupRole import *
from ..model.SetUserPosition import *
from ..model.SetUserGroupRole import *
from ..utils.PluginUtils import *
from ..controller.UserRoleManagementDetialDialog import *
from uuid import getnode as get_mac
import  commands
import datetime
import socket
import sys
import struct

INTERFACE_NAME = "eth0"
class UserRoleManagementDialog(QDialog, Ui_UserRoleManagementDialog):

    GROUP_SEPARATOR = '-----'
    PW_PLACEHOLDER = '0123456789'

    def __init__(self, has_privilege , user, parent=None):

        super(UserRoleManagementDialog,  self).__init__(parent)
        self.setupUi(self)

        self.db_session = SessionHandler().session_instance()
        self.has_privilege = has_privilege
        self.__username = user
        self.__privilage()
        self.__setup_combo_boxes()
        self.__populate_user_role_lwidget()

        self.__populate_group_lwidget()

        self.__populate_au_level1_cbox()

        self.close_button.clicked.connect(self.reject)

        # permit only alphanumeric characters for the username
        reg_ex = QRegExp(u"[a-z]{4}[0-9]{6}")
        validator = QRegExpValidator(reg_ex, None)

        reg_ex = QRegExp(u"[a-z_0-9]+")
        validator_pass = QRegExpValidator(reg_ex, None)

        database = QSettings().value(SettingsConstants.DATABASE_NAME)

        self.username_edit.setText('user'+ database[-4:])

        self.username_edit.setValidator(validator)

        self.password_edit.setValidator(validator_pass)
        self.retype_password_edit.setValidator(validator_pass)

        self.__setup_validators()
        self.selected_user = None
        # self.mac_address = self.get_mac_address()
        # self.mac_address_edit.setText(self.mac_address)

        self.__setup_twidget()
        self.__load_default_ritht_grud()

    def __setup_twidget(self):

        self.user_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.user_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.user_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.user_twidget.setSortingEnabled(True)

        self.position_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.position_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.position_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.position_twidget.setSortingEnabled(True)

        self.settings_position_twidget.setAlternatingRowColors(True)
        self.settings_position_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.settings_position_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.settings_right_grud_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.settings_right_grud_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.settings_right_grud_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.settings_right_grud_twidget.setSortingEnabled(True)

        self.settings_right_grud_twidget.setColumnWidth(0, 170)
        self.settings_right_grud_twidget.setColumnWidth(1, 170)
        self.settings_right_grud_twidget.setColumnWidth(2, 45)
        self.settings_right_grud_twidget.setColumnWidth(3, 45)
        self.settings_right_grud_twidget.setColumnWidth(4, 45)
        self.settings_right_grud_twidget.setColumnWidth(5, 45)

        self.right_grud_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.right_grud_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.right_grud_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.right_grud_twidget.setSortingEnabled(True)

        self.right_grud_twidget.setColumnWidth(0, 170)
        self.right_grud_twidget.setColumnWidth(1, 45)
        self.right_grud_twidget.setColumnWidth(2, 45)
        self.right_grud_twidget.setColumnWidth(3, 45)
        self.right_grud_twidget.setColumnWidth(4, 45)


    @pyqtSlot(int)
    def on_get_mac_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.mac_address = self.get_mac_address()
            self.mac_address_edit.setText(self.mac_address)
        else:
            self.mac_address_edit.clear()

    def __setup_validators(self):

        self.mac_validator = QRegExpValidator(
            QRegExp("[a-zA-Z0-9]{2}:[a-zA-Z0-9]{2}:[a-zA-Z0-9]{2}:[a-zA-Z0-9]{2}:[a-zA-Z0-9]{2}:[a-zA-Z0-9]{2}"),
            None)
        self.mac_address_edit.setValidator(self.mac_validator)

    def get_mac_address(self):

        if sys.platform == 'win32':
            for line in os.popen("ipconfig /all"):
                if line.lstrip().startswith('Physical Address'):
                    mac = line.split(':')[1].strip().replace('-', ':')
                    if len(mac) == 17:
                        mac = line.split(':')[1].strip().replace('-', ':')
                    break
        else:
            for line in os.popen("/sbin/ifconfig"):
                if line.find('Ether') > -1:
                    mac = line.split()[4]
                    if len(mac) == 17:
                        mac = line.split(':')[1].strip().replace('-', ':')
                    break
        return mac


    def get_macaddress(self, host):
        """ Returns the MAC address of a network host, requires >= WIN2K. """
        # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/347812
        import ctypes
        import socket
        import struct

        # Check for api availability
        try:
            SendARP = ctypes.windll.Iphlpapi.SendARP
        except:
            raise NotImplementedError('Usage only on Windows 2000 and above')

        # Doesn't work with loopbacks, but let's try and help.
        if host == '127.0.0.1' or host.lower() == 'localhost':
            host = socket.gethostname()

        # gethostbyname blocks, so use it wisely.
        try:
            inetaddr = ctypes.windll.wsock32.inet_addr(host)
            if inetaddr in (0, -1):
                raise Exception
        except:
            hostip = socket.gethostbyname(host)
            inetaddr = ctypes.windll.wsock32.inet_addr(hostip)

        buffer = ctypes.c_buffer(6)
        addlen = ctypes.c_ulong(ctypes.sizeof(buffer))
        if SendARP(inetaddr, 0, ctypes.byref(buffer), ctypes.byref(addlen)) != 0:
            raise WindowsError('Retreival of mac address(%s) - failed' % host)

        # Convert binary data into a string.
        macaddr = ''
        for intval in struct.unpack('BBBBBB', buffer):
            if intval > 15:
                replacestr = '0x'
            else:
                replacestr = 'x'
            if macaddr != '':
                macaddr = ':'.join([macaddr, hex(intval).replace(replacestr, '')])
            else:
                macaddr = ''.join([macaddr, hex(intval).replace(replacestr, '')])

        return macaddr.upper()

    def __privilage(self):

        if not self.has_privilege:
            self.groupBox_2.setEnabled(False)
            self.add_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.username_edit.setEnabled(False)
            self.phone_edit.setEnabled(False)
            self.surname_edit.setEnabled(False)
            self.firstname_edit.setEnabled(False)
            self.email_edit.setEnabled(False)
            self.position_cbox.setEnabled(False)
            self.mac_address_edit.setEnabled(False)
            self.groupBox_3.setEnabled(False)

    def __setup_combo_boxes(self):

        try:
            positions = self.db_session.query(ClPositionType).all()

            for position in positions:
                self.position_cbox.addItem(position.description, position.code)

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    # def set_username(self, username):
    #
    #     self.__username = username

    def __populate_user_role_lwidget(self):

        self.user_role_lwidget.clear()
        if self.has_privilege:
            users = self.db_session.query(SetRole.user_name).order_by(SetRole.user_name).group_by(SetRole.user_name)
        else:
            users = self.db_session.query(SetRole.user_name).filter(SetRole.user_name == self.__username).group_by(SetRole.user_name).all()

        try:
            for user in users:
                item = QListWidgetItem(QIcon(":/plugins/lm2/person.png"), user.user_name)
                # if user.user_name == self.__logged_on_user():
                item.setForeground(Qt.blue)
                # if self.__is_db_role(user.user_name):
                self.user_role_lwidget.addItem(item)

        except (DatabaseError, SQLAlchemyError), e:
            PluginUtils.show_error(self,  self.tr("Database Error"), e.message)

    def __is_db_role(self, user_name):

        try:
            sql = "SELECT count(*) FROM pg_roles WHERE rolname = '{0}' and rolcanlogin = true".format(user_name)
            count = self.db_session.execute(sql).fetchone()
            return True if count[0] == 1 else False
        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))

    def __populate_group_lwidget(self):

        self.group_lwidget.clear()
        self.member_lwidget.clear()

        QListWidgetItem("land_office_administration", self.group_lwidget)
        QListWidgetItem("db_creation", self.group_lwidget)
        QListWidgetItem("role_management", self.group_lwidget)
        QListWidgetItem(self.GROUP_SEPARATOR, self.group_lwidget)
        QListWidgetItem("application_view", self.group_lwidget)
        QListWidgetItem("application_update", self.group_lwidget)
        QListWidgetItem("cadastre_view", self.group_lwidget)
        QListWidgetItem("cadastre_update", self.group_lwidget)
        QListWidgetItem("contracting_view", self.group_lwidget)
        QListWidgetItem("contracting_update", self.group_lwidget)
        QListWidgetItem("reporting", self.group_lwidget)
        QListWidgetItem("log_view", self.member_lwidget)

    def __populate_au_level1_cbox(self):

        try:
            PluginUtils.populate_au_level1_cbox(self.aimag_cbox, True, False, False)
        except DatabaseError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))

    @pyqtSlot()
    def on_aimag_lwidget_itemSelectionChanged(self):

        try:
            self.soum_cbox.clear()
            self.soum_cbox.addItem("*", "*")
            if self.aimag_lwidget.currentItem() is None:
                return
            # if self.aimag_lwidget.count() > 1:
            #     return

            au_level1_code = self.aimag_lwidget.currentItem().data(Qt.UserRole)

            PluginUtils.populate_au_level2_cbox(self.soum_cbox, au_level1_code, True, False, False)

        except DatabaseError, e:
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))

    @pyqtSlot()
    def on_user_role_lwidget_itemSelectionChanged(self):

        self.selected_user = self.user_role_lwidget.currentItem().text()
        user_name = self.user_role_lwidget.currentItem().text()

        try:
            user_c = self.db_session.query(SetRole). \
                filter(SetRole.user_name == user_name).count()
            if user_c == 1:
                user = self.db_session.query(SetRole). \
                    filter(SetRole.user_name == user_name).one()
            else:
                user = self.db_session.query(SetRole).\
                    filter(SetRole.user_name == user_name).\
                    filter(SetRole.is_active == True).one()
        except NoResultFound:
            return

        self.username_real_lbl.setText(user.user_name_real)
        self.username_edit.setText(user.user_name)
        self.surname_edit.setText(user.surname)
        self.firstname_edit.setText(user.first_name)
        self.email_edit.setText(user.email)
        self.position_cbox.setCurrentIndex(self.position_cbox.findData(user.position))
        # self.position_edit.setText(user.position)
        self.phone_edit.setText(user.phone)
        self.mac_address_edit.setText(user.mac_addresses)
        self.password_edit.setText(self.PW_PLACEHOLDER)
        self.retype_password_edit.setText(self.PW_PLACEHOLDER)
        self.register_edit.setText(user.user_register)
        # populate groups
        self.__populate_group_lwidget()

        groups = self.__groupsByUser(user_name)
        for group in groups:

            group_name = group[0]
            items = self.group_lwidget.findItems(group_name, Qt.MatchExactly)
            if len(items) > 0:
                item = items[0]
                self.member_lwidget.addItem(item.text())
                self.group_lwidget.takeItem(self.group_lwidget.row(item))

        # populate admin units
        self.aimag_lwidget.clear()
        self.soum_lwidget.clear()
        restriction_au_level1 = user.restriction_au_level1
        aimag_codes = restriction_au_level1.split(',')

        try:
            if len(aimag_codes) == self.db_session.query(AuLevel1).count():  # all Aimags
                item = QListWidgetItem("*")
                item.setData(Qt.UserRole, "*")
                self.aimag_lwidget.addItem(item)
                self.soum_lwidget.addItem(item)
            else:
                for code in aimag_codes:
                    code = code.strip()
                    aimag = self.db_session.query(AuLevel1).filter(AuLevel1.code == code).one()
                    item = QListWidgetItem(aimag.name)
                    item.setData(Qt.UserRole, aimag.code)
                    self.aimag_lwidget.addItem(item)

                restriction_au_level2 = user.restriction_au_level2
                soum_codes = restriction_au_level2.split(',')

                # Find districts among the Aimags:
                l1_district_entries = filter(lambda x: x.startswith('1') or x.startswith('01'), aimag_codes)
                l2_district_entries = filter(lambda x: x.startswith('1') or x.startswith('01'), soum_codes)

                true_aimags = filter(lambda x: not x.startswith('1') and not x.startswith('01'), aimag_codes)

                if len(aimag_codes)-len(l1_district_entries) == 1 and \
                        len(soum_codes)-len(l2_district_entries) == self.db_session.query(AuLevel2)\
                                                                    .filter(AuLevel2.code.startswith(true_aimags[0]))\
                                                                    .count():
                    item = QListWidgetItem("*")
                    item.setData(Qt.UserRole, "*")
                    self.soum_lwidget.addItem(item)
                else:
                    for code in soum_codes:
                        code = code.strip()
                        soum = self.db_session.query(AuLevel2).filter(AuLevel2.code == code).one()
                        item = QListWidgetItem(soum.name+'_'+soum.code)
                        item.setData(Qt.UserRole, soum.code)
                        self.soum_lwidget.addItem(item)
        except NoResultFound:
            pass

    def reject(self):

        SessionHandler().destroy_session()
        QDialog.reject(self)

    @pyqtSlot()
    def on_add_button_clicked(self):

        try:
            if self.__add_or_update_role():
                PluginUtils.show_message(self, self.tr("User Role Management"), self.tr('New user created.'))
        except DatabaseError, e:
            self.db_session.rollback()
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))

    @pyqtSlot()
    def on_update_button_clicked(self):

        try:
            if self.__add_or_update_role('UPDATE'):
                PluginUtils.show_message(self, self.tr("User Role Management"), self.tr('User information updated.'))
        except DatabaseError, e:
            self.db_session.rollback()
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))

    def __add_or_update_role(self, mode='ADD'):

        if not self.__validate_user_input(mode):
            return False
        user_name = self.username_edit.text().strip()
        surname = self.surname_edit.text().strip()
        first_name = self.firstname_edit.text().strip()
        user_register = self.register_edit.text().strip()
        phone = self.phone_edit.text().strip()
        # position = self.position_edit.text().strip()
        position = self.position_cbox.itemData(self.position_cbox.currentIndex())
        mac_addresses = self.mac_address_edit.text().strip()
        password = self.password_edit.text().strip()
        email = ''
        if self.email_edit.text():
            email = self.email_edit.text().strip()
        if self.has_privilege:
            try:
                self.db_session.execute("SET ROLE role_management")
            except DatabaseError, e:
                self.db_session.rollback()
                PluginUtils.show_error(self, self.tr("Database Query Error"),
                                       self.tr("You must login different username with member of role management"))
                return

            if mode == 'ADD':

                sql = "SELECT count(*) FROM pg_roles WHERE rolname = '{0}' and rolcanlogin = true".format(user_name)
                count = self.db_session.execute(sql).fetchone()
                if count[0] == 0:
                    self.db_session.execute(u"CREATE ROLE {0} login PASSWORD '{1}'".format(user_name, password))
                else:
                    message_box = QMessageBox()
                    message_box.setText(self.tr("Could not execute: {0} already exists. Do you want to connect selected soums?").format(user_name))
                    yes_button = message_box.addButton(self.tr("Yes"), QMessageBox.ActionRole)
                    message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)

                    message_box.exec_()

                    if not message_box.clickedButton() == yes_button:
                        return
            else:
                if password != self.PW_PLACEHOLDER:
                    self.db_session.execute(u"ALTER ROLE {0} PASSWORD '{1}'".format(user_name, password))

            groups = self.__groupsByUser(user_name)
            for group in groups:
                self.db_session.execute(u"REVOKE {0} FROM {1}".format(group[0], user_name))

            for index in range(self.member_lwidget.count()):

                item = self.member_lwidget.item(index)
                sql = "SELECT count(*) FROM pg_roles WHERE rolname = '{0}' and rolcanlogin = true".format(user_name)
                count = self.db_session.execute(sql).fetchone()
                if count[0] == 0:
                    self.db_session.execute(u"CREATE ROLE {0} login PASSWORD '{1}'".format(user_name, password))
                self.db_session.execute(u"GRANT {0} TO {1}".format(item.text(), user_name))
            self.db_session.execute("RESET ROLE")

            restriction_au_level1 = ''
            restriction_au_level2 = ''
            is_first = 0
            for index in range(self.aimag_lwidget.count()):
                item = self.aimag_lwidget.item(index)
                if item.text() == '*':  # all Aimags
                    for index2 in range(self.aimag_cbox.count()):
                        au_level1_code = str(self.aimag_cbox.itemData(index2, Qt.UserRole))
                        if au_level1_code != '*':
                            restriction_au_level1 += au_level1_code + ','
                            # Special treatment for UB's districts:
                            if au_level1_code.startswith('1') or au_level1_code.startswith('01'):
                                restriction_au_level2 += au_level1_code + '00' + ','
                                self.db_session.execute("SET ROLE role_management")
                                self.db_session.execute(u"GRANT s{0}00 TO {1}".format(au_level1_code, user_name))
                                self.db_session.execute("RESET ROLE")

                        for au_level2 in self.db_session.query(AuLevel2).filter(AuLevel2.code.startswith(au_level1_code))\
                                .order_by(AuLevel2.code):

                            restriction_au_level2 += au_level2.code + ','
                            self.db_session.execute("SET ROLE role_management")
                            self.db_session.execute(u"GRANT s{0} TO {1}".format(au_level2.code, user_name))

                            self.db_session.execute(u"GRANT s{0} TO {1}".format(au_level2.code, user_name))

                            self.db_session.execute("RESET ROLE")
                    break
                else:
                    au_level1_code = str(item.data(Qt.UserRole))
                    restriction_au_level1 += au_level1_code + ','
                    # Special treatment for UB's districts:
                    # if au_level1_code.startswith('1') or au_level1_code.startswith('01'):
                    #     restriction_au_level2 += au_level1_code + '00' + ','
                    #     self.db_session.execute("SET ROLE role_management")
                    #     self.db_session.execute(u"GRANT s{0}00 TO {1}".format(au_level1_code, user_name))
                    #     self.db_session.execute("RESET ROLE")
                    if is_first == 0:
                        is_first = 1
                        for index2 in range(self.soum_lwidget.count()):
                            item = self.soum_lwidget.item(index2)
                            if item.text() == '*':
                                for au_level2 in self.db_session.query(AuLevel2).filter(AuLevel2.code.startswith(au_level1_code))\
                                        .order_by(AuLevel2.code):
                                    restriction_au_level2 += au_level2.code + ','
                                    self.db_session.execute("SET ROLE role_management")
                                    self.db_session.execute(u"GRANT s{0} TO {1}".format(au_level2.code, user_name))

                                    self.db_session.execute("RESET ROLE")
                            else:
                                try:
                                    au_level2_code = str(item.data(Qt.UserRole))
                                    restriction_au_level2 += au_level2_code + ','
                                    self.db_session.execute("SET ROLE role_management")
                                    self.db_session.execute(u"GRANT  s{0} TO {1}".format(au_level2_code, user_name))

                                    self.db_session.execute("RESET ROLE")
                                except DatabaseError, e:
                                    self.db_session.rollback()
                                    PluginUtils.show_error(self, self.tr("Database Query Error"),
                                                           self.tr("You must login different username with member of role management"))
                                    return

            restriction_au_level1 = restriction_au_level1[:len(restriction_au_level1)-1]
            restriction_au_level2 = restriction_au_level2[:len(restriction_au_level2)-1]

            pa_from = datetime.datetime.today()
            pa_till = datetime.date.max
            role_c = self.db_session.query(SetRole).filter(SetRole.user_name == user_name).count()


            if self.register_edit.text() == None or self.register_edit.text() == '':
                PluginUtils.show_message(None, self.tr("None register"),
                                         self.tr("Register not null!"))
                return

            if mode == 'ADD':
                if role_c != 0:
                    role_count = self.db_session.query(SetRole).filter(
                        SetRole.user_register == self.register_edit.text()).count()
                    # if role_count > 0:
                    #     PluginUtils.show_message(None, self.tr("Duplicate user"),
                    #                              self.tr("This user already registered!"))
                        # return
                is_active_user = False
                if role_c == 0:
                    is_active_user = True
                else:
                    active_role_count = self.db_session.query(SetRole).filter(SetRole.user_name == user_name).filter(SetRole.is_active == True).count()
                    if active_role_count == 0:
                        is_active_user = True
                    else:
                        is_active_user = False

                try:
                    count = self.db_session.query(SetRole) \
                        .filter(SetRole.user_name == user_name) \
                        .order_by(func.substr(SetRole.user_name_real, 11, 12).desc()).count()
                except SQLAlchemyError, e:
                    PluginUtils.show_error(self, self.tr("File Error"),
                                           self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
                    return

                if count > 0:
                    try:
                        max_number_user = self.db_session.query(SetRole) \
                            .filter(SetRole.user_name == user_name) \
                            .order_by(func.substr(SetRole.user_name_real, 11, 12).desc()).first()
                    except SQLAlchemyError, e:
                        PluginUtils.show_error(self, self.tr("File Error"),
                                               self.tr("Error in line {0}: {1}").format(currentframe().f_lineno,
                                                                                        e.message))
                        return

                    user_numbers = max_number_user.user_name_real[-2:]
                    new_user_number = (str(int(user_numbers[1]) + 1).zfill(2))

                    last_user_name = user_name[:10] + new_user_number
                    user_name_real = last_user_name
                    employee_type = 2
                else:
                    user_name_real = self.username_edit.text()+'01'
                    employee_type = 1

                role = SetRole(user_name=user_name, surname=surname, first_name=first_name, phone=phone, user_register=user_register,
                               mac_addresses=mac_addresses, position=position, restriction_au_level1=restriction_au_level1, user_name_real = user_name_real,
                               employee_type = employee_type, restriction_au_level2=restriction_au_level2, pa_from=pa_from, pa_till=pa_till, is_active=is_active_user, email=email)
                self.db_session.add(role)
            else:
                active_role_count = self.db_session.query(SetRole).filter(SetRole.user_name == user_name).filter(
                    SetRole.is_active == True).count()
                if active_role_count == 1:
                    role = self.db_session.query(SetRole).filter(SetRole.user_name == user_name).filter(SetRole.is_active == True).one()
                else:
                    role = self.db_session.query(SetRole).filter(SetRole.user_name == user_name).filter(SetRole.user_name_real == self.username_real_lbl.text()).one()
                    # for role in roles:
                    #     print role.user_name_real

                role.surname = surname
                role.first_name = first_name
                role.phone = phone
                role.user_register = user_register
                role.mac_addresses = mac_addresses
                if active_role_count == 0:
                    role.is_active = True
                role.position = position
                role.restriction_au_level1 = restriction_au_level1
                role.restriction_au_level2 = restriction_au_level2
                role.email = email

            self.db_session.commit()
            self.__populate_user_role_lwidget()
            item = self.user_role_lwidget.findItems(user_name, Qt.MatchExactly)[0]
            row = self.user_role_lwidget.row(item)
            self.user_role_lwidget.setCurrentRow(row)
            return True
        else:
            if password != self.PW_PLACEHOLDER:
                self.db_session.execute(u"ALTER ROLE {0} PASSWORD '{1}'".format(user_name, password))
            self.db_session.commit()
            self.__populate_user_role_lwidget()
            item = self.user_role_lwidget.findItems(user_name, Qt.MatchExactly)[0]
            row = self.user_role_lwidget.row(item)
            self.user_role_lwidget.setCurrentRow(row)
            return True

    def __validate_user_input(self, mode='ADD'):

        if mode == 'UPDATE':
            if self.username_edit.text().strip() != self.selected_user:
                PluginUtils.show_message(None, self.tr("Username can't be modified"),
                                        self.tr("The username of an existing user cannot be modified!"))
                self.username_edit.setText(self.selected_user)
                return False

        if self.username_edit.text().strip() == 'role_manager' \
                and not self.member_lwidget.findItems('role_management', Qt.MatchExactly):
            PluginUtils.show_message(self, self.tr("Required group"),
                                    self.tr("The user 'role_manager' must be member of group 'role_management'."))
            return False

        if len(self.username_edit.text().strip()) == 0:
            PluginUtils.show_message(self, self.tr("No Username"), self.tr("Provide a valid username!"))
            return False

        if len(self.password_edit.text().strip()) < 8:
            PluginUtils.show_message(self, self.tr("Invalid Password"),
                                    self.tr("Provide a valid password that consists of 8 characters or more!"))
            return False

        if self.password_edit.text().strip() != self.retype_password_edit.text().strip():
            PluginUtils.show_message(self, self.tr("Passwords Not Matching"),
                                    self.tr("Password and retyped password are not identical!"))
            return False

        if len(self.surname_edit.text().strip()) == 0:
            PluginUtils.show_message(self, self.tr("No Surname"), self.tr("Provide a valid surname!"))
            return False

        if len(self.firstname_edit.text().strip()) == 0:
            PluginUtils.show_message(self, self.tr("No First Name"), self.tr("Provide a valid first name!"))
            return False

        if len(self.email_edit.text().strip()) == 0:
            PluginUtils.show_message(self, self.tr("No Email"), self.tr("Provide a valid email!"))
            return False

        if len(self.firstname_edit.text().strip()) == 0:
            PluginUtils.show_message(self, self.tr("No Position"), self.tr("Provide a valid position!"))
            return False

        if self.member_lwidget.count() == 0:
            PluginUtils.show_message(self, self.tr("No Group Membership"),
                                    self.tr("The user must be member of at least one group!"))
            return False

        if not self.member_lwidget.findItems('role_management', Qt.MatchExactly) \
                and not self.member_lwidget.findItems('db_creation', Qt.MatchExactly):

                if self.aimag_lwidget.count() == 0:
                    PluginUtils.show_message(self, self.tr("No Aimag/Duureg"),
                                            self.tr("The user must be granted at least one Aimag/Duureg!"))
                    return False

                if self.soum_lwidget.count() == 0:
                    PluginUtils.show_message(self, self.tr("No Soum"),
                                            self.tr("The user must granted at least one Soum!"))
                    return False

        return True

    @pyqtSlot()
    def on_down_groups_button_clicked(self):

        if not self.group_lwidget.currentItem():
            return
        group = self.group_lwidget.currentItem().text()
        if group.find(self.GROUP_SEPARATOR) != -1:
            return

        self.group_lwidget.takeItem(self.group_lwidget.row(self.group_lwidget.currentItem()))
        self.member_lwidget.addItem(group)

        if group == 'land_office_administration':
            item_list = self.member_lwidget.findItems('contracting_update', Qt.MatchExactly)
            if len(item_list) == 0:
                contracting_update_item = self.group_lwidget.findItems('contracting_update', Qt.MatchExactly)[0]
                self.group_lwidget.takeItem(self.group_lwidget.row(contracting_update_item))
                self.member_lwidget.addItem(contracting_update_item.text())
        # elif group == 'contracting_update':
        #     item_list = self.member_lwidget.findItems('cadastre_update', Qt.MatchExactly)
        #     if len(item_list) == 0:
        #         cadastre_update_item = self.group_lwidget.findItems('cadastre_update', Qt.MatchExactly)[0]
        #         self.group_lwidget.takeItem(self.group_lwidget.row(cadastre_update_item))
        #         self.member_lwidget.addItem(cadastre_update_item.text())

    @pyqtSlot()
    def on_up_groups_button_clicked(self):

        if not self.member_lwidget.currentItem():
            return
        group = self.member_lwidget.currentItem().text()
        if group == 'log_view':  # cannot be removed from member widget
            return
        self.member_lwidget.takeItem(self.member_lwidget.row(self.member_lwidget.currentItem()))
        if group == 'role_management' or group == 'db_creation' or group == 'land_office_administration':
            self.group_lwidget.insertItem(0, group)
        else:
            self.group_lwidget.addItem(group)

        # if group == 'contracting_update':
        #     item_list = self.group_lwidget.findItems('land_office_administration', Qt.MatchExactly)
        #     if len(item_list) == 0:
        #         land_office_admin_item = self.member_lwidget.findItems('land_office_administration', Qt.MatchExactly)[0]
        #         self.member_lwidget.takeItem(self.member_lwidget.row(land_office_admin_item))
        #         self.group_lwidget.insertItem(0, land_office_admin_item.text())
        # elif group == 'cadastre_update':
        #     item_list = self.group_lwidget.findItems('contracting_update', Qt.MatchExactly)
        #     if len(item_list) == 0:
        #         contracting_update_item = self.member_lwidget.findItems('contracting_update', Qt.MatchExactly)[0]
        #         self.member_lwidget.takeItem(self.member_lwidget.row(contracting_update_item))
        #         self.group_lwidget.addItem(contracting_update_item.text())

    @pyqtSlot()
    def on_down_aimag_button_clicked(self):

        au_level1_name = self.aimag_cbox.currentText()
        au_level1_code = self.aimag_cbox.itemData(self.aimag_cbox.currentIndex(), Qt.UserRole)

        if len(self.aimag_lwidget.findItems(au_level1_name, Qt.MatchExactly)) == 0:
            if len(self.aimag_lwidget.findItems("*", Qt.MatchExactly)) == 0:
                if au_level1_name == '*':
                    self.aimag_lwidget.clear()
                    self.soum_lwidget.clear()
                    item = QListWidgetItem("*")
                    item.setData(Qt.UserRole, "*")
                    self.soum_lwidget.addItem(item)
                item = QListWidgetItem(au_level1_name)
                item.setData(Qt.UserRole, au_level1_code)
                self.aimag_lwidget.addItem(item)
                self.aimag_lwidget.setCurrentItem(item)

        if self.aimag_lwidget.count() > 1:
            self.soum_lwidget.clear()
            item = QListWidgetItem("*")
            item.setData(Qt.UserRole, "*")
            self.soum_lwidget.addItem(item)

    @pyqtSlot()
    def on_up_aimag_button_clicked(self):

        self.aimag_lwidget.takeItem(self.aimag_lwidget.row(self.aimag_lwidget.currentItem()))
        if self.aimag_lwidget.count() > 0:
            self.aimag_lwidget.setItemSelected(self.aimag_lwidget.item(0), False)
            self.aimag_lwidget.setCurrentItem(self.aimag_lwidget.item(0))
        self.soum_lwidget.clear()

    @pyqtSlot()
    def on_down_soum_button_clicked(self):

        au_level2_name = self.soum_cbox.currentText()
        au_level2_code = self.soum_cbox.itemData(self.soum_cbox.currentIndex(), Qt.UserRole)
        itemsList = self.aimag_lwidget.selectedItems()
        if len(self.soum_lwidget.findItems(au_level2_name +'_'+ au_level2_code, Qt.MatchExactly)) == 0:
            if len(self.soum_lwidget.findItems("*", Qt.MatchExactly)) == 0:
                if au_level2_name == '*':
                    self.soum_lwidget.clear()
                item = QListWidgetItem(au_level2_name +'_'+ au_level2_code)
                item.setData(Qt.UserRole, au_level2_code)
                self.soum_lwidget.addItem(item)

    @pyqtSlot()
    def on_up_soum_button_clicked(self):

        self.soum_lwidget.takeItem(self.soum_lwidget.row(self.soum_lwidget.currentItem()))

    @pyqtSlot()
    def on_delete_button_clicked(self):

        item = self.user_role_lwidget.currentItem()
        if item is None:
            return

        user_name = item.text()

        if user_name == 'role_manager':
            PluginUtils.show_message(self, self.tr("Delete User"),
                                     self.tr("The user 'role_manager' is a required role and cannot be deleted."))
            return

        # The user logged on must not delete himself:
        if self.__logged_on_user() == user_name:
            PluginUtils.show_message(self, self.tr("Delete User"),
                                     self.tr("The user currently logged on cannot be deleted."))
            return

        message = "Delete user role {0}".format(user_name)
        if QMessageBox.No == QMessageBox.question(self, self.tr("Delete User Role"),
                                                  message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No):
            return

        try:
            user_role = self.db_session.query(SetRole).filter(SetRole.user_name == user_name).one()
            self.db_session.delete(user_role)
            self.db_session.execute("SET ROLE role_management")
            self.db_session.execute(u"DROP ROLE {0}".format(user_name))
            self.db_session.execute("RESET ROLE")
            self.db_session.commit()
            self.__populate_user_role_lwidget()
            PluginUtils.show_message(self, self.tr("User Role Management"), self.tr('User role deleted.'))

        except DatabaseError, e:
            self.db_session.rollback()
            PluginUtils.show_error(self, self.tr("Database Query Error"), self.tr("Could not execute: {0}").format(e.message))

    def __groupsByUser(self, user_name):

        sql = "select rolname from pg_user join pg_auth_members on (pg_user.usesysid=pg_auth_members.member) " \
              "join pg_roles on (pg_roles.oid=pg_auth_members.roleid) where pg_user.usename=:bindName"
        result = self.db_session.execute(sql, {'bindName': user_name}).fetchall()

        return result

    def __logged_on_user(self):

        result = self.db_session.execute("SELECT USER")
        current_user = result.fetchone()
        return current_user[0]

    @pyqtSlot()
    def on_help_button_clicked(self):

        os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/user_role_management.htm")

    @pyqtSlot(QListWidgetItem)
    def on_user_role_lwidget_itemDoubleClicked(self, item):

        username = item.text()
        dlg = UserRoleManagementDetialDialog(username)
        dlg.exec_()

    @pyqtSlot()
    def on_settings_button_clicked(self):

        if not self.user_role_lwidget.currentItem():
            return
        username = self.user_role_lwidget.currentItem().text()

        dlg = UserRoleManagementDetialDialog(username)
        dlg.exec_()

    def __load_default_ritht_grud(self):

        aa = self.db_session.query(ClGroupRole).all()
        positions = self.db_session.query(ClPositionType).all()

        for position in positions:

            # right_grud = self.db_session.query(SetPositionGroupRole)
            row = self.settings_position_twidget.rowCount()
            self.settings_position_twidget.insertRow(row)
            item = QTableWidgetItem(u'{0}'.format(position.description))
            item.setData(Qt.UserRole, position.code)
            self.settings_position_twidget.setItem(row, 0, item)

    @pyqtSlot()
    def on_load_users_button_clicked(self):

        self.__load_user_roles()

    def __load_user_roles(self):

        self.user_twidget.setRowCount(0)

        user_start = "user" + "%"
        users = self.db_session.query(SetRole).filter(SetRole.user_name.like(user_start)).all()

        for user in users:
            row = self.user_twidget.rowCount()
            self.user_twidget.insertRow(row)
            full_name = '('+ user.user_name_real +') '+ user.surname[:1] + '.' + user.first_name
            item = QTableWidgetItem(u'{0}'.format(full_name))
            item.setData(Qt.UserRole, user.user_name_real)
            self.user_twidget.setItem(row, 0, item)

    @pyqtSlot()
    def on_load_position_button_clicked(self):

        self.__load_all_positions()

    def __load_all_positions(self):

        self.position_twidget.setRowCount(0)

        selected_items = self.user_twidget.selectedItems()

        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please select user."))
            return

        cur_row = self.user_twidget.currentRow()
        item = self.user_twidget.item(cur_row, 0)
        user_name_real = item.data(Qt.UserRole)

        positions = self.db_session.query(ClPositionType).all()

        for position in positions:
            row = self.position_twidget.rowCount()
            self.position_twidget.insertRow(row)

            user_positions_count = self.db_session.query(SetUserPosition).\
                filter(SetUserPosition.user_name_real == user_name_real).\
                filter(SetUserPosition.position == position.code).count()

            item = QTableWidgetItem(u'{0}'.format(position.description))
            item.setData(Qt.UserRole, position.code)
            if user_positions_count == 0:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
            self.position_twidget.setItem(row, 0, item)

    @pyqtSlot(QTableWidgetItem)
    def on_user_twidget_itemClicked(self, item):

        self.position_twidget.setRowCount(0)
        self.right_grud_twidget.setRowCount(0)

        cur_row = self.user_twidget.currentRow()
        item = self.user_twidget.item(cur_row, 0)
        user_name_real = item.data(Qt.UserRole)

        self.__load_user_positions(user_name_real)
        self.__load_user_right_types(user_name_real)

    def __load_user_right_types(self, user_name_real):

        right_types = self.db_session.query(ClGroupRole).all()

        for right_type in right_types:
            user_right_types_count = self.db_session.query(SetUserGroupRole). \
                filter(SetUserGroupRole.user_name_real == user_name_real).\
                filter(SetUserGroupRole.group_role == right_type.code).count()
            if user_right_types_count == 1:
                user_right_type = self.db_session.query(SetUserGroupRole). \
                    filter(SetUserGroupRole.user_name_real == user_name_real). \
                    filter(SetUserGroupRole.group_role == right_type.code).one()
            row = self.right_grud_twidget.rowCount()
            self.right_grud_twidget.insertRow(row)

            item = QTableWidgetItem(u'{0}'.format(right_type.description))
            item.setData(Qt.UserRole, right_type.code)
            self.right_grud_twidget.setItem(row, 0, item)

            item = QTableWidgetItem()
            item.setData(Qt.UserRole, right_type.code)
            if user_right_types_count == 0:
                item.setCheckState(Qt.Unchecked)
            else:
                if not user_right_type.r_view:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
            self.right_grud_twidget.setItem(row, 1, item)

            item = QTableWidgetItem()
            item.setData(Qt.UserRole, right_type.code)
            if user_right_types_count == 0:
                item.setCheckState(Qt.Unchecked)
            else:
                if not user_right_type.r_add:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
            self.right_grud_twidget.setItem(row, 2, item)

            item = QTableWidgetItem()
            item.setData(Qt.UserRole, right_type.code)
            if user_right_types_count == 0:
                item.setCheckState(Qt.Unchecked)
            else:
                if not user_right_type.r_remove:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
            self.right_grud_twidget.setItem(row, 3, item)

            item = QTableWidgetItem()
            item.setData(Qt.UserRole, right_type.code)
            if user_right_types_count == 0:
                item.setCheckState(Qt.Unchecked)
            else:
                if not user_right_type.r_update:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
            self.right_grud_twidget.setItem(row, 4, item)


    def __load_user_positions(self, user_name_real):

        user_positions = self.db_session.query(SetUserPosition). \
            filter(SetUserPosition.user_name_real == user_name_real).all()

        set_role = self.db_session.query(SetRole).filter(SetRole.user_name_real == user_name_real).one()

        position = self.db_session.query(ClPositionType). \
            filter(ClPositionType.code == set_role.position).one()

        user_positions_count = self.db_session.query(SetUserPosition). \
            filter(SetUserPosition.user_name_real == user_name_real). \
            filter(SetUserPosition.position == position.code).count()
        if user_positions_count == 0:

            row = self.position_twidget.rowCount()
            self.position_twidget.insertRow(row)

            item = QTableWidgetItem(u'{0}'.format(position.description))
            item.setData(Qt.UserRole, position.code)
            item.setCheckState(Qt.Checked)
            self.position_twidget.setItem(row, 0, item)

        for user_position in user_positions:
            position = self.db_session.query(ClPositionType). \
                filter(ClPositionType.code == user_position.position).one()
            row = self.position_twidget.rowCount()
            self.position_twidget.insertRow(row)

            user_positions_count = self.db_session.query(SetUserPosition). \
                filter(SetUserPosition.user_name_real == user_name_real). \
                filter(SetUserPosition.position == position.code).count()

            item = QTableWidgetItem(u'{0}'.format(position.description))
            item.setData(Qt.UserRole, position.code)
            if user_positions_count == 0:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
            self.position_twidget.setItem(row, 0, item)

    @pyqtSlot()
    def on_load_default_settings_button_clicked(self):

        self.right_grud_twidget.setRowCount(0)

        cur_row = self.user_twidget.currentRow()
        item = self.user_twidget.item(cur_row, 0)
        user_name_real = item.data(Qt.UserRole)

        user = self.db_session.query(SetRole).filter_by(user_name_real = user_name_real).one()
        position_code = user.position

        position_gruds = self.db_session.query(SetPositionGroupRole). \
            filter(SetPositionGroupRole.position == position_code).all()

        for position_grud in position_gruds:
            group_role = self.db_session.query(ClGroupRole).filter(ClGroupRole.code == position_grud.group_role).one()
            row = self.right_grud_twidget.rowCount()
            self.right_grud_twidget.insertRow(row)

            item = QTableWidgetItem(u'{0}'.format(group_role.description))
            item.setData(Qt.UserRole, group_role.code)
            self.right_grud_twidget.setItem(row, 0, item)

            item = QTableWidgetItem()
            item.setData(Qt.UserRole, group_role.code)
            if not position_grud.r_view:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
            self.right_grud_twidget.setItem(row, 1, item)

            item = QTableWidgetItem()
            item.setData(Qt.UserRole, group_role.code)
            if not position_grud.r_add:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
            self.right_grud_twidget.setItem(row, 2, item)

            item = QTableWidgetItem()
            item.setData(Qt.UserRole, group_role.code)
            if not position_grud.r_remove:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
            self.right_grud_twidget.setItem(row, 3, item)

            item = QTableWidgetItem()
            item.setData(Qt.UserRole, group_role.code)
            if not position_grud.r_update:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
            self.right_grud_twidget.setItem(row, 4, item)

    @pyqtSlot(QTableWidgetItem)
    def on_settings_position_twidget_itemClicked(self, item):

        self.settings_right_grud_twidget.setRowCount(0)

        cur_row = self.settings_position_twidget.currentRow()
        item = self.settings_position_twidget.item(cur_row, 0)
        position_code = item.data(Qt.UserRole)


        position_gruds = self.db_session.query(SetPositionGroupRole).\
            filter(SetPositionGroupRole.position == position_code).all()
        group_roles = self.db_session.query(ClGroupRole).all()
        for group_role in group_roles:
            position_grud_c = self.db_session.query(SetPositionGroupRole). \
                filter(SetPositionGroupRole.position == position_code). \
                filter(SetPositionGroupRole.group_role == group_role.code).count()
            if position_grud_c == 1:
                position_grud = self.db_session.query(SetPositionGroupRole). \
                    filter(SetPositionGroupRole.position == position_code).\
                    filter(SetPositionGroupRole.group_role == group_role.code).one()
                row = self.settings_right_grud_twidget.rowCount()
                self.settings_right_grud_twidget.insertRow(row)

                item = QTableWidgetItem(u'{0}'.format(group_role.description_en))
                item.setData(Qt.UserRole, group_role.code)
                self.settings_right_grud_twidget.setItem(row, 0, item)

                item = QTableWidgetItem(u'{0}'.format(group_role.description))
                item.setData(Qt.UserRole, group_role.code)
                self.settings_right_grud_twidget.setItem(row, 1, item)

                item = QTableWidgetItem()
                item.setData(Qt.UserRole, group_role.code)
                if not position_grud.r_view:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                self.settings_right_grud_twidget.setItem(row, 2, item)

                item = QTableWidgetItem()
                item.setData(Qt.UserRole, group_role.code)
                if not position_grud.r_add:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                self.settings_right_grud_twidget.setItem(row, 3, item)

                item = QTableWidgetItem()
                item.setData(Qt.UserRole, group_role.code)
                if not position_grud.r_remove:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                self.settings_right_grud_twidget.setItem(row, 4, item)

                item = QTableWidgetItem()
                item.setData(Qt.UserRole, group_role.code)
                if not position_grud.r_update:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                self.settings_right_grud_twidget.setItem(row, 5, item)
            else:

                row = self.settings_right_grud_twidget.rowCount()
                self.settings_right_grud_twidget.insertRow(row)

                item = QTableWidgetItem(u'{0}'.format(group_role.description_en))
                item.setData(Qt.UserRole, group_role.code)
                self.settings_right_grud_twidget.setItem(row, 0, item)

                item = QTableWidgetItem(u'{0}'.format(group_role.description))
                item.setData(Qt.UserRole, group_role.code)
                self.settings_right_grud_twidget.setItem(row, 1, item)

                item = QTableWidgetItem()
                item.setData(Qt.UserRole, group_role.code)
                item.setCheckState(Qt.Unchecked)

                self.settings_right_grud_twidget.setItem(row, 2, item)

                item = QTableWidgetItem()
                item.setData(Qt.UserRole, group_role.code)
                item.setCheckState(Qt.Unchecked)

                self.settings_right_grud_twidget.setItem(row, 3, item)

                item = QTableWidgetItem()
                item.setData(Qt.UserRole, group_role.code)
                item.setCheckState(Qt.Unchecked)

                self.settings_right_grud_twidget.setItem(row, 4, item)

                item = QTableWidgetItem()
                item.setData(Qt.UserRole, group_role.code)
                item.setCheckState(Qt.Unchecked)

                self.settings_right_grud_twidget.setItem(row, 5, item)

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

    def __save_settings(self):

        try:
            self.__save_right_settings()
            self.__save_user_positions()
            self.__save_user_right_type()
            return True
        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
            return False

    def __save_user_right_type(self):

        selected_items = self.user_twidget.selectedItems()

        if len(selected_items) == 0:
            return

        cur_row = self.user_twidget.currentRow()
        item = self.user_twidget.item(cur_row, 0)
        user_name_real = item.data(Qt.UserRole)

        for row in range(self.right_grud_twidget.rowCount()):
            check_item = self.right_grud_twidget.item(row, 0)
            group_role = check_item.data(Qt.UserRole)
            user_right_count = self.db_session.query(SetUserGroupRole).\
                filter(SetUserGroupRole.group_role == group_role) .\
                filter(SetUserGroupRole.user_name_real == user_name_real).count()

            check_view_item = self.right_grud_twidget.item(row, 1)
            check_add_item = self.right_grud_twidget.item(row, 2)
            check_delete_item = self.right_grud_twidget.item(row, 3)
            check_update_item = self.right_grud_twidget.item(row, 4)

            if user_right_count == 0:
                user_right = SetUserGroupRole()
                user_right.user_name_real = user_name_real
                user_right.group_role = group_role
                if check_view_item.checkState() == Qt.Checked:
                    user_right.r_view = True
                else:
                    user_right.r_view = False

                if check_add_item.checkState() == Qt.Checked:
                    user_right.r_add = True
                else:
                    user_right.r_add = False

                if check_delete_item.checkState() == Qt.Checked:
                    user_right.r_remove = True
                else:
                    user_right.r_remove = False

                if check_update_item.checkState() == Qt.Checked:
                    user_right.r_update = True
                else:
                    user_right.r_update = False
                self.db_session.add(user_right)
            else:
                if user_right_count == 1:
                    user_right = self.db_session.query(SetUserGroupRole). \
                        filter(SetUserGroupRole.group_role == group_role). \
                        filter(SetUserGroupRole.user_name_real == user_name_real).one()
                    if check_view_item.checkState() == Qt.Checked:
                        user_right.r_view = True
                    else:
                        user_right.r_view = False

                    if check_add_item.checkState() == Qt.Checked:
                        user_right.r_add = True
                    else:
                        user_right.r_add = False

                    if check_delete_item.checkState() == Qt.Checked:
                        user_right.r_remove = True
                    else:
                        user_right.r_remove = False

                    if check_update_item.checkState() == Qt.Checked:
                        user_right.r_update = True
                    else:
                        user_right.r_update = False

    def __save_user_positions(self):

        selected_items = self.user_twidget.selectedItems()

        if len(selected_items) == 0:
            return

        cur_row = self.user_twidget.currentRow()
        item = self.user_twidget.item(cur_row, 0)
        user_name_real = item.data(Qt.UserRole)

        for row in range(self.position_twidget.rowCount()):
            check_item = self.position_twidget.item(row, 0)
            position_code = check_item.data(Qt.UserRole)
            user_positions_count = self.db_session.query(SetUserPosition).\
                filter(SetUserPosition.position == position_code) .\
                filter(SetUserPosition.user_name_real == user_name_real).count()
            if check_item.checkState() == Qt.Checked:
                if user_positions_count == 0:
                    user_position = SetUserPosition()
                    user_position.user_name_real = user_name_real
                    user_position.position = position_code
                    self.db_session.add(user_position)
            else:
                if user_positions_count == 1:
                    self.db_session.query(SetUserPosition). \
                        filter(SetUserPosition.position == position_code). \
                        filter(SetUserPosition.user_name_real == user_name_real).delete()

    def __save_right_settings(self):

        selected_items = self.settings_position_twidget.selectedItems()

        if len(selected_items) == 0:
            return

        cur_row = self.settings_position_twidget.currentRow()
        item = self.settings_position_twidget.item(cur_row, 0)
        position_code = item.data(Qt.UserRole)

        for row in range(self.settings_right_grud_twidget.rowCount()):
            group_role = self.settings_right_grud_twidget.item(row, 0).data(Qt.UserRole)

            position_gruds_c = self.db_session.query(SetPositionGroupRole). \
                filter(SetPositionGroupRole.position == position_code). \
                filter(SetPositionGroupRole.group_role == group_role).count()
            if position_gruds_c == 1:
                position_gruds = self.db_session.query(SetPositionGroupRole).\
                    filter(SetPositionGroupRole.position == position_code). \
                    filter(SetPositionGroupRole.group_role == group_role).one()

                check_view_item = self.settings_right_grud_twidget.item(row, 2)
                check_add_item = self.settings_right_grud_twidget.item(row, 3)
                check_delete_item = self.settings_right_grud_twidget.item(row, 4)
                check_update_item = self.settings_right_grud_twidget.item(row, 5)

                if check_view_item.checkState() == Qt.Checked:
                    position_gruds.r_view = True
                else:
                    position_gruds.r_view = False

                if check_add_item.checkState() == Qt.Checked:
                    position_gruds.r_add = True
                else:
                    position_gruds.r_add = False

                if check_delete_item.checkState() == Qt.Checked:
                    position_gruds.r_remove = True
                else:
                    position_gruds.r_remove = False

                if check_update_item.checkState() == Qt.Checked:
                    position_gruds.r_update = True
                else:
                    position_gruds.r_update = False
            else:
                position_gruds = SetPositionGroupRole()

                position_gruds.group_role = group_role
                position_gruds.position = position_code

                check_view_item = self.settings_right_grud_twidget.item(row, 2)
                check_add_item = self.settings_right_grud_twidget.item(row, 3)
                check_delete_item = self.settings_right_grud_twidget.item(row, 4)
                check_update_item = self.settings_right_grud_twidget.item(row, 5)

                if check_view_item.checkState() == Qt.Checked:
                    position_gruds.r_view = True
                else:
                    position_gruds.r_view = False

                if check_add_item.checkState() == Qt.Checked:
                    position_gruds.r_add = True
                else:
                    position_gruds.r_add = False

                if check_delete_item.checkState() == Qt.Checked:
                    position_gruds.r_remove = True
                else:
                    position_gruds.r_remove = False

                if check_update_item.checkState() == Qt.Checked:
                    position_gruds.r_update = True
                else:
                    position_gruds.r_update = False

                self.db_session.add(position_gruds)


    @pyqtSlot()
    def on_apply_button_clicked(self):

        if not self.__save_settings():
            return

        self.db_session.commit()
        self.__start_fade_out_timer()
