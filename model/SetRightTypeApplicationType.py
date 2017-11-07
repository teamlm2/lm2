__author__ = 'anna'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *
from ClRightType import *


class SetRightTypeApplicationType(Base):

    __tablename__ = 'set_right_type_application_type'

    application_type = Column(String, ForeignKey('cl_application_type.code'), primary_key=True)
    application_type_ref = relationship("ClApplicationType")

    right_type = Column(Integer, ForeignKey('cl_right_type.code'), primary_key=True)
    right_type_ref = relationship("ClRightType")