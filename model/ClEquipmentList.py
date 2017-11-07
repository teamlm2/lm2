__author__ = 'anna'

from sqlalchemy import Column, String, Integer
from Base import *


class ClEquipmentList(Base):

    __tablename__ = 'cl_equipment_list'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
