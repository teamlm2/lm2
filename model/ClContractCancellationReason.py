__author__ = 'mwagner'

from sqlalchemy import Column, String, Integer
from Base import *


class ClContractCancellationReason(Base):

    __tablename__ = 'cl_contract_cancellation_reason'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
