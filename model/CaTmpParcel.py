__author__ = 'ankhaa'

from CaMaintenanceCase import *
from sqlalchemy import Boolean, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from ClLanduseType import *


class CaTmpParcel(Base):

    __tablename__ = 'ca_tmp_parcel'

    parcel_id = Column(String, primary_key=True)
    old_parcel_id = Column(String)
    geo_id = Column(String)
    area_m2 = Column(Float)
    documented_area_m2 = Column(Float)
    address_khashaa = Column(String)
    address_neighbourhood = Column(String)
    address_streetname = Column(String)
    valid_from = Column(Date)
    valid_till = Column(Date)
    geometry = Column(Geometry('POLYGON', 4326))
    maintenance_case = Column(Integer)
    initial_insert = Column(Boolean)

    # foreign keys:
    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")
