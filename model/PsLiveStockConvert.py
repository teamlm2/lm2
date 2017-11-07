__author__ = 'B.Ankhbold'

from sqlalchemy import ForeignKey, Column, String, Integer, Numeric, Boolean, Float
from Base import *
from sqlalchemy.orm import relationship
from CtFeePayment import *
from CtFineForFeePayment import *
from ClPaymentFrequency import *


class PsLiveStockConvert(Base):

    __tablename__ = 'ps_live_stock_convert'

    convert_value = Column(Numeric)

    # foreign keys:
    live_stock_type = Column(Integer, ForeignKey('cl_livestock.code'), primary_key=True)
    live_stock_type_ref = relationship("ClliveStock")
