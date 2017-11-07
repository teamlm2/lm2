__author__ = 'Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *


class PsContractDocType(Base):
    __tablename__ = 'ps_contract_doc_type'
    document = Column(Integer, ForeignKey('cl_pasture_document.code'), primary_key=True)
    document_ref = relationship("ClPastureDocument")

    app_type = Column(Integer, ForeignKey('cl_application_type.code'), primary_key=True)
    app_type_ref = relationship("ClApplicationType")