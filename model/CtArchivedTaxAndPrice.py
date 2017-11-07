__author__ = 'mwagner'

from sqlalchemy import ForeignKey, Column, String, Integer, Numeric, Date, Sequence
from Base import *


class CtArchivedTaxAndPrice(Base):

    __tablename__ = 'ct_archived_tax_and_price'

    id = Column(Integer, Sequence('ct_archived_tax_and_price_id_seq'), primary_key=True)
    record = Column(String, ForeignKey('ct_ownership_record.record_no'))
    person = Column(String, ForeignKey('bs_person.person_id'))
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
    valid_from = Column(Date)
    valid_till = Column(Date)

    # foreign keys:
    payment_frequency = Column(Integer, ForeignKey('cl_payment_frequency.code'))