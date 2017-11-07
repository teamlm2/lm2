__author__ = 'ankhbold'

from sqlalchemy import Column, Integer, String, Date, Sequence, ForeignKey, DateTime
from CaParcel import *

class VaInfoHomeLease(Base):

    __tablename__ = 'va_info_lease'

    id = Column(Integer, primary_key=True)
    area_m2 = Column(Float)
    lease_date = Column(DateTime)
    duration_month = Column(Integer)
    monthly_rent = Column(Float)
    rent_m2 = Column(Float)

    #foreign keys:
    register_no = Column(String, ForeignKey('va_info_parcel.register_no'))
    register_no_ref = relationship("VaInfoHomeParcel")

    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")
