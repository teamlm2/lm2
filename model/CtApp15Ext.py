__author__ = 'mwagner'

from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import relationship
from ClTransferType import *


class CtApp15Ext(Base):

    __tablename__ = 'ct_app15_ext'

    app_no = Column(String, ForeignKey('ct_application.app_no'), primary_key=True)
    # other foreign keys:
    transfer_type = Column(Integer, ForeignKey('cl_transfer_type.code'))
    transfer_type_ref = relationship("ClTransferType")
