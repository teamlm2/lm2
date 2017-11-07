__author__ = 'B.Ankhbold'
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from Base import *


class CtApplicationParcelPasture(Base):

    __tablename__ = 'ct_application_parcel_pasture'

    parcel = Column(String, ForeignKey('ca_pasture_parcel.parcel_id'), primary_key=True)
    application = Column(String, ForeignKey('ct_application.app_no'), primary_key=True)
    pasture = Column(Integer, ForeignKey('cl_pasture_type.code'), primary_key=True)

    begin_month = Column(Integer)
    end_month = Column(Integer)
    days = Column(Integer)