__author__ = 'Anna'

from sqlalchemy import String
from geoalchemy2 import Geometry
from SetBaseTaxAndPrice import *


class SetTaxAndPriceZone(Base):

    __tablename__ = 'set_tax_and_price_zone'

    location = Column(String)
    zone_no = Column(Integer)
    area_m2 = Column(Numeric)
    geometry = Column(Geometry('MULTIPOLYGON', srid=4326))
    zone_id = Column(String, primary_key=True)
    name = Column(String)
    code = Column(String)
    taxes = relationship("SetBaseTaxAndPrice", backref='parent', cascade="all, delete, delete-orphan")
