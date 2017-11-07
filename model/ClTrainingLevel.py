__author__ = 'B.Ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class ClTrainingLevel(Base):

    __tablename__ = 'cl_training_level'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
