#!/bin/bash

if [ "$1" == "" ]; then
    echo "Provide the password for dbop!"
    echo "Usage:"
    echo "./2_create_databases.sh password_for_dbop [host]"
    echo "host defaults to 'localhost'."
    echo ""
    exit 1
fi

PWD=$1

DBHOST=$2
if [ "$2" == "" ]; then
    DBHOST="localhost"
fi

while IFS= read -r line
do
    TESTSTR=$(echo ${line})
    if [ "${TESTSTR::1}" == "#" -o "${TESTSTR}" == "" ]; then
        continue
    fi
    PGPASSWORD=${PWD} psql -U dbop -h ${DBHOST} -p 5432 -d template1 -c "create database $line template=template_postgis"
    PGPASSWORD=${PWD} psql -U dbop -h ${DBHOST} -p 5432 -d template1 -c "grant create on database $line to geodb_admin"
done < "support/database_names.txt"

exit 0