__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey,Sequence
from sqlalchemy.orm import relationship, backref
from Base import *

class SdPosition(Base):

    __tablename__ = 'hr_position'

    position_id = Column(String, primary_key=True)
    code = Column(String)
    name = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    organization = Column(String, ForeignKey('sd_organization.id'))
    organization_ref = relationship("SdOrganization")

    department = Column(String, ForeignKey('hr_department.department_id'))
    department_ref = relationship("SdDepartment")
