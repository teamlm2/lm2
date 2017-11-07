__author__ = 'B.Ankhbold'

from sqlalchemy import String,Date, Integer, Column, Sequence
from geoalchemy2 import Geometry
from Base import *


class SetTraining(Base):

    __tablename__ = 'set_training'

    id = Column(Integer, Sequence('set_training_id_seq'), primary_key=True)
    location = Column(String)
    begin_date = Column(Date)
    end_date = Column(Date)
    description = Column(String)