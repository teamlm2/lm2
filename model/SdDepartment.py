__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey,Sequence
from sqlalchemy.orm import relationship, backref
from Base import *

class SdDepartment(Base):

    __tablename__ = 'hr_department'

    department_id = Column(String, primary_key=True)
    code = Column(String)
    name = Column(String)
    parent_id = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    address = Column(String)
    fax = Column(String)
    phone = Column(String)
    website = Column(String)
    report_email = Column(String)

    organization = Column(String, ForeignKey('sd_organization.id'))
    organization_ref = relationship("SdOrganization")

    au1 = Column(String, ForeignKey('au_level1.code'))
    au1_ref = relationship("AuLevel1")

    au2 = Column(String, ForeignKey('au_level2.code'))
    au2_ref = relationship("AuLevel2")
