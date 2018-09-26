__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, Date, ForeignKey,Sequence
from sqlalchemy.orm import relationship, backref
from Base import *

class SdOrganization(Base):

    __tablename__ = 'sd_organization'

    id = Column(String, primary_key=True)
    land_office_name = Column(String)
    address = Column(String)
    fax = Column(String)
    phone = Column(String)
    website = Column(String)
    report_email = Column(String)

    type = Column(String, ForeignKey('cl_organization_type.code'))
    type_ref = relationship("ClOrganizationType")
