__author__ = 'ankhbold'

from sqlalchemy import Column, String, Integer
from Base import *


class ClOrganizationType(Base):

    __tablename__ = 'cl_organization_type'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
