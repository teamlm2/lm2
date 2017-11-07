__author__ = 'mwagner'

from sqlalchemy import Column, String, Float, Integer, Sequence
from geoalchemy2 import Geometry
from Base import *


class AuKhoroolol(Base):

    __tablename__ = 'au_khoroolol'

    fid = Column(Integer, Sequence('au_khoroolol_tbl_fid_seq'), primary_key=True)
    name = Column(String)
    area_m2 = Column(Float)
    geometry = Column(Geometry('POLYGON'))
