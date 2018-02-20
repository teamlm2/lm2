@ECHO OFF
SET Dump_name=
SET Database_name=lm_4401
SET Host=localhost
SET Schema_name=s04207
SET pgsql_bin_path="C:\Program Files\PostgreSQL\9.5\bin"
REM Set path to backup directory
SET backup_file=D:/TM_LM2/dumps/s04207/s04207_2018-02-09.dump

ECHO "ANHAAR !!! LM2-iin medeelliin sang nootsolj baigaa tul tur HULEENE UU! Esvel ene tsonhnii Minimize tovchiig darna uu."
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d %Database_name% --disable-triggers %backup_file%
pause