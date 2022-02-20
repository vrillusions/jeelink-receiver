#!/bin/bash

set -e
set -u

influxdb_host="${INFLUXDB_HOST:-'docker-hostname'}"

# safety switch
exit 1

# note this only uses second precision
curl_cmd="curl -v -Ss -XPOST http://${influxdb_host}:8086/write?db=jeelink&rp=forever&precision=s --data-binary"
#$curl_cmd 'events,location=garage tags="garage,custom",title="Door to patio is open",status="updated" 1605965160'
$curl_cmd 'events,location=garage tags="garage,custom",title="Door to patio is closed",status="updated" 1605993780'
