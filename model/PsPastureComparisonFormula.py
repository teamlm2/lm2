__author__ = 'Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship
from Base import *


class PsPastureComparisonFormula(Base):
    __tablename__ = 'ps_pasture_comparison_formula'

    natural_zone = Column(Integer, ForeignKey('cl_natural_zone.code'), primary_key=True)
    natural_zone_ref = relationship("ClNaturalZone")

    plants = Column(Integer, ForeignKey('cl_pasture_values.code'), primary_key=True)
    plants_ref = relationship("ClPastureValues")

    land_form = Column(Integer, ForeignKey('cl_land_form.code'), primary_key=True)
    land_form_ref = relationship("ClLandForm")

    rc_id = Column(Integer, ForeignKey('ps_recovery_class.id'), primary_key=True)
    rc_id_ref = relationship("PsRecoveryClass")

    symbol_id = Column(Integer, ForeignKey('pcl_less_symbol.code'))
    symbol_id_ref = relationship("PClLessSymbol")