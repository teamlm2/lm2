__author__ = 'mwagner'

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import relationship
from ClMortgageType import *


class CtApp8Ext(Base):

    __tablename__ = 'ct_app8_ext'

    app_no = Column(String, ForeignKey('ct_application.app_no'), primary_key=True)
    start_mortgage_period = Column(Date)
    end_mortgage_period = Column(Date)

    # other foreign keys:
    mortgage_type = Column(Integer, ForeignKey('cl_mortgage_type.code'))
    mortgage_type_ref = relationship("ClMortgageType")

    mortgage_status = Column(Integer, ForeignKey('cl_mortgage_status.code'))
    mortgage_status_ref = relationship("ClMortgageStatus")
