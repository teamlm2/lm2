__author__ = 'B.Ankhbold'
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from Base import *



class CtGroupMember(Base):

    __tablename__ = 'ct_group_member'

    group_no = Column(Integer, ForeignKey('ct_person_group.group_no'), primary_key=True)
    person = Column(String, ForeignKey('bs_person.person_id'), primary_key=True)
    role = Column(Integer, ForeignKey('cl_member_role.code'))

    person_ref = relationship("BsPerson", backref="member_person_role", cascade="save-update")
    role_ref = relationship("ClMemberRole")