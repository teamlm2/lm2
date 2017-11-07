__author__ = 'B.Ankhbold'

from sqlalchemy import ForeignKey, Column, String, Integer, Numeric, Boolean, Float
from Base import *
from sqlalchemy.orm import relationship

class PsPointLiveStockValue(Base):

    __tablename__ = 'ps_point_live_stock_value'

    point_detail_id = Column(String, ForeignKey('ps_point_detail.point_detail_id'), primary_key=True)
    current_value = Column(Numeric)
    value_year = Column(Integer, primary_key=True)

    # foreign keys:
    live_stock_type = Column(Integer, ForeignKey('cl_livestock.code'), primary_key=True)
    live_stock_type_ref = relationship("ClliveStock")
