@ECHO OFF
SET Dump_name=
SET Database_name=lm_1101
SET Host=localhost
SET Schema_name=
SET pgsql_bin_path="C:\Program Files\PostgreSQL\9.5\bin"
REM Set path to backup directory
SET backup_file=

ECHO "ANHAAR !!! LM2-iin medeelliin sang nootsolj baigaa tul tur HULEENE UU! Esvel ene tsonhnii Minimize tovchiig darna uu."
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d %Database_name% --disable-triggers %backup_file%
pause