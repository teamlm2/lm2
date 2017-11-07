Two methods to restore the database:

Method A
--------
1.) Create a database "darkhan" as copy of template_postgis.
2.) pg_restore -U postgres -d darkhan --disable-triggers dumps/schemas_and_data.dump

Method B
--------
1.) Create a database "darkhan" as copy of template_postgis.
2.) In support/aimag.txt write the 3-digits Aimag code (e.g. 045) of the Aimag(s)
    for which Soum schemas (sXXXXXX) are to be generated.
3.) Run shell script "3_create_schemas.sh"
4.) pg_restore -U postgres -d darkhan --disable-triggers dumps/data_only_part1.dump
5.) pg_restore -U postgres -d darkhan --disable-triggers dumps/data_only_part2.dump


To create the three dump files above run the commands as follows:

"schemas_and_data.dump":
------------------------
pg_dump -U geodb_admin -Fc -N public -N topology -N tiger darkhan > dumps/schemas_and_data.dump
pg_dump -U geodb_admin -Fc -N public -N topology -N tiger -N admin_units -N codelists -N data -N logging -N settings darkhan > dumps/schemas_and_data.dump
pg_restore -U postgres -d darkhan --disable-triggers dumps/data_only_part1.dump


"data_only_partX.dump"
----------------------
pg_dump -U geodb_admin -Fc -a -N public -N topology -N tiger -N codelists -N logging -N base -N settings darkhan > dumps/data_only_part1.dump
pg_dump -U geodb_admin -Fc -a -t settings.set_base* -t settings.set*zone darkhan > dumps/data_only_part2.dump
