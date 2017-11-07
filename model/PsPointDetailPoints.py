__author__ = 'Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *


class PsPointDetailPoints(Base):
    __tablename__ = 'ps_point_detail_points'
    point_detail_id = Column(String, ForeignKey('ps_point_detail.point_detail_id'), primary_key=True)
    point_detail_id_ref = relationship("PsPointDetail")

    point_id = Column(String, ForeignKey('ca_pasture_monitoring.point_id'), primary_key=True)
    point_id_ref = relationship("CaPastureMonitoring")