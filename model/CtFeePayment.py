__author__ = 'mwagner'

from sqlalchemy import Date, Sequence, ForeignKeyConstraint
from CtFee import *
from ClPaymentType import *


class CtFeePayment(Base):

    __tablename__ = 'ct_fee_payment'
    __table_args__ = (ForeignKeyConstraint(['contract', 'person'], ['ct_fee.contract', 'ct_fee.person']),)

    id = Column(Integer, Sequence('ct_fee_payment_id_seq'), primary_key=True)
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
    contract = Column(String, nullable=False)
    person = Column(String, nullable=False)

    # foreign keys:
    payment_type = Column(Integer, ForeignKey('cl_payment_type.code'))
    payment_type_ref = relationship("ClPaymentType")
