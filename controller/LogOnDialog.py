import os

__author__ = 'Topmap'

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sqlalchemy.exc import DatabaseError, SQLAlchemyError
from inspect import currentframe

from ..view.Ui_LogOnDialog import *
from ..model.Enumerations import UserRight
from ..model import SettingsConstants
from ..model import Constants
from ..controller.UserRoleManagementDialog import *
from ..controller.LandOfficeAdministrativeSettingsDialog import *
from ..controller.ConnectionToMainDatabaseDialog import *
from ..model.DialogInspector import DialogInspector
from ..utils.SessionHandler import SessionHandler
from ..utils.PluginUtils import PluginUtils


class LogOnDialog(QDialog, Ui_LogOnDialog):

    def __init__(self, protected_dialog, parent=None):

        super(LogOnDialog,  self).__init__(parent)
        self.setupUi(self)
        self.protected_dialog = protected_dialog
        if protected_dialog == 10:
            self.setWindowTitle(self.tr("Log On To Database"))
        elif protected_dialog == 20:
            self.setWindowTitle(self.tr("Land Officer Settings"))
        self.__has_contracting_update_privilege = False

        database_name = QSettings().value(SettingsConstants.DATABASE_NAME, "")
        host = QSettings().value(SettingsConstants.HOST, "")
        port = QSettings().value(SettingsConstants.PORT, "5432")
        self.port_edit.setText(port)
        self.database_edit.setText(database_name)
        self.server_edit.setText(host)

        self.port_edit.setValidator(QIntValidator(1000,  6000, self.port_edit))

        if len(self.database_edit.text()) > 0 and len(self.port_edit.text()) > 0 and len(self.server_edit.text()) > 0:
            self.user_edit.setFocus()
        self.logon_button.setDefault(True)

        self.__protected_dialog = protected_dialog
        self.close_button.clicked.connect(self.reject)

        reg_ex = QRegExp(u"[a-z0-9_]+")
        validator = QRegExpValidator(reg_ex, None)
        self.password_edit.setValidator(validator)
        self.mac_addr = self.get_mac_address()

    @pyqtSignature("")
    def on_logon_button_clicked(self):

        host = self.server_edit.text().strip()
        port = self.port_edit.text().strip()

        database = self.database_edit.text().strip()
        user = self.user_edit.text().strip()
        password = self.password_edit.text().strip()

        if not self.__validate_user_input(host, port, database, user, password):
            return

        try:
            if not SessionHandler().create_session(user, password, host, port, database):
                return

        except (DatabaseError, SQLAlchemyError), e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("User name or password is not correct!!!"))
            return
        session = SessionHandler().session_instance()
        groups = self.__groupsByUser(user)
        is_role_manager = False
        for group in groups:
            group_name = group[0]
            if group_name == 'role_management':
                is_role_manager = True
                break

        setRole = session.query(SetRole).filter(SetRole.user_name == user).filter(SetRole.is_active == True).one()
        mac_address = setRole.mac_addresses

        if self.protected_dialog == 10:
            if mac_address != self.mac_addr and not is_role_manager:
                PluginUtils.show_error(self, self.tr("Query Error"),
                                       self.tr("You are not permitted use for this PC !!!"))
                return
        else:
            if mac_address != self.mac_addr:
                PluginUtils.show_error(self, self.tr("Query Error"),
                                       self.tr("You are not permitted use for this PC !!!"))
                return

        if setRole.pa_till < QDate.currentDate().toPyDate():
            PluginUtils.show_error(self, self.tr("User Error"),
                                   self.tr("Your login has expired. Please extend it !!!"))
            return
        session = SessionHandler().session_instance()
        setRole = session.query(SetRole).filter(SetRole.user_name == user).filter(
            SetRole.is_active == True).one()
        auLevel2List = setRole.restriction_au_level2.split(",")
        schemaList = []

        for auLevel2 in auLevel2List:
            auLevel2 = auLevel2.strip()
            schemaList.append("s" + auLevel2)

        schema_string = ",".join(schemaList)

        session.execute("SET search_path to base, codelists, admin_units, settings, public, data_soums_union, sdplatform"+ ", " + schema_string)
        sql = "select rolname from pg_user join pg_auth_members on (pg_user.usesysid=pg_auth_members.member) " \
              "join pg_roles on (pg_roles.oid=pg_auth_members.roleid) where pg_user.usename=:bindName"

        result = session.execute(sql, {'bindName': user}).fetchall()
        if len(result) == 0:
            PluginUtils.show_error(self, self.tr("Invalid input"), self.tr("The user {0} does not exist.").format(user))
            return

        has_privilege = False
        has_privilege_office =False
        self.__has_contracting_update_privilege = False

        for group in result:

            if self.__protected_dialog == Constants.ROLE_MANAGEMENT_DLG:
                if group[0] == UserRight.role_management:
                    has_privilege = True
                    break
            else:
                if group[0] == UserRight.land_office_admin:
                    has_privilege_office = True
                    break

        if self.protected_dialog == 10:
            # if DialogInspector().dialog_visible():
            #     return

            # record = self.__selected_record()
            if not has_privilege:
                if self.__protected_dialog == Constants.ROLE_MANAGEMENT_DLG:
                    PluginUtils.show_error(self, self.tr("No Privilege"),
                                           self.tr("The user has no privileges to perform "
                                                   "role management!"))
                    return

            dialog = UserRoleManagementDialog(has_privilege, user)
            # dialog.rejected.connect(self.reject)
            # DialogInspector().set_dialog_visible(True)
            # dialog.set_username(user)
            dialog.exec_()
            dialog.rejected.connect(self.reject)

        else:
            if not has_privilege_office:
                if self.__protected_dialog == Constants.LAND_ADMIN_SETTINGS_DLG:
                    PluginUtils.show_error(self, self.tr("No Privilege"),
                                       self.tr("The user has no privileges to perform "
                                               "land administration settings!"))
                    return
            dialog = LandOfficeAdministrativeSettingsDialog()
            dialog.exec_()
            dialog.rejected.connect(self.reject)

        session.commit()

        QDialog.accept(self)


    def __groupsByUser(self, user_name):

        session = SessionHandler().session_instance()
        sql = "select rolname from pg_user join pg_auth_members on (pg_user.usesysid=pg_auth_members.member) " \
              "join pg_roles on (pg_roles.oid=pg_auth_members.roleid) where pg_user.usename=:bindName"
        result = session.execute(sql, {'bindName': user_name}).fetchall()

        return result

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

    @pyqtSignature("")
    def reject(self):

        QDialog.reject(self)

    def __validate_user_input(self, host, port, database, user, password):

        # TODO: all the tests
        #the username, database needs to be checked in the create_session function
        if not port.isdigit():
            PluginUtils.show_error(self, self.tr("Wrong Parameter"), self.tr("Enter a valid port number!"))
            return False
        if not password:
            PluginUtils.show_error(self, self.tr("Wrong Parameter"), self.tr("Enter a valid password !"))
            return False
        if not database:
            PluginUtils.show_error(self, self.tr("Wrong Parameter"), self.tr("Enter a valid database !"))
            return False
        if not user:
            PluginUtils.show_error(self, self.tr("Wrong Parameter"), self.tr("Enter a valid user !"))
            return False
        if not host:
            PluginUtils.show_error(self, self.tr("Wrong Parameter"), self.tr("Enter a valid host !"))
            return False
        return True

    @pyqtSlot()
    def on_help_button_clicked(self):

        if self.protected_dialog == 10:
            os.system("hh.exe "+ str(os.path.dirname(os.path.realpath(__file__))[:-10]) +"help\output\help_lm2.chm::/html/Log_On_User_Role_Management.htm")
        else:
            os.system("hh.exe " + str(os.path.dirname(os.path.realpath(__file__))[
                                      :-10]) + "help\output\help_lm2.chm::/html/Log_On_To_Administrative_Settings.htm")