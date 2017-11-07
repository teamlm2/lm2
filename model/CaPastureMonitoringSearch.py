
__author__ = 'B.Ankhbold'
from sqlalchemy import Column, String, Float, Date, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from ClLanduseType import *


class CaPastureMonitoring(Base):

    __tablename__ = 'ca_pasture_monitoring_search'

    point_id = Column(String, primary_key=True)
    x_coordinate = Column(Float)
    y_coordinate = Column(Float)
    valid_from = Column(Date)
    valid_till = Column(Date)
    geometry = Column(Geometry('Point', 4326))
