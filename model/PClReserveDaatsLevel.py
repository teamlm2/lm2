__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, Date, Sequence, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, backref
from Base import *

class PClReserveDaatsLevel(Base):

    __tablename__ = 'pcl_reserve_daats_level'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)