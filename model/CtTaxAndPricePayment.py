__author__ = 'mwagner'

from sqlalchemy import Date, Sequence, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from CtTaxAndPrice import *
from ClPaymentType import *


class CtTaxAndPricePayment(Base):

    __tablename__ = 'ct_tax_and_price_payment'
    __table_args__ = (ForeignKeyConstraint(['record', 'person'], ['ct_tax_and_price.record', 'ct_tax_and_price.person']),)

    id = Column(Integer, Sequence('ct_tax_and_price_payment_id_seq'), primary_key=True)
    date_paid = Column(Date)
    amount_paid = Column(Integer)
    year_paid_for = Column(Integer)
    paid_total = Column(Integer)
    delay_to_dl1 = Column(Integer)
    delay_to_dl2 = Column(Integer)
    delay_to_dl3 = Column(Integer)
    delay_to_dl4 = Column(Integer)
    left_to_pay_for_q1 = Column(Integer)
    left_to_pay_for_q2 = Column(Integer)
    left_to_pay_for_q3 = Column(Integer)
    left_to_pay_for_q4 = Column(Integer)
    fine_for_q1 = Column(Integer)
    fine_for_q2 = Column(Integer)
    fine_for_q3 = Column(Integer)
    fine_for_q4 = Column(Integer)
    record = Column(String, nullable=False)
    person = Column(String, nullable=False)

    # foreign keys:
    payment_type = Column(Integer, ForeignKey('cl_payment_type.code'))
    payment_type_ref = relationship("ClPaymentType")
