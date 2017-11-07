__author__ = 'ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class VaTypePurchaseOrLease(Base):

    __tablename__ = 'cl_type_purchase_or_lease'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)

