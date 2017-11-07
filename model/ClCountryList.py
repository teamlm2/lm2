__author__ = 'ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class ClCountryList(Base):

    __tablename__ = 'cl_country_list'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
    zipcode = Column(Integer)
