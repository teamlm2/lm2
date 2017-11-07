
__author__ = 'Ankhaa'
from sqlalchemy import Column, String, Float, Date
from geoalchemy2 import Geometry
from Base import *


class AllPastureBuilding(Base):

    __tablename__ = 'all_pasture_building'

    building_id = Column(String, primary_key=True)
    building_no = Column(String)
    geo_id = Column(String)
    area_m2 = Column(Float)
    address_neighbourhood = Column(String)
    valid_from = Column(Date)
    valid_till = Column(Date)
    geometry = Column(Geometry('POLYGON', 4326))