__author__ = 'ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class VaTypeStatusBuilding(Base):

    __tablename__ = 'cl_type_status_building'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)


