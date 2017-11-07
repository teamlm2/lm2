
__author__ = 'ankhbold'
from sqlalchemy import Column, String, Float, Date, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from ClLanduseType import *
from Base import *

class SParcelTbl(Base):

    __tablename__ = 's_parcel_tbl'

    parcel_id = Column(String, primary_key=True)
    old_parcel_id = Column(String)
    geo_id = Column(String)
    area_m2 = Column(Float)
    documented_area_m2 = Column(Float)
    address_khashaa = Column(String)
    address_streetname = Column(String)
    address_neighbourhood = Column(String)
    valid_from = Column(Date)
    valid_till = Column(Date)
    geometry = Column(Geometry('POLYGON', 4326))

    # foreign keys:
    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")

    #applications = relationship("CtApplication")