__author__ = 'B.Ankhbold'
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from Base import *


class CtAppGroupBoundary(Base):

    __tablename__ = 'ct_app_group_boundary'

    application = Column(String, ForeignKey('ct_application.app_no'), primary_key=True)
    group_no = Column(Integer, ForeignKey('ct_person_group.group_no'), primary_key=True)
    boundary_code = Column(String, ForeignKey('ca_pug_boundary.code'), primary_key=True)