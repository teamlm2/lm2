__author__ = 'anna'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *


class CtRecordDocument(Base):

    __tablename__ = 'ct_record_document'

    record = Column(String, ForeignKey('ct_ownership_record.record_no'), primary_key=True)
    document = Column(Integer, ForeignKey('ct_document.id'), primary_key=True)

    document_ref = relationship("CtDocument", backref="contracts", cascade="all")

    role = Column(Integer, ForeignKey('cl_document_role.code'))
    role_ref = relationship('ClDocumentRole')