@ECHO OFF
SET Dump_name=
SET Database_name=lm_4401
SET Host=localhost
SET Schema_name=
SET pgsql_bin_path="C:\Program Files\PostgreSQL\9.5/bin"
REM Set path to backup directory
SET backup_file=D:/TM_LM2/dumps/s04201/person.sql

ECHO "ANHAAR !!! LM2-iin medeelliin sang nootsolj baigaa tul tur HULEENE UU! Esvel ene tsonhnii Minimize tovchiig darna uu."
%pgsql_bin_path%\psql -U postgres -h %Host% %Database_name% < %backup_file%
pause