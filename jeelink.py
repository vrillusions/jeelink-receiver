#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Python Template.

Environment Variables
    LOGLEVEL: overrides the level specified here. Choices are debug, info,
        warning, error, and critical. Default is warning.

"""

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)
import os
import sys
import logging
import sqlite3
from optparse import OptionParser

import serial


__version__ = '0.1.0-dev'


SERIAL_PORT = '/dev/ttyUSB0'


# Logger config
# DEBUG, INFO, WARNING, ERROR, or CRITICAL
# This will set log level from the environment variable LOGLEVEL or default
# to warning. You can also just hardcode the error if this is simple.
_LOGLEVEL = getattr(logging, os.getenv('LOGLEVEL', 'WARNING').upper())
_LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=_LOGLEVEL, format=_LOGFORMAT)


def _parse_opts(argv=None):
    """Parse the command line options.

    :param list argv: List of arguments to process. If not provided then will
        use optparse default
    :return: options,args where options is the list of specified options that
        were parsed and args is whatever arguments are left after parsing all
        options.

    """
    parser = OptionParser(version='%prog {}'.format(__version__))
    parser.set_defaults(verbose=False)
    parser.add_option('-c', '--config', dest='config', metavar='FILE',
        help='Use config FILE (default: %default)', default='config.ini')
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Be more verbose (default is no)')
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


def main(argv=None):
    """The main function.

    :param list argv: List of arguments passed to command line. Default is None,
        which then will translate to having it set to sys.argv.

    :return: Optionally returns a numeric exit code. If not given then will
        default to 0.
    :rtype: int

    """
    log = logging.getLogger()
    if argv is None:
        argv = sys.argv
    #(options, args) = _parse_opts(argv[1:])
    # If not using args then don't bother storing it
    options = _parse_opts(argv)[0]
    if options.verbose:
        log.setLevel(logging.DEBUG)
    ser = serial.Serial(SERIAL_PORT, 57600)
    conn = sqlite3.connect('jeelink-receiver.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM nodes")
    while True:
        line = ser.readline()
        if line[:2] == "OK":
            #line = line.rstrip()
            # format:  OK 2 33 44 55 66 77 88 99 00
            #  node id: 2
            #  port1:  33 + 44 * 256
            #  port2:  55 + 66 * 256
            #  port3:  77 + 88 * 256
            #  port4:  99 + 00 * 256
            # Door sensors: "01 00" for open, "00 00" for close
            # Temperature: "139 9" = 139 + (9 * 254) = 2444 / 100 = 24.44C
            log.debug(line)
            # currently temperature at port1 and door at port4
            linearray = line.split(" ")
            node = linearray[1]
            port1_temp = format_temp(linearray[2], linearray[3])
            port4_door = format_doorstatus(linearray[8])
            log.info('{} {} {}'.format(node, port1_temp, port4_door))
            c.execute("INSERT OR REPLACE INTO nodes (node_id, port1, port4) "
                    "VALUES (?, ?, ?)", (node, port1_temp, linearray[8]))
            conn.commit()


if __name__ == "__main__":
    sys.exit(main())

