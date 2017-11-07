@ECHO OFF

SET Host=localhost
SET Schema_name=
SET pgsql_bin_path="C:\Program Files\PostgreSQL\9.5\bin"
REM Set path to backup directory
SET pg_dump_path=D:\dumps\lm_44\soums\last

ECHO "ANHAAR !!! LM2-iin medeelliin sang nootsolj baigaa tul tur HULEENE UU! Esvel ene tsonhnii Minimize tovchiig darna uu."
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4401 > %pg_dump_path%\lm_4401.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4404 > %pg_dump_path%\lm_4404.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4407 > %pg_dump_path%\lm_4407.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4410 > %pg_dump_path%\lm_4410.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4413 > %pg_dump_path%\lm_4413.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4416 > %pg_dump_path%\lm_4416.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4419 > %pg_dump_path%\lm_4419.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4422 > %pg_dump_path%\lm_4422.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4425 > %pg_dump_path%\lm_4425.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4428 > %pg_dump_path%\lm_4428.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4431 > %pg_dump_path%\lm_4431.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4434 > %pg_dump_path%\lm_4434.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4437 > %pg_dump_path%\lm_4437.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4440 > %pg_dump_path%\lm_4440.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4443 > %pg_dump_path%\lm_4443.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4446 > %pg_dump_path%\lm_4446.dump
%pgsql_bin_path%\pg_dump -U geodb_admin -h %Host% -Fc -N data -N public -N topology -N tiger lm_4449 > %pg_dump_path%\lm_4449.dump

exit