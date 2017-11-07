__author__ = 'B.Ankhbold'

from sqlalchemy import ForeignKey, Column, String, Integer, Numeric, Boolean, Float
from Base import *
from sqlalchemy.orm import relationship
from ClBioMass import *

class PsAvgReserveDaats(Base):

    __tablename__ = 'ps_avg_reserve_daats'

    id = Column(Integer, primary_key=True)
    current_year = Column(Integer)
    avg_sheep_unit = Column(Float)
    avg_d3 = Column(Float)
    avg_unelgee = Column(Numeric)

    # foreign keys:
    reserve_level_type = Column(Integer, ForeignKey('pcl_reserve_daats_level.code'), primary_key=True)
    reserve_level_type_ref = relationship("PClReserveDaatsLevel")

    reserve_zone = Column(String, ForeignKey('au_reserve_zone.code'))
    reserve_zone_ref = relationship("AuReserveZone")

    reserve_parcel = Column(String, ForeignKey('ps_parcel.parcel_id'))
    reserve_parcel_ref = relationship("PsParcel")
