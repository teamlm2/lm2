
__author__ = 'B.Ankhbold'
from sqlalchemy import Column, String, Float, Date, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from ClLanduseType import *


class AllPastureParcel(Base):

    __tablename__ = 'all_pasture_parcel'

    parcel_id = Column(String, primary_key=True)
    old_parcel_id = Column(String)
    geo_id = Column(String)
    area_ga = Column(Float)
    capacity = Column(Float)
    address_neighbourhood = Column(String)
    pasture_type = Column(String)
    valid_from = Column(Date)
    valid_till = Column(Date)
    geometry = Column(Geometry('POLYGON', 4326))

    # foreign keys:
    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")

    #applications = relationship("CtApplication")