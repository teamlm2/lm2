__author__ = 'Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey, Date, Numeric
from Base import *


class PsNZSheepFood(Base):
    __tablename__ = 'ps_nz_sheep_food'

    natural_zone = Column(Integer, ForeignKey('cl_natural_zone.code'), primary_key=True)
    current_value = Column(Integer, primary_key=True)