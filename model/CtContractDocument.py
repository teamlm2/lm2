__author__ = 'anna'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *


class CtContractDocument(Base):

    __tablename__ = 'ct_contract_document'

    contract = Column(String, ForeignKey('ct_contract.contract_no'), primary_key=True)

    document = Column(Integer, ForeignKey('ct_document.id'), primary_key=True)
    document_ref = relationship("CtDocument", backref="records", cascade="all")

    role = Column(Integer, ForeignKey('cl_document_role.code'))
    role_ref = relationship('ClDocumentRole')