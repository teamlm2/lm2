__author__ = 'Anna'

from sqlalchemy import Column, String, Float
from geoalchemy2 import Geometry
from Base import *


class AuLevel3(Base):

    __tablename__ = 'au_level3'

    code = Column(String, primary_key=True)
    name = Column(String)
    area_m2 = Column(Float)
    geometry = Column(Geometry('POLYGON', 4326))