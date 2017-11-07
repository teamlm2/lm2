
__author__ = 'B.Ankhbold'
from sqlalchemy import Column, String, Float, Date, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from ClLanduseType import *


class CaParcelPollution(Base):

    __tablename__ = 'parcel_pollution'

    gid = Column(Integer, primary_key=True)
    area_m2 = Column(Float)
    polluted_area_m2 = Column(Float)
    address_khashaa = Column(String)
    address_streetname = Column(String)
    address_neighbourhood = Column(String)
    valid_from = Column(Date)
    valid_till = Column(Date)
    geometry = Column(Geometry('POLYGON', 4326))

    # foreign keys:
    pollution = Column(Integer, ForeignKey('cl_pollution_type.code'))
    pollution_ref = relationship("ClPollutionType")







