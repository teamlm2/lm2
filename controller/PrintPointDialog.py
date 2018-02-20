__author__ = 'anna'
# coding=utf8

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *
from qgis.core import *
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

        self.session = SessionHandler().session_instance()
        self.setupUi(self)

        self.image_id = 0
        self.image_type = 0

        self.printer = QPrinter()
        self.scaleFactor = 0.0

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

        self.setWindowTitle("Image Viewer")
        # self.resize(500, 400)

        self.open_button.setStyleSheet("""QToolTip { 
                           background-color: black; 
                           color: white; 
                           border: black solid 1px
                           }""")

    @pyqtSlot()
    def on_open_button_clicked(self):

        self.__open_image()

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
            self.scaleFactor = 1.0

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

        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    @pyqtSlot()
    def on_normal_size_button_clicked(self):

        self.__normal_size()

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

        QMessageBox.about(self, "About Image Viewer",
                                "<p>The <b>Image Viewer</b> example shows how to combine "
                                "QLabel and QScrollArea to display an image. QLabel is "
                                "typically used for displaying text, but it can also display "
                                "an image. QScrollArea provides a scrolling view around "
                                "another widget. If the child widget exceeds the size of the "
                                "frame, QScrollArea automatically provides scroll bars.</p>"
                                "<p>The example demonstrates how QLabel's ability to scale "
                                "its contents (QLabel.scaledContents), and QScrollArea's "
                                "ability to automatically resize its contents "
                                "(QScrollArea.widgetResizable), can be used to implement "
                                "zooming and scaling features.</p>"
                                "<p>In addition the example shows how to use QPainter to "
                                "print an image.</p>")

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

        self.open_button.addAction(self.openAct)
        self.zoomin_button.addAction(self.zoomInAct)
        self.zoomout_button.addAction(self.zoomOutAct)
        self.print_button.addAction(self.printAct)
        self.normal_size_button.addAction(self.normalSizeAct)
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
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

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
        point_detail_id = str(self.point_id[:-2])
        file_path = file_path + '/' + point_year + '/' + point_detail_id + '/image'

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

                    if photo_type == photo_type_code and point_detail_id == file_point_detail_id:
                        if fileName:
                            image = QImage(fileName)
                            if image.isNull():
                                QMessageBox.information(self, "Image Viewer",
                                                        "Cannot load %s." % fileName)
                                return

                            self.imageLabel.setPixmap(QPixmap.fromImage(image))
                            self.scaleFactor = 1.0

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
        point_detail_id = str(self.point_id[:-2])
        file_path = file_path + '/' + point_year + '/' + point_detail_id + '/image'

        if not os.path.exists(file_path):
            PluginUtils.show_message(self, self.tr("Image View"), self.tr("No image!"))
            return

        for file in os.listdir(file_path):
            image_true = False
            os.listdir(file_path)
            if file.endswith(".JPG") or file.endswith(".jpg"):
                file_name_split = file.split('_')
                photo_type = file_name_split[0]
                image_id = file_name_split[1]

                file_point_detail_id = file_name_split[2]
                file_point_detail_id = file_point_detail_id.split('.')[0]

                self.image_id = file_name_split[1]
                self.image_type = file_name_split[0]

                fileName = file_path + '/' + file

                for i in range(4):
                    photo_type_code = 'around'

                    if photo_type == photo_type_code and point_detail_id == file_point_detail_id:
                        if fileName:
                            image = QImage(fileName)
                            if image.isNull():
                                QMessageBox.information(self, "Image Viewer",
                                                        "Cannot load %s." % fileName)
                                return

                            self.imageLabel.setPixmap(QPixmap.fromImage(image))
                            self.scaleFactor = 1.0

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
        point_detail_id = str(self.point_id[:-2])
        file_path = file_path + '/' + point_year + '/' + point_detail_id + '/image'
        file_name = 'cover_' + str(int(self.image_id)+1) + '_' + point_detail_id
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
                self.scaleFactor = 1.0

                self.printAct.setEnabled(True)
                self.fitToWindowAct.setEnabled(True)
                self.updateActions()

                if not self.fitToWindowAct.isChecked():
                    self.imageLabel.adjustSize()
        self.image_id = str(int(self.image_id) + 1)
        self.count_label.setText(str(int(self.image_id))+'/9')

    def __load_around_next(self):

        file_path = PasturePath.pasture_photo_file_path()
        point_year = str(self.year_sbox.value())
        point_detail_id = str(self.point_id[:-2])
        file_path = file_path + '/' + point_year + '/' + point_detail_id + '/image'
        file_name = 'around_' + str(int(self.image_id)+1) + '_' + point_detail_id
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
                self.scaleFactor = 1.0

                self.printAct.setEnabled(True)
                self.fitToWindowAct.setEnabled(True)
                self.updateActions()

                if not self.fitToWindowAct.isChecked():
                    self.imageLabel.adjustSize()
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
        point_detail_id = str(self.point_id[:-2])
        file_path = file_path + '/' + point_year + '/' + point_detail_id + '/image'
        file_name = 'cover_' + str(int(self.image_id)-1) + '_' + point_detail_id
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
                self.scaleFactor = 1.0

                self.printAct.setEnabled(True)
                self.fitToWindowAct.setEnabled(True)
                self.updateActions()

                if not self.fitToWindowAct.isChecked():
                    self.imageLabel.adjustSize()
        self.image_id = str(int(self.image_id) - 1)
        self.count_label.setText(str(int(self.image_id))+'/9')

    def __load_around_prev(self):

        file_path = PasturePath.pasture_photo_file_path()
        point_year = str(self.year_sbox.value())
        point_detail_id = str(self.point_id[:-2])
        file_path = file_path + '/' + point_year + '/' + point_detail_id + '/image'
        file_name = 'around_' + str(int(self.image_id)-1) + '_' + point_detail_id
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
                self.scaleFactor = 1.0

                self.printAct.setEnabled(True)
                self.fitToWindowAct.setEnabled(True)
                self.updateActions()

                if not self.fitToWindowAct.isChecked():
                    self.imageLabel.adjustSize()
        self.image_id = str(int(self.image_id) - 1)
        self.count_label.setText(str(int(self.image_id))+'/4')