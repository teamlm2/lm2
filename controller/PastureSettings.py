__author__ = 'B.Ankhbold'
# -*- encoding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sqlalchemy import exc, or_
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_, extract
from datetime import date, datetime, timedelta
from ..view.Ui_PastureSettings import *
from ..model.DatabaseHelper import *
from ..model.LM2Exception import LM2Exception
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.SessionHandler import SessionHandler
from ..utils.PluginUtils import PluginUtils
from ..model import Constants
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.AuLevel3 import *
from ..model.PsApplicationTypePastureType import *
from ..model.EnumerationsPasture import ApplicationType, UserRight
from ..model.PsApplicationTypeDocType import *
from ..model.PsContractDocType import *
from ..model.PsRecoveryClass import *
from ..model.PsNZSheepFood import *
from ..model.PsPastureStatusFormula import *
from ..model.ClApplicationType import *
from ..utils.PluginUtils import *
from ..model import Constants
from ..model.DatabaseHelper import *
from ..model.ClNaturalZone import *
from ..model.ClLandForm import *
from ..model.PClLessSymbol import *
from ..model.PClFormulaType import *
from ..model.PsFormulaTypeLandForm import *
from ..model.PsNaturalZoneLandForm import *
from ..model.PsNaturalZonePlants import *
from ..model.PsSoilEvaluation import *
from ..model.PsPastureComparisonFormula import *
from ..model.PsPastureEvaluationFormula import *
from ..model.ClMemberRole import *
from ..model.ClPastureType import *
from ..model.ClPastureDocument import *
from ..model.ClPastureValues import *
from ..model.ClliveStock import *
from ..model.PsLiveStockConvert import *
from .qt_classes.DoubleSpinBoxDelegate import *
from .qt_classes.IntegerSpinBoxDelegate import IntegerSpinBoxDelegate
from inspect import currentframe
from ..utils.FileUtils import FileUtils
from ..utils.LayerUtils import LayerUtils
import os

CODELIST_CODE = 0
CODELIST_DESC = 1

class PastureSettings(QDialog, Ui_PastureSettings, DatabaseHelper):
    def __init__(self, parent=None):

        super(PastureSettings, self).__init__(parent)
        DatabaseHelper.__init__(self)

        self.setupUi(self)
        self.time_counter = None
        self.setWindowTitle(self.tr("Pasture settings"))
        self.close_button.clicked.connect(self.reject)
        self.session = SessionHandler().session_instance()
        self.old_codelist_index = -1
        self.__setup_twidget()
        self.__setup_combo_boxes()

        self.__setup_nz_sheep_food()
        self.__setup_rc()

    def __setup_twidget(self):

        self.connect_type_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.connect_type_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.connect_type_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.connect_type_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        self.land_form_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.land_form_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.land_form_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.land_form_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        self.formula_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.formula_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.formula_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.formula_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        self.formula_twidget.horizontalHeader().resizeSection(0, 50)
        self.formula_twidget.horizontalHeader().resizeSection(1, 120)
        self.formula_twidget.horizontalHeader().resizeSection(2, 100)
        self.formula_twidget.horizontalHeader().resizeSection(3, 80)

        self.formula_more_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.formula_more_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.formula_more_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.formula_more_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        self.formula_less_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.formula_less_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.formula_less_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.formula_less_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

        self.sheep_food_twidget.setAlternatingRowColors(True)
        self.sheep_food_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.sheep_food_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sheep_food_twidget.setSelectionMode(QTableWidget.SingleSelection)

        delegate = IntegerSpinBoxDelegate(1, 1, 1000, 1000, 10, self.sheep_food_twidget)
        self.sheep_food_twidget.setItemDelegateForColumn(1, delegate)

        self.recovery_class_twidget.setAlternatingRowColors(True)
        self.recovery_class_twidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.recovery_class_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.recovery_class_twidget.setSelectionMode(QTableWidget.SingleSelection)

        delegate = IntegerSpinBoxDelegate(1, 10, 100, 1000, 10, self.recovery_class_twidget)
        self.recovery_class_twidget.setItemDelegateForColumn(1, delegate)

    def __setup_combo_boxes(self):

        code_lists = self.__codelist_names()
        for key, value in code_lists.iteritems():
            self.select_codelist_cbox.addItem(value, key)

        natural_zones = self.session.query(ClNaturalZone).all()
        for natural_zone in natural_zones:
            self.natural_zone_cbox.addItem(natural_zone.description, natural_zone.code)

        formula_types = self.session.query(PClLessSymbol).all()
        for formula_type in formula_types:
            self.less_symbol_cbox.addItem(formula_type.description, formula_type.code)

        for formula_type in formula_types:
            # if formula_type.code == 1 or formula_type.code == 2:
            self.less_symbol_comp_cbox.addItem(formula_type.description, formula_type.code)

        soil_evaluations = self.session.query(PsSoilEvaluation).all()

        if soil_evaluations:
            for soil_evaluation in soil_evaluations:
                self.soil_evaluation_cbox.addItem(str(soil_evaluation.ball)+':'+soil_evaluation.description, soil_evaluation.code)

    @pyqtSlot(int)
    def on_natural_zone_cbox_currentIndexChanged(self, index):

        self.land_form_twidget.setRowCount(0)
        natural_zone_code = self.natural_zone_cbox.itemData(self.natural_zone_cbox.currentIndex())
        self.plants_cbox.clear()
        nz_plants = self.session.query(PsNaturalZonePlants).filter(PsNaturalZonePlants.natural_zone == natural_zone_code).all()
        for nz_plant in nz_plants:
            plants = self.session.query(ClPastureValues).filter(ClPastureValues.code == nz_plant.plants).one()
            self.plants_cbox.addItem(plants.description, plants.code)
            self.plants_comp_cbox.addItem(plants.description, plants.code)

        nz_land_forms = self.session.query(PsNaturalZoneLandForm).\
            filter(PsNaturalZoneLandForm.natural_zone == natural_zone_code).all()
        count = 0
        for nz_land_form in nz_land_forms:
            land_form = self.session.query(ClLandForm).filter(ClLandForm.code == nz_land_form.land_form).one()

            self.land_form_twidget.insertRow(count)

            item = QTableWidgetItem(unicode(land_form.description))
            item.setData(Qt.UserRole, land_form.code)
            self.land_form_twidget.setItem(count, 0, item)

    def __setup_rc(self):

        ps_rcs = self.session.query(PsRecoveryClass).all()
        count = 0
        for ps_rc in ps_rcs:
            self.recovery_class_twidget.insertRow(count)

            item = QTableWidgetItem(ps_rc.rc_code)
            item.setData(Qt.UserRole, ps_rc.id)
            item.setData(Qt.UserRole+1, ps_rc.rc_code)
            self.recovery_class_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(str(ps_rc.rc_precent))
            item.setData(Qt.UserRole, ps_rc.rc_precent)
            self.recovery_class_twidget.setItem(count, 1, item)

            count += 1

    def __setup_nz_sheep_food(self):

        natural_zones = self.session.query(ClNaturalZone).all()
        count = 0
        for natural_zone in natural_zones:
            self.sheep_food_twidget.insertRow(count)

            item = QTableWidgetItem(unicode(natural_zone.description))
            item.setData(Qt.UserRole, natural_zone.code)
            self.sheep_food_twidget.setItem(count, 0, item)

            ps_nz_sheep_foods_count = self.session.query(PsNZSheepFood).\
                filter(PsNZSheepFood.natural_zone == natural_zone.code).count()
            current_value = 511
            if ps_nz_sheep_foods_count == 1:
                ps_nz_sheep_food = self.session.query(PsNZSheepFood). \
                    filter(PsNZSheepFood.natural_zone == natural_zone.code).one()

                current_value = ps_nz_sheep_food.current_value

            item = QTableWidgetItem(str(current_value))
            item.setData(Qt.UserRole, current_value)
            self.sheep_food_twidget.setItem(count, 1, item)

            count += 1

    def __codelist_names(self):

        lookup = {}
        session = SessionHandler().session_instance()

        try:
            sql = text("select description, relname from pg_description join pg_class on pg_description.objoid = pg_class.oid join pg_namespace on pg_namespace.oid = pg_class.relnamespace where pg_namespace.nspname = 'codelists' and (relname = 'cl_pasture_type' or relname = 'cl_pasture_values' or relname = 'cl_member_role' or relname = 'cl_pasture_document')")
            result = session.execute(sql).fetchall()

            for row in result:
                lookup[row[1]] = row[0]

        except exc.SQLAlchemyError, e:
            PluginUtils.show_error(self, self.tr("SQL Error"), e.message)

        return lookup

    @pyqtSlot(int)
    def on_select_codelist_cbox_currentIndexChanged(self, idx):

        if idx == -1:
            return

        if self.old_codelist_index == idx:
            return

        if self.old_codelist_index == -1:
            self.__read_codelist_entries()
        else:
            try:
                self.__save_codelist_entries()
            except exc.SQLAlchemyError, e:
                PluginUtils.show_error(None, self.tr("SQL Error"), e.message)
                self.select_codelist_cbox.setCurrentIndex(self.old_codelist_index)
                return

        self.old_codelist_index = idx

    def __read_codelist_entries(self):

        self.table_widget.clearContents()
        self.table_widget.setRowCount(0)
        session = SessionHandler().session_instance()

        codelist_name = self.select_codelist_cbox.itemData(self.select_codelist_cbox.currentIndex())
        codelist_class = self.__codelist_class(codelist_name)
        codelist_entries = session.query(codelist_class).order_by(codelist_class.code).all()
        self.table_widget.setRowCount(len(codelist_entries))
        row = 0
        for entry in codelist_entries:
            self.__add_codelist_row(row, entry.code, entry.description)
            row += 1

        self.table_widget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

    def __add_codelist_row(self, row, code, description, lock_item=True):

        if lock_item:
            item = QTableWidgetItem('{0}'.format(code))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        else:
            item = QTableWidgetItem()

        item.setData(Qt.UserRole, code)
        self.table_widget.setItem(row, CODELIST_CODE, item)
        item = QTableWidgetItem(description)
        self.table_widget.setItem(row, CODELIST_DESC, item)

    def __codelist_class(self, table_name):

        if table_name == 'cl_pasture_type':
            cls = ClPastureType
        elif table_name == "cl_member_role":
            cls = ClMemberRole
        elif table_name == "cl_pasture_document":
            cls = ClPastureDocument
        elif table_name == "cl_pasture_values":
            cls = ClPastureValues
        else:
            return None

        return cls

    def __save_codelist_entries(self):

        codelist_name = self.select_codelist_cbox.itemData(self.old_codelist_index, Qt.UserRole)
        codelist_class = self.__codelist_class(codelist_name)

        session = SessionHandler().session_instance()
        self.create_savepoint()

        try:
            for row in range(self.table_widget.rowCount()):
                new_row = False

                code = self.table_widget.item(row, CODELIST_CODE).data(Qt.UserRole)

                if self.table_widget.item(row, CODELIST_CODE).text() == -1:
                    self.status_label.setText(self.tr("-1 is not allowed for code in codelists."))
                    self.rollback_to_savepoint()

                if code == -1:
                    new_row = True
                    # noinspection PyCallingNonCallable
                    codelist_entry = codelist_class()
                else:
                    codelist_entry = session.query(codelist_class).get(code)
                try:
                    code_int = int(self.table_widget.item(row, CODELIST_CODE).text())

                except ValueError:
                    self.status_label.setText(self.tr("A code in the codelist has a wrong value."))
                    self.rollback_to_savepoint()
                    raise LM2Exception(self.tr("Error"), self.tr("A code in the codelist has a wrong value."))
                codelist_name = self.select_codelist_cbox.itemData(self.select_codelist_cbox.currentIndex(),
                                                                   Qt.UserRole)
                if codelist_name == "cl_landuse_type":
                    description = self.table_widget.item(row, CODELIST_DESC).text()
                    codelist_entry.code = code_int
                    codelist_entry.description = description
                    codelist_entry.code2 = int(str(code_int)[:2])
                    codelist_entry.description2 = description
                else:
                    description = self.table_widget.item(row, CODELIST_DESC).text()
                    codelist_entry.code = code_int
                    codelist_entry.description = description

                if new_row:
                    session.add(codelist_entry)

        except exc.SQLAlchemyError:
            self.rollback_to_savepoint()
            raise

        self.__read_codelist_entries()

    @pyqtSlot()
    def on_add_button_clicked(self):

        if self.select_codelist_cbox.currentIndex() == -1:
            return

        row = self.table_widget.rowCount()
        self.table_widget.insertRow(row)

        self.__add_codelist_row(row, -1, None, False)

    @pyqtSlot()
    def on_delete_button_clicked(self):

        row = self.table_widget.currentRow()
        if row == -1:
            return

        codelist_name = self.select_codelist_cbox.itemData(self.select_codelist_cbox.currentIndex(), Qt.UserRole)
        codelist_class = self.__codelist_class(codelist_name)

        code = self.table_widget.item(row, CODELIST_CODE).data(Qt.UserRole)
        session = SessionHandler().session_instance()
        count = session.query(codelist_class).filter(codelist_class.code == code).count()
        if count > 0:
            entry = session.query(codelist_class).get(code)
            self.create_savepoint()
            try:
                session.delete(entry)

            except exc.SQLAlchemyError, e:
                self.rollback_to_savepoint()
                PluginUtils.show_error(None, self.tr("SQL Error"), e.message)
                return

        self.table_widget.removeRow(row)

    def __save_settings(self):

        # try:
        self.__save_codelist_entries()
        self.__save_codelist_settings()
        self.__save_formula_evaluation()
        return True
        # except exc.SQLAlchemyError,  e:
        #     PluginUtils.show_error(self, self.tr("SQL Error"), e.message)
        #     return False

    @pyqtSlot()
    def on_apply_button_clicked(self):

        if not self.__save_settings():
            return

        self.commit()
        self.__start_fade_out_timer()

    def __save_formula_evaluation(self):

        if self.soil_evaluation_chbox.isChecked():
            natural_zone_code = self.natural_zone_cbox.itemData(self.natural_zone_cbox.currentIndex())
            natural_zone = self.session.query(ClNaturalZone).filter(ClNaturalZone.code == natural_zone_code).one()

            current_row = self.land_form_twidget.currentRow()
            item = self.land_form_twidget.item(current_row, 0)
            land_form_code = item.data(Qt.UserRole)
            land_form = self.session.query(ClLandForm).filter(ClLandForm.code == land_form_code).one()

            rc_id = self.recovery_class_comp_cbox.itemData(self.recovery_class_comp_cbox.currentIndex())
            rc = self.session.query(PsRecoveryClass).filter(PsRecoveryClass.id == rc_id).one()

            soil_evaluation_code = self.soil_evaluation_cbox.itemData(self.soil_evaluation_cbox.currentIndex())
            soil_evaluation = self.session.query(PsSoilEvaluation).filter(PsSoilEvaluation.code == soil_evaluation_code).one()

            ps_soil_formula_count = self.session.query(PsPastureEvaluationFormula).\
                filter(PsPastureEvaluationFormula.natural_zone == natural_zone_code). \
                filter(PsPastureEvaluationFormula.land_form == land_form_code). \
                filter(PsPastureEvaluationFormula.rc_id == rc_id).count()
            if ps_soil_formula_count == 1:
                ps_soil_formula = self.session.query(PsPastureEvaluationFormula). \
                    filter(PsPastureEvaluationFormula.natural_zone == natural_zone_code). \
                    filter(PsPastureEvaluationFormula.land_form == land_form_code). \
                    filter(PsPastureEvaluationFormula.rc_id == rc_id).one()

                ps_soil_formula.soil_evaluation = soil_evaluation_code
                ps_soil_formula.soil_evaluation_ref = soil_evaluation
            else:
                ps_soil_formula = PsPastureEvaluationFormula()
                ps_soil_formula.natural_zone = natural_zone_code
                ps_soil_formula.natural_zone_ref = natural_zone
                ps_soil_formula.land_form = land_form_code
                ps_soil_formula.land_form_ref = land_form
                ps_soil_formula.rc_id = rc_id
                ps_soil_formula.rc_id_ref = rc
                ps_soil_formula.soil_evaluation = soil_evaluation_code
                ps_soil_formula.soil_evaluation_ref = soil_evaluation
                self.session.add(ps_soil_formula)

            ps_comparison_formulas = self.session.query(PsPastureComparisonFormula). \
                filter(PsPastureComparisonFormula.natural_zone == natural_zone_code). \
                filter(PsPastureComparisonFormula.land_form == land_form_code).\
                filter(PsPastureComparisonFormula.rc_id == rc_id).all()

            for ps_comparison_formula in ps_comparison_formulas:
                self.session.query(PsPastureComparisonFormula). \
                    filter(PsPastureComparisonFormula.natural_zone == natural_zone_code). \
                    filter(PsPastureComparisonFormula.land_form == land_form_code). \
                    filter(PsPastureComparisonFormula.rc_id == rc_id). \
                    filter(PsPastureComparisonFormula.plants == ps_comparison_formula.plants).delete()
            self.formula_more_twidget.setRowCount(0)
            self.formula_less_twidget.setRowCount(0)

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

    @pyqtSlot(bool)
    def on_app_type_pasture_type_rbutton_toggled(self, state):

        if state:
            self.base_type.setVisible(True)
            self.base_type.clear()

            try:
                application_types = self.session.query(ClApplicationType). \
                    filter(or_(ClApplicationType.code == ApplicationType.pasture_use,
                               ClApplicationType.code == ApplicationType.legitimate_rights)). \
                    order_by(ClApplicationType.code).all()

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"),
                                       self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

            for item in application_types:
                self.base_type.addItem(item.description, item.code)

            count = 0
            self.connect_type_twidget.clearContents()
            self.connect_type_twidget.setRowCount(0)

            app_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if self.all_types_chbox.isChecked():
                pasture_types = self.session.query(ClPastureType).all()
            else:
                pasture_types = self.session.query(ClPastureType) \
                    .join(PsApplicationTypePastureType, ClPastureType.code == PsApplicationTypePastureType.pasture_type)\
                    .filter(PsApplicationTypePastureType.app_type == app_type).all()
            app_pastures = self.session.query(PsApplicationTypePastureType).all()
            for type in pasture_types:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for app_pasture in app_pastures:
                    if type.code == app_pasture.pasture_type and app_pasture.app_type == app_type:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1

    @pyqtSlot(bool)
    def on_app_type_doc_type_rbutton_toggled(self, state):

        if state:
            self.base_type.setVisible(True)
            self.base_type.clear()
            try:
                application_types = self.session.query(ClApplicationType). \
                    filter(or_(ClApplicationType.code == ApplicationType.pasture_use,
                               ClApplicationType.code == ApplicationType.legitimate_rights)). \
                    order_by(ClApplicationType.code).all()

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"),
                                       self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

            for item in application_types:
                self.base_type.addItem(item.description, item.code)

            count = 0
            self.connect_type_twidget.clearContents()
            self.connect_type_twidget.setRowCount(0)

            app_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if self.all_types_chbox.isChecked():
                doc_types = self.session.query(ClPastureDocument).all()
            else:
                doc_types = self.session.query(ClPastureDocument) \
                    .join(PsApplicationTypeDocType, ClPastureDocument.code == PsApplicationTypeDocType.document) \
                    .filter(PsApplicationTypeDocType.app_type == app_type).all()
            app_docs = self.session.query(PsApplicationTypeDocType).all()
            for type in doc_types:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for app_doc in app_docs:
                    if type.code == app_doc.document and app_doc.app_type == app_type:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1

    @pyqtSlot(bool)
    def on_contract_doc_type_rbutton_toggled(self, state):

        if state:
            self.base_type.setVisible(True)
            self.base_type.clear()

            try:
                application_types = self.session.query(ClApplicationType). \
                    filter(or_(ClApplicationType.code == ApplicationType.pasture_use,
                               ClApplicationType.code == ApplicationType.legitimate_rights)). \
                    order_by(ClApplicationType.code).all()

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"),
                                       self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

            for item in application_types:
                self.base_type.addItem(item.description, item.code)

            count = 0
            self.connect_type_twidget.clearContents()
            self.connect_type_twidget.setRowCount(0)

            app_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if self.all_types_chbox.isChecked():
                doc_types = self.session.query(ClPastureDocument).all()
            else:
                doc_types = self.session.query(ClPastureDocument) \
                    .join(PsContractDocType, ClPastureDocument.code == PsContractDocType.document) \
                    .filter(PsContractDocType.app_type == app_type).all()
            app_docs = self.session.query(PsContractDocType).all()
            for type in doc_types:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for app_doc in app_docs:
                    if type.code == app_doc.document and app_doc.app_type == app_type:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1

    @pyqtSlot(bool)
    def on_natural_zone_land_form_rbutton_toggled(self, state):

        if state:
            self.base_type.setVisible(True)
            self.base_type.clear()

            try:
                natural_zones = self.session.query(ClNaturalZone).all()

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"),
                                       self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

            for item in natural_zones:
                self.base_type.addItem(item.description, item.code)

            count = 0
            self.connect_type_twidget.clearContents()
            self.connect_type_twidget.setRowCount(0)

            zone_code = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if self.all_types_chbox.isChecked():
                land_forms = self.session.query(ClLandForm).all()
            else:
                land_forms = self.session.query(ClLandForm) \
                    .join(PsNaturalZoneLandForm, ClLandForm.code == PsNaturalZoneLandForm.land_form) \
                    .filter(PsNaturalZoneLandForm.natural_zone == zone_code).all()
            zone_land_forms = self.session.query(PsNaturalZoneLandForm).all()
            for type in land_forms:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for form in zone_land_forms:
                    if type.code == form.land_form and form.natural_zone == zone_code:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1

    @pyqtSlot(bool)
    def on_natural_zone_land_plants_rbutton_toggled(self, state):

        if state:
            self.base_type.setVisible(True)
            self.base_type.clear()

            try:
                natural_zones = self.session.query(ClNaturalZone).all()

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"),
                                       self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

            for item in natural_zones:
                self.base_type.addItem(item.description, item.code)

            count = 0
            self.connect_type_twidget.clearContents()
            self.connect_type_twidget.setRowCount(0)

            zone_code = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if self.all_types_chbox.isChecked():
                land_forms = self.session.query(ClPastureValues).all()
            else:
                land_forms = self.session.query(ClPastureValues) \
                    .join(PsNaturalZonePlants, ClPastureValues.code == PsNaturalZonePlants.plants) \
                    .filter(PsNaturalZonePlants.natural_zone == zone_code).all()
            zone_land_forms = self.session.query(PsNaturalZonePlants).all()
            for type in land_forms:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for form in zone_land_forms:
                    if type.code == form.plants and form.natural_zone == zone_code:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1

    @pyqtSlot(bool)
    def on_formula_type_land_form_rbutton_toggled(self, state):

        if state:
            self.base_type.setVisible(True)
            self.base_type.clear()

            try:
                formula_types = self.session.query(PClFormulaType).all()

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"),
                                       self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

            for item in formula_types:
                self.base_type.addItem(item.description, item.code)

            count = 0
            self.connect_type_twidget.clearContents()
            self.connect_type_twidget.setRowCount(0)

            formula_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if self.all_types_chbox.isChecked():
                land_forms = self.session.query(ClLandForm).all()
            else:
                land_forms = self.session.query(ClLandForm) \
                    .join(PsFormulaTypeLandForm, ClLandForm.code == PsFormulaTypeLandForm.land_form) \
                    .filter(PsFormulaTypeLandForm.formula_type == formula_type).all()
            formula_land_forms = self.session.query(PsFormulaTypeLandForm).all()
            for type in land_forms:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for form in formula_land_forms:
                    if type.code == form.formula_type and form.formula_type == formula_type:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1

    @pyqtSlot(bool)
    def on_live_stock_convert_rbutton_toggled(self, state):

        if state:
            self.live_stock_convert_twidget.setEnabled(True)

            try:
                live_stocks = self.session.query(ClliveStock).all()

            except SQLAlchemyError, e:
                PluginUtils.show_error(self, self.tr("File Error"),
                                       self.tr("Error in line {0}: {1}").format(currentframe().f_lineno, e.message))

            count = 0
            self.live_stock_convert_twidget.clearContents()
            self.live_stock_convert_twidget.setRowCount(0)

            for live_stock in live_stocks:
                convert_value = 0
                live_stock_convert_count = self.session.query(PsLiveStockConvert).\
                    filter(PsLiveStockConvert.live_stock_type == live_stock.code).count()
                if live_stock_convert_count == 1:
                    live_stock_convert = self.session.query(PsLiveStockConvert). \
                        filter(PsLiveStockConvert.live_stock_type == live_stock.code).one()

                    convert_value = live_stock_convert.convert_value

                self.live_stock_convert_twidget.insertRow(count)

                item = QTableWidgetItem(live_stock.description)
                item.setData(Qt.UserRole, live_stock.code)
                self.live_stock_convert_twidget.setItem(count, 0, item)

                self.live_stock_convert_twidget.setColumnWidth(1, 75)

                delegate = DoubleSpinBoxDelegate(1, -100000, 1000000.0000, 0.0001, 0.001,
                                                 self.live_stock_convert_twidget)
                self.live_stock_convert_twidget.setItemDelegateForColumn(1, delegate)
                item = QTableWidgetItem(str(convert_value))
                item.setData(Qt.UserRole, convert_value)
                self.live_stock_convert_twidget.setItem(count, 1, item)

                count += 1
        else:
            self.live_stock_convert_twidget.setEnabled(False)

    @pyqtSlot(int)
    def on_base_type_currentIndexChanged(self, index):

        count = 0
        self.connect_type_twidget.clearContents()
        self.connect_type_twidget.setRowCount(0)

        if self.app_type_pasture_type_rbutton.isChecked():
            app_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if self.all_types_chbox.isChecked():
                pasture_types = self.session.query(ClPastureType).all()
            else:
                pasture_types = self.session.query(ClPastureType) \
                    .join(PsApplicationTypePastureType, ClPastureType.code == PsApplicationTypePastureType.pasture_type) \
                    .filter(PsApplicationTypePastureType.app_type == app_type).all()
            app_pastures = self.session.query(PsApplicationTypePastureType).all()
            for type in pasture_types:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for app_pasture in app_pastures:
                    if type.code == app_pasture.pasture_type and app_pasture.app_type == app_type:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1
        elif self.app_type_doc_type_rbutton.isChecked():
            app_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if self.all_types_chbox.isChecked():
                doc_types = self.session.query(ClPastureDocument).all()
            else:
                doc_types = self.session.query(ClPastureDocument) \
                    .join(PsApplicationTypeDocType, ClPastureDocument.code == PsApplicationTypeDocType.document) \
                    .filter(PsApplicationTypeDocType.app_type == app_type).all()
            app_docs = self.session.query(PsApplicationTypeDocType).all()
            for type in doc_types:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for app_doc in app_docs:
                    if type.code == app_doc.document and app_doc.app_type == app_type:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1
        elif self.contract_doc_type_rbutton.isChecked():
            app_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if self.all_types_chbox.isChecked():
                doc_types = self.session.query(ClPastureDocument).all()
            else:
                doc_types = self.session.query(ClPastureDocument) \
                    .join(PsContractDocType, ClPastureDocument.code == PsContractDocType.document) \
                    .filter(PsContractDocType.app_type == app_type).all()
            app_docs = self.session.query(PsContractDocType).all()
            for type in doc_types:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for app_doc in app_docs:
                    if type.code == app_doc.document and app_doc.app_type == app_type:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1
        elif self.natural_zone_land_form_rbutton.isChecked():
            zone_code = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if self.all_types_chbox.isChecked():
                land_forms = self.session.query(ClLandForm).all()
            else:
                land_forms = self.session.query(ClLandForm) \
                    .join(PsNaturalZoneLandForm, ClLandForm.code == PsNaturalZoneLandForm.land_form) \
                    .filter(PsNaturalZoneLandForm.natural_zone == zone_code).all()
            zone_land_forms = self.session.query(PsNaturalZoneLandForm).all()
            for type in land_forms:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for form in zone_land_forms:
                    if type.code == form.land_form and form.natural_zone == zone_code:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1
        elif self.formula_type_land_form_rbutton.isChecked():
            formula_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if self.all_types_chbox.isChecked():
                land_forms = self.session.query(ClLandForm).all()
            else:
                land_forms = self.session.query(ClLandForm) \
                    .join(PsFormulaTypeLandForm, ClLandForm.code == PsFormulaTypeLandForm.land_form) \
                    .filter(PsFormulaTypeLandForm.formula_type == formula_type).all()
            formula_land_forms = self.session.query(PsFormulaTypeLandForm).all()
            for type in land_forms:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for form in formula_land_forms:
                    if type.code == form.land_form and form.formula_type == formula_type:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1
        elif self.natural_zone_land_plants_rbutton.isChecked():
            zone_code = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if self.all_types_chbox.isChecked():
                land_forms = self.session.query(ClPastureValues).all()
            else:
                land_forms = self.session.query(ClPastureValues) \
                    .join(PsNaturalZonePlants, ClPastureValues.code == PsNaturalZonePlants.plants) \
                    .filter(PsNaturalZonePlants.natural_zone == zone_code).all()
            zone_land_forms = self.session.query(PsNaturalZonePlants).all()
            for type in land_forms:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for form in zone_land_forms:
                    if type.code == form.plants and form.natural_zone == zone_code:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1

    @pyqtSlot(int)
    def on_all_types_chbox_stateChanged(self, state):

        count = 0
        self.connect_type_twidget.clearContents()
        self.connect_type_twidget.setRowCount(0)
        if self.app_type_pasture_type_rbutton.isChecked():
            app_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if state == Qt.Checked:
                pasture_types = self.session.query(ClPastureType).all()
            else:
                pasture_types = self.session.query(ClPastureType) \
                    .join(PsApplicationTypePastureType, ClPastureType.code == PsApplicationTypePastureType.pasture_type) \
                    .filter(PsApplicationTypePastureType.app_type == app_type).all()
            app_pastures = self.session.query(PsApplicationTypePastureType).all()
            for type in pasture_types:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for app_pasture in app_pastures:
                    if type.code == app_pasture.pasture_type and app_pasture.app_type == app_type:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1
        elif self.app_type_doc_type_rbutton.isChecked():
            app_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if state == Qt.Checked:
                doc_types = self.session.query(ClPastureDocument).all()
            else:
                doc_types = self.session.query(ClPastureDocument) \
                    .join(PsApplicationTypeDocType, ClPastureDocument.code == PsApplicationTypeDocType.document) \
                    .filter(PsApplicationTypeDocType.app_type == app_type).all()
            app_docs = self.session.query(PsApplicationTypeDocType).all()
            for type in doc_types:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for app_doc in app_docs:
                    if type.code == app_doc.document and app_doc.app_type == app_type:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1
        elif self.contract_doc_type_rbutton.isChecked():
            app_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if state == Qt.Checked:
                doc_types = self.session.query(ClPastureDocument).all()
            else:
                doc_types = self.session.query(ClPastureDocument) \
                    .join(PsContractDocType, ClPastureDocument.code == PsContractDocType.document) \
                    .filter(PsContractDocType.app_type == app_type).all()
            app_docs = self.session.query(PsContractDocType).all()
            for type in doc_types:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for app_doc in app_docs:
                    if type.code == app_doc.document and app_doc.app_type == app_type:
                        item.setCheckState(Qt.Checked)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1
        elif self.natural_zone_land_form_rbutton.isChecked():
            zone_code = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if state == Qt.Checked:
                land_forms = self.session.query(ClLandForm).all()
            else:
                land_forms = self.session.query(ClLandForm) \
                    .join(PsNaturalZoneLandForm, ClLandForm.code == PsNaturalZoneLandForm.land_form) \
                    .filter(PsNaturalZoneLandForm.natural_zone == zone_code).all()
            zone_land_forms = self.session.query(PsNaturalZoneLandForm).all()
            for type in land_forms:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for form in zone_land_forms:
                    if type.code == form.land_form and form.natural_zone == zone_code:
                        item.setCheckState(Qt.Checked)
                        # item.setBackground(Qt.blue)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1
        elif self.natural_zone_land_plants_rbutton.isChecked():
            zone_code = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if state == Qt.Checked:
                land_forms = self.session.query(ClPastureValues).all()
            else:
                land_forms = self.session.query(ClPastureValues) \
                    .join(PsNaturalZonePlants, ClPastureValues.code == PsNaturalZonePlants.plants) \
                    .filter(PsNaturalZonePlants.natural_zone == zone_code).all()
            zone_land_forms = self.session.query(PsNaturalZonePlants).all()
            for type in land_forms:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for form in zone_land_forms:
                    if type.code == form.plants and form.natural_zone == zone_code:
                        item.setCheckState(Qt.Checked)
                        # item.setBackground(Qt.blue)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1
        elif self.formula_type_land_form_rbutton.isChecked():
            formula_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            if state == Qt.Checked:
                land_forms = self.session.query(ClLandForm).all()
            else:
                land_forms = self.session.query(ClLandForm) \
                    .join(PsFormulaTypeLandForm, ClLandForm.code == PsFormulaTypeLandForm.land_form) \
                    .filter(PsFormulaTypeLandForm.formula_type == formula_type).all()
            formula_land_forms = self.session.query(PsFormulaTypeLandForm).all()
            for type in land_forms:
                self.connect_type_twidget.insertRow(count)
                item = QTableWidgetItem()
                item.setCheckState(Qt.Unchecked)
                for form in formula_land_forms:
                    if type.code == form.land_form and form.formula_type == formula_type:
                        item.setCheckState(Qt.Checked)
                        # item.setBackground(Qt.blue)
                self.connect_type_twidget.setItem(count, 0, item)

                item = QTableWidgetItem(type.description)
                item.setData(Qt.UserRole, type.code)
                self.connect_type_twidget.setItem(count, 1, item)
                count += 1

    def __save_codelist_settings(self):

        if self.app_type_pasture_type_rbutton.isChecked():
            app_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            for row in range(self.connect_type_twidget.rowCount()):
                check_item = self.connect_type_twidget.item(row, 0)
                pasture_code = self.connect_type_twidget.item(row, 1).data(Qt.UserRole)
                is_count = self.session.query(PsApplicationTypePastureType) \
                    .filter(PsApplicationTypePastureType.app_type == app_type) \
                    .filter(PsApplicationTypePastureType.pasture_type == pasture_code).count()
                if check_item.checkState() == Qt.Checked:
                    if is_count == 0:
                        app_pasture = PsApplicationTypePastureType()
                        app_pasture.app_type = app_type
                        app_pasture.pasture_type = pasture_code
                        self.session.add(app_pasture)
                else:
                    if is_count == 1:
                        self.session.query(PsApplicationTypePastureType) \
                            .filter(PsApplicationTypePastureType.app_type == app_type) \
                            .filter(PsApplicationTypePastureType.pasture_type == pasture_code).delete()
        elif self.app_type_doc_type_rbutton.isChecked():
            app_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            for row in range(self.connect_type_twidget.rowCount()):
                check_item = self.connect_type_twidget.item(row, 0)
                doc_code = self.connect_type_twidget.item(row, 1).data(Qt.UserRole)
                is_count = self.session.query(PsApplicationTypeDocType) \
                    .filter(PsApplicationTypeDocType.app_type == app_type) \
                    .filter(PsApplicationTypeDocType.document == doc_code).count()
                if check_item.checkState() == Qt.Checked:
                    if is_count == 0:
                        app_doc = PsApplicationTypeDocType()
                        app_doc.app_type = app_type
                        app_doc.document = doc_code
                        self.session.add(app_doc)
                else:
                    if is_count == 1:
                        self.session.query(PsApplicationTypeDocType) \
                            .filter(PsApplicationTypeDocType.app_type == app_type) \
                            .filter(PsApplicationTypeDocType.document == doc_code).delete()
        elif self.contract_doc_type_rbutton.isChecked():
            app_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            for row in range(self.connect_type_twidget.rowCount()):
                check_item = self.connect_type_twidget.item(row, 0)
                doc_code = self.connect_type_twidget.item(row, 1).data(Qt.UserRole)
                is_count = self.session.query(PsContractDocType) \
                    .filter(PsContractDocType.app_type == app_type) \
                    .filter(PsContractDocType.document == doc_code).count()
                if check_item.checkState() == Qt.Checked:
                    if is_count == 0:
                        app_doc = PsContractDocType()
                        app_doc.app_type = app_type
                        app_doc.document = doc_code
                        self.session.add(app_doc)
                else:
                    if is_count == 1:
                        self.session.query(PsContractDocType) \
                            .filter(PsContractDocType.app_type == app_type) \
                            .filter(PsContractDocType.document == doc_code).delete()
        elif self.natural_zone_land_form_rbutton.isChecked():
            natural_zone = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            for row in range(self.connect_type_twidget.rowCount()):
                check_item = self.connect_type_twidget.item(row, 0)
                land_form = self.connect_type_twidget.item(row, 1).data(Qt.UserRole)
                is_count = self.session.query(PsNaturalZoneLandForm) \
                    .filter(PsNaturalZoneLandForm.natural_zone == natural_zone) \
                    .filter(PsNaturalZoneLandForm.land_form == land_form).count()
                if check_item.checkState() == Qt.Checked:
                    if is_count == 0:
                        natural_zone_land_from = PsNaturalZoneLandForm()
                        natural_zone_land_from.natural_zone = natural_zone
                        natural_zone_land_from.land_form = land_form
                        self.session.add(natural_zone_land_from)
                else:
                    if is_count == 1:
                        self.session.query(PsNaturalZoneLandForm) \
                            .filter(PsNaturalZoneLandForm.natural_zone == natural_zone) \
                            .filter(PsNaturalZoneLandForm.land_form == land_form).delete()
        elif self.formula_type_land_form_rbutton.isChecked():
            formula_type = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            for row in range(self.connect_type_twidget.rowCount()):
                check_item = self.connect_type_twidget.item(row, 0)
                land_form = self.connect_type_twidget.item(row, 1).data(Qt.UserRole)
                is_count = self.session.query(PsFormulaTypeLandForm) \
                    .filter(PsFormulaTypeLandForm.formula_type == formula_type) \
                    .filter(PsFormulaTypeLandForm.land_form == land_form).count()
                if check_item.checkState() == Qt.Checked:
                    if is_count == 0:
                        formula_type_land_from = PsFormulaTypeLandForm()
                        formula_type_land_from.formula_type = formula_type
                        formula_type_land_from.land_form = land_form
                        self.session.add(formula_type_land_from)
                else:
                    if is_count == 1:
                        self.session.query(PsFormulaTypeLandForm) \
                            .filter(PsFormulaTypeLandForm.formula_type == formula_type) \
                            .filter(PsFormulaTypeLandForm.land_form == land_form).delete()
        elif self.natural_zone_land_plants_rbutton.isChecked():
            natural_zone = self.base_type.itemData(self.base_type.currentIndex(), Qt.UserRole)
            for row in range(self.connect_type_twidget.rowCount()):
                check_item = self.connect_type_twidget.item(row, 0)
                plants = self.connect_type_twidget.item(row, 1).data(Qt.UserRole)
                is_count = self.session.query(PsNaturalZonePlants) \
                    .filter(PsNaturalZonePlants.natural_zone == natural_zone) \
                    .filter(PsNaturalZonePlants.plants == plants).count()
                if check_item.checkState() == Qt.Checked:
                    if is_count == 0:
                        natural_zone_land_from = PsNaturalZonePlants()
                        natural_zone_land_from.natural_zone = natural_zone
                        natural_zone_land_from.plants = plants
                        self.session.add(natural_zone_land_from)
                else:
                    if is_count == 1:
                        self.session.query(PsNaturalZonePlants) \
                            .filter(PsNaturalZonePlants.natural_zone == natural_zone) \
                            .filter(PsNaturalZonePlants.plants == plants).delete()
        elif self.live_stock_convert_rbutton.isChecked():

            for row in range(self.live_stock_convert_twidget.rowCount()):
                item = self.live_stock_convert_twidget.item(row, 0)
                live_stock_type = item.data(Qt.UserRole)
                item_value = self.live_stock_convert_twidget.item(row, 1)
                convert_value = float(item_value.text())

                is_count = self.session.query(PsLiveStockConvert) \
                    .filter(PsLiveStockConvert.live_stock_type == live_stock_type).count()

                if is_count == 0:
                    live_stock_convert = PsLiveStockConvert()
                    live_stock_convert.live_stock_type = live_stock_type
                    live_stock_convert.convert_value = convert_value
                    self.session.add(live_stock_convert)

                if is_count == 1:
                    live_stock_convert = self.session.query(PsLiveStockConvert) \
                        .filter(PsLiveStockConvert.live_stock_type == live_stock_type).one()

                    live_stock_convert.convert_value = convert_value

    @pyqtSlot()
    def on_formula_add_button_clicked(self):

        selected_items = self.land_form_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose land form!!!"))
            return

        natural_zone_code = self.natural_zone_cbox.itemData(self.natural_zone_cbox.currentIndex())
        natural_zone = self.session.query(ClNaturalZone).filter(ClNaturalZone.code == natural_zone_code).one()

        current_row = self.land_form_twidget.currentRow()
        item = self.land_form_twidget.item(current_row, 0)
        land_form_code = item.data(Qt.UserRole)
        land_form = self.session.query(ClLandForm).filter(ClLandForm.code == land_form_code).one()

        rc_id = self.recovery_class_cbox.itemData(self.recovery_class_cbox.currentIndex())
        rc = self.session.query(PsRecoveryClass).filter(PsRecoveryClass.id == rc_id).one()
        plants_code = self.plants_cbox.itemData(self.plants_cbox.currentIndex())
        plants = self.session.query(ClPastureValues).filter(ClPastureValues.code == plants_code).one()
        symbol_code = self.less_symbol_cbox.itemData(self.less_symbol_cbox.currentIndex())
        symbol = self.session.query(PClLessSymbol).filter(PClLessSymbol.code == symbol_code).one()
        precent_value = self.precent_value_sbox.value()

        ps_pasture_status_formula_count = self.session.query(PsPastureStatusFormula). \
            filter(PsPastureStatusFormula.natural_zone == natural_zone_code). \
            filter(PsPastureStatusFormula.land_form == land_form_code). \
            filter(PsPastureStatusFormula.plants == plants_code). \
            filter(PsPastureStatusFormula.rc_id == rc_id).count()
        if ps_pasture_status_formula_count > 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("This Plants registered!!!"))
            return

        row = self.formula_twidget.rowCount()
        self.formula_twidget.insertRow(row)

        item = QTableWidgetItem(str(rc.rc_code))
        item.setData(Qt.UserRole, rc.id)
        self.formula_twidget.setItem(row, 0, item)

        item = QTableWidgetItem(unicode(plants.description))
        item.setData(Qt.UserRole, plants.code)
        self.formula_twidget.setItem(row, 1, item)

        item = QTableWidgetItem(unicode(symbol.description))
        item.setData(Qt.UserRole, symbol.code)
        self.formula_twidget.setItem(row, 2, item)

        item = QTableWidgetItem(str(precent_value))
        item.setData(Qt.UserRole, precent_value)
        self.formula_twidget.setItem(row, 3, item)

        ps_pasture_status_rc = PsPastureStatusFormula()

        ps_pasture_status_rc.natural_zone = natural_zone_code
        ps_pasture_status_rc.natural_zone_ref = natural_zone
        ps_pasture_status_rc.plants = plants_code
        ps_pasture_status_rc.plants_ref = plants
        ps_pasture_status_rc.land_form = land_form_code
        ps_pasture_status_rc.land_form_ref = land_form
        ps_pasture_status_rc.rc_id = rc_id
        ps_pasture_status_rc.rc_id_ref = rc
        ps_pasture_status_rc.symbol_id = symbol_code
        ps_pasture_status_rc.symbol_id_ref = symbol
        ps_pasture_status_rc.cover_precent = precent_value

        self.session.add(ps_pasture_status_rc)

    @pyqtSlot()
    def on_formula_update_button_clicked(self):

        selected_items = self.formula_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose pasture formula!!!"))
            return

        selected_items = self.land_form_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose pasture land form!!!"))
            return

        natural_zone_code = self.natural_zone_cbox.itemData(self.natural_zone_cbox.currentIndex())
        natural_zone = self.session.query(ClNaturalZone).filter(ClNaturalZone.code == natural_zone_code).one()

        current_row = self.land_form_twidget.currentRow()
        item = self.land_form_twidget.item(current_row, 0)
        land_form_code = item.data(Qt.UserRole)
        land_form = self.session.query(ClLandForm).filter(ClLandForm.code == land_form_code).one()

        rc_id = self.recovery_class_cbox.itemData(self.recovery_class_cbox.currentIndex())
        rc_text = self.recovery_class_cbox.currentText()
        rc = self.session.query(PsRecoveryClass).filter(PsRecoveryClass.id == rc_id).one()

        plants_code = self.plants_cbox.itemData(self.plants_cbox.currentIndex())
        plants = self.session.query(ClPastureValues).filter(ClPastureValues.code == plants_code).one()

        symbol_code = self.less_symbol_cbox.itemData(self.less_symbol_cbox.currentIndex())
        symbol = self.session.query(PClLessSymbol).filter(PClLessSymbol.code == symbol_code).one()

        current_row = self.formula_twidget.currentRow()
        rc_item = self.formula_twidget.item(current_row, 0)
        plants_item = self.formula_twidget.item(current_row, 1)
        symbol_item = self.formula_twidget.item(current_row, 2)
        value_item = self.formula_twidget.item(current_row, 3)

        rc_item.setText(unicode(rc_text))
        rc_item.setData(Qt.UserRole, rc_id)

        plants_item.setText(unicode(plants.description))
        plants_item.setData(Qt.UserRole, plants.code)

        symbol_item.setText(unicode(symbol.description))
        symbol_item.setData(Qt.UserRole, symbol.code)

        value_item.setText(str(self.precent_value_sbox.value()))
        value_item.setData(Qt.UserRole, self.precent_value_sbox.value())

        ps_pasture_status_formula_count = self.session.query(PsPastureStatusFormula).\
            filter(PsPastureStatusFormula.natural_zone == natural_zone_code). \
            filter(PsPastureStatusFormula.land_form == land_form_code). \
            filter(PsPastureStatusFormula.plants == plants_code). \
            filter(PsPastureStatusFormula.rc_id == rc_id).count()

        if ps_pasture_status_formula_count == 1:
            ps_pasture_status_rc = self.session.query(PsPastureStatusFormula). \
                filter(PsPastureStatusFormula.natural_zone == natural_zone_code). \
                filter(PsPastureStatusFormula.land_form == land_form_code). \
                filter(PsPastureStatusFormula.plants == plants_code). \
                filter(PsPastureStatusFormula.rc_id == rc_id).one()

            ps_pasture_status_rc.plants = plants_code
            ps_pasture_status_rc.plants_ref = plants
            ps_pasture_status_rc.symbol_id = symbol_code
            ps_pasture_status_rc.symbol_id_ref = symbol
            ps_pasture_status_rc.cover_precent = self.precent_value_sbox.value()
        else:
            ps_pasture_status_rc = PsPastureStatusFormula()
            ps_pasture_status_rc.natural_zone = natural_zone_code
            ps_pasture_status_rc.natural_zone_ref = natural_zone
            ps_pasture_status_rc.plants = plants_code
            ps_pasture_status_rc.plants_ref = plants
            ps_pasture_status_rc.land_form = land_form_code
            ps_pasture_status_rc.land_form_ref = land_form
            ps_pasture_status_rc.rc_id = rc_id
            ps_pasture_status_rc.rc_id_ref = rc
            ps_pasture_status_rc.symbol_id = symbol_code
            ps_pasture_status_rc.symbol_id_ref = symbol
            ps_pasture_status_rc.cover_precent = self.precent_value_sbox.value()

            self.session.add(ps_pasture_status_rc)

    @pyqtSlot()
    def on_formula_delete_button_clicked(self):

        selected_items = self.formula_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose pasture formula!!!"))
            return

        selected_items = self.land_form_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose pasture land form!!!"))
            return

        natural_zone_code = self.natural_zone_cbox.itemData(self.natural_zone_cbox.currentIndex())

        current_row = self.land_form_twidget.currentRow()
        item = self.land_form_twidget.item(current_row, 0)
        land_form_code = item.data(Qt.UserRole)

        current_row = self.formula_twidget.currentRow()
        item = self.formula_twidget.item(current_row, 0)
        rc_id = item.data(Qt.UserRole)

        item = self.formula_twidget.item(current_row, 1)
        plants = item.data(Qt.UserRole)

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to delete the all information for point ?"))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        ps_pasture_status_formula_count = self.session.query(PsPastureStatusFormula). \
                filter(PsPastureStatusFormula.natural_zone == natural_zone_code). \
                filter(PsPastureStatusFormula.land_form == land_form_code). \
                filter(PsPastureStatusFormula.plants == plants).\
                filter(PsPastureStatusFormula.rc_id == rc_id).count()

        if ps_pasture_status_formula_count == 1:
            self.session.query(PsPastureStatusFormula). \
                filter(PsPastureStatusFormula.natural_zone == natural_zone_code). \
                filter(PsPastureStatusFormula.land_form == land_form_code). \
                filter(PsPastureStatusFormula.plants == plants). \
                filter(PsPastureStatusFormula.rc_id == rc_id).delete()

        selected_row = self.formula_twidget.currentRow()
        self.formula_twidget.removeRow(selected_row)

    @pyqtSlot(int)
    def on_recovery_class_cbox_currentIndexChanged(self, index):

        if self.recovery_class_cbox.currentIndex() == -1:
            return

        self.formula_twidget.setRowCount(0)
        rc_id = self.recovery_class_cbox.itemData(self.recovery_class_cbox.currentIndex())

        natural_zone_code = self.natural_zone_cbox.itemData(self.natural_zone_cbox.currentIndex())

        current_row = self.land_form_twidget.currentRow()
        item = self.land_form_twidget.item(current_row, 0)
        land_form_code = item.data(Qt.UserRole)

        ps_pasture_status_formulas = self.session.query(PsPastureStatusFormula). \
            filter(PsPastureStatusFormula.natural_zone == natural_zone_code). \
            filter(PsPastureStatusFormula.land_form == land_form_code). \
            filter(PsPastureStatusFormula.rc_id == rc_id).all()

        count = 0
        for ps_pasture_status_formula in ps_pasture_status_formulas:
            rc_id = ps_pasture_status_formula.rc_id
            rc = self.session.query(PsRecoveryClass).filter(PsRecoveryClass.id == rc_id).one()

            plants_code = ps_pasture_status_formula.plants
            plants = self.session.query(ClPastureValues).filter(ClPastureValues.code == plants_code).one()

            symbol_code = ps_pasture_status_formula.symbol_id
            symbol = self.session.query(PClLessSymbol).filter(PClLessSymbol.code == symbol_code).one()

            self.formula_twidget.insertRow(count)

            item = QTableWidgetItem(str(rc.rc_code))
            item.setData(Qt.UserRole, rc.id)
            self.formula_twidget.setItem(count, 0, item)

            item = QTableWidgetItem(unicode(plants.description))
            item.setData(Qt.UserRole, plants.code)
            self.formula_twidget.setItem(count, 1, item)

            item = QTableWidgetItem(unicode(symbol.description))
            item.setData(Qt.UserRole, symbol.code)
            self.formula_twidget.setItem(count, 2, item)

            item = QTableWidgetItem(str(ps_pasture_status_formula.cover_precent))
            item.setData(Qt.UserRole, ps_pasture_status_formula.cover_precent)
            self.formula_twidget.setItem(count, 3, item)
            count += 1

    @pyqtSlot(QTableWidgetItem)
    def on_land_form_twidget_itemClicked(self, item):

        current_row = self.land_form_twidget.currentRow()
        if current_row == -1:
            return

        self.recovery_class_comp_cbox.clear()
        self.recovery_class_cbox.clear()
        recovery_classes = self.session.query(PsRecoveryClass).all()
        for recovery_class in recovery_classes:
            self.recovery_class_cbox.addItem(recovery_class.rc_code, recovery_class.id)
            self.recovery_class_comp_cbox.addItem(recovery_class.rc_code, recovery_class.id)

        item = self.land_form_twidget.item(current_row, 0)
        land_form_code = item.data(Qt.UserRole)
        land_form = self.session.query(ClLandForm).filter(ClLandForm.code == land_form_code).one()
        self.__visible_tab(land_form_code)

    def __visible_tab(self,land_form_code):

        self.formula_tab_widget.removeTab(self.formula_tab_widget.indexOf(self.formula_precent_tab))
        self.formula_tab_widget.removeTab(self.formula_tab_widget.indexOf(self.formula_comparison_tab))

        formula_types = self.session.query(PsFormulaTypeLandForm.formula_type).\
            filter(PsFormulaTypeLandForm.land_form == land_form_code).group_by(PsFormulaTypeLandForm.formula_type).all()
        for formula_type in formula_types:
            if formula_type.formula_type == 1:
                self.formula_tab_widget.insertTab(self.formula_tab_widget.count()-1, self.formula_precent_tab,
                                                  self.tr("RC Precent"))
            if formula_type.formula_type == 2:
                self.formula_tab_widget.insertTab(self.formula_tab_widget.count(), self.formula_comparison_tab,
                                                  self.tr("RC Comparison"))

    @pyqtSlot(QTableWidgetItem)
    def on_formula_twidget_itemClicked(self, item):

        current_row = self.formula_twidget.currentRow()
        if current_row == -1:
            return

    @pyqtSlot(int)
    def on_soil_evaluation_chbox_stateChanged(self, state):

        if state == Qt.Checked:
            self.soil_evaluation_cbox.setEnabled(True)
            self.add_comparison_button.setEnabled(False)
            self.formula_more_twidget.setEnabled(False)
            self.formula_less_twidget.setEnabled(False)
            self.more_delete_button.setEnabled(False)
            self.less_delete_button.setEnabled(False)
        else:
            self.soil_evaluation_cbox.setEnabled(False)
            self.add_comparison_button.setEnabled(True)
            self.formula_more_twidget.setEnabled(True)
            self.formula_less_twidget.setEnabled(True)
            self.more_delete_button.setEnabled(True)
            self.less_delete_button.setEnabled(True)

    @pyqtSlot()
    def on_add_comparison_button_clicked(self):

        selected_items = self.land_form_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose land form!!!"))
            return

        natural_zone_code = self.natural_zone_cbox.itemData(self.natural_zone_cbox.currentIndex())
        natural_zone = self.session.query(ClNaturalZone).filter(ClNaturalZone.code == natural_zone_code).one()

        current_row = self.land_form_twidget.currentRow()
        item = self.land_form_twidget.item(current_row, 0)
        land_form_code = item.data(Qt.UserRole)
        land_form = self.session.query(ClLandForm).filter(ClLandForm.code == land_form_code).one()

        rc_id = self.recovery_class_comp_cbox.itemData(self.recovery_class_comp_cbox.currentIndex())
        rc = self.session.query(PsRecoveryClass).filter(PsRecoveryClass.id == rc_id).one()
        plants_code = self.plants_comp_cbox.itemData(self.plants_comp_cbox.currentIndex())
        plants = self.session.query(ClPastureValues).filter(ClPastureValues.code == plants_code).one()
        symbol_code = self.less_symbol_comp_cbox.itemData(self.less_symbol_comp_cbox.currentIndex())
        symbol = self.session.query(PClLessSymbol).filter(PClLessSymbol.code == symbol_code).one()

        ps_pasture_status_formula_count = self.session.query(PsPastureComparisonFormula). \
            filter(PsPastureComparisonFormula.natural_zone == natural_zone_code). \
            filter(PsPastureComparisonFormula.land_form == land_form_code). \
            filter(PsPastureComparisonFormula.plants == plants_code). \
            filter(PsPastureComparisonFormula.rc_id == rc_id).count()
        if ps_pasture_status_formula_count > 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("This Plants registered!!!"))
            return

        if symbol_code == 1:

            row = self.formula_more_twidget.rowCount()
            self.formula_more_twidget.insertRow(row)

            item = QTableWidgetItem(unicode(plants.description))
            item.setData(Qt.UserRole, plants.code)
            item.setData(Qt.UserRole+1, rc_id)
            self.formula_more_twidget.setItem(row, 0, item)

        if symbol_code == 2:

            row = self.formula_less_twidget.rowCount()
            self.formula_less_twidget.insertRow(row)

            item = QTableWidgetItem(unicode(plants.description))
            item.setData(Qt.UserRole, plants.code)
            item.setData(Qt.UserRole + 1, rc_id)
            self.formula_less_twidget.setItem(row, 0, item)

        ps_pasture_status_rc = PsPastureComparisonFormula()

        ps_pasture_status_rc.natural_zone = natural_zone_code
        ps_pasture_status_rc.natural_zone_ref = natural_zone
        ps_pasture_status_rc.plants = plants_code
        ps_pasture_status_rc.plants_ref = plants
        ps_pasture_status_rc.land_form = land_form_code
        ps_pasture_status_rc.land_form_ref = land_form
        ps_pasture_status_rc.rc_id = rc_id
        ps_pasture_status_rc.rc_id_ref = rc
        ps_pasture_status_rc.symbol_id = symbol_code
        ps_pasture_status_rc.symbol_id_ref = symbol

        self.session.add(ps_pasture_status_rc)

    @pyqtSlot()
    def on_more_delete_button_clicked(self):

        selected_items = self.formula_more_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose pasture formula!!!"))
            return

        selected_items = self.land_form_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose pasture land form!!!"))
            return

        natural_zone_code = self.natural_zone_cbox.itemData(self.natural_zone_cbox.currentIndex())

        current_row = self.land_form_twidget.currentRow()
        item = self.land_form_twidget.item(current_row, 0)
        land_form_code = item.data(Qt.UserRole)

        current_row = self.formula_more_twidget.currentRow()
        item = self.formula_more_twidget.item(current_row, 0)
        plants = item.data(Qt.UserRole)

        item = self.formula_more_twidget.item(current_row, 0)
        rc_id = item.data(Qt.UserRole+1)

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to delete the all information for point ?"))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        ps_pasture_status_formula_count = self.session.query(PsPastureComparisonFormula). \
            filter(PsPastureComparisonFormula.natural_zone == natural_zone_code). \
            filter(PsPastureComparisonFormula.land_form == land_form_code). \
            filter(PsPastureComparisonFormula.plants == plants). \
            filter(PsPastureComparisonFormula.rc_id == rc_id).count()

        if ps_pasture_status_formula_count == 1:
            self.session.query(PsPastureComparisonFormula). \
                filter(PsPastureComparisonFormula.natural_zone == natural_zone_code). \
                filter(PsPastureComparisonFormula.land_form == land_form_code). \
                filter(PsPastureComparisonFormula.plants == plants). \
                filter(PsPastureComparisonFormula.rc_id == rc_id).delete()

        selected_row = self.formula_more_twidget.currentRow()
        self.formula_more_twidget.removeRow(selected_row)

    @pyqtSlot()
    def on_less_delete_button_clicked(self):

        selected_items = self.formula_less_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose pasture formula!!!"))
            return

        selected_items = self.land_form_twidget.selectedItems()
        if len(selected_items) == 0:
            PluginUtils.show_message(self, self.tr("Selection"), self.tr("Please choose pasture land form!!!"))
            return

        natural_zone_code = self.natural_zone_cbox.itemData(self.natural_zone_cbox.currentIndex())

        current_row = self.land_form_twidget.currentRow()
        item = self.land_form_twidget.item(current_row, 0)
        land_form_code = item.data(Qt.UserRole)

        current_row = self.formula_less_twidget.currentRow()
        item = self.formula_less_twidget.item(current_row, 0)
        plants = item.data(Qt.UserRole)

        item = self.formula_less_twidget.item(current_row, 0)
        rc_id = item.data(Qt.UserRole + 1)

        message_box = QMessageBox()
        message_box.setText(self.tr("Do you want to delete the all information for point ?"))

        delete_button = message_box.addButton(self.tr("Delete"), QMessageBox.ActionRole)
        message_box.addButton(self.tr("Cancel"), QMessageBox.ActionRole)
        message_box.exec_()

        if not message_box.clickedButton() == delete_button:
            return

        ps_pasture_status_formula_count = self.session.query(PsPastureComparisonFormula). \
            filter(PsPastureComparisonFormula.natural_zone == natural_zone_code). \
            filter(PsPastureComparisonFormula.land_form == land_form_code). \
            filter(PsPastureComparisonFormula.plants == plants). \
            filter(PsPastureComparisonFormula.rc_id == rc_id).count()

        if ps_pasture_status_formula_count == 1:
            self.session.query(PsPastureComparisonFormula). \
                filter(PsPastureComparisonFormula.natural_zone == natural_zone_code). \
                filter(PsPastureComparisonFormula.land_form == land_form_code). \
                filter(PsPastureComparisonFormula.plants == plants). \
                filter(PsPastureComparisonFormula.rc_id == rc_id).delete()

        selected_row = self.formula_less_twidget.currentRow()
        self.formula_less_twidget.removeRow(selected_row)

    @pyqtSlot(int)
    def on_recovery_class_comp_cbox_currentIndexChanged(self, index):

        if self.recovery_class_comp_cbox.currentIndex() == -1:
            return

        self.formula_more_twidget.setRowCount(0)
        self.formula_less_twidget.setRowCount(0)
        rc_id = self.recovery_class_comp_cbox.itemData(self.recovery_class_comp_cbox.currentIndex())

        natural_zone_code = self.natural_zone_cbox.itemData(self.natural_zone_cbox.currentIndex())

        current_row = self.land_form_twidget.currentRow()
        item = self.land_form_twidget.item(current_row, 0)
        land_form_code = item.data(Qt.UserRole)

        ps_pasture_status_formulas = self.session.query(PsPastureComparisonFormula). \
            filter(PsPastureComparisonFormula.natural_zone == natural_zone_code). \
            filter(PsPastureComparisonFormula.land_form == land_form_code). \
            filter(PsPastureComparisonFormula.rc_id == rc_id).all()

        count = 0
        count_less = 0
        for ps_pasture_status_formula in ps_pasture_status_formulas:
            rc_id = ps_pasture_status_formula.rc_id
            rc = self.session.query(PsRecoveryClass).filter(PsRecoveryClass.id == rc_id).one()

            plants_code = ps_pasture_status_formula.plants
            plants = self.session.query(ClPastureValues).filter(ClPastureValues.code == plants_code).one()

            symbol_code = ps_pasture_status_formula.symbol_id
            symbol = self.session.query(PClLessSymbol).filter(PClLessSymbol.code == symbol_code).one()

            if symbol_code == 1:
                self.formula_more_twidget.insertRow(count)

                item = QTableWidgetItem(unicode(plants.description))
                item.setData(Qt.UserRole, plants.code)
                item.setData(Qt.UserRole+1, rc_id)
                self.formula_more_twidget.setItem(count, 0, item)

                count += 1
            if symbol_code == 2:
                self.formula_less_twidget.insertRow(count_less)

                item = QTableWidgetItem(unicode(plants.description))
                item.setData(Qt.UserRole, plants.code)
                item.setData(Qt.UserRole + 1, rc_id)
                self.formula_less_twidget.setItem(count_less, 0, item)

                count_less += 1

        evaluation_formula_count = self.session.query(PsPastureEvaluationFormula).\
            filter(PsPastureEvaluationFormula.rc_id == rc_id). \
            filter(PsPastureEvaluationFormula.natural_zone == natural_zone_code). \
            filter(PsPastureEvaluationFormula.land_form == land_form_code).count()
        if evaluation_formula_count == 1:
            evaluation_formula = self.session.query(PsPastureEvaluationFormula). \
                filter(PsPastureEvaluationFormula.rc_id == rc_id). \
                filter(PsPastureEvaluationFormula.natural_zone == natural_zone_code). \
                filter(PsPastureEvaluationFormula.land_form == land_form_code).one()

            self.soil_evaluation_cbox.setCurrentIndex(self.soil_evaluation_cbox.findData(evaluation_formula.soil_evaluation))
            self.soil_evaluation_chbox.setChecked(True)
        else:
            self.soil_evaluation_chbox.setChecked(False)