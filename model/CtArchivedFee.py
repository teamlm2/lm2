__author__ = 'mwagner'

from sqlalchemy import ForeignKey, Column, String, Integer, Numeric, Date, Sequence
from Base import *


class CtArchivedFee(Base):

    __tablename__ = 'ct_archived_fee'

    id = Column(Integer, Sequence('ct_archived_fee_id_seq'), primary_key=True)
    contract = Column(String, ForeignKey('ct_contract.contract_no'))
    person = Column(String, ForeignKey('bs_person.person_id'))
    share = Column(Numeric)
    area = Column(Integer)
    fee_calculated = Column(Integer)
    fee_contract = Column(Integer)
    grace_period = Column(Integer)
    base_fee_per_m2 = Column(Integer)
    subsidized_area = Column(Integer)
    subsidized_fee_rate = Column(Numeric)
    valid_from = Column(Date)
    valid_till = Column(Date)

    # foreign keys:
    payment_frequency = Column(Integer, ForeignKey('cl_payment_frequency.code'))