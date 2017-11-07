__author__ = 'mwagner'

from sqlalchemy import Column, String, Integer
from Base import *


class ClPaymentType(Base):

    __tablename__ = 'cl_payment_type'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
