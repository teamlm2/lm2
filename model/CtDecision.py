__author__ = 'mwagner'

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import relationship
from ClDecision import *
from ClDecisionLevel import *
from CtDecisionApplication import *
from CtDecisionDocument import *

from CtDocument import *


class CtDecision(Base):

    __tablename__ = 'ct_decision'

    decision_no = Column(String, primary_key=True)
    decision_date = Column(Date)

    # other foreign keys:
    decision_level = Column(Integer, ForeignKey('cl_decision_level.code'))
    decision_level_ref = relationship("ClDecisionLevel")

    results = relationship("CtDecisionApplication", lazy='dynamic')
    documents = relationship("CtDecisionDocument", lazy="dynamic", cascade="all, delete-orphan")

    imported_by = Column(String, ForeignKey('set_role.user_name_real'))
    imported_by_ref = relationship("SetRole")