__author__ = 'Ankhaa'

from sqlalchemy import Column, String, Integer, Sequence
from Base import *


class SetValidation(Base):

    __tablename__ = 'set_validation'

    set_validation_id = Column(Integer, Sequence('set_validation_id'), primary_key=True)
    sql_statement = Column(String)
