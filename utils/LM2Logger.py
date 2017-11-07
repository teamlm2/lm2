__author__ = 'Anna'
# !/usr/bin/python
# -*- coding: utf-8
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from ..model.Singleton import Singleton
from ..model import Constants


class LM2Logger(QObject):

    __metaclass__ = Singleton

    def __init__(self, parent=None):

        super(QObject, self).__init__(parent)
        self.parent = parent
        self.file_path = QDir.homePath() + "/.lm2"

        self.__create_path()

    def __create_path(self):

        if not QFileInfo(self.file_path).exists():
            QDir().mkpath(self.file_path)

        if not QFileInfo(self.file_path + "/" + Constants.LOG_FILE_NAME).exists():
            file = QFile(self.file_path + "/" + Constants.LOG_FILE_NAME)
            if not file.open(QFile.ReadWrite):
                QMessageBox.information(self.parent, self.tr("Logging error"), self.tr("Could not create log file"))
                return
            file.close()

    def log_message(self, log_message):

        date_time = QDateTime.currentDateTime().toString(Constants.DATABASE_DATETIME_FORMAT)
        log_string = date_time + u": " + log_message + u"\n"

        try:
            test_file = open(self.file_path + "/" + Constants.LOG_FILE_NAME, 'a')
        except IOError as e:
            QMessageBox.information(None, self.tr("Logging error"), self.tr("Could not open log file: {0}").format(e.strerror))
            return

        test_file.writelines([log_string.encode("UTF-8")])
        test_file.close()

