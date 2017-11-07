__author__ = 'anna'

from sqlalchemy import Column, String, Integer
from Base import *


class ClCertificateType(Base):

    __tablename__ = 'cl_certificate_type'

    code = Column(Integer, primary_key=True)
    description = Column(String)
    description_en = Column(String)
