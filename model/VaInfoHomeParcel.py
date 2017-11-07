__author__ = 'ankhbold'

from sqlalchemy import Column, Integer, Float, String, Date, Sequence, ForeignKey, DateTime, Table, Boolean, Numeric
from sqlalchemy.orm import relationship
from CaParcel import *
from CtApplicationDocument import *


class VaInfoHomeParcel(Base):

    __tablename__ = 'va_info_parcel'

    register_no = Column(String, primary_key=True)
    area_m2 = Column(Float)
    info_date = Column(DateTime)
    decision_date = Column(DateTime)
    approved_duration = Column(Integer)
    is_electricity = Column(Boolean)
    is_central_heating = Column(Boolean)
    is_fresh_water = Column(Boolean)
    is_sewage = Column(Boolean)
    is_well = Column(Boolean)
    is_self_financed_system = Column(Boolean)
    is_telephone = Column(Boolean)
    is_flood_channel = Column(Boolean)
    is_vegetable_plot = Column(Boolean)
    is_land_slope = Column(Boolean)
    electricity_distancel = Column(Numeric)
    electricity_conn_cost = Column(Numeric)
    central_heating_distancel = Column(Numeric)
    central_heating_conn_cost = Column(Numeric)
    fresh_water_distancel = Column(Numeric)
    fresh_water_conn_cost = Column(Numeric)
    sewage_distancel = Column(Numeric)
    sewage_conn_cost = Column(Numeric)
    well_distancel = Column(Numeric)
    telephone_distancel = Column(Numeric)
    flood_channel_distancel = Column(Numeric)
    vegetable_plot_size = Column(Numeric)
    other_info = Column(String)

    #foreign keys:
    app_type = Column(Integer, ForeignKey('cl_application_type.code'))
    app_type_ref = relationship("ClApplicationType")

    source_type = Column(Integer, ForeignKey('cl_type_source.code'))
    source_type_ref = relationship("VaTypeSource")

    parcel_id = Column(String, ForeignKey('ca_parcel.parcel_id'))
    parcel_ref = relationship("CaParcel")

    purchase_or_lease_type = Column(Integer, ForeignKey('cl_type_purchase_or_lease.code'))
    purchase_or_lease_type_ref = relationship("VaTypePurchaseOrLease")