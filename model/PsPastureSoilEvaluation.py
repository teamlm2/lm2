__author__ = 'Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship
from Base import *


class PsPastureSoilEvaluation(Base):

    __tablename__ = 'ps_pasture_soil_evaluation'

    current_year = Column(Integer, primary_key=True)

    point_detail_id = Column(String, ForeignKey('ps_point_detail.point_detail_id'), primary_key=True)
    point_detail_id_ref = relationship("PsPointDetail")

    soil_evaluation = Column(Integer, ForeignKey('ps_soil_evaluation.code'))
    soil_evaluation_ref = relationship("PsSoilEvaluation")