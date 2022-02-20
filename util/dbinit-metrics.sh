#!/bin/bash

set -e
set -u

influxdb_host="${INFLUXDB_HOST:-'docker-hostname'}"

curl_cmd="curl -Ss -XPOST http://${influxdb_host}:8086/query --data-urlencode"
#$curl_cmd 'q=CREATE DATABASE "metrics" WITH DURATION 7d REPLICATION 1 NAME "short"'
$curl_cmd 'q=DROP DATABASE "metrics"'
$curl_cmd 'q=CREATE DATABASE "metrics" WITH DURATION inf REPLICATION 1'
#$curl_cmd 'q=CREATE RETENTION POLICY "medium" ON "metrics" DURATION 24w REPLICATION 1'
#$curl_cmd 'q=CREATE RETENTION POLICY "forever" ON "metrics" DURATION INF REPLICATION 1'
#$curl_cmd 'q=CREATE CONTINUOUS QUERY "cq_short2medium" ON "metrics" BEGIN SELECT mean("humidity") AS humidity, mean("temperature") AS temperature, last("door_open") AS door_open, last("low_battery") AS low_battery, last("water_detected") AS water_detected INTO "metrics"."medium"."node" FROM "short"."node" GROUP BY time(5m),* END;'
#$curl_cmd 'q=CREATE CONTINUOUS QUERY "cq_medium2forever" ON "metrics" BEGIN SELECT mean("humidity") AS humidity, mean("temperature") AS temperature, last("door_open") AS door_open, last("low_battery") AS low_battery, last("water_detected") AS water_detected INTO "metrics"."forever"."node" FROM "medium"."node" GROUP BY time(6h),* END'
