__author__ = 'Ankhbold'

from sqlalchemy import Column, String, Float, Integer
from geoalchemy2 import Geometry
from Base import *


class AuNaturalZone(Base):

    __tablename__ = 'au_natural_zone'

    code = Column(Integer, primary_key=True)
    name = Column(String)
    name_en = Column(String)
    area_m2 = Column(Float)
    geometry = Column(Geometry('MULTIPOLYGON', 4326))