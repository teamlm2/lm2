__author__ = 'B.Ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class ClMemberRole(Base):

    __tablename__ = 'cl_member_role'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
