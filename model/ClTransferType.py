__author__ = 'mwagner'

from sqlalchemy import Column, String, Integer
from Base import *


class ClTransferType(Base):

    __tablename__ = 'cl_transfer_type'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
