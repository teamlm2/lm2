__author__ = 'mwagner'

from sqlalchemy import Column, Integer, String, Date
from Base import *


class PersonSearch(Base):

    __tablename__ = 'person_search'

    name = Column(String)
    middle_name = Column(String)
    first_name = Column(String)
    person_id = Column(String, primary_key=True)
    state_registration_no = Column(String)
    mobile_phone = Column(String)
    phone = Column(String)
    parcel_id = Column(String)
    tmp_parcel_id = Column(String)
    app_no = Column(String)
    decision_no = Column(String)
    contract_no = Column(String)
    record_no = Column(String)
    type = Column(Integer)
    app_type = Column(Integer)
