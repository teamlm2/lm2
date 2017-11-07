drop schema if exists logging cascade;
create schema logging;
grant usage on schema logging to public;

set search_path to logging, base, public;

CREATE TABLE ca_parcel_tbl as select 'xxx'::varchar(6) as schema, 'DEL'::varchar(3) as operation, '2011-01-01'::timestamp without time zone as stamp, 'mwagner'::text, * from s00000.ca_parcel with no data;

CREATE TABLE ca_building_tbl as select 'xxx'::varchar(6) as schema, 'DEL'::varchar(3) as operation, '2011-01-01'::timestamp without time zone as stamp, 'mwagner'::text, * from s00000.ca_building with no data;

CREATE TABLE ct_application as select 'xxx'::varchar(6) as schema, 'DEL'::varchar(3) as operation, '2011-01-01'::timestamp without time zone as stamp, 'mwagner'::text, * from s00000.ct_application with no data;

CREATE TABLE ct_contract as select 'xxx'::varchar(6) as schema, 'DEL'::varchar(3) as operation, '2011-01-01'::timestamp without time zone as stamp, 'mwagner'::text, * from s00000.ct_contract with no data;

CREATE TABLE ct_ownership_record as select 'xxx'::varchar(6) as schema, 'DEL'::varchar(3) as operation, '2011-01-01'::timestamp without time zone as stamp, 'mwagner'::text, * from s00000.ct_ownership_record with no data;

CREATE TABLE bs_person as select 'xxx'::varchar(6) as schema, 'DEL'::varchar(3) as operation, '2011-01-01'::timestamp without time zone as stamp, 'mwagner'::text, * from base.bs_person with no data;

CREATE TABLE ct_fee as select 'xxx'::varchar(6) as schema, 'DEL'::varchar(3) as operation, '2011-01-01'::timestamp without time zone as stamp, 'mwagner'::text, * from s00000.ct_fee with no data;

CREATE TABLE ct_tax_and_price as select 'xxx'::varchar(6) as schema, 'DEL'::varchar(3) as operation, '2011-01-01'::timestamp without time zone as stamp, 'mwagner'::text, * from s00000.ct_tax_and_price with no data;

CREATE TABLE ct_decision as select 'xxx'::varchar(6) as schema, 'DEL'::varchar(3) as operation, '2011-01-01'::timestamp without time zone as stamp, 'mwagner'::text, * from s00000.ct_decision with no data;

CREATE TABLE ca_parcel_conservation_tbl as select 'xxx'::varchar(6) as schema, 'DEL'::varchar(3) as operation, '2011-01-01'::timestamp without time zone as stamp, 'mwagner'::text, * from s00000.ca_parcel_conservation_tbl with no data;

CREATE TABLE ca_parcel_pollution_tbl as select 'xxx'::varchar(6) as schema, 'DEL'::varchar(3) as operation, '2011-01-01'::timestamp without time zone as stamp, 'mwagner'::text, * from s00000.ca_parcel_pollution_tbl with no data;



CREATE OR REPLACE FUNCTION base.log_changes()
  RETURNS trigger AS
$BODY$
BEGIN
	IF (TG_OP = 'DELETE') THEN
		EXECUTE 'INSERT INTO logging.' || TG_TABLE_NAME || ' SELECT ' || quote_literal(TG_TABLE_SCHEMA) || ', ' || quote_literal('DEL') || ', now(), session_user, $1.*' using OLD;
	ELSIF (TG_OP = 'UPDATE') THEN
		EXECUTE 'INSERT INTO logging.' || TG_TABLE_NAME || ' SELECT ' || quote_literal(TG_TABLE_SCHEMA) || ', ' || quote_literal('OLD') || ', now(), session_user, $1.*' using OLD;
		EXECUTE 'INSERT INTO logging.' || TG_TABLE_NAME || ' SELECT ' || quote_literal(TG_TABLE_SCHEMA) || ', ' || quote_literal('NEW') || ', now(), session_user, $1.*' using NEW;
	ELSIF (TG_OP = 'INSERT') THEN
		EXECUTE 'INSERT INTO logging.' || TG_TABLE_NAME || ' SELECT ' || quote_literal(TG_TABLE_SCHEMA) || ', ' || quote_literal('INS') || ', now(), session_user, $1.*' using NEW;
	END IF;
	RETURN NULL;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE SECURITY DEFINER
  COST 100;

grant select on ca_parcel_tbl, ca_building_tbl, ct_contract, ct_ownership_record, ct_application, ct_decision, ct_fee, ct_tax_and_price, bs_person to log_view;


