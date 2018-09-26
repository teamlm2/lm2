__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *


class SetOrganizationRightType(Base):
    __tablename__ = 'set_organization_type_right_type'

    organization = Column(Integer, ForeignKey('sd_organization.id'), primary_key=True)
    organization_ref = relationship("SdOrganization")

    right_type = Column(String, ForeignKey('cl_right_type.code'), primary_key=True)
    right_type_ref = relationship("ClRightType")