__author__ = 'B.Ankhbold'

from sqlalchemy import Date
from sqlalchemy import Column, Integer, String, Date, Sequence, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, backref
from Base import *

bag_table = Table('ct_pasture_group_bag', Base.metadata,
                        Column('group_no', Integer, ForeignKey('ct_person_group.group_no')),
                        Column('bag', String, ForeignKey('au_level3.code'))
                    )

class CtPersonGroup(Base):

    __tablename__ = 'ct_person_group'

    group_no = Column(Integer, primary_key=True)
    group_name = Column(String)
    is_contract = Column(String)
    created_date = Column(Date)

    bags = relationship("AuLevel3", secondary=bag_table)

    members = relationship("CtGroupMember", backref="member_ref",
                                lazy='dynamic', cascade="all, delete-orphan")