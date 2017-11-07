__author__ = 'anna'
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *


class CtApplicationDocument(Base):

    __tablename__ = 'ct_application_document'

    application = Column(String, ForeignKey('ct_application.app_no'), primary_key=True)
    document = Column(Integer, ForeignKey('ct_document.id'), primary_key=True)
    role = Column(Integer, ForeignKey('cl_document_role.code'))
    person = Column(String, ForeignKey('bs_person.person_id'))

    document_ref = relationship("CtDocument", backref="applications", cascade="all")
    person_ref = relationship("BsPerson", backref="application_documents")