__author__ = 'ankhaa'

from sqlalchemy import Column, Integer, String, ForeignKey,Float,Numeric,Date
from sqlalchemy.orm import relationship
from ClLanduseType import *
from Base import *


class ParcelReport(Base):

    __tablename__ = 'parcel_report'

    parcel_id = Column(String, primary_key=True)
    area_m2 = Column(Float)
    au1_code = Column(String)
    au2_code = Column(String)
    excess_area = Column(Float)
    share = Column(Numeric(1, 2))
    person_id = Column(String)
    name = Column(String)
    first_name = Column(String)
    middle_name = Column(String)
    app_no = Column(String)
    decision_no = Column(String)
    contract_no = Column(String)
    record_no = Column(String)
    record_date = Column(Date)
    right_type = Column(Integer)
    contract_date = Column(Date)
    valid_from = Column(Date)
    valid_till = Column(Date)
    landuse_code2 = Column(Integer)
    # foreign keys:
    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")

    app_type = Column(Integer, ForeignKey('cl_application_type.code'))
    app_type_ref = relationship("ClApplicationType")

    person_type = Column(Integer, ForeignKey('cl_person_type.code'))
    person_type_ref = relationship("ClPersonType")

    contract_status = Column(Integer, ForeignKey('cl_contract_status.code'))
    contact_status_ref = relationship("ClContractStatus")

    record_status = Column(Integer, ForeignKey('cl_record_status.code'))
    record_status_ref = relationship("ClRecordStatus")
