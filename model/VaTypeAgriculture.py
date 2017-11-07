__author__ = 'ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class VaTypeAgriculture(Base):

    __tablename__ = 'cl_type_agriculture'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)

