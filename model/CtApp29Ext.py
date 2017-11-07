__author__ = 'Ankhbold'

from sqlalchemy import Date, ForeignKey, Integer, String, Column
from sqlalchemy.orm import relationship
from ClCourtStatus import *


class CtApp29Ext(Base):

    __tablename__ = 'ct_app29_ext'

    app_no = Column(String, ForeignKey('ct_application.app_no'), primary_key=True)
    start_period = Column(Date)
    end_period = Column(Date)

    # other foreign keys:
    court_status = Column(Integer, ForeignKey('cl_court_status.code'))
    court_status_ref = relationship("ClCourtStatus")
