__author__ = 'anna'

import unittest
from qgis.core import *
from qgis.gui import *

from trunk.utils.SessionHandler import SessionHandler
from trunk.model.CtApplication import CtApplication
from trunk.model.CtApplicationPersonRole import CtApplicationPersonRole
from trunk.model.CtApplicationStatus import CtApplicationStatus
from trunk.model.ClPersonRole import ClPersonRole
from trunk.model.ClApplicationStatus import ClApplicationStatus
from trunk.model.ClDocumentRole import ClDocumentRole
from trunk.model.CtDocument import CtDocument
from trunk.model.CtApplicationDocument import CtApplicationDocument
from trunk.model.CtApp1Ext import CtApp1Ext
from trunk.model.CtApp8Ext import CtApp8Ext
from trunk.model.CtApp15Ext import CtApp15Ext
from trunk.model.ClMortgageType import ClMortgageType
from trunk.model.ClTransferType import ClTransferType
from trunk.model.SetRole import SetRole
from trunk.model.BsPerson import BsPerson
from trunk.utils.PluginUtils import PluginUtils
from sqlalchemy.exc import SQLAlchemyError

class test_CtApplication(unittest.TestCase):

    def setUp(self):

        user = "anna"
        password = "anna"
        database = "darkhan_update_final"
        host = "localhost"
        port = "5432"


        SessionHandler().create_session(user, password, host, port, database)
        self.session = SessionHandler().session_instance()

    def test_create(self):

        try:
            ct_application = PluginUtils.create_new_application("123")
            self.session.add(ct_application)
            self.session.commit()

        except SQLAlchemyError:
            self.assertRaises(SQLAlchemyError)

    def test_update(self):

        try:
            ct_application = self.session.query(CtApplication).filter_by(app_no="123").one()

            ct_application.app_no = "1234"
            ct_application.approved_duration = 10
            ct_application.remarks = "Unit tests class"

            #Add ApplicationStatus
            set_role = self.session.query(SetRole).filter_by(username="anna").one()
            status = CtApplicationStatus()
            status.next_officer_in_charge_ref = set_role
            status.officer_in_charge_ref = set_role
            dateTimeString = QDateTime.currentDateTime().toString(Constants.DATABASE_DATETIME_FORMAT)
            status.status_date = datetime.strptime(str(dateTimeString), Constants.PYTHON_DATETIME_FORMAT)
            status_ref = self.session.query(ClApplicationStatus).first()
            status.status_ref = status_ref
            ct_application.statuse.append(status)

            #Add ApplicationPersonRole instance
            person = self.session.query(BsPerson).filter_by(id=1).one()
            role_ref = self.session.query(ClPersonRole).first()
            person_role = CtApplicationPersonRole()
            person_role.person = 1
            person_role.person_ref = person
            person_role.role = role_ref.code
            person_role.role_ref = role_ref
            ct_application.stakeholders.append(person_role)

            #Add DocumentPersonRole
            doc_role = self.session.query(ClDocumentRole).first()
            ct_document_role = CtApplicationDocument()
            ct_document = CtDocument()
            ct_document = "test.doc"
            currentFile = QFile("/Users/anna/Documents/Projects/Mongolia/Orga/LandManager 2.pdf")
            if not currentFile.open(QIODevice.ReadOnly):
                self.assertRaises("")
            byteArray = currentFile.readAll()
            ct_document.content = bytes(byteArray)
            ct_document_role.document_ref = ct_document
            ct_document_role.person_ref = person
            ct_document_role.role_ref = doc_role

            #app1Ext
            app_1_Ext = CtApp1Ext()
            app_1_Ext.applicant_has_paid = True
            app_1_Ext.excess_area = 123
            app_1_Ext.price_to_be_paid = 12.12
            ct_application.app1ext = app_1_Ext

            #app8Ext
            app_8_Ext = CtApp8Ext()
            app_8_Ext_type = self.session.query(ClMortgageType).first()
            app_8_Ext.end_mortgage_period = datetime.strptime(str(dateTimeString), Constants.PYTHON_DATETIME_FORMAT)
            app_8_Ext.start_mortgage_period = datetime.strptime(str(dateTimeString), Constants.PYTHON_DATETIME_FORMAT)
            app_8_Ext.mortgage_type_ref = app_8_Ext_type
            ct_application.app8ext = app_8_Ext

            #app15Ext
            app_15_ext = CtApp15Ext()
            transfer_type = self.session.query(ClTransferType).first()
            app_15_ext.transfer_type_ref = transfer_type
            ct_application.app15ext = app_15_ext

            self.session.commit()

        except SQLAlchemyError, e:
            self.assertRaises(SQLAlchemyError)

    def test_delete(self):

        try:
            self.session.query(CtApplication).filter_by(app_no="1234").delete()
            self.session.commit()

        except SQLAlchemyError:
            self.assertRaises(SQLAlchemyError)

if __name__ == '__main__':
    unittest.main()


