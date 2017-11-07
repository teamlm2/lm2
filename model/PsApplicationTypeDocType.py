__author__ = 'Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *


class PsApplicationTypeDocType(Base):
    __tablename__ = 'ps_app_type_doc_type'
    document = Column(Integer, ForeignKey('cl_pasture_document.code'), primary_key=True)
    document_ref = relationship("ClPastureDocument")

    app_type = Column(Integer, ForeignKey('cl_application_type.code'), primary_key=True)
    app_type_ref = relationship("ClApplicationType")

    parent_type = Column(Integer)