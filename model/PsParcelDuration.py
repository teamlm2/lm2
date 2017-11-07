__author__ = 'B.Ankhbold'
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from Base import *


class PsParcelDuration(Base):

    __tablename__ = 'ps_parcel_duration'

    parcel = Column(String, primary_key=True)
    application = Column(String, primary_key=True)
    pasture = Column(Integer, ForeignKey('cl_pasture_type.code'), primary_key=True)

    begin_month = Column(Integer)
    end_month = Column(Integer)
    days = Column(Integer)