__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from Base import *

class SetUserPosition(Base):

    __tablename__ = 'set_user_position'

    user_name_real = Column(Integer, ForeignKey("set_role.user_name_real"), primary_key=True)
    user_name_real_ref = relationship("SetRole")

    position = Column(Integer, ForeignKey("cl_position_type.code"), primary_key=True)
    position_ref = relationship("ClPositionType")
