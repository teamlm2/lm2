__author__ = 'Ankhaa'

from sqlalchemy import Column, String, Float, Date, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from ClLanduseType import *
from SetRole import *
from SetSurveyor import *
from CtApplication import *

parcel_table = Table('ca_parcel_maintenance_case', Base.metadata,
                        Column('maintenance', Integer, ForeignKey('ca_maintenance_case.id')),
                        Column('parcel', String, ForeignKey('ca_parcel.parcel_id'))
                    )

building_table = Table('ca_building_maintenance_case', Base.metadata,
                            Column('maintenance', Integer, ForeignKey('ca_maintenance_case.id')),
                            Column('building', String, ForeignKey('ca_building.building_id'))
                       )


class CaMaintenanceCase(Base):

    __tablename__ = 'ca_maintenance_case'

    id = Column(Integer, primary_key=True)
    creation_date = Column(Date)
    survey_date = Column(Date)
    completion_date = Column(Date)

    # foreign keys:
    created_by = Column(String, ForeignKey('set_role.user_name_real'))
    # created_by_ref = relationship("SetRole")

    surveyed_by_land_office = Column(String, ForeignKey('set_role.user_name_real'))
    # surveyed_by_land_office_ref = relationship("SetRole")

    surveyed_by_surveyor = Column(String, ForeignKey('set_surveyor.id'))
    surveyed_by_surveyor_ref = relationship("SetSurveyor")

    completed_by = Column(String, ForeignKey('set_role.user_name_real'))
    # completed_by_ref = relationship("SetRole")

    landuse = Column(Integer, ForeignKey('cl_landuse_type.code'))
    landuse_ref = relationship("ClLanduseType")

    parcels = relationship("CaParcel", secondary=parcel_table)
    buildings = relationship("CaBuilding", secondary=building_table)
    applications = relationship("CtApplication", backref="maintenance_case_ref")
