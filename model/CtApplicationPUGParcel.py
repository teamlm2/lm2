__author__ = 'B.Ankhbold'
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from Base import *


class CtApplicationPUGParcel(Base):

    __tablename__ = 'ct_application_pug_parcel'

    parcel = Column(String, ForeignKey('ca_pasture_parcel.parcel_id'), primary_key=True)
    application = Column(String, ForeignKey('ct_application.app_no'), primary_key=True)