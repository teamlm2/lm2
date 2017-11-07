__author__ = 'mwagner'

from sqlalchemy import Column, String, Integer
from Base import *


class ClDecisionLevel(Base):

    __tablename__ = 'cl_decision_level'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
