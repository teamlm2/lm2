__author__ = 'anna'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *


class SetApplicationTypeLanduseType(Base):

    __tablename__ = 'set_application_type_landuse_type'

    application_type = Column(String, ForeignKey('cl_application_type.code'), primary_key=True)
    application_type_ref = relationship("ClApplicationType")

    landuse_type = Column(Integer, ForeignKey('cl_landuse_type.code'), primary_key=True)
    landuse_type_ref = relationship("ClLanduseType")