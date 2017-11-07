__author__ = 'mwagner'

from sqlalchemy import Column, String, Integer
from Base import *


class ClContractStatus(Base):

    __tablename__ = 'cl_contract_status'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
