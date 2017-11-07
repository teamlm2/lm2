__author__ = 'Anna'

from sqlalchemy import Column, Numeric, Integer, Sequence, ForeignKey, String
from Base import *
from sqlalchemy.orm import relationship


class SetBaseFee(Base):

    __tablename__ = 'set_base_fee'

    id = Column(Integer, Sequence('set_base_fee_id_seq'), primary_key=True)
    base_fee_per_m2 = Column(Integer)
    subsidized_area = Column(Integer)
    subsidized_fee_rate = Column(Numeric)

    # foreign keys:
    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")

    fee_zone = Column(String, ForeignKey('set_fee_zone.zone_id'))
