__author__ = 'mwagner'

from sqlalchemy import ForeignKey, Column, String, Integer
from sqlalchemy.orm import relationship
from Base import *
from CtContract import *
from CtApplication import *
from ClApplicationRole import *


class CtContractApplicationRole(Base):

    __tablename__ = 'ct_contract_application_role'

    contract = Column(String, ForeignKey('ct_contract.contract_no'), primary_key=True)

    application = Column(String, ForeignKey('ct_application.app_no'), primary_key=True)
    #application_ref = relationship("CtApplication")

    role = Column(Integer, ForeignKey('cl_application_role.code'))
    role_ref = relationship("ClApplicationRole")
