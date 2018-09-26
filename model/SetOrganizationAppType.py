__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *


class SetOrganizationAppType(Base):
    __tablename__ = 'set_organization_type_app_type'
    application_type = Column(String, ForeignKey('cl_application_type.code'), primary_key=True)
    application_type_ref = relationship("ClApplicationType")

    organization = Column(Integer, ForeignKey('sd_organization.id'), primary_key=True)
    organization_ref = relationship("SdOrganization")