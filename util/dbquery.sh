#!/bin/bash

set -e
set -u

influxdb_host="${INFLUXDB_HOST:-'docker-hostname'}"

curl_cmd="curl -Ss -XPOST http://${influxdb_host}:8086/query --data-urlencode"
#$curl_cmd 'q=CREATE DATABASE "jeelink" WITH DURATION 1d REPLICATION 1 NAME "1day"'
#$curl_cmd 'q=CREATE RETENTION POLICY "7day" ON "jeelink" DURATION 7d REPLICATION 1'
#$curl_cmd 'q=CREATE RETENTION POLICY "30day" ON "jeelink" DURATION 30d REPLICATION 1'
#$curl_cmd 'q=CREATE RETENTION POLICY "2month" ON "jeelink" DURATION 8w REPLICATION 1'
#$curl_cmd 'q=CREATE RETENTION POLICY "forever" ON "jeelink" DURATION INF REPLICATION 1'
#$curl_cmd 'q=CREATE CONTINUOUS QUERY "cq_5min" ON "jeelink" BEGIN SELECT mean(*),last(*) INTO "7day".:MEASUREMENT FROM "1day"./.*/ GROUP BY time(5m),* END'
#$curl_cmd 'q=CREATE CONTINUOUS QUERY "cq_30min" ON "jeelink" BEGIN SELECT mean(*),last(*) INTO "30day".:MEASUREMENT FROM "7day"./.*/ GROUP BY time(30m),* END'
#$curl_cmd 'q=CREATE CONTINUOUS QUERY "cq_2hour" ON "jeelink" BEGIN SELECT mean(*),last(*) INTO "2month".:MEASUREMENT FROM "30day"./.*/ GROUP BY time(2h),* END'
#$curl_cmd 'q=CREATE CONTINUOUS QUERY "cq_1day" ON "jeelink" BEGIN SELECT mean(*),last(*) INTO "forever".:MEASUREMENT FROM "2month"./.*/ GROUP BY time(1d),* END'
#$curl_cmd 'q=ALTER RETENTION POLICY "1day" ON "jeelink" DURATION 4d'
#$curl_cmd "q=DELETE FROM \"events\" WHERE time < '2020-01-01'"
#$curl_cmd "q=SELECT * FROM \"jeelink\".\"forever\".\"events\" "


curl_cmd="curl -Ss -XPOST http://${influxdb_host}:8086/write?db=jeelink&rp=forever --data-binary"
#$curl_cmd 'events location="garage",sensor="door_open" tags="garage",text="Garage door is now open",title="Garage door open",status="open" 1587787852619029546'
#INSERT 'events location="garage",sensor="door_open" tags="garage",text="Garage door is now closed",title="Garage door closed",status="closed" 1587788226532106250'
$curl_cmd 'events,location="basement",sensor="annotation" tags="basement",text="Basement jeenode has updated code and should report accurate humidity and temperature",title="Basement jeenode updated",status="updated" 1603546751466000000'
