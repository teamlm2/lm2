-- To be run by 'geodb_admin'

drop schema if exists pasture cascade;
create schema pasture;
grant usage on schema pasture to pasture;
set search_path to pasture, public;

create table ca_parcel_tbl
(
parcel_id varchar(12) primary key,
old_parcel_id varchar(14),
geo_id varchar(17),
landuse int references cl_landuse_type on update cascade on delete restrict,
area_m2 decimal,
documented_area_m2 decimal,
address_khashaa varchar(64),
address_streetname varchar(250),
address_neighbourhood varchar(250),
valid_from date default current_date,
valid_till date default 'infinity',
geometry geometry(POLYGON, 4326)
);

CREATE INDEX st_idx_ca_parcel_tbl
  ON ca_parcel_tbl
  USING gist
  (geometry);

CREATE TRIGGER update_area
  BEFORE INSERT OR UPDATE
  ON ca_parcel_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE update_area_or_length();

CREATE TRIGGER check_spatial_restriction
  BEFORE INSERT OR UPDATE
  ON ca_parcel_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE check_spatial_restriction();

CREATE TRIGGER a_create_parcel_id
  BEFORE INSERT
  ON ca_parcel_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE create_parcel_id();

CREATE TRIGGER set_default_valid_time
  BEFORE INSERT OR UPDATE
  ON ca_parcel_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE set_default_valid_time();  

create or replace view ca_parcel as select * from ca_parcel_tbl where user in (select user_name from set_role) AND overlaps(valid_from, valid_till, (SELECT pa_from from set_role where user_name = user), (select pa_till from set_role where user_name = user));

grant select, insert, update, delete on ca_parcel to cadastre_update;
grant select on ca_parcel to cadastre_view, reporting;


CREATE OR REPLACE VIEW ca_refused_parcel AS
 SELECT ca_parcel_tbl.parcel_id,
    ca_parcel_tbl.old_parcel_id,
    ca_parcel_tbl.geo_id,
    ca_parcel_tbl.landuse,
    ca_parcel_tbl.area_m2,
    ca_parcel_tbl.documented_area_m2,
    ca_parcel_tbl.address_khashaa,
    ca_parcel_tbl.address_streetname,
    ca_parcel_tbl.address_neighbourhood,
    ca_parcel_tbl.valid_from,
    ca_parcel_tbl.valid_till,
    ca_parcel_tbl.geometry
   FROM ca_parcel_tbl
  WHERE ca_parcel_tbl.valid_from IS NULL OR ca_parcel_tbl.valid_till IS NULL;

GRANT SELECT ON TABLE ca_refused_parcel TO cadastre_update, cadastre_view, reporting;

create view ca_union_parcel as
  Select * from ca_parcel
  UNION ALL
    SELECT * from ca_refused_parcel;

grant select on ca_union_parcel to cadastre_view, cadastre_update, reporting;

-- ca_building
create table ca_building_tbl
(
building_id varchar(15) primary key,
building_no varchar(10),
geo_id varchar(17),
area_m2 decimal,
address_khashaa varchar(64),
address_streetname varchar(250),
address_neighbourhood varchar(250),
valid_from date not null default current_date,
valid_till date not null default 'infinity',
geometry geometry(POLYGON, 4326)
);

CREATE INDEX st_idx_ca_building_tbl
  ON ca_building_tbl
  USING gist
  (geometry);

CREATE TRIGGER update_area
  BEFORE INSERT OR UPDATE
  ON ca_building_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE update_area_or_length();

CREATE TRIGGER check_spatial_restriction
  BEFORE INSERT OR UPDATE
  ON ca_building_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE check_spatial_restriction();

 CREATE TRIGGER a_create_building_id
  BEFORE INSERT OR UPDATE
  ON ca_building_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE create_building_id();

CREATE TRIGGER set_default_valid_time
  BEFORE INSERT OR UPDATE
  ON ca_building_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE set_default_valid_time();  

CREATE INDEX idx_parcel_valid_from ON ca_parcel_tbl(valid_from);
CREATE INDEX idx_parcel_valid_till ON ca_parcel_tbl(valid_till);
CREATE INDEX idx_building_valid_from ON ca_building_tbl(valid_from);
CREATE INDEX idx_building_valid_till ON ca_building_tbl(valid_till);
  
create or replace view ca_building as select * from ca_building_tbl where user in (select user_name from set_role) AND overlaps(valid_from, valid_till, (SELECT pa_from from set_role where user_name = user), (select pa_till from set_role where user_name = user));

grant select, insert, update, delete on ca_building to cadastre_update;
grant select on ca_building to cadastre_view, reporting;

create table ca_maintenance_case
(
id serial primary key,
creation_date date,
survey_date date,
completion_date date,
created_by varchar(30) references set_role on update cascade on delete restrict not null,
surveyed_by_land_office varchar(30) references set_role on update cascade on delete restrict,
surveyed_by_surveyor int references set_surveyor on update cascade on delete restrict,
completed_by varchar(30) references set_role on update cascade on delete restrict,
landuse int references cl_landuse_type on update cascade on delete restrict
);
grant select, insert, update, delete on ca_maintenance_case to cadastre_update;
grant usage on sequence ca_maintenance_case_id_seq to cadastre_update;
grant select on ca_maintenance_case to cadastre_view, reporting;

create table ct_application
(
app_no varchar(17) primary key,
app_timestamp timestamp not null,
app_type int references cl_application_type on update cascade on delete restrict not null,
requested_landuse int references cl_landuse_type on update cascade on delete restrict,
approved_landuse int references cl_landuse_type on update cascade on delete restrict,
requested_duration int,
approved_duration int,
remarks text,
parcel varchar(12) references ca_parcel_tbl on update cascade on delete restrict
);
grant select, insert, update, delete on ct_application to contracting_update;
grant select on ct_application to contracting_view, reporting;

create table ct_app8_ext
(
app_no varchar(17) references ct_application on update cascade on delete cascade primary key,
start_mortgage_period date,
end_mortgage_period date,
mortgage_type int references cl_mortgage_type on update cascade on delete restrict
);
grant select, insert, update, delete on ct_app8_ext to contracting_update;
grant select on ct_app8_ext to contracting_view, reporting;

create table ct_app1_ext
(
app_no varchar(17) references ct_application on update cascade on delete cascade primary key,
excess_area int,
price_to_be_paid int,
applicant_has_paid boolean
);
grant select, insert, update, delete on ct_app1_ext to contracting_update;
grant select on ct_app1_ext to contracting_view, reporting;

create table ct_app15_ext
(
app_no varchar(17) references ct_application on update cascade on delete cascade primary key,
transfer_type int references cl_transfer_type on update cascade on delete restrict
);
grant select, insert, update, delete on ct_app15_ext to contracting_update;
grant select on ct_app15_ext to contracting_view, reporting;


create table ca_parcel_maintenance_case
(
parcel varchar(12) references ca_parcel_tbl on update cascade on delete restrict,
maintenance int references ca_maintenance_case on update cascade on delete CASCADE ,
primary key (parcel, maintenance)
);
grant select, insert, update, delete on ca_parcel_maintenance_case to cadastre_update;
grant select on ca_parcel_maintenance_case to cadastre_view, reporting;

create table ca_building_maintenance_case
(
building varchar(15) references ca_building_tbl on update cascade on delete restrict,
maintenance int references ca_maintenance_case on update cascade on delete CASCADE ,
primary key (building, maintenance)
);
grant select, insert, update, delete on ca_building_maintenance_case to cadastre_update;
grant select on ca_building_maintenance_case to cadastre_view, reporting;

create table ca_tmp_parcel
(
parcel_id varchar(12) primary key,
old_parcel_id varchar(14),
geo_id varchar(17),
landuse int references cl_landuse_type on update cascade on delete restrict,
area_m2 decimal,
documented_area_m2 decimal,
address_khashaa varchar(64),
address_neighbourhood CHARACTER VARYING(250),
address_streetname varchar(250),
valid_from date,
valid_till date,
geometry geometry(POLYGON, 4326),
maintenance_case int references ca_maintenance_case on update cascade on delete CASCADE not null,
initial_insert boolean
);

CREATE INDEX st_idx_ca_tmp_parcel
  ON ca_tmp_parcel
  USING gist
  (geometry);

CREATE TRIGGER update_area
  BEFORE INSERT OR UPDATE
  ON ca_tmp_parcel
  FOR EACH ROW
  EXECUTE PROCEDURE update_area_or_length();

grant select, insert, update, delete on ca_tmp_parcel to cadastre_update;
grant select on ca_tmp_parcel to cadastre_view, reporting;

create table ca_tmp_building
(
building_id varchar(15) primary key,
building_no varchar(10),
geo_id varchar(17),
area_m2 decimal,
address_khashaa varchar(64),
address_streetname varchar(250),
address_neighbourhood varchar(250),
valid_from date,
valid_till date,
geometry geometry(POLYGON, 4326),
maintenance_case int references ca_maintenance_case on update cascade on delete CASCADE not null
);

CREATE INDEX st_idx_ca_tmp_building
  ON ca_tmp_building
  USING gist
  (geometry);

CREATE TRIGGER update_area
  BEFORE INSERT OR UPDATE
  ON ca_tmp_building
  FOR EACH ROW
  EXECUTE PROCEDURE update_area_or_length();

grant select, insert, update, delete on ca_tmp_building to cadastre_update;
grant select on ca_tmp_building to cadastre_view, reporting;

create table ct_document
(
id serial primary key,
name varchar(100),
content bytea
);
grant select, insert, update, delete on ct_document to contracting_update;
grant usage on sequence ct_document_id_seq to contracting_update;
grant select on ct_document to contracting_view, reporting;

create table ct_decision
(
decision_no varchar(20) primary key,
decision_date date not null,
imported_by varchar(30) references set_role on update cascade on delete restrict not null,
decision_level int references cl_decision_level on update cascade on delete restrict not null
);
grant select, insert, update, delete on ct_decision to contracting_update;
grant select on ct_decision to contracting_view, reporting;

create table ct_decision_application
(
application varchar(17) primary key references ct_application on update cascade on delete CASCADE not null,
decision varchar (20) references ct_decision on update cascade on delete CASCADE not null,
decision_result int references cl_decision on update cascade on delete restrict not null
);

grant select, insert, update, delete on ct_decision_application to contracting_update;
grant select, insert, update, delete on ct_decision_application to contracting_view, reporting;

create table ct_decision_document
(
decision varchar(20) references ct_decision on update cascade on delete CASCADE not null,
document int references ct_document on update cascade on delete RESTRICT not null,
primary key (decision, document)
);

grant select, insert, update, delete on ct_decision_document to contracting_update;
grant select, insert, update, delete on ct_decision_document to contracting_view, reporting;

create table ct_application_status
(
application varchar(17) references ct_application on update cascade on delete cascade,
status int references cl_application_status on update cascade on delete restrict,
status_date date not null,
officer_in_charge varchar(30) references set_role on update cascade on delete restrict not null,
next_officer_in_charge varchar(30) references set_role on update cascade on delete restrict,
primary key(application, status)
);
grant select, insert, update, delete on ct_application_status to contracting_update;
grant select on ct_application_status to contracting_view, reporting;

create table ct_application_document
(
application varchar(17) references ct_application on update cascade on delete cascade,
person varchar(10) references bs_person on update cascade  on delete restrict,
document int references ct_document on update cascade on delete restrict,
role int references cl_document_role on update cascade on delete restrict,
primary key(application, document)
);
grant select, insert, update, delete on ct_application_document to contracting_update;
grant select on ct_application_document to contracting_view, reporting;

create table ct_contract
(
contract_no varchar(16) primary key,
contract_date date,
contract_begin date,
contract_end date,
certificate_no integer,
status int references cl_contract_status on update cascade on delete restrict,
cancellation_date date,
cancellation_reason int references cl_contract_cancellation_reason on update cascade on delete restrict
);
grant select, insert, update, delete on ct_contract to contracting_update;
grant select on ct_contract to contracting_view, reporting;

create table ct_ownership_record
(
record_no varchar(16) primary key,
record_date date,
record_begin date,
certificate_no varchar(15),
status int references cl_record_status on update cascade on delete restrict,
right_type int references cl_record_right_type on update cascade on delete restrict,
cancellation_date date,
cancellation_reason int references cl_record_cancellation_reason on update cascade on delete restrict
);
grant select, insert, update, delete on ct_ownership_record to contracting_update;
grant select on ct_ownership_record to contracting_view, reporting;

create table ct_contract_application_role
(
contract varchar(16) references ct_contract on update cascade on delete cascade,
application varchar(17) references ct_application on update cascade on delete restrict,
role int references cl_application_role on update cascade on delete restrict,
primary key(contract, application)
);
grant select, insert, update, delete on ct_contract_application_role to contracting_update;
grant select on ct_contract_application_role to contracting_view, reporting;

create table ct_record_application_role
(
record varchar(16) references ct_ownership_record on update cascade on delete cascade,
application varchar(17) references ct_application on update cascade on delete restrict,
role int references cl_application_role on update cascade on delete restrict,
primary key(record, application)
);
grant select, insert, update, delete on ct_record_application_role to contracting_update;
grant select on ct_record_application_role to contracting_view, reporting;

create table ct_application_person_role
(
application varchar(17) references ct_application on update cascade on delete cascade,
person varchar(10) references bs_person on update cascade on delete restrict,
role int references cl_person_role on update cascade on delete restrict,
main_applicant boolean not null default false,
share numeric(2,1),
primary key(application, person, role)
);
grant select, insert, update, delete on ct_application_person_role to contracting_update;
grant select on ct_application_person_role to contracting_view, reporting;

create table ct_person_document
(
person varchar(10) references bs_person on update cascade on delete restrict,
document int references ct_document on update cascade on delete restrict,
primary key(person, document)
);
grant select, insert, update, delete on ct_person_document to contracting_update;
grant select on ct_person_document to contracting_view, reporting;

create table ct_contract_document
(
contract varchar(16) references ct_contract on update cascade on delete cascade,
role int references cl_document_role on update cascade on delete restrict,
document int references ct_document on update cascade on delete restrict,
primary key(contract, document)
);
grant select, insert, update, delete on ct_contract_document to contracting_update;
grant select on ct_contract_document to contracting_view, reporting;

create table ct_contract_conditions
(
contract varchar(16) references ct_contract on update cascade on delete restrict,
condition int references cl_contract_condition on update cascade on delete restrict,
primary key(contract, condition)
);
grant select, insert, update, delete on ct_contract_conditions to contracting_update;
grant select on ct_contract_conditions to contracting_view, reporting;

create table ct_record_document
(
record varchar(16) references ct_ownership_record on update cascade on delete cascade,
role int references cl_document_role on update cascade on delete restrict,
document int references ct_document on update cascade on delete restrict,
primary key(record, document)
);
grant select, insert, update, delete on ct_record_document to contracting_update;
grant select on ct_record_document to contracting_view, reporting;

create table ct_fee
(
contract varchar(16) references ct_contract on update cascade on delete cascade,
person varchar(10) references bs_person on update cascade on delete restrict, 
share decimal not null,
area int not null,
fee_calculated int not null,
fee_contract int not null,
grace_period int,
payment_frequency int references cl_payment_frequency on update cascade on delete restrict not null,
base_fee_per_m2 int not null,
subsidized_area int,
subsidized_fee_rate decimal,
primary key(contract, person)
);
grant select, insert, update, delete on ct_fee to contracting_update;
grant select on ct_fee to contracting_view, reporting;

create table ct_fee_payment
(
id serial primary key,
date_paid date not null,
amount_paid int not null,
payment_type int references cl_payment_type on update cascade on delete restrict not null,
year_paid_for int not null,
paid_total int default 0,
delay_to_dl1 int default 0,
delay_to_dl2 int default 0,
delay_to_dl3 int default 0,
delay_to_dl4 int DEFAULT 0,
left_to_pay_for_q1 int default 0,
left_to_pay_for_q2 int default 0,
left_to_pay_for_q3 int default 0,
left_to_pay_for_q4 int DEFAULT 0,
fine_for_q1 int default 0,
fine_for_q2 int default 0,
fine_for_q3 int default 0,
fine_for_q4 int DEFAULT 0,
contract varchar(16) not null,
person varchar(10) not null,
CONSTRAINT ct_fee_fk FOREIGN KEY (contract, person) REFERENCES ct_fee (contract, person) on update cascade on delete cascade
);
grant select, insert, update, delete on ct_fee_payment to contracting_update;
grant select on ct_fee_payment to contracting_view, reporting;
grant usage on sequence ct_fee_payment_id_seq to contracting_update;

create table ct_fine_for_fee_payment
(
id serial primary key,
date_paid date not null,
amount_paid int not null,
payment_type int references cl_payment_type on update cascade on delete restrict not null,
year_paid_for int not null,
contract varchar(16) not null,
person varchar(10) not null,
CONSTRAINT ct_fee_fk FOREIGN KEY (contract, person) REFERENCES ct_fee (contract, person) on update cascade on delete cascade
);
grant select, insert, update, delete on ct_fine_for_fee_payment to contracting_update;
grant select on ct_fine_for_fee_payment to contracting_view, reporting;
grant usage on sequence ct_fine_for_fee_payment_id_seq to contracting_update;

create table ct_archived_fee
(
id serial primary key,
contract varchar(16) references ct_contract on update cascade on delete cascade not null,
person varchar(10) references bs_person on update cascade on delete restrict not null, 
share decimal not null,
area int not null,
fee_calculated int not null,
fee_contract int not null,
grace_period int,
payment_frequency int references cl_payment_frequency on update cascade on delete restrict not null,
base_fee_per_m2 int not null,
subsidized_area int,
subsidized_fee_rate decimal,
valid_from date not null,
valid_till date not null
);
grant select, insert, update, delete on ct_archived_fee to contracting_update;
grant usage on sequence ct_archived_fee_id_seq to contracting_update;
grant select on ct_archived_fee to contracting_view, reporting;

create table ct_tax_and_price
(
record varchar(16) references ct_ownership_record on update cascade on delete cascade,
person varchar(10) references bs_person on update cascade on delete restrict, 
share decimal not null,
area int not null,
value_calculated int not null,
price_paid int not null,
land_tax int not null,
grace_period int,
payment_frequency int references cl_payment_frequency on update cascade on delete restrict not null,
base_value_per_m2 int not null,
base_tax_rate decimal not null,
subsidized_area int,
subsidized_tax_rate decimal,
primary key(record, person)
);
grant select, insert, update, delete on ct_tax_and_price to contracting_update;
grant select on ct_tax_and_price to contracting_view, reporting;

create table ct_tax_and_price_payment
(
id serial primary key,
date_paid date not null,
amount_paid int not null,
payment_type int references cl_payment_type on update cascade on delete restrict not null,
year_paid_for int not null,
paid_total int default 0,
delay_to_dl1 int default 0,
delay_to_dl2 int default 0,
delay_to_dl3 int default 0,
delay_to_dl4 int DEFAULT 0,
left_to_pay_for_q1 int default 0,
left_to_pay_for_q2 int default 0,
left_to_pay_for_q3 int default 0,
left_to_pay_for_q4 int DEFAULT 0,
fine_for_q1 int default 0,
fine_for_q2 int default 0,
fine_for_q3 int default 0,
fine_for_q4 int DEFAULT 0,
record varchar(16) not null,
person varchar(10) not null,
CONSTRAINT ct_record_fk FOREIGN KEY (record, person) REFERENCES ct_tax_and_price (record, person) on update cascade on delete cascade
);
grant select, insert, update, delete on ct_tax_and_price_payment to contracting_update;
grant select on ct_tax_and_price_payment to contracting_view, reporting;
grant usage on sequence ct_tax_and_price_payment_id_seq to contracting_update;

create table ct_fine_for_tax_payment
(
id serial primary key,
date_paid date not null,
amount_paid int not null,
payment_type int references cl_payment_type on update cascade on delete restrict not null,
year_paid_for int not null,
record varchar(16) not null,
person varchar(10) not null,
CONSTRAINT ct_tax_and_price_fk FOREIGN KEY (record, person) REFERENCES ct_tax_and_price (record, person) on update cascade on delete cascade
);
grant select, insert, update, delete on ct_fine_for_tax_payment to contracting_update;
grant select on ct_fine_for_tax_payment to contracting_view, reporting;
grant usage on sequence ct_fine_for_tax_payment_id_seq to contracting_update;

create table ct_archived_tax_and_price
(
id serial primary key,
record varchar(16) references ct_ownership_record on update cascade on delete restrict not null,
person varchar(10) references bs_person on update cascade on delete restrict not null, 
share decimal not null,
area int not null,
value_calculated int not null,
price_paid int not null,
land_tax int not null,
grace_period int,
payment_frequency int references cl_payment_frequency on update cascade on delete restrict not null,
base_value_per_m2 int not null,
base_tax_rate decimal not null,
subsidized_area int,
subsidized_tax_rate decimal,
valid_from date not null,
valid_till date not null
);
grant select, insert, update, delete on ct_archived_tax_and_price to contracting_update;
grant usage on sequence ct_archived_tax_and_price_id_seq to contracting_update;
grant select on ct_archived_tax_and_price to contracting_view, reporting;

CREATE TRIGGER a_create_tmp_building_id
  BEFORE INSERT OR UPDATE
  ON ca_tmp_building
  FOR EACH ROW
  EXECUTE PROCEDURE create_tmp_building_id();

CREATE TRIGGER create_tmp_parcel_id
  BEFORE INSERT OR UPDATE
  ON ca_tmp_parcel
  FOR EACH ROW
  EXECUTE PROCEDURE create_tmp_parcel_id();

--TABLES FOR VALUATION SCHEMA--
--create info home parcel
CREATE TABLE va_info_parcel
(
  register_no varchar(16) primary key,
  parcel_id varchar(12) references ca_parcel_tbl on update cascade on delete restrict,
  area_m2 numeric NOT NULL,
  app_type int references cl_application_type on update cascade on delete restrict not null,
  source_type int references cl_type_source on update cascade on delete restrict not null,
  purchase_or_lease_type int references cl_type_purchase_or_lease on update cascade on delete restrict not null,
  info_date date NOT NULL,
  decision_date date,
  approved_duration integer,
  parcel_type integer
);
grant select, insert, update, delete on va_info_parcel to contracting_update;
grant select on va_info_parcel to contracting_view, reporting;

--create home purchase info
CREATE TABLE va_info_purchase
(
  id serial primary key,
  register_no varchar(16) not null,
  landuse int references cl_landuse_type on update cascade on delete restrict,
  area_m2 decimal,
  purchase_date date,
  price decimal
);
grant select, insert, update, delete on va_info_purchase to contracting_update;
grant usage on sequence va_info_purchase_id_seq to contracting_update;
grant select on va_info_purchase to contracting_view, reporting;

--create home lease info
CREATE TABLE va_info_lease
(
  id serial primary key,
  register_no varchar(16) references va_info_parcel on update cascade on delete restrict,
  landuse int references cl_landuse_type on update cascade on delete restrict,
  area_m2 decimal,
  lease_date date,
  duration_month int,
  monthly_rent decimal
);
grant select, insert, update, delete on va_info_lease to contracting_update;
grant usage on sequence va_info_lease_id_seq to contracting_update;
grant select on va_info_lease to contracting_view, reporting;

--create home building info
CREATE TABLE va_info_building
(
  id serial primary key,
  register_no varchar(16) not null,
  building_id varchar(15) references ca_building_tbl on update cascade on delete restrict,
  landuse_building int references cl_type_landuse_building on update cascade on delete restrict,
  floor int,
  area_m2 decimal,
  status_year integer,
  construction_year integer,
  stove_type int references cl_type_stove on update cascade on delete restrict,
  material_type int references cl_type_material on update cascade on delete restrict,
  heat_type int references cl_type_heat on update cascade on delete restrict,
  building_status int references cl_type_status_building on update cascade on delete restrict
);
grant select, insert, update, delete on va_info_building to contracting_update;
grant usage on sequence va_info_building_id_seq to contracting_update;
grant select on va_info_building to contracting_view, reporting;

-- Conservation parcels
--create ca_parcel_conservation
CREATE TABLE ca_parcel_conservation_tbl
(
  gid serial NOT NULL,
  conservation integer,
  area_m2 numeric,
  polluted_area_m2 numeric,
  address_khashaa character varying(64),
  address_streetname character varying(64),
  address_neighbourhood character varying(64),
  valid_from date DEFAULT ('now'::text)::date,
  valid_till date DEFAULT 'infinity'::date,
  geometry geometry(Polygon,4326),

  CONSTRAINT ca_parcel_conservation_tbl_conservation_fkey FOREIGN KEY (conservation)
      REFERENCES codelists.cl_conservation_type (code) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE RESTRICT
)
WITH (
  OIDS=FALSE
);
ALTER TABLE ca_parcel_conservation_tbl
  OWNER TO geodb_admin;

CREATE INDEX idx_parcel_conservation_valid_from
  ON ca_parcel_conservation_tbl
  USING btree
  (valid_from);

CREATE INDEX idx_parcel_conservation_valid_till
  ON ca_parcel_conservation_tbl
  USING btree
  (valid_till);

CREATE INDEX st_idx_ca_parcel_conservation_tbl
  ON ca_parcel_conservation_tbl
  USING gist
  (geometry);

CREATE TRIGGER check_spatial_restriction
  BEFORE INSERT OR UPDATE
  ON ca_parcel_conservation_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE base.check_spatial_restriction();

CREATE TRIGGER set_default_valid_time
  BEFORE INSERT OR UPDATE
  ON ca_parcel_conservation_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE base.set_default_valid_time();

CREATE TRIGGER update_area
  BEFORE INSERT OR UPDATE
  ON ca_parcel_conservation_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE base.update_area_or_length();

--create view ca_parcel_conservation
CREATE OR REPLACE VIEW ca_parcel_conservation AS
 SELECT ca_parcel_conservation_tbl.gid,
    ca_parcel_conservation_tbl.conservation,
    ca_parcel_conservation_tbl.area_m2,
    ca_parcel_conservation_tbl.polluted_area_m2,
    ca_parcel_conservation_tbl.address_khashaa,
    ca_parcel_conservation_tbl.address_streetname,
    ca_parcel_conservation_tbl.address_neighbourhood,
    ca_parcel_conservation_tbl.valid_from,
    ca_parcel_conservation_tbl.valid_till,
    ca_parcel_conservation_tbl.geometry
   FROM ca_parcel_conservation_tbl
  WHERE ("current_user"() IN ( SELECT set_role.user_name
           FROM settings.set_role)) AND "overlaps"(ca_parcel_conservation_tbl.valid_from::timestamp with time zone, ca_parcel_conservation_tbl.valid_till::timestamp with time zone, (( SELECT set_role.pa_from
           FROM settings.set_role
          WHERE set_role.user_name::name = "current_user"()))::timestamp with time zone, (( SELECT set_role.pa_till
           FROM settings.set_role
          WHERE set_role.user_name::name = "current_user"()))::timestamp with time zone);

grant select, insert, update, delete on ca_parcel_conservation to cadastre_update;
grant select on ca_parcel_conservation to cadastre_view, reporting;

--create ca_parcel_pollution
CREATE TABLE ca_parcel_pollution_tbl
(
  gid serial NOT NULL,
  pollution integer,
  area_m2 numeric,
  polluted_area_m2 numeric,
  address_khashaa character varying(64),
  address_streetname character varying(64),
  address_neighbourhood character varying(64),
  valid_from date DEFAULT ('now'::text)::date,
  valid_till date DEFAULT 'infinity'::date,
  geometry geometry(Polygon,4326),

  CONSTRAINT ca_parcel_pollution_tbl_pollution_fkey FOREIGN KEY (pollution)
      REFERENCES codelists.cl_pollution_type (code) MATCH SIMPLE
      ON UPDATE CASCADE ON DELETE RESTRICT
)
WITH (
  OIDS=FALSE
);
ALTER TABLE ca_parcel_pollution_tbl
  OWNER TO geodb_admin;

CREATE INDEX idx_parcel_pollution_valid_from
  ON ca_parcel_pollution_tbl
  USING btree
  (valid_from);

CREATE INDEX idx_parcel_pollution_valid_till
  ON ca_parcel_pollution_tbl
  USING btree
  (valid_till);

CREATE INDEX st_idx_ca_parcel_pollution_tbl
  ON ca_parcel_pollution_tbl
  USING gist
  (geometry);

CREATE TRIGGER check_spatial_restriction
  BEFORE INSERT OR UPDATE
  ON ca_parcel_pollution_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE base.check_spatial_restriction();

CREATE TRIGGER set_default_valid_time
  BEFORE INSERT OR UPDATE
  ON ca_parcel_pollution_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE base.set_default_valid_time();

CREATE TRIGGER update_area
  BEFORE INSERT OR UPDATE
  ON ca_parcel_pollution_tbl
  FOR EACH ROW
  EXECUTE PROCEDURE base.update_area_or_length();

--create view ca_parcel_pollution
CREATE OR REPLACE VIEW ca_parcel_pollution AS
 SELECT
    ca_parcel_pollution_tbl.gid,
    ca_parcel_pollution_tbl.pollution,
    ca_parcel_pollution_tbl.area_m2,
    ca_parcel_pollution_tbl.polluted_area_m2,
    ca_parcel_pollution_tbl.address_khashaa,
    ca_parcel_pollution_tbl.address_streetname,
    ca_parcel_pollution_tbl.address_neighbourhood,
    ca_parcel_pollution_tbl.valid_from,
    ca_parcel_pollution_tbl.valid_till,
    ca_parcel_pollution_tbl.geometry
   FROM ca_parcel_pollution_tbl
  WHERE ("current_user"() IN ( SELECT set_role.user_name
           FROM settings.set_role)) AND "overlaps"(ca_parcel_pollution_tbl.valid_from::timestamp with time zone, ca_parcel_pollution_tbl.valid_till::timestamp with time zone, (( SELECT set_role.pa_from
           FROM settings.set_role
          WHERE set_role.user_name::name = "current_user"()))::timestamp with time zone, (( SELECT set_role.pa_till
           FROM settings.set_role
          WHERE set_role.user_name::name = "current_user"()))::timestamp with time zone);

grant select, insert, update, delete on ca_parcel_pollution to cadastre_update;
grant select on ca_parcel_pollution to cadastre_view, reporting;
