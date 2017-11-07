__author__ = 'Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *


class PsNaturalZonePlants(Base):
    __tablename__ = 'ps_natural_zone_plants'
    natural_zone = Column(Integer, ForeignKey('cl_natural_zone.code'), primary_key=True)
    natural_zone_ref = relationship("ClNaturalZone")

    plants = Column(Integer, ForeignKey('cl_pasture_values.code'), primary_key=True)
    plants_ref = relationship("ClPastureValues")