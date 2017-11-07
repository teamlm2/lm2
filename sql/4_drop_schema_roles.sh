#!/bin/bash

if [ "$1" == "" ]; then
    echo "Provide the password for dbop!"
    echo "Usage:"
    echo "./4_drop_schema_roles.sh password_for_dbop [host]"
    echo "password_for_dbop: Password for database role 'dbop'"
    echo "host: IP address or server name (defaults to 'localhost')"
    echo ""
    exit 1
fi

PWD=$1

DBHOST=$2
if [ "$2" == "" ]; then
    DBHOST="localhost"
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

        PGPASSWORD=${PWD} psql -U dbop -h ${DBHOST} -p 5432 -d template1 -c "drop role s$line"
    done < "support/${AIMAG_CODE}_soums.txt"

done < "support/aimag.txt"
