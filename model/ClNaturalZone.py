__author__ = 'ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class ClNaturalZone(Base):

    __tablename__ = 'cl_natural_zone'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
