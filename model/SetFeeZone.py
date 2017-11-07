__author__ = 'Anna'

from sqlalchemy import String,Date
from geoalchemy2 import Geometry
from SetBaseFee import *


class SetFeeZone(Base):

    __tablename__ = 'set_fee_zone'

    location = Column(String)
    zone_no = Column(Integer)
    area_m2 = Column(Numeric)
    valid_from = Column(Date)
    valid_till = Column(Date)
    zone_id = Column(String, primary_key=True)
    name = Column(String)
    code = Column(String)
    geometry = Column(Geometry('MULTIPOLYGON', srid=4326))
    fees = relationship("SetBaseFee", backref='parent', cascade="all, delete, delete-orphan")
    documents = relationship("SetFeeDocument", lazy="dynamic", cascade="all, delete-orphan")
