__author__ = 'anna'

import unittest
from trunk.utils.SessionHandler import SessionHandler
from trunk.model.BsPerson import BsPerson
from trunk.model.ClPersonType import ClPersonType
from trunk.model.ClGender import ClGender
from trunk.model.AuLevel1 import AuLevel1
from trunk.model.AuLevel2 import AuLevel2
from trunk.model.AuLevel3 import AuLevel3
from trunk.model.AuKhoroolol import AuKhoroolol
from trunk.model.ClBank import ClBank

class test_BsPerson(unittest.TestCase):

    def setUp(self):
        user = "anna"
        password = "anna"
        database = "darkhan_update_final"
        host = "localhost"
        port = "5432"

        SessionHandler().create_session(user, password, host, port, database)
        self.session = SessionHandler().session_instance()

    def test_create(self):
        person = BsPerson()
        person.id = 123
        type = self.session.query(ClPersonType).first()
        bank = self.session.query(ClBank).first()
        person.type_ref = type
        person.name = "Sherman"
        person.middle_name = " the greatest"
        person.first_name = "Gary"
        dateTimeString = QDateTime.currentDateTime().toString(Constants.DATABASE_DATETIME_FORMAT)
        person.date_of_birth = datetime.strptime(str(dateTimeString), Constants.PYTHON_DATETIME_FORMAT)
        person.person_id = "AC123456001"
        person.bank_account_no = "12121212"
        person.bank_ref = bank
        person.phone = 234567890
        person.mobile_phone = 12345678
        person.gender_ref = self.session.query(ClGender).first()
        person.address_au_level1_ref = self.session.query(AuLevel1).first()
        person.address_au_level2_ref = self.session.query(AuLevel2).first()
        person.address_au_level3_ref = self.session.query(AuLevel3).first()
        person.address_au_khoroolol_ref = self.session.query(AuKhoroolol).first

        self.session.add(person)
        self.session.commit()

    def test_udpate(self):

        person = self.session.query(BsPerson).filter_by(id=123).one()
        person.id = 1234
        person.address_au_level1_ref = self.session.query(AuLevel1).filter_by("045").one()
        person.address_au_level2_ref = self.session.query(AuLevel2).filter_by("04510").one()


    def test_delete(self):

        self.session.query(BsPerson).filter_by(id=1234).delete()
        self.session.commit()

if __name__ == '__main__':
    unittest.main()
