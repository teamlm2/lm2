__author__ = 'anna'

from sqlalchemy import ForeignKey, Column, String, Integer
from sqlalchemy.orm import relationship
from Base import *
from CtContract import *
from CtApplication import *
from ClApplicationRole import *


class CtRecordApplicationRole(Base):

    __tablename__ = 'ct_record_application_role'

    record = Column(String, ForeignKey('ct_ownership_record.record_no'), primary_key=True)

    application = Column(String, ForeignKey('ct_application.app_no'), primary_key=True)
    application_ref = relationship("CtApplication")

    role = Column(Integer, ForeignKey('cl_application_role.code'))
    #role_ref = relationship("ClApplicationRole")
