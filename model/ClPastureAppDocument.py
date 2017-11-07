__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, Date, Sequence, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, backref
from Base import *

class ClPastureAppDocument(Base):

    __tablename__ = 'cl_pasture_app_document'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)