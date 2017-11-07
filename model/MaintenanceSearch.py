__author__ = 'anna'

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from Base import *
from ClApplicationStatus import *
from ClApplicationType import *
from SetRole import *


class MaintenanceSearch(Base):

    __tablename__ = 'maintenance_search'

    id = Column(Integer, primary_key=True)
    completion_date = Column(Date)

    created_by = Column(String, ForeignKey('set_role.user_name'))
    completed_by = Column(String, ForeignKey('set_role.user_name'))

    parcel = Column(String)
    building = Column(String)
    app_no = Column(String)
    soum = Column(String)

    surveyed_by_land_office = Column(String)
    surveyed_by_surveyor = Column(String)

    company = Column(String)

    person_id = Column(String)
    name = Column(String)
    first_name = Column(String)