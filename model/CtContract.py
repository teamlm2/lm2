__author__ = 'mwagner'

from sqlalchemy import Date
from sqlalchemy.orm import relationship
from CtFee import *
from CtContractCondition import *


class CtContract(Base):

    __tablename__ = 'ct_contract'

    contract_no = Column(String, primary_key=True)
    contract_date = Column(Date)
    contract_begin = Column(Date)
    contract_end = Column(Date)
    certificate_no = Column(Integer)
    cancellation_date = Column(Date)

    # foreign keys:
    status = Column(Integer, ForeignKey('cl_contract_status.code'))
    status_ref = relationship("ClContractStatus")

    cancellation_reason = Column(Integer, ForeignKey('cl_contract_cancellation_reason.code'))
    cancellation_reason_ref = relationship("ClContractCancellationReason")

    application_roles = relationship("CtContractApplicationRole", backref="contract_ref",
                                     lazy='dynamic', cascade="all, delete-orphan")
    documents = relationship("CtContractDocument", backref="contract_ref",
                             lazy='dynamic', cascade="all, delete-orphan")

    fees = relationship("CtFee", backref='contract_ref', lazy='dynamic', cascade="all, delete, delete-orphan")
    archived_fees = relationship("CtArchivedFee", backref='contract_ref',
                                 lazy='dynamic', cascade="all, delete, delete-orphan")

    conditions = relationship("CtContractCondition", backref="contract_ref",
                              lazy='dynamic', cascade="all, delete, delete-orphan")