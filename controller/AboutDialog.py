__author__ = 'anna'
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ..view.Ui_AboutDialog import *
from ..model import Constants
from ..utils.SessionHandler import SessionHandler


class AboutDialog(QDialog, Ui_AboutDialog):

    def __init__(self, parent=None):

        super(AboutDialog,  self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(self.tr("About Landmanager II"))
        self.version_label.setText(Constants.VERSION)

        session = SessionHandler().session_instance()

        sql = "select a.text, sum(a.count) from (select 'application', text, count(text) from logging.ct_application  group by text " \
              "UNION " \
                    "select 'contract', text, count(text) from logging.ct_contract  group by text" \
              " UNION " \
                    "select 'parcels', text, count(text) from logging.ca_parcel_tbl  group by text" \
              " UNION " \
                    "select 'person', text, count(text) from logging.bs_person  group by text" \
              " UNION " \
                    "select 'building', text, count(text) from logging.ca_building_tbl  group by text" \
              " UNION " \
                    "select 'decision', text, count(text) from logging.ct_decision  group by text" \
              " UNION " \
                    "select 'fee', text, count(text) from logging.ct_fee  group by text" \
              " UNION " \
                    "select 'record', text, count(text) from logging.ct_ownership_record  group by text" \
              " UNION " \
                    "select 'tax', text, count(text) from logging.ct_tax_and_price group by text) as a group by a.text order by sum desc;" \

        result = session.execute(sql).fetchall()
        length = len(result)
        for item in result:
            row = self.officer_twidget.rowCount()
            self.officer_twidget.insertRow(row)

            name_item = QTableWidgetItem(item[0])
            if row == 0:
                name_item.setIcon(QIcon(":/plugins/lm2/crown.png"))
            if row == length-1:
                name_item.setIcon(QIcon(":/plugins/lm2/fatcow.png"))

            count_item = QTableWidgetItem(str(item[1]))
            self.officer_twidget.setItem(row, 1, count_item)
            self.officer_twidget.setItem(row, 0, name_item)

        self.officer_twidget.setColumnWidth(0, 160)
        self.officer_twidget.setColumnWidth(1, 160)

        self.officer_twidget.setAlternatingRowColors(True)
        self.officer_twidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.officer_twidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.officer_twidget.verticalHeader().setVisible(False)


    @pyqtSlot()
    def on_close_button_clicked(self):

        self.reject()