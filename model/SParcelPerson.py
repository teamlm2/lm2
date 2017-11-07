__author__ = 'ankhbold'
from sqlalchemy import Column, String, Float, Date, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship
from Base import *

class SParcelPerson(Base):

    __tablename__ = 's_parcel_person'

    parcel_id = Column(String, ForeignKey('s_parcel_tbl.parcel_id'), primary_key=True)
    parcel_id_ref = relationship("SParcelTbl")

    person_id = Column(String, ForeignKey('bs_person.person_id'), primary_key=True)
    person_id_ref = relationship("BsPerson")