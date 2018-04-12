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
from ..view.Ui_WebgisUtilityDialog import *
from ..utils.FileUtils import FileUtils
import webbrowser
from ..utils.SessionHandler import SessionHandler
from docxtpl import DocxTemplate, RichText

class WebgisUtilityDialog(QDialog, Ui_WebgisUtilityDialog):

    def __init__(self, parent=None):

        super(WebgisUtilityDialog, self).__init__(parent)
        self.setupUi(self)
        self.timer = None
        self.close_button.clicked.connect(self.reject)
        self.session = None
        self.session_db = SessionHandler().session_instance()
        self.__setup()

        self.progressBar.setMinimum(1)
        self.progressBar.setValue(0)
        self.person = None

    def __setup(self):

        if QSettings().value(SettingsConstants.WEBGIS_IP):
            self.webgis_ip_edit.setText(QSettings().value(SettingsConstants.WEBGIS_IP))
            self.webgis_url_edit.setText(QSettings().value(SettingsConstants.WEBGIS_IP))

        self.owner_co_twidget.setAlternatingRowColors(True)
        self.owner_co_twidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.owner_co_twidget.setSelectionBehavior(QTableWidget.SelectRows)

        self.owner_twidget.setAlternatingRowColors(True)
        self.owner_twidget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.owner_twidget.setSelectionBehavior(QTableWidget.SelectRows)

    @pyqtSlot()
    def on_refresh_webgis_button_clicked(self):

        if self.webgis_ip_edit.text() == '':
            PluginUtils.show_message(self, self.tr("invalid value"), self.tr('WebGIS IP Address null!!!.'))
            return
        host = 'SET Host=' + self.webgis_ip_edit.text()
        sql_path = str(os.path.dirname(os.path.realpath(__file__))[:-10])+"template"
        sql_row = 'SET backup_path=' +'"'+ sql_path + '"'

        file_path = str(os.path.dirname(os.path.realpath(__file__))[:-10])+"template/backup_refresh.bat"
        self.__replace_line_host(file_path, 3, host)
        self.__replace_line_host(file_path, 7, sql_row)
        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def __replace_line_host(self, file_name, line_num, text):

        lines = open(file_name, 'r').readlines()
        lines[line_num] = ''
        lines[line_num] = text+'\n'
        out = open(file_name, "w")
        out.writelines(lines)
        out.close()

    @pyqtSlot()
    def on_open_webgis_button_clicked(self):

        if self.webgis_url_edit.text():
            webbrowser.open(self.webgis_url_edit.text())

    @pyqtSlot()
    def on_check_connect_button_clicked(self):

        self.__connect_webgis()

    @pyqtSlot()
    def on_find_ownership_button_clicked(self):

        if not self.person_id.text():
            PluginUtils.show_message(self, self.tr("Person ID"),
                                     self.tr("Enter find value!!!"))
            return
        person_id = self.person_id.text()

        if self.lm_rbutton.isChecked():
            self.__find_lm(person_id)
        if self.lpis_rbutton.isChecked():
            self.__find_lpis(person_id)
        if self.subject_rbutton.isChecked():
            self.__find_subject(person_id)


        # self.owner_twidget.setRowCount(0)
        self.progressBar.setValue(0)

    def __find_subject(self, person_id):

        sql = "select * from owner.all_burtgel c where (upper(c.owner_reg) = :person_id) "

        count = 0
        results = self.session.execute(sql, {'person_id': person_id})
        # print len(results)
        self.owner_twidget.setRowCount(0)
        for row in results:
            self.owner_twidget.insertRow(count)

            item = QTableWidgetItem(str(row[5]))
            self.owner_twidget.setItem(count, 0, item)

            item = QTableWidgetItem((row[21]) + ' (' + (row[19]) + ' ' + (row[20]) + ')')
            item.setData(Qt.UserRole, row[21])
            self.owner_twidget.setItem(count, 1, item)

            item = QTableWidgetItem((row[22]) + ' ' + (row[23]) +' '+ unicode(row[24])+ u'-р баг')
            self.owner_twidget.setItem(count, 2, item)

            item = QTableWidgetItem((row[25]) +' '+ unicode(row[26]) + u'-р гудамж' + unicode(row[27]) + u' хашаа/хаалга/')
            self.owner_twidget.setItem(count, 3, item)

            item = QTableWidgetItem(str(row[28]))
            self.owner_twidget.setItem(count, 4, item)

            count += 1

        if self.owner_twidget.rowCount() == 0:
            self.error_label.setText(self.tr("Owner record not found"))

    @pyqtSlot(QTableWidgetItem)
    def on_owner_twidget_itemClicked(self, item):

        self.owner_co_twidget.setRowCount(0)

        selected_row = self.owner_twidget.currentRow()

        if selected_row == -1:
            return
        register = self.owner_twidget.item(selected_row, 1).data(Qt.UserRole)

        sql = "select register, ovog,ner ,hen,zahid " \
              "from owner.ub_lpis_co info " \
              "where oregister = :register "

        result = self.session.execute(sql, {'register': register})
        row = 0
        for item_row in result:
            row = self.owner_co_twidget.rowCount()
            self.owner_co_twidget.insertRow(row)
            item = QTableWidgetItem()
            item.setText(unicode(item_row[0]))
            item.setData(Qt.UserRole, item_row[0])
            self.owner_co_twidget.setItem(row, 0, item)

            item = QTableWidgetItem()
            item.setText(unicode(item_row[1]))
            self.owner_co_twidget.setItem(row, 1, item)

            item = QTableWidgetItem()
            item.setText(unicode(item_row[2]))
            self.owner_co_twidget.setItem(row, 2, item)

            item = QTableWidgetItem()
            item.setText(unicode(item_row[3]))
            self.owner_co_twidget.setItem(row, 3, item)

            item = QTableWidgetItem()
            item.setText(unicode(item_row[4]))
            self.owner_co_twidget.setItem(row, 4, item)

            row = + 1

    def __find_lpis(self, person_id):

        sql = "select * from owner.ub_lpis c where (c.register = :person_id) "

        count = 0
        results = self.session.execute(sql, {'person_id': person_id})
        # print len(results)
        self.owner_twidget.setRowCount(0)
        for row in results:
            self.owner_twidget.insertRow(count)

            item = QTableWidgetItem((row[14]))
            self.owner_twidget.setItem(count, 0, item)

            item = QTableWidgetItem((row[1]) + ' (' + (row[3]) + ' ' + (row[4]) + ')')
            item.setData(Qt.UserRole, row[1])
            self.owner_twidget.setItem(count, 1, item)

            item = QTableWidgetItem((row[10]) + ' ' + (row[11]))
            self.owner_twidget.setItem(count, 2, item)

            item = QTableWidgetItem((row[12]))
            self.owner_twidget.setItem(count, 3, item)

            item = QTableWidgetItem((row[29]))
            self.owner_twidget.setItem(count, 4, item)

            count += 1

        if self.owner_twidget.rowCount() == 0:
            self.error_label.setText(self.tr("Owner record not found"))

    def __find_lm(self, person_id):

        sql = "select * from webgis.wg_rightholder c where (c.person_id = :person_id) and tr_type_code = 3  "

        sql = "{0} order by parcel_id;".format(sql)
        count = 0
        results = self.session.execute(sql, {'person_id': person_id})
        # print len(results)
        self.owner_twidget.setRowCount(0)
        for row in results:
            self.owner_twidget.insertRow(count)

            item = QTableWidgetItem((row[1]))
            self.owner_twidget.setItem(count, 0, item)

            item = QTableWidgetItem((row[3]) + ' (' + (row[5]) + ' ' + (row[6]) + ')')
            self.owner_twidget.setItem(count, 1, item)

            item = QTableWidgetItem((row[11]) + ' ' + (row[12]) + ' ' + (row[13]))
            self.owner_twidget.setItem(count, 2, item)

            item = QTableWidgetItem((row[14]) + ' ' + (row[15]))
            self.owner_twidget.setItem(count, 3, item)

            count += 1

        if self.owner_twidget.rowCount() == 0:
            self.error_label.setText(self.tr("Owner record not found"))

    def __connect_webgis(self):

        user = 'geodb_user'
        password = 'geodb_user'
        host = self.webgis_ip_edit.text()
        port = '5432'
        database = 'map_server'
        if not self.__session_webgis(user, password, host, port, database):
            PluginUtils.show_message(self, self.tr("Connection failed"),
                                     self.tr("Please check your VPN connection!!!"))
            return
        else:
            PluginUtils.show_message(self, self.tr("Connection"),
                                     self.tr("Successfully connected"))
            self.refresh_webgis_button.setDisabled(False)
            self.find_ownership_button.setDisabled(False)
            return

    def __session_webgis(self, user, password, host, port, database):

        if self.session is not None:
            self.session.close()

        try:
            self.engine = create_engine("postgresql://{0}:{1}@{2}:{3}/{4}".format(user, password, host, port, database))
            self.password = password
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            self.session.autocommit = False
            self.session.execute("SET search_path to base, codelists, admin_units, settings, public, webgis")

            self.session.commit()

            return True

        except SQLAlchemyError, e:
            self.session = None
            self.engine = None
            self.password = None
            raise e

    @pyqtSlot(str)
    def on_person_id_textChanged(self, text):

        self.person_id.setStyleSheet(self.styleSheet())
        new_text = self.__auto_correct_private_person_id(text)
        if new_text is not text:
            self.person_id.setText(new_text)
            return
        if not self.__validate_private_person_id(text):
            self.person_id.setStyleSheet(Constants.ERROR_LINEEDIT_STYLESHEET)
            return

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

        if len(new_text) > 10:
            new_text = new_text[:10]

        return new_text

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

    @pyqtSlot()
    def on_defination_print_button_clicked(self):

        selected_row = self.owner_twidget.currentRow()
        if selected_row == -1:
            return

        register = self.owner_twidget.item(selected_row, 1).data(Qt.UserRole)

        path = FileUtils.map_file_path()
        default_path = r'D:/TM_LM2/contracts'

        tpl = DocxTemplate(path+'owner_refer.docx')


        person_id = register
        person_surname = ''
        person_firstname = ''

        user = DatabaseUtils.current_user()

        restrictions = user.restriction_au_level2.split(",")
        is_true_text = u'эрхгүй'
        for restriction in restrictions:
            restriction = restriction.strip()
            soum = self.session_db.query(AuLevel2).filter(AuLevel2.code == restriction).one()
            for row in range(self.owner_twidget.rowCount()):
                item_name = self.owner_twidget.item(row,1)
                soum_name = item_name.data(Qt.UserRole)
                if soum_name == soum.name:
                    is_true_text = u'эрхтэй'

        officers = self.session_db.query(SetRole) \
            .filter(SetRole.user_name == user.user_name) \
            .filter(SetRole.is_active == True).one()
        role_position_code = officers.position
        role_position_desc = officers.position_ref.description
        working_aimag = officers.working_au_level1_ref.name
        working_soum = officers.working_au_level2_ref.name
        header_text = ''
        position_text = ''
        officer_name = officers.surname[:1] +'.'+ officers.first_name
        current_date = ''
        current_year = QDate().currentDate().year()
        current_month = QDate().currentDate().month()
        current_day = QDate().currentDate().day()
        current_date = str(current_year)+ u' оны ' + str(current_month) + u' сарын ' + str(current_day)
        if role_position_code == 7:
            header_text = (working_aimag).upper() + u' АЙМГИЙН ' + (working_soum).upper() + u' СУМЫН ЗДТГАЗАР'
            position_text = (working_soum).upper() + u' сумын газрын даамал'
        else:
            header_text = (working_aimag).upper() + u' АЙМГИЙН ГАЗРЫН ХАРИЛЦАА, БАРИЛГА ХОТ БАЙГУУЛАЛТЫН ГАЗАР'
            position_text = (working_aimag).upper() + u' аймгийн газрын харилцаа, барилга хот байгуулалтын газрын мэргэжилтэн'

        # to_aimag = self.aimag_cbox.currentText() +u' аймгийн '+ self.soum_cbox.currentText() + u' сумын ЗДТГазарт'
        context = {
            'HEADER_TEXT': header_text,
            'person_id': person_id,
            'surname': person_surname,
            'firstname': person_firstname,
            'current_date': current_date,
            'position_text': position_text,
            'officer_name': officer_name,
            # 'to_soum': to_aimag,
            'is_true': is_true_text
        }

        tpl.render(context)

        try:
            tpl.save(default_path + "/ownership_refer.docx")
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(default_path + "/ownership_refer.docx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"),
                                   self.tr("This file is already opened. Please close re-run"))