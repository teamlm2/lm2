@ECHO OFF

SET Host=192.168.1.145
SET Schema_name=
SET pgsql_bin_path="C:\Program Files\PostgreSQL\9.5\bin"
REM Set path to backup directory
SET restore_path=D:\dumps\lm_44

ECHO "ANHAAR !!! LM2-iin medeelliin sang sergeej baigaa tul tur HULEENE UU! Esvel ene tsonhnii Minimize tovchiig darna uu."
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4401 --disable-triggers %restore_path%\lm_4401.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4404 --disable-triggers %restore_path%\lm_4404.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4407 --disable-triggers %restore_path%\lm_4407.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4410 --disable-triggers %restore_path%\lm_4410.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4413 --disable-triggers %restore_path%\lm_4413.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4416 --disable-triggers %restore_path%\lm_4416.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4419 --disable-triggers %restore_path%\lm_4419.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4422 --disable-triggers %restore_path%\lm_4422.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4425 --disable-triggers %restore_path%\lm_4425.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4428 --disable-triggers %restore_path%\lm_4428.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4431 --disable-triggers %restore_path%\lm_4431.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4434 --disable-triggers %restore_path%\lm_4434.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4437 --disable-triggers %restore_path%\lm_4437.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4440 --disable-triggers %restore_path%\lm_4440.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4443 --disable-triggers %restore_path%\lm_4443.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4446 --disable-triggers %restore_path%\lm_4446.dump
%pgsql_bin_path%\pg_restore -U postgres -h %Host% -d lm_4449 --disable-triggers %restore_path%\lm_4449.dump

exit