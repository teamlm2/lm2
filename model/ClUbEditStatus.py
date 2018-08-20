__author__ = 'B.Ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class ClUbEditStatus(Base):

    __tablename__ = 'cl_ub_edit_status'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
