__author__ = 'ankhbold'

from sqlalchemy import Column, Integer, String, Date, Sequence, ForeignKey, DateTime
from CaParcel import *

class VaInfoAgriculture(Base):

    __tablename__ = 'va_info_agriculture'

    id = Column(Integer, primary_key=True)
    area_m2 = Column(Float)
    yield_ga = Column(Float)
    costs = Column(Float)
    profit = Column(Float)
    net_profit = Column(Float)

    #foreign keys:
    register_no = Column(String, ForeignKey('va_info_parcel.register_no'))
    register_no_ref = relationship("VaInfoHomeParcel")

    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")

    crop_type = Column(Integer, ForeignKey('cl_type_crop.code'))
    crop_type_ref = relationship("VaTypeCrop")
