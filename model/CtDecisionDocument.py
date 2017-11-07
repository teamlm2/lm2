__author__ = 'anna'

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import relationship
from CtDecision import *
from CtDocument import *


class CtDecisionDocument(Base):

    __tablename__ = 'ct_decision_document'

    decision = Column(String, ForeignKey("ct_decision.decision_no"), primary_key=True)
    decision_ref = relationship("CtDecision")

    document = Column(String, ForeignKey("ct_document.id"), primary_key=True)
    document_ref = relationship("CtDocument")

