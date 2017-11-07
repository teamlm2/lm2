__author__ = 'B.Ankhbold'

from sqlalchemy import Column, Integer, String, Date, Sequence, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, backref
from Base import *

class SetTrainingPerson(Base):

    __tablename__ = 'set_training_person'

    id = Column(Integer, Sequence('set_training_person_id_seq'), primary_key=True)
    certificate_no = Column(String)
    begin_date = Column(Date)
    end_date = Column(Date)
    # foreign keys:
    training_id = Column(Integer, ForeignKey('set_training.id'))
    training_ref = relationship("SetTraining")

    person_id = Column(String, ForeignKey('set_certificate_person.person_id'))
    person_ref = relationship("SetCertificatePerson")

    level_id = Column(String, ForeignKey('cl_training_level.code'))
    level_ref = relationship("ClTrainingLevel")


