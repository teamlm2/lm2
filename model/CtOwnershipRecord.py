__author__ = 'anna'

from sqlalchemy import Date
from sqlalchemy.orm import relationship
from ClRecordCancellationReason import *
from CtRecordDocument import *
from ClRecordStatus import *
from ClRecordRightType import *
from CtTaxAndPrice import *


class CtOwnershipRecord(Base):

    __tablename__ = 'ct_ownership_record'

    record_no = Column(String, primary_key=True)
    record_date = Column(Date)
    record_begin = Column(Date)
    certificate_no = Column(String)
    cancellation_date = Column(Date)

    cancellation_reason = Column(Integer, ForeignKey('cl_record_cancellation_reason.code'))
    cancellation_reason_ref = relationship("ClRecordCancellationReason")

    status = Column(Integer, ForeignKey('cl_record_status.code'))
    status_ref = relationship("ClRecordStatus")

    right_type = Column(Integer, ForeignKey('cl_record_right_type.code'))
    right_type_ref = relationship("ClRecordRightType")

    application_roles = relationship("CtRecordApplicationRole", backref="record_ref", lazy='dynamic', cascade="all, delete-orphan")
    documents = relationship("CtRecordDocument", backref="record_ref", lazy='dynamic', cascade="all, delete-orphan")

    taxes = relationship("CtTaxAndPrice", backref='record_ref', lazy='dynamic', cascade="all, delete, delete-orphan")
    archived_taxes = relationship("CtArchivedTaxAndPrice", backref='record_ref',
                                 lazy='dynamic', cascade="all, delete, delete-orphan")