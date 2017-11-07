__author__ = 'anna'

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import relationship
from SetFeeZone import *
from SetDocument import *


class SetFeeDocument(Base):

    __tablename__ = 'set_fee_document'

    fee = Column(String, ForeignKey("set_fee_zone.zone_id"), primary_key=True)
    fee_ref = relationship("SetFeeZone")

    document = Column(String, ForeignKey("set_document.id"), primary_key=True)
    document_ref = relationship("SetDocument")