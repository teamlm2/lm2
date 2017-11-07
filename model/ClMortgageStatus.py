__author__ = 'Ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class ClMortgageStatus(Base):

    __tablename__ = 'cl_mortgage_status'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
