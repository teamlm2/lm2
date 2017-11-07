__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, Date, Sequence, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, backref
from Base import *

class PClFormulaType(Base):

    __tablename__ = 'pcl_formula_type'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)