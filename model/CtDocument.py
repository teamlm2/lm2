__author__ = 'mwagner'

from sqlalchemy import Column, String, Integer, Sequence, Binary
from Base import *


class CtDocument(Base):

    __tablename__ = 'ct_document'

    id = Column(Integer, Sequence('ct_document_id_seq'), primary_key=True)
    name = Column(String)
    content = Column(Binary)
