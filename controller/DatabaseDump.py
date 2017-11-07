__author__ = 'Ankhbold'
# -*- encoding: utf-8 -*-

import glob
from qgis.core import *
from qgis.gui import *
from inspect import currentframe
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import DatabaseError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from ..utils.PluginUtils import *
from ..view.Ui_DatabaseDump import *

class DatabaseDump(QDialog, Ui_DatabaseDump):

    def __init__(self, parent=None):

        super(DatabaseDump, self).__init__(parent)
        mydialog = QDialog
        self.setupUi(self)
        self.timer = None
        self.close_button.clicked.connect(self.reject)
        self.__password = None
        self.psql_dir = None
        ############
        self.__set_password()

        ############
        self.engine = self.__database_conn()
        try:
            connection = self.engine.connect()
        except (DatabaseError, SQLAlchemyError), e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        if not self.engine:
            self.reject()
            return
        self.__setup()
        self.__setup_cbox()

    def __set_password(self):

        text, ok = QtGui.QInputDialog.getText(self, "QInputDialog.getText()",
                "Postgres password:", QtGui.QLineEdit.Password)

        if ok and text != '':
            self.__password = text
        else:
            self.reject()
            # PluginUtils.show_message(self, self.tr("password"), self.tr('Please insert password!!!.'))
            return

    def __setup(self):

        database_name = QSettings().value(SettingsConstants.DATABASE_NAME, "")
        host = QSettings().value(SettingsConstants.HOST, "")
        self.database_edit.setText(database_name)
        self.host_edit.setText(host)
        self.dump_date.setDate(QDate().currentDate())
        self.dump_date.setDisplayFormat("yyyy-MM-dd")
        self.dump_name_edit.setText(database_name+'_'+self.dump_date.text())

        default_path = r'D:/TM_LM2/dumps'
        default_parent_path = r'D:/TM_LM2'
        if not os.path.exists(default_parent_path):
            os.makedirs('D:/TM_LM2')
            os.makedirs('D:/TM_LM2/application_response')
            os.makedirs('D:/TM_LM2/application_list')
            os.makedirs('D:/TM_LM2/approved_decision')
            os.makedirs('D:/TM_LM2/cad_maintenance')
            os.makedirs('D:/TM_LM2/cad_maps')
            os.makedirs('D:/TM_LM2/contracts')
            os.makedirs('D:/TM_LM2/decision_draft')
            os.makedirs('D:/TM_LM2/dumps')
            os.makedirs('D:/TM_LM2/q_data')
            os.makedirs('D:/TM_LM2/refused_decision')
            os.makedirs('D:/TM_LM2/reports')
            os.makedirs('D:/TM_LM2/training')
        if not os.path.exists(default_path):
            os.makedirs(default_path)

        self.dump_path_edit.setText(default_path)

    def __setup_cbox(self):

        insp = inspect(self.engine)
        if self.database_edit.text():
            schemas =  insp.get_schema_names()
            for schema in schemas:
                if schema[:2] == 's0':
                    self.schema_cbox.addItem(schema, schema)

        # self.postgresql_version_cbox.addItem('PostgreSQL-9.4', '9.4')
        # self.postgresql_version_cbox.addItem('PostgreSQL-9.5', '9.5')
        # self.postgresql_version_cbox.addItem('PostgreSQL-9.6', '9.6')
        # self.postgresql_version_cbox.addItem('PostgreSQL-9.7', '9.7')
        # self.postgresql_version_cbox.addItem('PostgreSQL-9.8', '9.8')


        if os.path.isdir("C:/Program Files/PostgreSQL/9.3/bin"):
            self.postgresql_version_cbox.addItem('PostgreSQL-9.3', '9.3')
            self.psql_dir  = "SET pgsql_bin_path="+ '"' +"C:\Program Files\PostgreSQL\9.3/bin"+'"'
        elif os.path.isdir("C:/Program Files/PostgreSQL/9.4/bin"):
            self.postgresql_version_cbox.addItem('PostgreSQL-9.4', '9.4')
            self.psql_dir  = "SET pgsql_bin_path="+ '"' +"C:\Program Files\PostgreSQL\9.4/bin"+'"'
        elif os.path.isdir("C:/Program Files/PostgreSQL/9.5/bin"):
            self.postgresql_version_cbox.addItem('PostgreSQL-9.5', '9.5')
            self.psql_dir  = "SET pgsql_bin_path="+ '"' +"C:\Program Files\PostgreSQL\9.5/bin"+'"'
        elif os.path.isdir("C:/Program Files/PostgreSQL/9.6/bin"):
            self.postgresql_version_cbox.addItem('PostgreSQL-9.6', '9.6')
            self.psql_dir  = "SET pgsql_bin_path="+ '"' +"C:\Program Files\PostgreSQL\9.6/bin"+'"'
        elif os.path.isdir("C:/Program Files/PostgreSQL/9.7/bin"):
            self.postgresql_version_cbox.addItem('PostgreSQL-9.7', '9.7')
            self.psql_dir  = "SET pgsql_bin_path="+ '"' +"C:\Program Files\PostgreSQL\9.7/bin"+'"'
        else:
            PluginUtils.show_message(self, self.tr("invalid postgresql"), self.tr('No PostgreSQL!!!.'))
            return

    @pyqtSlot(int)
    def on_schema_cbox_currentIndexChanged(self, index):

        if self.schem_checkbox.isChecked():
            self.dump_name_edit.setText(self.schema_cbox.currentText()+'_'+self.dump_date.text())

    @pyqtSlot(int)
    def on_schem_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.info_label.setText('schema soum, person info')
            self.dump_name_edit.setText(self.schema_cbox.currentText()+'_'+self.dump_date.text())
            self.schema_cbox.setEnabled(True)
        else:
            self.info_label.setText('')
            database_name = QSettings().value(SettingsConstants.DATABASE_NAME, "")
            self.dump_name_edit.setText(database_name+'_'+self.dump_date.text())
            self.schema_cbox.setEnabled(False)

    @pyqtSlot()
    def on_dump_button_clicked(self):

        if self.dump_path_edit.text() == '' or self.dump_name_edit.text() == '':
            PluginUtils.show_message(self, self.tr("invalid value"), self.tr('Not connect!!!.'))
            return
        if not self.schem_checkbox.isChecked():
            file_path = str(os.path.dirname(os.path.realpath(__file__))[:-10])+"template/backup.bat"

            database = 'SET Database_name=' + self.database_edit.text()
            host = 'SET Host=' + self.host_edit.text()
            dump_name = 'SET Dump_name=' + self.dump_name_edit.text()

            self.__replace_line_dump_name(file_path, 1, dump_name)
            self.__replace_line_database(file_path, 2, database)
            self.__replace_line_host(file_path, 3, host)
            self.__replace_line_psql_dir(file_path, 5, self.psql_dir)
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            file_path = str(os.path.dirname(os.path.realpath(__file__))[:-10])+"template/backup_schema.bat"
            file_path_person = str(os.path.dirname(os.path.realpath(__file__))[:-10])+"template/backup_person_data.bat"

            database = 'SET Database_name=' + self.database_edit.text()
            host = 'SET Host=' + self.host_edit.text()
            dump_name = 'SET Dump_name=' + self.dump_name_edit.text()
            schema_name = 'SET Schema_name=' + self.schema_cbox.currentText()

            self.__replace_line_dump_name(file_path, 1, dump_name)
            self.__replace_line_database(file_path, 2, database)
            self.__replace_line_host(file_path, 3, host)
            self.__replace_schema_name(file_path, 4, schema_name)
            self.__replace_line_psql_dir(file_path, 5, self.psql_dir)

            self.__replace_line_dump_name(file_path_person, 1, dump_name)
            self.__replace_line_database(file_path_person, 2, database)
            self.__replace_line_host(file_path_person, 3, host)
            self.__replace_schema_name(file_path_person, 4, schema_name)
            self.__replace_line_psql_dir(file_path, 5, self.psql_dir)

            default_path = r'D:/TM_LM2/dumps/'+self.schema_cbox.currentText()
            default_parent_path = r'D:/TM_LM2'
            if not os.path.exists(default_parent_path):
                os.makedirs('D:/TM_LM2')
                os.makedirs('D:/TM_LM2/application_response')
                os.makedirs('D:/TM_LM2/application_list')
                os.makedirs('D:/TM_LM2/approved_decision')
                os.makedirs('D:/TM_LM2/cad_maintenance')
                os.makedirs('D:/TM_LM2/cad_maps')
                os.makedirs('D:/TM_LM2/contracts')
                os.makedirs('D:/TM_LM2/decision_draft')
                os.makedirs('D:/TM_LM2/dumps')
                os.makedirs('D:/TM_LM2/q_data')
                os.makedirs('D:/TM_LM2/refused_decision')
                os.makedirs('D:/TM_LM2/reports')
                os.makedirs('D:/TM_LM2/training')
            if not os.path.exists(default_path):
                os.makedirs(default_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path_person))

    @pyqtSlot()
    def on_database_path_button_clicked(self):

        default_path = r'D:/TM_LM2/dumps/'+self.restore_schema_edit.text()
        file_dialog = QFileDialog()
        file_dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        file_dialog.setModal(True)
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setFilter(self.tr("Sql File (*.dump)"))
        file_dialog.setDirectory(default_path)
        if file_dialog.exec_():

            selected_file = file_dialog.selectedFiles()[0]
            file_path = QFileInfo(selected_file).path()
            file_name = QFileInfo(selected_file).fileName()

            self.database_path_edit.setText(file_path+'/'+file_name)
            self.database_name.setText(file_name[:7])

    @pyqtSlot()
    def on_create_role_button_clicked(self):

        is_role = True
        groups = self.__groupsByUser()
        for group in groups:
            if group != self.create_soums_edit.text():
                is_role = False
        if not is_role:
            self.engine.execute(u"CREATE ROLE "+self.create_soums_edit.text())
            self.engine.execute(u"grant create on database "+ "test" + " to geodb_admin")

    @pyqtSlot()
    def on_database_restore_button_clicked(self):

        database = 'SET Database_name=' + self.database_name.text()
        host = 'SET Host=' + self.host_edit.text()
        dump_path = 'SET backup_file='+self.database_path_edit.text()



        #create empty database

        file_database_dump = str(os.path.dirname(os.path.realpath(__file__))[:-10])+"template/restore_database.bat"
        self.__replace_line_database(file_database_dump, 2, database)
        self.__replace_line_host(file_database_dump, 3, host)
        self.__replace_schema_path(file_database_dump, 7, dump_path)
        self.__replace_line_psql_dir(file_database_dump, 5, self.psql_dir)

        QDesktopServices.openUrl(QUrl.fromLocalFile(file_database_dump))

    @pyqtSlot()
    def on_person_path_clicked(self):

        default_path = r'D:/TM_LM2/dumps/'+self.restore_schema_edit.text()
        file_dialog = QFileDialog()
        file_dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        file_dialog.setModal(True)
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setFilter(self.tr("Sql File (*.sql)"))
        file_dialog.setDirectory(default_path)
        if file_dialog.exec_():

            selected_file = file_dialog.selectedFiles()[0]
            file_path = QFileInfo(selected_file).path()
            file_name = QFileInfo(selected_file).fileName()

            self.restore_person_edit.setText(file_path+'/'+file_name)

    @pyqtSlot(int)
    def on_name_edit_checkbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.database_name.setReadOnly(False)
        else:
            self.database_name.setReadOnly(True)

    @pyqtSlot()
    def on_schema_path_button_clicked(self):

        default_path = r'D:/TM_LM2/dumps/'+self.restore_schema_edit.text()
        file_dialog = QFileDialog()
        file_dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        file_dialog.setModal(True)
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setFilter(self.tr("Dump File (*.dump)"))
        file_dialog.setDirectory(default_path)
        if file_dialog.exec_():

            selected_file = file_dialog.selectedFiles()[0]
            file_path = QFileInfo(selected_file).path()
            file_name = QFileInfo(selected_file).fileName()

            self.restore_schema_path_edit.setText(file_path+'/'+file_name)
            self.restore_schema_edit.setReadOnly(True)
            self.restore_schema_edit.setText(file_name[:6])

            insp = inspect(self.engine)
            schemas =  insp.get_schema_names()
            s_count = 0
            old_shema = ''
            schema_n = self.restore_schema_edit.text()
            for schema in schemas:
                if schema == schema_n+'s':
                    old_shema = schema
                if schema[:6] == schema_n:
                    s_count = s_count + 1
            if s_count >= 2:
                self.old_schema_edit.setText(old_shema)
                self.new_schema_edit.setText(schema_n)
                self.restore_button.setEnabled(True)
                self.old_schema_delete_button.setEnabled(True)
            self.schema_import_button.setEnabled(True)

    @pyqtSlot()
    def on_person_import_button_clicked(self):

        schema_path = 'SET backup_file='+self.restore_person_edit.text()
        schema_name = 'SET Schema_name=' + self.restore_schema_edit.text()
        database = 'SET Database_name=' + self.database_edit.text()
        host = 'SET Host=' + self.host_edit.text()

        file_schema_person = str(os.path.dirname(os.path.realpath(__file__))[:-10])+"template/restore_schema_person.bat"
        self.__replace_line_database(file_schema_person, 2, database)
        self.__replace_line_host(file_schema_person, 3, host)
        self.__replace_schema_name(file_schema_person, 4, schema_name)
        self.__replace_schema_path(file_schema_person, 7, schema_path)
        self.__replace_line_psql_dir(file_schema_person, 5, self.psql_dir)
        QDesktopServices.openUrl(QUrl.fromLocalFile(file_schema_person))

    @pyqtSlot()
    def on_restore_button_clicked(self):

        schema_old = self.old_schema_edit.text()
        schema_n = self.restore_schema_edit.text()
        user = QSettings().value(SettingsConstants.USER)

        insp = inspect(self.engine)
        self.engine.execute(u"REVOKE {0} FROM {1}".format(schema_n, user))
        sql = "revoke USAGE ON SCHEMA "+ schema_n + " from "+ schema_n
        self.engine.execute(sql)
        self.engine = "drop schema if exists "+schema_n + " cascade"
        self.engine.execute(sql)

        sql = "alter schema "+schema_old+" rename to "+schema_old[:6]
        self.engine.execute(sql)

        self.new_schema_edit.clear()
        self.old_schema_edit.clear()
        self.restore_button.setEnabled(False)
        self.old_schema_delete_button.setEnabled(False)

    @pyqtSlot()
    def on_old_schema_delete_button_clicked(self):

        host_eng = self.host_edit.text()
        database_eng = self.database_edit.text()
        schema_old = self.old_schema_edit.text()

        insp = inspect(self.engine)
        schemas =  insp.get_schema_names()
        user = QSettings().value(SettingsConstants.USER)

        for schema in schemas:
            if schema == schema_old:
                self.engine.execute(u"REVOKE {0} FROM {1}".format(schema[:6], user))
                sql = "revoke USAGE ON SCHEMA "+ schema_old + " from "+ schema[:6]
                self.engine.execute(sql)
                sql = "drop schema if exists "+schema_old + " cascade"
                self.engine.execute(sql)
        self.new_schema_edit.clear()
        self.old_schema_edit.clear()
        self.restore_button.setEnabled(False)
        self.old_schema_delete_button.setEnabled(False)

    def __database_conn(self):

        user_eng = 'postgres'
        password_eng = self.__password
        host_eng = QSettings().value(SettingsConstants.HOST)
        port_eng = '5432'
        database_eng = self.database_edit.text()
        database_name = QSettings().value(SettingsConstants.DATABASE_NAME, "")

        conn_string = "postgresql://postgres:"+self.__password+"@"+host_eng+":5432/"+database_name
        eng = create_engine(conn_string)
        return  eng

    @pyqtSlot()
    def on_schema_import_button_clicked(self):

        schema_path = 'SET backup_file='+self.restore_schema_path_edit.text()
        schema_name = 'SET Schema_name=' + self.restore_schema_edit.text()
        database = 'SET Database_name=' + self.database_edit.text()
        host = 'SET Host=' + self.host_edit.text()
        schema_n = self.restore_schema_edit.text()
        if self.old_schema_edit.text() == schema_n+'s':
            PluginUtils.show_message(self, self.tr("Soum schema"), self.tr('Old schema delete!!!.'))
            return

        insp = inspect(self.engine)

        schemas =  insp.get_schema_names()
        is_scheme = False
        is_not_schema = True
        for schema in schemas:
            if schema == schema_n:
                is_scheme = True
                is_not_schema = False
        if is_scheme:
            sql = "alter schema "+schema_n+" rename to "+schema_n+"s"
            self.engine.execute(sql)

        file_schema = str(os.path.dirname(os.path.realpath(__file__))[:-10])+"template/restore_schema.bat"
        self.__replace_line_database(file_schema, 2, database)
        self.__replace_line_host(file_schema, 3, host)
        self.__replace_schema_name(file_schema, 4, schema_name)
        self.__replace_schema_path(file_schema, 7, schema_path)

        QDesktopServices.openUrl(QUrl.fromLocalFile(file_schema))

        self.schema_import_button.setEnabled(False)

        self.new_schema_edit.setText(schema_n)
        self.old_schema_edit.setText(schema_n+'s')

        self.restore_button.setEnabled(True)
        self.old_schema_delete_button.setEnabled(True)

    def __replace_line_database(self, file_name, line_num, text):

        lines = open(file_name, 'r').readlines()
        lines[line_num] = ''
        lines[line_num] = text+'\n'
        out = open(file_name, 'w')
        out.writelines(lines)
        out.close()

    def __replace_line_host(self, file_name, line_num, text):

        lines = open(file_name, 'r').readlines()
        lines[line_num] = ''
        lines[line_num] = text+'\n'
        out = open(file_name, 'w')
        out.writelines(lines)
        out.close()

    def __replace_line_psql_dir(self, file_name, line_num, text):

        lines = open(file_name, 'r').readlines()
        lines[line_num] = ''
        lines[line_num] = text+'\n'
        out = open(file_name, 'w')
        out.writelines(lines)
        out.close()

    def __replace_line_dump_name(self, file_name, line_num, text):

        lines = open(file_name, 'r').readlines()
        lines[line_num] = ''
        lines[line_num] = text+'\n'
        out = open(file_name, 'w')
        out.writelines(lines)
        out.close()

    def __replace_schema_name(self, file_name, line_num, text):

        lines = open(file_name, 'r').readlines()
        lines[line_num] = ''
        lines[line_num] = text+'\n'
        out = open(file_name, 'w')
        out.writelines(lines)
        out.close()

    def __replace_schema_path(self, file_name, line_num, text):

        lines = open(file_name, 'r').readlines()
        lines[line_num] = ''
        lines[line_num] = text+'\n'
        out = open(file_name, 'w')
        out.writelines(lines)
        out.close()

    def __groupsByUser(self):

        sql = "select rolname from pg_user join pg_auth_members on (pg_user.usesysid=pg_auth_members.member) " \
              "join pg_roles on (pg_roles.oid=pg_auth_members.roleid)"
        result = self.engine.execute(sql).fetchall()

        return result