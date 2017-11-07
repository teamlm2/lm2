__author__ = 'B.Ankhbold'

from sqlalchemy import String,Date, Integer, Column, Sequence
from geoalchemy2 import Geometry
from Base import *


class SetCertificatePerson(Base):

    __tablename__ = 'set_certificate_person'

    id = Column(Integer, Sequence('set_certificate_person_id_seq'), primary_key=True)
    person_id = Column(String)
    surname = Column(String)
    firstname = Column(String)