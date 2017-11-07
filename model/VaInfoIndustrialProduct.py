__author__ = 'ankhbold'

from sqlalchemy import Column, Integer, String, Date, Sequence, ForeignKey, DateTime
from CaParcel import *

class VaInfoIndustrialProduct(Base):

    __tablename__ = 'va_info_industrial_product'

    id = Column(Integer, primary_key=True)
    count_product = Column(Float)
    cost_per_item = Column(Float)
    come_per_item = Column(Float)

    #foreign keys:
    register_no = Column(String, ForeignKey('va_info_parcel.register_no'))
    register_no_ref = relationship("VaInfoHomeParcel")

    product = Column(Integer, ForeignKey('cl_type_product.code'))
    product_ref = relationship("VaTypeProduct")

    product_time = Column(Integer, ForeignKey('cl_type_product_time.code'))
    product_time_ref = relationship("VaTypeProductTime")

    industrial_process = Column(Integer, ForeignKey('cl_type_industrial_process.code'))
    industrial_process_ref = relationship("VaTypeIndustrialProcess")
