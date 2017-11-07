__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, Date, ForeignKey,Sequence
from sqlalchemy.orm import relationship, backref
from Base import *

class SetCadastrePage(Base):

    __tablename__ = 'set_cadastre_page'

    id = Column(String, primary_key=True)
    description = Column(String)
    range_first_no = Column(Integer)
    range_last_no = Column(Integer)
    current_no = Column(Integer)
    register_date = Column(Date)
    end_date = Column(Date)

    au_level1 = Column(String, ForeignKey('au_level1.code'))
    au_level1_ref = relationship("AuLevel1")

    au_level2 = Column(String, ForeignKey('au_level2.code'))
    au_level2_ref = relationship("AuLevel2")
