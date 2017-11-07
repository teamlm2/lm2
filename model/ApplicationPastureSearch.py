__author__ = 'anna'

from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from Base import *
from ClApplicationStatus import *
from ClApplicationType import *
from SetRole import *


class ApplicationPastureSearch(Base):

    __tablename__ = 'pasture_app_search'

    app_no = Column(Integer, primary_key=True)
    group_no = Column(Integer)
    app_timestamp = Column(Date)
    decision_no = Column(String)
    contract_no = Column(String)
    record_no = Column(String)
    person_id = Column(String)
    name = Column(String)
    first_name = Column(String)
    middle_name = Column(String)
    parcel_id = Column(String)
    tmp_parcel_id = Column(String)
    status_date = Column(Date)

    app_type = Column(Integer, ForeignKey('cl_application_type.code'))
    app_type_ref = relationship("ClApplicationType")

    pasture_type = Column(Integer, ForeignKey('cl_pasture_type.code'))
    pasture_type_ref = relationship("ClPastureType")

    status = Column(Integer, ForeignKey('cl_application_status.code'))
    status_ref = relationship("ClApplicationStatus")

    officer_in_charge = Column(String, ForeignKey('set_role.user_name'))
    officer_in_charge_ref = relationship("SetRole", foreign_keys=[officer_in_charge])

    next_officer_in_charge = Column(String, ForeignKey('set_role.user_name'))
    next_officer_in_charge_ref = relationship("SetRole", foreign_keys=[next_officer_in_charge])