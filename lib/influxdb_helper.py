
# -*- coding: utf-8 -*-
from functools import lru_cache

from influxdb import InfluxDBClient
from loguru import logger
from requests.exceptions import ConnectionError


class InfluxDBHelper():
    def __init__(self, hostname, database, port=8086, user=None, password=None):
        logger.trace(f'Initiating InfluxDB connection to {hostname}:{port}')
        self.client = InfluxDBClient(hostname, port, user, password, database)

    def _write_points(self, points, retention_policy=None):
        logger.trace(f'Sending request {points}')
        try:
            self.client.write_points(points, retention_policy=retention_policy)
        except ConnectionError as exc:
            # Likely server is offline temporarily. Just log it and continue
            logger.error(f'requests.exceptions.ConnectionError: {exc}')
        pass

    def add_sensor_data(self, sensor_data, measurement='sensor'):
        logger.trace(f'sensor_data: {sensor_data}')
        location = sensor_data.pop('location')
        events = sensor_data.pop('events')
        points = [
            {
                "measurement": measurement,
                "tags": {"location": location},
                "fields": sensor_data,
            }]
        if len(events) > 0:
            self.add_events(location, sensor_data, events)
        self._write_points(points)

    def add_events(self, location, sensor_data, events, measurement='events'):
        points = []
        logger.trace(f'events: {events}')
        # bug: if both a door status and water sensor in same sensor only one
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
        response = self.client.query(query, bind_params=bind_params)
        result = list(response.get_points())
        logger.trace(f'result: {result}')
        if len(result) > 0:
            status = result[0]['status']
        else:
            status = None
        logger.trace(f'status: {status}')
        return status
