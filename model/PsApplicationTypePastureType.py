__author__ = 'Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *


class PsApplicationTypePastureType(Base):
    __tablename__ = 'ps_app_type_pasture_type'
    app_type = Column(String, ForeignKey('cl_application_type.code'), primary_key=True)
    app_type_ref = relationship("ClApplicationType")

    pasture_type = Column(Integer, ForeignKey('cl_pasture_type.code'), primary_key=True)
    pasture_type_ref = relationship("ClPastureType")