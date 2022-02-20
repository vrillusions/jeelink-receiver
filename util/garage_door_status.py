#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import cPickle as pickle
import smtplib
import email.message
import errno
from optparse import OptionParser


__version__ = '0.1.0-dev'


# Logger config
# DEBUG, INFO, WARNING, ERROR, or CRITICAL
# This will set log level from the environment variable LOGLEVEL or default
# to warning. You can also just hardcode the error if this is simple.
_LOGLEVEL = getattr(logging, os.getenv('LOGLEVEL', 'WARNING').upper())
_LOGFORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=_LOGLEVEL, format=_LOGFORMAT)


class PickleWrap(object):
    def __init__(self, filename):
        self.log = logging.getLogger()
        self.filename = filename
        self._load_file()

    def _load_file(self):
        try:
            with open(self.filename, 'rb') as fh:
                self.content = pickle.load(fh)
        except IOError as exc:
            if exc.errno == errno.ENOENT:
                # Just make content blank and save to create file
                self.log.info("File didn't exist, creating")
                self.content = {}
                self.save()
            else:
                raise

    def save(self):
        with open(self.filename, 'wb') as fh:
            pickle.dump(self.content, fh, -1)


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
    parser.add_option('-f', '--file-cache', dest='file_cache', metavar='FILE',
            help='Use FILE for cache (default: %default%)',
            default='./garage_door_status.cache')
    parser.add_option('-n', '--count', dest='hitcount', default='6',
            help='Send email after this number of times (default: %default%)')
    (options, args) = parser.parse_args(argv)
    return options, args


def format_doorstatus(int1):
    # First off cast them int in case sent as strings
    int1 = int(int1)
    if int1 == 0:
        result = "CLOSED"
    else:
        result = "OPEN"
    return result


def send_notification(door_status, count):
    msg = email.message.Message()
    msg['Subject'] = 'Garage door is {}'.format(door_status)
    msg['From'] = 'vr@vrillusions.com'
    msg['To'] = '3306207260@txt.att.net'
    msg.set_payload('Garage door is currently {}'.format(door_status))
    smtpobj = smtplib.SMTP('localhost', 25, 'vrillusions.com')
    smtpobj.sendmail(msg['From'], msg['To'], msg.as_string())
    return True


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
    cache = PickleWrap(options.file_cache)
    conn = sqlite3.connect('jeelink-receiver.sqlite3')
    c = conn.cursor()
    c.execute("SELECT port4 FROM nodes WHERE node_id = 2;")
    if c.rowcount == 0:
        log.error('Unable to get current status')
        return 1
    doornum = c.fetchone()[0]
    log.debug(doornum)
    door = format_doorstatus(doornum)
    log.debug('Door status: {}'.format(door))
    if door == 'OPEN':
        log.info('Door opened, incrementing counter')
        if 'opencount' in cache.content:
            cache.content['opencount'] = cache.content['opencount'] + 1
            if cache.content['opencount'] >= int(options.hitcount):
                log.info('Door has been open for {} checks, send notification'.
                        format(cache.content['opencount']))
                send_notification(door, cache.content['opencount'])
        else:
            log.info('initializing new counter')
            cache.content['opencount'] = 1
    else:
        log.info('Door closed, setting count to 0')
        cache.content['opencount'] = 0
    cache.save()


if __name__ == "__main__":
    sys.exit(main())

