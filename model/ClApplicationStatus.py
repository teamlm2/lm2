__author__ = 'anna'

from sqlalchemy import Column, String, Integer
from Base import *


class ClApplicationStatus(Base):

    __tablename__ = 'cl_application_status'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
