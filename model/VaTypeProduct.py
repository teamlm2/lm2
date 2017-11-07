__author__ = 'ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class VaTypeProduct(Base):

    __tablename__ = 'cl_type_product'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)

