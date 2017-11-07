__author__ = 'mwagner'

from sqlalchemy import ForeignKey, Column, String, Integer, Numeric
from Base import *
from sqlalchemy.orm import relationship
from CtFeePayment import *
from CtFineForFeePayment import *
from ClPaymentFrequency import *


class CtFee(Base):

    __tablename__ = 'ct_fee'

    contract = Column(String, ForeignKey('ct_contract.contract_no'), primary_key=True)
    person = Column(String, ForeignKey('bs_person.person_id'), primary_key=True)
    share = Column(Numeric)
    area = Column(Integer)
    fee_calculated = Column(Integer)
    fee_contract = Column(Integer)
    grace_period = Column(Integer)
    base_fee_per_m2 = Column(Integer)
    subsidized_area = Column(Integer)
    subsidized_fee_rate = Column(Numeric)

    # foreign keys:
    payment_frequency = Column(Integer, ForeignKey('cl_payment_frequency.code'))
    payment_frequency_ref = relationship("ClPaymentFrequency")

    payments = relationship("CtFeePayment", backref='fee_ref', lazy='dynamic', cascade="all, delete, delete-orphan")
    fine_payments = relationship("CtFineForFeePayment", backref='fee_ref', lazy='dynamic', cascade="all, delete, delete-orphan")