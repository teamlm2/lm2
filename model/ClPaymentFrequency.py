__author__ = 'anna'

from sqlalchemy import Column, String, Integer
from Base import *


class ClPaymentFrequency(Base):

    __tablename__ = 'cl_payment_frequency'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
