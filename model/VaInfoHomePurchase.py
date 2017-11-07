__author__ = 'ankhbold'

from sqlalchemy import Column, Integer, String, Date, Sequence, ForeignKey, DateTime, Table
from CaParcel import *
from CtApplicationDocument import *


class VaInfoHomePurchase(Base):

    __tablename__ = 'va_info_purchase'

    id = Column(Integer, primary_key=True)
    area_m2 = Column(Float)
    purchase_date = Column(DateTime)
    price = Column(Float)
    price_m2 =Column(Float)

    #foreign keys:
    register_no = Column(String, ForeignKey('va_info_parcel.register_no'))
    register_no_ref = relationship("VaInfoHomeParcel")

    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")
