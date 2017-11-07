__author__ = 'Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship
from Base import *


class PsPastureEvaluationFormula(Base):
    __tablename__ = 'ps_pasture_evaluation_formula'

    natural_zone = Column(Integer, ForeignKey('cl_natural_zone.code'), primary_key=True)
    natural_zone_ref = relationship("ClNaturalZone")

    soil_evaluation = Column(Integer, ForeignKey('ps_soil_evaluation.code'))
    soil_evaluation_ref = relationship("PsSoilEvaluation")

    land_form = Column(Integer, ForeignKey('cl_land_form.code'), primary_key=True)
    land_form_ref = relationship("ClLandForm")

    rc_id = Column(Integer, ForeignKey('ps_recovery_class.id'), primary_key=True)
    rc_id_ref = relationship("PsRecoveryClass")