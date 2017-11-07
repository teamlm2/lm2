__author__ = 'B.Ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class ClLanduseType(Base):

    __tablename__ = 'cl_landuse_type'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
    code2 = Column(Integer)
    description2 = Column(String)