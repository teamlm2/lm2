__author__ = 'Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey, String
from sqlalchemy.orm import relationship
from Base import *


class PsFormulaTypeLandForm(Base):
    __tablename__ = 'ps_formula_type_land_form'
    formula_type = Column(Integer, ForeignKey('pcl_formula_type.code'), primary_key=True)
    formula_type_ref = relationship("PClFormulaType")

    land_form = Column(Integer, ForeignKey('cl_land_form.code'), primary_key=True)
    land_form_ref = relationship("ClLandForm")