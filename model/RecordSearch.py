__author__ = 'anna'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *
from ClApplicationType import *
from ClApplicationStatus import *
from SetRole import *


class RecordSearch(Base):

    __tablename__ = 'record_search'

    record_no = Column(Integer, primary_key=True)
    record_date = Column(Date)
    person_id = Column(String)
    name = Column(String)
    first_name = Column(String)
    middle_name = Column(String)
    parcel_id = Column(String)
    app_no = Column(String)
    decision_no = Column(String)
    au2_code = Column(String)
    status = Column(Integer)