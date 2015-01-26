#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Jeelink Receiver.

Environment Variables
    LOGLEVEL: overrides the level specified here. Choices are debug, info,
        warning, error, and critical. Default is warning.

"""

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)
import os
import sys
import logging
import logging.config
import atexit
import sqlite3
from optparse import OptionParser

import serial

from lib.utcformatter import UTCFormatter


__version__ = '0.1.0-dev'


SERIAL_PORT = '/dev/ttyUSB0'


def _parse_opts(argv=None):
    """Parse the command line options.

    :param list argv: List of arguments to process. If not provided then will
        use optparse default
    :return: options,args where options is the list of specified options that
        were parsed and args is whatever arguments are left after parsing all
        options.

    """
    parser = OptionParser(version='%prog {}'.format(__version__))
    parser.set_defaults(
        verbose=False, readonly=False, config='config.ini',
        db_name='jeelink-receiver.sqlite3')
    parser.add_option('-c', '--config', dest='config', metavar='FILE',
        help='Use config FILE (default: %default)')
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Be more verbose (default is no)')
    parser.add_option('-r', '--read-only', dest='readonly', action='store_true',
        help="Don't update database (useful with -v)")
    parser.add_option('-d', '--db-name', dest='db_name', metavar='FILE',
        help="Use database FILE (default: %default)")
    (options, args) = parser.parse_args(argv)
    return options, args


def format_temp(int1, int2):
    # First off cast them int in case sent as strings
    int1 = int(int1)
    int2 = int(int2)
    result = int1 + (int2 << 8)
    # Divide by 100 to get actual float
    # PY2 note: make sure you import division from __future__
    result = result / 100
    # Now to handle negative numbers
    if result > 128:
        result = result - 256
    # Only want max 2 decimal precision
    result = round(result, 2)
    return result


def format_doorstatus(int1):
    # First off cast them int in case sent as strings
    int1 = int(int1)
    if int1 == 0:
        result = "CLOSED"
    else:
        result = "OPEN"
    return result


def format_lowbat(int1):
    # First off cast them int in case sent as strings
    int1 = int(int1)
    if int1 == 0:
        result = False
    else:
        result = True
    return result


def _serial_cleanup(ser=None):
    log = logging.getLogger()
    log.debug("Closing serial port")
    if ser:
        ser.close()


def main(argv=None):
    """The main function.

    :param list argv: List of arguments passed to command line. Default is None,
        which then will translate to having it set to sys.argv.

    :return: Optionally returns a numeric exit code. If not given then will
        default to 0.
    :rtype: int

    """
    _loglevel = getattr(logging, os.getenv('LOGLEVEL', 'INFO').upper())
    _logformat = "%(asctime)sZ - %(name)s - %(levelname)s - %(message)s"
    logging.config.fileConfig('logging.ini')
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(UTCFormatter(_logformat))
    _console_handler.setLevel(_loglevel)
    log = logging.getLogger()
    log.addHandler(_console_handler)
    if argv is None:
        argv = sys.argv
    #(options, args) = _parse_opts(argv[1:])
    # If not using args then don't bother storing it
    options = _parse_opts(argv)[0]
    if options.verbose:
        log.setLevel(logging.DEBUG)
        _console_handler.setLevel(logging.DEBUG)
    if not options.readonly:
        conn = sqlite3.connect(options.db_name)
        c = conn.cursor()
        c.execute("SELECT 1 FROM nodes")
    else:
        log.warning('Running in read only mode')
    ser = serial.Serial(SERIAL_PORT, 57600)
    atexit.register(_serial_cleanup, ser)
    log.info("Initial startup successful. Monitoring JeeLink.")
    while True:
        line = ser.readline()
        log.debug(line.rstrip())
        linearray  = line.split(" ")
        if line[:2] == "OK":
            #line = line.rstrip()
            # format:  OK 2 11 22 33 44 55 66 77 88 99 00
            #  node id: 2
            #  low battery: "01 00" for low, "00 00" for ok
            #  port1:  33 + 44 * 256
            #  port2:  55 + 66 * 256
            #  port3:  77 + 88 * 256
            #  port4:  99 + 00 * 256
            # Door sensors: "01 00" for open, "00 00" for close
            # Temperature: "139 9" = 139 + (9 * 254) = 2444 / 100 = 24.44C
            # currently temperature at port1 and door at port4
            node = linearray[1]
            lowbattery = format_lowbat(linearray[2])
            port1_temp = format_temp(linearray[4], linearray[5])
            port4_door = format_doorstatus(linearray[10])
            log.info('node={} low_battery={} temperature={} door={}'.format(
                node, lowbattery, port1_temp, port4_door))
            if not options.readonly:
                # TODO:2014-02-11:teddy: deduplicate this
                c.execute("UPDATE nodes SET port1 = ?, port4 = ?, "
                    "low_battery = ? WHERE node_id = ?", (
                        port1_temp, linearray[10], linearray[2], node))
                if c.rowcount == 0:
                    log.info("node {} doesn't exist. creating".format(node))
                    c.execute("INSERT INTO nodes (node_id) VALUES (?)", (node))
                    c.execute("UPDATE nodes SET port1 = ?, port4 = ?, "
                        "low_battery = ? WHERE node_id = ?", (
                            port1_temp, linearray[10], linearray[2], node))
                if c.rowcount == 0:
                    log.error("unable to update table")
                    return 1
                conn.commit()
        elif line[:2] == "DF":
            # Dataflash message - currently just mention the store markers:
            #  DF S 42 8 123
            #       ^  ^--^---- 16 bit checksum
            #       \---------- memory page just finished
            if linearray[1] == "S":
                log.info('DataFlash: Store: page={}'.format(linearray[2]))
        elif line[:2] == " A":
            # Current config printed at startup
            #  A i1 g100 @ 915 MHz
            #    node_id network_group @ mhz_band MHz
            jeelink_id = linearray[2].lstrip('i')
            group = linearray[3].lstrip('g')
            mhz = linearray[5]
            log.info('Jeelink Configuration: node={} group={} freq={}'.format(
                jeelink_id, group, mhz))


if __name__ == "__main__":
    sys.exit(main())

