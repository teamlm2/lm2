__author__ = 'Anna'

from sqlalchemy import Column, Numeric, Integer, Sequence, ForeignKey, String
from Base import *
from sqlalchemy.orm import relationship


class SetBaseTaxAndPrice(Base):

    __tablename__ = 'set_base_tax_and_price'

    id = Column(Integer, Sequence('set_base_tax_and_price_id_seq'), primary_key=True)
    base_value_per_m2 = Column(Integer)
    base_tax_rate = Column(Numeric)
    subsidized_area = Column(Integer)
    subsidized_tax_rate = Column(Numeric)

    # foreign keys:
    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")

    tax_zone = Column(String, ForeignKey('set_tax_and_price_zone.zone_id'))
