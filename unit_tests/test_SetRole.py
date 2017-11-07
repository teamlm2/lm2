__author__ = 'anna'

import unittest
from datetime import datetime
from trunk.utils.SessionHandler import SessionHandler
from trunk.model.AuLevel1 import AuLevel1
from trunk.model.AuLevel2 import AuLevel2
from trunk.model.AuLevel3 import AuLevel3
from trunk.model.SetRole import SetRole
from trunk.model import Constants

from sqlalchemy.exc import SQLAlchemyError
from geoalchemy2 import WKTElement

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
            set_role = SetRole()
            geometryString = "POLYGON((" + str(0) + " " + str(1) + "," + str(1) + " " + str(1) + "," + str(1) + " " + str(0) + ", " + str(1) + " " + str(0) + "," + str(0) + " " + str(1) + "))"
            filter_bbox = WKTElement(geometryString, 4326)
            set_role.filter_bbox = filter_bbox
            set_role.first_name = "Gary"
            set_role.surname = "Sherman"
            set_role.user_name = "gary_the_sherman"
            set_role.position = "Programmer"
            set_role.phone = "1234567"
            set_role.mac_addresses = "12.12.12.12.12"
            set_role.restriction_au_level2_ref = self.session.query(AuLevel2).first()
            set_role.restriction_au_level1_ref = self.session.query(AuLevel1).order_by(AuLevel1.code.desc()).first()
            set_role.restriction_au_level3_ref = self.session.query(AuLevel3).order_by(AuLevel3.code.desc()).first()
            set_role.working_au_level1_ref = self.session.query(AuLevel1).order_by(AuLevel1.code.desc()).first()
            set_role.working_au_level2_ref = self.session.query(AuLevel2).order_by(AuLevel2.code.desc()).first()
            dateTimeString = QDateTime.currentDateTime().toString(Constants.DATABASE_DATETIME_FORMAT)
            set_role.pa_from = datetime.strptime(str(dateTimeString), Constants.PYTHON_DATETIME_FORMAT)
            set_role.set_role.pa_till = datetime.strptime(str(dateTimeString), Constants.PYTHON_DATETIME_FORMAT)

            self.session.add(set_role)
            self.session.commit()

        except SQLAlchemyError:
            self.assertRaises(SQLAlchemyError)

    def test_update(self):

        try:
            set_role = self.session.query(SetRole).filter_by(user_name="gary_the_sherman").one()

            set_role.restriction_au_level1 = self.session.query(AuLevel1).order_by(AuLevel1.code.asc()).first()
            set_role.restriction_au_level2 = self.session.query(AuLevel2).order_by(AuLevel2.code.asc()).first()
            set_role.working_au_level1_ref = self.session.query(AuLevel1).order_by(AuLevel1.code.asc()).first()
            set_role.working_au_level2_ref = self.session.query(AuLevel1).order_by(AuLevel2.code.asc()).first()

            self.session.commit()

        except SQLAlchemyError, e:
            self.assertRaises(SQLAlchemyError)

    def test_delete(self):

        try:
            self.session.query(SetRole).filter_by(user_name="gary_the_sherman").delete()
            self.session.commit()

        except SQLAlchemyError:
            self.assertRaises(SQLAlchemyError)


if __name__ == '__main__':
    unittest.main()
