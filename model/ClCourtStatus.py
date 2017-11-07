__author__ = 'Ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class ClCourtStatus(Base):

    __tablename__ = 'cl_court_status'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
