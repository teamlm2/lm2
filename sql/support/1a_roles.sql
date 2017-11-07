-- To be run by a user with 'createrole' privilege
-- creates all required group roles and two user roles (role_manager and role_reporting)
create role geodb_admin createdb createrole login password 'geodb_admin';
create role land_office_administration;
create role db_creation createdb;
create role role_management createrole;
create role cadastre_view;
create role cadastre_update;
create role contracting_view;
create role contracting_update;
create role reporting;
create role log_view;
create role role_manager login password 'role_manager';
create role role_reporting login password 'role_reporting';
grant role_management to role_manager;
grant reporting to role_reporting;
