__author__ = 'B.Ankhbold'

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import relationship
from CtDecision import *
from CtDocument import *


class SetEquipmentDocument(Base):

    __tablename__ = 'set_equipment_document'

    equipment = Column(String, ForeignKey("set_equipment.id"), primary_key=True)
    equipment_ref = relationship("SetEquipment")

    document = Column(String, ForeignKey("set_document.id"), primary_key=True)
    document_ref = relationship("SetDocument")

