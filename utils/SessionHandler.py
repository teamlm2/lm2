__author__ = 'Anna'
# !/usr/bin/python
# -*- coding: utf-8
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from ..model.Singleton import Singleton
from ..model.SetRole import SetRole


class SessionHandler(QObject):

    __metaclass__ = Singleton

    def __init__(self, parent=None):

        super(QObject, self).__init__(parent)
        self.parent = parent
        self.session = None
        self.engine = None
        self.password = None

    def current_password(self):

        return self.password

    def session_instance(self):
        return self.session

    def get_connection(self):

        connection = self.engine.connect()
        return connection

    def create_session(self, user, password, host, port, database):

        if self.session is not None:
            self.session.close()

        try:
            self.engine = create_engine("postgresql://{0}:{1}@{2}:{3}/{4}".format(user, password, host, port, database))
            self.password = password
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            self.session.autocommit = False
            self.session.execute("SET search_path to base, codelists, ub_data, admin_units, settings, pasture, public, sdplatform")

            set_role_count = self.session.query(SetRole).filter(SetRole.user_name == user).filter(SetRole.is_active == True).count()
            if set_role_count == 0:
                QMessageBox.information(None, self.tr("Connection Error"), self.tr("The user name {0} is not registered.").format(user))
                self.session = None
                self.engine = None
                self.password = None
                return False

            setRole = self.session.query(SetRole).filter(SetRole.user_name == user).filter(SetRole.is_active == True).one()
            auLevel2List = setRole.restriction_au_level2.split(",")
            schemaList = []

            for auLevel2 in auLevel2List:

                auLevel2 = auLevel2.strip()
                schemaList.append("s" + auLevel2)

            schema_string = ",".join(schemaList)

            self.session.execute("SET search_path to base, codelists, ub_data, admin_units, settings, pasture, public, data_soums_union, sdplatform" + ", " + schema_string)
            self.session.commit()

            return True

        except SQLAlchemyError, e:
            self.session = None
            self.engine = None
            self.password = None
            raise e

    def destroy_session(self):

        if self.session is not None:
            self.session.close()
            self.session = None