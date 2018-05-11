__author__ = 'B.Ankhbold'
# coding=utf8
import os
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell, xl_col_to_name
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *
from qgis.core import *
from qgis.gui import *
from inspect import currentframe
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_, and_, desc,extract
from xlrd import open_workbook
from ..model.SetApplicationTypeLanduseType import *
from ..model.ParcelGt1 import *
from ..model.CtFee import *
from ..view.Ui_ReportDialog import *
from ..model.DatabaseHelper import *
from ..model.ParcelReport import *
from ..model.ClConservationType import *
from ..model.CaParcelConservation import *
from ..model.ClPollutionType import *
from ..model.CaParcelPollution import *
from ..model.ParcelFeeReport import *
from ..model.ParcelTaxReport import *
from ..utils.LayerUtils import LayerUtils
from ..utils.DatabaseUtils import *
from ..utils.PluginUtils import *
from .qt_classes.IntegerSpinBoxDelegate import *
import xlsxwriter
import math

LANDUSE_1 = u'Хөдөө аж ахуйн газар'
LANDUSE_2 = u'Хот, тосгон, бусад суурины газар'
LANDUSE_3 = u'Зам, шугам сүлжээний газар'
LANDUSE_4 = u'Ойн сан бүхий газар'
LANDUSE_5 = u'Усны сан бүхий газар'
LANDUSE_6 = u'Улсын тусгай хэрэгцээний газар'

class ReportDialog(QDialog, Ui_ReportDialog, DatabaseHelper):

    def __init__(self, parent=None):

        super(ReportDialog,  self).__init__(parent)
        DatabaseHelper.__init__(self)
        self.setupUi(self)

        self.setWindowTitle(self.tr("Report Dialog"))
        self.close_button.clicked.connect(self.reject)
        self.session = SessionHandler().session_instance()
        self.begin_year_sbox.setMinimum(1900)
        self.begin_year_sbox.setMaximum(2200)
        self.begin_year_sbox.setSingleStep(1)
        self.begin_year_sbox.setValue(QDate.currentDate().year())

        self.end_date = (str(self.begin_year_sbox.value() + 1) + '-01-01')
        self.end_date = datetime.strptime(self.end_date, "%Y-%m-%d").date()

        self.before_date = (str(self.begin_year_sbox.value()) + '-01-01')
        self.before_date = datetime.strptime(self.before_date, "%Y-%m-%d").date()

        self.after_year_date = (str(self.begin_year_sbox.value() + 2) + '-01-01')
        self.after_year_date = datetime.strptime(self.after_year_date, "%Y-%m-%d").date()

        self.userSettings = None
        self.__setup_combo_box()
        self.__load_role_settings()
        self.progressBar.setMinimum(1)
        self.progressBar.setValue(0)
        self.progressBar.setVisible(False)

    @pyqtSlot(int)
    def on_begin_year_sbox_valueChanged(self, sbox_value):

        print

        self.end_date = (str(sbox_value + 1) + '-01-01')
        self.end_date = datetime.strptime(self.end_date, "%Y-%m-%d").date()

        self.before_date = (str(sbox_value) + '-01-01')
        self.before_date = datetime.strptime(self.before_date, "%Y-%m-%d").date()

    def __load_role_settings(self):

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        au2_count = 0
        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        au1_count = 0
        for au2 in au_level2_list:
            au2_count = au2_count + 1
        for au1 in au_level1_list:
            au1_count = au1_count + 1
        if au1_count > 1:
            self.work_level_lbl.setText(u'Улсын хэмжээнд ажиллах аймгын тоо:'+ str(au1_count))
        else:
            self.aimag_cbox.setDisabled(True)
            if au2_count > 1:
                self.work_level_lbl.setText(u'Аймгийн хэмжээнд ажиллах сумын тоо:'+ str(au2_count))
            else:
                self.work_level_lbl.setText(u'Зөвхөн нэг суманд ажиллах эрхтэй')

        self.__create_parcel_view()

    def __create_parcel_view(self):

            au_level2_string = self.userSettings.restriction_au_level2
            au_level2_list = au_level2_string.split(",")
            sql = ""
            sql_gt1 = ""
            sql_conservation = ""
            sql_pollution = ""
            sql_fee_payment = ""
            sql_tax_payment = ""
            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql:
                    sql = "Create temp view parcel_report as" + "\n"
                else:
                    sql = sql + "UNION" + "\n"

                select = "SELECT parcel.parcel_id, parcel.area_m2, au1.code as au1_code,au2.code as au2_code, parcel.landuse,\
                                          application.app_type, app1_ext.excess_area,app_pers.share, person.id as person_pk_id, \
                                          person.type as person_type, person.name, person.middle_name, person.first_name, \
                                          application.app_no, decision.decision_no, contract.contract_no, record.record_no, \
                                          record.record_date, record.right_type, contract.contract_date, parcel.valid_till, parcel.valid_from, \
                                          landuse.code2 as landuse_code2, record.status as record_status, contract.status as contract_status " \
                         "FROM s{0}.ca_parcel parcel " \
                         "LEFT JOIN s{0}.ct_application application on application.parcel = parcel.parcel_id " \
                         "LEFT JOIN s{0}.ct_application_person_role app_pers on application.app_no = app_pers.application " \
                         "LEFT JOIN base.bs_person person ON app_pers.person = person.person_id " \
                         "LEFT JOIN s{0}.ct_contract_application_role con_app on con_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_contract contract on con_app.contract = contract.contract_no " \
                         "LEFT JOIN s{0}.ct_record_application_role rec_app on rec_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_ownership_record record on rec_app.record = record.record_no " \
                         "LEFT JOIN s{0}.ct_decision_application dec_app on dec_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_decision decision on decision.decision_no = dec_app.application "\
                         "LEFT JOIN s{0}.ct_app1_ext app1_ext on application.app_no = app1_ext.app_no "\
                         "LEFT JOIN codelists.cl_landuse_type landuse on parcel.landuse = landuse.code "\
                         "LEFT JOIN admin_units.au_level1 au1 on ST_Within(parcel.geometry, au1.geometry) "\
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry)".format(au_level2)  + "\n"

                sql = sql + select

            sql = "{0} order by parcel_id;".format(sql)

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql_gt1:
                    sql_gt1 = "Create temp view parcel_gt1 as" + "\n"
                else:
                    sql_gt1 = sql_gt1 + "UNION" + "\n"

                select = "SELECT parcel.parcel_id, parcel.area_m2, au1.code as au1_code,au2.code as au2_code,parcel.valid_from, parcel.valid_till, parcel.landuse, landuse.code2 as landuse_code2, parcel.geometry " \
                         "FROM s{0}.ca_parcel parcel " \
                         "LEFT JOIN codelists.cl_landuse_type landuse on parcel.landuse = landuse.code "\
                         "LEFT JOIN admin_units.au_level1 au1 on ST_Within(parcel.geometry, au1.geometry) "\
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry)".format(au_level2)  + "\n"

                sql_gt1 = sql_gt1 + select

            sql_gt1 = "{0} order by parcel_id;".format(sql_gt1)

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql_conservation:
                    sql_conservation = "Create temp view parcel_conservation as" + "\n"
                else:
                    sql_conservation = sql_conservation + "UNION" + "\n"

                select = "SELECT parcel.gid, parcel.conservation, parcel.area_m2, parcel.polluted_area_m2, parcel.address_khashaa, parcel.address_streetname, \
                                  parcel.address_neighbourhood, parcel.valid_from, parcel.valid_till, parcel.geometry " \
                         "FROM s{0}.ca_parcel_conservation parcel " \
                         "LEFT JOIN admin_units.au_level1 au1 on ST_Within(parcel.geometry, au1.geometry) "\
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry)".format(au_level2)  + "\n"

                sql_conservation = sql_conservation + select

            sql_conservation = "{0} order by conservation;".format(sql_conservation)

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql_pollution:
                    sql_pollution = "Create temp view parcel_pollution as" + "\n"
                else:
                    sql_pollution = sql_pollution + "UNION" + "\n"

                select = "SELECT parcel.gid, parcel.pollution, parcel.area_m2, parcel.polluted_area_m2, parcel.address_khashaa, parcel.address_streetname, \
                                  parcel.address_neighbourhood, parcel.valid_from, parcel.valid_till, parcel.geometry " \
                         "FROM s{0}.ca_parcel_pollution parcel " \
                         "LEFT JOIN admin_units.au_level1 au1 on ST_Within(parcel.geometry, au1.geometry) "\
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry)".format(au_level2)  + "\n"

                sql_pollution = sql_pollution + select

            sql_pollution = "{0} order by pollution;".format(sql_pollution)

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql_fee_payment:
                    sql_fee_payment = "Create temp view parcel_fee as" + "\n"
                else:
                    sql_fee_payment = sql_fee_payment + "UNION" + "\n"

                select = "SELECT fee_payment.id,parcel.parcel_id, parcel.area_m2, au1.code as au1_code,au2.code as au2_code, parcel.landuse,\
                                          application.app_type, \
                                          application.app_no, contract.contract_no, \
                                          fee.area as fee_area, fee.subsidized_area, fee.fee_contract, fee_payment.amount_paid, \
                                          contract.contract_date, parcel.valid_till, parcel.valid_from, \
                                          landuse.code2 as landuse_code2, contract.status as contract_status " \
                         "FROM s{0}.ca_parcel parcel " \
                         "LEFT JOIN s{0}.ct_application application on application.parcel = parcel.parcel_id " \
                         "LEFT JOIN s{0}.ct_application_person_role app_pers on application.app_no = app_pers.application " \
                         "LEFT JOIN s{0}.ct_contract_application_role con_app on con_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_contract contract on con_app.contract = contract.contract_no " \
                         "LEFT JOIN s{0}.ct_fee fee on contract.contract_no = fee.contract " \
                         "LEFT JOIN s{0}.ct_fee_payment fee_payment on fee.person = fee_payment.person " \
                         "LEFT JOIN codelists.cl_landuse_type landuse on parcel.landuse = landuse.code "\
                         "LEFT JOIN admin_units.au_level1 au1 on ST_Within(parcel.geometry, au1.geometry) "\
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry)".format(au_level2)  + "\n"

                sql_fee_payment = sql_fee_payment + select

            sql_fee_payment = "{0} group by parcel.parcel_id, parcel.area_m2, au1.code,au2.code, landuse,\
                                          app_type, id, \
                                          app_no, contract_no,\
                                          area, subsidized_area, fee_contract, amount_paid,\
                                          contract_date, valid_till, valid_from, \
                                          code2, status, left_to_pay_for_q1,left_to_pay_for_q2,left_to_pay_for_q3,left_to_pay_for_q4;".format(sql_fee_payment)

            for au_level2 in au_level2_list:

                au_level2 = au_level2.strip()
                if not sql_tax_payment:
                    sql_tax_payment = "Create temp view parcel_tax as" + "\n"
                else:
                    sql_tax_payment = sql_tax_payment + "UNION" + "\n"

                select = "SELECT tax_payment.id,parcel.parcel_id, parcel.area_m2, au1.code as au1_code,au2.code as au2_code, parcel.landuse,\
                                          application.app_type, \
                                          application.app_no, record.record_no, \
                                          tax.area as tax_area, tax.subsidized_area, tax.land_tax, tax_payment.amount_paid, \
                                          record.record_date, parcel.valid_till, parcel.valid_from, \
                                          landuse.code2 as landuse_code2, record.status as record_status " \
                         "FROM s{0}.ca_parcel parcel " \
                         "LEFT JOIN s{0}.ct_application application on application.parcel = parcel.parcel_id " \
                         "LEFT JOIN s{0}.ct_application_person_role app_pers on application.app_no = app_pers.application " \
                         "LEFT JOIN s{0}.ct_record_application_role rec_app on rec_app.application = application.app_no " \
                         "LEFT JOIN s{0}.ct_ownership_record record on rec_app.record = record.record_no " \
                         "LEFT JOIN s{0}.ct_tax_and_price tax on record.record_no = tax.record " \
                         "LEFT JOIN s{0}.ct_tax_and_price_payment tax_payment on tax.person = tax_payment.person " \
                         "LEFT JOIN codelists.cl_landuse_type landuse on parcel.landuse = landuse.code "\
                         "LEFT JOIN admin_units.au_level1 au1 on ST_Within(parcel.geometry, au1.geometry) "\
                         "LEFT JOIN admin_units.au_level2 au2 on ST_Within(parcel.geometry, au2.geometry)".format(au_level2)  + "\n"

                sql_tax_payment = sql_tax_payment + select

            sql_tax_payment = "{0} group by parcel.parcel_id, parcel.area_m2, au1.code,au2.code, landuse,\
                                          app_type, id, \
                                          app_no, record_no,\
                                          area, subsidized_area, land_tax, amount_paid,\
                                          record_date, valid_till, valid_from, \
                                          code2, status, left_to_pay_for_q1,left_to_pay_for_q2,left_to_pay_for_q3,left_to_pay_for_q4;".format(sql_tax_payment)

            try:
                self.session.execute(sql)
                self.session.execute(sql_gt1)
                self.session.execute(sql_conservation)
                self.session.execute(sql_pollution)
                self.session.execute(sql_fee_payment)
                self.session.execute(sql_tax_payment)
                self.commit()

            except SQLAlchemyError, e:
                PluginUtils.show_message(self, self.tr("LM2", "Sql Error"), e.message)
                return

    def __setup_combo_box(self):

        PluginUtils.populate_au_level1_cbox(self.aimag_cbox,True,True,False)

    def __report_gt_1(self):

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        au2_count = 0
        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        au1_count = 0
        for au2 in au_level2_list:
            au2_count = au2_count + 1
        for au1 in au_level1_list:
            au1_count = au1_count + 1

        restrictions = DatabaseUtils.working_l2_code()
        default_path = r'D:/TM_LM2/reports'
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
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_1.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_landscape()
        worksheet.set_paper(8)
        worksheet.set_margins(left=0.3, right=0.3, top=0.3, bottom=0.3)
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)

        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        row = 9
        count = 1
        code1 = 0
        code2 = 0


        worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 1 дүгээр хавсралт',format_header)
        worksheet.merge_range('K2:M2', u'/га-гаар/            Маягт ГТ-1 ',format_header)
        worksheet.merge_range('A4:A8', u'д/д', format)
        worksheet.merge_range('B4:B8', u'Аймаг/сумын нэр',format)
        worksheet.merge_range('C4:C8', u'Нийт',format)
        worksheet.write(8,0, 0,format)
        worksheet.write(8,1, 1,format)
        worksheet.write(8,2, 2,format)

        landuse_type = self.session.query(ClLanduseType).order_by(ClLanduseType.code.asc()).all()
        worksheet.merge_range('D2:J2', u'ГАЗРЫН НЭГДМЭЛ САНГИЙН АНГИЛЛЫН '+str(self.begin_year_sbox.value())+u' ОНЫ ТАЙЛАН',format_header)
        # all aimags
        if len(au_level1_list) > 1:
            admin_unit_1 = self.session.query(AuLevel1)\
                        .filter(AuLevel1.code.in_(au_level1_list)).all()
        elif len(au_level1_list) == 1 or len(au_level2_list) >= 1:
            admin_unit_1 = self.session.query(AuLevel2)\
                        .filter(AuLevel2.code.in_(au_level2_list)).all()

            for au1 in admin_unit_1:
                area_level_2 = 0
                area_level_3 = 0
                all_area_landuse = 0
                col = 0
                column = col+2

                worksheet.write(row, col, (count),format)
                worksheet.write(row, col+1, au1.name,format)
                #landuse all area
                all_area = self.session.query(func.sum(ParcelGt1.area_m2).label("area"))\
                    .join(AuLevel1, ParcelGt1.geometry.ST_Within(AuLevel1.geometry))\
                    .join(AuLevel2, ParcelGt1.geometry.ST_Within(AuLevel2.geometry))\
                    .filter(ParcelGt1.valid_till == 'infinity')\
                    .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code))\
                    .filter(ParcelGt1.valid_from < self.end_date).one()

                if all_area.area == None:
                    area_level_1 = 0
                else:
                    area_level_1 = (all_area.area/10000)
                worksheet.write(row, col+2, (round(area_level_1,2)),format)

                column_count_1 = 0
                column_count_2 = 0
                all_landuse_count = 0
                for landuse in landuse_type:
                    if code1 == str(landuse.code)[:1]:
                        if code2 == str(landuse.code)[:2]:
                            column = column + 1
                            worksheet.write(8,column, column,format)
                            worksheet.write(7,column,landuse.description,format_90)
                            #

                            all_area = self.session.query(func.sum(ParcelGt1.area_m2).label("area"))\
                                .join(AuLevel1, ParcelGt1.geometry.ST_Within(AuLevel1.geometry))\
                                .join(AuLevel2, ParcelGt1.geometry.ST_Within(AuLevel2.geometry))\
                                .filter(ParcelGt1.landuse == landuse.code)\
                                .filter(ParcelGt1.valid_till == 'infinity')\
                                .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code))\
                                .filter(ParcelGt1.valid_from < self.end_date).one()
                            if all_area.area == None:
                                area_ga = 0
                            else:
                                area_ga = (all_area.area/10000)
                            worksheet.write(row, column, (round(area_ga,2)),format)
                            area_level_3 = area_level_3 + area_ga
                            area_level_2 = area_level_2 + area_ga
                            all_area_landuse = all_area_landuse + area_ga
                            all_landuse_count += 1
                            column_count_2 += 1
                            column_count_1 += 1
                        else:
                            code2 = 0
                            worksheet.write(row, column-column_count_2, (round(area_level_3,2)),format)
                            if column_count_2 > 1:
                                worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                            else:
                                worksheet.write(6,column, u"Үүнээс",format)
                            area_level_3 = 0
                            column_count_2 = 0

                        if code2 == 0:
                            code2 = str(landuse.code)[:2]
                            column = column + 1
                            worksheet.write(8,column, column,format)
                            worksheet.merge_range(6,column,7,column, landuse.description2,format_90)
                            column = column + 1
                            worksheet.write(8,column, column,format)
                            all_landuse_count += 1
                            column_count_1 += 1
                            worksheet.write(7,column,landuse.description,format_90)
                            all_area = self.session.query(func.sum(ParcelGt1.area_m2).label("area"))\
                                .join(AuLevel1, ParcelGt1.geometry.ST_Within(AuLevel1.geometry))\
                                .join(AuLevel2, ParcelGt1.geometry.ST_Within(AuLevel2.geometry))\
                                .filter(ParcelGt1.landuse == landuse.code)\
                                .filter(ParcelGt1.valid_till == 'infinity')\
                                .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code))\
                                .filter(ParcelGt1.valid_from < self.end_date).one()
                            if all_area.area == None:
                                area_ga = 0
                            else:
                                area_ga = (all_area.area/10000)
                            worksheet.write(row, column, (round(area_ga,1)),format)
                            area_level_3 = area_level_3 + area_ga
                            area_level_2 = area_level_2 + area_ga
                            all_area_landuse = all_area_landuse + area_ga
                            all_landuse_count += 1
                            column_count_2 += 1
                            column_count_1 += 1
                    else:
                        worksheet.write(row, column-column_count_1, (round(area_level_2,2)),format)
                        worksheet.merge_range(5,column-column_count_1+1,5,column, u"Үүнээс",format)
                        if code1 == '1':
                            worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_1,format)
                        elif code1 == '2':
                            worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_2,format)
                        elif code1 == '3':
                            worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_3,format)
                        elif code1 == '4':
                            worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_4,format)
                        elif code1 == '5':
                            worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_5,format)
                        elif code1 == '6':
                            worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_6,format)
                        code1 = 0
                        column_count_1 = 0
                        area_level_2 = 0

                        code2 = 0
                        worksheet.write(row, column-column_count_2, (round(area_level_3,2)),format)
                        if column_count_2 > 1:
                            worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                        else:
                            worksheet.write(6,column, u"Үүнээс",format)
                        area_level_3 = 0
                        column_count_2 = 0

                    if code1 == 0:
                        code1 = str(landuse.code)[:1]
                        code2 = str(landuse.code)[:2]
                        column = column + 1
                        worksheet.write(8,column, column,format)
                        worksheet.merge_range(5,column,7,column, u'Бүгд',format)
                        column = column + 1
                        worksheet.write(8,column, column,format)
                        all_landuse_count += 1
                        worksheet.merge_range(6,column,7,column, landuse.description2,format_90)
                        column_count_1 += 1
                        all_landuse_count += 1
                        column = column + 1
                        worksheet.write(8,column, column,format)
                        worksheet.write(7,column,landuse.description,format_90)
                        all_area = self.session.query(func.sum(ParcelGt1.area_m2).label("area"))\
                                .join(AuLevel1, ParcelGt1.geometry.ST_Within(AuLevel1.geometry))\
                                .join(AuLevel2, ParcelGt1.geometry.ST_Within(AuLevel2.geometry))\
                                .filter(ParcelGt1.landuse == landuse.code)\
                                .filter(ParcelGt1.valid_till == 'infinity')\
                                .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code))\
                                .filter(ParcelGt1.valid_from < self.end_date).one()
                        if all_area.area == None:
                            area_ga = 0
                        else:
                            area_ga = (all_area.area/10000)
                        worksheet.write(row, column, (round(area_ga,2)),format)
                        area_level_3 = area_level_3 + area_ga
                        area_level_2 = area_level_2 + area_ga
                        all_area_landuse = all_area_landuse + area_ga
                        all_landuse_count += 1
                        column_count_1 += 1
                        column_count_2 += 1
                code1 = 0
                worksheet.write(row, column-column_count_1, (round(area_level_2,2)),format)
                worksheet.merge_range(5,column-column_count_1+1,5,column, u"Үүнээс",format)
                worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_6,format)
                worksheet.merge_range(3,3,3,column, u"Үүнээс газрын ангиаллын төрлөөр",format)

                code2 = 0
                worksheet.write(row, column-column_count_2, (round(area_level_3,2)),format)
                if column_count_2 > 1:
                    worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                else:
                    worksheet.write(6,column, u"Үүнээс",format)
                worksheet.write(row, column-all_landuse_count, (round(all_area_landuse,2)),format)
                # cell = xl_rowcol_to_cell(row, column-all_landuse_count)
                # column = xl_col_to_name(column)
                # print cell+'-'+column


                value_p = self.progressBar.value() + 1
                self.progressBar.setValue(value_p)
                row += 1
                count +=1
            worksheet.merge_range(row,0,row,1,u"ДҮН",format)
            for i in range(2,column+1):
                cell_up = xl_rowcol_to_cell(9, i)
                cell_down = xl_rowcol_to_cell(row-1, i)
                worksheet.write(row,i,'=SUM('+cell_up+':'+cell_down+')',format)
                i = i + 1

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_1.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_2(self):

        restrictions = DatabaseUtils.working_l2_code()
        default_path = r'D:/TM_LM2/reports'
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
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_2.xlsx")
        worksheet = workbook.add_worksheet()

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)
        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        col = 0
        column = col+4
        code1 = 0
        code2 = 0


        worksheet.merge_range('D2:J2', u'ГАЗРЫН НЭГДМЭЛ САНГИЙН ЭРХ ЗҮЙН БАЙДЛЫН '+str(self.begin_year_sbox.value())+u' ОНЫ ТАЙЛАН',format_header)
        worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 2 дугаар хавсралт',format_header)
        worksheet.merge_range('K2:M2', u'/га-гаар/            Маягт ГТ-2 ',format_header)
        worksheet.merge_range('A4:A8', u'д/д', format)
        worksheet.merge_range('B4:C8', u'Газар өмчлөгч, эзэмшигч, ашиглагч',format)
        worksheet.merge_range('D4:D8', u'д/д',format)
        worksheet.merge_range('E4:E8', u'Нийт',format)
        worksheet.write(8,0, u'А',format)
        worksheet.merge_range(8,1,8,2, u'Б',format)
        worksheet.write(8,3, 0,format)
        worksheet.write(8,4, 1,format)
        worksheet.merge_range('B10:B11', u'Өмчлөгч',format_90)
        worksheet.merge_range('B12:B15', u'Эзэмшигч',format_90)
        worksheet.merge_range('B16:B19', u'Бусдын эзэмшил газрыг ашиглагч Монгол улсын',format_90)
        worksheet.merge_range('B20:B22', u'Ашиглагч',format_90)
        worksheet.write('A10', 1,format)
        worksheet.write('A11', 2,format)
        worksheet.write('A12', 1,format)
        worksheet.write('A13', 2,format)
        worksheet.write('A14', 3,format)
        worksheet.write('A15', 4,format)
        worksheet.write('A16', 5,format)
        worksheet.write('A17', 6,format)
        worksheet.write('A18', 7,format)
        worksheet.write('A19', 8,format)
        worksheet.write('A20', 9,format)
        worksheet.write('A21', 10,format)
        worksheet.write('A22', 11,format)

        worksheet.write('C10', u'а/гэр бүлийн хэрэгцээнд',format)
        worksheet.write('C11', u'б/аж ахуйн зориулалтаар',format)
        worksheet.write('C12', u'а/иргэн',format)
        worksheet.write('C13', u'б/төрийн байгууллага',format)
        worksheet.write('C14', u'в/аж ахуйн нэгж',format)
        worksheet.write('C15', u'Дүн',format)
        worksheet.write('C16', u'а/иргэн',format)
        worksheet.write('C17', u'б/төрийн байгууллага',format)
        worksheet.write('C18', u'в/аж ахуйн нэгж',format)
        worksheet.write('C19', u'Дүн',format)
        worksheet.write('C20', u'а/гадаадын иргэн болон харъялалгүй хүн',format)
        worksheet.write('C21', u'б/гадаадын хөрөнгө оруулалтай аж ахуйн нэгж, гадаадын хуулийн этгээд',format)
        worksheet.write('C22', u'Дүн',format)
        worksheet.merge_range('A23:C23', u'Нийт дүн',format)

        worksheet.write('D10', 1,format)
        worksheet.write('D11', 2,format)
        worksheet.write('D12', 3,format)
        worksheet.write('D13', 4,format)
        worksheet.write('D14', 5,format)
        worksheet.write('D15', 6,format)
        worksheet.write('D16', 7,format)
        worksheet.write('D17', 8,format)
        worksheet.write('D18', 9,format)
        worksheet.write('D19', 10,format)
        worksheet.write('D20', 11,format)
        worksheet.write('D21', 12,format)
        worksheet.write('D22', 13,format)
        worksheet.write('D23', 14,format)

        landuse_type = self.session.query(ClLanduseType).order_by(ClLanduseType.code.asc()).all()
        column_count_1 = 0
        column_count_2 = 0
        all_landuse_count = 0
        column_number = 1
        landuse_all_1_level_1 = 0
        landuse_all_1_level_2 = 0
        landuse_all_1_level_3 = 0
        landuse_all_2_level_1 = 0
        landuse_all_2_level_2 = 0
        landuse_all_2_level_3 = 0
        landuse_all_3_level_1 = 0
        landuse_all_3_level_2 = 0
        landuse_all_3_level_3 = 0
        landuse_all_4_level_1 = 0
        landuse_all_4_level_2 = 0
        landuse_all_4_level_3 = 0
        landuse_all_5_level_1 = 0
        landuse_all_5_level_2 = 0
        landuse_all_5_level_3 = 0
        landuse_all_7_level_1 = 0
        landuse_all_7_level_2 = 0
        landuse_all_7_level_3 = 0
        landuse_all_8_level_1 = 0
        landuse_all_8_level_2 = 0
        landuse_all_8_level_3 = 0
        landuse_all_9_level_1 = 0
        landuse_all_9_level_2 = 0
        landuse_all_9_level_3 = 0
        landuse_all_11_level_1 = 0
        landuse_all_11_level_2 = 0
        landuse_all_11_level_3 = 0
        landuse_all_12_level_1 = 0
        landuse_all_12_level_2 = 0
        landuse_all_12_level_3 = 0

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        au2_count = 0
        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        au1_count = 0
        for au2 in au_level2_list:
            au2_count = au2_count + 1
        for au1 in au_level1_list:
            au1_count = au1_count + 1
        if au1_count > 1:
            self.work_level_lbl.setText(u'Улсын хэмжээнд ажиллах аймгын тоо:'+ str(au1_count))
        else:
            self.aimag_cbox.setDisabled(True)
            if au2_count > 1:
                self.work_level_lbl.setText(u'Аймгийн хэмжээнд ажиллах сумын тоо:'+ str(au2_count))
            else:
                self.work_level_lbl.setText(u'Зөвхөн нэг суманд ажиллах эрхтэй')

        progress_count = len(landuse_type)
        self.progressBar.setMaximum(progress_count)
        for landuse in landuse_type:
            area_ga = 0
            if code1 == str(landuse.code)[:1]:
                if code2 == str(landuse.code)[:2]:
                    column = column + 1
                    column_number = column_number + 1
                    worksheet.write(8,column, column_number,format)
                    worksheet.write(7,column,landuse.description,format_90)
                    #OWNERSHIP
                    #NO 1
                    landuse_area_1 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area"))\
                                    .filter(ParcelReport.app_type == 1)\
                                    .filter(ParcelReport.valid_till == 'infinity')\
                                    .filter(ParcelReport.record_date < self.end_date)\
                                    .filter(ParcelReport.record_status == 20)\
                                    .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                    .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_1.area == None or landuse_area_1.area == 0:
                        area_no_1 = ''
                    else:
                        area_no_1 = round((landuse_area_1.area/10000),2)
                    worksheet.write(9, column, area_no_1,format)
                    if area_no_1 == '':
                        area_no_1 = 0
                    landuse_all_1_level_1 = landuse_all_1_level_1 + area_no_1
                    landuse_all_1_level_2 = landuse_all_1_level_2 + area_no_1
                    landuse_all_1_level_3 = landuse_all_1_level_3 + area_no_1
                    #NO 2
                    landuse_area_2 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 4)\
                                    .filter(ParcelReport.valid_till == 'infinity')\
                                    .filter(ParcelReport.record_date < self.end_date)\
                                    .filter(ParcelReport.record_status == 20)\
                                    .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                    .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_2.area == None or landuse_area_1.area == 0:
                        area_no_2 = ''
                    else:
                        area_no_2 = round((landuse_area_2.area/10000),2)
                    worksheet.write(10, column, area_no_2,format)
                    if area_no_2 == '':
                        area_no_2 = 0
                    landuse_all_2_level_1 = landuse_all_2_level_1 + area_no_2
                    landuse_all_2_level_2 = landuse_all_2_level_2 + area_no_2
                    landuse_all_2_level_3 = landuse_all_2_level_3 + area_no_2
                    #POSSESS
                    #NO 3
                    landuse_area_3 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_3.area == None or landuse_area_3.area == 0:
                        area_no_3 = ''
                    else:
                        area_no_3 = round((landuse_area_3.area/10000),2)
                    worksheet.write(11, column, area_no_3,format)
                    if area_no_3 == '':
                        area_no_3 = 0
                    landuse_all_3_level_1 = landuse_all_3_level_1 + area_no_3
                    landuse_all_3_level_2 = landuse_all_3_level_2 + area_no_3
                    landuse_all_3_level_3 = landuse_all_3_level_3 + area_no_3
                    #NO 4
                    landuse_area_4 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_4.area == None or landuse_area_4.area == 0:
                        area_no_4 = ''
                    else:
                        area_no_4 = round((landuse_area_4.area/10000),2)
                    worksheet.write(12, column, area_no_4,format)
                    if area_no_4 == '':
                        area_no_4 = 0
                    landuse_all_4_level_1 = landuse_all_4_level_1 + area_no_4
                    landuse_all_4_level_2 = landuse_all_4_level_2 + area_no_4
                    landuse_all_4_level_3 = landuse_all_4_level_3 + area_no_4
                    #NO 5
                    landuse_area_5 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_5.area == None or landuse_area_5.area == 0:
                        area_no_5 = ''
                    else:
                        area_no_5 = round((landuse_area_5.area/10000),2)
                    worksheet.write(13, column, area_no_5,format)
                    if area_no_5 == '':
                        area_no_5 = 0
                    landuse_all_5_level_1 = landuse_all_5_level_1 + area_no_5
                    landuse_all_5_level_2 = landuse_all_5_level_2 + area_no_5
                    landuse_all_5_level_3 = landuse_all_5_level_3 + area_no_5
                    #NO 6 ALL
                    cell_up = xl_rowcol_to_cell(11, column)
                    cell_down = xl_rowcol_to_cell(13, column)
                    worksheet.write(14, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #POSSESSION RIGHT TO BE USED BY OTHERS
                    #NO 7
                    landuse_area_7 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_7.area == None or landuse_area_7.area == 0:
                        area_no_7 = ''
                    else:
                        area_no_7 = round((landuse_area_7.area/10000),2)
                    worksheet.write(15, column, area_no_7,format)
                    if area_no_7 == '':
                        area_no_7 = 0
                    landuse_all_7_level_1 = landuse_all_7_level_1 + area_no_7
                    landuse_all_7_level_2 = landuse_all_7_level_2 + area_no_7
                    landuse_all_7_level_3 = landuse_all_7_level_3 + area_no_7
                    #NO 8
                    landuse_area_8 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_8.area == None or landuse_area_8.area == 0:
                        area_no_8 = ''
                    else:
                        area_no_8 = round((landuse_area_8.area/10000),2)
                    worksheet.write(16, column, area_no_8,format)
                    if area_no_8 == '':
                        area_no_8 = 0
                    landuse_all_8_level_1 = landuse_all_8_level_1 + area_no_8
                    landuse_all_8_level_2 = landuse_all_8_level_2 + area_no_8
                    landuse_all_8_level_3 = landuse_all_8_level_3 + area_no_8
                    #NO 9
                    landuse_area_9 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_9.area == None or landuse_area_9.area == 0:
                        area_no_9 = ''
                    else:
                        area_no_9 = round((landuse_area_9.area/10000),2)
                    worksheet.write(17, column, area_no_9,format)
                    if area_no_9 == '':
                        area_no_9 = 0
                    landuse_all_9_level_1 = landuse_all_9_level_1 + area_no_9
                    landuse_all_9_level_2 = landuse_all_9_level_2 + area_no_9
                    landuse_all_9_level_3 = landuse_all_9_level_3 + area_no_9
                    #NO 10
                    cell_up = xl_rowcol_to_cell(15, column)
                    cell_down = xl_rowcol_to_cell(17, column)
                    worksheet.write(18, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #USE
                    #NO 11
                    landuse_area_11 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 50)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_11.area == None or landuse_area_11.area == 0:
                        area_no_11 = ''
                    else:
                        area_no_11 = round((landuse_area_11.area/10000),2)
                    worksheet.write(19, column, area_no_11,format)
                    if area_no_11 == '':
                        area_no_11 = 0
                    landuse_all_11_level_1 = landuse_all_11_level_1 + area_no_11
                    landuse_all_11_level_2 = landuse_all_11_level_2 + area_no_11
                    landuse_all_11_level_3 = landuse_all_11_level_3 + area_no_11
                    #NO 12
                    landuse_area_12 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 60)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_12.area == None or landuse_area_12.area == 0:
                        area_no_12 = ''
                    else:
                        area_no_12 = round((landuse_area_12.area/10000),2)
                    worksheet.write(20, column, area_no_12,format)
                    if area_no_12 == '':
                        area_no_12 = 0
                    landuse_all_12_level_1 = landuse_all_12_level_1 + area_no_12
                    landuse_all_12_level_2 = landuse_all_12_level_2 + area_no_12
                    landuse_all_12_level_3 = landuse_all_12_level_3 + area_no_12
                    #NO 13 USE ALL
                    cell_up = xl_rowcol_to_cell(19, column)
                    cell_down = xl_rowcol_to_cell(20, column)
                    worksheet.write(21, column, '=SUM('+cell_up+':'+cell_down+')',format)

                    #ALL AREA
                    cell_1 = xl_rowcol_to_cell(9, column)
                    cell_2 = xl_rowcol_to_cell(10, column)
                    cell_3 = xl_rowcol_to_cell(14, column)
                    cell_4 = xl_rowcol_to_cell(18, column)
                    cell_5 = xl_rowcol_to_cell(21, column)
                    worksheet.write_formula(22,column,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                    all_landuse_count += 1
                    column_count_2 += 1
                    column_count_1 += 1
                else:
                    code2 = 0
                    if column_count_2 > 1:
                        worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                    else:
                        worksheet.write(6,column, u"Үүнээс",format)
                    #OWNERSHIP
                    #NO 1
                    if landuse_all_1_level_2 == 0:
                        landuse_all_1_level_2 = ''
                    else:
                        landuse_all_1_level_2 = (round(landuse_all_1_level_2,2))
                    worksheet.write(9, column-column_count_2, landuse_all_1_level_2,format)
                    landuse_all_1_level_2 = 0
                    #NO 2
                    if landuse_all_2_level_2 == 0:
                        landuse_all_2_level_2 = ''
                    else:
                        landuse_all_2_level_2 = (round(landuse_all_2_level_2,2))
                    worksheet.write(10, column-column_count_2, landuse_all_2_level_2,format)
                    landuse_all_2_level_2 = 0
                    #POSSESS
                    #NO 3
                    if landuse_all_3_level_2 == 0:
                        landuse_all_3_level_2 = ''
                    else:
                        landuse_all_3_level_2 = (round(landuse_all_3_level_2,2))
                    worksheet.write(11, column-column_count_2, landuse_all_3_level_2,format)
                    landuse_all_3_level_2 = 0
                    #NO 4
                    if landuse_all_4_level_2 == 0:
                        landuse_all_4_level_2 = ''
                    else:
                        landuse_all_4_level_2 = (round(landuse_all_4_level_2,2))
                    worksheet.write(12, column-column_count_2, landuse_all_4_level_2,format)
                    landuse_all_4_level_2 = 0
                    #NO 5
                    if landuse_all_5_level_2 == 0:
                        landuse_all_5_level_2 = ''
                    else:
                        landuse_all_5_level_2 = (round(landuse_all_5_level_2,2))
                    worksheet.write(13, column-column_count_2, landuse_all_5_level_2,format)
                    landuse_all_5_level_2 = 0
                    #NO 6
                    cell_up = xl_rowcol_to_cell(11, column-column_count_2)
                    cell_down = xl_rowcol_to_cell(13, column-column_count_2)
                    worksheet.write(14,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                    #NO 7
                    if landuse_all_7_level_2 == 0:
                        landuse_all_7_level_2 = ''
                    else:
                        landuse_all_7_level_2 = (round(landuse_all_7_level_2,2))
                    worksheet.write(15, column-column_count_2, landuse_all_7_level_2,format)
                    landuse_all_7_level_2 = 0
                    #NO 8
                    if landuse_all_8_level_2 == 0:
                        landuse_all_8_level_2 = ''
                    else:
                        landuse_all_8_level_2 = (round(landuse_all_8_level_2,2))
                    worksheet.write(16, column-column_count_2, landuse_all_8_level_2,format)
                    landuse_all_8_level_2 = 0
                    #NO 9
                    if landuse_all_9_level_2 == 0:
                        landuse_all_9_level_2 = ''
                    else:
                        landuse_all_9_level_2 = (round(landuse_all_9_level_2,2))
                    worksheet.write(17, column-column_count_2, landuse_all_9_level_2,format)
                    landuse_all_9_level_2 = 0
                    #NO 10
                    cell_up = xl_rowcol_to_cell(15, column-column_count_2)
                    cell_down = xl_rowcol_to_cell(17, column-column_count_2)
                    worksheet.write(18,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                    #NO 11
                    if landuse_all_11_level_2 == 0:
                        landuse_all_11_level_2 = ''
                    else:
                        landuse_all_11_level_2 = (round(landuse_all_11_level_2,2))
                    worksheet.write(19, column-column_count_2, landuse_all_11_level_2,format)
                    landuse_all_11_level_2 = 0
                    #NO 12
                    if landuse_all_12_level_2 == 0:
                        landuse_all_12_level_2 = ''
                    else:
                        landuse_all_12_level_2 = (round(landuse_all_12_level_2,2))
                    worksheet.write(20, column-column_count_2, landuse_all_12_level_2,format)
                    landuse_all_12_level_2 = 0
                    #NO 13
                    cell_up = xl_rowcol_to_cell(19, column-column_count_2)
                    cell_down = xl_rowcol_to_cell(20, column-column_count_2)
                    worksheet.write(21,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                    #ALL AREA
                    cell_1 = xl_rowcol_to_cell(9, column-column_count_2)
                    cell_2 = xl_rowcol_to_cell(10, column-column_count_2)
                    cell_3 = xl_rowcol_to_cell(14, column-column_count_2)
                    cell_4 = xl_rowcol_to_cell(18, column-column_count_2)
                    cell_5 = xl_rowcol_to_cell(21, column-column_count_2)
                    worksheet.write_formula(22,column-column_count_2,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                    column_count_2 = 0

                if code2 == 0:
                    #COUNTS AND HEADER
                    code2 = str(landuse.code)[:2]
                    column = column + 1
                    column_number = column_number + 1
                    worksheet.write(8,column, column_number,format)
                    worksheet.merge_range(6,column,7,column, landuse.description2,format_90)
                    column = column + 1
                    column_number = column_number + 1
                    worksheet.write(8,column, column_number,format)
                    all_landuse_count += 1
                    column_count_1 += 1
                    worksheet.write(7,column,landuse.description,format_90)
                    #NO 1
                    landuse_area_1 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 1)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.record_date < self.end_date)\
                                .filter(ParcelReport.record_status == 20)\
                                .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_1.area == None or landuse_area_1.area == 0:
                        area_no_1 = ''
                    else:
                        area_no_1 = round((landuse_area_1.area/10000),2)
                    worksheet.write(9, column, area_no_1,format)
                    if area_no_1 == '':
                        area_no_1 = 0
                    landuse_all_1_level_1 = landuse_all_1_level_1 + area_no_1
                    landuse_all_1_level_2 = landuse_all_1_level_2 + area_no_1
                    landuse_all_1_level_3 = landuse_all_1_level_3 + area_no_1
                    #NO 2
                    landuse_area_2 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 4)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.record_date < self.end_date)\
                                .filter(ParcelReport.record_status == 20)\
                                .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_2.area == None or landuse_area_2.area == 0:
                        area_no_2 = ''
                    else:
                        area_no_2 = round((landuse_area_2.area/10000), 2)
                    worksheet.write(10, column, area_no_2,format)
                    if area_no_2 == '':
                        area_no_2 = 0
                    landuse_all_2_level_1 = landuse_all_2_level_1 + area_no_2
                    landuse_all_2_level_2 = landuse_all_2_level_2 + area_no_2
                    landuse_all_2_level_3 = landuse_all_2_level_3 + area_no_2

                    #POSSESS
                    #NO 3
                    landuse_area_3 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_3.area == None or landuse_area_3.area == 0:
                        area_no_3 = ''
                    else:
                        area_no_3 = round((landuse_area_3.area/10000),2)
                    worksheet.write(11, column, area_no_3,format)
                    if area_no_3 == '':
                        area_no_3 = 0
                    landuse_all_3_level_1 = landuse_all_3_level_1 + area_no_3
                    landuse_all_3_level_2 = landuse_all_3_level_2 + area_no_3
                    landuse_all_3_level_3 = landuse_all_3_level_3 + area_no_3
                    #NO 4
                    landuse_area_4 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_4.area == None or landuse_area_4.area == 0:
                        area_no_4 = ''
                    else:
                        area_no_4 = round((landuse_area_4.area/10000),2)
                    worksheet.write(12, column, area_no_4,format)
                    if area_no_4 == '':
                        area_no_4 = 0
                    landuse_all_4_level_1 = landuse_all_4_level_1 + area_no_4
                    landuse_all_4_level_2 = landuse_all_4_level_2 + area_no_4
                    landuse_all_4_level_3 = landuse_all_4_level_3 + area_no_4
                    #NO 5
                    landuse_area_5 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_5.area == None or landuse_area_5.area == 0:
                        area_no_5 = ''
                    else:
                        area_no_5 = round((landuse_area_5.area/10000),2)
                    worksheet.write(13, column, area_no_5,format)
                    if area_no_5 == '':
                        area_no_5 = 0
                    landuse_all_5_level_1 = landuse_all_5_level_1 + area_no_5
                    landuse_all_5_level_2 = landuse_all_5_level_2 + area_no_5
                    landuse_all_5_level_3 = landuse_all_5_level_3 + area_no_5
                    #NO 6 ALL
                    cell_up = xl_rowcol_to_cell(11, column)
                    cell_down = xl_rowcol_to_cell(13, column)
                    worksheet.write(14, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #POSSESSION RIGHT TO BE USED BY OTHERS
                    #NO 7
                    landuse_area_7 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_7.area == None or landuse_area_7.area == 0:
                        area_no_7 = ''
                    else:
                        area_no_7 = round((landuse_area_7.area/10000),2)
                    worksheet.write(15, column, area_no_7,format)
                    if area_no_7 == '':
                        area_no_7 = 0
                    landuse_all_7_level_1 = landuse_all_7_level_1 + area_no_7
                    landuse_all_7_level_2 = landuse_all_7_level_2 + area_no_7
                    landuse_all_7_level_3 = landuse_all_7_level_3 + area_no_7
                    #NO 8
                    landuse_area_8 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_8.area == None or landuse_area_8.area == 0:
                        area_no_8 = ''
                    else:
                        area_no_8 = round((landuse_area_8.area/10000),2)
                    worksheet.write(16, column, area_no_8,format)
                    if area_no_8 == '':
                        area_no_8 = 0
                    landuse_all_8_level_1 = landuse_all_8_level_1 + area_no_8
                    landuse_all_8_level_2 = landuse_all_8_level_2 + area_no_8
                    landuse_all_8_level_3 = landuse_all_8_level_3 + area_no_8
                    #NO 9
                    landuse_area_9 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_9.area == None or landuse_area_9.area == 0:
                        area_no_9 = ''
                    else:
                        area_no_9 = round((landuse_area_9.area/10000),2)
                    worksheet.write(17, column, area_no_9,format)
                    if area_no_9 == '':
                        area_no_9 = 0
                    landuse_all_9_level_1 = landuse_all_9_level_1 + area_no_9
                    landuse_all_9_level_2 = landuse_all_9_level_2 + area_no_9
                    landuse_all_9_level_3 = landuse_all_9_level_3 + area_no_9
                    #NO 10
                    cell_up = xl_rowcol_to_cell(15, column)
                    cell_down = xl_rowcol_to_cell(17, column)
                    worksheet.write(18, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #USE
                    #NO 11
                    landuse_area_11 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 50)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_11.area == None or landuse_area_11.area == 0:
                        area_no_11 = ''
                    else:
                        area_no_11 = round((landuse_area_11.area/10000),2)
                    worksheet.write(19, column, area_no_11,format)
                    if area_no_11 == '':
                        area_no_11 = 0
                    landuse_all_11_level_1 = landuse_all_11_level_1 + area_no_11
                    landuse_all_11_level_2 = landuse_all_11_level_2 + area_no_11
                    landuse_all_11_level_3 = landuse_all_11_level_3 + area_no_11
                    #NO 12
                    landuse_area_12 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 60)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                    if landuse_area_12.area == None or landuse_area_12.area == 0:
                        area_no_12 = ''
                    else:
                        area_no_12 = round((landuse_area_12.area/10000),2)
                    worksheet.write(20, column, area_no_12,format)
                    if area_no_12 == '':
                        area_no_12 = 0
                    landuse_all_12_level_1 = landuse_all_12_level_1 + area_no_12
                    landuse_all_12_level_2 = landuse_all_12_level_2 + area_no_12
                    landuse_all_12_level_3 = landuse_all_12_level_3 + area_no_12
                    #NO 13 USE ALL
                    cell_up = xl_rowcol_to_cell(19, column)
                    cell_down = xl_rowcol_to_cell(20, column)
                    worksheet.write(21, column, '=SUM('+cell_up+':'+cell_down+')',format)

                    #ALL AREA
                    cell_1 = xl_rowcol_to_cell(9, column)
                    cell_2 = xl_rowcol_to_cell(10, column)
                    cell_3 = xl_rowcol_to_cell(14, column)
                    cell_4 = xl_rowcol_to_cell(18, column)
                    cell_5 = xl_rowcol_to_cell(21, column)
                    worksheet.write_formula(22,column,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)
                    #COUNTS
                    all_landuse_count += 1
                    column_count_2 += 1
                    column_count_1 += 1
            else:
                #HEADER
                worksheet.merge_range(5,column-column_count_1+1,5,column, u"Үүнээс",format)
                if code1 == '1':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_1,format)
                elif code1 == '2':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_2,format)
                elif code1 == '3':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_3,format)
                elif code1 == '4':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_4,format)
                elif code1 == '5':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_5,format)
                elif code1 == '6':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_6,format)
                if column_count_2 > 1:
                    worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                else:
                    worksheet.write(6,column, u"Үүнээс",format)
                #OWNERSHIP
                #NO 1
                if landuse_all_1_level_1 == 0:
                    landuse_all_1_level_1 = ''
                else:
                    landuse_all_1_level_1 = (round(landuse_all_1_level_1,2))
                worksheet.write(9, column-column_count_1, landuse_all_1_level_1,format)
                if landuse_all_1_level_2 == 0:
                    landuse_all_1_level_2 = ''
                else:
                    landuse_all_1_level_2 = (round(landuse_all_1_level_2,2))
                worksheet.write(9, column-column_count_2, landuse_all_1_level_2,format)
                landuse_all_1_level_1 = 0
                landuse_all_1_level_2 = 0
                #NO 2
                if landuse_all_2_level_1 == 0:
                    landuse_all_2_level_1 = ''
                else:
                    landuse_all_2_level_1 = (round(landuse_all_2_level_1,2))
                worksheet.write(10, column-column_count_1, landuse_all_2_level_1,format)
                if landuse_all_2_level_2 == 0:
                    landuse_all_2_level_2 = ''
                else:
                    landuse_all_2_level_2 = (round(landuse_all_2_level_2,2))
                worksheet.write(10, column-column_count_2, landuse_all_2_level_2,format)
                landuse_all_2_level_1 = 0
                landuse_all_2_level_2 = 0
                #POSSESS
                #NO 3
                if landuse_all_3_level_1 == 0:
                    landuse_all_3_level_1 = ''
                else:
                    landuse_all_3_level_1 = (round(landuse_all_3_level_1,2))
                worksheet.write(11, column-column_count_1, landuse_all_3_level_1,format)
                if landuse_all_3_level_2 == 0:
                    landuse_all_3_level_2 = ''
                else:
                    landuse_all_3_level_2 = (round(landuse_all_3_level_2,2))
                worksheet.write(11, column-column_count_2, landuse_all_3_level_2,format)
                landuse_all_3_level_1 = 0
                landuse_all_3_level_2 = 0
                #NO 4
                if landuse_all_4_level_1 == 0:
                    landuse_all_4_level_1 = ''
                else:
                    landuse_all_4_level_1 = (round(landuse_all_4_level_1,2))
                worksheet.write(12, column-column_count_1, landuse_all_4_level_1,format)
                if landuse_all_4_level_2 == 0:
                    landuse_all_4_level_2 = ''
                else:
                    landuse_all_4_level_2 = (round(landuse_all_4_level_2,2))
                worksheet.write(12, column-column_count_2, landuse_all_4_level_2,format)
                landuse_all_4_level_1 = 0
                landuse_all_4_level_2 = 0
                #NO 5
                if landuse_all_5_level_1 == 0:
                    landuse_all_5_level_1 = ''
                else:
                    landuse_all_5_level_1 = (round(landuse_all_5_level_1,2))
                worksheet.write(13, column-column_count_1, landuse_all_5_level_1,format)
                if landuse_all_5_level_2 == 0:
                    landuse_all_5_level_2 = ''
                else:
                    landuse_all_5_level_2 = (round(landuse_all_5_level_2,2))
                worksheet.write(13, column-column_count_2, landuse_all_5_level_2,format)
                landuse_all_5_level_1 = 0
                landuse_all_5_level_2 = 0
                #NO 6
                cell_up = xl_rowcol_to_cell(11, column-column_count_1)
                cell_down = xl_rowcol_to_cell(13, column-column_count_1)
                worksheet.write(14,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
                cell_up = xl_rowcol_to_cell(11, column-column_count_2)
                cell_down = xl_rowcol_to_cell(13, column-column_count_2)
                worksheet.write(14,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                #NO 7
                if landuse_all_7_level_1 == 0:
                    landuse_all_7_level_1 = ''
                else:
                    landuse_all_7_level_1 = (round(landuse_all_7_level_1,2))
                worksheet.write(15, column-column_count_1, landuse_all_7_level_1,format)
                if landuse_all_7_level_2 == 0:
                    landuse_all_7_level_2 = ''
                else:
                    landuse_all_7_level_2 = (round(landuse_all_7_level_2,2))
                worksheet.write(15, column-column_count_2, landuse_all_7_level_2,format)
                landuse_all_7_level_1 = 0
                landuse_all_7_level_2 = 0
                #NO 8
                if landuse_all_8_level_1 == 0:
                    landuse_all_8_level_1 = ''
                else:
                    landuse_all_8_level_1 = (round(landuse_all_8_level_1,2))
                worksheet.write(16, column-column_count_1, landuse_all_8_level_1,format)
                if landuse_all_8_level_2 == 0:
                    landuse_all_8_level_2 = ''
                else:
                    landuse_all_8_level_2 = (round(landuse_all_8_level_2,2))
                worksheet.write(16, column-column_count_2, landuse_all_8_level_2,format)
                landuse_all_8_level_1 = 0
                landuse_all_8_level_2 = 0
                #NO 9
                if landuse_all_9_level_1 == 0:
                    landuse_all_9_level_1 = ''
                else:
                    landuse_all_9_level_1 = (round(landuse_all_9_level_1,2))
                worksheet.write(17, column-column_count_1, landuse_all_9_level_1,format)
                if landuse_all_9_level_2 == 0:
                    landuse_all_9_level_2 = ''
                else:
                    landuse_all_9_level_2 = (round(landuse_all_9_level_2,2))
                worksheet.write(17, column-column_count_2, landuse_all_9_level_2,format)
                landuse_all_9_level_1 = 0
                landuse_all_9_level_2 = 0
                #NO 10
                cell_up = xl_rowcol_to_cell(15, column-column_count_1)
                cell_down = xl_rowcol_to_cell(17, column-column_count_1)
                worksheet.write(18,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
                cell_up = xl_rowcol_to_cell(15, column-column_count_2)
                cell_down = xl_rowcol_to_cell(17, column-column_count_2)
                worksheet.write(18,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                #NO 11
                if landuse_all_11_level_1 == 0:
                    landuse_all_11_level_1 = ''
                else:
                    landuse_all_11_level_1 = (round(landuse_all_11_level_1,2))
                worksheet.write(19, column-column_count_1, landuse_all_11_level_1,format)
                if landuse_all_11_level_2 == 0:
                    landuse_all_11_level_2 = ''
                else:
                    landuse_all_11_level_2 = (round(landuse_all_11_level_2,2))
                worksheet.write(19, column-column_count_2, landuse_all_11_level_2,format)
                landuse_all_11_level_1 = 0
                landuse_all_11_level_2 = 0
                #NO 12
                if landuse_all_12_level_1 == 0:
                    landuse_all_12_level_1 = ''
                else:
                    landuse_all_12_level_1 = (round(landuse_all_12_level_1,2))
                worksheet.write(20, column-column_count_1, landuse_all_12_level_1,format)
                if landuse_all_12_level_2 == 0:
                    landuse_all_12_level_2 = ''
                else:
                    landuse_all_12_level_2 = (round(landuse_all_12_level_2,2))
                worksheet.write(20, column-column_count_2, landuse_all_12_level_2,format)
                landuse_all_12_level_1 = 0
                landuse_all_12_level_2 = 0
                #NO 13
                cell_up = xl_rowcol_to_cell(19, column-column_count_1)
                cell_down = xl_rowcol_to_cell(20, column-column_count_1)
                worksheet.write(21,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
                cell_up = xl_rowcol_to_cell(19, column-column_count_2)
                cell_down = xl_rowcol_to_cell(20, column-column_count_2)
                worksheet.write(21,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)

                #ALL AREA
                cell_1 = xl_rowcol_to_cell(9, column-column_count_1)
                cell_2 = xl_rowcol_to_cell(10, column-column_count_1)
                cell_3 = xl_rowcol_to_cell(14, column-column_count_1)
                cell_4 = xl_rowcol_to_cell(18, column-column_count_1)
                cell_5 = xl_rowcol_to_cell(21, column-column_count_1)
                worksheet.write_formula(22,column-column_count_1,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                cell_1 = xl_rowcol_to_cell(9, column-column_count_2)
                cell_2 = xl_rowcol_to_cell(10, column-column_count_2)
                cell_3 = xl_rowcol_to_cell(14, column-column_count_2)
                cell_4 = xl_rowcol_to_cell(18, column-column_count_2)
                cell_5 = xl_rowcol_to_cell(21, column-column_count_2)
                worksheet.write_formula(22,column-column_count_2,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                code1 = 0
                code2 = 0
                column_count_1 = 0
                column_count_2 = 0

            if code1 == 0:
                code1 = str(landuse.code)[:1]
                code2 = str(landuse.code)[:2]
                #COUNTS AND HEADER
                column = column + 1
                column_number = column_number + 1
                worksheet.write(8,column, column_number,format)
                worksheet.merge_range(5,column,7,column, u'Бүгд',format)
                column = column + 1
                column_number = column_number + 1
                worksheet.write(8,column, column_number,format)
                all_landuse_count += 1
                worksheet.merge_range(6,column,7,column, landuse.description2,format_90)
                column_count_1 += 1
                all_landuse_count += 1
                column = column + 1
                column_number = column_number + 1
                worksheet.write(8,column, column_number,format)
                worksheet.write(7,column,landuse.description,format_90)

                #NO 1
                landuse_area_1 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 1)\
                            .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.record_date < self.end_date)\
                            .filter(ParcelReport.record_status == 20)\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_1.area == None or landuse_area_1.area == 0:
                    area_no_1 = ''
                else:
                    area_no_1 = round((landuse_area_1.area/10000),2)
                worksheet.write(9, column, area_no_1,format)
                if area_no_1 == '':
                    area_no_1 = 0
                landuse_all_1_level_1 = landuse_all_1_level_1 + area_no_1
                landuse_all_1_level_2 = landuse_all_1_level_2 + area_no_1
                landuse_all_1_level_3 = landuse_all_1_level_3 + area_no_1
                #NO 2
                landuse_area_2 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 4)\
                            .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.record_date < self.end_date)\
                            .filter(ParcelReport.record_status == 20)\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_2.area == None or landuse_area_2.area == 0:
                    area_no_2 = ''
                else:
                    area_no_2 = round((landuse_area_2.area/10000),2)
                worksheet.write(10, column, area_no_2,format)
                if area_no_2 == '':
                    area_no_2 = 0
                landuse_all_2_level_1 = landuse_all_2_level_1 + area_no_2
                landuse_all_2_level_2 = landuse_all_2_level_2 + area_no_2
                landuse_all_2_level_3 = landuse_all_2_level_3 + area_no_2
                #POSSESS
                #NO 3
                landuse_area_3 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                            ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                            ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                            .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_3.area == None or landuse_area_3.area == 0:
                    area_no_3 = ''
                else:
                    area_no_3 = round((landuse_area_3.area/10000),2)
                worksheet.write(11, column, area_no_3,format)
                if area_no_3 == '':
                    area_no_3 = 0
                landuse_all_3_level_1 = landuse_all_3_level_1 + area_no_3
                landuse_all_3_level_2 = landuse_all_3_level_2 + area_no_3
                landuse_all_3_level_3 = landuse_all_3_level_3 + area_no_3
                #NO 4
                landuse_area_4 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                            ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                            ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_4.area == None or landuse_area_4.area == 0:
                    area_no_4 = ''
                else:
                    area_no_4 = round((landuse_area_4.area/10000),2)
                worksheet.write(12, column, area_no_4,format)
                if area_no_4 == '':
                    area_no_4 = 0
                landuse_all_4_level_1 = landuse_all_4_level_1 + area_no_4
                landuse_all_4_level_2 = landuse_all_4_level_2 + area_no_4
                landuse_all_4_level_3 = landuse_all_4_level_3 + area_no_4
                #NO 5
                landuse_area_5 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(or_(ParcelReport.app_type == 5,\
                            ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                            ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_5.area == None or landuse_area_5.area == 0:
                    area_no_5 = ''
                else:
                    area_no_5 = round((landuse_area_5.area/10000),2)
                worksheet.write(13, column, area_no_5,format)
                if area_no_5 == '':
                    area_no_5 = 0
                landuse_all_5_level_1 = landuse_all_5_level_1 + area_no_5
                landuse_all_5_level_2 = landuse_all_5_level_2 + area_no_5
                landuse_all_5_level_3 = landuse_all_5_level_3 + area_no_5
                #NO 6 ALL
                cell_up = xl_rowcol_to_cell(11, column)
                cell_down = xl_rowcol_to_cell(13, column)
                worksheet.write(14, column, '=SUM('+cell_up+':'+cell_down+')',format)
                #POSSESSION RIGHT TO BE USED BY OTHERS
                #NO 7
                landuse_area_7 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                            .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_7.area == None or landuse_area_7.area == 0:
                    area_no_7 = ''
                else:
                    area_no_7 = round((landuse_area_7.area/10000),2)
                worksheet.write(15, column, area_no_7,format)
                if area_no_7 == '':
                    area_no_7 = 0
                landuse_all_7_level_1 = landuse_all_7_level_1 + area_no_7
                landuse_all_7_level_2 = landuse_all_7_level_2 + area_no_7
                landuse_all_7_level_3 = landuse_all_7_level_3 + area_no_7
                #NO 8
                landuse_area_8 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_8.area == None or landuse_area_8.area == 0:
                    area_no_8 = ''
                else:
                    area_no_8 = round((landuse_area_8.area/10000),2)
                worksheet.write(16, column, area_no_8,format)
                if area_no_8 == '':
                    area_no_8 = 0
                landuse_all_8_level_1 = landuse_all_8_level_1 + area_no_8
                landuse_all_8_level_2 = landuse_all_8_level_2 + area_no_8
                landuse_all_8_level_3 = landuse_all_8_level_3 + area_no_8
                #NO 9
                landuse_area_9 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 11)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_9.area == None or landuse_area_9.area == 0:
                    area_no_9 = ''
                else:
                    area_no_9 = round((landuse_area_9.area/10000),2)
                worksheet.write(17, column, area_no_9,format)
                if area_no_9 == '':
                    area_no_9 = 0
                landuse_all_9_level_1 = landuse_all_9_level_1 + area_no_9
                landuse_all_9_level_2 = landuse_all_9_level_2 + area_no_9
                landuse_all_9_level_3 = landuse_all_9_level_3 + area_no_9
                #NO 10
                cell_up = xl_rowcol_to_cell(15, column)
                cell_down = xl_rowcol_to_cell(17, column)
                worksheet.write(18,column,'=SUM('+cell_up+':'+cell_down+')',format)
                #USE
                #NO 11
                landuse_area_11 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 6)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 50)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_11.area == None or landuse_area_11.area == 0:
                    area_no_11 = ''
                else:
                    area_no_11 = round((landuse_area_11.area/10000),2)
                worksheet.write(19, column, area_no_11,format)
                if area_no_11 == '':
                    area_no_11 = 0
                landuse_all_11_level_1 = landuse_all_11_level_1 + area_no_11
                landuse_all_11_level_2 = landuse_all_11_level_2 + area_no_11
                landuse_all_11_level_3 = landuse_all_11_level_3 + area_no_11
                #NO 12
                landuse_area_12 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.app_type == 6)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 60)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_(ParcelReport.au1_code.in_(au_level1_list), ParcelReport.au2_code.in_(au_level1_list))).one()
                if landuse_area_12.area == None or landuse_area_12.area == 0:
                    area_no_12 = ''
                else:
                    area_no_12 = round((landuse_area_12.area/10000),2)
                worksheet.write(20, column, area_no_12,format)
                if area_no_12 == '':
                    area_no_12 = 0
                landuse_all_12_level_1 = landuse_all_12_level_1 + area_no_12
                landuse_all_12_level_2 = landuse_all_12_level_2 + area_no_12
                landuse_all_12_level_3 = landuse_all_12_level_3 + area_no_12
                #NO 13 USE ALL
                cell_up = xl_rowcol_to_cell(19, column)
                cell_down = xl_rowcol_to_cell(20, column)
                worksheet.write(21, column, '=SUM('+cell_up+':'+cell_down+')',format)

                #ALL AREA
                cell_1 = xl_rowcol_to_cell(9, column)
                cell_2 = xl_rowcol_to_cell(10, column)
                cell_3 = xl_rowcol_to_cell(14, column)
                cell_4 = xl_rowcol_to_cell(18, column)
                cell_5 = xl_rowcol_to_cell(21, column)
                worksheet.write_formula(22,column,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)
                #COUNTS
                all_landuse_count += 1
                column_count_1 += 1
                column_count_2 += 1

            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
        #HEADER
        worksheet.merge_range(5,column-column_count_1+1,5,column, u"Үүнээс",format)
        worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_6,format)
        worksheet.merge_range(3,5,3,column, u"Үүнээс газрын ангиаллын төрлөөр",format)
        if column_count_2 > 1:
            worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
        else:
            worksheet.write(6,column, u"Үүнээс",format)
        #OWNERSHIP
        #NO 1
        if landuse_all_1_level_1 == 0:
            landuse_all_1_level_1 = ''
        else:
            landuse_all_1_level_1 = (round(landuse_all_1_level_1,2))
        worksheet.write(9, column-column_count_1, landuse_all_1_level_1,format)
        if landuse_all_1_level_2 == 0:
            landuse_all_1_level_2 = ''
        else:
            landuse_all_1_level_2 = (round(landuse_all_1_level_2,2))
        worksheet.write(9, column-column_count_2, landuse_all_1_level_2,format)
        if landuse_all_1_level_3 == 0:
            landuse_all_1_level_3 = ''
        else:
            landuse_all_1_level_3 = (round(landuse_all_1_level_3,2))
        worksheet.write(9, column-all_landuse_count, landuse_all_1_level_3,format)
        #NO 2
        if landuse_all_2_level_1 == 0:
            landuse_all_2_level_1 = ''
        else:
            landuse_all_2_level_1 = (round(landuse_all_2_level_1,2))
        worksheet.write(10, column-column_count_1, landuse_all_2_level_1,format)
        if landuse_all_2_level_2 == 0:
            landuse_all_2_level_2 = ''
        else:
            landuse_all_2_level_2 = (round(landuse_all_2_level_2,2))
        worksheet.write(10, column-column_count_2, landuse_all_2_level_2,format)
        if landuse_all_2_level_3 == 0:
            landuse_all_2_level_3 = ''
        else:
            landuse_all_2_level_3 = (round(landuse_all_2_level_3,2))
        worksheet.write(10, column-all_landuse_count, landuse_all_2_level_3,format)
        #POSSESS
        #NO 3
        if landuse_all_3_level_1 == 0:
            landuse_all_3_level_1 = ''
        else:
            landuse_all_3_level_1 = (round(landuse_all_3_level_1,2))
        worksheet.write(11, column-column_count_1, landuse_all_3_level_1,format)
        if landuse_all_3_level_2 == 0:
            landuse_all_3_level_2 = ''
        else:
            landuse_all_3_level_2 = (round(landuse_all_3_level_2,2))
        worksheet.write(11, column-column_count_2, landuse_all_3_level_2,format)
        if landuse_all_3_level_3 == 0:
            landuse_all_3_level_3 = ''
        else:
            landuse_all_3_level_3 = (round(landuse_all_3_level_3,2))
        worksheet.write(11, column-all_landuse_count, landuse_all_3_level_3,format)
        #NO 4
        if landuse_all_4_level_1 == 0:
            landuse_all_4_level_1 = ''
        else:
            landuse_all_4_level_1 = (round(landuse_all_4_level_1,2))
        worksheet.write(12, column-column_count_1, landuse_all_4_level_1,format)
        if landuse_all_4_level_2 == 0:
            landuse_all_4_level_2 = ''
        else:
            landuse_all_4_level_2 = (round(landuse_all_4_level_2,2))
        worksheet.write(12, column-column_count_2, landuse_all_4_level_2,format)
        if landuse_all_4_level_3 == 0:
            landuse_all_4_level_3 = ''
        else:
            landuse_all_4_level_3 = (round(landuse_all_4_level_3,2))
        worksheet.write(12, column-all_landuse_count, landuse_all_4_level_3,format)
        #NO 5
        if landuse_all_5_level_1 == 0:
            landuse_all_5_level_1 = ''
        else:
            landuse_all_5_level_1 = (round(landuse_all_5_level_1,2))
        worksheet.write(13, column-column_count_1, landuse_all_5_level_1,format)
        if landuse_all_5_level_2 == 0:
            landuse_all_5_level_2 = ''
        else:
            landuse_all_5_level_2 = (round(landuse_all_5_level_2,2))
        worksheet.write(13, column-column_count_2, landuse_all_5_level_2,format)
        if landuse_all_5_level_3 == 0:
            landuse_all_5_level_3 = ''
        else:
            landuse_all_5_level_3 = (round(landuse_all_5_level_3,2))
        worksheet.write(13, column-all_landuse_count, landuse_all_5_level_3,format)
        #NO 6
        cell_up = xl_rowcol_to_cell(11, column-column_count_1)
        cell_down = xl_rowcol_to_cell(13, column-column_count_1)
        worksheet.write(14,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(11, column-column_count_2)
        cell_down = xl_rowcol_to_cell(13, column-column_count_2)
        worksheet.write(14,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(11, column-all_landuse_count)
        cell_down = xl_rowcol_to_cell(13, column-all_landuse_count)
        worksheet.write(14,column-all_landuse_count,'=SUM('+cell_up+':'+cell_down+')',format)
        #NO 7
        if landuse_all_7_level_1 == 0:
            landuse_all_7_level_1 = ''
        else:
            landuse_all_7_level_1 = (round(landuse_all_7_level_1,2))
        worksheet.write(15, column-column_count_1, landuse_all_7_level_1,format)
        if landuse_all_7_level_2 == 0:
            landuse_all_7_level_2 = ''
        else:
            landuse_all_7_level_2 = (round(landuse_all_7_level_2,2))
        worksheet.write(15, column-column_count_2, landuse_all_7_level_2,format)
        if landuse_all_7_level_3 == 0:
            landuse_all_7_level_3 = ''
        else:
            landuse_all_7_level_3 = (round(landuse_all_7_level_3,2))
        worksheet.write(15, column-all_landuse_count, landuse_all_7_level_3,format)
        #NO 8
        if landuse_all_8_level_1 == 0:
            landuse_all_8_level_1 = ''
        else:
            landuse_all_8_level_1 = (round(landuse_all_8_level_1,2))
        worksheet.write(16, column-column_count_1, landuse_all_8_level_1,format)
        if landuse_all_8_level_2 == 0:
            landuse_all_8_level_2 = ''
        else:
            landuse_all_8_level_2 = (round(landuse_all_8_level_2,2))
        worksheet.write(16, column-column_count_2, landuse_all_8_level_2,format)
        if landuse_all_8_level_3 == 0:
            landuse_all_8_level_3 = ''
        else:
            landuse_all_8_level_3 = (round(landuse_all_8_level_3,2))
        worksheet.write(16, column-all_landuse_count, landuse_all_8_level_3,format)
        #NO 9
        if landuse_all_9_level_1 == 0:
            landuse_all_9_level_1 = ''
        else:
            landuse_all_9_level_1 = (round(landuse_all_9_level_1,2))
        worksheet.write(17, column-column_count_1, landuse_all_9_level_1,format)
        if landuse_all_9_level_2 == 0:
            landuse_all_9_level_2 = ''
        else:
            landuse_all_9_level_2 = (round(landuse_all_9_level_2,2))
        worksheet.write(17, column-column_count_2, landuse_all_9_level_2,format)
        if landuse_all_9_level_3 == 0:
            landuse_all_9_level_3 = ''
        else:
            landuse_all_9_level_3 = (round(landuse_all_9_level_3,2))
        worksheet.write(17, column-all_landuse_count, landuse_all_9_level_3,format)
        #NO 10
        cell_up = xl_rowcol_to_cell(15, column-column_count_1)
        cell_down = xl_rowcol_to_cell(17, column-column_count_1)
        worksheet.write(18,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(15, column-column_count_2)
        cell_down = xl_rowcol_to_cell(17, column-column_count_2)
        worksheet.write(18,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(15, column-all_landuse_count)
        cell_down = xl_rowcol_to_cell(17, column-all_landuse_count)
        worksheet.write(18,column-all_landuse_count,'=SUM('+cell_up+':'+cell_down+')',format)
        #NO 11
        if landuse_all_11_level_1 == 0:
            landuse_all_11_level_1 = ''
        else:
            landuse_all_11_level_1 = (round(landuse_all_11_level_1,2))
        worksheet.write(19, column-column_count_1, landuse_all_11_level_1,format)
        if landuse_all_11_level_2 == 0:
            landuse_all_11_level_2 = ''
        else:
            landuse_all_11_level_2 = (round(landuse_all_11_level_2,2))
        worksheet.write(19, column-column_count_2, landuse_all_11_level_2,format)
        if landuse_all_11_level_3 == 0:
            landuse_all_11_level_3 = ''
        else:
            landuse_all_11_level_3 = (round(landuse_all_11_level_3,2))
        worksheet.write(19, column-all_landuse_count, landuse_all_11_level_3,format)
        #NO 12
        if landuse_all_12_level_1 == 0:
            landuse_all_12_level_1 = ''
        else:
            landuse_all_12_level_1 = (round(landuse_all_12_level_1,2))
        worksheet.write(20, column-column_count_1, landuse_all_12_level_1,format)
        if landuse_all_12_level_2 == 0:
            landuse_all_12_level_2 = ''
        else:
            landuse_all_12_level_2 = (round(landuse_all_12_level_2,2))
        worksheet.write(20, column-column_count_2, landuse_all_12_level_2,format)
        if landuse_all_12_level_3 == 0:
            landuse_all_12_level_3 = ''
        else:
            landuse_all_12_level_3 = (round(landuse_all_12_level_3,2))
        worksheet.write(20, column-all_landuse_count, landuse_all_12_level_3,format)
        #NO 13
        cell_up = xl_rowcol_to_cell(19, column-column_count_1)
        cell_down = xl_rowcol_to_cell(20, column-column_count_1)
        worksheet.write(21,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(19, column-column_count_2)
        cell_down = xl_rowcol_to_cell(20, column-column_count_2)
        worksheet.write(21,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(19, column-all_landuse_count)
        cell_down = xl_rowcol_to_cell(20, column-all_landuse_count)
        worksheet.write(21,column-all_landuse_count,'=SUM('+cell_up+':'+cell_down+')',format)

        #ALL AREA
        cell_1 = xl_rowcol_to_cell(9, column-column_count_1)
        cell_2 = xl_rowcol_to_cell(10, column-column_count_1)
        cell_3 = xl_rowcol_to_cell(14, column-column_count_1)
        cell_4 = xl_rowcol_to_cell(18, column-column_count_1)
        cell_5 = xl_rowcol_to_cell(21, column-column_count_1)
        worksheet.write_formula(22,column-column_count_1,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

        cell_1 = xl_rowcol_to_cell(9, column-column_count_2)
        cell_2 = xl_rowcol_to_cell(10, column-column_count_2)
        cell_3 = xl_rowcol_to_cell(14, column-column_count_2)
        cell_4 = xl_rowcol_to_cell(18, column-column_count_2)
        cell_5 = xl_rowcol_to_cell(21, column-column_count_2)
        worksheet.write_formula(22,column-column_count_2,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

        cell_1 = xl_rowcol_to_cell(9, column-all_landuse_count)
        cell_2 = xl_rowcol_to_cell(10, column-all_landuse_count)
        cell_3 = xl_rowcol_to_cell(14, column-all_landuse_count)
        cell_4 = xl_rowcol_to_cell(18, column-all_landuse_count)
        cell_5 = xl_rowcol_to_cell(21, column-all_landuse_count)
        worksheet.write_formula(22,column-all_landuse_count,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_2.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_3(self):

        restrictions = DatabaseUtils.working_l2_code()
        default_path = r'D:/TM_LM2/reports'
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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_3.xlsx")
        worksheet = workbook.add_worksheet()

        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)
        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        row = 9
        count = 1
        col = 0
        column = col+4
        code1 = 0
        code2 = 0

        worksheet.merge_range('D2:J2', u'ГАЗРЫН НЭГДМЭЛ САНГИЙН ЭРХ ЗҮЙН БАЙДЛЫН '+str(self.begin_year_sbox.value())+u' ОНЫ ТАЙЛАН',format_header)
        worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 3 дугаар хавсралт',format_header)
        worksheet.merge_range('K2:M2', u'/тоогоор/            Маягт ГТ-3 ',format_header)
        worksheet.merge_range('A4:A8', u'д/д', format)
        worksheet.merge_range('B4:C8', u'Газар өмчлөгч, эзэмшигч, ашиглагч',format)
        worksheet.merge_range('D4:D8', u'д/д',format)
        worksheet.merge_range('E4:E8', u'Нийт',format)
        worksheet.write(8,0, u'А',format)
        worksheet.merge_range(8,1,8,2, u'Б',format)
        worksheet.write(8,3, 0,format)
        worksheet.write(8,4, 1,format)
        worksheet.merge_range('B10:B11', u'Өмчлөгч',format_90)
        worksheet.merge_range('B12:B15', u'Эзэмшигч',format_90)
        worksheet.merge_range('B16:B19', u'Бусдын эзэмшил газрыг ашиглагч Монгол улсын',format_90)
        worksheet.merge_range('B20:B22', u'Ашиглагч',format_90)
        worksheet.write('A10', 1,format)
        worksheet.write('A11', 2,format)
        worksheet.write('A12', 1,format)
        worksheet.write('A13', 2,format)
        worksheet.write('A14', 3,format)
        worksheet.write('A15', 4,format)
        worksheet.write('A16', 5,format)
        worksheet.write('A17', 6,format)
        worksheet.write('A18', 7,format)
        worksheet.write('A19', 8,format)
        worksheet.write('A20', 9,format)
        worksheet.write('A21', 10,format)
        worksheet.write('A22', 11,format)

        worksheet.write('C10', u'а/гэр бүлийн хэрэгцээнд',format)
        worksheet.write('C11', u'б/аж ахуйн зориулалтаар',format)
        worksheet.write('C12', u'а/иргэн',format)
        worksheet.write('C13', u'б/төрийн байгууллага',format)
        worksheet.write('C14', u'в/аж ахуйн нэгж',format)
        worksheet.write('C15', u'Дүн',format)
        worksheet.write('C16', u'а/иргэн',format)
        worksheet.write('C17', u'б/төрийн байгууллага',format)
        worksheet.write('C18', u'в/аж ахуйн нэгж',format)
        worksheet.write('C19', u'Дүн',format)
        worksheet.write('C20', u'а/гадаадын иргэн болон харъялалгүй хүн',format)
        worksheet.write('C21', u'б/гадаадын хөрөнгө оруулалтай аж ахуйн нэгж, гадаадын хуулийн этгээд',format)
        worksheet.write('C22', u'Дүн',format)
        worksheet.write('C23', u'Нийт дүн',format)

        worksheet.write('D10', 1,format)
        worksheet.write('D11', 2,format)
        worksheet.write('D12', 3,format)
        worksheet.write('D13', 4,format)
        worksheet.write('D14', 5,format)
        worksheet.write('D15', 6,format)
        worksheet.write('D16', 7,format)
        worksheet.write('D17', 8,format)
        worksheet.write('D18', 9,format)
        worksheet.write('D19', 10,format)
        worksheet.write('D20', 11,format)
        worksheet.write('D21', 12,format)
        worksheet.write('D22', 13,format)
        worksheet.write('D23', 14,format)


        landuse_type = self.session.query(ClLanduseType).order_by(ClLanduseType.code.asc()).all()
        area_level_1 = 0
        area_level_2 = 0
        area_level_3 = 0
        column_count_1 = 0
        column_count_2 = 0
        all_landuse_count = 0
        all_area_landuse = 0
        column_number = 1
        area_no_1 = 0
        landuse_all_1_level_1 = 0
        landuse_all_1_level_2 = 0
        landuse_all_1_level_3 = 0
        area_no_2 = 0
        landuse_all_2_level_1 = 0
        landuse_all_2_level_2 = 0
        landuse_all_2_level_3 = 0
        area_no_3 = 0
        landuse_all_3_level_1 = 0
        landuse_all_3_level_2 = 0
        landuse_all_3_level_3 = 0
        area_no_4 = 0
        landuse_all_4_level_1 = 0
        landuse_all_4_level_2 = 0
        landuse_all_4_level_3 = 0
        area_no_5 = 0
        landuse_all_5_level_1 = 0
        landuse_all_5_level_2 = 0
        landuse_all_5_level_3 = 0
        area_no_6 = 0
        landuse_all_6_level_1 = 0
        landuse_all_6_level_2 = 0
        landuse_all_6_level_3 = 0
        area_no_7 = 0
        landuse_all_7_level_1 = 0
        landuse_all_7_level_2 = 0
        landuse_all_7_level_3 = 0
        area_no_8 = 0
        landuse_all_8_level_1 = 0
        landuse_all_8_level_2 = 0
        landuse_all_8_level_3 = 0
        area_no_9 = 0
        landuse_all_9_level_1 = 0
        landuse_all_9_level_2 = 0
        landuse_all_9_level_3 = 0
        area_no_10 = 0
        landuse_all_10_level_1 = 0
        landuse_all_10_level_2 = 0
        landuse_all_10_level_3 = 0
        area_no_11 = 0
        landuse_all_11_level_1 = 0
        landuse_all_11_level_2 = 0
        landuse_all_11_level_3 = 0
        area_no_12 = 0
        landuse_all_12_level_1 = 0
        landuse_all_12_level_2 = 0
        landuse_all_12_level_3 = 0
        area_no_13 = 0
        landuse_all_13_level_1 = 0
        landuse_all_13_level_2 = 0
        landuse_all_13_level_3 = 0

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        au2_count = 0
        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        au1_count = 0

        for au2 in au_level2_list:
            au2_count = au2_count + 1
        for au1 in au_level1_list:
            au1_count = au1_count + 1
        if au1_count > 1:
            self.work_level_lbl.setText(u'Улсын хэмжээнд ажиллах аймгын тоо:'+ str(au1_count))
            au_level2_string = '00000,00000'
        else:
            au_level1_string = '000,000'
            self.aimag_cbox.setDisabled(True)
            if au2_count > 1:
                self.work_level_lbl.setText(u'Аймгийн хэмжээнд ажиллах сумын тоо:'+ str(au2_count))
            else:
                self.work_level_lbl.setText(u'Зөвхөн нэг суманд ажиллах эрхтэй')

        progress_count = len(landuse_type)
        self.progressBar.setMaximum(progress_count)
        for landuse in landuse_type:
            area_ga = 0
            if code1 == str(landuse.code)[:1]:
                if code2 == str(landuse.code)[:2]:
                    column = column + 1
                    column_number = column_number + 1
                    worksheet.write(8,column, column_number,format)
                    worksheet.write(7,column,landuse.description,format_90)
                    #OWNERSHIP
                    #NO 1
                    landuse_area_1 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 1)\
                                    .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                    .filter(ParcelReport.valid_till == 'infinity')\
                                    .filter(ParcelReport.record_date < self.end_date)\
                                    .filter(ParcelReport.record_status == 20)\
                                    .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_1 == None or landuse_area_1 == 0:
                        area_no_1 = ''
                    else:
                        area_no_1 = round((landuse_area_1),2)
                    worksheet.write(9, column, area_no_1,format)
                    if area_no_1 == '':
                        area_no_1 = 0
                    landuse_all_1_level_1 = landuse_all_1_level_1 + area_no_1
                    landuse_all_1_level_2 = landuse_all_1_level_2 + area_no_1
                    landuse_all_1_level_3 = landuse_all_1_level_3 + area_no_1
                    #NO 2
                    landuse_area_2 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 4)\
                                    .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                    .filter(ParcelReport.valid_till == 'infinity')\
                                    .filter(ParcelReport.record_date < self.end_date)\
                                    .filter(ParcelReport.record_status == 20)\
                                    .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()

                    if landuse_area_2 == None or landuse_area_1 == 0:
                        area_no_2 = ''
                    else:
                        area_no_2 = round((landuse_area_2),2)
                    worksheet.write(10, column, area_no_2,format)
                    if area_no_2 == '':
                        area_no_2 = 0
                    landuse_all_2_level_1 = landuse_all_2_level_1 + area_no_2
                    landuse_all_2_level_2 = landuse_all_2_level_2 + area_no_2
                    landuse_all_2_level_3 = landuse_all_2_level_3 + area_no_2
                    #POSSESS
                    #NO 3
                    landuse_area_3 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_3 == None or landuse_area_3 == 0:
                        area_no_3 = ''
                    else:
                        area_no_3 = round((landuse_area_3),2)
                    worksheet.write(11, column, area_no_3,format)
                    if area_no_3 == '':
                        area_no_3 = 0
                    landuse_all_3_level_1 = landuse_all_3_level_1 + area_no_3
                    landuse_all_3_level_2 = landuse_all_3_level_2 + area_no_3
                    landuse_all_3_level_3 = landuse_all_3_level_3 + area_no_3
                    #NO 4
                    landuse_area_4 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_4 == None or landuse_area_4 == 0:
                        area_no_4 = ''
                    else:
                        area_no_4 = round((landuse_area_4),2)
                    worksheet.write(12, column, area_no_4,format)
                    if area_no_4 == '':
                        area_no_4 = 0
                    landuse_all_4_level_1 = landuse_all_4_level_1 + area_no_4
                    landuse_all_4_level_2 = landuse_all_4_level_2 + area_no_4
                    landuse_all_4_level_3 = landuse_all_4_level_3 + area_no_4
                    #NO 5
                    landuse_area_5 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_5 == None or landuse_area_5 == 0:
                        area_no_5 = ''
                    else:
                        area_no_5 = round((landuse_area_5),2)
                    worksheet.write(13, column, area_no_5,format)
                    if area_no_5 == '':
                        area_no_5 = 0
                    landuse_all_5_level_1 = landuse_all_5_level_1 + area_no_5
                    landuse_all_5_level_2 = landuse_all_5_level_2 + area_no_5
                    landuse_all_5_level_3 = landuse_all_5_level_3 + area_no_5
                    #NO 6 ALL
                    cell_up = xl_rowcol_to_cell(11, column)
                    cell_down = xl_rowcol_to_cell(13, column)
                    worksheet.write(14, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #POSSESSION RIGHT TO BE USED BY OTHERS
                    #NO 7
                    landuse_area_7 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_7 == None or landuse_area_7 == 0:
                        area_no_7 = ''
                    else:
                        area_no_7 = round((landuse_area_7),2)
                    worksheet.write(15, column, area_no_7,format)
                    if area_no_7 == '':
                        area_no_7 = 0
                    landuse_all_7_level_1 = landuse_all_7_level_1 + area_no_7
                    landuse_all_7_level_2 = landuse_all_7_level_2 + area_no_7
                    landuse_all_7_level_3 = landuse_all_7_level_3 + area_no_7
                    #NO 8
                    landuse_area_8 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_8 == None or landuse_area_8 == 0:
                        area_no_8 = ''
                    else:
                        area_no_8 = round((landuse_area_8),2)
                    worksheet.write(16, column, area_no_8,format)
                    if area_no_8 == '':
                        area_no_8 = 0
                    landuse_all_8_level_1 = landuse_all_8_level_1 + area_no_8
                    landuse_all_8_level_2 = landuse_all_8_level_2 + area_no_8
                    landuse_all_8_level_3 = landuse_all_8_level_3 + area_no_8
                    #NO 9
                    landuse_area_9 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_9 == None or landuse_area_9 == 0:
                        area_no_9 = ''
                    else:
                        area_no_9 = round((landuse_area_9),2)
                    worksheet.write(17, column, area_no_9,format)
                    if area_no_9 == '':
                        area_no_9 = 0
                    landuse_all_9_level_1 = landuse_all_9_level_1 + area_no_9
                    landuse_all_9_level_2 = landuse_all_9_level_2 + area_no_9
                    landuse_all_9_level_3 = landuse_all_9_level_3 + area_no_9
                    #NO 10
                    cell_up = xl_rowcol_to_cell(15, column)
                    cell_down = xl_rowcol_to_cell(17, column)
                    worksheet.write(18, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #USE
                    #NO 11
                    landuse_area_11 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 50)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_11 == None or landuse_area_11 == 0:
                        area_no_11 = ''
                    else:
                        area_no_11 = round((landuse_area_11),2)
                    worksheet.write(19, column, area_no_11,format)
                    if area_no_11 == '':
                        area_no_11 = 0
                    landuse_all_11_level_1 = landuse_all_11_level_1 + area_no_11
                    landuse_all_11_level_2 = landuse_all_11_level_2 + area_no_11
                    landuse_all_11_level_3 = landuse_all_11_level_3 + area_no_11
                    #NO 12
                    landuse_area_12 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 60)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_12 == None or landuse_area_12 == 0:
                        area_no_12 = ''
                    else:
                        area_no_12 = round((landuse_area_12),2)
                    worksheet.write(20, column, area_no_12,format)
                    if area_no_12 == '':
                        area_no_12 = 0
                    landuse_all_12_level_1 = landuse_all_12_level_1 + area_no_12
                    landuse_all_12_level_2 = landuse_all_12_level_2 + area_no_12
                    landuse_all_12_level_3 = landuse_all_12_level_3 + area_no_12
                    #NO 13 USE ALL
                    cell_up = xl_rowcol_to_cell(19, column)
                    cell_down = xl_rowcol_to_cell(20, column)
                    worksheet.write(21, column, '=SUM('+cell_up+':'+cell_down+')',format)

                    #ALL AREA
                    cell_1 = xl_rowcol_to_cell(9, column)
                    cell_2 = xl_rowcol_to_cell(10, column)
                    cell_3 = xl_rowcol_to_cell(14, column)
                    cell_4 = xl_rowcol_to_cell(18, column)
                    cell_5 = xl_rowcol_to_cell(21, column)
                    worksheet.write_formula(22,column,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                    all_landuse_count += 1
                    column_count_2 += 1
                    column_count_1 += 1
                else:
                    code2 = 0
                    if column_count_2 > 1:
                        worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                    else:
                        worksheet.write(6,column, u"Үүнээс",format)
                    #OWNERSHIP
                    #NO 1
                    if landuse_all_1_level_2 == 0:
                        landuse_all_1_level_2 = ''
                    else:
                        landuse_all_1_level_2 = (round(landuse_all_1_level_2,2))
                    worksheet.write(9, column-column_count_2, landuse_all_1_level_2,format)
                    landuse_all_1_level_2 = 0
                    #NO 2
                    if landuse_all_2_level_2 == 0:
                        landuse_all_2_level_2 = ''
                    else:
                        landuse_all_2_level_2 = (round(landuse_all_2_level_2,2))
                    worksheet.write(10, column-column_count_2, landuse_all_2_level_2,format)
                    landuse_all_2_level_2 = 0
                    #POSSESS
                    #NO 3
                    if landuse_all_3_level_2 == 0:
                        landuse_all_3_level_2 = ''
                    else:
                        landuse_all_3_level_2 = (round(landuse_all_3_level_2,2))
                    worksheet.write(11, column-column_count_2, landuse_all_3_level_2,format)
                    landuse_all_3_level_2 = 0
                    #NO 4
                    if landuse_all_4_level_2 == 0:
                        landuse_all_4_level_2 = ''
                    else:
                        landuse_all_4_level_2 = (round(landuse_all_4_level_2,2))
                    worksheet.write(12, column-column_count_2, landuse_all_4_level_2,format)
                    landuse_all_4_level_2 = 0
                    #NO 5
                    if landuse_all_5_level_2 == 0:
                        landuse_all_5_level_2 = ''
                    else:
                        landuse_all_5_level_2 = (round(landuse_all_5_level_2,2))
                    worksheet.write(13, column-column_count_2, landuse_all_5_level_2,format)
                    landuse_all_5_level_2 = 0
                    #NO 6
                    cell_up = xl_rowcol_to_cell(11, column-column_count_2)
                    cell_down = xl_rowcol_to_cell(13, column-column_count_2)
                    worksheet.write(14,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                    #NO 7
                    if landuse_all_7_level_2 == 0:
                        landuse_all_7_level_2 = ''
                    else:
                        landuse_all_7_level_2 = (round(landuse_all_7_level_2,2))
                    worksheet.write(15, column-column_count_2, landuse_all_7_level_2,format)
                    landuse_all_7_level_2 = 0
                    #NO 8
                    if landuse_all_8_level_2 == 0:
                        landuse_all_8_level_2 = ''
                    else:
                        landuse_all_8_level_2 = (round(landuse_all_8_level_2,2))
                    worksheet.write(16, column-column_count_2, landuse_all_8_level_2,format)
                    landuse_all_8_level_2 = 0
                    #NO 9
                    if landuse_all_9_level_2 == 0:
                        landuse_all_9_level_2 = ''
                    else:
                        landuse_all_9_level_2 = (round(landuse_all_9_level_2,2))
                    worksheet.write(17, column-column_count_2, landuse_all_9_level_2,format)
                    landuse_all_9_level_2 = 0
                    #NO 10
                    cell_up = xl_rowcol_to_cell(15, column-column_count_2)
                    cell_down = xl_rowcol_to_cell(17, column-column_count_2)
                    worksheet.write(18,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                    #NO 11
                    if landuse_all_11_level_2 == 0:
                        landuse_all_11_level_2 = ''
                    else:
                        landuse_all_11_level_2 = (round(landuse_all_11_level_2,2))
                    worksheet.write(19, column-column_count_2, landuse_all_11_level_2,format)
                    landuse_all_11_level_2 = 0
                    #NO 12
                    if landuse_all_12_level_2 == 0:
                        landuse_all_12_level_2 = ''
                    else:
                        landuse_all_12_level_2 = (round(landuse_all_12_level_2,2))
                    worksheet.write(20, column-column_count_2, landuse_all_12_level_2,format)
                    landuse_all_12_level_2 = 0
                    #NO 13
                    cell_up = xl_rowcol_to_cell(19, column-column_count_2)
                    cell_down = xl_rowcol_to_cell(20, column-column_count_2)
                    worksheet.write(21,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                    #ALL AREA
                    cell_1 = xl_rowcol_to_cell(9, column-column_count_2)
                    cell_2 = xl_rowcol_to_cell(10, column-column_count_2)
                    cell_3 = xl_rowcol_to_cell(14, column-column_count_2)
                    cell_4 = xl_rowcol_to_cell(18, column-column_count_2)
                    cell_5 = xl_rowcol_to_cell(21, column-column_count_2)
                    worksheet.write_formula(22,column-column_count_2,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                    column_count_2 = 0

                if code2 == 0:
                    #COUNTS AND HEADER
                    code2 = str(landuse.code)[:2]
                    column = column + 1
                    column_number = column_number + 1
                    worksheet.write(8,column, column_number,format)
                    worksheet.merge_range(6,column,7,column, landuse.description2,format_90)
                    column = column + 1
                    column_number = column_number + 1
                    worksheet.write(8,column, column_number,format)
                    all_landuse_count += 1
                    column_count_1 += 1
                    worksheet.write(7,column,landuse.description,format_90)
                    #NO 1
                    landuse_area_1 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 1)\
                                .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.record_date < self.end_date)\
                                .filter(ParcelReport.record_status == 20)\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_1 == None or landuse_area_1 == 0:
                        area_no_1 = ''
                    else:
                        area_no_1 = round((landuse_area_1),2)
                    worksheet.write(9, column, area_no_1,format)
                    if area_no_1 == '':
                        area_no_1 = 0
                    landuse_all_1_level_1 = landuse_all_1_level_1 + area_no_1
                    landuse_all_1_level_2 = landuse_all_1_level_2 + area_no_1
                    landuse_all_1_level_3 = landuse_all_1_level_3 + area_no_1
                    #NO 2
                    landuse_area_2 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 4)\
                                .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.record_date < self.end_date)\
                                .filter(ParcelReport.record_status == 20)\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_2 == None or landuse_area_2 == 0:
                        area_no_2 = ''
                    else:
                        area_no_2 = round((landuse_area_2),2)
                    worksheet.write(10, column, area_no_2,format)
                    if area_no_2 == '':
                        area_no_2 = 0
                    landuse_all_2_level_1 = landuse_all_2_level_1 + area_no_2
                    landuse_all_2_level_2 = landuse_all_2_level_2 + area_no_2
                    landuse_all_2_level_3 = landuse_all_2_level_3 + area_no_2

                    #POSSESS
                    #NO 3
                    landuse_area_3 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_3 == None or landuse_area_3 == 0:
                        area_no_3 = ''
                    else:
                        area_no_3 = round((landuse_area_3),2)
                    worksheet.write(11, column, area_no_3,format)
                    if area_no_3 == '':
                        area_no_3 = 0
                    landuse_all_3_level_1 = landuse_all_3_level_1 + area_no_3
                    landuse_all_3_level_2 = landuse_all_3_level_2 + area_no_3
                    landuse_all_3_level_3 = landuse_all_3_level_3 + area_no_3
                    #NO 4
                    landuse_area_4 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_4 == None or landuse_area_4 == 0:
                        area_no_4 = ''
                    else:
                        area_no_4 = round((landuse_area_4),2)
                    worksheet.write(12, column, area_no_4,format)
                    if area_no_4 == '':
                        area_no_4 = 0
                    landuse_all_4_level_1 = landuse_all_4_level_1 + area_no_4
                    landuse_all_4_level_2 = landuse_all_4_level_2 + area_no_4
                    landuse_all_4_level_3 = landuse_all_4_level_3 + area_no_4
                    #NO 5
                    landuse_area_5 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                                ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                                ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_5 == None or landuse_area_5 == 0:
                        area_no_5 = ''
                    else:
                        area_no_5 = round((landuse_area_5),2)
                    worksheet.write(13, column, area_no_5,format)
                    if area_no_5 == '':
                        area_no_5 = 0
                    landuse_all_5_level_1 = landuse_all_5_level_1 + area_no_5
                    landuse_all_5_level_2 = landuse_all_5_level_2 + area_no_5
                    landuse_all_5_level_3 = landuse_all_5_level_3 + area_no_5
                    #NO 6 ALL
                    cell_up = xl_rowcol_to_cell(11, column)
                    cell_down = xl_rowcol_to_cell(13, column)
                    worksheet.write(14, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #POSSESSION RIGHT TO BE USED BY OTHERS
                    #NO 7
                    landuse_area_7 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_7 == None or landuse_area_7 == 0:
                        area_no_7 = ''
                    else:
                        area_no_7 = round((landuse_area_7),2)
                    worksheet.write(15, column, area_no_7,format)
                    if area_no_7 == '':
                        area_no_7 = 0
                    landuse_all_7_level_1 = landuse_all_7_level_1 + area_no_7
                    landuse_all_7_level_2 = landuse_all_7_level_2 + area_no_7
                    landuse_all_7_level_3 = landuse_all_7_level_3 + area_no_7
                    #NO 8
                    landuse_area_8 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_8 == None or landuse_area_8 == 0:
                        area_no_8 = ''
                    else:
                        area_no_8 = round((landuse_area_8),2)
                    worksheet.write(16, column, area_no_8,format)
                    if area_no_8 == '':
                        area_no_8 = 0
                    landuse_all_8_level_1 = landuse_all_8_level_1 + area_no_8
                    landuse_all_8_level_2 = landuse_all_8_level_2 + area_no_8
                    landuse_all_8_level_3 = landuse_all_8_level_3 + area_no_8
                    #NO 9
                    landuse_area_9 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_9 == None or landuse_area_9 == 0:
                        area_no_9 = ''
                    else:
                        area_no_9 = round((landuse_area_9),2)
                    worksheet.write(17, column, area_no_9,format)
                    if area_no_9 == '':
                        area_no_9 = 0
                    landuse_all_9_level_1 = landuse_all_9_level_1 + area_no_9
                    landuse_all_9_level_2 = landuse_all_9_level_2 + area_no_9
                    landuse_all_9_level_3 = landuse_all_9_level_3 + area_no_9
                    #NO 10
                    cell_up = xl_rowcol_to_cell(15, column)
                    cell_down = xl_rowcol_to_cell(17, column)
                    worksheet.write(18, column, '=SUM('+cell_up+':'+cell_down+')',format)
                    #USE
                    #NO 11
                    landuse_area_11 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 50)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_11 == None or landuse_area_11 == 0:
                        area_no_11 = ''
                    else:
                        area_no_11 = round((landuse_area_11),2)
                    worksheet.write(19, column, area_no_11,format)
                    if area_no_11 == '':
                        area_no_11 = 0
                    landuse_all_11_level_1 = landuse_all_11_level_1 + area_no_11
                    landuse_all_11_level_2 = landuse_all_11_level_2 + area_no_11
                    landuse_all_11_level_3 = landuse_all_11_level_3 + area_no_11
                    #NO 12
                    landuse_area_12 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 6)\
                                .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 60)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(ParcelReport.contract_date < self.end_date)\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if landuse_area_12 == None or landuse_area_12 == 0:
                        area_no_12 = ''
                    else:
                        area_no_12 = round((landuse_area_12),2)
                    worksheet.write(20, column, area_no_12,format)
                    if area_no_12 == '':
                        area_no_12 = 0
                    landuse_all_12_level_1 = landuse_all_12_level_1 + area_no_12
                    landuse_all_12_level_2 = landuse_all_12_level_2 + area_no_12
                    landuse_all_12_level_3 = landuse_all_12_level_3 + area_no_12
                    #NO 13 USE ALL
                    cell_up = xl_rowcol_to_cell(19, column)
                    cell_down = xl_rowcol_to_cell(20, column)
                    worksheet.write(21, column, '=SUM('+cell_up+':'+cell_down+')',format)

                    #ALL AREA
                    all_area = self.session.query((ParcelReport.parcel_id).label("area"))\
                                .filter(or_(ParcelReport.contract_no != None, ParcelReport.record_no != None)).filter(ParcelReport.landuse == landuse.code)\
                                .filter(ParcelReport.valid_till == 'infinity')\
                                .filter(or_(ParcelReport.contract_date < self.end_date,ParcelReport.record_date < self.end_date))\
                                .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30,ParcelReport.record_status == 20))\
                                .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                    if all_area == None:
                        area_ga = 0
                    else:
                        area_ga = (all_area)
                    worksheet.write(22, column, (round(area_ga,1)),format)
                    area_level_3 = area_level_3 + area_ga
                    area_level_2 = area_level_2 + area_ga
                    all_area_landuse = all_area_landuse + area_ga
                    #COUNTS
                    all_landuse_count += 1
                    column_count_2 += 1
                    column_count_1 += 1
            else:
                #HEADER
                worksheet.merge_range(5,column-column_count_1+1,5,column, u"Үүнээс",format)
                if code1 == '1':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_1,format)
                elif code1 == '2':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_2,format)
                elif code1 == '3':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_3,format)
                elif code1 == '4':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_4,format)
                elif code1 == '5':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_5,format)
                elif code1 == '6':
                    worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_6,format)
                if column_count_2 > 1:
                    worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
                else:
                    worksheet.write(6,column, u"Үүнээс",format)
                #OWNERSHIP
                #NO 1
                if landuse_all_1_level_1 == 0:
                    landuse_all_1_level_1 = ''
                else:
                    landuse_all_1_level_1 = (round(landuse_all_1_level_1,2))
                worksheet.write(9, column-column_count_1, landuse_all_1_level_1,format)
                if landuse_all_1_level_2 == 0:
                    landuse_all_1_level_2 = ''
                else:
                    landuse_all_1_level_2 = (round(landuse_all_1_level_2,2))
                worksheet.write(9, column-column_count_2, landuse_all_1_level_2,format)
                landuse_all_1_level_1 = 0
                landuse_all_1_level_2 = 0
                #NO 2
                if landuse_all_2_level_1 == 0:
                    landuse_all_2_level_1 = ''
                else:
                    landuse_all_2_level_1 = (round(landuse_all_2_level_1,2))
                worksheet.write(10, column-column_count_1, landuse_all_2_level_1,format)
                if landuse_all_2_level_2 == 0:
                    landuse_all_2_level_2 = ''
                else:
                    landuse_all_2_level_2 = (round(landuse_all_2_level_2,2))
                worksheet.write(10, column-column_count_2, landuse_all_2_level_2,format)
                landuse_all_2_level_1 = 0
                landuse_all_2_level_2 = 0
                #POSSESS
                #NO 3
                if landuse_all_3_level_1 == 0:
                    landuse_all_3_level_1 = ''
                else:
                    landuse_all_3_level_1 = (round(landuse_all_3_level_1,2))
                worksheet.write(11, column-column_count_1, landuse_all_3_level_1,format)
                if landuse_all_3_level_2 == 0:
                    landuse_all_3_level_2 = ''
                else:
                    landuse_all_3_level_2 = (round(landuse_all_3_level_2,2))
                worksheet.write(11, column-column_count_2, landuse_all_3_level_2,format)
                landuse_all_3_level_1 = 0
                landuse_all_3_level_2 = 0
                #NO 4
                if landuse_all_4_level_1 == 0:
                    landuse_all_4_level_1 = ''
                else:
                    landuse_all_4_level_1 = (round(landuse_all_4_level_1,2))
                worksheet.write(12, column-column_count_1, landuse_all_4_level_1,format)
                if landuse_all_4_level_2 == 0:
                    landuse_all_4_level_2 = ''
                else:
                    landuse_all_4_level_2 = (round(landuse_all_4_level_2,2))
                worksheet.write(12, column-column_count_2, landuse_all_4_level_2,format)
                landuse_all_4_level_1 = 0
                landuse_all_4_level_2 = 0
                #NO 5
                if landuse_all_5_level_1 == 0:
                    landuse_all_5_level_1 = ''
                else:
                    landuse_all_5_level_1 = (round(landuse_all_5_level_1,2))
                worksheet.write(13, column-column_count_1, landuse_all_5_level_1,format)
                if landuse_all_5_level_2 == 0:
                    landuse_all_5_level_2 = ''
                else:
                    landuse_all_5_level_2 = (round(landuse_all_5_level_2,2))
                worksheet.write(13, column-column_count_2, landuse_all_5_level_2,format)
                landuse_all_5_level_1 = 0
                landuse_all_5_level_2 = 0
                #NO 6
                cell_up = xl_rowcol_to_cell(11, column-column_count_1)
                cell_down = xl_rowcol_to_cell(13, column-column_count_1)
                worksheet.write(14,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
                cell_up = xl_rowcol_to_cell(11, column-column_count_2)
                cell_down = xl_rowcol_to_cell(13, column-column_count_2)
                worksheet.write(14,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                #NO 7
                if landuse_all_7_level_1 == 0:
                    landuse_all_7_level_1 = ''
                else:
                    landuse_all_7_level_1 = (round(landuse_all_7_level_1,2))
                worksheet.write(15, column-column_count_1, landuse_all_7_level_1,format)
                if landuse_all_7_level_2 == 0:
                    landuse_all_7_level_2 = ''
                else:
                    landuse_all_7_level_2 = (round(landuse_all_7_level_2,2))
                worksheet.write(15, column-column_count_2, landuse_all_7_level_2,format)
                landuse_all_7_level_1 = 0
                landuse_all_7_level_2 = 0
                #NO 8
                if landuse_all_8_level_1 == 0:
                    landuse_all_8_level_1 = ''
                else:
                    landuse_all_8_level_1 = (round(landuse_all_8_level_1,2))
                worksheet.write(16, column-column_count_1, landuse_all_8_level_1,format)
                if landuse_all_8_level_2 == 0:
                    landuse_all_8_level_2 = ''
                else:
                    landuse_all_8_level_2 = (round(landuse_all_8_level_2,2))
                worksheet.write(16, column-column_count_2, landuse_all_8_level_2,format)
                landuse_all_8_level_1 = 0
                landuse_all_8_level_2 = 0
                #NO 9
                if landuse_all_9_level_1 == 0:
                    landuse_all_9_level_1 = ''
                else:
                    landuse_all_9_level_1 = (round(landuse_all_9_level_1,2))
                worksheet.write(17, column-column_count_1, landuse_all_9_level_1,format)
                if landuse_all_9_level_2 == 0:
                    landuse_all_9_level_2 = ''
                else:
                    landuse_all_9_level_2 = (round(landuse_all_9_level_2,2))
                worksheet.write(17, column-column_count_2, landuse_all_9_level_2,format)
                landuse_all_9_level_1 = 0
                landuse_all_9_level_2 = 0
                #NO 10
                cell_up = xl_rowcol_to_cell(15, column-column_count_1)
                cell_down = xl_rowcol_to_cell(17, column-column_count_1)
                worksheet.write(18,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
                cell_up = xl_rowcol_to_cell(15, column-column_count_2)
                cell_down = xl_rowcol_to_cell(17, column-column_count_2)
                worksheet.write(18,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
                #NO 11
                if landuse_all_11_level_1 == 0:
                    landuse_all_11_level_1 = ''
                else:
                    landuse_all_11_level_1 = (round(landuse_all_11_level_1,2))
                worksheet.write(19, column-column_count_1, landuse_all_11_level_1,format)
                if landuse_all_11_level_2 == 0:
                    landuse_all_11_level_2 = ''
                else:
                    landuse_all_11_level_2 = (round(landuse_all_11_level_2,2))
                worksheet.write(19, column-column_count_2, landuse_all_11_level_2,format)
                landuse_all_11_level_1 = 0
                landuse_all_11_level_2 = 0
                #NO 12
                if landuse_all_12_level_1 == 0:
                    landuse_all_12_level_1 = ''
                else:
                    landuse_all_12_level_1 = (round(landuse_all_12_level_1,2))
                worksheet.write(20, column-column_count_1, landuse_all_12_level_1,format)
                if landuse_all_12_level_2 == 0:
                    landuse_all_12_level_2 = ''
                else:
                    landuse_all_12_level_2 = (round(landuse_all_12_level_2,2))
                worksheet.write(20, column-column_count_2, landuse_all_12_level_2,format)
                landuse_all_12_level_1 = 0
                landuse_all_12_level_2 = 0
                #NO 13
                cell_up = xl_rowcol_to_cell(19, column-column_count_1)
                cell_down = xl_rowcol_to_cell(20, column-column_count_1)
                worksheet.write(21,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
                cell_up = xl_rowcol_to_cell(19, column-column_count_2)
                cell_down = xl_rowcol_to_cell(20, column-column_count_2)
                worksheet.write(21,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)

                #ALL AREA
                cell_1 = xl_rowcol_to_cell(9, column-column_count_1)
                cell_2 = xl_rowcol_to_cell(10, column-column_count_1)
                cell_3 = xl_rowcol_to_cell(14, column-column_count_1)
                cell_4 = xl_rowcol_to_cell(18, column-column_count_1)
                cell_5 = xl_rowcol_to_cell(21, column-column_count_1)
                worksheet.write_formula(22,column-column_count_1,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                cell_1 = xl_rowcol_to_cell(9, column-column_count_2)
                cell_2 = xl_rowcol_to_cell(10, column-column_count_2)
                cell_3 = xl_rowcol_to_cell(14, column-column_count_2)
                cell_4 = xl_rowcol_to_cell(18, column-column_count_2)
                cell_5 = xl_rowcol_to_cell(21, column-column_count_2)
                worksheet.write_formula(22,column-column_count_2,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

                code1 = 0
                code2 = 0
                column_count_1 = 0
                column_count_2 = 0
                area_level_2 = 0
                area_level_3 = 0

            if code1 == 0:
                code1 = str(landuse.code)[:1]
                code2 = str(landuse.code)[:2]
                #COUNTS AND HEADER
                column = column + 1
                column_number = column_number + 1
                worksheet.write(8,column, column_number,format)
                worksheet.merge_range(5,column,7,column, u'Бүгд',format)
                column = column + 1
                column_number = column_number + 1
                worksheet.write(8,column, column_number,format)
                all_landuse_count += 1
                worksheet.merge_range(6,column,7,column, landuse.description2,format_90)
                column_count_1 += 1
                all_landuse_count += 1
                column = column + 1
                column_number = column_number + 1
                worksheet.write(8,column, column_number,format)
                worksheet.write(7,column,landuse.description,format_90)

                #NO 1
                landuse_area_1 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 1)\
                            .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.record_date < self.end_date)\
                            .filter(ParcelReport.record_status == 20)\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_1 == None or landuse_area_1 == 0:
                    area_no_1 = ''
                else:
                    area_no_1 = round((landuse_area_1),2)
                worksheet.write(9, column, area_no_1,format)
                if area_no_1 == '':
                    area_no_1 = 0
                landuse_all_1_level_1 = landuse_all_1_level_1 + area_no_1
                landuse_all_1_level_2 = landuse_all_1_level_2 + area_no_1
                landuse_all_1_level_3 = landuse_all_1_level_3 + area_no_1
                #NO 2
                landuse_area_2 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 4)\
                            .filter(ParcelReport.record_no != None).filter(ParcelReport.landuse == landuse.code)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.record_date < self.end_date)\
                            .filter(ParcelReport.record_status == 20)\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_2 == None or landuse_area_2 == 0:
                    area_no_2 = ''
                else:
                    area_no_2 = round((landuse_area_2))
                worksheet.write(10, column, area_no_2,format)
                if area_no_2 == '':
                    area_no_2 = 0
                landuse_all_2_level_1 = landuse_all_2_level_1 + area_no_2
                landuse_all_2_level_2 = landuse_all_2_level_2 + area_no_2
                landuse_all_2_level_3 = landuse_all_2_level_3 + area_no_2
                #POSSESS
                #NO 3
                landuse_area_3 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                            ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                            ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                            .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_3 == None or landuse_area_3 == 0:
                    area_no_3 = ''
                else:
                    area_no_3 = round((landuse_area_3),2)
                worksheet.write(11, column, area_no_3,format)
                if area_no_3 == '':
                    area_no_3 = 0
                landuse_all_3_level_1 = landuse_all_3_level_1 + area_no_3
                landuse_all_3_level_2 = landuse_all_3_level_2 + area_no_3
                landuse_all_3_level_3 = landuse_all_3_level_3 + area_no_3
                #NO 4
                landuse_area_4 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                            ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                            ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_4 == None or landuse_area_4 == 0:
                    area_no_4 = ''
                else:
                    area_no_4 = round((landuse_area_4),2)
                worksheet.write(12, column, area_no_4,format)
                if area_no_4 == '':
                    area_no_4 = 0
                landuse_all_4_level_1 = landuse_all_4_level_1 + area_no_4
                landuse_all_4_level_2 = landuse_all_4_level_2 + area_no_4
                landuse_all_4_level_3 = landuse_all_4_level_3 + area_no_4
                #NO 5
                landuse_area_5 = self.session.query((ParcelReport.parcel_id).label("area")).filter(or_(ParcelReport.app_type == 5,\
                            ParcelReport.app_type == 7,ParcelReport.app_type == 9,ParcelReport.app_type == 10,ParcelReport.app_type == 12,\
                            ParcelReport.app_type == 13)).filter(ParcelReport.contract_no != None)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_5 == None or landuse_area_5 == 0:
                    area_no_5 = ''
                else:
                    area_no_5 = round((landuse_area_5),2)
                worksheet.write(13, column, area_no_5,format)
                if area_no_5 == '':
                    area_no_5 = 0
                landuse_all_5_level_1 = landuse_all_5_level_1 + area_no_5
                landuse_all_5_level_2 = landuse_all_5_level_2 + area_no_5
                landuse_all_5_level_3 = landuse_all_5_level_3 + area_no_5
                #NO 6 ALL
                cell_up = xl_rowcol_to_cell(11, column)
                cell_down = xl_rowcol_to_cell(13, column)
                worksheet.write(14, column, '=SUM('+cell_up+':'+cell_down+')',format)
                #POSSESSION RIGHT TO BE USED BY OTHERS
                #NO 7
                landuse_area_7 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                            .filter(ParcelReport.landuse == landuse.code).filter(or_(ParcelReport.person_type == 10,ParcelReport.person_type == 20))\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_7 == None or landuse_area_7 == 0:
                    area_no_7 = ''
                else:
                    area_no_7 = round((landuse_area_7),2)
                worksheet.write(15, column, area_no_7,format)
                if area_no_7 == '':
                    area_no_7 = 0
                landuse_all_7_level_1 = landuse_all_7_level_1 + area_no_7
                landuse_all_7_level_2 = landuse_all_7_level_2 + area_no_7
                landuse_all_7_level_3 = landuse_all_7_level_3 + area_no_7
                #NO 8
                landuse_area_8 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 40)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_8 == None or landuse_area_8 == 0:
                    area_no_8 = ''
                else:
                    area_no_8 = round((landuse_area_8),2)
                worksheet.write(16, column, area_no_8,format)
                if area_no_8 == '':
                    area_no_8 = 0
                landuse_all_8_level_1 = landuse_all_8_level_1 + area_no_8
                landuse_all_8_level_2 = landuse_all_8_level_2 + area_no_8
                landuse_all_8_level_3 = landuse_all_8_level_3 + area_no_8
                #NO 9
                landuse_area_9 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 11)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.person_type == 30)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_9 == None or landuse_area_9 == 0:
                    area_no_9 = ''
                else:
                    area_no_9 = round((landuse_area_9),2)
                worksheet.write(17, column, area_no_9,format)
                if area_no_9 == '':
                    area_no_9 = 0
                landuse_all_9_level_1 = landuse_all_9_level_1 + area_no_9
                landuse_all_9_level_2 = landuse_all_9_level_2 + area_no_9
                landuse_all_9_level_3 = landuse_all_9_level_3 + area_no_9
                #NO 10
                cell_up = xl_rowcol_to_cell(15, column)
                cell_down = xl_rowcol_to_cell(17, column)
                worksheet.write(18,column,'=SUM('+cell_up+':'+cell_down+')',format)
                #USE
                #NO 11
                landuse_area_11 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 6)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 50)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_11 == None or landuse_area_11 == 0:
                    area_no_11 = ''
                else:
                    area_no_11 = round((landuse_area_11),2)
                worksheet.write(19, column, area_no_11,format)
                if area_no_11 == '':
                    area_no_11 = 0
                landuse_all_11_level_1 = landuse_all_11_level_1 + area_no_11
                landuse_all_11_level_2 = landuse_all_11_level_2 + area_no_11
                landuse_all_11_level_3 = landuse_all_11_level_3 + area_no_11
                #NO 12
                landuse_area_12 = self.session.query((ParcelReport.parcel_id).label("area")).filter(ParcelReport.app_type == 6)\
                            .filter(ParcelReport.landuse == landuse.code).filter(ParcelReport.contract_no != None).filter(ParcelReport.person_type == 60)\
                            .filter(ParcelReport.valid_till == 'infinity')\
                            .filter(ParcelReport.contract_date < self.end_date)\
                            .filter(or_(ParcelReport.contract_status == 20,ParcelReport.contract_status == 30))\
                            .filter(or_((ParcelReport.au2_code.in_(au_level2_list)),(ParcelReport.au1_code.in_(au_level1_list)))).group_by(ParcelReport.parcel_id).count()
                if landuse_area_12 == None or landuse_area_12 == 0:
                    area_no_12 = ''
                else:
                    area_no_12 = round((landuse_area_12),2)
                worksheet.write(20, column, area_no_12,format)
                if area_no_12 == '':
                    area_no_12 = 0
                landuse_all_12_level_1 = landuse_all_12_level_1 + area_no_12
                landuse_all_12_level_2 = landuse_all_12_level_2 + area_no_12
                landuse_all_12_level_3 = landuse_all_12_level_3 + area_no_12
                #NO 13 USE ALL
                cell_up = xl_rowcol_to_cell(19, column)
                cell_down = xl_rowcol_to_cell(20, column)
                worksheet.write(21, column, '=SUM('+cell_up+':'+cell_down+')',format)

                #ALL AREA
                cell_1 = xl_rowcol_to_cell(9, column)
                cell_2 = xl_rowcol_to_cell(10, column)
                cell_3 = xl_rowcol_to_cell(14, column)
                cell_4 = xl_rowcol_to_cell(18, column)
                cell_5 = xl_rowcol_to_cell(21, column)
                worksheet.write_formula(22,column,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)
                #COUNTS
                all_landuse_count += 1
                column_count_1 += 1
                column_count_2 += 1

            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
        #HEADER
        worksheet.merge_range(5,column-column_count_1+1,5,column, u"Үүнээс",format)
        worksheet.merge_range(4,column-column_count_1,4,column, LANDUSE_6,format)
        worksheet.merge_range(3,5,3,column, u"Үүнээс газрын ангиаллын төрлөөр",format)
        if column_count_2 > 1:
            worksheet.merge_range(6,column-column_count_2+1,6,column, u"Үүнээс",format)
        else:
            worksheet.write(6,column, u"Үүнээс",format)
        #OWNERSHIP
        #NO 1
        if landuse_all_1_level_1 == 0:
            landuse_all_1_level_1 = ''
        else:
            landuse_all_1_level_1 = (round(landuse_all_1_level_1,2))
        worksheet.write(9, column-column_count_1, landuse_all_1_level_1,format)
        if landuse_all_1_level_2 == 0:
            landuse_all_1_level_2 = ''
        else:
            landuse_all_1_level_2 = (round(landuse_all_1_level_2,2))
        worksheet.write(9, column-column_count_2, landuse_all_1_level_2,format)
        if landuse_all_1_level_3 == 0:
            landuse_all_1_level_3 = ''
        else:
            landuse_all_1_level_3 = (round(landuse_all_1_level_3,2))
        worksheet.write(9, column-all_landuse_count, landuse_all_1_level_3,format)
        #NO 2
        if landuse_all_2_level_1 == 0:
            landuse_all_2_level_1 = ''
        else:
            landuse_all_2_level_1 = (round(landuse_all_2_level_1,2))
        worksheet.write(10, column-column_count_1, landuse_all_2_level_1,format)
        if landuse_all_2_level_2 == 0:
            landuse_all_2_level_2 = ''
        else:
            landuse_all_2_level_2 = (round(landuse_all_2_level_2,2))
        worksheet.write(10, column-column_count_2, landuse_all_2_level_2,format)
        if landuse_all_2_level_3 == 0:
            landuse_all_2_level_3 = ''
        else:
            landuse_all_2_level_3 = (round(landuse_all_2_level_3,2))
        worksheet.write(10, column-all_landuse_count, landuse_all_2_level_3,format)
        #POSSESS
        #NO 3
        if landuse_all_3_level_1 == 0:
            landuse_all_3_level_1 = ''
        else:
            landuse_all_3_level_1 = (round(landuse_all_3_level_1,2))
        worksheet.write(11, column-column_count_1, landuse_all_3_level_1,format)
        if landuse_all_3_level_2 == 0:
            landuse_all_3_level_2 = ''
        else:
            landuse_all_3_level_2 = (round(landuse_all_3_level_2,2))
        worksheet.write(11, column-column_count_2, landuse_all_3_level_2,format)
        if landuse_all_3_level_3 == 0:
            landuse_all_3_level_3 = ''
        else:
            landuse_all_3_level_3 = (round(landuse_all_3_level_3,2))
        worksheet.write(11, column-all_landuse_count, landuse_all_3_level_3,format)
        #NO 4
        if landuse_all_4_level_1 == 0:
            landuse_all_4_level_1 = ''
        else:
            landuse_all_4_level_1 = (round(landuse_all_4_level_1,2))
        worksheet.write(12, column-column_count_1, landuse_all_4_level_1,format)
        if landuse_all_4_level_2 == 0:
            landuse_all_4_level_2 = ''
        else:
            landuse_all_4_level_2 = (round(landuse_all_4_level_2,2))
        worksheet.write(12, column-column_count_2, landuse_all_4_level_2,format)
        if landuse_all_4_level_3 == 0:
            landuse_all_4_level_3 = ''
        else:
            landuse_all_4_level_3 = (round(landuse_all_4_level_3,2))
        worksheet.write(12, column-all_landuse_count, landuse_all_4_level_3,format)
        #NO 5
        if landuse_all_5_level_1 == 0:
            landuse_all_5_level_1 = ''
        else:
            landuse_all_5_level_1 = (round(landuse_all_5_level_1,2))
        worksheet.write(13, column-column_count_1, landuse_all_5_level_1,format)
        if landuse_all_5_level_2 == 0:
            landuse_all_5_level_2 = ''
        else:
            landuse_all_5_level_2 = (round(landuse_all_5_level_2,2))
        worksheet.write(13, column-column_count_2, landuse_all_5_level_2,format)
        if landuse_all_5_level_3 == 0:
            landuse_all_5_level_3 = ''
        else:
            landuse_all_5_level_3 = (round(landuse_all_5_level_3,2))
        worksheet.write(13, column-all_landuse_count, landuse_all_5_level_3,format)
        #NO 6
        cell_up = xl_rowcol_to_cell(11, column-column_count_1)
        cell_down = xl_rowcol_to_cell(13, column-column_count_1)
        worksheet.write(14,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(11, column-column_count_2)
        cell_down = xl_rowcol_to_cell(13, column-column_count_2)
        worksheet.write(14,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(11, column-all_landuse_count)
        cell_down = xl_rowcol_to_cell(13, column-all_landuse_count)
        worksheet.write(14,column-all_landuse_count,'=SUM('+cell_up+':'+cell_down+')',format)
        #NO 7
        if landuse_all_7_level_1 == 0:
            landuse_all_7_level_1 = ''
        else:
            landuse_all_7_level_1 = (round(landuse_all_7_level_1,2))
        worksheet.write(15, column-column_count_1, landuse_all_7_level_1,format)
        if landuse_all_7_level_2 == 0:
            landuse_all_7_level_2 = ''
        else:
            landuse_all_7_level_2 = (round(landuse_all_7_level_2,2))
        worksheet.write(15, column-column_count_2, landuse_all_7_level_2,format)
        if landuse_all_7_level_3 == 0:
            landuse_all_7_level_3 = ''
        else:
            landuse_all_7_level_3 = (round(landuse_all_7_level_3,2))
        worksheet.write(15, column-all_landuse_count, landuse_all_7_level_3,format)
        #NO 8
        if landuse_all_8_level_1 == 0:
            landuse_all_8_level_1 = ''
        else:
            landuse_all_8_level_1 = (round(landuse_all_8_level_1,2))
        worksheet.write(16, column-column_count_1, landuse_all_8_level_1,format)
        if landuse_all_8_level_2 == 0:
            landuse_all_8_level_2 = ''
        else:
            landuse_all_8_level_2 = (round(landuse_all_8_level_2,2))
        worksheet.write(16, column-column_count_2, landuse_all_8_level_2,format)
        if landuse_all_8_level_3 == 0:
            landuse_all_8_level_3 = ''
        else:
            landuse_all_8_level_3 = (round(landuse_all_8_level_3,2))
        worksheet.write(16, column-all_landuse_count, landuse_all_8_level_3,format)
        #NO 9
        if landuse_all_9_level_1 == 0:
            landuse_all_9_level_1 = ''
        else:
            landuse_all_9_level_1 = (round(landuse_all_9_level_1,2))
        worksheet.write(17, column-column_count_1, landuse_all_9_level_1,format)
        if landuse_all_9_level_2 == 0:
            landuse_all_9_level_2 = ''
        else:
            landuse_all_9_level_2 = (round(landuse_all_9_level_2,2))
        worksheet.write(17, column-column_count_2, landuse_all_9_level_2,format)
        if landuse_all_9_level_3 == 0:
            landuse_all_9_level_3 = ''
        else:
            landuse_all_9_level_3 = (round(landuse_all_9_level_3,2))
        worksheet.write(17, column-all_landuse_count, landuse_all_9_level_3,format)
        #NO 10
        cell_up = xl_rowcol_to_cell(15, column-column_count_1)
        cell_down = xl_rowcol_to_cell(17, column-column_count_1)
        worksheet.write(18,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(15, column-column_count_2)
        cell_down = xl_rowcol_to_cell(17, column-column_count_2)
        worksheet.write(18,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(15, column-all_landuse_count)
        cell_down = xl_rowcol_to_cell(17, column-all_landuse_count)
        worksheet.write(18,column-all_landuse_count,'=SUM('+cell_up+':'+cell_down+')',format)
        #NO 11
        if landuse_all_11_level_1 == 0:
            landuse_all_11_level_1 = ''
        else:
            landuse_all_11_level_1 = (round(landuse_all_11_level_1,2))
        worksheet.write(19, column-column_count_1, landuse_all_11_level_1,format)
        if landuse_all_11_level_2 == 0:
            landuse_all_11_level_2 = ''
        else:
            landuse_all_11_level_2 = (round(landuse_all_11_level_2,2))
        worksheet.write(19, column-column_count_2, landuse_all_11_level_2,format)
        if landuse_all_11_level_3 == 0:
            landuse_all_11_level_3 = ''
        else:
            landuse_all_11_level_3 = (round(landuse_all_11_level_3,2))
        worksheet.write(19, column-all_landuse_count, landuse_all_11_level_3,format)
        #NO 12
        if landuse_all_12_level_1 == 0:
            landuse_all_12_level_1 = ''
        else:
            landuse_all_12_level_1 = (round(landuse_all_12_level_1,2))
        worksheet.write(20, column-column_count_1, landuse_all_12_level_1,format)
        if landuse_all_12_level_2 == 0:
            landuse_all_12_level_2 = ''
        else:
            landuse_all_12_level_2 = (round(landuse_all_12_level_2,2))
        worksheet.write(20, column-column_count_2, landuse_all_12_level_2,format)
        if landuse_all_12_level_3 == 0:
            landuse_all_12_level_3 = ''
        else:
            landuse_all_12_level_3 = (round(landuse_all_12_level_3,2))
        worksheet.write(20, column-all_landuse_count, landuse_all_12_level_3,format)
        #NO 13
        cell_up = xl_rowcol_to_cell(19, column-column_count_1)
        cell_down = xl_rowcol_to_cell(20, column-column_count_1)
        worksheet.write(21,column-column_count_1,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(19, column-column_count_2)
        cell_down = xl_rowcol_to_cell(20, column-column_count_2)
        worksheet.write(21,column-column_count_2,'=SUM('+cell_up+':'+cell_down+')',format)
        cell_up = xl_rowcol_to_cell(19, column-all_landuse_count)
        cell_down = xl_rowcol_to_cell(20, column-all_landuse_count)
        worksheet.write(21,column-all_landuse_count,'=SUM('+cell_up+':'+cell_down+')',format)

        #ALL AREA
        cell_1 = xl_rowcol_to_cell(9, column-column_count_1)
        cell_2 = xl_rowcol_to_cell(10, column-column_count_1)
        cell_3 = xl_rowcol_to_cell(14, column-column_count_1)
        cell_4 = xl_rowcol_to_cell(18, column-column_count_1)
        cell_5 = xl_rowcol_to_cell(21, column-column_count_1)
        worksheet.write_formula(22,column-column_count_1,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

        cell_1 = xl_rowcol_to_cell(9, column-column_count_2)
        cell_2 = xl_rowcol_to_cell(10, column-column_count_2)
        cell_3 = xl_rowcol_to_cell(14, column-column_count_2)
        cell_4 = xl_rowcol_to_cell(18, column-column_count_2)
        cell_5 = xl_rowcol_to_cell(21, column-column_count_2)
        worksheet.write_formula(22,column-column_count_2,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

        cell_1 = xl_rowcol_to_cell(9, column-all_landuse_count)
        cell_2 = xl_rowcol_to_cell(10, column-all_landuse_count)
        cell_3 = xl_rowcol_to_cell(14, column-all_landuse_count)
        cell_4 = xl_rowcol_to_cell(18, column-all_landuse_count)
        cell_5 = xl_rowcol_to_cell(21, column-all_landuse_count)
        worksheet.write_formula(22,column-all_landuse_count,'='+cell_1+' + '+cell_2+' + '+cell_3+' + '+cell_4+' + '+cell_5+'',format)

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_3.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_4(self):

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")

        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")

        restrictions = DatabaseUtils.working_l2_code()
        default_path = r'D:/TM_LM2/reports'
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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_4.xlsx")
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 3.5)
        worksheet.set_column('B:B', 45)

        worksheet.set_landscape()
        # worksheet.set_margins([left=0.7,] right=0.7,] top=0.75,] bottom=0.75]]])
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)
        format.set_border(1)
        format.set_shrink()

        format_left = workbook.add_format()
        format_left.set_text_wrap()
        format_left.set_align('justify')
        format_left.set_font_name('Times New Roman')
        format_left.set_font_size(8)
        format_left.set_border(1)
        format_left.set_shrink()

        format_right = workbook.add_format()
        format_right.set_text_wrap()
        format_right.set_align('right')
        format_right.set_font_name('Times New Roman')
        format_right.set_font_size(8)
        format_right.set_border(1)
        format_right.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        # format_header.set_align('right')
        format_header.set_align('vcenter')
        format_header.set_align('justify')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        format_bold = workbook.add_format()
        format_bold.set_text_wrap()
        format_bold.set_align('center')
        format_bold.set_align('vcenter')
        format_bold.set_font_name('Times New Roman')
        format_bold.set_font_size(8)
        format_bold.set_border(1)
        format_bold.set_shrink()
        format_bold.set_bold()

        row = 5
        col = 0
        count = 1
        code1 = 0
        code2 = 0

        worksheet.merge_range('B2:G2', u'УЛСЫН ТУСГАЙ ХЭРЭГЦЭЭНИЙ ГАЗРЫН '+str(self.begin_year_sbox.value())+u' ОНЫ ӨӨРЧЛӨЛТИЙН ТАЙЛАН',format_header)
        # worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        # worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 4 дүгээр хавсралт',format_header)
        if len(au_level1_list) == 1 and len(au_level2_list) == 1:
            worksheet.write('E3', u'/га/',format_header)
        else:
            worksheet.write('E3', u'/мян.га/',format_header)
        worksheet.write('A4', u'',format_bold)
        worksheet.write('B4', u'Газрын нэгдмэл сангийн ангилал',format_bold)
        worksheet.write('C4', u'Өмнөх он',format_bold)
        worksheet.write('D4', u'Тайлант он',format_bold)
        worksheet.write('E4', u'Өөрчлөлт',format_bold)
        worksheet.write('A5', u'VI', format_bold)
        worksheet.write('B5', u'Улсын тусгай хэрэгцээний газар',format_bold)

        try:
            landuse = self.session.query(ClLanduseType.code2,ClLanduseType.description2).filter(or_(ClLanduseType.code2 == 61,\
                                    ClLanduseType.code2 == 62,ClLanduseType.code2 == 63,ClLanduseType.code2 == 64,ClLanduseType.code2 == 65,\
                                    ClLanduseType.code2 == 66,ClLanduseType.code2 == 67,ClLanduseType.code2 == 68,ClLanduseType.code2 == 69))\
                                    .group_by(ClLanduseType.code2,ClLanduseType.description2).order_by(ClLanduseType.code2.asc()).all()

            for code2, desc2 in landuse:
                area_now = 0
                area_before = 0
                area_sub = 0
                worksheet.write(row, col,count,format)
                worksheet.write(row,col+1,desc2,format_left)

                landuse_area_before_year = self.session.query(func.sum(ParcelGt1.area_m2).label("area"))\
                                    .filter(ParcelGt1.landuse_code2 == code2)\
                                    .filter(ParcelGt1.valid_till == 'infinity')\
                                    .filter(ParcelGt1.valid_from < self.before_date)\
                                    .filter(or_(ParcelGt1.au1_code.in_(au_level1_list), ParcelGt1.au2_code.in_(au_level2_list))).one()
                if landuse_area_before_year.area == None or landuse_area_before_year.area == 0:
                    area_before = ''
                else:
                    if len(au_level1_list) == 1 and len(au_level2_list) == 1:
                        area_before = round(landuse_area_before_year.area/10000,1)
                    else:
                        area_before = round(landuse_area_before_year.area/10000000,1)

                worksheet.write(row, col+2,area_before,format_right)

                landuse_area_now = self.session.query(func.sum(ParcelGt1.area_m2).label("area"))\
                                    .filter(ParcelGt1.landuse_code2 == code2)\
                                    .filter(ParcelGt1.valid_till == 'infinity')\
                                    .filter(ParcelGt1.valid_from < self.end_date)\
                                    .filter(or_(ParcelGt1.au1_code.in_(au_level1_list), ParcelGt1.au2_code.in_(au_level2_list))).one()

                if landuse_area_now.area == None or landuse_area_now.area == 0:
                    area_now = ''
                else:
                    if len(au_level1_list) == 1 and len(au_level2_list) == 1:
                        area_now = round(landuse_area_now.area/10000,1)
                    else:
                        area_now = round(landuse_area_now.area/10000000,1)
                worksheet.write(row, col+3,area_now,format_right)

                if area_now == '' and area_before == '':
                    area_sub = ''
                else:
                    if area_now == '':
                        area_now = 0
                    if area_before == '':
                        area_before = 0
                    area_sub = area_now-area_before

                worksheet.write(row, col+4,area_sub,format_right)

                cell_up = xl_rowcol_to_cell(5, col+2)
                cell_down = xl_rowcol_to_cell(row, col+2)
                worksheet.write(4,col+2,'=SUM('+cell_up+':'+cell_down+')',format_right)

                cell_up = xl_rowcol_to_cell(5, col+3)
                cell_down = xl_rowcol_to_cell(row, col+3)
                worksheet.write(4,col+3,'=SUM('+cell_up+':'+cell_down+')',format_right)

                cell_up = xl_rowcol_to_cell(5, col+4)
                cell_down = xl_rowcol_to_cell(row, col+4)
                worksheet.write(4,col+4,'=SUM('+cell_up+':'+cell_down+')',format_right)

                row += 1
                count +=1

        except SQLAlchemyError, e:
            raise LM2Exception(self.tr("File Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_4.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_5(self):

        restrictions = DatabaseUtils.working_l2_code()
        default_path = r'D:/TM_LM2/reports'
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
        path = os.path.join(os.path.dirname(__file__), "../view/map/report_temp/")
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_5.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_landscape()
        worksheet.set_column('B:B', 33.5)
        worksheet.set_row(0,50)
        worksheet.set_row(7,50)
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)

        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        # format_header.set_align('right')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        row = 9
        count = 1
        code1 = 0

        worksheet.merge_range('D2:J2', u'ГАЗРЫН ШИЛЖИЛТ ХӨДӨЛГӨӨНИЙ ТЭНЦЭЛ /'+str(self.begin_year_sbox.value())+u' он/',format_header)
        worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 5 дугаар хавсралт',format_header)
        worksheet.merge_range('K2:M2', u'/га-гаар/            Маягт ГТ-5 ',format_header)
        worksheet.merge_range('A4:A8', u'д/д', format)
        worksheet.merge_range('B4:B8', u'Газрын төрөл',format)
        worksheet.merge_range('C4:C8', u'Нийт',format)
        worksheet.write(8,0, 0,format)
        worksheet.write(8,1, 1,format)
        worksheet.write(8,2, 2,format)

        special_needs = self.session.query(ClLanduseType.code2,ClLanduseType.description2).group_by(ClLanduseType.code2,ClLanduseType.description2)\
                                                    .order_by(ClLanduseType.code2.asc()).all()

        progress_count = len(special_needs)
        self.progressBar.setMaximum(progress_count)

        for code2, desc2 in special_needs:
            col = 0
            column = col+2
            is_first = 0
            worksheet.write(row, col, (count),format)
            worksheet.write(row, col+1, desc2,format)
            column_count_1 = 0
            column_count_2 = 0
            all_landuse_count = 0
            for code_2, desc_2 in special_needs:
                if code1 == str(code_2)[:1]:
                    is_first = 1
                    worksheet.write(8,column, column,format)
                    worksheet.merge_range(6,column,7,column, desc_2,format_90)
                    column = column + 1
                    all_landuse_count += 1
                    column_count_2 += 1
                    column_count_1 += 1
                else:
                    if is_first == 1:

                        if column_count_1 > 1:
                            worksheet.merge_range(5,column-column_count_1,5,column-1, u"Үүнээс",format)
                        else:
                            worksheet.write(5,column-1, u"Үүнээс",format)
                        if code1 == '1':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_1,format)
                        elif code1 == '2':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_2,format)
                        elif code1 == '3':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_3,format)
                        elif code1 == '4':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_4,format)
                        elif code1 == '5':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_5,format)
                        elif code1 == '6':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_6,format)
                        code1 = 0
                        column_count_1 = 0
                        column_count_2 = 0
                if code1 == 0:
                    code1 = str(code_2)[:1]
                    if is_first == 0:
                        column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.merge_range(5,column,7,column, u'Бүгд',format)
                    column = column + 1
                    worksheet.write(8,column, column,format)
                    all_landuse_count += 1
                    worksheet.merge_range(6,column,7,column, desc_2,format_90)
                    all_landuse_count += 1
                    column = column + 1
                    column_count_1 += 1
                    column_count_2 += 1
            code1 = 0
            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_6,format)
            worksheet.merge_range(3,3,3,column-1, u"Үүнээс газрын ангиаллын төрлөөр",format)
            if column_count_1 > 1:
                worksheet.merge_range(5,column-column_count_1,5,column-1, u"Үүнээс",format)
            else:
                worksheet.write(5,column-1, u"Үүнээс",format)
            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
            row += 1
            count +=1
        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_5.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_6(self):

        restrictions = DatabaseUtils.working_l2_code()
        default_path = r'D:/TM_LM2/reports'
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
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_6.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_landscape()
        worksheet.set_column('A:A', 3.5)
        worksheet.set_column('B:B', 15)
        worksheet.set_row(1,50)
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)

        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        worksheet.merge_range('D4:J4', u'ГАЗАРТ УЧРУУЛСАН ХОХИРЛЫН '+str(self.begin_year_sbox.value())+u' ОНЫ ТАЙЛАН',format_header)
        worksheet.merge_range('A2:G2', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('J2:P2', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 6 дугаар хавсралт',format_header)
        worksheet.merge_range('J6:L6', u'/га-гаар/        Маягт ГТ-6 ',format_header)
        worksheet.merge_range('A8:A9', u'Д/д', format)
        worksheet.merge_range('B8:B9', u'Аймаг, нийслэл, сум, дүүргийн нэр',format)
        worksheet.merge_range('C8:C9', u'Хохирол учирсан нийт талбай, га',format)
        worksheet.write(9,0, 0,format)
        worksheet.write(9,1, u'А',format)
        worksheet.write(9,2, 1,format)

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")

        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        if len(au_level1_list) > 1:
            admin_unit_1 = self.session.query(AuLevel1)\
                        .filter(AuLevel1.code.in_(au_level1_list)).all()
        elif len(au_level1_list) == 1 or len(au_level2_list) >= 1:
            admin_unit_1 = self.session.query(AuLevel2)\
                        .filter(AuLevel2.code.in_(au_level2_list)).all()
        conservation_type = self.session.query(ClPollutionType).order_by(ClPollutionType.code.asc()).all()

        progress_count = len(admin_unit_1)
        self.progressBar.setMaximum(progress_count)
        col = 0
        row = 10
        count = 1
        code1 = 0

        for au1 in admin_unit_1:
            worksheet.write(row, col, (count),format)
            worksheet.write(row, col+1, au1.name,format)
            col = 0
            column = col+2
            column_count_2 = 0
            all_landuse_count = 0
            area_level_3 = 0
            all_area_landuse = 0
            is_first = 0
            for con in conservation_type:
                code2 = str(con.code)[:2]
                landuse_count = self.session.query(ClLanduseType.description2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2).count()
                if landuse_count != 0:
                    landuse = self.session.query(ClLanduseType.description2,ClLanduseType.code2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2,ClLanduseType.code2).one()
                    if code1 == str(landuse.code2)[:2]:
                        is_first = 1
                        column = column + 1
                        worksheet.write(8,column,con.description,format)
                        worksheet.write(9,column, column,format)

                        srid_list = self.session.query((((((func.ST_X(func.ST_Centroid(CaParcelPollution.geometry))+186)/6)))).label("srid"))\
                                        .join(ParcelGt1, CaParcelPollution.geometry.ST_Intersects(ParcelGt1.geometry))\
                                        .join(AuLevel1, CaParcelPollution.geometry.ST_Within(AuLevel1.geometry))\
                                        .join(AuLevel2, CaParcelPollution.geometry.ST_Within(AuLevel2.geometry))\
                                        .filter(CaParcelPollution.pollution == con.code)\
                                        .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()
                        srid = 0
                        for a in srid_list:
                            srid = 32600 + int(a.srid)

                        area = self.session.query(func.sum(func.ST_Area(func.ST_Intersection(func.ST_Transform(func.ST_SetSRID(CaParcelPollution.geometry,4326),srid), func.ST_Transform(func.ST_SetSRID(ParcelGt1.geometry,4326),srid)))).label("area"))\
                                        .join(ParcelGt1, CaParcelPollution.geometry.ST_Intersects(ParcelGt1.geometry))\
                                        .join(AuLevel1, CaParcelPollution.geometry.ST_Within(AuLevel1.geometry))\
                                        .join(AuLevel2, CaParcelPollution.geometry.ST_Within(AuLevel2.geometry))\
                                        .filter(CaParcelPollution.pollution == con.code)\
                                        .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()
                        conservation_area = 0
                        for a in area:
                            if a.area == None or a.area == 0:
                                conservation_area = ''
                            else:
                                conservation_area = str(a.area)
                                conservation_area = float(conservation_area)
                                conservation_area = round(conservation_area,2)
                        worksheet.write(row,column, conservation_area,format)
                        if conservation_area == '':
                            conservation_area = 0
                        area_level_3 = area_level_3 + conservation_area
                        all_area_landuse = all_area_landuse + conservation_area
                        column_count_2 += 1
                        all_landuse_count += 1
                    else:
                        if is_first == 1:
                            code1 = 0
                            if area_level_3 == 0:
                                area_level_3 = ''
                            else:
                                area_level_3 = (round(area_level_3,2))
                            worksheet.write(row, column-column_count_2, area_level_3,format)
                            if column_count_2 > 1:
                                worksheet.merge_range(7,column-column_count_2+1,7,column, u"Үүнээс",format)
                            else:
                                worksheet.write(7,column, u"Үүнээс",format)
                            area_level_3 = 0
                            column_count_2 = 0
                    if code1 == 0:

                        column = column + 1
                        code1 = str(landuse.code2)[:2]
                        code2 = str(landuse.code2)[:2]
                        landuse_count = self.session.query(ClLanduseType.description2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2).count()
                        if landuse_count != 0:
                            landuse = self.session.query(ClLanduseType.description2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2).one()
                            worksheet.merge_range(7,column,8,column,landuse.description2+u' ,бүгд',format)

                            worksheet.write(9,column, column,format)
                            column = column + 1
                            worksheet.write(8,column,con.description,format)
                            worksheet.write(9,column, column,format)

                            srid_list = self.session.query((((((func.ST_X(func.ST_Centroid(CaParcelPollution.geometry))+186)/6)))).label("srid"))\
                                        .join(ParcelGt1, CaParcelPollution.geometry.ST_Intersects(ParcelGt1.geometry))\
                                        .join(AuLevel1, CaParcelPollution.geometry.ST_Within(AuLevel1.geometry))\
                                        .join(AuLevel2, CaParcelPollution.geometry.ST_Within(AuLevel2.geometry))\
                                        .filter(CaParcelPollution.pollution == con.code)\
                                        .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()
                            srid = 0
                            for a in srid_list:
                                srid = 32600 + int(a.srid)
                            area = self.session.query(func.sum(func.ST_Area(func.ST_Intersection(func.ST_Transform(func.ST_SetSRID(CaParcelPollution.geometry,4326),srid), func.ST_Transform(func.ST_SetSRID(ParcelGt1.geometry,4326),srid)))).label("area"))\
                                            .join(ParcelGt1, CaParcelPollution.geometry.ST_Intersects(ParcelGt1.geometry))\
                                            .join(AuLevel1, CaParcelPollution.geometry.ST_Within(AuLevel1.geometry))\
                                            .join(AuLevel2, CaParcelPollution.geometry.ST_Within(AuLevel2.geometry))\
                                            .filter(CaParcelPollution.pollution == con.code)\
                                            .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()

                            conservation_area = 0
                            for a in area:
                                if a.area == None or a.area == 0:
                                    conservation_area = ''
                                else:
                                    conservation_area = str(a.area)
                                    conservation_area = float(conservation_area)
                                    conservation_area = round(conservation_area,2)
                            worksheet.write(row,column, conservation_area,format)
                            if conservation_area == '':
                                conservation_area = 0
                            area_level_3 = area_level_3 + conservation_area
                            all_area_landuse = all_area_landuse + conservation_area
                            column_count_2 += 1
                            all_landuse_count += 1
            code1 = 0
            if area_level_3 == 0:
                area_level_3 = ''
            else:
                area_level_3 = (round(area_level_3,2))
            worksheet.write(row, column-column_count_2, area_level_3,format)
            if column_count_2 > 1:
                worksheet.merge_range(7,column-column_count_2+1,7,column, u"Үүнээс",format)
            else:
                worksheet.write(7,column, u"Үүнээс",format)
            if all_area_landuse == 0:
                all_area_landuse = ''
            else:
                all_area_landuse = (round(all_area_landuse,2))
            worksheet.write(row, 2, all_area_landuse,format)
            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
            row += 1
            count +=1
        worksheet.merge_range(row,0,row,1,u"ДҮН",format)
        for i in range(2,column+1):
            cell_up = xl_rowcol_to_cell(10, i)
            cell_down = xl_rowcol_to_cell(row-1, i)
            worksheet.write(row,i,'=SUM('+cell_up+':'+cell_down+')',format)

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_6.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_7(self):

        restrictions = DatabaseUtils.working_l2_code()
        default_path = r'D:/TM_LM2/reports'
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
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_7.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_landscape()
        worksheet.set_column('A:A', 3.5)
        worksheet.set_column('B:B', 15)
        worksheet.set_row(1,50)
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)

        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        worksheet.merge_range('D4:J4', u'ГАЗАР ХАМГААЛАХ АРГА ХЭМЖЭЭНИЙ '+str(self.begin_year_sbox.value())+u' ОНЫ ТАЙЛАН',format_header)
        worksheet.merge_range('A2:G2', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('J2:P2', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 7 дугаар хавсралт',format_header)
        worksheet.merge_range('J6:L6', u'/га-гаар/        Маягт ГТ-7 ',format_header)
        worksheet.merge_range('A8:A9', u'Д/д', format)
        worksheet.merge_range('B8:B9', u'Аймаг, нийслэл, сум, дүүргийн нэр',format)
        worksheet.merge_range('C8:C9', u'Хамгаалах арга хэмжээ авсан нийт талбай, га',format)
        worksheet.write(9,0, 0,format)
        worksheet.write(9,1, u'А',format)
        worksheet.write(9,2, 1,format)

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")

        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        if len(au_level1_list) > 1:
            admin_unit_1 = self.session.query(AuLevel1)\
                        .filter(AuLevel1.code.in_(au_level1_list)).all()
        elif len(au_level1_list) == 1 or len(au_level2_list) >= 1:
            admin_unit_1 = self.session.query(AuLevel2)\
                        .filter(AuLevel2.code.in_(au_level2_list)).all()
        conservation_type = self.session.query(ClConservationType).order_by(ClConservationType.code.asc()).all()

        progress_count = len(admin_unit_1)
        self.progressBar.setMaximum(progress_count)
        col = 0
        row = 10
        count = 1
        code1 = 0

        for au1 in admin_unit_1:
            worksheet.write(row, col, (count),format)
            worksheet.write(row, col+1, au1.name,format)
            col = 0
            column = col+2
            column_count_2 = 0
            all_landuse_count = 0
            area_level_3 = 0
            all_area_landuse = 0
            is_first = 0
            for con in conservation_type:
                code2 = str(con.code)[:2]
                landuse_count = self.session.query(ClLanduseType.description2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2).count()
                if landuse_count != 0:
                    landuse = self.session.query(ClLanduseType.description2,ClLanduseType.code2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2,ClLanduseType.code2).one()
                    if code1 == str(landuse.code2)[:2]:
                        is_first = 1
                        column = column + 1
                        worksheet.write(8,column,con.description,format)
                        worksheet.write(9,column, column,format)

                        srid_list = self.session.query((((((func.ST_X(func.ST_Centroid(CaParcelConservation.geometry))+186)/6)))).label("srid"))\
                                        .join(ParcelGt1, CaParcelConservation.geometry.ST_Intersects(ParcelGt1.geometry))\
                                        .join(AuLevel1, CaParcelConservation.geometry.ST_Within(AuLevel1.geometry))\
                                        .join(AuLevel2, CaParcelConservation.geometry.ST_Within(AuLevel2.geometry))\
                                        .filter(CaParcelConservation.conservation == con.code)\
                                        .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()
                        srid = 0
                        for a in srid_list:
                            srid = 32600 + int(a.srid)

                        area = self.session.query(func.sum(func.ST_Area(func.ST_Intersection(func.ST_Transform(func.ST_SetSRID(CaParcelConservation.geometry,4326),srid), func.ST_Transform(func.ST_SetSRID(ParcelGt1.geometry,4326),srid)))).label("area"))\
                                        .join(ParcelGt1, CaParcelConservation.geometry.ST_Intersects(ParcelGt1.geometry))\
                                        .join(AuLevel1, CaParcelConservation.geometry.ST_Within(AuLevel1.geometry))\
                                        .join(AuLevel2, CaParcelConservation.geometry.ST_Within(AuLevel2.geometry))\
                                        .filter(CaParcelConservation.conservation == con.code)\
                                        .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()
                        conservation_area = 0
                        for a in area:
                            if a.area == None or a.area == 0:
                                conservation_area = ''
                            else:
                                conservation_area = str(a.area)
                                conservation_area = float(conservation_area)
                                conservation_area = round(conservation_area,2)
                        worksheet.write(row,column, conservation_area,format)
                        if conservation_area == '':
                            conservation_area = 0
                        area_level_3 = area_level_3 + conservation_area
                        all_area_landuse = all_area_landuse + conservation_area
                        column_count_2 += 1
                        all_landuse_count += 1
                    else:
                        if is_first == 1:
                            code1 = 0
                            if area_level_3 == 0:
                                area_level_3 = ''
                            else:
                                area_level_3 = (round(area_level_3,2))
                            worksheet.write(row, column-column_count_2, area_level_3,format)
                            if column_count_2 > 1:
                                worksheet.merge_range(7,column-column_count_2+1,7,column, u"Үүнээс",format)
                            else:
                                worksheet.write(7,column, u"Үүнээс",format)
                            area_level_3 = 0
                            column_count_2 = 0
                    if code1 == 0:

                        column = column + 1
                        code1 = str(landuse.code2)[:2]
                        code2 = str(landuse.code2)[:2]
                        landuse_count = self.session.query(ClLanduseType.description2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2).count()
                        if landuse_count != 0:
                            landuse = self.session.query(ClLanduseType.description2).filter(ClLanduseType.code2 == int(code2)).group_by(ClLanduseType.description2).one()
                            worksheet.merge_range(7,column,8,column,landuse.description2+u' ,бүгд',format)

                            worksheet.write(9,column, column,format)
                            column = column + 1
                            worksheet.write(8,column,con.description,format)
                            worksheet.write(9,column, column,format)
                            srid_list = self.session.query((((((func.ST_X(func.ST_Centroid(CaParcelConservation.geometry))+186)/6)))).label("srid"))\
                                        .join(ParcelGt1, CaParcelConservation.geometry.ST_Intersects(ParcelGt1.geometry))\
                                        .join(AuLevel1, CaParcelConservation.geometry.ST_Within(AuLevel1.geometry))\
                                        .join(AuLevel2, CaParcelConservation.geometry.ST_Within(AuLevel2.geometry))\
                                        .filter(CaParcelConservation.conservation == con.code)\
                                        .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()
                            srid = 0
                            for a in srid_list:
                                srid = 32600 + int(a.srid)

                            area = self.session.query(func.sum(func.ST_Area(func.ST_Intersection(func.ST_Transform(func.ST_SetSRID(CaParcelConservation.geometry,4326),srid), func.ST_Transform(func.ST_SetSRID(ParcelGt1.geometry,4326),srid)))).label("area"))\
                                            .join(ParcelGt1, CaParcelConservation.geometry.ST_Intersects(ParcelGt1.geometry))\
                                            .join(AuLevel1, CaParcelConservation.geometry.ST_Within(AuLevel1.geometry))\
                                            .join(AuLevel2, CaParcelConservation.geometry.ST_Within(AuLevel2.geometry))\
                                            .filter(CaParcelConservation.conservation == con.code)\
                                            .filter(or_(AuLevel1.code == au1.code, AuLevel2.code == au1.code)).all()

                            conservation_area = 0
                            for a in area:
                                if a.area == None or a.area == 0:
                                    conservation_area = ''
                                else:
                                    conservation_area = str(a.area)
                                    conservation_area = float(conservation_area)
                                    conservation_area = round(conservation_area,2)
                            worksheet.write(row,column, conservation_area,format)
                            if conservation_area == '':
                                conservation_area = 0
                            area_level_3 = area_level_3 + conservation_area
                            all_area_landuse = all_area_landuse + conservation_area
                            column_count_2 += 1
                            all_landuse_count += 1
            code1 = 0
            if area_level_3 == 0:
                area_level_3 = ''
            else:
                area_level_3 = (round(area_level_3,2))
            worksheet.write(row, column-column_count_2, area_level_3,format)
            if column_count_2 > 1:
                worksheet.merge_range(7,column-column_count_2+1,7,column, u"Үүнээс",format)
            else:
                worksheet.write(7,column, u"Үүнээс",format)
            if all_area_landuse == 0:
                all_area_landuse = ''
            else:
                all_area_landuse = (round(all_area_landuse,2))
            worksheet.write(row, 2, all_area_landuse,format)
            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
            row += 1
            count +=1
        worksheet.merge_range(row,0,row,1,u"ДҮН",format)
        for i in range(2,column+1):
            cell_up = xl_rowcol_to_cell(10, i)
            cell_down = xl_rowcol_to_cell(row-1, i)
            worksheet.write(row,i,'=SUM('+cell_up+':'+cell_down+')',format)

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_7.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_8(self):

        restrictions = DatabaseUtils.working_l2_code()
        default_path = r'D:/TM_LM2/reports'
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
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_8.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_row(0,50)
        worksheet.set_row(6,25)
        worksheet.set_paper(8)
        worksheet.set_landscape()
        worksheet.set_column('B:B', 20)
        worksheet.set_margins(left=0.3, right=0.3, top=0.3, bottom=0.3)
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)

        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        worksheet.merge_range('D2:J2', u'ГАЗРЫН ТӨЛБӨР НОГДУУЛАЛТ, ТӨЛӨЛТИЙН ТАЙЛАН /'+str(self.begin_year_sbox.value())+u' он/',format_header)
        worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 8 дугаар хавсралт',format_header)
        worksheet.merge_range('K2:M2', u'/мян.төг/            Маягт ГТ-8 ',format_header)
        worksheet.merge_range('A4:A8', u'д/д', format)
        worksheet.merge_range('B4:B8', u'Аймаг, нийслэл, сум, дүүргийн нэр',format)
        worksheet.merge_range('C4:C8', u'Газрын төлбөрийн төлөвлөгөө(мян.төг)',format)
        worksheet.merge_range('D4:D8', u'Төлбөл зохих нийт төлбөр/мян.төг/',format)
        worksheet.merge_range('E4:E8', u'Тайлангийн хугацаанд төлсөн төлбөр(мян.төг)',format)
        worksheet.merge_range('F4:F8', u'Нийт үлдэгдэл төлбөр(мян.төг)',format)
        worksheet.write(8,0, 0,format)
        worksheet.write(8,1, 1,format)
        worksheet.write(8,2, 2,format)
        worksheet.write(8,3, 3,format)
        worksheet.write(8,4, 4,format)
        worksheet.write(8,5, 5,format)

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")

        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        if len(au_level1_list) > 1:
            admin_unit_1 = self.session.query(AuLevel1)\
                        .filter(AuLevel1.code.in_(au_level1_list)).all()
        elif len(au_level1_list) == 1 or len(au_level2_list) >= 1:
            admin_unit_1 = self.session.query(AuLevel2)\
                        .filter(AuLevel2.code.in_(au_level2_list)).all()
        special_needs = self.session.query(ClLanduseType.code2,ClLanduseType.description2).group_by(ClLanduseType.code2,ClLanduseType.description2)\
                                                    .order_by(ClLanduseType.code2.asc()).all()
        progress_count = len(admin_unit_1)
        self.progressBar.setMaximum(progress_count)
        code1 = 0
        row = 9
        col = 0
        count = 1
        for au1 in admin_unit_1:
            worksheet.write(row, col, count,format)
            worksheet.write(row, col+1, au1.name,format)
            col = 0
            column = col+4
            is_first = 0
            column_count_1 = 0
            all_balance = 0
            all_fee = 0
            all_paymnet = 0

            for code_2, desc_2 in special_needs:

                if code1 == str(code_2)[:1]:
                    is_first = 1
                    worksheet.write(8,column, column,format)

                    worksheet.merge_range(6,column,6,column+4, desc_2,format)
                    if code_2 == 11:
                        worksheet.write(7,column,u'Төлбөр ногдох нийт хонин толгой',format)
                    else:
                        worksheet.write(7,column,u'Төлбөр ногдох нийт талбай/га/',format)
                    fee_all_area = self.session.query(func.sum(ParcelFeeReport.fee_area).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.contract_no != None).filter(ParcelFeeReport.landuse_code2 == code_2)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if fee_all_area.area == None or fee_all_area.area == 0:
                        all_area = ''
                    else:
                        all_area = float(fee_all_area.area)/10000
                        all_area = round(all_area, 2)
                    worksheet.write(row,column, all_area, format)
                    if all_area == '':
                        all_area = 0

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Төлбөрөөс чөлөөлсөн/га/',format)
                    subsidized_area = self.session.query(func.sum(ParcelFeeReport.subsidized_area).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.landuse_code2 == code_2).filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.area_m2 > ParcelFeeReport.subsidized_area)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if subsidized_area.area == None or subsidized_area.area == 0:
                        sub_area = ''
                    else:
                        sub_area = float(subsidized_area.area)/10000
                        sub_area = round(sub_area, 2)
                    worksheet.write(row,column, sub_area, format)
                    if sub_area == '':
                        sub_area = 0

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Төлбөл зохих төлбөр/мян.төг/',format)
                    fee_contract = self.session.query(func.sum(ParcelFeeReport.fee_contract).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.landuse_code2 == code_2).filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.fee_contract != None)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if fee_contract.area == None or fee_contract.area == 0:
                        fee = ''
                    else:
                        fee = float(fee_contract.area)/1000
                        fee = round(fee, 2)
                    worksheet.write(row,column, fee, format)
                    if fee == '':
                        fee = 0
                    all_fee = all_fee + fee

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Үүнээс төлсөн төлбөр/мян.төг/',format)
                    fee_payment = self.session.query(func.sum(ParcelFeeReport.amount_paid).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.landuse_code2 == code_2).filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.amount_paid != None)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if fee_payment.area == None or fee_payment.area == 0:
                        payment = ''
                    else:
                        payment = float(fee_payment.area)/1000
                        payment = round(payment, 2)
                    worksheet.write(row,column, payment, format)
                    if payment == '':
                        payment = 0
                    all_paymnet = all_paymnet + payment

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Үлдэгдэл төлбөр/мян.төг/',format)
                    balance = fee - payment
                    worksheet.write(row,column, balance, format)
                    all_balance = all_balance + balance

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    column_count_1 = column_count_1 + 5
                else:
                    if is_first == 1:

                        if column_count_1 > 1:
                            worksheet.merge_range(5,column-column_count_1-1,5,column-1, u"Үүнээс",format)
                        else:
                            worksheet.write(5,column-1, u"Үүнээс",format)
                        if code1 == '1':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_1,format)
                        elif code1 == '2':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_2,format)
                        elif code1 == '3':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_3,format)
                        elif code1 == '4':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_4,format)
                        elif code1 == '5':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_5,format)
                        elif code1 == '6':
                            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_6,format)
                        code1 = 0
                        column_count_1 = 0
                if code1 == 0:
                    code1 = str(code_2)[:1]
                    if is_first == 0:
                        column = column + 2
                    worksheet.merge_range(6,column,6,column+4,desc_2,format)
                    if code_2 == 11:
                        worksheet.write(7,column,u'Төлбөр ногдох нийт хонин толгой',format)
                    else:
                        worksheet.write(7,column,u'Төлбөр ногдох нийт талбай/га/',format)
                    fee_all_area = self.session.query(func.sum(ParcelFeeReport.fee_area).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.contract_no != None).filter(ParcelFeeReport.landuse_code2 == code_2)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if fee_all_area.area == None or fee_all_area.area == 0:
                        all_area = ''
                    else:
                        all_area = float(fee_all_area.area)/10000
                        all_area = round(all_area, 2)
                    worksheet.write(row,column, all_area, format)
                    if all_area == '':
                        all_area = 0

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Төлбөрөөс чөлөөлсөн/га/',format)
                    subsidized_area = self.session.query(func.sum(ParcelFeeReport.subsidized_area).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.landuse_code2 == code_2).filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.area_m2 > ParcelFeeReport.subsidized_area)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if subsidized_area.area == None or subsidized_area.area == 0:
                        sub_area = ''
                    else:
                        sub_area = float(subsidized_area.area)/10000
                        sub_area = round(sub_area, 2)
                    worksheet.write(row,column, sub_area, format)
                    if sub_area == '':
                        sub_area = 0

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Төлбөл зохих төлбөр/мян.төг/',format)
                    fee_contract = self.session.query(func.sum(ParcelFeeReport.fee_contract).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.landuse_code2 == code_2).filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.fee_contract != None)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if fee_contract.area == None or fee_contract.area == 0:
                        fee = ''
                    else:
                        fee = float(fee_contract.area)/1000
                        fee = round(fee, 2)
                    worksheet.write(row,column, fee, format)
                    if fee == '':
                        fee = 0
                    all_fee = all_fee + fee

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Үүнээс төлсөн төлбөр/мян.төг/',format)
                    fee_payment = self.session.query(func.sum(ParcelFeeReport.amount_paid).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.end_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.landuse_code2 == code_2).filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.amount_paid != None)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
                    if fee_payment.area == None or fee_payment.area == 0:
                        payment = ''
                    else:
                        payment = float(fee_payment.area)/1000
                        payment = round(payment, 2)
                    worksheet.write(row,column, payment, format)
                    if payment == '':
                        payment = 0
                    all_paymnet = all_paymnet + payment

                    column = column + 1
                    worksheet.write(8,column, column,format)
                    worksheet.write(7,column,u'Үлдэгдэл төлбөр/мян.төг/',format)
                    balance = fee - payment
                    worksheet.write(row,column, balance, format)
                    all_balance = all_balance + balance

                    column = column + 1
                    column_count_1 = column_count_1 + 4
            code1 = 0
            worksheet.merge_range(4,column-column_count_1-1,4,column-1, LANDUSE_6,format)
            worksheet.merge_range(3,6,3,column-1, u"Үүнээс газрын ангиаллын төрлөөр",format)
            if column_count_1 > 1:
                worksheet.merge_range(5,column-column_count_1-1,5,column-1, u"Үүнээс",format)
            else:
                worksheet.write(5,column-1, u"Үүнээс",format)

            worksheet.merge_range(3,column,7,column, u'Дараа оны төсвийн төлөвлөгөө(мян.төг)',format)
            worksheet.write(8,column, column,format)
            fee_report_year = self.session.query(func.sum(ParcelFeeReport.fee_contract).label("area"))\
                                .filter(ParcelFeeReport.valid_till == 'infinity')\
                                .filter(ParcelFeeReport.contract_date < self.after_year_date)\
                                .filter(ParcelFeeReport.contract_no != None)\
                                .filter(ParcelFeeReport.fee_area != None)\
                                .filter(ParcelFeeReport.parcel_id != None)\
                                .filter(ParcelFeeReport.fee_contract != None)\
                                .filter(or_(ParcelFeeReport.au1_code == au1.code, ParcelFeeReport.au2_code == au1.code))\
                                .one()
            if fee_report_year.area == None or fee_report_year.area == 0:
                fee = 0
            else:
                fee = float(fee_report_year.area)/1000
                fee = round(fee, 2)
            worksheet.write(row,column, fee+all_balance, format)

            worksheet.write(row,2,all_fee, format)
            worksheet.write(row,3,all_fee, format)
            worksheet.write(row,4,all_paymnet, format)
            worksheet.write(row,5,all_balance, format)

            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
            row += 1
            count +=1
        worksheet.merge_range(row,0,row,1, u'ДҮН',format)
        for i in range(2,column+1):
            cell_up = xl_rowcol_to_cell(9, i)
            cell_down = xl_rowcol_to_cell(row-1, i)
            worksheet.write(row,i,'=SUM('+cell_up+':'+cell_down+')',format)
        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_8.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    def __report_gt_9(self):

        restrictions = DatabaseUtils.working_l2_code()
        default_path = r'D:/TM_LM2/reports'
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
        workbook = xlsxwriter.Workbook(default_path + "/"+restrictions+"_"+"report_gt_9.xlsx")
        worksheet = workbook.add_worksheet()

        worksheet.set_row(0,50)
        worksheet.set_row(3,50)
        worksheet.set_column('A:A', 3)
        worksheet.set_column('B:B', 20)
        worksheet.set_paper(8)
        worksheet.set_landscape()
        worksheet.set_margins(left=0.3, right=0.3, top=0.3, bottom=0.3)
        format = workbook.add_format()
        format.set_text_wrap()
        format.set_align('center')
        format.set_align('vcenter')
        format.set_font_name('Times New Roman')
        format.set_font_size(8)

        format.set_border(1)
        format.set_shrink()

        format_90 = workbook.add_format()
        format_90.set_text_wrap()
        format_90.set_align('center')
        format_90.set_align('vcenter')
        format_90.set_rotation(90)
        format_90.set_font_name('Times New Roman')
        format_90.set_font_size(8)
        format_90.set_border(1)
        format.set_shrink()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(8)
        format_header.set_bold()

        worksheet.merge_range('D2:J2', u'МОНГОЛ УЛСЫН ИРГЭНД ӨМЧЛҮҮЛСЭН ГАЗРЫН ТАЙЛАН '+str(self.begin_year_sbox.value())+u' ОН',format_header)
        worksheet.merge_range('A1:E1', u'Жил бүр сум, дүүргийн Засаг дарга 12-р сарын 15-ны дотор аймаг, нийслэлийн Засаг даргад, аймаг, нийслэлийн Засаг дарга дараа оны 01-р сарын 15-ны дотор Газрын асуудал эрхэлсэн төрийн захиргааны байгууллагад тус тус гаргана.',format_header)
        worksheet.merge_range('H1:P1', u'Засгийн газрын 2003 оны 204 дүгээр тогтоолын 9 дүгээр хавсралт',format_header)
        worksheet.merge_range('K2:M2', u'/га-гаар/            Маягт ГТ-9 ',format_header)
        worksheet.merge_range('A4:A5', u'№', format)
        worksheet.merge_range('B4:B5', u'Аймаг, нийслэл, сум, дүүргийн нэр',format)
        worksheet.merge_range('C4:C5', u'Нийт газар өмчлөгч иргэдийн тоо',format_90)
        worksheet.merge_range('D4:D5', u'Өмчлөлд буй газрын нийт хэмжээ /га/',format_90)
        worksheet.merge_range('E4:F4', u'Гэр бүлийн хэрэгцээнд нэг удаа үнэгүй өмчилсөн',format)
        worksheet.merge_range('G4:H4', u'Гэр бүлийн хэрэгцээнд үнээр нь худалдаж авсан',format)
        worksheet.merge_range('I4:J4', u'Аж ахуйн зориулалтаар давуу эрхээр худалдаж авсан',format)
        worksheet.merge_range('K4:L4', u'Аж ахуйн зориулалтаар дуудлага худалдаагаар худалдаж авсан',format)
        worksheet.merge_range('M4:N4', u'Газар тариалангийн зориулалтаар давуу эрхээр худалдаж авсан',format)
        worksheet.merge_range('O4:P4', u'Газар тариалангийн зориулалтаар дуудлага худалдаагаар худалдаж авсан',format)
        worksheet.write('E5', u'Иргэдийн тоо',format_90)
        worksheet.write('F5', u'Газрын хэмжээ/га/',format_90)
        worksheet.write('G5', u'Иргэдийн тоо',format_90)
        worksheet.write('H5', u'Газрын хэмжээ/га/',format_90)
        worksheet.write('I5', u'Иргэдийн тоо',format_90)
        worksheet.write('J5', u'Газрын хэмжээ/га/',format_90)
        worksheet.write('K5', u'Иргэдийн тоо',format_90)
        worksheet.write('L5', u'Газрын хэмжээ/га/',format_90)
        worksheet.write('M5', u'Иргэдийн тоо',format_90)
        worksheet.write('N5', u'Газрын хэмжээ/га/',format_90)
        worksheet.write('O5', u'Иргэдийн тоо',format_90)
        worksheet.write('P5', u'Газрын хэмжээ/га/',format_90)
        worksheet.merge_range('Q4:Q5', u'Өмчилсөн газрын үл хөдлөх хөрөнгийн татвар ногдуулалт/мян.төг/',format_90)
        worksheet.merge_range('R4:R5', u'Өмчилсөн газрын үл хөдлөх хөрөнгийн татварын орлогын хэмжээ/мян.төг/',format_90)
        worksheet.write(5,0, u'А',format)
        worksheet.write(5,1, u'Б',format)
        worksheet.write(5,2, 1,format)
        worksheet.write(5,3, 2,format)
        worksheet.write(5,4, 3,format)
        worksheet.write(5,5, 4,format)
        worksheet.write(5,6, 5,format)
        worksheet.write(5,7, 6,format)
        worksheet.write(5,8, 7,format)
        worksheet.write(5,9, 8,format)
        worksheet.write(5,10, 9,format)
        worksheet.write(5,11, 10,format)
        worksheet.write(5,12, 11,format)
        worksheet.write(5,13, 12,format)
        worksheet.write(5,14, 13,format)
        worksheet.write(5,15, 14,format)
        worksheet.write(5,16, 15,format)
        worksheet.write(5,17, 16,format)

        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")

        au_level1_string = self.userSettings.restriction_au_level1
        au_level1_list = au_level1_string.split(",")
        if len(au_level1_list) > 1:
            admin_unit_1 = self.session.query(AuLevel1)\
                        .filter(AuLevel1.code.in_(au_level1_list)).all()
        elif len(au_level1_list) == 1 or len(au_level2_list) >= 1:
            admin_unit_1 = self.session.query(AuLevel2)\
                        .filter(AuLevel2.code.in_(au_level2_list)).all()
        # admin_unit_1 = self.session.query(AuLevel1)\
        #         .filter(or_(AuLevel1.code == "021", AuLevel1.code == "022", AuLevel1.code == "023", AuLevel1.code == "041", AuLevel1.code == "042"\
        #                     , AuLevel1.code == "043", AuLevel1.code == "044", AuLevel1.code == "045", AuLevel1.code == "046", AuLevel1.code == "048"\
        #                     , AuLevel1.code == "061", AuLevel1.code == "062", AuLevel1.code == "063", AuLevel1.code == "064", AuLevel1.code == "065"\
        #                     , AuLevel1.code == "067", AuLevel1.code == "081", AuLevel1.code == "082", AuLevel1.code == "083", AuLevel1.code == "084", AuLevel1.code == "085")).order_by(AuLevel1.name.asc()).all()

        progress_count = len(admin_unit_1)
        self.progressBar.setMaximum(progress_count)
        row = 6
        col = 0
        count = 1

        for au1 in admin_unit_1:
            record_area_all = 0
            record_area_app_type1 = 0
            record_area_app_type4 = 0
            record_area_type16_economy = 0
            excess_area = 0
            record_area_app_landuse13 = 0
            record_area_app16_landuse = 0

            worksheet.write(row, col, count,format)
            worksheet.write(row, col+1, au1.name,format)

            person_count = self.session.query(ParcelReport.person_pk_id).filter(ParcelReport.record_no != None).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_pk_id).count()
            record_area_sum_all = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.record_no != None).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).one()

            person_count_app_type1 = self.session.query(ParcelReport.person_pk_id).filter(ParcelReport.record_no != None).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(ParcelReport.app_type == 1).\
                            filter(or_(ParcelReport.landuse == 2204,ParcelReport.landuse == 2205,ParcelReport.landuse == 2206)).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_pk_id).count()
            record_area_sum_all_app_type1 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.record_no != None).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(ParcelReport.app_type == 1).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(or_(ParcelReport.landuse == 2204,ParcelReport.landuse == 2205,ParcelReport.landuse == 2206)).one()

            person_count_app_type4 = self.session.query(ParcelReport.person_pk_id).filter(ParcelReport.record_no != None).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(ParcelReport.app_type == 4).\
                            filter(ParcelReport.right_type == 20).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_pk_id).count()
            record_area_sum_all_app_type4 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.record_no != None).\
                            filter(ParcelReport.right_type == 20).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(ParcelReport.app_type == 4).one()

            person_count_app_type16_economy = self.session.query(ParcelReport.person_pk_id).filter(ParcelReport.record_no != None).\
                            join(SetApplicationTypeLanduseType, ParcelReport.landuse == SetApplicationTypeLanduseType.landuse_type).\
                            filter(SetApplicationTypeLanduseType.application_type == 4).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).\
                            filter(ParcelReport.app_type == 16).\
                            filter(SetApplicationTypeLanduseType.landuse_type != None).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_pk_id).count()
            record_area_sum_all_app_type16_economy = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.record_no != None).\
                            join(SetApplicationTypeLanduseType, ParcelReport.landuse == SetApplicationTypeLanduseType.landuse_type).\
                            filter(SetApplicationTypeLanduseType.application_type == 4).\
                            filter(ParcelReport.right_type == 20).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).\
                            filter(SetApplicationTypeLanduseType.landuse_type != None).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(ParcelReport.app_type == 16).one()

            person_count_app_landuse13 = self.session.query(ParcelReport.person_pk_id).filter(ParcelReport.record_no != None).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(or_(ParcelReport.landuse == 1301,ParcelReport.landuse == 1302,\
                            ParcelReport.landuse == 1303,ParcelReport.landuse == 1304,ParcelReport.landuse == 1305,ParcelReport.landuse == 1306,\
                            ParcelReport.landuse == 1401,ParcelReport.landuse == 1402,ParcelReport.landuse == 1403,\
                            ParcelReport.landuse == 1404,ParcelReport.landuse == 1405,ParcelReport.landuse == 1406)).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_pk_id).count()
            record_area_sum_all_app_landuse13 = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.record_no != None).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(or_(ParcelReport.landuse == 1301,ParcelReport.landuse == 1302,\
                            ParcelReport.landuse == 1303,ParcelReport.landuse == 1304,ParcelReport.landuse == 1305,ParcelReport.landuse == 1306,\
                            ParcelReport.landuse == 1401,ParcelReport.landuse == 1402,ParcelReport.landuse == 1403,\
                            ParcelReport.landuse == 1404,ParcelReport.landuse == 1405,ParcelReport.landuse == 1406)).one()

            person_count_app16_landuse = self.session.query(ParcelReport.person_pk_id).filter(ParcelReport.record_no != None).\
                            filter(ParcelReport.app_type == 16).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(or_(ParcelReport.landuse_code2 == 13, ParcelReport.landuse_code2 == 14, ParcelReport.landuse_code2 == 15)).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_pk_id).count()
            record_area_sum_all_app16_landuse = self.session.query(func.sum(ParcelReport.area_m2*ParcelReport.share).label("area")).filter(ParcelReport.record_no != None).\
                            filter(ParcelReport.app_type == 16).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(or_(ParcelReport.landuse_code2 == 13, ParcelReport.landuse_code2 == 14, ParcelReport.landuse_code2 == 15)).one()

            excess_person_count = self.session.query(ParcelReport.person_pk_id).filter(ParcelReport.record_no != None).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(ParcelReport.excess_area != 0).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            group_by(ParcelReport.person_pk_id).count()

            excess_area_sum = self.session.query(func.sum(ParcelReport.excess_area * ParcelReport.share).label("excess_area"))\
                            .filter(ParcelReport.record_no != None).\
                            filter(ParcelReport.record_no != None).filter(ParcelReport.valid_till == 'infinity').\
                            filter(ParcelReport.record_date < self.end_date).\
                            filter(or_(ParcelReport.au1_code == au1.code, ParcelReport.au2_code == au1.code)).filter(ParcelReport.excess_area != 0).one()

            tax = self.session.query(func.sum(ParcelTaxReport.land_tax).label("area"))\
                                .filter(ParcelTaxReport.valid_till == 'infinity')\
                                .filter(ParcelTaxReport.record_date < self.end_date)\
                                .filter(ParcelTaxReport.record_no != None)\
                                .filter(ParcelTaxReport.tax_area != None)\
                                .filter(ParcelTaxReport.parcel_id != None)\
                                .filter(ParcelTaxReport.land_tax != None)\
                                .filter(or_(ParcelTaxReport.au1_code == au1.code, ParcelTaxReport.au2_code == au1.code))\
                                .one()
            if tax.area == None or tax.area == 0:
                fee = ''
            else:
                fee = float(tax.area)/1000
                fee = round(fee, 2)
            worksheet.write(row,16, fee, format)

            tax_payment = self.session.query(func.sum(ParcelTaxReport.amount_paid).label("area"))\
                                .filter(ParcelTaxReport.valid_till == 'infinity')\
                                .filter(ParcelTaxReport.record_date < self.end_date)\
                                .filter(ParcelTaxReport.record_no != None)\
                                .filter(ParcelTaxReport.parcel_id != None)\
                                .filter(ParcelTaxReport.amount_paid != None)\
                                .filter(or_(ParcelTaxReport.au1_code == au1.code, ParcelTaxReport.au2_code == au1.code))\
                                .one()
            if tax_payment.area == None or tax_payment.area == 0:
                payment = ''
            else:
                payment = float(tax_payment.area)/1000
                payment = round(payment, 2)
            worksheet.write(row,17, payment, format)

            if record_area_sum_all.area != None:
                record_area_all = round(record_area_sum_all.area/10000, 2)
            else:
                record_area_all = ""
            if record_area_sum_all_app_type1.area != None:
                record_area_app_type1 = round(record_area_sum_all_app_type1.area/10000, 2)
            else:
                record_area_app_type1 = ""
            if record_area_sum_all_app_type4.area != None:
                record_area_app_type4 = round(record_area_sum_all_app_type4.area/10000, 2)
            else:
                record_area_app_type4 = ""
            if record_area_sum_all_app_type16_economy.area != None:
                record_area_type16_economy = round(record_area_sum_all_app_type16_economy.area/10000, 2)
            else:
                record_area_type16_economy = ""
            if record_area_sum_all_app_landuse13.area != None:
                record_area_app_landuse13 = round(record_area_sum_all_app_landuse13.area/10000, 2)
            else:
                record_area_app_landuse13 = ""
            if excess_area_sum.excess_area != None:
                excess_area = round(excess_area_sum.excess_area/10000, 2)
            else:
                excess_area = ""
            if record_area_sum_all_app16_landuse.area != None:
                record_area_app16_landuse = round(record_area_sum_all_app16_landuse.area/10000, 2)
            else:
                record_area_app16_landuse = ""
            worksheet.write(row, col+2,person_count,format)
            worksheet.write(row, col+3,record_area_all,format)
            worksheet.write(row, col+4,person_count_app_type1,format)
            worksheet.write(row, col+5,record_area_app_type1,format)
            worksheet.write(row, col+6,excess_person_count,format)
            worksheet.write(row, col+7,excess_area,format)
            worksheet.write(row, col+8,person_count_app_type4,format)
            worksheet.write(row, col+9,record_area_app_type4,format)
            worksheet.write(row, col+10,person_count_app_type16_economy, format)
            worksheet.write(row, col+11,record_area_type16_economy,format)
            worksheet.write(row, col+12,person_count_app_landuse13,format)
            worksheet.write(row, col+13,record_area_app_landuse13,format)
            worksheet.write(row, col+14,person_count_app16_landuse,format)
            worksheet.write(row, col+15,record_area_app16_landuse,format)

            value_p = self.progressBar.value() + 1
            self.progressBar.setValue(value_p)
            row += 1
            count +=1
        worksheet.merge_range(row,0,row,1, u'ДҮН',format)
        for i in range(2,18):
            cell_up = xl_rowcol_to_cell(6, i)
            cell_down = xl_rowcol_to_cell(row-1, i)
            worksheet.write(row,i,'=SUM('+cell_up+':'+cell_down+')',format)
        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + "/"+restrictions+"_"+"report_gt_9.xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    @pyqtSlot()
    def on_print_button_clicked(self):

        self.progressBar.setVisible(True)
        self.progressBar.setMinimum(1)
        self.progressBar.setValue(0)
        user_name = QSettings().value(SettingsConstants.USER)
        self.userSettings = DatabaseUtils.role_settings(user_name)
        au_level2_string = self.userSettings.restriction_au_level2
        au_level2_list = au_level2_string.split(",")
        sql = ""

        itemsList = self.listWidget.selectedItems()
        code = '0'
        for item in itemsList:
            code = str(item.text()[:2])

        if code == '01':
            self.__report_gt_1()
        elif code == '02':
            self.__report_gt_2()
        elif code == '03':
            self.__report_gt_3()
        elif code == '04':
            self.__report_gt_4()
        elif code == '05':
            self.__report_gt_5()
        elif code == '06':
            self.__report_gt_6()
        elif code == '07':
            self.__report_gt_7()
        elif code == '08':
            self.__report_gt_8()
        elif code == '09':
            self.__report_gt_9()

        self.progressBar.setVisible(False)

    @pyqtSlot()
    def on_layer_view_button_clicked(self):

        restrictions = DatabaseUtils.working_l2_code()
        itemsList = self.listWidget.selectedItems()
        code = '0'
        for item in itemsList:
            code = str(item.text()[:2])
        if code == '01':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt1_report")
            if tmp_parcel_layer is None:
                LayerUtils.load_layer_by_name("view_gt1_report", "parcel_id", restrictions)
        elif code == '02':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt2_report")
            if tmp_parcel_layer is None:
                LayerUtils.load_layer_by_name("view_gt2_report", "parcel_id", restrictions)
        elif code == '03':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt2_report")
            if tmp_parcel_layer is None:
                LayerUtils.load_layer_by_name("view_gt2_report", "parcel_id", restrictions)
        elif code == '04':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt4_report")
            if tmp_parcel_layer is None:
                LayerUtils.load_layer_by_name("view_gt4_report", "parcel_id", restrictions)
        elif code == '06':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt6_report")
            if tmp_parcel_layer is None:
                LayerUtils.load_layer_by_name("view_gt6_report", "parcel_id", restrictions)
        elif code == '07':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt7_report")
            if tmp_parcel_layer is None:
                LayerUtils.load_layer_by_name("view_gt7_report", "parcel_id", restrictions)
        elif code == '08':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt8_report")
            if tmp_parcel_layer is None:
                LayerUtils.load_layer_by_name("view_gt8_report", "parcel_id", restrictions)
        elif code == '09':
            tmp_parcel_layer = LayerUtils.layer_by_data_source("s" + restrictions, "view_gt9_report")
            if tmp_parcel_layer is None:
                LayerUtils.load_layer_by_name("view_gt9_report", "parcel_id", restrictions)








