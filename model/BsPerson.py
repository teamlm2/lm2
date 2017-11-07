__author__ = 'mwagner'

from sqlalchemy.orm import relationship
from CtArchivedFee import *
from CtArchivedTaxAndPrice import *


class BsPerson(Base):

    __tablename__ = 'bs_person'

    name = Column(String)
    first_name = Column(String)
    middle_name = Column(String)
    date_of_birth = Column(Date)
    contact_surname = Column(String)
    contact_first_name = Column(String)
    contact_position = Column(String)
    person_id = Column(String, Sequence('bs_person_id_seq'), primary_key=True)
    state_registration_no = Column(String)
    bank_account_no = Column(String)
    phone = Column(String)
    mobile_phone = Column(String)
    email_address = Column(String)
    website = Column(String)
    address_town_or_local_name = Column(String)
    address_neighbourhood = Column(String)
    address_street_name = Column(String)
    address_khaskhaa = Column(String)
    address_building_no = Column(String)
    address_entrance_no = Column(String)
    address_apartment_no = Column(String)

    # foreign keys:
    type = Column(Integer, ForeignKey('cl_person_type.code'))
    type_ref = relationship("ClPersonType")

    country = Column(Integer, ForeignKey('cl_country_list.code'))
    country_ref = relationship("ClCountryList")

    gender = Column(Integer, ForeignKey('cl_gender.code'))
    gender_ref = relationship("ClGender")

    bank = Column(Integer, ForeignKey('cl_bank.code'))
    bank_ref = relationship("ClBank")

    address_au_level1 = Column(String, ForeignKey('au_level1.code'))
    au_level1_ref = relationship("AuLevel1")

    address_au_level2 = Column(String, ForeignKey('au_level2.code'))
    au_level2_ref = relationship("AuLevel2")

    address_au_level3 = Column(String, ForeignKey('au_level3.code'))
    au_level3_ref = relationship("AuLevel3")

    address_au_khoroolol = Column(Integer, ForeignKey('au_khoroolol.fid'))
    address_au_khoroolol_ref = relationship("AuKhoroolol")

    fees = relationship("CtFee", backref='person_ref', lazy='dynamic', cascade="all, delete, delete-orphan")
    archived_fees = relationship("CtArchivedFee", backref='person_ref',
                                 lazy='dynamic', cascade="all, delete, delete-orphan")

    taxes = relationship("CtTaxAndPrice", backref='person_ref', lazy='dynamic', cascade="all, delete, delete-orphan")
    archived_taxes = relationship("CtArchivedTaxAndPrice", backref='person_ref',
                                  lazy='dynamic', cascade="all, delete, delete-orphan")
