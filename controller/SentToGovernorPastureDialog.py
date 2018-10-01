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
from datetime import timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_, and_, desc
from xlrd import open_workbook
from ..view.Ui_SentToGovernorPastureDialog import *
from ..utils.SessionHandler import SessionHandler
from ..model.CtApplication import *
from ..model.CtApplicationStatus import *
from ..model.CtDecision import *
from ..model.DatabaseHelper import *
from ..utils.PluginUtils import PluginUtils
from ..model.ApplicationPastureSearch import *
from ..model.ContractSearch import *
from ..model.BsPerson import *
from ..model.ClDecisionLevel import *
from ..model.ClDecision import *
from ..model.ClCountryList import *
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.AuLevel3 import *
from ..model.SetTaxAndPriceZone import *
from ..model.SetBaseTaxAndPrice import *
from ..model.CtApplicationPersonRole import *
from ..model import ConstantsPasture
from ..model.EnumerationsPasture import ApplicationType, UserRight
from ..model.CtApplicationPUGParcel import *
from ..model.CtApplicationParcelPasture import *
from ..model.CtApplicationPUG import *
from ..model.CaPastureParcel import *
from ..model.ClPastureType import *
from ..model.CtGroupMember import *
from ..model.CtPersonGroup import *
from ..utils.DatabaseUtils import *
from .DecisionErrorDialog import DecisionErrorDialog
from .qt_classes.ComboBoxDelegate import *
from .qt_classes.DropLabel import DropLabel
from .qt_classes.IntegerSpinBoxDelegate import *
from .qt_classes.ObjectAppDocumentDelegate import ObjectAppDocumentDelegate
from .qt_classes.ContractDocumentDelegate import ContractDocumentDelegate
from docxtpl import DocxTemplate, RichText

class SentToGovernorPastureDialog(QDialog, Ui_SentToGovernorPastureDialog, DatabaseHelper):

    def __init__(self,attribute_update, parent=None):

        super(SentToGovernorPastureDialog, self).__init__(parent)
        DatabaseHelper.__init__(self)
        self.setupUi(self)

        self.setWindowTitle(self.tr("Sent and prepare governor decision Dialog"))
        self.session = SessionHandler().session_instance()
        self.attribute_update = attribute_update
        self.error_list = {}
        self.timer = None
        user = DatabaseUtils.current_user()
        self.original_pa_from = user.pa_from
        self.__setup_validators()
        self.__app_status_count()
        self.close_button.clicked.connect(self.reject)
        self.__setup_combo_boxes()
        self.__setup_tree_widget()
        self.__setup_treewidget(self.draft_detail_twidget)
        self.begin_date.setDateTime(QDateTime().currentDateTime())

        begin_qt_date = self.begin_date.date().toString(ConstantsPasture.DATABASE_DATE_FORMAT)
        p_begin_date = datetime.strptime(str(begin_qt_date), ConstantsPasture.PYTHON_DATE_FORMAT)
        p_begin_date = p_begin_date  - timedelta(days=1)
        self.begin_date.setDateTime(p_begin_date)

        self.end_date.setDateTime(QDateTime().currentDateTime())
        self.draft_date.setDateTime(QDateTime().currentDateTime())
        self.decision_date.setDateTime(QDateTime().currentDateTime())
        self.__set_up_draft_detail_twidget()
        self.select_app_count.setText(str(0)+'/')
        self.tabWidget.currentChanged.connect(self.onChangetab)
        self.is_tmp_parcel = False
        self.app_no = None
        self.tab_index = 0

    def __setup_validators(self):

        self.int_validator = QRegExpValidator(QRegExp("[0-9]+"), None)
        self.draft_no_edit.setValidator(self.int_validator)

    def __setup_twidget(self, table_widget):

        table_widget.setAlternatingRowColors(True)
        table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        table_widget.setSelectionMode(QTableWidget.SingleSelection)

    def __setup_tree_widget(self):

        self.item_approved = QTreeWidgetItem()
        self.item_approved.setText(0, self.tr("Approved"))
        self.item_approved.setData(0, Qt.UserRole, ConstantsPasture.DECISION_RESULT_REFUSED)

        self.item_refused = QTreeWidgetItem()
        self.item_refused.setText(0, self.tr("Refused"))
        self.item_refused.setData(0, Qt.UserRole, ConstantsPasture.DECISION_RESULT_REFUSED)

        self.item_skipped = QTreeWidgetItem()
        self.item_skipped.setText(0, self.tr("Skipped"))
        self.item_skipped.setData(0, Qt.UserRole, -1)

        self.result_tree_widget.addTopLevelItem(self.item_approved)
        self.result_tree_widget.addTopLevelItem(self.item_refused)
        self.result_tree_widget.addTopLevelItem(self.item_skipped)

    def __setup_treewidget(self, tree_widget):

        header_labels = [self.tr("Group name"),
                  self.tr("Surname/Company name"),
                  self.tr("First name"),
                  self.tr("Person ID"),
                  self.tr("Application No"),
                  self.tr("Decision No"),
                  self.tr("Decision Date"),
                  self.tr("Decision Level"),
                  self.tr("Decision Result"),
                  self.tr("Duration")]

        tree_widget.setDragEnabled(True)
        tree_widget.setDragDropMode(QAbstractItemView.InternalMove)
        tree_widget.setColumnCount(len(header_labels))
        tree_widget.setHeaderLabels(header_labels)

        for i in range(tree_widget.columnCount()):
            tree_widget.headerItem().setTextAlignment(i, Qt.AlignHCenter)
            tree_widget.header().setResizeMode(QHeaderView.ResizeToContents)

    def __set_up_draft_detail_twidget(self):

        self.drafts_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.drafts_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.drafts_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.drafts_twidget.setSortingEnabled(True)

    def __app_status_count(self):

        app_count = ""
        try:
            app_count = self.session.query(CtApplicationStatus.application, func.max(CtApplicationStatus.status_date))\
                .group_by(CtApplicationStatus.application)\
                .having(func.max(CtApplicationStatus.status) == ConstantsPasture.APP_STATUS_WAITING).distinct().count()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self.iface.mainWindow(), QApplication.translate("Plugin", "Error executing"), e.message)

        self.app_count_lbl.setText(str(app_count))

    def __setup_combo_boxes(self):

        soum_code = ''
        au_level2 = DatabaseUtils.current_working_soum_schema()
        soum_code = str(au_level2)[3:]

        database_name = QSettings().value(SettingsConstants.DATABASE_NAME)
        user_code = database_name.split('_')[1]
        user_start = 'user' + user_code

        try:
            user = DatabaseUtils.current_user()
            officers = self.session.query(SetRole) \
                .filter(SetRole.user_name == user.user_name) \
                .filter(SetRole.is_active == True).one()

            application_types = self.session.query(ClApplicationType).\
                filter(or_(ClApplicationType.code == ApplicationType.legitimate_rights, ClApplicationType.code == ApplicationType.pasture_use)).all()

            set_roles = self.session.query(SetRole). \
                filter(SetRole.user_name.startswith(user_start)).all()
            set_role = self.session.query(SetRole).filter(SetRole.user_name_real == officers.user_name_real).one()
            aimag_code = set_role.working_au_level1
            aimag_code = aimag_code[:2]
        except SQLAlchemyError, e:
            PluginUtils.show_error(self.iface.mainWindow(), QApplication.translate("Plugin", "Error executing"), e.message)

        self.officer_cbox.addItem("*", -1)
        try:
            for item in application_types:
                self.app_type_cbox.addItem(item.description, item.code)
            if aimag_code == '01' or aimag_code == '12':
                decision_level = self.session.query(ClDecisionLevel).filter(or_(ClDecisionLevel.code == 10, ClDecisionLevel.code == 20)).all()
                for item in decision_level:
                    self.decision_level_cbox.addItem(item.description, item.code)
            else:
                if soum_code == '01':
                    decision_level = self.session.query(ClDecisionLevel).filter(or_(ClDecisionLevel.code == 30, ClDecisionLevel.code == 40)).all()
                    for item in decision_level:
                        self.decision_level_cbox.addItem(item.description, item.code)
                    # self.decision_level_cbox.setCurrentIndex(2)
                else:
                    decision_level = self.session.query(ClDecisionLevel).filter(ClDecisionLevel.code == 40).all()
                    for item in decision_level:
                        self.decision_level_cbox.addItem(item.description, item.code)
                    # self.decision_level_cbox.setCurrentIndex(3)

            if set_roles is not None:
                for role in set_roles:
                    self.officer_cbox.addItem(role.surname + ", " + role.first_name, role)
        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            raise LM2Exception(self.tr("Database Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))


    def __remove_application_items(self):

        self.draft_detail_twidget.setRowCount(0)

    @pyqtSlot()
    def on_search_button_clicked(self):

        self.draft_no_edit.setText('')
        self.draft_detail_twidget.clear()
        begin_qt_date = self.begin_date.date().toString(ConstantsPasture.DATABASE_DATE_FORMAT)
        p_begin_date = datetime.strptime(str(begin_qt_date), ConstantsPasture.PYTHON_DATE_FORMAT)

        end_qt_date = self.end_date.date().toString(ConstantsPasture.DATABASE_DATE_FORMAT)
        p_end_date = datetime.strptime(str(end_qt_date), ConstantsPasture.PYTHON_DATE_FORMAT)
        p_end_date = p_end_date  + timedelta(days=1)

        application_type = self.app_type_cbox.itemData(self.app_type_cbox.currentIndex())
        try:
            applications = self.session.query(ApplicationPastureSearch)
            sub = self.session.query(ApplicationPastureSearch, func.row_number().over(partition_by = ApplicationPastureSearch.app_no, order_by = (desc(ApplicationPastureSearch.status_date), desc(ApplicationPastureSearch.status))).label("row_number")).subquery()
            applications = applications.select_entity_from(sub).filter(sub.c.row_number == 1)
            status = 5

            applications = applications.filter(ApplicationPastureSearch.status == status)
            if not self.officer_cbox.itemData(self.officer_cbox.currentIndex()) == -1:
                officer = "%" + self.officer_cbox.itemData(self.officer_cbox.currentIndex()).user_name_real + "%"

                applications = applications.filter(ApplicationPastureSearch.next_officer_in_charge.ilike(officer))

        except SQLAlchemyError, e:
            PluginUtils.show_error(self.iface.mainWindow(), QApplication.translate("Plugin", "Error executing"), e.message)

        # self.__remove_application_items()
        count = 0

        for app in applications:

            application = app.app_no

            application_instance = self.session.query(CtApplication).filter(CtApplication.app_no == application).one()

            if int(application[6:-9]) == (self.app_type_cbox.itemData(self.app_type_cbox.currentIndex())) and application_instance.app_timestamp >= p_begin_date and application_instance.app_timestamp <= p_end_date:

                app_person = self.session.query(CtApplicationPersonRole).filter(CtApplicationPersonRole.application == application).\
                    filter(CtApplicationPersonRole.role == 70).count()
                if app_person > 0:
                    app_person = self.session.query(CtApplicationPersonRole).filter(
                        CtApplicationPersonRole.application == application).filter(CtApplicationPersonRole.role == 70).all()
                else:
                    app_person = self.session.query(CtApplicationPersonRole).filter(
                        CtApplicationPersonRole.application == application).all()
                parcel_count = self.session.query(CtApplicationPUGParcel).filter(CtApplicationPUGParcel.application == application_instance.app_no).count()
                if parcel_count == 0:
                    PluginUtils.show_message(self, self.tr("parcel none"), self.tr("None Parcel!!!"))
                    return

                for p in app_person:
                    if p.main_applicant == True:
                        person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()
                app_pug = self.session.query(CtApplicationPUG).filter(CtApplicationPUG.application == application_instance.app_no).all()
                group_name = u'Бүлэгт хамаарахгүй'
                group_no = None
                for app_group in app_pug:
                    group_member_count = self.session.query(CtGroupMember).filter(CtGroupMember.group_no == app_group.group_no).\
                        filter(CtGroupMember.person == person.person_id).count()
                    if group_member_count == 1:
                        group = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == app_group.group_no).one()
                        group_name = group.group_name
                        group_no = group.group_no
                decision_result = self.session.query(ClDecision).filter(ClDecision.code == 20).one()
                decision_level = self.decision_level_cbox.itemText(self.decision_level_cbox.currentIndex())
                decision_res = decision_result.description
                duration = str(application_instance.requested_duration)
                app_info = [group_name,person.name, person.first_name,person.person_id,application_instance.app_no, \
                            self.draft_no_edit.text(),self.draft_date.text(),decision_level,decision_res,duration]
                app_item = QTreeWidgetItem(app_info)
                # app_item.setText(0, group_name)
                app_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2_pasture/group.png")))
                app_item.setData(0, Qt.UserRole, person.person_id)
                app_item.setData(0, Qt.UserRole + 1, application_instance.app_no)
                app_item.setData(0, Qt.UserRole + 2, group_no)

                self.draft_detail_twidget.addTopLevelItem(app_item)
                spin = QSpinBox()
                spin.setValue(int(duration))
                self.draft_detail_twidget.setItemWidget(app_item, 9, spin)

                app_parcels = self.session.query(CtApplicationPUGParcel).\
                    filter(CtApplicationPUGParcel.application == application_instance.app_no).all()
                for app_parcel in app_parcels:
                    parcel = self.session.query(CaPastureParcel).filter(CaPastureParcel.parcel_id == app_parcel.parcel).one()

                    pasture_type_list = ''
                    parcel_pastures = self.session.query(CtApplicationParcelPasture).filter(
                        CtApplicationParcelPasture.parcel == app_parcel.parcel).all()
                    for pastures in parcel_pastures:
                        pasture = self.session.query(ClPastureType).filter(ClPastureType.code == pastures.pasture).one()
                        pasture_text = pasture.description
                        if pasture_type_list == '':
                            pasture_type_list = pasture_text
                        else:
                            pasture_type_list = pasture_type_list + '-' + pasture_text

                    address = ''
                    if parcel.address_neighbourhood:
                        address = parcel.address_neighbourhood
                    parcel_desc = parcel.parcel_id +' | '+ pasture_type_list +' | '+ str(parcel.area_ga) + ' | '+ address
                    parcel_info = [parcel_desc]
                    parcel_item = QTreeWidgetItem(parcel_info)
                    parcel_item.setBackgroundColor(0, QColor('#FFB6C1'))
                    parcel_item.setBackgroundColor(1, QColor('#FFB6C1'))
                    parcel_item.setBackgroundColor(2, QColor('#FFB6C1'))
                    parcel_item.setBackgroundColor(3, QColor('#FFB6C1'))
                    parcel_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2/parcel.png")))
                    parcel_item.setData(0, Qt.UserRole, parcel.parcel_id)
                    parcel_item.setData(0, Qt.UserRole + 1, application_instance.app_no)
                    app_item.addChild(parcel_item)
                    self.draft_detail_twidget.setFirstItemColumnSpanned(parcel_item,True)
            count =+ 1
        self.select_app_count.setText(str(count) + '/')
        if count != 0:
            self.sent_to_governor_button.setEnabled(True)
        else:
            self.sent_to_governor_button.setEnabled(False)

    def __drafts_twidget(self):

        if self.drafts_edit.text() == "":
            PluginUtils.show_message(self,self.tr("no dir"),self.tr("no dir"))
            return
        self.drafts_twidget.setRowCount(0)
        count = 0
        for file in os.listdir(self.drafts_edit.text()):
            if file.endswith(".xlsx") and str(file)[:5] == "draft":
                item_name = QTableWidgetItem(str(file))
                item_name.setData(Qt.UserRole,file)

                self.drafts_twidget.insertRow(count)
                self.drafts_twidget.setItem(count,0,item_name)
                count +=1
    @pyqtSlot()
    def on_drafts_path_button_clicked(self):

        default_path = r'D:/TM_LM2/Pasture/decision_draft'
        default_parent_path = r'D:/TM_LM2/Pasture'
        if not os.path.exists(default_parent_path):
            os.makedirs('D:/TM_LM2/Pasture')
            os.makedirs('D:/TM_LM2/Pasture/application_response')
            os.makedirs('D:/TM_LM2/Pasture/application_list')
            os.makedirs('D:/TM_LM2/Pasture/approved_decision')
            os.makedirs('D:/TM_LM2/Pasture/cad_maps')
            os.makedirs('D:/TM_LM2/Pasture/contracts')
            os.makedirs('D:/TM_LM2/Pasture/decision_draft')

        if not os.path.exists(default_path):
            os.makedirs(default_path)
        workbook = xlsxwriter.Workbook(default_path+'/'+'default.xlsx')
        worksheet = workbook.add_worksheet()
        file_dialog = QFileDialog()
        file_dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        file_dialog.setModal(True)
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setDirectory(default_path)
        if file_dialog.exec_():

            selected_file = file_dialog.selectedFiles()[0]
            file_path = QFileInfo(selected_file).path()
            file_name = QFileInfo(selected_file).fileName()
            self.drafts_edit.setText(file_path)
            self.__drafts_twidget()
            self.__drafts_twidget_2()

    @pyqtSlot()
    def on_sent_to_governor_button_clicked(self):

        row_num = self.drafts_twidget.rowCount()

        for row in range(row_num):
            item = self.drafts_twidget.item(row, 0)
            draft_id = item.data(Qt.UserRole)
            draft_id = draft_id[15:-5]
            if draft_id == self.draft_no_edit.text():
                PluginUtils.show_message(self, self.tr("File operation"), self.tr("Duplicated draft number!!!."))
                return
        root = self.draft_detail_twidget.invisibleRootItem()
        select_app_count = root.childCount()
        if select_app_count == 0:
            PluginUtils.show_message(self, self.tr("draft info"), self.tr("No select application!!!"))
            return

        if self.draft_no_edit.text() == "":
            PluginUtils.show_message(self, self.tr("draft info"), self.tr("None Decision Draft No!!!"))
            return
        if self.drafts_edit.text() == "":
            PluginUtils.show_message(self, self.tr("draft info"), self.tr("None Decision Draft Path No!!!"))
            return
        app_count = ""
        begin_qt_date = self.begin_date.date().toString(ConstantsPasture.DATABASE_DATE_FORMAT)
        p_begin_date = datetime.strptime(str(begin_qt_date), ConstantsPasture.PYTHON_DATE_FORMAT)

        end_qt_date = self.end_date.date().toString(ConstantsPasture.DATABASE_DATE_FORMAT)
        p_end_date = datetime.strptime(str(end_qt_date), ConstantsPasture.PYTHON_DATE_FORMAT)
        p_end_date = p_end_date  + timedelta(days=1)
        try:
            applications = self.session.query(ApplicationPastureSearch)

            sub = self.session.query(ApplicationPastureSearch, func.row_number().over(partition_by = ApplicationPastureSearch.app_no, order_by = (desc(ApplicationPastureSearch.status_date), desc(ApplicationPastureSearch.status))).label("row_number")).subquery()
            applications = applications.select_entity_from(sub).filter(sub.c.row_number == 1)
            status = 5

            applications = applications.filter(ApplicationPastureSearch.status == status)
            if not self.officer_cbox.itemData(self.officer_cbox.currentIndex()) == -1:
                officer = "%" + self.officer_cbox.itemData(self.officer_cbox.currentIndex()).user_name_real + "%"

                applications = applications.filter(ApplicationPastureSearch.officer_in_charge.ilike(officer))

            stati = self.session.query(CtApplicationStatus.application, func.max(CtApplicationStatus.status_date))\
                .group_by(CtApplicationStatus.application)\
                .having(func.max(CtApplicationStatus.status) == ConstantsPasture.APP_STATUS_WAITING).distinct()

        except SQLAlchemyError, e:
            PluginUtils.show_error(self.iface.mainWindow(), QApplication.translate("Plugin", "Error executing"), e.message)
        au_level2 = DatabaseUtils.current_working_soum_schema()

        current_user = DatabaseUtils.current_user()
        year_filter = str(QDate().currentDate().toString("yyyy"))
        month_filter = str(QDate().currentDate().toString("MM"))
        day_filter = str(QDate().currentDate().toString("dd"))

        file_name = 'draft_'+ year_filter + month_filter + day_filter + '_' + self.draft_no_edit.text()+'.xlsx'
        workbook = xlsxwriter.Workbook(self.drafts_edit.text()+'/'+file_name)
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 18)
        worksheet.set_column('E:E', 18)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 12)
        worksheet.set_column('H:H', 25)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('J:J', 22)

        bold = workbook.add_format({'bold': True})
        bold.set_bg_color('#C0C0C0')

        worksheet.write('A1', u"Бүлгийн нэр", bold)
        worksheet.write('B1',u"Овог", bold)
        worksheet.write('C1',u"Нэр", bold)
        worksheet.write('D1',u"Регистрийн дугаар", bold)
        worksheet.write('E1',u"Өргөдлийн дугаар", bold)
        worksheet.write('F1',u"Төсөлийн дугаар", bold)
        worksheet.write('G1',u"Огноо", bold)
        worksheet.write('H1',u"Захирамжийн түвшин", bold)
        worksheet.write('I1',u"Төлөв", bold)
        worksheet.write('J1',u"Хүсэлт гаргасан хугацаа", bold)
        row = 1
        col = 0
        app_no_without_parcel = []
        root = self.draft_detail_twidget.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):
            item = root.child(i)
            application = item.data(0, Qt.UserRole+1)

            application_instance = self.session.query(CtApplication).filter(CtApplication.app_no == application).one()
            app_person = self.session.query(CtApplicationPersonRole).filter(
                CtApplicationPersonRole.application == application). \
                filter(CtApplicationPersonRole.role == 70).count()
            if app_person > 0:
                app_person = self.session.query(CtApplicationPersonRole).filter(
                    CtApplicationPersonRole.application == application).filter(CtApplicationPersonRole.role == 70).all()
            else:
                app_person = self.session.query(CtApplicationPersonRole).filter(
                    CtApplicationPersonRole.application == application).all()
            landuse_type = self.session.query(ClLanduseType).filter(ClLanduseType.code == application_instance.requested_landuse).one()
            for p in app_person:
                if p.main_applicant == True:
                    person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()
            if person.type == 10 or person.type == 20 or person == 50:
                first_name = person.first_name
            else:
                first_name = u"ААН"

            app_pug = self.session.query(CtApplicationPUG).filter(
                CtApplicationPUG.application == application).all()
            group_name = u'Бүлэгт хамаарахгүй'
            group_no = None
            for app_group in app_pug:
                group_member_count = self.session.query(CtGroupMember).filter(
                    CtGroupMember.group_no == app_group.group_no). \
                    filter(CtGroupMember.person == person.person_id).count()
                if group_member_count == 1:
                    group = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == app_group.group_no).one()
                    group_name = group.group_name
                    group_no = group.group_no

            decision_result = self.session.query(ClDecision).filter(ClDecision.code == 20).one()

            format0 = workbook.add_format()
            format0.set_border(style=1)

            worksheet.write(row, col, group_name,format0)
            worksheet.write(row, col+1,person.name,format0)
            worksheet.write(row, col+2,first_name,format0)
            worksheet.write(row, col+3,person.person_id,format0)
            worksheet.write(row, col+4,application,format0)
            worksheet.write(row, col+5,self.draft_no_edit.text(),format0)
            worksheet.write(row, col+6,self.draft_date.text(),format0)
            worksheet.write(row, col+7,self.decision_level_cbox.itemText(self.decision_level_cbox.currentIndex()),format0)
            worksheet.write(row, col+8,decision_result.description,format0)
            worksheet.write(row, col+9,str(application_instance.requested_duration),format0)

            app_parcels = self.session.query(CtApplicationPUGParcel). \
                filter(CtApplicationPUGParcel.application == application_instance.app_no).all()
            for app_parcel in app_parcels:
                parcel = self.session.query(CaPastureParcel).filter(
                    CaPastureParcel.parcel_id == app_parcel.parcel).one()
                pasture_type_list = ''
                parcel_pastures = self.session.query(CtApplicationParcelPasture).filter(
                    CtApplicationParcelPasture.parcel == app_parcel.parcel).all()
                for pastures in parcel_pastures:
                    pasture = self.session.query(ClPastureType).filter(ClPastureType.code == pastures.pasture).one()
                    pasture_text = pasture.description
                    if pasture_type_list == '':
                        pasture_type_list = pasture_text
                    else:
                        pasture_type_list = pasture_type_list + '-' + pasture_text
                address = ''
                if parcel.address_neighbourhood:
                    address = parcel.address_neighbourhood
                parcel_desc = parcel.parcel_id + ' | ' + pasture_type_list + ' | ' + str(
                    parcel.area_ga) + ' | ' + address
                row += 1
                format1 = workbook.add_format({'bg_color': '#FFC7CE',
                                               'font_color': '#9C0006'})
                format1.set_border(style=1)
                worksheet.merge_range(row, col + 1, row, col+9, parcel_desc,format1)

            user = DatabaseUtils.current_user()
            officers = self.session.query(SetRole) \
                .filter(SetRole.user_name == user.user_name) \
                .filter(SetRole.is_active == True).one()

            new_status = CtApplicationStatus()
            new_status.application = application
            new_status.next_officer_in_charge = officers.user_name_real
            new_status.officer_in_charge = officers.user_name_real
            new_status.status = ConstantsPasture.APP_STATUS_SEND
            new_status.status_date = datetime.now().strftime(ConstantsPasture.PYTHON_DATE_FORMAT)
            self.session.add(new_status)
            row += 1

        self.session.commit()

        if len(app_no_without_parcel) > 0:
            app_no_string = ", ".join(app_no_without_parcel)
            QMessageBox.information(None, QApplication.translate("LM2", "Mark Applications"),
                                        QApplication.translate("LM2", "The following applications have no parcels assigned and could not be updated: {0} ".format(app_no_string)))

        workbook.close()
        self.__drafts_twidget()
        self.__drafts_twidget_2()
        self.draft_detail_twidget.clear()
        self.__app_status_count()
        QMessageBox.information(self,self.tr("Sent To Governor"), self.tr("Successful"))
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.drafts_edit.text()+file_name))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    @pyqtSlot(QTableWidgetItem)
    def on_drafts_twidget_itemClicked(self, item):

        self.sent_to_governor_button.setDisabled(True)

        current_row = self.drafts_twidget.currentRow()
        item = self.drafts_twidget.item(current_row,0)
        draft_id = item.data(Qt.UserRole)
        file_name = self.drafts_edit.text() + '/' +draft_id

        self.__read_xls_file(file_name)

        self.draft_no_edit.setText(draft_id[15:-5])

    def __read_xls_file(self, file_name):

        if file_name == "":
            PluginUtils.show_message(self, self.tr("File operation"), self.tr("Please select a file."))
            return

        if not QFileInfo(file_name).exists():
            PluginUtils.show_message(self, self.tr("File operation"), self.tr("Invalid file."))
            return

        workbook = open_workbook(file_name)
        worksheet = workbook.sheet_by_name('Sheet1')
        self.draft_detail_twidget.clear()
        count = 0

        for curr_row in range(worksheet.nrows-1):
            curr_row = curr_row + 1
            app_no = worksheet.cell_value(curr_row, 4)
            if len(app_no) == 17:
                self.app_no = app_no

                applications = self.session.query(ApplicationPastureSearch)
                sub = self.session.query(ApplicationPastureSearch,
                                         func.row_number().over(partition_by=ApplicationPastureSearch.app_no, order_by=(
                                         desc(ApplicationPastureSearch.status_date),
                                         desc(ApplicationPastureSearch.status))).label("row_number")).subquery()
                applications = applications.select_entity_from(sub).filter(sub.c.row_number == 1)

                application_count = self.session.query(CtApplication).\
                    filter(or_(CtApplication.app_type == ApplicationType.legitimate_rights, CtApplication.app_type == ApplicationType.pasture_use)).\
                    filter(CtApplication.app_no == str(self.app_no)).count()

                if application_count == 1:
                    application = self.session.query(CtApplication). \
                        filter(or_(CtApplication.app_type == ApplicationType.legitimate_rights,
                                   CtApplication.app_type == ApplicationType.pasture_use)). \
                        filter(CtApplication.app_no == self.app_no).one()

                    app_person = self.session.query(CtApplicationPersonRole).filter(
                        CtApplicationPersonRole.application == self.app_no).all()
                    parcel_count = self.session.query(CtApplicationPUGParcel).filter(
                        CtApplicationPUGParcel.application == self.app_no).count()
                    if parcel_count == 0:
                        PluginUtils.show_message(self, self.tr("parcel none"), self.tr("None Parcel!!!"))
                        return

                    for p in app_person:
                        if p.main_applicant == True:
                            person = self.session.query(BsPerson).filter(BsPerson.person_id == p.person).one()
                    app_pug = self.session.query(CtApplicationPUG).filter(
                        CtApplicationPUG.application == self.app_no).all()
                    group_name = u'Бүлэгт хамаарахгүй'
                    group_no = None
                    for app_group in app_pug:
                        group_member_count = self.session.query(CtGroupMember).filter(
                            CtGroupMember.group_no == app_group.group_no). \
                            filter(CtGroupMember.person == person.person_id).count()
                        if group_member_count == 1:
                            group = self.session.query(CtPersonGroup).filter(CtPersonGroup.group_no == app_group.group_no).one()
                            group_name = group.group_name
                            group_no = group.group_no
                    decision_result = self.session.query(ClDecision).filter(ClDecision.code == 20).one()
                    decision_level = self.decision_level_cbox.itemText(self.decision_level_cbox.currentIndex())
                    decision_res = decision_result.description
                    duration = str(application.requested_duration)
                    app_info = [group_name, person.name, person.first_name, person.person_id, application.app_no, \
                                self.draft_no_edit.text(), self.draft_date.text(), decision_level, decision_res, duration]
                    app_item = QTreeWidgetItem(app_info)
                    # app_item.setText(0, group_name)
                    app_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2_pasture/group.png")))
                    app_item.setData(0, Qt.UserRole, person.person_id)
                    app_item.setData(0, Qt.UserRole + 1, application.app_no)
                    app_item.setData(0, Qt.UserRole + 2, group_no)

                    self.draft_detail_twidget.addTopLevelItem(app_item)
                    if self.tab_index == 1:
                        decision_results = self.session.query(ClDecision).all()
                        combobox = QComboBox()
                        for res in decision_results:
                            combobox.addItem(res.description, res.code)
                        self.draft_detail_twidget.setItemWidget(app_item, 8, combobox)
                        app_item.setText(8, combobox.currentText())
                        spin = QSpinBox()
                        spin.setValue(int(duration))
                        self.draft_detail_twidget.setItemWidget(app_item, 9, spin)
                        app_item.setText(9, str(spin.value()))

                    app_parcels = self.session.query(CtApplicationPUGParcel). \
                        filter(CtApplicationPUGParcel.application == self.app_no).all()
                    for app_parcel in app_parcels:
                        parcel = self.session.query(CaPastureParcel).filter(
                            CaPastureParcel.parcel_id == app_parcel.parcel).one()
                        pasture_type_list = ''
                        parcel_pastures = self.session.query(CtApplicationParcelPasture).filter(
                            CtApplicationParcelPasture.parcel == app_parcel.parcel).all()
                        for pastures in parcel_pastures:
                            pasture = self.session.query(ClPastureType).filter(
                                ClPastureType.code == pastures.pasture).one()
                            pasture_text = pasture.description
                            if pasture_type_list == '':
                                pasture_type_list = pasture_text
                            else:
                                pasture_type_list = pasture_type_list + '-' + pasture_text
                        address = ''
                        if parcel.address_neighbourhood:
                            address = parcel.address_neighbourhood
                        parcel_desc = parcel.parcel_id + ' | ' + pasture_type_list + ' | ' + str(
                            parcel.area_ga) + ' | ' + address
                        parcel_info = [parcel_desc]
                        parcel_item = QTreeWidgetItem(parcel_info)
                        parcel_item.setBackgroundColor(0, QColor('#FFB6C1'))
                        parcel_item.setBackgroundColor(1, QColor('#FFB6C1'))
                        parcel_item.setBackgroundColor(2, QColor('#FFB6C1'))
                        parcel_item.setBackgroundColor(3, QColor('#FFB6C1'))
                        parcel_item.setIcon(0, QIcon(QPixmap(":/plugins/lm2/parcel.png")))
                        parcel_item.setData(0, Qt.UserRole, parcel.parcel_id)
                        parcel_item.setData(0, Qt.UserRole + 1, self.app_no)
                        app_item.addChild(parcel_item)
                        self.draft_detail_twidget.setFirstItemColumnSpanned(parcel_item, True)

            count += 1

    @pyqtSlot()
    def on_doc_print_button_clicked(self):

        root = self.draft_detail_twidget.invisibleRootItem()
        select_app_count = root.childCount()
        if select_app_count == 0:
            PluginUtils.show_message(self,self.tr("List None"),self.tr("Draft list null!!!"))
            return
        if self.drafts_twidget.rowCount() == 0:
            PluginUtils.show_message(self,self.tr("List None"),self.tr("Drafts list null!!!"))
            return
        if self.draft_no_edit.text() == "":
            PluginUtils.show_message(self,self.tr("Draft No None"),self.tr("Draft No null!!!"))
            return

        select_item = self.drafts_twidget.selectedItems()
        name_item = select_item[0]
        file_name = name_item.data(Qt.UserRole)

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to print for draft doc of governor decision"))

        yes_button = message_box.addButton(self.tr("Yes"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("No"), QMessageBox.ActionRole)
        message_box.exec_()

        if message_box.clickedButton() == yes_button:
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.drafts_edit.text()+"/"+file_name))
            except IOError, e:
                PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    @pyqtSlot()
    def on_change_button_clicked(self):

        if len(self.drafts_twidget_2.selectedItems()) == 0:
            PluginUtils.show_message(self, self.tr("Draft path"), self.tr("Select draft list!"))
            return
        if len(self.drafts_twidget_2.selectedItems()) > 1:
            PluginUtils.show_message(self, self.tr("Draft path"), self.tr("2 tusul songoh bolomjhui"))
            return

        if self.drafts_edit.text() == "":
            PluginUtils.show_message(self, self.tr("Draft path"), self.tr("Choose the draft path first!"))
            return

        root = self.draft_detail_twidget.invisibleRootItem()
        select_app_count = root.childCount()
        if select_app_count == 0:
            PluginUtils.show_message(self, self.tr("Decision list"), self.tr("Application list is empty. Choose the draft decision!"))
            return

        if self.decision_number_edit.text() == "":
            PluginUtils.show_message(self, self.tr("Decision No"), self.tr("Please enter decision number!"))
            return
        au_level2 = DatabaseUtils.current_working_soum_schema()
        year_filter = str(QDate().currentDate().toString("yyyy"))

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to insert the decision number?"))

        yes_button = message_box.addButton(self.tr("Yes"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("No"), QMessageBox.ActionRole)
        message_box.exec_()

        root = self.draft_detail_twidget.invisibleRootItem()
        select_app_count = root.childCount()
        decision_no = au_level2 + '-' + self.decision_number_edit.text() + '/' + year_filter
        if message_box.clickedButton() == yes_button:
            for i in range(select_app_count):
                item = self.draft_detail_twidget.topLevelItem(i)
                item.setText(5, decision_no)
                item.setText(6, self.decision_date.text())


    @pyqtSlot()
    def on_decision_save_button_clicked(self):

        if self.decision_number_edit.text() == "" or self.decision_number_edit.text() == None:
            PluginUtils.show_message(self, self.tr("Decision No"), self.tr("Please enter decision number!"))
            return
        au_level2 = DatabaseUtils.current_working_soum_schema()
        year_filter = str(QDate().currentDate().toString("yyyy"))
        decision_no = 'decision_'+au_level2 + '_' + self.decision_number_edit.text() + '_' + year_filter
        path = QSettings().value(SettingsConstants.LAST_FILE_PATH, QDir.homePath())

        # default_path = path + QDir.separator()
        default_path = r'D:/TM_LM2/Pasture/approved_decision'
        default_parent_path = r'D:/TM_LM2/Pasture'
        if not os.path.exists(default_parent_path):
            os.makedirs('D:/TM_LM2/Pasture')
            os.makedirs('D:/TM_LM2/Pasture/application_response')
            os.makedirs('D:/TM_LM2/Pasture/application_list')
            os.makedirs('D:/TM_LM2/Pasture/approved_decision')
            os.makedirs('D:/TM_LM2/Pasture/cad_maps')
            os.makedirs('D:/TM_LM2/Pasture/contracts')
            os.makedirs('D:/TM_LM2/Pasture/decision_draft')
        if not os.path.exists(default_path):
            os.makedirs(default_path)

        file_dialog = QFileDialog(self, Qt.WindowStaysOnTopHint)
        file_dialog.setFilter('XLSX (*.xlsx)')
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setDirectory(default_path)
        file_dialog.selectFile(decision_no + ".xlsx")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            if file_path is None or type(file_path) == QPyNullVariant:
                return
            f_info = QFileInfo(file_path)

            QSettings().setValue(SettingsConstants.LAST_FILE_PATH, f_info.dir().path())

            self.decision_save_edit.setText(file_path)
        else:
            return

        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 18)
        worksheet.set_column('B:B', 18)
        worksheet.set_column('C:C', 18)
        worksheet.set_column('D:D', 18)
        worksheet.set_column('E:E', 18)
        worksheet.set_column('F:F', 18)
        worksheet.set_column('G:G', 20)

        bold = workbook.add_format({'bold': True})

        worksheet.write('A1',u"Өргөдлийн дугаар", bold)
        worksheet.write('B1',u"Захирамж дугаар", bold)
        worksheet.write('C1',u"Захирамж огноо", bold)
        worksheet.write('D1',u"Захирамж түвшин", bold)
        worksheet.write('E1',u"Захирамж гарсан эсэх", bold)
        worksheet.write('F1',u"Хугацаа", bold)
        worksheet.write('G1',u"Газар ашиглалтын зориулалт", bold)
        xrow = 1
        xcol = 0
        root = self.draft_detail_twidget.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):

            app_no = self.draft_detail_twidget.topLevelItem(i).text(4)
            decision_no = self.draft_detail_twidget.topLevelItem(i).text(5)
            decision_date = self.draft_detail_twidget.topLevelItem(i).text(6)

            approved_diratoin = self.draft_detail_twidget.topLevelItem(i).text(9)

            decision_level_desc = self.draft_detail_twidget.topLevelItem(i).text(7)
            decision_level = self.session.query(ClDecisionLevel). \
                filter(ClDecisionLevel.description == decision_level_desc).one()

            decision_result_desc = self.draft_detail_twidget.topLevelItem(i).text(8)

            decision_result = self.session.query(ClDecision). \
                filter(ClDecision.description == decision_result_desc).one()

            worksheet.write(xrow, xcol,app_no)
            worksheet.write(xrow, xcol+1,decision_no)
            worksheet.write(xrow, xcol+2,decision_date)
            worksheet.write(xrow, xcol+3,str(decision_level.code))
            worksheet.write(xrow, xcol+4,str(decision_result.code))
            worksheet.write(xrow, xcol+5,approved_diratoin)
            worksheet.write(xrow, xcol+6,'1101')
            xrow = xrow + 1

        workbook.close()
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))

    @pyqtSlot()
    def on_draft_print_button_clicked(self):

        root = self.draft_detail_twidget.invisibleRootItem()
        select_app_count = root.childCount()
        if select_app_count == 0:
            PluginUtils.show_message(self,self.tr("List None"),self.tr("Draft list null!!!"))
            return
        if self.draft_no_edit.text() == "":
            PluginUtils.show_message(self,self.tr("Draft No None"),self.tr("Draft No null!!!"))
            return
        au_level2 = DatabaseUtils.current_working_soum_schema()
        au_level1 = au_level2[:3]

        try:
            soum = self.session.query(AuLevel2).filter(AuLevel2.code == au_level2).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"),
                                   self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        path = os.path.join(os.path.dirname(__file__), "../view/map/pasture/")

        application = self.session.query(CtApplication). \
            filter(or_(CtApplication.app_type == ApplicationType.legitimate_rights,
                       CtApplication.app_type == ApplicationType.pasture_use)). \
            filter(CtApplication.app_no == self.app_no).one()

        if application.app_type == ApplicationType.pasture_use:
            tpl = DocxTemplate(path + 'draft_pasture.docx')
        elif application.app_type == ApplicationType.legitimate_rights:
            tpl = DocxTemplate(path + 'draft_rights.docx')
        else:
            tpl = DocxTemplate(path + 'draft_pasture.docx')

        user_name = QSettings().value(SettingsConstants.USER)

        try:
            user = self.session.query(SetRole).filter(SetRole.user_name == user_name).filter(SetRole.is_active == True).one()
        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"),
                                   self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        sum_officer = user.position_ref.name
        o_surname = user.surname
        o_firstname = user.first_name
        context = {
            'sum_officer': sum_officer,
            'o_surname': o_surname,
            'o_firstname': o_firstname
        }

        tpl.render(context)
        default_path = r'D:/TM_LM2/Pasture/approved_decision'

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to print for draft of governor decision"))

        yes_button = message_box.addButton(self.tr("Yes"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("No"), QMessageBox.ActionRole)
        message_box.exec_()
        if message_box.clickedButton() == yes_button:
            try:
                tpl.save(default_path + "/draft" + ".docx")
                QDesktopServices.openUrl(
                    QUrl.fromLocalFile(default_path + "/draft" + ".docx"))
            except IOError, e:
                PluginUtils.show_error(self, self.tr("Out error"),
                                       self.tr("This file is already opened. Please close re-run"))

    def __drafts_twidget_2(self):

        if self.drafts_edit.text() == "":
            PluginUtils.show_message(self,self.tr("no dir"),self.tr("no dir"))
            return
        self.drafts_twidget_2.setRowCount(0)
        count = 0
        for file in os.listdir(self.drafts_edit.text()):
            if file.endswith(".xlsx") and str(file)[:5] == "draft":
                item_name = QTableWidgetItem(str(file))
                item_name.setData(Qt.UserRole,file)

                self.drafts_twidget_2.insertRow(count)
                self.drafts_twidget_2.setItem(count,0,item_name)
                count +=1

    @pyqtSlot(QTableWidgetItem)
    def on_drafts_twidget_2_itemClicked(self, item):

        current_row = self.drafts_twidget_2.currentRow()
        item = self.drafts_twidget_2.item(current_row,0)
        draft_id = item.data(Qt.UserRole)
        file_name = self.drafts_edit.text() + '/' +draft_id

        self.__read_xls_file(file_name)

    def onChangetab(self, i):

        self.tab_index = i
        self.draft_detail_twidget.clear()

    @pyqtSlot(int)
    def on_app_type_cbox_currentIndexChanged(self, index):

        self.decision_level_cbox.clear()
        app_type = self.app_type_cbox.itemData(index)
        if app_type == 22:
            decision_level = self.session.query(ClDecisionLevel).filter(ClDecisionLevel.code == 80).all()
            for item in decision_level:
                self.decision_level_cbox.addItem(item.description, item.code)
        else:
            soum_code = ''
            au_level2 = DatabaseUtils.current_working_soum_schema()
            soum_code = str(au_level2)[3:]

            set_role = self.session.query(SetRole).filter(
                SetRole.user_name == DatabaseUtils.current_user().user_name).filter(SetRole.is_active == True).one()
            aimag_code = set_role.working_au_level1
            aimag_code = aimag_code[:2]
            if aimag_code == '01' or aimag_code == '12':
                decision_level = self.session.query(ClDecisionLevel).filter(
                    or_(ClDecisionLevel.code == 10, ClDecisionLevel.code == 20)).all()
                for item in decision_level:
                    self.decision_level_cbox.addItem(item.description, item.code)
            else:
                if soum_code == '01':
                    decision_level = self.session.query(ClDecisionLevel).filter(
                        or_(ClDecisionLevel.code == 30, ClDecisionLevel.code == 40)).all()
                    for item in decision_level:
                        self.decision_level_cbox.addItem(item.description, item.code)
                        # self.decision_level_cbox.setCurrentIndex(2)
                else:
                    decision_level = self.session.query(ClDecisionLevel).filter(ClDecisionLevel.code == 40).all()
                    for item in decision_level:
                        self.decision_level_cbox.addItem(item.description, item.code)
                        # self.decision_level_cbox.setCurrentIndex(3)

    @pyqtSlot()
    def on_select_file_button_clicked(self):

        default_path = r'D:/TM_LM2/Pasture/approved_decision'

        file_dialog = QFileDialog()
        file_dialog.setFilter(self.tr("Excel Files (*.xlsx)"))
        file_dialog.setModal(True)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setDirectory(default_path)
        if file_dialog.exec_():
            selected_file = file_dialog.selectedFiles()[0]
            file_name = QFileInfo(selected_file).filePath()
            self.decision_file_edit.setText(file_name)
            self.import_button.setEnabled(True)
            self.__read_import_xls_file()

    def __read_import_xls_file(self):

        file_name = self.decision_file_edit.text()
        if file_name == "":
            PluginUtils.show_message(self, self.tr("File operation"), self.tr("Please select a file."))
            return

        if not QFileInfo(file_name).exists():
            PluginUtils.show_message(self, self.tr("File operation"), self.tr("Invalid file."))
            return

        work_book = open_workbook(file_name)

        decision_no_column = -1
        decision_date_column = -1
        decision_level_column = -1
        decision_column = -1
        application_no_column = -1
        application_duration_column = -1
        landuse_column = -1

        for s in work_book.sheets():
            for row in range(1):
                for col in range(s.ncols):
                    if s.cell(row, col).value == ConstantsPasture.DECISION_COLUMN_NAME:
                        decision_column = col
                    elif s.cell(row, col).value == ConstantsPasture.DECISION_NO_COLUMN_NAME:
                        decision_no_column = col
                    elif s.cell(row, col).value == ConstantsPasture.DECISION_DATE_COLUMN_NAME:
                        decision_date_column = col
                    elif s.cell(row, col).value == ConstantsPasture.DECISION_LEVEL_COLUMN_NAME:
                        decision_level_column = col
                    elif s.cell(row, col).value == ConstantsPasture.APPLICATION_NO_COLUMN_NAME:
                        application_no_column = col
                    elif s.cell(row, col).value == ConstantsPasture.APPROVED_DURATION_COLUMN_NAME:
                        application_duration_column = col
                    elif s.cell(row, col).value == ConstantsPasture.LANDUSE_COLUMN_NAME:
                        landuse_column = col

        # check: if any column wasn't found -> exit
        if decision_no_column == -1 \
                or decision_date_column == -1 \
                or decision_level_column == -1 \
                or decision_column == -1 \
                or application_no_column == -1 \
                or landuse_column == -1 \
                or application_duration_column == -1:

            PluginUtils.show_message(self, self.tr("Error in Excel file"),
                                     self.tr(u"The Excel file doesn't contain the following columns: \n "
                                             u"{0}, {1}, {2}, {3}, {4}, {5}, {6}").format(ConstantsPasture.DECISION_COLUMN_NAME,
                                             ConstantsPasture.DECISION_NO_COLUMN_NAME, ConstantsPasture.DECISION_DATE_COLUMN_NAME,
                                             ConstantsPasture.APPLICATION_NO_COLUMN_NAME, ConstantsPasture.DECISION_LEVEL_COLUMN_NAME,
                                             ConstantsPasture.APPROVED_DURATION_COLUMN_NAME, ConstantsPasture.LANDUSE_COLUMN_NAME))

            self.error_list["Excel"] = self.tr(u"The Excel file doesn't contain the following columns: \n "
                                             u"{0}, {1}, {2}, {3}, {4}, {5}, {6}").format(ConstantsPasture.DECISION_COLUMN_NAME,
                                             ConstantsPasture.DECISION_NO_COLUMN_NAME, ConstantsPasture.DECISION_DATE_COLUMN_NAME,
                                             ConstantsPasture.APPLICATION_NO_COLUMN_NAME, ConstantsPasture.DECISION_LEVEL_COLUMN_NAME,
                                             ConstantsPasture.APPROVED_DURATION_COLUMN_NAME, ConstantsPasture.LANDUSE_COLUMN_NAME)

            return

        user = DatabaseUtils.current_user()
        current_employee = self.session.query(SetRole) \
            .filter(SetRole.user_name == user.user_name)\
            .filter(SetRole.is_active == True).one()
        self.import_by_edit.setText(current_employee.user_name_real)

        s = work_book.sheets()[0]

        self.create_savepoint()
        maintenance_cases = []

        try:
            first_date = str(s.cell(1, decision_date_column).value)
            decision_no = s.cell(1, decision_no_column).value
            decision_level = s.cell(1, decision_level_column).value

            if not self.__validate_decision_attributes(first_date, decision_no, decision_level):
                self.import_button.setEnabled(False)
                self.add_document_button.setEnabled(False)
                self.load_document_button.setEnabled(False)
                self.delete_document_button.setEnabled(False)
                self.view_document_button.setEnabled(False)

                return

            user = DatabaseUtils.current_user()
            current_employee = self.session.query(SetRole) \
                .filter(SetRole.user_name == user.user_name) \
                .filter(SetRole.is_active == True).one()

            self.decision = CtDecision()
            self.decision.decision_date = s.cell(1, decision_date_column).value
            self.decision.decision_no = s.cell(1, decision_no_column).value
            self.decision.decision_level = s.cell(1, decision_level_column).value
            self.decision.imported_by = current_employee.user_name_real

            self.decision_no_edit.setText(self.decision.decision_no)
            self.decision_date_edit.setText(str(self.decision.decision_date))
            self.level_cbox.setCurrentIndex(self.level_cbox.findData(self.decision.decision_level))

            for row in range(1, s.nrows):

                decision_result = s.cell(row, decision_column).value
                app_no = s.cell(row, application_no_column).value
                current_decision_no = s.cell(row, decision_no_column).value
                duration = s.cell(1, application_duration_column).value
                landuse = s.cell(row, landuse_column).value

                if not self.__validate_row(decision_result, app_no, current_decision_no, self.decision.decision_no,
                                           duration, landuse):
                    item = QTreeWidgetItem()
                    item.setText(0, app_no)
                    self.item_skipped.addChild(item)
                    self.import_button.setEnabled(False)
                    self.error_details_button.setEnabled(True)
                    continue

                decision_app = CtDecisionApplication()
                decision_app.decision_result = decision_result
                decision_app.application = app_no
                self.decision.results.append(decision_app)

                application = self.session.query(CtApplication).filter_by(app_no=app_no).one()
                application_result_exists = False
                application.approved_landuse = landuse

                if decision_app.decision_result == ConstantsPasture.DECISION_RESULT_APPROVED:
                    count = application.statuses\
                        .filter(CtApplicationStatus.status == ConstantsPasture.APP_STATUS_APPROVED).count()
                    if count > 0:
                        application_result_exists = True
                else:
                    count = application.statuses\
                        .filter(CtApplicationStatus.status == ConstantsPasture.APP_STATUS_REFUSED).count()
                    if count > 0:
                        application_result_exists = True

                if not application_result_exists:

                    app_status = CtApplicationStatus()
                    user = DatabaseUtils.current_user()
                    app_status.next_officer_in_charge = current_employee.user_name_real
                    app_status.officer_in_charge = current_employee.user_name_real
                    app_status.application = app_no
                    app_status.status_date = self.decision.decision_date

                    if decision_app.decision_result == ConstantsPasture.DECISION_RESULT_APPROVED or decision_app.decision_result == '10':
                        app_status.status = ConstantsPasture.APP_STATUS_APPROVED
                    else:
                        app_status.status = ConstantsPasture.APP_STATUS_REFUSED

                        #rollback: set date of parcel that isn't approved to NULL
                        #set valid_till of parcels back to infinity
                        application = self.session.query(CtApplication).get(app_no)
                        if application.maintenance_case not in maintenance_cases and application.maintenance_case is not None:
                            maintenance_cases.append(application.maintenance_case)

                    self.session.add(app_status)

                if application.app_type in ConstantsPasture.APPLICATION_TYPE_WITH_DURATION:
                    approved_duration = int(duration)
                    application.approved_duration = approved_duration

                item = QTreeWidgetItem()
                item.setText(0, decision_app.application)
                if int(decision_app.decision_result) == int(ConstantsPasture.DECISION_RESULT_APPROVED):
                    self.item_approved.addChild(item)
                else:
                    self.item_refused.addChild(item)

                self.session.add(self.decision)
                self.add_document_button.setEnabled(True)
                self.load_document_button.setEnabled(True)
                self.delete_document_button.setEnabled(True)
                self.view_document_button.setEnabled(True)
                self.select_file_button.setEnabled(False)

        except SQLAlchemyError, e:
            self.rollback_to_savepoint()
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Could not import xls file {0}: {1}").format(currentframe().f_lineno, e.message))
            return

    def __validate_decision_attributes(self, current_date_string, decision_no, decision_level):

        qt_date = QDate.fromString(current_date_string, ConstantsPasture.DATABASE_DATE_FORMAT)
        count = 0

        if not qt_date.isValid():
            self.rollback()
            PluginUtils.show_error(self, self.tr("Error in xls file"),
                                   self.tr("The date is not in the correct format. "
                                           "Expected yyyy-MM-dd and found: " + current_date_string))

            self.error_list[decision_no + " # " + str(count)] = self.tr("The date is not in the correct format. "
                                           "Expected yyyy-MM-dd and found: " + current_date_string)
            count += 1
            return False

        try:
            #check that the decision number contains a soum code
            soum_no = decision_no.split("-")[0]
            count = self.session.query(AuLevel2).filter(AuLevel2.code == soum_no).count()
            if count == 0:
                PluginUtils.show_error(self, self.tr("Error in xls file"), self.tr("The decision number {0} "
                                                                                   "contains an invalid soum code.")
                                                                                    .format(decision_no))
                self.error_list[decision_no + " # " + str(count)] = self.tr("The decision number {0} "
                                                                                   "contains an invalid soum code.").format(decision_no)
                count += 1
                return False
            else:
                DatabaseUtils.set_working_schema(soum_no)

            #check if decision_no already exists in case of a new import
            if not self.attribute_update:
                count = self.session.query(CtDecision).filter(CtDecision.decision_no == decision_no).count()
                if count > 0:
                    PluginUtils.show_error(self, self.tr("Error in xls file"),
                                                self.tr("The decision number {0} already exists in the database.")
                                                    .format(decision_no))
                    self.error_list[decision_no + " # " + str(count)] = self.tr("The decision number {0} already exists in the database.")
                    count += 1
                    return False

            #check if the decision level is in the codelist and of the type int
            try:
                int(decision_level)
            except ValueError:

                PluginUtils.show_error(self, self.tr("Error in xls file"),
                                            self.tr("The decision level code {0} is not of the type integer.")
                                            .format(decision_level))

                self.error_list[decision_no + " # " + str(count)] = self.tr("The decision level code {0} is not of the type integer.").format(decision_level)
                count += 1
                return False

            count = self.session.query(ClDecisionLevel).filter(ClDecisionLevel.code == decision_level).count()
            if count == 0:
                PluginUtils.show_error(self, self.tr("Error in xls file"),
                                            self.tr("The decision level code {0} is not in the database.")
                                                .format(decision_level))

                self.error_list[decision_no + " # " + str(count)] = self.tr("The decision level code {0} is not in the database.").format(decision_level)
                count += 1

                return False

        except SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("Query Error"), self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return False

        return True

    def __validate_row(self, decision_result, app_no, current_decision_no, decision_no, duration, landuse):

        #1st: decision result is type of integer
        #2cnd: decision id exists
        #3rd: application exists
        #4th: check if the decision number is different
        #5th: check the decision level
        #6th: check existance of landuse
        valid_row = True
        count = 1

        try:
            int(decision_result)

        except ValueError:
            self.error_list[app_no + " # " + str(count)] = self.tr("Could not convert decision result: {0} to integer.")\
                                                                    .format(str(decision_result))
            valid_row = False
            count += 1

        if valid_row:
            decision_result_count = self.session.query(ClDecision.code, ClDecision.description)\
                .filter_by(code=int(decision_result)).count()

            if decision_result_count == 0:
                self.error_list[app_no + " # " + str(count)] = \
                    self.tr("Could not find the decision result: {0}. Import will be canceled")\
                        .format(str(decision_result))

                valid_row = False
                count += 1

        try:
            int(landuse)

        except ValueError:
            self.error_list[app_no + " # " + str(count)] = self.tr("Could not convert landuse type: {0} to integer.")\
                                                                    .format(str(decision_result))
            valid_row = False
            count += 1

        if valid_row:
            decision_result_count = self.session.query(ClLanduseType.code, ClLanduseType.description)\
                .filter_by(code=int(landuse)).count()

            if decision_result_count == 0:
                self.error_list[app_no + " # " + str(count)] = \
                    self.tr("Could not find the landuse type: {0}. Import will be canceled")\
                        .format(str(landuse))

                valid_row = False
                count += 1

        application_count = self.session.query(CtApplication).filter_by(app_no=app_no).count()
        if application_count == 0:
            self.error_list[app_no + " # " + str(count)] = \
                self.tr("The application {0} does not exist. Import will be skipped.").format(app_no)

            valid_row = False
            count += 1

        elif application_count == 1:

            application = self.session.query(CtApplication).filter(CtApplication.app_no == app_no).one()

            if application.app_type in ConstantsPasture.APPLICATION_TYPE_WITH_DURATION:
                try:
                    int_duration = int(duration)
                    if int_duration == 0:
                        self.error_list[app_no + " # " + str(count)] = \
                            self.tr("The application {0} should have an approved duration.").format(app_no)
                        valid_row = False
                        count += 1
                except ValueError:
                    self.error_list[app_no + " # " + str(count)] = \
                        self.tr("The application {0} should have an approved duration.").format(app_no)
                    valid_row = False
                    count += 1

            if application.decision_result is not None:
                self.error_list[app_no + " # " + str(count)] = \
                    self.tr("There is already a decision for the application {0}.").format(app_no)
                valid_row = False
                count += 1

            count = application.statuses.filter(CtApplicationStatus.status == ConstantsPasture.APP_STATUS_SEND).count()
            if count == 0:
                self.error_list[app_no + " # " + str(count)] = \
                    self.tr("The application isn't send to the governor.").format(app_no)
                valid_row = False
                count += 1

        if decision_no != current_decision_no:
            self.error_list[app_no + " # " + str(count)] = \
                self.tr("The decision number is not equal in the dataset. Found number {0}").format(current_decision_no)
            valid_row = False
            count += 1

        return valid_row

    @pyqtSlot()
    def on_error_details_button_clicked(self):
        dialog = DecisionErrorDialog(self.error_list, self)
        dialog.exec_()

    @pyqtSlot()
    def on_import_button_clicked(self):

        try:
            self.commit()

        except SQLAlchemyError, e:
            self.rollback()
            PluginUtils.show_error(self, self.tr("Query Error"),
                                   self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))
            return

        self.__start_fade_out_timer()
        user = DatabaseUtils.current_user()
        user.pa_from = self.original_pa_from

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