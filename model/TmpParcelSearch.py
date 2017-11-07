__author__ = 'ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ClLanduseType import *
from Base import *


class TmpParcelSearch(Base):

    __tablename__ = 'tmp_parcel_search'

    parcel_id = Column(String, primary_key=True)
    old_parcel_id = Column(Integer)
    geo_id = Column(String)
    person_id = Column(String)
    name = Column(String)
    first_name = Column(String)
    middle_name = Column(String)
    app_no = Column(String)
    decision_no = Column(String)
    contract_no = Column(String)
    record_no = Column(String)
    address_streetname = Column(String)
    address_khashaa = Column(String)
    au2_code = Column(String)

    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")
