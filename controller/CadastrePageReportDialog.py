__author__ = 'B.Ankhbold'
# coding=utf8
import os
import xlsxwriter
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *
from qgis.core import *
from qgis.gui import *
from inspect import currentframe
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_, extract
from xlrd import open_workbook
from ..view.Ui_CadastrePageReportDialog import *
from ..utils.SessionHandler import SessionHandler
from ..model.CtApplicationStatus import *
from ..model import Constants
from ..model.DatabaseHelper import *
from ..utils.PluginUtils import PluginUtils
from ..model.CtApplication import *
from ..model.BsPerson import *
from ..model.ClDecisionLevel import *
from ..model.ClDecision import *
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.AuLevel3 import *
from ..model.CadastrePageSearch import *
from ..model.ClPositionType import *
from ..utils.DatabaseUtils import *
from .qt_classes.ComboBoxDelegate import *
from .qt_classes.DropLabel import DropLabel
from .qt_classes.IntegerSpinBoxDelegate import *
from .qt_classes.ObjectAppDocumentDelegate import ObjectAppDocumentDelegate
from .qt_classes.ContractDocumentDelegate import ContractDocumentDelegate
from .qt_classes.ApplicantDocumentDelegate import ApplicationDocumentDelegate
from .qt_classes.DocumentsTableWidget import DocumentsTableWidget
from .qt_classes.DragTableWidget import DragTableWidget
from .qt_classes.DoubleSpinBoxDelegate import DoubleSpinBoxDelegate
from .qt_classes.DropLabel import DropLabel

class CadastrePageReportDialog(QDialog, Ui_CadastrePageReportDialog, DatabaseHelper):

    def __init__(self, parent=None):

        super(CadastrePageReportDialog, self).__init__(parent)
        DatabaseHelper.__init__(self)
        self.setupUi(self)

        self.setWindowTitle(self.tr("Cadastre page reporty Dialog"))
        self.session = SessionHandler().session_instance()
        self.close_button.clicked.connect(self.reject)

        # self.__cbox_setup()
        self.__setup_twidget()
        self.__setup_twidget()
        self.__setup_validators()
        self.__create_cadastre_page_view()

    def __setup_validators(self):

        self.numbers_validator = QRegExpValidator(QRegExp("[1-9][0-9]+( *,*[1-9][0-9]+)*"), None)
        self.parcel_id_edit.setValidator(self.numbers_validator)

    def __cbox_setup(self):

        right_type = self.session.query(ClRightType).all()

        self.right_type_cbox.addItem('*', -1)
        for item in right_type:
            self.right_type_cbox.addItem(item.description, item.code)

    def __setup_twidget(self):

        self.cpage_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cpage_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cpage_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cpage_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

    def __create_cadastre_page_view(self):

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        sql = ""

        for au_level2 in au_level2_list:

            au_level2 = au_level2.strip()
            if not sql:
                sql = "Create or replace temp view cadastre_page_search as" + "\n"
            else:
                sql = sql + "UNION" + "\n"

            select = "SELECT row_number() over() as id, cadastre.print_date, cadastre.cadastre_page_number, cadastre.person_id, " \
                     "cadastre.parcel_id, person.name ||' '|| person.first_name as right_holder, parcel.address_streetname ||' - '|| parcel.address_khashaa as parcel_address " \
                     "FROM s{0}.ct_cadastre_page cadastre " \
                     "left join base.bs_person person on person.person_id = cadastre.person_id " \
                     "left join s{0}.ca_parcel parcel on parcel.parcel_id = cadastre.parcel_id ".format(au_level2) + "\n"

            sql = sql + select

        sql = "{0} order by print_date;".format(sql)

        # try:
        self.session.execute(sql)
        self.commit()
        # except SQLAlchemyError, e:
        #     PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
        #     return

    @pyqtSlot(int)
    def on_print_year_chbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.print_year_sbox.setEnabled(True)
        else:
            self.print_year_sbox.setEnabled(False)

    @pyqtSlot()
    def on_find_button_clicked(self):

        self.cpage_twidget.setRowCount(0)
        print self.session.query(CadastrePageSearch).count()

        cadastre_pages = self.session.query(CadastrePageSearch)
        filter_is_set = False

        if self.person_id_edit.text():
            filter_is_set = True
            person_id = "%" + self.person_id_edit.text() + "%"
            cadastre_pages = cadastre_pages.filter(CadastrePageSearch.person_id.ilike(person_id))

        if self.parcel_id_edit.text():
            filter_is_set = True
            parcel_id = "%" + self.parcel_id_edit.text() + "%"
            cadastre_pages = cadastre_pages.filter(CadastrePageSearch.parcel_id.ilike(parcel_id))

        if self.print_year_chbox.isChecked():
            filter_is_set = True
            print_year = self.print_year_sbox.value()
            cadastre_pages = cadastre_pages.filter(extract('year', CadastrePageSearch.print_date) == print_year)

        count = 0
        for cadastre_page in cadastre_pages:
            self.cpage_twidget.insertRow(count)

            item = QTableWidgetItem(str(cadastre_page.id))
            item.setData(Qt.UserRole, cadastre_page.id)
            self.cpage_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(str(cadastre_page.print_date))
            item.setData(Qt.UserRole, cadastre_page.print_date)
            self.cpage_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(str(cadastre_page.cadastre_page_number))
            item.setData(Qt.UserRole, cadastre_page.cadastre_page_number)
            self.cpage_twidget.setItem(count, 2, item)

            item = QTableWidgetItem(unicode(cadastre_page.person_id))
            item.setData(Qt.UserRole, cadastre_page.person_id)
            self.cpage_twidget.setItem(count, 3, item)

            item = QTableWidgetItem(unicode(cadastre_page.right_holder))
            item.setData(Qt.UserRole, cadastre_page.right_holder)
            self.cpage_twidget.setItem(count, 4, item)

            item = QTableWidgetItem(cadastre_page.parcel_id)
            item.setData(Qt.UserRole, cadastre_page.parcel_id)
            self.cpage_twidget.setItem(count, 5, item)

            item = QTableWidgetItem(unicode(cadastre_page.parcel_address))
            item.setData(Qt.UserRole, cadastre_page.parcel_address)
            self.cpage_twidget.setItem(count, 6, item)

            count += 1

        self.results_label.setText(self.tr("Results: ") + str(count))

    @pyqtSlot()
    def on_print_button_clicked(self):

        default_path = r'D:/TM_LM2/cadastre_page'
        default_parent_path = r'D:/TM_LM2'
        if not os.path.exists(default_parent_path):
            os.makedirs('D:/TM_LM2')

        if not os.path.exists(default_path):
            os.makedirs(default_path)

        workbook = xlsxwriter.Workbook(default_path + "/" + 'cadastre_page_report' + ".xlsx")
        worksheet = workbook.add_worksheet()

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(12)
        format.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(14)
        format_header.set_bold()

        worksheet.merge_range('B2:G2', u'Кадастрын зургийн үнэт цаасны тайлан', format_header)

        worksheet.set_column('A:A', 18)
        worksheet.set_column('B:B', 18)
        worksheet.set_column('C:C', 18)
        worksheet.set_column('D:D', 18)
        worksheet.set_column('E:E', 18)
        worksheet.set_column('F:F', 18)
        worksheet.set_column('G:G', 20)

        xrow = 4
        xcol = 0

        worksheet.write('A4', u"Дугаар", format)
        worksheet.write('B4', u"Хэвлэсэн огноо", format)
        worksheet.write('C4', u"Үнэт цаасны дугаар", format)
        worksheet.write('D4', u"Регистрийн дугаар", format)
        worksheet.write('E4', u"Хуулийн этгээдийн нэр", format)
        worksheet.write('F4', u"Нэгж талбарын дугаар", format)
        worksheet.write('G4', u"Нэгж талбарын хаяг", format)

        num_rows = self.cpage_twidget.rowCount()
        for row in range(num_rows):
            id = self.cpage_twidget.item(row, 0)
            print_date = self.cpage_twidget.item(row, 1)
            page_number = self.cpage_twidget.item(row, 2)
            person_id = self.cpage_twidget.item(row, 3)
            right_holder = self.cpage_twidget.item(row, 4)
            parcel_id = self.cpage_twidget.item(row, 5)
            parcel_address = self.cpage_twidget.item(row, 6)

            worksheet.write(xrow, xcol, id.text(), format)
            worksheet.write(xrow, xcol + 1, print_date.text(), format)
            worksheet.write(xrow, xcol + 2, page_number.text(), format)
            worksheet.write(xrow, xcol + 3, person_id.text(), format)
            worksheet.write(xrow, xcol + 4, right_holder.text(), format)
            worksheet.write(xrow, xcol + 5, parcel_id.text(), format)
            worksheet.write(xrow, xcol + 6, parcel_address.text(), format)
            xrow = xrow + 1

        user_name = QSettings().value(SettingsConstants.USER)
        officer = self.session.query(SetRole) \
            .filter(SetRole.user_name == user_name) \
            .filter(SetRole.is_active == True).one()
        position = officer.position
        position = self.session.query(ClPositionType).filter(ClPositionType.code == position).one()
        position = position.description
        worksheet.write(xrow + 2, xcol, u'Тайлан гаргасан:')
        worksheet.merge_range(xrow + 2, xcol + 1, xrow + 2, xcol+3, '________________/'+officer.surname[:1]+'.'+officer.first_name+'/')

        worksheet.write(xrow + 3, xcol, u'Албан тушаал:')
        worksheet.merge_range(xrow + 3, xcol + 1, xrow + 3, xcol + 5, position)

        workbook.close()
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/" + 'cadastre_page_report' + ".xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"),
                                   self.tr("This file is already opened. Please close re-run"))