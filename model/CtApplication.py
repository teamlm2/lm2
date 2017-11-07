__author__ = 'mwagner'

from sqlalchemy import Column, Integer, String, Date, Sequence, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, backref
from CtApp1Ext import *
from CtApp8Ext import *
from CtApp15Ext import *
from CtApp29Ext import *
from ClLanduseType import *
from ClApplicationType import *
from CaParcel import *
from CtApplicationPersonRole import *
from CtApplicationDocument import *
from CaMaintenanceCase import *
from CaUnionParcel import *
from CaUBParcel import *

class CtApplication(Base):

    __tablename__ = 'ct_application'

    app_no = Column(String, primary_key=True)
    app_timestamp = Column(DateTime)
    requested_duration = Column(Integer)
    approved_duration = Column(Integer)
    remarks = Column(String)

    # foreign keys:
    app_type = Column(Integer, ForeignKey('cl_application_type.code'))
    app_type_ref = relationship("ClApplicationType")

    decision_result = relationship("CtDecisionApplication", uselist=False)

    requested_landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    requested_landuse_ref = relationship("ClLanduseType", foreign_keys=[requested_landuse])

    approved_landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    approved_landuse_ref = relationship("ClLanduseType", foreign_keys=[approved_landuse])

    parcel = Column(String, ForeignKey('ca_union_parcel.parcel_id'))
    parcel_ref = relationship("CaUnionParcel")

    # ub_parcel = Column(String, ForeignKey('ca_ub_parcel_tbl.old_parcel_id'))
    # ub_parcel_ref = relationship(String, ForeignKey("CaUBParcel"))

    tmp_parcel = Column(String, ForeignKey('ca_tmp_parcel.parcel_id'))
    tmp_parcel_ref = relationship("CaTmpParcel")

    maintenance_case = Column(Integer, ForeignKey('ca_maintenance_case.id'))
    #maintenance_case_ref = relationship("CaMaintenanceCase")

    #many to many relationships
    statuses = relationship("CtApplicationStatus", backref="application_ref",
                            lazy='dynamic', cascade="all, delete-orphan")

    stakeholders = relationship("CtApplicationPersonRole", backref="application_ref",
                                lazy='dynamic', cascade="all, delete-orphan")

    documents = relationship("CtApplicationDocument", backref="application_ref",
                             lazy='dynamic', cascade="all, delete-orphan")

    contracts = relationship("CtContractApplicationRole", backref="application_ref",
                             lazy='dynamic')

    records = relationship("CtRecordApplicationRole", lazy='dynamic')

    #decisions = relationship("CtDecisionApplication", backref="application_ref", lazy='dynamic', cascade="all, delete-orphan")

    # 1:1 relationships:
    app1ext = relationship("CtApp1Ext", uselist=False,  cascade="all, delete-orphan")
    app8ext = relationship("CtApp8Ext", uselist=False,  cascade="all, delete-orphan")
    app15ext = relationship("CtApp15Ext", uselist=False,  cascade="all, delete-orphan")
    app29ext = relationship("CtApp29Ext", uselist=False, cascade="all, delete-orphan")
