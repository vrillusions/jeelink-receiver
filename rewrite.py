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


def update_influxdb(location, node_fields):
    # "sensor,location={} {}".format(location, ','.join(node_fields))
    pass


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

    config = ConfigParser(interpolation=None)
    config.read_file(open(os.path.join(_SCRIPT_PATH, 'default.ini')))
    config.read(
        [os.path.join(_SCRIPT_PATH, 'config.ini'), xdgconfig, args.config])

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

    serial_port = config.get('serial', 'port')
    baudrate = config.getint('serial', 'baudrate')
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
                if sensor['node'] == 2:
                    # node 2: garage
                    location = 'garage'
                    node_fields = {
                        'location': 'garage',
                        'lowbatt': bool(sensor['lowbatt']),
                        'temperature': sensor['port1'] / 100.0,
                        'door_open': bool(sensor['port4']),
                    }
                    update_influxdb(location, node_fields)
                    logger.info("{}: {}".format(location, node_fields))
                    #logger.info(','.join(list(node_fields.items())))
                elif sensor['node'] == 3:
                    # node 3: basement
                    location = 'basement'
                    node_fields = {
                        'lowbatt': bool(sensor['lowbatt']),
                        'temperature': sensor['port2'] / 100.0,
                        'humidity': sensor['port1'] / 100.0,
                        'water_detected': bool(sensor['port3']),
                    }
                    update_influxdb(location, node_fields)
                    logger.info(location, node_fields)
                logger.info(sensor)
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
    args = _parser.parse_args()
    sys.exit(main(args))
