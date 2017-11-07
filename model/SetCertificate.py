__author__ = 'mwagner'

from sqlalchemy import Column, Integer, String, Date, ForeignKey,Sequence
from sqlalchemy.orm import relationship, backref
from Base import *


class SetCertificate(Base):

    __tablename__ = 'set_certificate'

    id = Column(Integer, Sequence('set_certificate_id_seq'), primary_key=True)
    description = Column(String)
    range_first_no = Column(Integer)
    range_last_no = Column(Integer)
    current_no = Column(Integer)
    begin_date = Column(Date)
    end_date = Column(Date)

    certificate_type = Column(Integer, ForeignKey('cl_certificate_type.code'))
    certificate_type_ref = relationship("ClCertificateType")
