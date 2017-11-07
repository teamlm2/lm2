__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from Base import *

class SetPositionGroupRole(Base):

    __tablename__ = 'set_position_group_role'

    position = Column(Integer, ForeignKey("cl_position_type.code"), primary_key=True)
    position_ref = relationship("ClPositionType")

    group_role = Column(Integer, ForeignKey("cl_group_role.code"), primary_key=True)
    group_role_ref = relationship("ClGroupRole")

    r_view = Column(Boolean)
    r_add = Column(Boolean)
    r_remove = Column(Boolean)
    r_update = Column(Boolean)