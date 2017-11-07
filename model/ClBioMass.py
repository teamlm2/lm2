__author__ = 'b.ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class ClBioMass(Base):

    __tablename__ = 'cl_biomass'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
