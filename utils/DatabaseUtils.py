# !/usr/bin/python
# -*- coding: utf-8
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sqlalchemy import exc
from sqlalchemy.exc import DatabaseError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from datetime import date, datetime
from ..model.DialogInspector import DialogInspector
from ..controller.ConnectionToMainDatabaseDialog import *
from .SessionHandler import SessionHandler
from ..model import SettingsConstants
from ..model.Enumerations import UserRight
from ..model.CaParcel import CaParcel
from ..model.CtApplication import CtApplication
from ..model.CaTmpBuilding import CaTmpBuilding
from ..model.CaTmpParcel import CaTmpParcel
from ..model.LM2Exception import LM2Exception
from ..model.CtApplicationStatus import *
from ..model.CaMaintenanceCase import *
from ..model import Constants
from ..LM2Plugin import *

class DatabaseUtils():

    def __init__(self):
        pass

    @staticmethod
    def userright_by_name(user_name):

        session = SessionHandler().session_instance()
        convRights = []

        try:
            sql = "select rolname from pg_user join pg_auth_members on (pg_user.usesysid=pg_auth_members.member) " \
                  "join pg_roles on (pg_roles.oid=pg_auth_members.roleid) where pg_user.usename=:bindName;"

            result = session.execute(sql, {'bindName': user_name}).fetchall()

            for right_result in result:

                if right_result[0] == UserRight.cadastre_view:
                    convRights.append(UserRight.cadastre_view)
                elif right_result[0] == UserRight.cadastre_update:
                    convRights.append(UserRight.cadastre_update)
                elif right_result[0] == UserRight.contracting_update:
                    convRights.append(UserRight.contracting_update)
                elif right_result[0] == UserRight.contracting_view:
                    convRights.append(UserRight.contracting_view)
                elif right_result[0] == UserRight.land_office_admin:
                    convRights.append(UserRight.land_office_admin)
                elif right_result[0] == UserRight.reporting:
                    convRights.append(UserRight.reporting)
                elif right_result[0] == UserRight.application_update:
                    convRights.append(UserRight.application_update)
                elif right_result[0] == UserRight.application_view:
                    convRights.append(UserRight.application_view)
            
        except exc.SQLAlchemyError, e:
            session.rollback()
            raise LM2Exception(QApplication.translate("LM2", "Database Query Error"),
                               QApplication.translate("LM2", "Could not execute: {0}").format(e.message))

        return convRights

    @staticmethod
    def current_user():

        try:
            session = SessionHandler().session_instance()
            user = QSettings().value(SettingsConstants.USER)
            if not session:
                QMessageBox.information(None, QApplication.translate("LM2", "Role Error"),
                                        QApplication.translate("LM2", "No User Connection To Main Database"))
                if DialogInspector().dialog_visible():
                    return

                # dlg = ConnectionToMainDatabaseDialog()

                DialogInspector().set_dialog_visible(True)
                #dlg.rejected.connect(self.on_current_dialog_rejected)
                # dlg.exec_()

                SessionHandler().destroy_session()

                #self.__update_database_connection(dlg.get_password())

            else:
                set_role_count = session.query(SetRole).filter(SetRole.user_name == user).filter(SetRole.is_active == True).count()
                if set_role_count == 0:
                    QMessageBox.information(None, QApplication.translate("LM2", "Role Error"),
                                            QApplication.translate("LM2", "No User Connection To Main Database"))
                    return
                else:
                    set_role = session.query(SetRole).filter(SetRole.user_name == user).filter(SetRole.is_active == True).one()
                    return set_role

        except exc.SQLAlchemyError, e:
            QMessageBox.information(None, QApplication.translate("LM2", "Database Query Error"),
                               QApplication.translate("LM2", "Could not execute: {0}").format(e.message))

    @staticmethod
    def codelist_by_name(schema, name, primary, description):

        session = SessionHandler().session_instance()
        lookup = {}
        try:
            sql = "Select {0}, {1} from {2}.{3};".format(primary, description, schema, name)
            result = session.execute(sql).fetchall()

            for row in result:
                lookup[row[0]] = row[1]

        except exc.SQLAlchemyError, e:
            raise LM2Exception(QApplication.translate("LM2", "Database Query Error"),
                               QApplication.translate("LM2", "Could not execute: {0}").format(e.message))

        return lookup

    @staticmethod
    def role_settings(name):

        user_setting_result = None
        session = SessionHandler().session_instance()

        try:
            user_setting_result = session.query(SetRole).filter_by(user_name=name).filter(SetRole.is_active == True).one()
            session.commit()
        except exc.SQLAlchemyError, e:
            session.rollback()
            raise LM2Exception(QApplication.translate("LM2", "Database Query Error"),
                               QApplication.translate("LM2", "Could not execute: {0}").format(e.message))

        return user_setting_result

    @staticmethod
    def class_instance_by_code(class_obj, code):

        session = SessionHandler().session_instance()
        class_instance = None

        try:
            class_instance = session.query(class_obj).filter(class_obj.code == code).one()
        except exc.SQLAlchemyError, e:
            session.rollback()
            raise LM2Exception(QApplication.translate("LM2", "Database Query Error"),
                               QApplication.translate("LM2", "Could not execute: {0}").format(e.message))

        return class_instance

    @staticmethod
    def convert_date(date_obj):

        return date(date_obj.year(), date_obj.month(), date_obj.day())

    @staticmethod
    def l1_restriction_array():

        is_current_user = True
        role = DatabaseUtils.current_user()
        if role == None:
            is_current_user = False
        l1_code_list = ""
        if is_current_user == False:
            QMessageBox.information(None, QApplication.translate("LM2", "Role Error"),
                                        QApplication.translate("LM2", "No User Connection To Main Database"))
            l1_code_list = "0000"
        else:
            l1_code_list = role.restriction_au_level1.split(',')
        return l1_code_list

    @staticmethod
    def l2_restriction_array():

        is_current_user = True
        role = DatabaseUtils.current_user()
        if role == None:
            is_current_user = False
        l2_code_list = ""
        if is_current_user == False:
            QMessageBox.information(None, QApplication.translate("LM2", "Role Error"),
                                        QApplication.translate("LM2", "No User Connection To Main Database"))
            l2_code_list = "0000"
        else:
            l2_code_list = role.restriction_au_level2.split(',')
        return l2_code_list

    @staticmethod
    def working_l1_code():

        try:
            role = DatabaseUtils.current_user()
            if role:
                return role.working_au_level1
            else:
                QMessageBox.information(None, QApplication.translate("LM2", "Database disconnect"),
                                        QApplication.translate("LM2",
                                                               "Please connect to database!!!"))
                return
        except DatabaseError, e:
            raise LM2Exception(QApplication.translate("Connection Error"),
                               QApplication.translate("Plugin", "Database disconnected!"))

    @staticmethod
    def working_l2_code():

        is_session = True
        try:
            role = DatabaseUtils.current_user()
            if role:
                return role.working_au_level2
            else:
                QMessageBox.information(None, QApplication.translate("LM2", "Database disconnect"),
                                        QApplication.translate("LM2",
                                                               "Please connect to database!!!"))
                is_session = False

        except DatabaseError, e:
            raise LM2Exception(QApplication.translate("Connection Error"),
                               QApplication.translate("Plugin", "Database disconnected!"))

        if not is_session:
            database = QSettings().value(SettingsConstants.DATABASE_NAME)
            host = QSettings().value(SettingsConstants.HOST)
            port = QSettings().value(SettingsConstants.PORT, "5432")
            user = QSettings().value(SettingsConstants.USER)

            text, ok = QtGui.QInputDialog.getText(None, "QInputDialog.getText()",
                                                  "user password:", QtGui.QLineEdit.Password)
            password = text
            try:
                if not SessionHandler().create_session(user, password, host, port, database):
                    return
            except SQLAlchemyError, e:
                return

    @staticmethod
    def current_working_soum_schema():

        w_au_level2 = DatabaseUtils.working_l2_code()
        w_au_level1 = DatabaseUtils.working_l1_code()

        # In case of a district the level2 is empty
        if w_au_level2 is None:
            return w_au_level1 + "00"
        else:
            return w_au_level2

    @staticmethod
    def set_working_schema(first_code=None):

        session = SessionHandler().session_instance()
        if not session:
            QMessageBox.information(None, QApplication.translate("LM2", "Database disconnect"),
                                    QApplication.translate("LM2",
                                                           "Please connect to database!!!"))
            return
        if first_code is None:
            first_code = DatabaseUtils.current_working_soum_schema()

        try:
            session.begin_nested()
            l1_working_code = DatabaseUtils.working_l1_code()

            #in case of districts - sort after l1 code
            if l1_working_code[:2] == "01":
                search_path_array = DatabaseUtils.l2_restriction_array()
            else:
                search_path_array = DatabaseUtils.l2_restriction_array()

            found_code = False
            schema_list = []

            for item in search_path_array:
                au_level2 = item.strip()

                if item == first_code:
                    found_code = True
                else:
                    schema_list.append("s" + au_level2)

            if found_code:
                schema_list.insert(0, "s" + first_code.strip())

            session.execute("SET search_path to base, codelists, ub_data, admin_units, settings, pasture, public" + ", " + ", ".join(schema_list))
            session.commit()

        except DatabaseError, e:
            session.rollback()
            raise LM2Exception(QApplication.translate("LM2", "Database Query Error"),
                               QApplication.translate("LM2", "Could not execute: {0}").format(e.message))

    @staticmethod
    def file_data(file_path):

        current_file = QFile(file_path)
        if not current_file.open(QIODevice.ReadOnly):
            raise LM2Exception(QApplication.translate("File Error"),
                               QApplication.translate("Plugin", "Could not open/read File: {0}").format(file_path))

        byte_array = current_file.readAll()

        return byte_array

    @staticmethod
    def update_application_status():

        session = SessionHandler().session_instance()
        stati = session.query(CtApplicationStatus.application, func.max(CtApplicationStatus.status_date))\
                        .group_by(CtApplicationStatus.application)\
                        .having(func.max(CtApplicationStatus.status) == Constants.APP_STATUS_WAITING).distinct()

        current_user = DatabaseUtils.current_user()
        app_no_without_parcel = []

        for application, cu_date in stati:
            application_instance = session.query(CtApplication).filter(CtApplication.app_no == application).one()

            if application_instance.parcel is None:
                app_no_without_parcel.append(application_instance.app_no)

                continue

            new_status = CtApplicationStatus()
            new_status.application = application
            new_status.next_officer_in_charge = current_user.user_name
            new_status.officer_in_charge = current_user.user_name
            new_status.status = Constants.APP_STATUS_SEND
            new_status.status_date = datetime.now().strftime(Constants.PYTHON_DATE_FORMAT)
            session.add(new_status)

        session.commit()

        if len(app_no_without_parcel) > 0:
            app_no_string = ", ".join(app_no_without_parcel)
            QMessageBox.information(None, QApplication.translate("LM2", "Mark Applications"),
                                        QApplication.translate("LM2", "The following applications have no parcels assigned and could not be updated: {0} ".format(app_no_string)))

    @staticmethod
    def revert_case(case_id):

        session = SessionHandler().session_instance()

        try:
            m_case = session.query(CaMaintenanceCase).filter(CaMaintenanceCase.id == case_id).one()
            if m_case.completion_date is not None:
                QMessageBox.information(None, QApplication.translate("LM2", "Maintenance Case"),
                                        QApplication.translate("LM2", "The maintenance case {0} is already finalized."
                                                               .format(str(case_id))))
                return

            session.query(CaTmpParcel).filter(CaTmpParcel.maintenance_case == case_id).delete()
            session.query(CaTmpBuilding).filter(CaTmpBuilding.maintenance_case == case_id).delete()
            session.query(CaMaintenanceCase).filter(CaMaintenanceCase.id == case_id).delete()
            session.commit()

        except exc.SQLAlchemyError, e:
            session.rollback()
            raise LM2Exception(QApplication.translate("LM2", "Database Query Error"),
                               QApplication.translate("LM2", "Could not execute: {0}").format(e.message))
