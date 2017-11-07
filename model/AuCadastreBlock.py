__author__ = 'anna'

from sqlalchemy import Column, String, Float, Integer, Sequence
from geoalchemy2 import Geometry
from Base import *


class AuCadastreBlock(Base):

    __tablename__ = 'au_cadastre_block'

    code = Column(String, primary_key=True)
    block_no = Column(String)
    area_m2 = Column(Float)
    soum_code = Column(String)
    geometry = Column(Geometry('MULTIPOLYGON'))
