__author__ = 'b.ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class ClliveStock(Base):

    __tablename__ = 'cl_livestock'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
