#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Python Template.

Environment Variables
    LOGLEVEL: overrides the level specified here. Default is warning
        option: DEBUG, INFO, WARNING, ERROR, or CRITICAL
"""
import os
import sys
import argparse
from configparser import ConfigParser
from datetime import datetime

from appdirs import AppDirs
import serial
from loguru import logger

from lib.config import Config
from lib.influxdb_helper import InfluxDBHelper


__version__ = '0.1.0-dev'
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))


def to_int(byte_array, signed=True):
    return int.from_bytes(
        [int(x) for x in byte_array], byteorder='little', signed=signed)


def to_byte_string(value, count=2, signed=False, byteorder='little'):
    """Take bytes and return string of integers.

    Example: to_byte_string(123456, count=4) = '64 226 1 0'
    """
    byte_value = value.to_bytes(count, byteorder=byteorder, signed=signed)
    return ' '.join([str(x) for x in byte_value])


def get_replay_string(page, sequence):
    result = []
    result.extend(to_byte_string(page, byteorder='big').split())
    result.extend(to_byte_string(sequence, byteorder='big', count=4).split())
    return '{} r'.format(','.join(result))


def parse_sensor(sensor):
    """Parse the sensor data received from jeelink

    sensor should look like the following:
    sensor = {
        'node': int(line_bytes[1]),
        'lowbatt': to_int(line_bytes[2:4]),
        'port1': to_int(line_bytes[4:6]),
        'port2': to_int(line_bytes[6:8]),
        'port3': to_int(line_bytes[8:10]),
        'port4': to_int(line_bytes[10:12]),
    }

    Returned object will be similar to the following:
    parsed = {
        "location": "garage",
        "temperature": 23.04,
        "door_open": False,
    }
    """
    config = Config()
    node_section = 'node{}'.format(sensor['node'])
    if not config.has_section(node_section):
        logger.error('section [{}] does not exist'.format(node_section))
        return
    parsed = {
        "location": config[node_section]['location'],
        "low_battery": bool(sensor['lowbatt']),
        "events": {},
    }
    for i in range(1,5):
        port_name = f'port{i}'
        # XXX: Current limitation is if two ports serve the same purpose (two
        # temperature ports) the second one will overwrite first.
        if port_name in config[node_section]:
            port_type = config[node_section][port_name]
            if port_type in ['temperature', 'humidity']:
                # Temp and humidity had their values multiplied by 100 before
                # sending over so change it back
                parsed[port_type] = round(sensor[port_name] * .01, 2)
            elif port_type in ['door_open', 'water_detected']:
                parsed[port_type] = bool(sensor[port_name])
                parsed[f'{port_type}_int'] = int(sensor[port_name])
                parsed['events'][port_type] = bool(sensor[port_name])
            else:
                parsed[f'{port_name}_value'] = sensor[port_name]
    return parsed


@logger.catch
def main(args=None):
    """The main function.

    :param obj args: arguments as processed from argparse.

    :return: Optionally returns a numeric exit code. If not 0 then assume an
        error has happened.
    :rtype: int
    """
    appdir = AppDirs(appname='jeelink-receiver')
    xdgconfig = os.path.join(appdir.user_config_dir, 'config.ini')
    Config.default_config = os.path.join(_SCRIPT_PATH, 'default.ini')
    Config.user_config = [
        os.path.join(_SCRIPT_PATH, 'config.ini'), xdgconfig, args.config]
    config = Config()

    log_file = os.path.join(_SCRIPT_PATH, 'log', 'jeelink-receiver.log')
    logger.trace('removing all existing loggers up to this point')
    logger.remove()
    if args.verbose:
        if args.verbose == 1:
            loglevel = 'DEBUG'
        else:
            loglevel = 'TRACE'
    else:
        loglevel = 'INFO'
    logger.add(sys.stderr, level=loglevel)
    logger.add(log_file, rotation='daily', retention=5, level='DEBUG')

    idb = InfluxDBHelper(config['influxdb']['host'], config['influxdb']['db_name'], int(config['influxdb']['port']))

    serial_port = config['serial']['port']
    baudrate = int(config['serial']['baudrate'])
    with serial.Serial(serial_port, baudrate=baudrate) as ser:
        while True:
            raw_line = ser.readline()
            logger.debug(raw_line.rstrip())
            line_bytes = raw_line.split()
            if len(line_bytes) < 1:
                continue
            if line_bytes[0] == b'OK':
                # data line
                sensor = {
                    'node': int(line_bytes[1]),
                    'lowbatt': to_int(line_bytes[2:4]),
                    'port1': to_int(line_bytes[4:6]),
                    'port2': to_int(line_bytes[6:8]),
                    'port3': to_int(line_bytes[8:10]),
                    'port4': to_int(line_bytes[10:12]),
                }
                logger.debug(sensor)
                parsed = parse_sensor(sensor)
                logger.info(parsed)
                if not args.readonly:
                    idb.add_sensor_data(parsed)
            elif line_bytes[0] == b'DF':
                # dataflash line
                if line_bytes[1] == b'S':
                    dataflash = {
                        'last_page': int(line_bytes[2]),
                        'sequence_number': int(line_bytes[3]),
                        'timestamp': int(line_bytes[4]),
                    }
                    logger.info(dataflash)
                    df_replay = get_replay_string(
                        dataflash['last_page'], dataflash['sequence_number'])
                    logger.info('to replay: {}'.format(df_replay))
                elif line_bytes[1] == b'I':
                    dataflash = {
                        'last_page': int(line_bytes[2]),
                        'sequence_number': int(line_bytes[3]),
                    }
                    logger.info(dataflash)
                    df_replay = get_replay_string(
                        dataflash['last_page'], dataflash['sequence_number'])
                    logger.info('to replay: {}'.format(df_replay))
                else:
                    logger.info('dataflash: {}', line_bytes[1:])
            elif line_bytes[0] == b'A':
                # current config line
                logger.info('config {}', line_bytes[1:])


if __name__ == "__main__":
    _parser = argparse.ArgumentParser(description='Monitor JeeLink device')
    _parser.add_argument(
        '--version', action='version',
        version='%(prog)s {}'.format(__version__))
    _parser.add_argument(
        '-v', '--verbose', dest='verbose', action='count',
        help='increase verbosity')
    _parser.add_argument(
        '-c', '--config', dest='config', metavar='FILE',
        help='Use config FILE (default: %(default)s)', default='config.ini')
    _parser.add_argument(
        '-r', '--read-only', dest='readonly', action='store_true',
        help="Don't write data anywhere")
    args = _parser.parse_args()
    sys.exit(main(args))
