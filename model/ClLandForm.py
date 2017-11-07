__author__ = 'ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class ClLandForm(Base):

    __tablename__ = 'cl_land_form'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
