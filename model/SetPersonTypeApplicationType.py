__author__ = 'Anna'

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from Base import *


class SetPersonTypeApplicationType(Base):

    __tablename__ = 'set_person_type_application_type'

    application_type = Column(Integer, ForeignKey('cl_application_type.code'), primary_key=True)
    application_type_ref = relationship("ClApplicationType")

    person_type = Column(Integer, ForeignKey('cl_person_type.code'), primary_key=True)
    person_type_ref = relationship("ClPersonType")
