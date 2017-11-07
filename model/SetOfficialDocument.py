__author__ = 'anna'

from sqlalchemy import Column, String, Integer, Sequence, Binary, Boolean
from Base import *


class SetOfficialDocument(Base):

    __tablename__ = 'set_official_document'

    id = Column(Integer, Sequence('set_official_document_id_seq'), primary_key=True)
    name = Column(String)
    description = Column(String)
    visible = Column(Boolean)
    content = Column(Binary)
