__author__ = 'anna'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *


class SetContractDocumentRole(Base):
    __tablename__ = 'set_contract_document_role'

    role = Column(Integer, ForeignKey('cl_document_role.code'), primary_key=True)
    role_ref = relationship("ClDocumentRole")