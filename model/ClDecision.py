__author__ = 'mwagner'

from sqlalchemy import Column, String, Integer
from Base import *


class ClDecision(Base):

    __tablename__ = 'cl_decision'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
