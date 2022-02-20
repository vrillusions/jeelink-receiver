#!/bin/bash

set -e
set -u

influxdb_host="${INFLUXDB_HOST:-'docker-hostname'}"

curl_cmd="curl -Ss -XPOST http://${influxdb_host}:8086/query --data-urlencode"
$curl_cmd 'q=CREATE DATABASE "jeelink" WITH DURATION 7d REPLICATION 1 NAME "short"'
$curl_cmd 'q=CREATE RETENTION POLICY "medium" ON "jeelink" DURATION 24w REPLICATION 1'
$curl_cmd 'q=CREATE RETENTION POLICY "forever" ON "jeelink" DURATION INF REPLICATION 1'
$curl_cmd 'q=CREATE CONTINUOUS QUERY "cq_short2medium" ON "jeelink" BEGIN SELECT mean("humidity") AS humidity, mean("temperature") AS temperature, last("door_open") AS door_open, last("low_battery") AS low_battery, last("water_detected") AS water_detected INTO "jeelink"."medium"."node" FROM "short"."node" GROUP BY time(5m),* END;'
$curl_cmd 'q=CREATE CONTINUOUS QUERY "cq_medium2forever" ON "jeelink" BEGIN SELECT mean("humidity") AS humidity, mean("temperature") AS temperature, last("door_open") AS door_open, last("low_battery") AS low_battery, last("water_detected") AS water_detected INTO "jeelink"."forever"."node" FROM "medium"."node" GROUP BY time(6h),* END'
