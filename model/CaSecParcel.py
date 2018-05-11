__author__ = 'B.Ankhbold'
from sqlalchemy import Column, String, Float, Date, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from ClLanduseType import *

class CaSecParcel(Base):

    __tablename__ = 'ca_sec_parcel'

    parcel_id = Column(Integer, primary_key=True)
    valid_from = Column(Date)
    valid_till = Column(Date)
    area_m2 = Column(Float)
    explan = Column(String)
    geometry = Column(Geometry('POLYGON', 4326))

    # foreign keys:
    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")
