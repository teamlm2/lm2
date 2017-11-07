__author__ = 'B.Ankhbold'

from sqlalchemy import ForeignKey, Column, String, Integer, Numeric, Boolean
from Base import *
from sqlalchemy.orm import relationship
from ClBioMass import *

class PsPointPastureValue(Base):

    __tablename__ = 'ps_point_pasture_value'

    point_detail_id = Column(String, ForeignKey('ps_point_detail.point_detail_id'), primary_key=True)
    current_value = Column(Numeric)
    value_year = Column(Integer, primary_key=True)
    is_cover = Column(Boolean)

    # foreign keys:
    pasture_value = Column(Integer, ForeignKey('cl_pasture_values.code'), primary_key=True)
    pasture_value_ref = relationship("ClPastureValues")
