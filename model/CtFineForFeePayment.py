__author__ = 'mwagner'

from CtFee import *
from ClPaymentType import *


class CtFineForFeePayment(Base):

    __tablename__ = 'ct_fine_for_fee_payment'
    __table_args__ = (ForeignKeyConstraint(['contract', 'person'], ['ct_fee.contract', 'ct_fee.person']),)

    id = Column(Integer, Sequence('ct_fine_for_fee_payment_id_seq'), primary_key=True)
    date_paid = Column(Date)
    amount_paid = Column(Integer)
    year_paid_for = Column(Integer)
    contract = Column(String, nullable=False)
    person = Column(String, nullable=False)

    # foreign keys:
    payment_type = Column(Integer, ForeignKey('cl_payment_type.code'))
    payment_type_ref = relationship("ClPaymentType")
