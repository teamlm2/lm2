__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from Base import *

class SetUserGroupRole(Base):

    __tablename__ = 'set_user_group_role'

    user_name_real = Column(String, ForeignKey("set_role.user_name_real"), primary_key=True)
    user_name_real_ref = relationship("SetRole")

    group_role = Column(Integer, ForeignKey("cl_group_role.code"), primary_key=True)
    group_role_ref = relationship("ClGroupRole")

    r_view = Column(Boolean)
    r_add = Column(Boolean)
    r_remove = Column(Boolean)
    r_update = Column(Boolean)