@ECHO OFF
SET Dump_name=
SET Database_name=lm_1101
SET Host=localhost
REM Set path to PostgreSQL bin directory
SET pgsql_bin_path="C:\Program Files\PostgreSQL\9.5\bin"
REM Set path to backup directory
SET backup_path="D:\TM_LM2\dumps"

ECHO "ANHAAR !!! LM2-iin medeelliin sang nootsolj baigaa tul tur HULEENE UU! Esvel ene tsonhnii Minimize tovchiig darna uu."
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N public -N topology -N tiger %Database_name% > %backup_path%\%Dump_name%.dump
pause