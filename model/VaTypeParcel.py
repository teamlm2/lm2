__author__ = 'ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class VaTypeParcel(Base):

    __tablename__ = 'cl_type_parcel'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)

