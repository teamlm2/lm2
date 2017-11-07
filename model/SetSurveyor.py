__author__ = 'Ankhaa'

from sqlalchemy import Column, String, Integer, Sequence, ForeignKey
from Base import *


class SetSurveyor(Base):

    __tablename__ = 'set_surveyor'

    id = Column(String, primary_key=True)
    surname = Column(String)
    first_name = Column(String)
    phone = Column(String)

    # foreign keys:
    company = Column(Integer, ForeignKey('set_survey_company.id'))
