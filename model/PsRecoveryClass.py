__author__ = 'Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey, Date, Numeric
from Base import *


class PsRecoveryClass(Base):
    __tablename__ = 'ps_recovery_class'

    id = Column(Integer, primary_key=True)
    rc_code = Column(String)
    description = Column(String)
    rc_code_number = Column(Integer)
    rc_precent = Column(Integer)