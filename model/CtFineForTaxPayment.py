__author__ = 'mwagner'

from sqlalchemy import ForeignKeyConstraint, Sequence, Date
from sqlalchemy.orm import relationship
from CtTaxAndPrice import *
from ClPaymentType import *


class CtFineForTaxPayment(Base):

    __tablename__ = 'ct_fine_for_tax_payment'
    __table_args__ = (ForeignKeyConstraint(['record', 'person'], ['ct_tax_and_price.record', 'ct_tax_and_price.person']),)

    id = Column(Integer, Sequence('ct_fine_for_tax_payment_id_seq'), primary_key=True)
    date_paid = Column(Date)
    amount_paid = Column(Integer)
    year_paid_for = Column(Integer)
    record = Column(String, nullable=False)
    person = Column(String, nullable=False)

    # foreign keys:
    payment_type = Column(Integer, ForeignKey('cl_payment_type.code'))
    payment_type_ref = relationship("ClPaymentType")
