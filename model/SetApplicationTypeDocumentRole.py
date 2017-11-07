__author__ = 'anna'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *


class SetApplicationTypeDocumentRole(Base):
    __tablename__ = 'set_application_type_document_role'
    application_type = Column(String, ForeignKey('cl_application_type.code'), primary_key=True)
    application_type_ref = relationship("ClApplicationType")

    document_role = Column(Integer, ForeignKey('cl_document_role.code'), primary_key=True)
    document_role_ref = relationship("ClDocumentRole")