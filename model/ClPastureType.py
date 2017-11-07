__author__ = 'mwagner'

from sqlalchemy import Column, String, Integer
from Base import *


class ClPastureType(Base):

    __tablename__ = 'cl_pasture_type'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
