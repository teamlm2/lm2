__author__ = 'Ankhaa'

from sqlalchemy import Column, String, Integer
from Base import *


class ClUserCancelReason(Base):

    __tablename__ = 'cl_user_cancel_reason'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)