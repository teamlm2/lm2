__author__ = 'mwagner'

from sqlalchemy import Column, Integer, String, ForeignKey,Float,Numeric,Date
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from ClLanduseType import *
from Base import *


class ParcelGt1(Base):

    __tablename__ = 'parcel_gt1'

    parcel_id = Column(String, primary_key=True)
    area_m2 = Column(Float)
    au1_code = Column(String)
    au2_code = Column(String)
    valid_from = Column(Date)
    valid_till = Column(Date)
    landuse_code2 = Column(Integer)
    geometry = Column(Geometry('POLYGON', 4326))
    # foreign keys:
    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")

