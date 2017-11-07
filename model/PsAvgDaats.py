__author__ = 'B.Ankhbold'

from sqlalchemy import ForeignKey, Column, String, Integer, Numeric, Boolean, Float
from Base import *
from sqlalchemy.orm import relationship
from ClBioMass import *

class PsAvgDaats(Base):

    __tablename__ = 'ps_avg_daats'

    id = Column(Integer, primary_key=True)
    current_year = Column(Integer)
    avg_sheep_unit = Column(Float)
    avg_d3 = Column(Float)
    avg_unelgee = Column(Numeric)
    pasture_group = Column(String)
    pasture_parcel = Column(String)

    # foreign keys:
    daats_level_type = Column(Integer, ForeignKey('pcl_pasture_daats_level.code'), primary_key=True)
    daats_level_type_ref = relationship("PClPastureDaatsLevel")

    level1 = Column(String, ForeignKey('au_level1.code'))
    level1_ref = relationship("AuLevel1")

    level2 = Column(String, ForeignKey('au_level2.code'))
    level2_ref = relationship("AuLevel2")

    level3 = Column(String, ForeignKey('au_level3.code'))
    level3_ref = relationship("AuLevel3")
