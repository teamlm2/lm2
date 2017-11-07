__author__ = 'ankhbold'

from sqlalchemy import Column, Integer, String, Date, Sequence, ForeignKey, DateTime
from CaParcel import *

class VaInfoAgricultureOther(Base):

    __tablename__ = 'va_info_agriculture_other'

    id = Column(Integer, primary_key=True)
    other_price = Column(Float)
    other = Column(String)

    #foreign keys:
    register_no = Column(String, ForeignKey('va_info_parcel.register_no'))
    register_no_ref = relationship("VaInfoHomeParcel")

    irrigation = Column(Integer, ForeignKey('cl_type_irrigation_system.code'))
    irrigation_ref = relationship("VaTypeIrrigation")

