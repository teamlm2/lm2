__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from Base import *

class PsPastureBoundary(Base):

    __tablename__ = 'ps_pasture_boundary'

    parcel_id = Column(String, primary_key=True)
    pasture_land_name = Column(String)
    pasture_type = Column(String)
    pasture_area = Column(Numeric)
    pug_code = Column(String)
    pug_area = Column(Numeric)
    pug_name = Column(String)
    au2_code = Column(String)
    au3_code = Column(String)
    parcel_geom = Column(Geometry('POLYGON', 4326))
    pug_geom = Column(Geometry('POLYGON', 4326))
