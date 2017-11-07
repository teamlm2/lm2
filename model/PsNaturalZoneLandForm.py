__author__ = 'Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey, String
from sqlalchemy.orm import relationship
from Base import *


class PsNaturalZoneLandForm(Base):
    __tablename__ = 'ps_natural_zone_land_form'
    natural_zone = Column(Integer, ForeignKey('cl_natural_zone.code'), primary_key=True)
    natural_zone_ref = relationship("ClNaturalZone")
    land_form_code = Column(String)
    land_form = Column(Integer, ForeignKey('cl_land_form.code'), primary_key=True)
    land_form_ref = relationship("ClLandForm")