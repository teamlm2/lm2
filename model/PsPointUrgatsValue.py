__author__ = 'B.Ankhbold'

from sqlalchemy import ForeignKey, Column, String, Integer, Numeric, Boolean, Float
from Base import *
from ClBioMass import *
from sqlalchemy.orm import relationship

class PsPointUrgatsValue(Base):

    __tablename__ = 'ps_point_urgats_value'

    point_detail_id = Column(String, ForeignKey('ps_point_detail.point_detail_id'), primary_key=True)
    value_year = Column(Integer, primary_key=True)

    m_1 = Column(Integer)
    m_1_value = Column(Numeric)
    m_2 = Column(Integer)
    m_2_value = Column(Numeric)
    m_3 = Column(Integer)
    m_3_value = Column(Numeric)
    biomass_kg_ga = Column(Numeric)

    # foreign keys:
    biomass_type = Column(Integer, ForeignKey('cl_biomass.code'))
    biomass_type_ref = relationship("ClBioMass")
