__author__ = 'mwagner'

from sqlalchemy import Column, Integer, String, Date, Float
from Base import *


class FeeUnified(Base):

    __tablename__ = 'land_fee_unified'

    contract_no = Column(String, primary_key=True)
    year_paid_for = Column(Integer)
    status = Column(Integer)
    fee_contract = Column(Integer)
    paid = Column(Integer)
    p_paid = Column(Integer)
    person_id = Column(String)
    landuse = Column(String)
    decision_date = Column(Date)
    decision_no = Column(String)
    first_name = Column(String)
    name = Column(String)
    contact_surname = Column(String)
    contact_first_name = Column(String)
    person_streetname = Column(String)
    person_khashaa = Column(String)
    parcel_id = Column(String)
    certificate_no = Column(String)
    person_bag = Column(String)
    bag_name = Column(String)
    mobile_phone = Column(String)
    area_m2 = Column(Float)
    approved_duration = Column(Integer)
    address_streetname = Column(String)
    address_khashaa = Column(String)



