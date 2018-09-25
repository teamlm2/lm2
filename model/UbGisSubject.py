__author__ = 'B.Ankhbold'

from sqlalchemy.orm import relationship
from sqlalchemy import Column, Numeric, Integer, Sequence, ForeignKey, Float, Boolean
from CtArchivedFee import *
from CtArchivedTaxAndPrice import *


class UbGisSubject(Base):

    __tablename__ = 'all_subject'

    objectid = Column(Integer, primary_key=True)
    pid = Column(String)
    oldpid = Column(String)
    zoriulalt = Column(Date)
    horoo = Column(String)
    gudamj = Column(String)
    hashaa = Column(String)
    register = Column(String)
    ovogner = Column(String)
    ovog = Column(String)
    ner = Column(String)
    utas1 = Column(String)
    utas2 = Column(String)
    changedate = Column(Date)
    huchindate = Column(Date)
    heid = Column(String)
    gaid = Column(String)
    zovshbaig = Column(String)
    zovshshiid = Column(String)
    zovshdate = Column(Date)
    gerchid = Column(String)
    duusdate = Column(Date)
    uhid = Column(String)
    uhdate = Column(Date)
    tailbar = Column(String)
    gerid = Column(String)
    gerdate = Column(Date)
    gazobject = Column(String)
    app_type = Column(Integer)
    status_date = Column(Date)
    status_user = Column(String)
    is_finish = Column(Boolean)
    finish_user = Column(String)
    finish_date = Column(Date)