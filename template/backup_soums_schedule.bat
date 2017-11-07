@ECHO OFF
SET Today=%date:~-4,4%-%date:~-7,2%-%date:~4,2%

REM Set path to PostgreSQL bin directory
SET pgsql_bin_path="C:\Program Files\PostgreSQL\9.5\bin"
REM Set path to backup directory
SET backup_path="D:\TM_LM2\dumps"
SET database_name=lm_1101

ECHO "ANHAAR !!! LM2-iin medeelliin sang nootsolj baigaa tul tur HULEENE UU! Esvel ene tsonhnii Minimize tovchiig darna uu."
%pgsql_bin_path%\pg_dump -U geodb_admin -Fc -N public -N tiger -N data -N topology %database_name% > %backup_path%\%database_name%_%Today%.dump