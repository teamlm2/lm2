__author__ = 'anna'

from sqlalchemy import Column, String, Integer
from Base import *


class ClDocumentRole(Base):

    __tablename__ = 'cl_document_role'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
