__author__ = 'Ankhaa'

from sqlalchemy.orm import relationship
from SetSurveyor import *


class SetSurveyCompany(Base):

    __tablename__ = 'set_survey_company'

    id = Column(String, primary_key=True)
    name = Column(String)
    address = Column(String)
    surveyors = relationship("SetSurveyor", backref='parent', cascade="all, delete, delete-orphan")



