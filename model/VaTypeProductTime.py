__author__ = 'ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class VaTypeProductTime(Base):

    __tablename__ = 'cl_type_product_time'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)

