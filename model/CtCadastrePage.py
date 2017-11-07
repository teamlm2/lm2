__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, Date, ForeignKey,Sequence
from sqlalchemy.orm import relationship, backref
from Base import *

class CtCadastrePage(Base):

    __tablename__ = 'ct_cadastre_page'

    id = Column(Integer, primary_key=True)
    print_date = Column(Date)
    cadastre_page_number = Column(Integer)

    person_id = Column(String, ForeignKey('bs_person.person_id'))
    person_id_ref = relationship("BsPerson")

    parcel_id = Column(String, ForeignKey('ca_union_parcel.parcel_id'))
    parcel_id_ref = relationship("CaUnionParcel")
