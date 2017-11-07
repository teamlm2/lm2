__author__ = 'B.Ankhbold'
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from Base import *


class CtApplicationPUG(Base):

    __tablename__ = 'ct_application_pug'

    group_no = Column(Integer, ForeignKey('ct_person_group.group_no'), primary_key=True)
    application = Column(String, ForeignKey('ct_application.app_no'), primary_key=True)
