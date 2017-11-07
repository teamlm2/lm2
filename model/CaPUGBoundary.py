__author__ = 'B.Ankhbold'

from sqlalchemy import Column, String, Float
from geoalchemy2 import Geometry
from Base import *


class CaPUGBoundary(Base):

    __tablename__ = 'ca_pug_boundary'

    code = Column(String, primary_key=True)
    area_ga = Column(Float)
    group_name = Column(String)
    geometry = Column(Geometry('POLYGON', 4326))
