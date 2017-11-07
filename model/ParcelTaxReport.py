__author__ = 'ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey,Float,Numeric,Date
from sqlalchemy.orm import relationship
from ClLanduseType import *
from Base import *


class ParcelTaxReport(Base):

    __tablename__ = 'parcel_tax'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String)
    area_m2 = Column(Float)
    au1_code = Column(String)
    au2_code = Column(String)
    app_no = Column(String)
    record_no = Column(String)
    record_date = Column(Date)
    tax_area = Column(Integer)
    subsidized_area = Column(Integer)
    land_tax = Column(Integer)
    amount_paid = Column(Integer)
    valid_from = Column(Date)
    valid_till = Column(Date)
    landuse_code2 = Column(Integer)
    # foreign keys:
    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")

    app_type = Column(Integer, ForeignKey('cl_application_type.code'))
    app_type_ref = relationship("ClApplicationType")

    record_status = Column(Integer, ForeignKey('cl_record_status.code'))
    record_status_ref = relationship("ClRecordStatus")

