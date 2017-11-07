__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from Base import *
from ClApplicationStatus import *
from ClApplicationType import *
from SetRole import *


class CadastrePageSearch(Base):

    __tablename__ = 'cadastre_page_search'

    id = Column(Integer, primary_key=True)
    print_date = Column(Date)
    cadastre_page_number = Column(Integer)
    person_id = Column(String)
    parcel_id = Column(String)
    right_holder = Column(String)
    parcel_address = Column(String)