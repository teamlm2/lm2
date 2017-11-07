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
from ..utils.LayerUtils import LayerUtils
from ..view.Ui_SParcelPersonDialog import *
from ..model.SParcelTbl import *
from ..model.SParcelPerson import *
from ..model.BsPerson import *

from xlsxwriter.utility import xl_rowcol_to_cell, xl_col_to_name
import xlsxwriter

class SParcelPersonDialog(QDialog, Ui_SParcelPersonDialog):

    def __init__(self, plugin ,parent=None,):

        super(SParcelPersonDialog, self).__init__(parent)
        mydialog = QDialog
        self.plugin = plugin
        self.setupUi(self)      
        self.close_button.clicked.connect(self.reject)

        self.session = SessionHandler().session_instance()
        self.__setup_twidgets()
        self.__setup_combo_box()

    def __setup_combo_box(self):

        landuse = self.session.query(ClLanduseType).all()
        for test in landuse:
            desc =  str(test.code)+': '+test.description
            aa = test.code
            self.landuse_cbox.addItem(desc, aa)

    def __setup_twidgets(self):

        self.result_person_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.result_person_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_person_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_person_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        self.result_parcel_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.result_parcel_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_parcel_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_parcel_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        self.parcel_person_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.parcel_person_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parcel_person_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.parcel_person_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        self.parcel_person_twidget.setColumnWidth(0, 80)
        self.parcel_person_twidget.setColumnWidth(1, 80)
        self.parcel_person_twidget.setColumnWidth(2, 500)

    @pyqtSlot()
    def on_search_parcel_button_clicked(self):

        self.result_parcel_twidget.setRowCount(0)

    	parcels = self.session.query(SParcelTbl).all()

    	count = 0
    	for parcel in parcels:
            self.result_parcel_twidget.insertRow(count)

            item = QTableWidgetItem(parcel.parcel_id)
            item.setData(Qt.UserRole, parcel.parcel_id)
            self.result_parcel_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(unicode(parcel.address_khashaa))
            item.setData(Qt.UserRole, parcel.address_khashaa)
            self.result_parcel_twidget.setItem(count, 1, item)

            count += 1

    @pyqtSlot()
    def on_search_person_button_clicked(self):

        self.result_person_twidget.setRowCount(0)

        register_number = self.search_person_id_edit.text()

        person_name = self.search_person_name_edit.text()
        person_name_like = '%'+person_name+'%'
        register_number_like = '%' + register_number + '%'

        persons = self.session.query(BsPerson)
        if register_number:
    	    persons = persons.filter(BsPerson.person_id.like(register_number_like))
        if person_name:
            persons = persons.filter(BsPerson.name.like(person_name_like))

    	count = 0
    	for person in persons:

    	    self.result_person_twidget.insertRow(count)

            item = QTableWidgetItem(unicode(person.person_id))
            item.setData(Qt.UserRole, person.person_id)
            self.result_person_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(unicode(person.name))
            item.setData(Qt.UserRole, person.name)
            self.result_person_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(unicode(person.first_name))
            item.setData(Qt.UserRole, person.first_name)
            self.result_person_twidget.setItem(count, 2, item)

    	    count += 1

        self.person_count_lbl.setText("Person Result:"+str(count))

    @pyqtSlot()
    def on_add_button_clicked(self):

        selected_items = self.result_person_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Songono uu"), self.tr("Ta irgenees zaawal songoson bh yostoi!"))
            return

        selected_items = self.result_parcel_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Songono uu"), self.tr("Ta negj talbaraas zaawal songoson bh yostoi!"))
            return

        landuse = None
        parcel_id = None
        person_id = None

        # land use
        landuse_code = self.landuse_cbox.itemData(self.landuse_cbox.currentIndex())
        landuse_text = self.landuse_cbox.currentText()

        # parcel_id
        parcel_selected_row = self.result_parcel_twidget.currentRow()
        parcel_item = self.result_parcel_twidget.item(parcel_selected_row, 0)
        parcel_id = parcel_item.data(Qt.UserRole)

        # person_id
        person_selected_row = self.result_person_twidget.currentRow()
        person_item = self.result_person_twidget.item(person_selected_row, 0)
        person_id = person_item.data(Qt.UserRole)

        parcel_person_count = self.session.query(SParcelPerson).filter(SParcelPerson.person_id == person_id).\
            filter(SParcelPerson.parcel_id == parcel_id).count()
        if parcel_person_count > 0:
            PluginUtils.show_message(self, self.tr("asdfafa"), self.tr("aaalsdjf;aldj"))
            return

        row_count = self.parcel_person_twidget.rowCount()
        self.parcel_person_twidget.insertRow(row_count)

        # add person_id
        item = QTableWidgetItem(unicode(person_id))
        item.setData(Qt.UserRole, person_id)
        self.parcel_person_twidget.setItem(row_count, 0, item)

        # add parcel_id
        item = QTableWidgetItem(parcel_id)
        item.setData(Qt.UserRole, parcel_id)
        self.parcel_person_twidget.setItem(row_count, 1, item)

        # add landuse
        item = QTableWidgetItem(unicode(landuse_text))
        item.setData(Qt.UserRole, landuse_code)
        self.parcel_person_twidget.setItem(row_count, 2, item)


        parcel_person = SParcelPerson()

        parcel_person.parcel_id = parcel_id
        parcel_person.person_id = person_id

        self.session.add(parcel_person)

        self.session.commit()

    @pyqtSlot()
    def on_search_parcel_person_button_clicked(self):

        self.parcel_person_twidget.setRowCount(0)

        person_id = self.search_parcel_person_edit.text()
        person_parcels = self.session.query(SParcelPerson)
        if person_id:
            person_id_like = '%'+person_id+'%'
            person_parcels = person_parcels.filter(SParcelPerson.person_id.like(person_id_like))

        count = 0
        for person_parcel in person_parcels:
            self.parcel_person_twidget.insertRow(count)

            # get landuse object
            landuse_code = None
            landuse_text = ''
            parcel = self.session.query(SParcelTbl).filter(SParcelTbl.parcel_id == person_parcel.parcel_id).one()
            if parcel.landuse:
                landuse = self.session.query(ClLanduseType).filter(ClLanduseType.code == parcel.landuse).one()
                landuse_text = landuse.description
                landuse_code = landuse.code

            # set columns
            item = QTableWidgetItem(unicode(person_parcel.person_id))
            item.setData(Qt.UserRole, person_parcel.person_id)
            self.parcel_person_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(unicode(person_parcel.parcel_id))
            item.setData(Qt.UserRole, person_parcel.parcel_id)
            self.parcel_person_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(landuse_text)
            item.setData(Qt.UserRole, landuse_code)
            self.parcel_person_twidget.setItem(count, 2, item)

            count +=1

    @pyqtSlot()
    def on_edit_button_clicked(self):

        selected_items = self.parcel_person_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Songono uu"), self.tr("Ta zaawal songoson bh yostoi!"))
            return

        # landuse get combobox value
        landuse_code = self.landuse_cbox.itemData(self.landuse_cbox.currentIndex())
        landuse_text = self.landuse_cbox.currentText()

        # selected row of table
        selected_row = self.parcel_person_twidget.currentRow()

        # parcel_id column item
        parcel_id_item = self.parcel_person_twidget.item(selected_row, 1)
        parcel_id = parcel_id_item.data(Qt.UserRole)

        # landuse colum item
        landuse_item = self.parcel_person_twidget.item(selected_row, 2)

        # set landuse value for landuse item
        landuse_item.setText(unicode(landuse_text))
        landuse_item.setData(Qt.UserRole, landuse_code)


        # database update landuse column for s_parcel_tbl
        parcel = self.session.query(SParcelTbl).filter(SParcelTbl.parcel_id == parcel_id).one()
        parcel.landuse = landuse_code

        self.session.commit()

    @pyqtSlot()
    def on_delete_button_clicked(self):

        selected_items = self.parcel_person_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Songono uu"), self.tr("Ta zaawal songoson bh yostoi!"))
            return

        # selected row of table
        selected_row = self.parcel_person_twidget.currentRow()

        # parcel_id column item
        parcel_id_item = self.parcel_person_twidget.item(selected_row, 1)
        parcel_id = parcel_id_item.data(Qt.UserRole)

        person_id_item = self.parcel_person_twidget.item(selected_row, 0)
        person_id = person_id_item.data(Qt.UserRole)

        object_count = self.session.query(SParcelPerson).filter(SParcelPerson.parcel_id == parcel_id).\
            filter(SParcelPerson.person_id == person_id).count()

        if object_count == 1:
            self.session.query(SParcelPerson).filter(SParcelPerson.parcel_id == parcel_id). \
                filter(SParcelPerson.person_id == person_id).delete()

            self.parcel_person_twidget.removeRow(selected_row)

        self.session.commit()

    @pyqtSlot()
    def on_zoom_button_clicked(self):

        selected_items = self.parcel_person_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Songono uu"), self.tr("Ta zaawal songoson bh yostoi!"))
            return

        # selected row of table
        selected_row = self.parcel_person_twidget.currentRow()

        # parcel_id column item
        parcel_id_item = self.parcel_person_twidget.item(selected_row, 1)
        parcel_id = parcel_id_item.data(Qt.UserRole)

        layer = LayerUtils.layer_by_data_source("base", 's_parcel_tbl')

        self.__select_feature(parcel_id, layer)

    def __select_feature(self, parcel_id, layer):

        expression = " parcel_id = \'" + parcel_id + "\'"
        request = QgsFeatureRequest()
        request.setFilterExpression(expression)
        feature_ids = []
        iterator = layer.getFeatures(request)

        for feature in iterator:
            feature_ids.append(feature.id())
        if len(feature_ids) == 0:
            self.error_label.setText(self.tr("No parcel assigned"))

        layer.setSelectedFeatures(feature_ids)
        self.plugin.iface.mapCanvas().zoomToSelected(layer)

    @pyqtSlot()
    def on_print_button_clicked(self):

        report_name = 'my_report'
        default_path = r'D:/TM_LM2/'
        default_parent_path = r'D:/TM_LM2'
        if not os.path.exists(default_parent_path):
            os.makedirs('D:/TM_LM2')

        if not os.path.exists(default_path):
            os.makedirs(default_path)

        workbook = xlsxwriter.Workbook(default_path + report_name + ".xlsx")
        worksheet = workbook.add_worksheet()

        format_header = workbook.add_format()
        format_header.set_text_wrap()
        format_header.set_align('center')
        format_header.set_align('vcenter')
        format_header.set_font_name('Times New Roman')
        format_header.set_font_size(14)
        format_header.set_bold()

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 15)

        worksheet.merge_range('C2:F2', u'Миний анхны тайлан', format_header)

        try:
            workbook.close()
            QDesktopServices.openUrl(QUrl.fromLocalFile(default_path + report_name + ".xlsx"))
        except IOError, e:
            PluginUtils.show_error(self, self.tr("Out error"), self.tr("This file is already opened. Please close re-run"))