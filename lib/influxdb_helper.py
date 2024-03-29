
# -*- coding: utf-8 -*-
from functools import lru_cache

from influxdb import InfluxDBClient
from loguru import logger
from requests.exceptions import ConnectionError


class InfluxDBHelper():
    def __init__(self, hostname, database, port=8086, user=None, password=None):
        logger.debug(f'Initiating InfluxDB connection to {hostname}:{port}')
        self.client = InfluxDBClient(
                hostname, port, user, password, database, timeout=20, retries=3)

    def _write_points(self, points, retention_policy=None):
        logger.trace(f'Sending request {points}')
        try:
            self.client.write_points(points, retention_policy=retention_policy)
        except ConnectionError as exc:
            # Likely server is offline temporarily. Just log it and continue
            logger.error(f'requests.exceptions.ConnectionError: {exc}')
            pass
        logger.debug('Wrote data to InfluxDB successfully')

    def add_node_data(self, node_data, measurement='node'):
        logger.trace(f'node_data: {node_data}')
        location = node_data.pop('location')
        events = node_data.pop('events')
        points = [
            {
                "measurement": measurement,
                "tags": {"location": location},
                "fields": node_data,
            }]
        if len(events) > 0:
            self.add_events(location, node_data, events)
        self._write_points(points)

    def add_events(self, location, node_data, events, measurement='events'):
        points = []
        logger.trace(f'events: {events}')
        # bug: if both a door status and water sensor in same node only one
        # event will be created (this was original in a loop)
        if 'door_open' in events:
            sensor = 'door_open'
            status = 'open' if events['door_open'] else 'closed'
            previous_status = self.get_last_event_status(location, sensor)
            title = f'{location} door is {status}'
            #text = f'{location} door is now {status}'
        elif 'water_detected' in events:
            sensor = 'water_detected'
            status = 'wet' if events['water_detected'] else 'dry'
            previous_status = self.get_last_event_status(location, sensor)
            title = f'{location} water sensor is {status}'
            #text = f'{location} water sensor is now {status}'
        logger.trace(f'get_last_event_status cache info: {self.get_last_event_status.cache_info()}')
        points.append(
            {
                "measurement": measurement,
                "tags": {
                    "location": location,
                    "sensor": sensor,
                },
                "fields": {
                    "title": title,
                    "tags": location,
                    "status": status,
                }
            }
        )
        if status != previous_status:
            logger.trace(f'Writing new event: {points}')
            self._write_points(points, retention_policy='forever')
            logger.debug('New event written to database, clear event status cache')
            logger.debug(f'get_last_event_status cache info: {self.get_last_event_status.cache_info()}')
            self.get_last_event_status.cache_clear()

    @lru_cache()
    def get_last_event_status(self, location, sensor):
        bind_params = {
            "location": location,
            "sensor": sensor,
        }
        query = 'SELECT status FROM forever.events WHERE location=$location AND sensor=$sensor ORDER BY time DESC LIMIT 1;'
        try:
            response = self.client.query(query, bind_params=bind_params)
        except ConnectionError as exc:
            # Likely server is offline temporarily. Just log it and continue
            logger.error(f'requests.exceptions.ConnectionError: {exc}')
            return None
        result = list(response.get_points())
        logger.trace(f'result: {result}')
        if len(result) > 0:
            status = result[0]['status']
        else:
            status = None
        logger.trace(f'status: {status}')
        return status
