__author__ = 'mwagner'

from sqlalchemy import Column, Numeric, Integer, Sequence
from Base import *


class SetPayment(Base):

    __tablename__ = 'set_payment'

    id = Column(Integer, Sequence('set_payment_id_seq'), primary_key=True)
    landfee_fine_rate_per_day = Column(Numeric)
    landtax_fine_rate_per_day = Column(Numeric)
