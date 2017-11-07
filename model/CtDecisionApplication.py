__author__ = 'anna'

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import relationship
from ClDecision import *
from ClDecisionLevel import *
from CtDecision import *
from CtApplication import *


class CtDecisionApplication(Base):

    __tablename__ = 'ct_decision_application'

    application = Column(String, ForeignKey('ct_application.app_no'), primary_key=True)
    application_ref = relationship("CtApplication")

    decision = Column(String, ForeignKey("ct_decision.decision_no"))
    decision_ref = relationship("CtDecision")

    decision_result = Column(Integer, ForeignKey("cl_decision.code"))
    decision_result_ref = relationship("ClDecision")