__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, Date, Sequence, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, backref
from Base import *

class SetEquipment(Base):

    __tablename__ = 'set_equipment'

    id = Column(Integer, primary_key=True)
    description = Column(String)
    purchase_date = Column(DateTime)
    given_date = Column(DateTime)
    duration_date = Column(DateTime)
    mac_address = Column(String)
    seller_name = Column(String)
    # foreign keys:
    type = Column(Integer, ForeignKey('cl_equipment_list.code'))
    type_ref = relationship("ClEquipmentList")

    officer_user = Column(String, ForeignKey('set_role.user_name_real'))
    officer_user_ref = relationship("SetRole")

    aimag = Column(String, ForeignKey('au_level1.code'))
    aimag_ref = relationship("AuLevel1")

    soum = Column(String, ForeignKey('au_level2.code'))
    soum_ref = relationship("AuLevel2")

    documents = relationship("SetEquipmentDocument", lazy="dynamic", cascade="all, delete-orphan")


