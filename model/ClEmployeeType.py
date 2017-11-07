__author__ = 'ankhaa'

from sqlalchemy import Column, String, Integer
from Base import *


class ClEmployeeType(Base):

    __tablename__ = 'cl_employee_type'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)