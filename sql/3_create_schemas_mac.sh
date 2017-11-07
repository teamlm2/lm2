#!/bin/bash

create_schemas()
{
    AIMAG_CODES=''
    SOUM_CODES=''

    while IFS= read -r line
    do
        TESTSTR=$(echo ${line})
        if [ "${TESTSTR::1}" == "#" -o "${TESTSTR}" == "" ]; then
            continue
        fi
        ACODE=${TESTSTR}
        AIMAG_CODES=${AIMAG_CODES},${ACODE}

        while IFS= read -r line
        do
            TESTSTR=$(echo ${line})
            if [ "${TESTSTR}" == "" ]; then
                continue
            fi

            SOUM_CODES=${SOUM_CODES},${line}

        done < "support/${ACODE}_soums.txt"

    done < "support/aimag.txt"

    LENGTH_SOUM_CODES=${#SOUM_CODES}
    SOUM_CODES=${SOUM_CODES:1:${LENGTH_SOUM_CODES}}

    LENGTH_AIMAG_CODES=${#AIMAG_CODES}
    AIMAG_CODES=${AIMAG_CODES:1:${LENGTH_AIMAG_CODES}}

    if [ "${SOUM_CODES}" == "" -o "${AIMAG_CODES}" == "" ]; then
        return
    fi

    sed -i '' "s/AAA/${AIMAG_CODES}/g" support/3a_create_schemas.sql
    sed -i '' "s/SSSSS/${SOUM_CODES}/g" support/3a_create_schemas.sql

    PGPASSWORD=${PWD} psql -U geodb_admin -h ${DBHOST} -p 5432 -d ${DBNAME} -f support/3a_create_schemas.sql

    sed -i '' "s/${SOUM_CODES}/SSSSS/g" support/3a_create_schemas.sql
    sed -i '' "s/${AIMAG_CODES}/AAA/g" support/3a_create_schemas.sql
}

create_soum_schemas()
{
    while IFS= read -r line
    do
        TESTSTR=$(echo ${line})
        if [ "${TESTSTR}" == "" ]; then
            continue
        fi

        sed -i '' "s/00000/${line}/g" support/3b_tables_per_soum.sql
        PGPASSWORD=${PWD} psql -U geodb_admin -h ${DBHOST} -p 5432 -d ${DBNAME} -f support/3b_tables_per_soum.sql
        sed -i '' "s/${line}/00000/g" support/3b_tables_per_soum.sql

    done < "support/${AIMAG_CODE}_soums.txt"
}

populate_codelist_tables()
{
    PGPASSWORD=${PWD} psql -U geodb_admin -h ${DBHOST} -p 5432 -d ${DBNAME} -f support/3c_populate_codelist_tables.sql
}

create_logging_schema()
{
    FIRST_SOUM=''

    while IFS= read -r line
    do
        TESTSTR=$(echo ${line})
        if [ "${TESTSTR}" == "" ]; then
            continue
        fi

        FIRST_SOUM=${line}
        break
    done < "support/${AIMAG_CODE}_soums.txt"

    sed -i '' "s/00000/${FIRST_SOUM}/g" support/3d_create_logging_schema.sql
    PGPASSWORD=${PWD} psql -U geodb_admin -h ${DBHOST} -p 5432 -d ${DBNAME} -f support/3d_create_logging_schema.sql
    sed -i '' "s/${FIRST_SOUM}/00000/g" support/3d_create_logging_schema.sql
}

create_logging_triggers()
{
    while IFS= read -r line
    do
        TESTSTR=$(echo ${line})
        if [ "${TESTSTR}" == "" ]; then
            continue
        fi

        sed -i '' "s/00000/${line}/g" support/3e_create_logging_triggers.sql
        PGPASSWORD=${PWD} psql -U geodb_admin -h ${DBHOST} -p 5432 -d ${DBNAME} -f support/3e_create_logging_triggers.sql
        sed -i '' "s/${line}/00000/g" support/3e_create_logging_triggers.sql
    done < "support/${AIMAG_CODE}_soums.txt"
}

create_report_views()
{
    while IFS= read -r line
    do
        TESTSTR=$(echo ${line})
        if [ "${TESTSTR}" == "" ]; then
            continue
        fi

        echo ${line}

        sed -i '' "s/00000/${line}/g" support/3f_create_report_views.sql
        PGPASSWORD=${PWD} psql -U geodb_admin -h ${DBHOST} -p 5432 -d ${DBNAME} -f support/3f_create_report_views.sql
        sed -i '' "s/${line}/00000/g" support/3f_create_report_views.sql
    done < "support/${AIMAG_CODE}_soums.txt"
}


# main script:

if [ "$1" == "" ]; then
    echo ""
    echo "Provide a database name (db already created)!"
    echo "Usage:"
    echo "./3_create_schemas.sh database_name password_for_geodb_admin [host]"
    echo "host defaults to 'localhost'."
    echo ""
    exit 1
fi
if [ "$2" == "" ]; then
    echo "Provide the password for geodb_admin!"
    echo "Usage:"
    echo "./3_create_schemas.sh database_name password_for_geodb_admin [host]"
    echo "host defaults to 'localhost'."
    echo ""
    exit 1
fi

DBNAME=$1
PWD=$2
DBHOST=$3

if [ "$3" == "" ]; then
    DBHOST="localhost"
fi

AIMAG_CODE=""
TESTSTR=""
FIRST_RUN="TRUE"

while IFS= read -r line
do
    TESTSTR=$(echo ${line})
    if [ "${TESTSTR::1}" == "#" -o "${TESTSTR}" == "" ]; then
        continue
    fi
    AIMAG_CODE=${TESTSTR}

    # call once only:
    if [ "${FIRST_RUN}" == "TRUE" ]; then
        create_schemas $DBNAME $PWD $DBHOST
    fi

    # call for each Aimag
    create_soum_schemas $AIMAG_CODE $DBNAME $PWD $DBHOST

    # call once only:
    if [ "${FIRST_RUN}" == "TRUE" ]; then
        populate_codelist_tables $DBNAME $PWD $DBHOST
        create_logging_schema $AIMAG_CODE $DBNAME $PWD $DBHOST
    fi

    # call for each Aimag
    create_logging_triggers $AIMAG_CODE $DBNAME $PWD $DBHOST
    create_report_views $AIMAG_CODE $DBNAME $PWD $DBHOST

    FIRST_RUN="FALSE"

done < "support/aimag.txt"

exit 0