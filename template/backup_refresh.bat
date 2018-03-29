@ECHO OFF
SET Dump_name=
SET Database_name=mn_webgis
SET Host=192.168.15.36
REM Set path to PostgreSQL bin directory
SET pgsql_bin_path="C:\Program Files\PostgreSQL\9.5\bin"
REM Set path to backup directory
SET backup_path="C:\Users\B.Ankhbold\.qgis2\python\plugins\lm2\template"

ECHO "ANHAAR !!! WebGIS -iin davhargiin medeelliig shinechilj baigaa tul tur HULEENE UU! Esvel ene tsonhnii Minimize tovchiig darna uu."
%pgsql_bin_path%\psql -U geodb_admin -h %Host% -d %Database_name% -f %backup_path%/webgis_refresh.sql
pause