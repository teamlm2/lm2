__author__ = 'anna'

from sqlalchemy import Column, String, Integer
from Base import *


class ClContractCondition(Base):

    __tablename__ = 'cl_contract_condition'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
