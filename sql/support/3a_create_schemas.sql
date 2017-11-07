-- To be run by 'geodb_admin'

drop schema if exists base cascade;
drop schema if exists admin_units cascade;
drop schema if exists codelists cascade;
drop schema if exists settings cascade;

create schema base;
create schema admin_units;
create schema codelists;
create schema settings;

grant usage on schema base to public;
grant usage on schema admin_units to public;
grant usage on schema codelists to public;
grant usage on schema settings to public;

-- Schema "base"
set search_path to base, public;

CREATE OR REPLACE FUNCTION update_area_or_length()
  RETURNS trigger AS
$BODY$
DECLARE
	v_geometry_type text;
BEGIN
	IF (NOT (NEW.geometry IS NULL)) THEN
		v_geometry_type := ST_GeometryType(NEW.geometry);
		IF (v_geometry_type ILIKE '%POLYGON%') THEN
			NEW.area_m2 := base.calculate_area_utm(NEW.geometry);
		ELSIF (v_geometry_type ILIKE '%LINESTRING%') THEN
			NEW.length_m := round(st_length(NEW.geometry)::decimal, 2);
		END IF;
	END IF;

	RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;


CREATE OR REPLACE FUNCTION find_utm_srid(p geometry)
  RETURNS integer AS
$BODY$

DECLARE
         out_srid integer;
         base_srid integer;
BEGIN
         IF st_srid(p) != 4326 THEN
                 RAISE NOTICE 'find_utm_srid: input geometry has wrong SRID (%)',  st_srid(p);
                 RETURN NULL;
         END IF;

         IF st_y(p) < 0 THEN
                 --- south hemisphere
                 base_srid := 32700;
         ELSE
                 --- north hemisphere or on equator
                 base_srid := 32600;
         END IF;

         out_srid := base_srid + floor((st_x(p)+186)/6);
         IF (st_x(p) = 180) THEN
                 out_srid := base_srid + 60;
         END IF;

         RETURN out_srid;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

CREATE OR REPLACE FUNCTION  calculate_area_utm(geometry)
  RETURNS double precision AS
$BODY$

DECLARE
    v_inputgeo alias for $1;
    v_geocheck geometry;
    v_utmsrid integer;
    v_area double precision;

BEGIN
    IF (v_inputgeo is  null) THEN
      RAISE exception '%', 'Geometry is null!';
    END IF;

    IF NOT(st_geometrytype(v_inputgeo) = 'ST_Polygon' OR st_geometrytype(v_inputgeo) = 'ST_MultiPolygon') THEN
      RAISE exception '%', 'Wrong geometry type';
    END IF;

    SELECT base.find_utm_srid(st_centroid(v_inputgeo)) into v_utmsrid;
    IF NOT FOUND THEN
      RAISE EXCEPTION '%','SRID not found';
    END IF;

    v_area:= round(st_area(st_transform(v_inputgeo, v_utmsrid))::numeric);
    RETURN v_area;

END;

$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

CREATE OR REPLACE FUNCTION base.create_parcel_id()
  RETURNS trigger AS
$BODY$
DECLARE
  v_admin_unit_l1_code text;
  v_cblock_code text;
  v_parcel_prefix text;
  v_counter int;
  v_error_counter int;
  v_pa_from date;
  v_pa_till date;
BEGIN

	NEW.geometry := st_force2d(NEW.geometry);

	IF (NEW.valid_from IS NULL) THEN
		NEW.valid_from := now();
	END IF;

  SELECT pa_from INTO v_pa_from FROM settings.set_role where user_name = current_user;
  SELECT pa_till INTO v_pa_till FROM settings.set_role where user_name = current_user;

  UPDATE settings.set_role SET pa_from = '1800-01-01' where user_name = current_user;
  UPDATE settings.set_role SET pa_till = 'infinity' where user_name = current_user;

 	IF (NEW.geometry IS NOT NULL) THEN
        SELECT code FROM admin_units.au_level1 INTO v_admin_unit_l1_code WHERE ST_COVERS(geometry, NEW.geometry);
        IF NOT FOUND THEN
            RAISE NOTICE 'No Aimag / Duureg found around the parcel, parcel will have an error code!';
        END IF;

        SELECT block_no FROM admin_units.au_cadastre_block INTO v_cblock_code WHERE ST_COVERS(geometry, NEW.geometry);
        IF NOT FOUND THEN
            RAISE NOTICE 'No cadastre block found around the parcel, parcel will have an error code!';
        END IF;

        v_parcel_prefix := lpad(v_admin_unit_l1_code, 3, '0') || lpad(v_cblock_code, 4, '0');

        execute 'SELECT max(substring(parcel_id from 8 for 5)::int) FROM ' || TG_TABLE_SCHEMA || '.ca_union_parcel WHERE parcel_id LIKE $1' into v_counter using v_parcel_prefix || '%';
        IF v_counter IS NULL THEN
            v_counter := 0;
        END IF;
        v_counter := v_counter + 1;

        IF (v_admin_unit_l1_code || v_cblock_code || lpad(v_counter::text, 5, '0')) IS NULL THEN
            execute 'SELECT max(substring(parcel_id from 6 for 7)::int) FROM ' || TG_TABLE_SCHEMA || '.ca_union_parcel WHERE parcel_id LIKE $1' into v_error_counter using 'ERROR%';
            IF v_error_counter IS NULL THEN
                v_error_counter := 0;
            END IF;
            v_error_counter := v_error_counter + 1;
            NEW.parcel_id := 'ERROR' || lpad(v_error_counter::text, 7, '0');
        ELSE
            NEW.parcel_id := v_admin_unit_l1_code || v_cblock_code || lpad(v_counter::text, 5, '0');
        END IF;
    END IF;

    UPDATE settings.set_role SET pa_from = v_pa_from where user_name = current_user;
    UPDATE settings.set_role SET pa_till = v_pa_till where user_name = current_user;

    RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION create_building_id ()
  RETURNS trigger
AS
$BODY$
  DECLARE
  v_parcel_id text;
  v_counter int;
  v_error_counter int;
  v_pa_from date;
  v_pa_till date;
BEGIN

	NEW.geometry := st_force2d(NEW.geometry);

	IF (NEW.valid_from IS NULL) THEN
		NEW.valid_from := now();
	END IF;

  SELECT pa_from INTO v_pa_from FROM settings.set_role where user_name = current_user;
  SELECT pa_till INTO v_pa_till FROM settings.set_role where user_name = current_user;

  UPDATE settings.set_role SET pa_from = '1800-01-01' where user_name = current_user;
  UPDATE settings.set_role SET pa_till = 'infinity' where user_name = current_user;

 	IF (NEW.geometry IS NOT NULL) THEN
        execute 'SELECT parcel_id FROM ' || TG_TABLE_SCHEMA || '.ca_parcel a WHERE ST_Covers(a.geometry, ST_Centroid($1))' into v_parcel_id using NEW.geometry;
        IF v_parcel_id is null THEN
            RAISE NOTICE 'No parcel found around the building, building will have an error code!';
            execute 'SELECT max(substring(building_id from 6 for 10)::int) FROM ' || TG_TABLE_SCHEMA || '.ca_building WHERE building_id LIKE $1' into v_error_counter using 'ERROR%';
            IF v_error_counter IS NULL THEN
                v_error_counter := 0;
            END IF;
            v_error_counter := v_error_counter + 1;
            NEW.building_id := 'ERROR' || lpad(v_error_counter::text, 10, '0');
        ELSE
            IF TG_OP = 'UPDATE' THEN
              IF substring(OLD.building_id for 12) = v_parcel_id THEN
                RETURN NEW;
              END IF;
            END IF;
            execute 'SELECT max(substring(building_id from 13 for 3)::int) FROM ' || TG_TABLE_SCHEMA || '.ca_building WHERE building_id LIKE $1' into v_counter using v_parcel_id || '%';
            IF v_counter IS NULL THEN
                v_counter := 0;
            END IF;
            v_counter := v_counter + 1;
            NEW.building_id := v_parcel_id || lpad(v_counter::text, 3, '0');
        END IF;
    END IF;

    UPDATE settings.set_role SET pa_from = v_pa_from where user_name = current_user;
    UPDATE settings.set_role SET pa_till = v_pa_till where user_name = current_user;

    RETURN NEW;
END;
$BODY$
LANGUAGE plpgsql VOLATILE;

CREATE OR REPLACE FUNCTION check_spatial_restriction()
  RETURNS trigger AS
$BODY$
DECLARE
	is_within boolean := false;
BEGIN	
	IF (NEW.geometry IS NOT NULL) THEN
        IF substring(TG_TABLE_SCHEMA from 2 for 1) = '1' OR substring(TG_TABLE_SCHEMA from 2 for 2) = '01' THEN
            execute 'SELECT st_within($1, geometry) from admin_units.au_level1 where code = $2' into is_within using NEW.geometry, substring(TG_TABLE_SCHEMA from 2 for 3);
        ELSE
            execute 'SELECT st_within($1, geometry) from admin_units.au_level2 where code = $2' into is_within using NEW.geometry, substring(TG_TABLE_SCHEMA from 2 for 5);
        END IF;
	END IF;
	IF (is_within is null or NOT is_within) THEN
		RAISE EXCEPTION 'The user''s spatial restriction does not permit this insert or update!';
	END IF;

	RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION set_default_valid_time()
  RETURNS trigger AS
$BODY$
  BEGIN

  IF (NEW.valid_till) is null then
    IF TG_TABLE_NAME = 'ca_parcel_tbl' then
	    IF NEW.old_parcel_id = 'refused' then
	      NEW.valid_till := NULL;
	      NEW.valid_from := NULL;
	      RETURN NEW;
	    END IF;
    END IF;

		NEW.valid_till := 'infinity';

	end if;

  IF (NEW.valid_from) is null then
		NEW.valid_from := current_date;
	end if;

	RETURN NEW;

END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

CREATE OR REPLACE FUNCTION create_tmp_building_id()
  RETURNS trigger AS
$BODY$
DECLARE
    v_parcel_id text;
    v_maintenance_case int;
    v_counter int;
    v_error_counter int;
    v_pa_from date;
    v_pa_till date;
BEGIN

	NEW.geometry := st_force2d(NEW.geometry);

	IF (NEW.valid_from IS NULL) THEN
		NEW.valid_from := now();
	END IF;

	SELECT pa_from INTO v_pa_from FROM settings.set_role where user_name = current_user;
	SELECT pa_till INTO v_pa_till FROM settings.set_role where user_name = current_user;

	UPDATE settings.set_role SET pa_from = '1800-01-01' where user_name = current_user;
	UPDATE settings.set_role SET pa_till = 'infinity' where user_name = current_user;

 	IF (NEW.geometry IS NOT NULL) THEN
        execute 'SELECT parcel_id FROM ' || TG_TABLE_SCHEMA || '.ca_tmp_parcel a WHERE ST_Covers(a.geometry, ST_Centroid($1))' into v_parcel_id using NEW.geometry;

        IF v_parcel_id is null THEN
            RAISE NOTICE 'No parcel found around the building, building will have an error code!';
            execute 'SELECT max(substring(building_id from 6 for 10)::int) FROM ' || TG_TABLE_SCHEMA || '.ca_tmp_building WHERE building_id LIKE $1' into v_error_counter using 'ERROR%';
            IF v_error_counter IS NULL THEN
                v_error_counter := 0;
            END IF;
            v_error_counter := v_error_counter + 1;
            NEW.building_id := 'ERROR' || lpad(v_error_counter::text, 10, '0');

        ELSE
            execute 'SELECT max(substring(building_id from 13 for 3)::int) FROM ' || TG_TABLE_SCHEMA || '.ca_tmp_building WHERE building_id LIKE $1' into v_counter using v_parcel_id || '%';

            IF NEW.building_id IS NULL THEN
		    IF v_counter IS NULL THEN
			v_counter := 0;
		    END IF;
		    IF NEW.maintenance_case IS NULL THEN
			execute 'SELECT maintenance_case FROM ' || TG_TABLE_SCHEMA || '.ca_tmp_parcel a WHERE parcel_id = $1;' into v_maintenance_case using v_parcel_id;
			NEW.maintenance_case = v_maintenance_case;
		    END IF;
		    v_counter := v_counter + 1;
		    NEW.building_id := NEW.maintenance_case || '-' || lpad(v_counter::text, 3, '0');
	    ELSE
		IF v_counter IS NULL THEN
			v_counter := 0;
	        END IF;
		v_counter := v_counter + 1;
	        NEW.building_id := v_parcel_id || lpad(v_counter::text, 3, '0');
	    END IF;
        END IF;
    END IF;

    UPDATE settings.set_role SET pa_from = v_pa_from where user_name = current_user;
    UPDATE settings.set_role SET pa_till = v_pa_till where user_name = current_user;

    RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

CREATE OR REPLACE FUNCTION base.create_tmp_parcel_id()
  RETURNS trigger AS
$BODY$
DECLARE
    v_id int;
BEGIN

    IF NEW.initial_insert = true THEN
        NEW.initial_insert := false;
        RETURN NEW;
    END IF;

    -- Changes of geometry that result in less than 1 sqm difference are not considered as UPDATE:
    IF TG_OP = 'UPDATE' THEN
        IF abs(base.calculate_area_utm(NEW.geometry) - base.calculate_area_utm(OLD.geometry)) < 1 THEN
            RETURN NEW;
        END IF;
    END IF;

    execute 'SELECT max(case when position(''-'' in parcel_id) > 0 then substring(parcel_id from position(''-'' in parcel_id)+1)::int else 0 end) FROM ' || TG_TABLE_SCHEMA || '.ca_tmp_parcel WHERE maintenance_case = $1' into v_id using NEW.maintenance_case;
    IF v_id IS NULL THEN
        v_id := 0;
    END IF;
    v_id := v_id + 1;
    NEW.parcel_id := NEW.maintenance_case || '-' || v_id;

    RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

-- Schema "admin_units"
set search_path to admin_units, base, public;

create table au_level1
(
code varchar(3) primary key,
name varchar(50) not null,
area_m2 decimal,
geometry geometry(POLYGON, 4326)
);
comment on table au_level1 is 'Aimag code is extended to 3 numbers, because the districts of Ulan Bator are included';
grant select, insert, update, delete on au_level1 to land_office_administration;
grant select on au_level1 to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting, role_management;

CREATE INDEX st_idx_au_level1
  ON au_level1
  USING gist
  (geometry);

CREATE TRIGGER update_area
  BEFORE INSERT OR UPDATE
  ON au_level1
  FOR EACH ROW
  EXECUTE PROCEDURE update_area_or_length();

create table au_level2
(
code varchar(5) primary key,
name varchar(50) not null,
area_m2 decimal,
geometry geometry(POLYGON, 4326)
);

comment on table au_level2 is 'code-Structure: aaass [a = aimag or district; s = soum]';
comment on table au_level2 is 'soum code is taken from the ZIP-Code';
grant select, insert, update, delete on au_level2 to land_office_administration;
grant select on au_level2 to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting, role_management;

CREATE INDEX st_idx_au_level2
  ON au_level2
  USING gist
  (geometry);

CREATE TRIGGER update_area
  BEFORE INSERT OR UPDATE
  ON au_level2
  FOR EACH ROW
  EXECUTE PROCEDURE update_area_or_length();
  
create table au_level3
(
code varchar(8) primary key,
name varchar(50) not null,
area_m2 decimal,
geometry geometry(POLYGON, 4326)
);
grant select, insert, update, delete on au_level3 to land_office_administration;
grant select on au_level3 to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting, role_management;

CREATE INDEX st_idx_au_level3
  ON au_level3
  USING gist
  (geometry);

CREATE TRIGGER update_area
  BEFORE INSERT OR UPDATE
  ON au_level3
  FOR EACH ROW
  EXECUTE PROCEDURE update_area_or_length();

create table au_cadastre_block
(
code varchar(7) primary key,
block_no varchar(4) not null,
area_m2 decimal,
soum_code character varying(5) not null,
geometry geometry(MultiPolygon, 4326)
);
grant select, insert, update, delete on au_cadastre_block to land_office_administration;
grant select on au_cadastre_block to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting, role_management;

CREATE INDEX st_idx_au_cadastre_block
  ON au_cadastre_block
  USING gist
  (geometry);

CREATE TRIGGER update_area
  BEFORE INSERT OR UPDATE
  ON au_cadastre_block
  FOR EACH ROW
  EXECUTE PROCEDURE update_area_or_length();

create table au_khoroolol
(
fid serial primary key,
name varchar(50) not null,
area_m2 decimal,
geometry geometry(POLYGON, 4326)
);
grant usage on sequence au_khoroolol_fid_seq to land_office_administration;
grant select, insert, update, delete on au_khoroolol to land_office_administration;
grant select on au_khoroolol to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting, role_management;

CREATE INDEX st_idx_au_khoroolol
  ON au_khoroolol
  USING gist
  (geometry);

CREATE TRIGGER update_area
  BEFORE INSERT OR UPDATE
  ON au_khoroolol
  FOR EACH ROW
  EXECUTE PROCEDURE update_area_or_length();

-- Schema "codelists"
set search_path to codelists, public;

create table cl_application_role
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_application_role to land_office_administration;
grant select on cl_application_role to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_application_type
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_application_type to land_office_administration;
grant select on cl_application_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_contract_condition
(
code int primary key,
description text unique not null,
description_en text unique
);
grant select, insert, update, delete on cl_contract_condition to land_office_administration;
grant select on cl_contract_condition to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_gender
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_gender to land_office_administration;
grant select on cl_gender to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_bank
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_bank to land_office_administration;
grant select on cl_bank to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_landuse_type
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique,
code2 integer not null,
description2 character varying(120) not null
);
-- data to beimported from old database
grant select, insert, update, delete on cl_landuse_type to land_office_administration;
grant select on cl_landuse_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_mortgage_type
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_mortgage_type to land_office_administration;
grant select on cl_mortgage_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_payment_frequency
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_payment_frequency to land_office_administration;
grant select on cl_payment_frequency to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_application_status
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
-- data to beimported from old database
grant select, insert, update, delete on cl_application_status to land_office_administration;
grant select on cl_application_status to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_transfer_type
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_transfer_type to land_office_administration;
grant select on cl_transfer_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_person_role
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_person_role to land_office_administration;
grant select on cl_person_role to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_person_type
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_person_type to land_office_administration;
grant select on cl_person_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_decision_level
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_decision_level to land_office_administration;
grant select on cl_decision_level to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_contract_status
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_contract_status to land_office_administration;
grant select on cl_contract_status to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_document_role
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
-- data to beimported from old database
grant select, insert, update, delete on cl_document_role to land_office_administration;
grant select on cl_document_role to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_record_right_type
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_record_right_type to land_office_administration;
grant select on cl_record_right_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_decision
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_decision to land_office_administration;
grant select on cl_decision to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_contract_cancellation_reason
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_contract_cancellation_reason to land_office_administration;
grant select on cl_contract_cancellation_reason to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_record_status
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_record_status to land_office_administration;
grant select on cl_record_status to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_record_cancellation_reason
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_record_cancellation_reason to land_office_administration;
grant select on cl_record_cancellation_reason to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_right_type
(
  code int primary key,
  description varchar(75) unique not null,
  description_en varchar(75) unique
);
grant select, insert, update, delete on cl_right_type to land_office_administration;
grant select on cl_right_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_payment_type
(
  code int primary key,
  description varchar(75) unique not null,
  description_en varchar(75) unique
);
grant select, insert, update, delete on cl_payment_type to land_office_administration;
grant select on cl_payment_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table cl_position_type
(
  code int primary key,
  description varchar(150) unique not null,
  description_en varchar(150) unique
);
grant select, insert, update, delete on cl_position_type to land_office_administration;
grant select on cl_position_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

comment on TABLE cl_application_role is 'Өргөдөл-төлөв';
comment on TABLE cl_application_status is 'Өргөдлийн явц';
comment on TABLE cl_application_type is 'Өргөдлийн төрөл';
comment on TABLE cl_bank is 'Банкны бүртгэл';
comment on TABLE cl_contract_cancellation_reason is 'Гэрээ цуцлах нөхцөл';
comment on TABLE cl_contract_condition is 'Гэрээний нөхцөлд өөрчлөлт хийх';
comment on TABLE cl_contract_status is 'Гэрээний явц';
comment on TABLE cl_decision is 'Захирамжийн шийдвэрлэлт';
comment on TABLE cl_decision_level is 'Захирамжийн түвшин';
comment on TABLE cl_document_role is 'Хавсралт бичиг баримтын жагсаалт';
comment on TABLE cl_gender is 'Хүйс';
comment on TABLE cl_landuse_type is 'Газрын нэгдмэл сангийн ангилал';
comment on TABLE cl_mortgage_type is 'Барьцааны төрөл';
comment on TABLE cl_payment_frequency is 'Газрын төлбөр, татварын нөхцөл';
comment on TABLE cl_person_role is 'Иргэн, хуулийн этгээдийн төлөв';
comment on TABLE cl_person_type is 'Иргэн, хуулийн этгээдийн төрөл';
comment on TABLE cl_record_cancellation_reason is 'Өмчлөлийн бүртгэл цуцлах нөхцөл';
comment on TABLE cl_record_right_type is 'Өмчлөлийн бүртгэлийн эрхийн төрөл';
comment on TABLE cl_record_status is 'Өмчлөлийн бүртгэлийн явц';
comment on TABLE cl_right_type is 'Эрхийн төрөл';
comment on TABLE cl_transfer_type is 'Эрх шилжүүлэх төрөл';
comment on TABLE cl_position_type is 'Албан тушаалын төрөл';

--conservation type
CREATE TABLE cl_conservation_type
(
  code integer NOT NULL,
  description character varying(75) NOT NULL,
  description_en character varying(75),
  CONSTRAINT cl_conservation_type_pkey PRIMARY KEY (code),
  CONSTRAINT cl_conservation_type_description_en_key UNIQUE (description_en),
  CONSTRAINT cl_conservation_type_description_key UNIQUE (description)
);
grant select, insert, update, delete on cl_conservation_type to land_office_administration;
grant select on cl_conservation_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;
COMMENT ON TABLE cl_conservation_type
  IS 'Газар хамгаалах';

--pollution type
CREATE TABLE cl_pollution_type
(
  code integer NOT NULL,
  description character varying(75) NOT NULL,
  description_en character varying(75),
  CONSTRAINT cl_pollution_type_pkey PRIMARY KEY (code),
  CONSTRAINT cl_pollution_type_description_en_key UNIQUE (description_en),
  CONSTRAINT cl_pollution_type_description_key UNIQUE (description)
);
grant select, insert, update, delete on cl_pollution_type to land_office_administration;
grant select on cl_pollution_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;
COMMENT ON TABLE cl_pollution_type
  IS 'Газарт учирсан хохирол';

-- Schema "settings"
set search_path to settings, cadastre, codelists, base, public;

create table set_role
(
user_name varchar(30) primary key,
surname varchar(30) not null,
first_name varchar(30) not null,
position varchar(50),
phone varchar(50),
mac_addresses varchar(100),
restriction_au_level1 text not null,
restriction_au_level2 text not null,
restriction_au_level3 text,
pa_from date not null default current_Date,
pa_till date not null default 'infinity',
working_au_level1 varchar(3) references admin_units.au_level1 ON UPDATE CASCADE ON DELETE RESTRICT,
working_au_level2 varchar(5) references admin_units.au_level2 ON UPDATE CASCADE ON DELETE RESTRICT
);
grant usage on sequence set_role_user_id_seq to land_office_administration;
grant select, insert, update, delete on set_role to role_management;
grant SELECT, update(pa_from, pa_till, working_au_level1, working_au_level2) on set_role to public;

CREATE OR REPLACE FUNCTION user_check()
  RETURNS trigger AS
$BODY$
DECLARE
	is_role_manager boolean := false;
BEGIN
	SELECT 'role_management' in (SELECT d.rolname AS group FROM pg_roles c JOIN (SELECT rolname, member FROM pg_auth_members a JOIN pg_roles b ON a.roleid = b.oid) d ON d.member = c.oid WHERE lower(c.rolname) = user) into is_role_manager;
	
	IF (NEW.user_name != user AND not is_role_manager and user != 'geodb_admin') THEN
		RAISE EXCEPTION 'The current user (%) is not allowed to insert or update entries for another user (%) in table <set_role>!', user, NEW.user_name;
	END IF;

	IF (TG_OP = 'UPDATE' AND not is_role_manager and user != 'geodb_admin') THEN
		IF (OLD.user_name != user) THEN
			RAISE EXCEPTION 'The current user (%) is not allowed to insert or update entries for another user (%) in table <set_role>!', user, OLD.user_name;
		END IF;
	END IF;
 			
	RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql;

CREATE TRIGGER user_check
  BEFORE INSERT OR UPDATE
  ON set_role
  FOR EACH ROW
  EXECUTE PROCEDURE user_check();

CREATE OR REPLACE FUNCTION settings.set_role_date()
  RETURNS trigger AS
$BODY$
DECLARE
	year integer;
BEGIN
	year := date_part('year', NEW.pa_till);

	IF (year = 9999) THEN
		NEW.pa_till := 'infinity';
	END IF;

	RETURN NEW;
END;
$BODY$
  LANGUAGE plpgsql;

CREATE TRIGGER set_role_date
  BEFORE INSERT OR UPDATE
  ON settings.set_role
  FOR EACH ROW
  EXECUTE PROCEDURE settings.set_role_date();

create table set_report_parameter
(
name varchar(30) primary key,
value text not null
);
grant select, update(value) on set_report_parameter to land_office_administration;
grant select on set_report_parameter to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

insert into set_report_parameter VALUES ('land_office_name', '');
insert into set_report_parameter VALUES ('address', '');
insert into set_report_parameter VALUES ('phone', '');
insert into set_report_parameter VALUES ('fax', '');
insert into set_report_parameter VALUES ('report_email', '');
insert into set_report_parameter VALUES ('website', '');
insert into set_report_parameter VALUES ('bank', '');
insert into set_report_parameter VALUES ('account', '');

create table set_certificate
(
type int PRIMARY KEY,
description text,
range_first_no int not null,
range_last_no int not null,
current_no int not null
);
grant select, update(range_first_no, range_last_no) on set_certificate to land_office_administration;
grant select on set_certificate to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;
grant update(current_no) on set_certificate to contracting_update;

insert into set_certificate (type, description, range_first_no, range_last_no, current_no) VALUES (1, 'Mongolian Citizen', 1, 5000, 0);
insert into set_certificate (type, description, range_first_no, range_last_no, current_no) VALUES (2, 'Mongolian Business', 1, 5000, 0);
insert into set_certificate (type, description, range_first_no, range_last_no, current_no) VALUES (3, 'Foreign Citizen / Entity', 1, 5000, 0);
insert into set_certificate (type, description, range_first_no, range_last_no, current_no) VALUES (4, 'Mongolian State Organization', 1, 5000, 0);

create table set_payment
(
id serial primary key,
landfee_fine_rate_per_day decimal,
landtax_fine_rate_per_day decimal
);
grant select, update(landfee_fine_rate_per_day, landtax_fine_rate_per_day) on set_payment to land_office_administration;
grant usage on sequence set_payment_id_seq to land_office_administration;
grant select on set_payment to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

insert into set_payment (landfee_fine_rate_per_day, landtax_fine_rate_per_day) VALUES (0.5, 0.5);

create table set_logging
(
log_enabled BOOLEAN not null
);
grant select, update on set_logging to land_office_administration;
grant select on set_logging to log_view, role_management, cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

insert into set_logging (log_enabled) values (True);

create table set_survey_company
(
id serial primary key,
name varchar(100) not null,
address varchar(200)
);
grant usage on sequence set_survey_company_id_seq to land_office_administration;
grant select, insert, update, delete on set_survey_company to land_office_administration;
grant select on set_survey_company to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table set_surveyor
(
id serial primary key,
surname varchar(30) not null,
first_name varchar(30) not null,
phone varchar(50),
company int references set_survey_company on update cascade on delete restrict
);
grant usage on sequence set_surveyor_id_seq to land_office_administration;
grant select, insert, update, delete on set_surveyor to land_office_administration;
grant select on set_surveyor to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table set_fee_zone
(
fid serial primary key,
location varchar(30),
zone_no int,
area_m2 decimal,
geometry geometry(MULTIPOLYGON, 4326),
unique (location, zone_no)
);
grant usage on sequence set_fee_zone_fid_seq to land_office_administration;
grant select, insert, update, delete on set_fee_zone to land_office_administration;
grant select on set_fee_zone to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

CREATE INDEX st_idx_set_fee_zone
  ON set_fee_zone
  USING gist
  (geometry);

CREATE TRIGGER update_area
  BEFORE INSERT OR UPDATE
  ON set_fee_zone
  FOR EACH ROW
  EXECUTE PROCEDURE update_area_or_length();

create table set_tax_and_price_zone
(
fid serial primary key,
location varchar(30),
zone_no int,
area_m2 decimal,
geometry geometry(MULTIPOLYGON, 4326),
unique (location, zone_no)
);
grant usage on sequence set_tax_and_price_zone_fid_seq to land_office_administration;
grant select, insert, update, delete on set_tax_and_price_zone to land_office_administration;
grant select on set_tax_and_price_zone to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

CREATE INDEX st_idx_set_tax_and_price_zone
  ON set_tax_and_price_zone
  USING gist
  (geometry);

CREATE TRIGGER update_area
  BEFORE INSERT OR UPDATE
  ON set_tax_and_price_zone
  FOR EACH ROW
  EXECUTE PROCEDURE update_area_or_length();

create table set_base_fee
(
id serial primary key,
landuse int references cl_landuse_type on update cascade on delete restrict not null,
base_fee_per_m2 decimal not null,
subsidized_area int,
subsidized_fee_rate decimal,
fee_zone int references set_fee_zone on update cascade on delete restrict not null,
unique (landuse, fee_zone)
);
grant select, insert, update, delete on set_base_fee to land_office_administration;
grant usage on sequence set_base_fee_id_seq to land_office_administration;
grant select on set_base_fee to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table set_base_tax_and_price
(
id serial primary key,
landuse int references cl_landuse_type on update cascade on delete restrict not null,
base_value_per_m2 decimal not null,
base_tax_rate decimal,
subsidized_area int,
subsidized_tax_rate decimal,
tax_zone int references set_tax_and_price_zone on update cascade on delete restrict not null,
unique (landuse, tax_zone)
);
grant select, insert, update, delete on set_base_tax_and_price to land_office_administration;
grant usage on sequence set_base_tax_and_price_id_seq to land_office_administration;
grant select on set_base_tax_and_price to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table set_application_type_document_role
(
application_type integer references cl_application_type on update cascade on delete restrict not null,
document_role integer references cl_document_role on update cascade on delete restrict not null,
constraint set_application_type_document_role_pkey PRIMARY KEY (application_type, document_role)
);
grant select, insert, update, delete on set_application_type_document_role to land_office_administration;
grant select on set_application_type_document_role to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table set_application_type_landuse_type
(
application_type integer references cl_application_type on update cascade on delete restrict not null,
landuse_type integer references cl_landuse_type on update cascade on delete restrict not null,
constraint set_application_type_landuse_type_pkey PRIMARY KEY (application_type, landuse_type)
);
grant select, insert, update, delete on set_application_type_landuse_type to land_office_administration;
grant select on set_application_type_landuse_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table set_person_type_application_type
(
  application_type integer references cl_application_type on update cascade on delete restrict not null,
  person_type integer references cl_person_type on update cascade on delete restrict not null,
  constraint set_person_type_application_type_pkey PRIMARY KEY (application_type, person_type)
);
grant select, insert, update, delete on set_person_type_application_type to land_office_administration;
grant select on set_person_type_application_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table set_right_type_application_type
(
  application_type integer references cl_application_type on update cascade on delete restrict not null,
  right_type integer references cl_right_type on update cascade on delete restrict not null,
  constraint set_right_type_application_type_pkey PRIMARY KEY (application_type, right_type)
);
grant select, insert, update, delete on set_right_type_application_type to land_office_administration;
grant select on set_right_type_application_type to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table set_contract_document_role
(
  role integer primary key  references cl_document_role on update cascade on delete restrict not null
);
grant select, insert, update, delete on set_contract_document_role to land_office_administration;
grant select on set_contract_document_role to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table set_validation
(
  set_validation_id CHARACTER VARYING PRIMARY KEY,
  sql_statement CHARACTER VARYING
);
grant select on set_validation to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;


INSERT INTO set_validation (set_validation_id, sql_statement) VALUES ('app_type_7_drop_parcel', 'Select count(*) from ct_contract contract, ct_contract_application_role con_app, ct_application app
where con_app.application = app.app_no and con_app.contract = contract.contract_no
      and contract.cancellation_date is NULL and app.parcel = ''{0}'' and app.app_type = 7;');
INSERT INTO set_validation (set_validation_id, sql_statement) VALUES ('app_type_8_drop_parcel', 'Select count(*) from ct_contract contract, ct_contract_application_role con_app, ct_application app
where con_app.application = app.app_no and con_app.contract = contract.contract_no
      and contract.cancellation_date is NULL and app.parcel = ''{0}'' and app.app_type = 8;');
INSERT INTO set_validation (set_validation_id, sql_statement) VALUES ('app_type_9_drop_parcel', 'Select count(*) from ct_contract contract, ct_contract_application_role con_app, ct_application app
where con_app.application = app.app_no and con_app.contract = contract.contract_no
      and contract.cancellation_date is NULL and app.parcel = ''{0}'' and app.app_type = 9;');
INSERT INTO set_validation (set_validation_id, sql_statement) VALUES ('app_type_10_drop_parcel', 'Select count(*) from ct_contract contract, ct_contract_application_role con_app, ct_application app
where con_app.application = app.app_no and con_app.contract = contract.contract_no
      and contract.cancellation_date is NULL and app.parcel = ''{0}'' and app.app_type = 10;');
INSERT INTO set_validation (set_validation_id, sql_statement) VALUES ('app_type_11_drop_parcel', 'Select count(*) from ct_contract contract, ct_contract_application_role con_app, ct_application app
where con_app.application = app.app_no and con_app.contract = contract.contract_no
      and contract.cancellation_date is NULL and app.parcel = ''{0}'' and app.app_type = 11;');
INSERT INTO set_validation (set_validation_id, sql_statement) VALUES ('app_type_12_drop_parcel', 'Select count(*) from ct_contract contract, ct_contract_application_role con_app, ct_application app
where con_app.application = app.app_no and con_app.contract = contract.contract_no
      and contract.cancellation_date is NULL and app.parcel = ''{0}'' and app.app_type = 12;');
INSERT INTO set_validation (set_validation_id, sql_statement) VALUES ('app_type_13_drop_parcel', 'Select count(*) from ct_contract contract, ct_contract_application_role con_app, ct_application app
where con_app.application = app.app_no and con_app.contract = contract.contract_no
      and contract.cancellation_date is NULL and app.parcel = ''{0}'' and app.app_type = 13;');
INSERT INTO set_validation (set_validation_id, sql_statement) VALUES ('app_type_14_drop_parcel', 'Select count(*) from ct_contract contract, ct_contract_application_role con_app, ct_application app
where con_app.application = app.app_no and con_app.contract = contract.contract_no
      and contract.cancellation_date is NULL and app.parcel = ''{0}'' and app.app_type = 14;');

INSERT INTO set_validation (set_validation_id, sql_statement) VALUES ('app_type_15_drop_parcel', 'Select count(distinct(app.app_no)) from ct_application app,
  (select row_number() over (PARTITION BY application order by status_date, status desc) as row, status, application, status_date
from ct_application_status order by application) as status
where  row = 1 and app.app_no = status.application and app.app_type = 15 and (status.status = 2 or status.status < 9) and app.parcel = ''{0}'';
');
INSERT INTO set_validation (set_validation_id, sql_statement) VALUES ('app_type_2_drop_parcel', 'Select count(distinct(app.app_no)) from ct_application app,
  (select row_number() over (PARTITION BY application order by status_date, status desc) as row, status, application, status_date
from ct_application_status order by application) as status
where  row = 1 and app.app_no = status.application and app.app_type = 2 and (status.status = 2 or status.status < 9) and app.parcel = ''{0}'';');

CREATE TABLE set_official_document (
  id serial primary key,
  visible BOOLEAN DEFAULT TRUE,
  name CHARACTER VARYING(100),
  description CHARACTER VARYING (100),
  content BYTEA
);

grant select, insert, update, delete on set_official_document to land_office_administration;
grant usage on sequence set_official_document_id_seq to land_office_administration;
grant select on set_official_document to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

set search_path to base, codelists, admin_units, public;

create table bs_person
(
id serial,
type int references cl_person_type on update cascade on delete restrict not null,
name varchar(250) not null,
middle_name varchar(50),
first_name varchar(50),
gender int references cl_gender on update cascade on delete restrict,
date_of_birth date,
contact_surname varchar(50),
contact_first_name varchar(50),
contact_position varchar(50),
person_id varchar primary key,
state_registration_no varchar(20),
bank int references cl_bank on update cascade on delete restrict,
bank_account_no varchar(20),
phone varchar(30),
mobile_phone varchar(30),
email_address varchar(60),
website varchar(60),
address_town_or_local_name varchar(50),
address_neighbourhood varchar(250),
address_street_name varchar(250),
address_khaskhaa varchar(50),
address_building_no varchar(10),
address_entrance_no varchar(10),
address_apartment_no varchar(10),
address_au_level1 varchar(3) references au_level1 on update cascade on delete restrict,
address_au_level2 varchar(5) references au_level2 on update cascade on delete restrict,
address_au_level3 varchar(8) references au_level3 on update cascade on delete restrict,
address_au_khoroolol int references au_khoroolol on update cascade on delete restrict
);
grant select, insert, update, delete on bs_person to contracting_update;
grant usage on sequence bs_person_id_seq to contracting_update;
grant select on bs_person to contracting_view, reporting;

insert into settings.set_role(user_name, surname, first_name, restriction_au_level1, restriction_au_level2)
values('role_manager', 'Duck', 'Donald', 'AAA', 'SSSSS');

insert into settings.set_role(user_name, surname, first_name, restriction_au_level1, restriction_au_level2)
values('role_reporting', 'Reporter', 'Reporter', 'AAA', 'SSSSS');

-- Schema "valuations"
set search_path to codelists, public;
--create parcel type
CREATE TABLE cl_type_parcel
(
  code integer primary key,
  description character varying(75) unique NOT NULL,
  description_en character varying(75) unique
);
grant select, insert, update, delete on cl_type_parcel to land_office_administration;
grant select on cl_type_parcel to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

--create stove type
CREATE TABLE cl_type_stove
(
  code integer primary key,
  description character varying(75) unique NOT NULL,
  description_en character varying(75) unique
);
grant select, insert, update, delete on cl_type_stove to land_office_administration;
grant select on cl_type_stove to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

--create source information
CREATE TABLE cl_type_source
(
  code integer primary key,
  description character varying(75) unique NOT NULL,
  description_en character varying(75) unique
);
grant select, insert, update, delete on cl_type_source to land_office_administration;
grant select on cl_type_source to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

--create material building
CREATE TABLE cl_type_material
(
  code integer primary key,
  description character varying(75) unique NOT NULL,
  description_en character varying(75) unique
);
grant select, insert, update, delete on cl_type_material to land_office_administration;
grant select on cl_type_material to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

--create design building
CREATE TABLE cl_type_design
(
  code integer primary key,
  description character varying(75) unique NOT NULL,
  description_en character varying(75) unique
);
grant select, insert, update, delete on cl_type_design to land_office_administration;
grant select on cl_type_design to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

--create heat building
CREATE TABLE cl_type_heat
(
  code integer primary key,
  description character varying(75) unique NOT NULL,
  description_en character varying(75) unique
);
grant select, insert, update, delete on cl_type_heat to land_office_administration;
grant select on cl_type_heat to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

--create heat building
CREATE TABLE cl_type_status_building
(
  code integer primary key,
  description character varying(75) unique NOT NULL,
  description_en character varying(75) unique
);
grant select, insert, update, delete on cl_type_status_building to land_office_administration;
grant select on cl_type_status_building to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

--create building landuse
CREATE TABLE cl_type_landuse_building
(
  code integer primary key,
  description character varying(75) unique NOT NULL,
  description_en character varying(75) unique
);
grant select, insert, update, delete on cl_type_landuse_building to land_office_administration;
grant select on cl_type_landuse_building to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

--create type agriculture
CREATE TABLE cl_type_agriculture
(
  code integer primary key,
  description character varying(75) unique NOT NULL,
  description_en character varying(75) unique
);
grant select, insert, update, delete on cl_type_agriculture to land_office_administration;
grant select on cl_type_agriculture to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

--create type purchase or lease
CREATE TABLE cl_type_purchase_or_lease
(
  code integer primary key,
  description character varying(75) unique NOT NULL,
  description_en character varying(75) unique
);
grant select, insert, update, delete on cl_type_purchase_or_lease to land_office_administration;
grant select on cl_type_purchase_or_lease to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

--create equipment list
set search_path to codelists, public;

create table cl_equipment_list
(
code int primary key,
description varchar(75) unique not null,
description_en varchar(75) unique
);
grant select, insert, update, delete on cl_equipment_list to land_office_administration;
grant select on cl_equipment_list to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;
comment on TABLE cl_equipment_list is 'Тоног төхөөрөмжийн бүртгэл';

set search_path to settings, cadastre, codelists, base, public;
create table set_equipment
(
id serial primary key,
type int references cl_equipment_list on update cascade on delete restrict not null,
description varchar(250) not null,
officer_user varchar(30) references set_role on update cascade on delete restrict not null,
purchase_date date not null,
given_date date not null,
duration_date date not null,
mac_address varchar(50),
seller_name varchar(64)
);
grant usage on sequence set_equipment_id_seq to land_office_administration;
grant select, insert, update, delete on set_equipment to land_office_administration;
grant select on set_equipment to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table set_document
(
id serial primary key,
name varchar(100),
content bytea
);
grant select, insert, update, delete on set_document to land_office_administration;
grant usage on sequence set_document_id_seq to land_office_administration;
grant select on set_document to cadastre_view, cadastre_update, contracting_view, contracting_update, reporting;

create table set_equipment_document
(
equipment int references set_equipment on update cascade on delete cascade,
document int references set_document on update cascade on delete cascade,
primary key(equipment, document)
);
grant select, insert, update, delete on set_equipment_document to contracting_update,land_office_administration;
grant select on set_equipment_document to contracting_view, reporting;