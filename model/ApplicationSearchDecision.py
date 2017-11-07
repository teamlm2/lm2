__author__ = 'anna'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *
from ClApplicationStatus import *
from ClApplicationType import *
from SetRole import *


class ApplicationSearchDecision(Base):

    __tablename__ = 'application_search_decision'

    app_no = Column(Integer, primary_key=True)
    decision_no = Column(String)
    contract_no = Column(String)
    record_no = Column(String)
    person_id = Column(String)
    name = Column(String)
    first_name = Column(String)
    middle_name = Column(String)
    parcel_id = Column(String)
    status_date = Column(Date)

    app_type = Column(Integer, ForeignKey('cl_application_type.code'))
    app_type_ref = relationship("ClApplicationType")

    status = Column(Integer, ForeignKey('cl_application_status.code'))
    status_ref = relationship("ClApplicationStatus")

    officer_in_charge = Column(String, ForeignKey('set_role.user_name'))
    officer_in_charge_ref = relationship("SetRole", foreign_keys=[officer_in_charge])

    next_officer_in_charge = Column(String, ForeignKey('set_role.user_name'))
    next_officer_in_charge_ref = relationship("SetRole", foreign_keys=[next_officer_in_charge])