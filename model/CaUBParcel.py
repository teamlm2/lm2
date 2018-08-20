
__author__ = 'B.Ankhbold'
from sqlalchemy import Column, String, Float, Date, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from ClLanduseType import *
from ClUbEditStatus import *

class CaUBParcel(Base):

    __tablename__ = 'ca_ub_parcel'

    parcel_id = Column(String)
    old_parcel_id = Column(String, primary_key=True)
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

    edit_status = Column(Integer, ForeignKey('cl_ub_edit_status.code'))
    edit_status_ref = relationship("ClUbEditStatus")