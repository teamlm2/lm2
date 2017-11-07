__author__ = 'mwagner'

from sqlalchemy import Column, String, Integer, Sequence, Binary
from Base import *


class SetDocument(Base):

    __tablename__ = 'set_document'

    id = Column(Integer, Sequence('set_document_id_seq'), primary_key=True)
    name = Column(String)
    content = Column(Binary)
