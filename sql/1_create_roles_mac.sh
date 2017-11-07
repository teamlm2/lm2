#!/bin/bash

if [ "$1" == "" ]; then
    echo "Provide the password for dbop!"
    echo "Usage:"
    echo "./1_create_roles.sh password_for_dbop [create_schema_roles_only] [host]"
    echo "password_for_dbop: Password for database role 'dbop'"
    echo "create_schema_roles_only: 0/1 (defaults to 1)"
    echo "host: IP address or server name (defaults to 'localhost')"
    echo ""
    exit 1
fi

if [ "$2" != "" -a "$2" != "0" -a "$2" != "1" ]; then
    echo "The 'create_schema_roles_only' parameter can be set to '0' or '1' only!"
    echo "Usage:"
    echo "./1_create_roles.sh password_for_dbop [create_schema_roles_only] [host]"
    echo "password_for_dbop: Password for database role 'dbop'"
    echo "create_schema_roles_only: 0/1 (defaults to 1)"
    echo "host: IP address or server name (defaults to 'localhost')"
    echo ""
    exit 1
fi

PWD=$1

DBHOST=$3
if [ "$3" == "" ]; then
    DBHOST="localhost"
fi

SCHEMA_ROLES_ONLY=$2
if [ "$2" == "" ]; then
    SCHEMA_ROLES_ONLY='1'
fi

if [ "$SCHEMA_ROLES_ONLY" == "0" ]; then
    PGPASSWORD=${PWD} psql -U dbop -h ${DBHOST} -p 5432 -d template1 -f support/1a_roles.sql
fi

AIMAG_CODE=""
TESTSTR=""

while IFS= read -r line
do
    TESTSTR=$(echo ${line})
    if [ "${TESTSTR::1}" == "#" -o "${TESTSTR}" == "" ]; then
        continue
    fi
    AIMAG_CODE=${TESTSTR}

    while IFS= read -r line
    do
        TESTSTR=$(echo ${line})
        if [ "${TESTSTR}" == "" ]; then
            continue
        fi

        PGPASSWORD=${PWD} psql -U dbop -h ${DBHOST} -p 5432 -d template1 -c "create role s$line"
    done < "support/${AIMAG_CODE}_soums.txt"

done < "support/aimag.txt"
