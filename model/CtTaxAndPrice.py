__author__ = 'mwagner'

from sqlalchemy import ForeignKey, Column, String, Integer, Numeric
from CtFineForTaxPayment import *
from ClPaymentFrequency import *
from CtTaxAndPricePayment import *


class CtTaxAndPrice(Base):

    __tablename__ = 'ct_tax_and_price'

    record = Column(String, ForeignKey('ct_ownership_record.record_no'), primary_key=True)
    person = Column(String, ForeignKey('bs_person.person_id'), primary_key=True)
    share = Column(Numeric)
    area = Column(Integer)
    value_calculated = Column(Integer)
    price_paid = Column(Integer)
    land_tax = Column(Integer)
    grace_period = Column(Integer)
    base_value_per_m2 = Column(Integer)
    base_tax_rate = Column(Numeric)
    subsidized_area = Column(Integer)
    subsidized_tax_rate = Column(Numeric)

    # foreign keys:
    payment_frequency = Column(Integer, ForeignKey('cl_payment_frequency.code'))
    payment_frequency_ref = relationship("ClPaymentFrequency")

    payments = relationship("CtTaxAndPricePayment", backref='tax_ref', lazy='dynamic', cascade="all, delete, delete-orphan")
    fine_payments = relationship("CtFineForTaxPayment", backref='tax_ref', lazy='dynamic', cascade="all, delete, delete-orphan")