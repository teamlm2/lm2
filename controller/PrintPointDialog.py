__author__ = 'anna'
# coding=utf8

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *
from qgis.core import *
from qgis.gui import *
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.exc import SQLAlchemyError
from geoalchemy2.elements import WKTElement
from sqlalchemy import func, or_, and_, desc
from ..view.Ui_PrintPointDialog import Ui_PrintPointDialog
from ..utils.PluginUtils import PluginUtils
from ..utils.LayerUtils import LayerUtils
from ..utils.DatabaseUtils import DatabaseUtils
from ..utils.SessionHandler import SessionHandler
from ..utils.PasturePath import *
from ..utils.FileUtils import FileUtils
from ..model.PsPointDetail import *
from ..model.CaPastureMonitoring import *
from ..model.PsPointDaatsValue import *
from ..model.PsPointDetailPoints import *
from ..model.CaPastureParcel import *
from ..model.CaPUGBoundary import *
from ..model.PsParcel import *
from ..model.PsPointPastureValue import *
from ..model.PsRecoveryClass import *
from ..model.CaBuilding import *
from ..model.CtApplication import *
from ..model.AuLevel1 import *
from ..model.AuLevel2 import *
from ..model.AuLevel3 import *
from ..model import SettingsConstants
from ..model import Constants
from ..model.SetRightTypeApplicationType import *
from ..model.LM2Exception import LM2Exception
from ..model.ClPositionType import *
from ..model.CtCadastrePage import *
from ..model.Enumerations import ApplicationType, UserRight
from ..model.SetCadastrePage import *
import math
import locale
import os

class PrintPointDialog(QDialog, Ui_PrintPointDialog):

    CODEIDCARD, FAMILYNAME, MIDDLENAME, FIRSTNAME, DATEOFBIRTH, CONTRACTNO, CONTRACTDATE = range(7)

    STREET_NAME = 7
    KHASHAA_NAME = 6
    GEO_ID = 2
    OLD_PARCEL_ID = 1

    def __init__(self, plugin, point_id, parent=None):

        super(PrintPointDialog,  self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.plugin = plugin
        self.point_id = point_id
        self.point_detail_id = str(self.point_id[:-2])

        self.session = SessionHandler().session_instance()
        self.setupUi(self)

        self.image_id = 0
        self.image_type = 0
        self.pixmap_size = None

        self.__label_setup()

        self.setWindowTitle("Image Viewer")
        # self.resize(500, 400)

        # self.open_button.setStyleSheet("""QToolTip {
        #                    background-color: black;
        #                    color: white;
        #                    border: black solid 1px
        #                    }""")
        # self.open_button.setStyleSheet("background: transparent;")
        self.zoomin_button.setStyleSheet("background: transparent;")
        self.zoomout_button.setStyleSheet("background: transparent;")
        self.fit_button.setStyleSheet("background: transparent;")
        self.print_button.setStyleSheet("background: transparent;")

        self.__point_detail_info()

    def __label_setup(self):

        self.printer = QPrinter()
        self.scaleFactor = 0.12

        # self.imageLabel = QLabel()

        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored,
                                      QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        # self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)
        # self.setCentralWidget(self.scrollArea)

        self.createActions()
        self.createMenus()

        self.land_form_label.setWordWrap(True)
        self.point_address_label.setWordWrap(True)
        self.point_address_label.setAlignment(Qt.AlignCenter)

        address_font = QFont()
        address_font.setBold(True)
        address_font.setItalic(True)
        address_font.setUnderline(True)
        address_font.setPointSize(10)

        self.point_address_label.setFont(address_font)

        self.rc_label.setStyleSheet('color: red')
        self.rc_label.setOpenExternalLinks(True)

        self.biomass_label.setStyleSheet('color: red')
        self.cover_label.setStyleSheet('color: red')

    def __point_detail_info(self):

        if self.point_detail_id:

            point_detail = self.session.query(PsPointDetail).filter(PsPointDetail.point_detail_id == self.point_detail_id).one()

            land_form_desc = point_detail.land_form_ref.description

            self.land_form_label.setText(land_form_desc)

            address_point = ''
            aimag = self.session.query(AuLevel1).filter(CaPastureMonitoring.geometry.ST_Within(AuLevel1.geometry)).\
                filter(CaPastureMonitoring.point_id == self.point_id).one()

            soum = self.session.query(AuLevel2).filter(CaPastureMonitoring.geometry.ST_Within(AuLevel2.geometry)). \
                filter(CaPastureMonitoring.point_id == self.point_id).one()

            bag = self.session.query(AuLevel3).filter(CaPastureMonitoring.geometry.ST_Within(AuLevel3.geometry)). \
                filter(CaPastureMonitoring.point_id == self.point_id).one()

            address_point = aimag.name + ', ' + soum.name + ', ' + bag.name + ', ' + point_detail.land_name
            self.point_address_label.setText(address_point)

    # @pyqtSlot()
    # def on_open_button_clicked(self):
    #
    #     self.__open_image()

    def __open_image(self):

        fileName = QFileDialog.getOpenFileName(self, "Open File",
                                               QDir.currentPath())
        if fileName:
            image = QImage(fileName)
            if image.isNull():
                QMessageBox.information(self, "Image Viewer",
                                        "Cannot load %s." % fileName)
                return

            self.imageLabel.setPixmap(QPixmap.fromImage(image))
            self.scaleFactor = 0.34

            self.printAct.setEnabled(True)
            self.fitToWindowAct.setEnabled(True)
            self.updateActions()

            if not self.fitToWindowAct.isChecked():
                self.imageLabel.adjustSize()

    @pyqtSlot()
    def on_print_button_clicked(self):

        self.__print_image()

    def __print_image(self):

        dialog = QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.imageLabel.pixmap().size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(self.imageLabel.pixmap().rect())
            painter.drawPixmap(0, 0, self.imageLabel.pixmap())

    def __zoomin(self):

        self.scaleImage(1.25)

    @pyqtSlot()
    def on_zoomin_button_clicked(self):

        self.__zoomin()

    def __zoomout(self):

        self.scaleImage(0.8)

    @pyqtSlot()
    def on_zoomout_button_clicked(self):

        self.__zoomout()

    def __normal_size(self):

        if self.pixmap_size:
            self.imageLabel.resize(QSize(420, 325))
        self.scaleFactor = 0.12

    # @pyqtSlot()
    # def on_normal_size_button_clicked(self):
    #
    #     self.__normal_size()

    def __fit_image(self):

        fitToWindow = self.fitToWindowAct.isChecked()

        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.__normal_size()

        self.updateActions()

    @pyqtSlot()
    def on_fit_button_clicked(self):

        self.__fit_image()

    @pyqtSlot()
    def on_about_button_clicked(self):

        QMessageBox.about(self, u"Мониторингийн цэгийн мэдээлэл",
                                u"<p>Бэлчээрийн газрын тухайн цэгийн <b>Мониторингийн мэдээлэл</b> "
                                u"Мониторингийн цэгийн байршлын/аймаг, сум, баг, газрын нэр/ мэдээлэл</b> "
                                u"болон тухайн газрын гадаргийн хэлбэр төлөв байдлын загварыг харуулна.</b> "
                                u"Цэгийн мониторингийн мэдээллийг он оноор харж болох бөгөөд "
                                u"фото зургийг орчны болон бүрхэцийн сонголттойгоор бүгдийг нь "
                                u"томруулж, жижигрүүлж харах боломжтой. "
                                u"Сонгогдсон жилийн бэлчээрийн даац, сэргэх чадавхи, төлөв байдлын "
                                u"мэдээлэл болон Фото зургийг хэвлэх командыг оруулж өгсөн болно.</p> "
                                u"<p>Дараах зурган мэдээлэл хэвлэх боломжтой</p> "
                                u"<p>-БАХ-ийн зураг</p> "
                                u"<p>-Улирлын бэлчээрийн зураг</p> "
                                u"<p>-Сэргэх чадавхийн зураг</p> ")

    def createActions(self):
        self.openAct = QAction("&Open...", self, shortcut="Ctrl+O",
                                     triggered=self.__open_image)

        self.printAct = QAction("&Print...", self, shortcut="Ctrl+P",
                                      enabled=False, triggered=self.__print_image)

        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                                     triggered=self.close)

        self.zoomInAct = QAction("Zoom &In (25%)", self,
                                       shortcut="Ctrl++", enabled=False, triggered=self.__zoomin)

        self.zoomOutAct = QAction("Zoom &Out (25%)", self,
                                        shortcut="Ctrl+-", enabled=False, triggered=self.__zoomout)

        self.normalSizeAct = QAction("&Normal Size", self,
                                           shortcut="Ctrl+S", enabled=False, triggered=self.__normal_size)

        self.fitToWindowAct = QAction("&Fit to Window", self,
                                            enabled=False, checkable=True, shortcut="Ctrl+F",
                                            triggered=self.__fit_image)

        # self.aboutAct = QAction("&About", self, triggered=self.on_about_button_clicked)

        # self.aboutQtAct = QAction("About &Qt", self,
        #                                 triggered=qApp.aboutQt)

    def createMenus(self):

        # self.open_button.addAction(self.openAct)
        self.zoomin_button.addAction(self.zoomInAct)
        self.zoomout_button.addAction(self.zoomOutAct)
        self.print_button.addAction(self.printAct)
        # self.normal_size_button.addAction(self.normalSizeAct)
        self.fit_button.addAction(self.fitToWindowAct)

        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)

        self.helpMenu = QMenu("&Help", self)
        # self.helpMenu.addAction(self.aboutAct)
        # self.helpMenu.addAction(self.aboutQtAct)

        # self.menuBar().addMenu(self.fileMenu)
        # self.menuBar().addMenu(self.viewMenu)
        # self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):

        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):

        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        self.updateActions()

        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        # self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        # self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))

    @pyqtSlot()
    def on_load_image_button_clicked(self):

        if self.cover_rbutton.isChecked():
            self.__load_cover_image()
        elif self.around_rbutton.isChecked():
            self.__load_around_image()

    def __load_cover_image(self):

        file_path = PasturePath.pasture_photo_file_path()
        point_year = str(self.year_sbox.value())

        file_path = file_path + '/' + point_year + '/' + self.point_detail_id + '/image'

        if not os.path.exists(file_path):
            PluginUtils.show_message(self, self.tr("Image View"), self.tr("No image!"))
            return

        for file in os.listdir(file_path):
            image_true = False
            os.listdir(file_path)
            if file.endswith(".JPG") or file.endswith(".jpg"):
                file_name_split = file.split('_')
                photo_type = file_name_split[0]

                file_point_detail_id = file_name_split[2]
                file_point_detail_id = file_point_detail_id.split('.')[0]

                self.image_id = file_name_split[1]
                self.image_type = file_name_split[0]

                fileName = file_path + '/' + file


                for i in range(4):
                    photo_type_code = 'cover'

                    if photo_type == photo_type_code and self.point_detail_id == file_point_detail_id:
                        if fileName:
                            image = QImage(fileName)
                            if image.isNull():
                                QMessageBox.information(self, "Image Viewer",
                                                        "Cannot load %s." % fileName)
                                return

                            self.imageLabel.setPixmap(QPixmap.fromImage(image))
                            self.pixmap_size = self.imageLabel.pixmap().size()
                            self.printAct.setEnabled(True)
                            self.fitToWindowAct.setEnabled(True)
                            self.updateActions()

                            if not self.fitToWindowAct.isChecked():
                                self.imageLabel.adjustSize()
                            image_true = True
                            break
            if image_true:
                break
        self.count_label.setText('1/9')

    def __load_around_image(self):

        file_path = PasturePath.pasture_photo_file_path()
        point_year = str(self.year_sbox.value())

        file_path = file_path + '/' + point_year + '/' + self.point_detail_id + '/image'

        if not os.path.exists(file_path):
            PluginUtils.show_message(self, self.tr("Image View"), self.tr("No image!"))
            return

        for file in os.listdir(file_path):
            image_true = False
            os.listdir(file_path)
            if file.endswith(".JPG") or file.endswith(".jpg"):
                file_name_split = file.split('_')
                photo_type = file_name_split[0]

                file_point_detail_id = file_name_split[2]
                file_point_detail_id = file_point_detail_id.split('.')[0]

                self.image_id = file_name_split[1]
                self.image_type = file_name_split[0]

                fileName = file_path + '/' + file

                for i in range(4):
                    photo_type_code = 'around'

                    if photo_type == photo_type_code and self.point_detail_id == file_point_detail_id:
                        if fileName:
                            image = QImage(fileName)
                            if image.isNull():
                                QMessageBox.information(self, "Image Viewer",
                                                        "Cannot load %s." % fileName)
                                return

                            self.imageLabel.setPixmap(QPixmap.fromImage(image))
                            self.pixmap_size = self.imageLabel.pixmap().size()
                            self.printAct.setEnabled(True)
                            self.fitToWindowAct.setEnabled(True)
                            self.updateActions()

                            if not self.fitToWindowAct.isChecked():
                                self.imageLabel.adjustSize()
                            image_true = True
                            break
            if image_true:
                break
        self.count_label.setText('1/4')

    @pyqtSlot()
    def on_next_button_clicked(self):

        if self.cover_rbutton.isChecked():
            self.__load_cover_next()
        elif self.around_rbutton.isChecked():
            self.__load_around_next()

    def __load_cover_next(self):

        file_path = PasturePath.pasture_photo_file_path()
        point_year = str(self.year_sbox.value())
        file_path = file_path + '/' + point_year + '/' + self.point_detail_id + '/image'
        file_name = 'cover_' + str(int(self.image_id)+1) + '_' + self.point_detail_id
        fileName = file_path + '/' + file_name

        photo_type_code = 'cover'

        if self.image_type == photo_type_code:
            if fileName:
                image = QImage(fileName)
                if image.isNull():
                    QMessageBox.information(self, "Image Viewer",
                                            "Cannot load %s." % fileName)
                    return

                self.imageLabel.setPixmap(QPixmap.fromImage(image))
                self.pixmap_size = self.imageLabel.pixmap().size()
                self.printAct.setEnabled(True)
                self.fitToWindowAct.setEnabled(True)
                self.updateActions()

                # if not self.fitToWindowAct.isChecked():
                #     self.imageLabel.adjustSize()
        self.image_id = str(int(self.image_id) + 1)
        self.count_label.setText(str(int(self.image_id))+'/9')

    def __load_around_next(self):

        file_path = PasturePath.pasture_photo_file_path()
        point_year = str(self.year_sbox.value())
        file_path = file_path + '/' + point_year + '/' + self.point_detail_id + '/image'
        file_name = 'around_' + str(int(self.image_id)+1) + '_' + self.point_detail_id
        fileName = file_path + '/' + file_name

        photo_type_code = 'around'

        if self.image_type == photo_type_code:
            if fileName:
                image = QImage(fileName)
                if image.isNull():
                    QMessageBox.information(self, "Image Viewer",
                                            "Cannot load %s." % fileName)
                    return

                self.imageLabel.setPixmap(QPixmap.fromImage(image))
                self.pixmap_size = self.imageLabel.pixmap().size()
                self.printAct.setEnabled(True)
                self.fitToWindowAct.setEnabled(True)
                self.updateActions()

                # if not self.fitToWindowAct.isChecked():
                #     self.imageLabel.adjustSize()
        self.image_id = str(int(self.image_id) + 1)
        self.count_label.setText(str(int(self.image_id))+'/4')

    @pyqtSlot()
    def on_prev_button_clicked(self):

        if self.cover_rbutton.isChecked():
            self.__load_cover_prev()
        elif self.around_rbutton.isChecked():
            self.__load_around_prev()

    def __load_cover_prev(self):

        file_path = PasturePath.pasture_photo_file_path()
        point_year = str(self.year_sbox.value())
        file_path = file_path + '/' + point_year + '/' + self.point_detail_id + '/image'
        file_name = 'cover_' + str(int(self.image_id)-1) + '_' + self.point_detail_id
        fileName = file_path + '/' + file_name

        photo_type_code = 'cover'

        if self.image_type == photo_type_code:
            if fileName:
                image = QImage(fileName)
                if image.isNull():
                    QMessageBox.information(self, "Image Viewer",
                                            "Cannot load %s." % fileName)
                    return

                self.imageLabel.setPixmap(QPixmap.fromImage(image))
                self.pixmap_size = self.imageLabel.pixmap().size()
                self.printAct.setEnabled(True)
                self.fitToWindowAct.setEnabled(True)
                self.updateActions()

                # if not self.fitToWindowAct.isChecked():
                #     self.imageLabel.adjustSize()
        self.image_id = str(int(self.image_id) - 1)
        self.count_label.setText(str(int(self.image_id))+'/9')

    def __load_around_prev(self):

        file_path = PasturePath.pasture_photo_file_path()
        point_year = str(self.year_sbox.value())

        file_path = file_path + '/' + point_year + '/' + self.point_detail_id + '/image'
        file_name = 'around_' + str(int(self.image_id)-1) + '_' + self.point_detail_id
        fileName = file_path + '/' + file_name

        photo_type_code = 'around'

        if self.image_type == photo_type_code:
            if fileName:
                image = QImage(fileName)
                if image.isNull():
                    QMessageBox.information(self, "Image Viewer",
                                            "Cannot load %s." % fileName)
                    return

                self.imageLabel.setPixmap(QPixmap.fromImage(image))
                self.pixmap_size = self.imageLabel.pixmap().size()
                self.printAct.setEnabled(True)
                self.fitToWindowAct.setEnabled(True)
                self.updateActions()

                # if not self.fitToWindowAct.isChecked():
                #     self.imageLabel.adjustSize()
        self.image_id = str(int(self.image_id) - 1)
        self.count_label.setText(str(int(self.image_id))+'/4')

    @pyqtSlot()
    def on_load_data_button_clicked(self):

        year = self.year_sbox.value()
        point_daats_count = self.session.query(PsPointDaatsValue).\
            filter(PsPointDaatsValue.point_detail_id == self.point_detail_id).\
            filter(PsPointDaatsValue.monitoring_year == year).count()
        if point_daats_count == 1:
            point_daats = self.session.query(PsPointDaatsValue).\
                filter(PsPointDaatsValue.point_detail_id == self.point_detail_id).\
                filter(PsPointDaatsValue.monitoring_year == year).one()



            self.calc_d1_edit.setText(str(round(point_daats.d1, 2)))
            self.calc_d1_100ga_edit.setText(str(round(point_daats.d1_100ga, 2)))
            self.calc_d2_edit.setText(str(round(point_daats.d2, 2)))
            self.calc_d3_edit.setText(str(round(point_daats.d3, 2)))
            self.calc_unelgee_edit.setText(str(round(point_daats.unelgee, 2)))
            self.calc_duration_sbox.setValue(point_daats.duration)


            rc_count = self.session.query(PsRecoveryClass).filter(PsRecoveryClass.rc_code == point_daats.rc).count()
            rc_tooltip = ''
            if rc_count == 1:
                rc = self.session.query(PsRecoveryClass).filter(PsRecoveryClass.rc_code == point_daats.rc).one()
                rc_tooltip = rc.description
                self.rc_label.setToolTip(rc_tooltip)

            self.rc_label.setText(point_daats.rc)


            self.biomass_label.setText(str(round(point_daats.biomass, 2)))

        point_pasture_value_count = self.session.query(PsPointPastureValue).\
            filter(PsPointPastureValue.point_detail_id == self.point_detail_id).\
            filter(PsPointPastureValue.pasture_value == 1).\
            filter(PsPointPastureValue.value_year == year).count()
        if point_pasture_value_count == 1:
            point_pasture_value = self.session.query(PsPointPastureValue). \
                filter(PsPointPastureValue.point_detail_id == self.point_detail_id). \
                filter(PsPointPastureValue.pasture_value == 1). \
                filter(PsPointPastureValue.value_year == year).one()
            if self.__load_pug(self.point_detail_id):
                pug_boundary = self.__load_pug(self.point_detail_id)
                self.rc_label_2.setText(pug_boundary.group_name)

            if self.__load_parcel(self.point_detail_id):
                parcel = self.__load_parcel(self.point_detail_id)
                self.rc_label_3.setText(parcel.pasture_type)
            self.cover_label.setText(str(point_pasture_value.current_value))

    def __load_pug(self, point_detail_id):

        pug_boundary = None
        point_id = None
        point_detail_points = self.session.query(PsPointDetailPoints) \
            .filter(PsPointDetailPoints.point_detail_id == point_detail_id).all()

        for point_detail_point in point_detail_points:
            point_id = point_detail_point.point_id

        if not point_id:
            return
        point = self.session.query(CaPastureMonitoring).filter(CaPastureMonitoring.point_id == point_id).one()

        pug_boundaries = self.session.query(CaPUGBoundary).filter(
            point.geometry.ST_Within(CaPUGBoundary.geometry)).all()

        for pug_bound in pug_boundaries:
            pug_boundary = pug_bound

        return pug_boundary
    def __load_parcel(self, point_detail_id):

        parcel = None
        point_id = None
        point_detail_points = self.session.query(PsPointDetailPoints) \
            .filter(PsPointDetailPoints.point_detail_id == point_detail_id).all()

        for point_detail_point in point_detail_points:
            point_id = point_detail_point.point_id

        if not point_id:
            return
        point = self.session.query(CaPastureMonitoring).filter(CaPastureMonitoring.point_id == point_id).one()

        parcel_count = self.session.query(CaPastureParcel).filter(
            point.geometry.ST_Within(CaPastureParcel.geometry)).count()

        if parcel_count == 1:
            parcel = self.session.query(CaPastureParcel).filter(
                point.geometry.ST_Within(CaPastureParcel.geometry)).one()
        else:
            parcel_count = self.session.query(PsParcel).filter(
                point.geometry.ST_Within(PsParcel.geometry)).count()

            if parcel_count == 1:
                parcel = self.session.query(PsParcel).filter(
                    point.geometry.ST_Within(PsParcel.geometry)).one()

        return parcel

    @pyqtSlot()
    def on_close_button_clicked(self):

        self.reject()