__author__ = 'Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey, Date, Numeric
from sqlalchemy.orm import relationship
from Base import *


class PsPointDetail(Base):
    __tablename__ = 'ps_point_detail'

    point_detail_id = Column(String, primary_key=True)
    register_date = Column(Date)
    land_name = Column(String)
    elevation = Column(Numeric)
    scale = Column(Numeric)

    land_form = Column(Integer, ForeignKey('cl_land_form.code'))
    land_form_ref = relationship("ClLandForm")