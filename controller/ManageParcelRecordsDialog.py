__author__ = 'Ankhbold'
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from sqlalchemy.exc import SQLAlchemyError
from ..model.VaTypeParcel import *
from ..view.Ui_ManageParcelRecordsDialog import *
from ..utils.LayerUtils import LayerUtils
from ..utils.PluginUtils import *
from ..utils.SessionHandler import SessionHandler

from ..controller.ParcelRecordDialog import *
import sys

class ManageParcelRecordsDialog(QDialog, Ui_ManageParcelRecordsDialog):

    def __init__(self, parent=None):

        super(ManageParcelRecordsDialog,  self).__init__(parent)
        self.setupUi(self)
        self.closeButton.clicked.connect(self.reject)
        self.__select_feature()
        self.__setup_combo_boxes()
        self.__setup_record_widget()

    def __setup_record_widget(self):

        self.record_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.record_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.record_twidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def __setup_combo_boxes(self):

        session = SessionHandler().session_instance()
        parcelTypeList = []

        restrictions = DatabaseUtils.working_l2_code()
        parcelLayer = LayerUtils.layer_by_data_source("s" + restrictions, "ca_parcel")
        select_feature = parcelLayer.selectedFeatures()

        for feature in select_feature:
            attr = feature.attributes()
            parcel_id = attr[0]

        try:
            session = SessionHandler().session_instance()
            parcel = session.query(CaParcel).filter(CaParcel.parcel_id == parcel_id).one()
            if parcel.landuse != None:
                landuse = session.query(ClLanduseType).filter(ClLanduseType.code == parcel.landuse).one()

                if parcel.landuse == 2204 or parcel.landuse == 2205 or parcel.landuse == 2206:
                    parcelTypeList = session.query(VaTypeParcel).filter(VaTypeParcel.code == 10).all()
                elif landuse.code2 == 11 or landuse.code2 == 12 or landuse.code2 == 13 or landuse.code2 == 14 \
                        or landuse.code2 == 15 or landuse.code2 == 16 or landuse.code2 == 17:
                    parcelTypeList = session.query(VaTypeParcel).filter(VaTypeParcel.code == 40).all()
                elif landuse.code2 == 21 or landuse.code2 == 24 or landuse.code2 == 25 or landuse.code == 2201 \
                        or landuse.code == 2202 or landuse.code == 2203:
                    parcelTypeList = session.query(VaTypeParcel).filter(VaTypeParcel.code == 20).all()
                elif landuse.code2 == 23 or landuse.code2 == 26:
                    parcelTypeList = session.query(VaTypeParcel).filter(VaTypeParcel.code == 30).all()
                else:
                    self.addButton.setEnabled(False)
                    self.editButton.setEnabled(False)
                    self.deleteButton.setEnabled(False)
        except SQLAlchemyError, e:
            QMessageBox.information(self, QApplication.translate("LM2", "Sql Error"), e.message)

        for parceltype in parcelTypeList:
            self.parcel_type_cbox.addItem(parceltype.description, parceltype.code)

    parcel_id = None
    def __select_feature(self):

        restrictions = DatabaseUtils.working_l2_code()
        parcelLayer = LayerUtils.layer_by_data_source("s" + restrictions, "ca_parcel")
        select_feature = parcelLayer.selectedFeatures()
        count = parcelLayer.selectedFeatureCount()
        if count != 1:
            PluginUtils.show_message(self,self.tr("No select parcel"),self.tr("No select parcel"))
            self.addButton.setEnabled(False)
            self.editButton.setEnabled(False)
            self.deleteButton.setEnabled(False)
            self.parcel_type_cbox.clear()
            self.parcel_type_cbox.setEnabled(False)
            return
        for feature in select_feature:
            attr = feature.attributes()
            parcel_id = attr[0]

        session = SessionHandler().session_instance()

        home_parcel = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.parcel_id == parcel_id).all()

        count = 0
        for valuation in home_parcel:

            if valuation.purchase_or_lease_type == 10:
                purchase_type = session.query(VaTypePurchaseOrLease).filter(VaTypePurchaseOrLease.code == valuation.purchase_or_lease_type).one()
                purchase_count = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == valuation.register_no).count()
                if purchase_count == 0:
                    record_data = "["+ valuation.register_no +"] "+ str(valuation.info_date) +" [ "+ purchase_type.description +"  ] "+ "no price"
                    record_item = QTableWidgetItem(record_data)
                    record_item.setData(Qt.UserRole, valuation.register_no)
                else:
                    purchase = session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == valuation.register_no).one()
                    record_data = "["+ valuation.register_no +"] "+ str(valuation.info_date) +" [ "+ purchase_type.description +"  ] "+ str(purchase.price)
                    record_item = QTableWidgetItem(record_data)
                    record_item.setData(Qt.UserRole, valuation.register_no)

                self.record_twidget.insertRow(count)
                self.record_twidget.setItem(count, 0, record_item)
            else:
                lease_type = session.query(VaTypePurchaseOrLease).filter(VaTypePurchaseOrLease.code == valuation.purchase_or_lease_type).one()
                lease_count = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == valuation.register_no).count()
                if lease_count == 0:
                    record_data = "["+ valuation.register_no +"] "+ str(valuation.info_date) +" [ "+ lease_type.description +"  ] "+ "no price"
                    record_item = QTableWidgetItem(record_data)
                    record_item.setData(Qt.UserRole, valuation.register_no)
                else:
                    lease = session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == valuation.register_no).one()
                    purchase_type = session.query(VaTypePurchaseOrLease).filter(VaTypePurchaseOrLease.code == valuation.purchase_or_lease_type).one()
                    record_data = "[" + valuation.register_no +"] "+ str(valuation.info_date) +" ["+ purchase_type.description +"] "+ str(lease.monthly_rent)
                    record_item = QTableWidgetItem(record_data)
                    record_item.setData(Qt.UserRole, valuation.register_no)
                self.record_twidget.insertRow(count)
                self.record_twidget.setItem(count, 0, record_item)

    @pyqtSignature("")
    def on_addButton_clicked(self):

        record = VaInfoHomeParcel()
        parcel_type = self.parcel_type_cbox.itemData(self.parcel_type_cbox.currentIndex())
        restrictions = DatabaseUtils.working_l2_code()
        parcelLayer = LayerUtils.layer_by_data_source("s" + restrictions, "ca_parcel")
        select_feature = parcelLayer.selectedFeatures()
        for feature in select_feature:
            attr = feature.attributes()
            parcel_id = attr[0]
        register_no = "00000-00-0000-00"
        dlg = ParcelRecordDialog(parcel_type, register_no, parcel_id, record)
        dlg.exec_()

    def __selected_record(self):

        session = SessionHandler().session_instance()
        if not len(self.record_twidget.selectedItems()) == 1:
            PluginUtils.show_message(self, self.tr("Selection Error"), self.tr("Select one item to start editing."))
            return

        selectedItem = self.record_twidget.selectedItems()[0]
        register_no = selectedItem.data(Qt.UserRole)
        record = None

        try:
            record = session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no == register_no).one()
        except SQLAlchemyError, e:
            session.rollback()
            PluginUtils.show_message(self, self.tr("LM2"), self.tr("Sql Error"), e.message)

        return record

    @pyqtSignature("")
    def on_editButton_clicked(self):

        record = self.__selected_record()
        if not record:
            return

        parcel_type = self.parcel_type_cbox.itemData(self.parcel_type_cbox.currentIndex())
        restrictions = DatabaseUtils.working_l2_code()
        parcelLayer = LayerUtils.layer_by_data_source("s" + restrictions, "ca_parcel")
        select_feature = parcelLayer.selectedFeatures()
        for feature in select_feature:
            attr = feature.attributes()
            parcel_id = attr[0]

        dlg = ParcelRecordDialog(parcel_type, record.register_no, parcel_id, record)
        dlg.exec_()

    @pyqtSlot()
    def on_deleteButton_clicked(self):

        session = SessionHandler().session_instance()

        msgBox = QMessageBox()
        msgBox.setText(self.tr("Do you want to delete?"))
        okButton = msgBox.addButton(self.tr("Yes"), QMessageBox.ActionRole)
        msgBox.addButton(self.tr("No"), QMessageBox.ActionRole)
        msgBox.setWindowFlags(Qt.WindowStaysOnTopHint)
        msgBox.exec_()
        if msgBox.clickedButton() == okButton:

            selected_row = self.record_twidget.currentRow()
            item = self.record_twidget.selectedItems()[0]
            selected_data = item.data(Qt.UserRole)
            self.record_twidget.removeRow(selected_row)

            session.query(VaInfoHomeParcel).filter(VaInfoHomeParcel.register_no == selected_data).delete()
            session.query(VaInfoHomeBuilding).filter(VaInfoHomeBuilding.register_no == selected_data).delete()
            if session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == selected_data).count() != 0:
                session.query(VaInfoHomePurchase).filter(VaInfoHomePurchase.register_no == selected_data).delete()
            if session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == selected_data).count() != 0:
                session.query(VaInfoHomeLease).filter(VaInfoHomeLease.register_no == selected_data).delete()
            session.commit()