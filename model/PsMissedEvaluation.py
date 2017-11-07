__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, Date, Sequence, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, backref
from Base import *

class PsMissedEvaluation(Base):

    __tablename__ = 'ps_missed_evaluation'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    ball = Column(Integer)