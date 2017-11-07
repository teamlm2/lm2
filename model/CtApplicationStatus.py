__author__ = 'anna'

from sqlalchemy import Column, String, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from Base import *
from SetRole import *


class CtApplicationStatus(Base):

    __tablename__ = 'ct_application_status'

    status_date = Column(Date)

    application = Column(String, ForeignKey('ct_application.app_no'), primary_key=True)
    #application_ref = relationship("CtApplication")

    status = Column(Integer, ForeignKey('cl_application_status.code'), primary_key=True)
    status_ref = relationship("ClApplicationStatus")

    officer_in_charge = Column(String, ForeignKey('set_role.user_name_real'))
    officer_in_charge_ref = relationship("SetRole", foreign_keys=[officer_in_charge], cascade="save-update")

    next_officer_in_charge = Column(String, ForeignKey('set_role.user_name_real'))
    next_officer_in_charge_ref = relationship("SetRole", foreign_keys=[next_officer_in_charge], cascade="save-update")
