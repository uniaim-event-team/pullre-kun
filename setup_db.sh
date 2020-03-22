#!/usr/bin/env bash

echo "drop database $2;" \
    | mysql -u $3 -p$4 -h $5 -P$6
echo "create database $2 character set utf8mb4;" \
    | mysql -u $3 -p$4 -h $5 -P$6
mysqldump -u $3 --password=$4 -h $5 -P$6 $1 \
    | mysql -u $3 -p$4 -h $5 -P$6 $2
