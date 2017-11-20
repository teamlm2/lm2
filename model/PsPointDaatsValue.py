__author__ = 'Ankhbold'

from sqlalchemy import ForeignKey, Column, String, Integer, Numeric, Date
from Base import *
from sqlalchemy.orm import relationship

class PsPointDaatsValue(Base):

    __tablename__ = 'ps_point_d_value'

    point_detail_id = Column(String, ForeignKey('ps_point_detail.point_detail_id'), primary_key=True)
    monitoring_year = Column(Integer, primary_key=True)
    register_date = Column(Date)
    area_ga = Column(Numeric)
    duration = Column(Integer)
    rc = Column(String)
    rc_precent = Column(Integer)
    sheep_unit = Column(Integer)
    sheep_unit_plant = Column(Numeric)
    biomass = Column(Numeric)
    d1 = Column(Numeric)
    d1_100ga = Column(Numeric)
    d2 = Column(Numeric)
    d3   = Column(Numeric)
    d3_rc = Column(Numeric)
    unelgee = Column(Numeric)
    begin_month = Column(String)
    end_month = Column(String)

    # foreign keys:
    rc_id = Column(Integer, ForeignKey('ps_recovery_class.id'))
    rc_id_ref = relationship("PsRecoveryClass")