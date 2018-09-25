__author__ = 'Anna'

from sqlalchemy import Column, String, Integer, Date, Boolean, ForeignKey, Sequence
from sqlalchemy.orm import relationship
from ClEmployeeType import *
from ClUserCancelReason import *
from Base import *


class SetRole(Base):

    __tablename__ = 'set_role'

    user_name = Column(String)
    surname = Column(String)
    user_name_real = Column(String, primary_key=True)
    first_name = Column(String)
    user_register = Column(String)
    phone = Column(String)
    mac_addresses = Column(String)
    restriction_au_level1 = Column(String)
    restriction_au_level2 = Column(String)
    restriction_au_level3 = Column(String)
    pa_from = Column(Date)
    pa_till = Column(Date)
    is_active = Column(Boolean)
    email = Column(String)
    # foreign keys:
    position = Column(Integer, ForeignKey('hr_position.position_id'))
    position_ref = relationship("SdPosition")

    employee_type = Column(Integer, ForeignKey('cl_employee_type.code'))
    employee_type_ref = relationship("ClEmployeeType")

    cancel_reason = Column(Integer, ForeignKey('cl_user_cancel_reason.code'))
    cancel_reason_ref = relationship("ClUserCancelReason")

    working_au_level1 = Column(String, ForeignKey('au_level1.code'))
    working_au_level1_ref = relationship("AuLevel1")

    working_au_level2 = Column(String, ForeignKey('au_level2.code'))
    working_au_level2_ref = relationship("AuLevel2")

    organization = Column(Integer, ForeignKey('sd_organization.id'))
    organization_ref = relationship("SdOrganization")

    department = Column(Integer, ForeignKey('hr_department.department_id'))
    department_ref = relationship("SdDepartment")

    def __init__(self, user_name=None, surname=None, first_name=None, position=None, employee_type=None,
                 cancel_reason=None, phone=None, mac_addresses=None, user_name_real=None,
                 restriction_au_level1=None, restriction_au_level2=None, restriction_au_level3=None, pa_from=None,
                 pa_till=None, is_active=None, user_register=None, email=None, working_au_level2 = None, organization = None, department = None):

        self.user_name = user_name
        self.user_name_real = user_name_real
        self.surname = surname
        self.first_name = first_name
        self.position = position
        self.employee_type = employee_type
        self.cancel_reason = cancel_reason
        self.phone = phone
        self.user_register = user_register
        self.mac_addresses = mac_addresses
        self.restriction_au_level1 = restriction_au_level1
        self.restriction_au_level2 = restriction_au_level2
        self.restriction_au_level3 = restriction_au_level3
        self.pa_from = pa_from
        self.pa_till = pa_till
        self.is_active = is_active
        self.email = email
        self.working_au_level2 = working_au_level2
        self.organization = organization
        self.department = department