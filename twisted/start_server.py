#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Listener for jeelink device."""
import os
import sys
import logging
import logging.config

from twisted.internet import reactor
from twisted.internet.serialport import SerialPort
from twisted.python import usage, log

import jeelink_receiver


if __name__ == '__main__':
    o = jeelink_receiver.Options()
    try:
        o.parseOptions()
    except usage.UsageError as errortext:
        print("%s: %s" % (sys.argv[0], errortext))
        print("%s: Try --help for usage details." % (sys.argv[0]))
        raise SystemExit(1)

    # This is if we want to just use twisted's logging but we don't
    #logFile = sys.stdout
    #if o.opts['outfile']:
    #    logFile = o.opts['outfile']
    #log.startLogging(logFile)
    #_loglevel = getattr(logging, os.getenv('LOGLEVEL', 'INFO').upper())
    _loglevel = getattr(logging, os.getenv('LOGLEVEL', 'DEBUG').upper())
    _logformat = "%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s"
    logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(logging.Formatter(_logformat))
    _console_handler.setLevel(_loglevel)
    _log = logging.getLogger()
    _log.addHandler(_console_handler)
    observer = log.PythonLoggingObserver()
    observer.start()

    SerialPort(
        jeelink_receiver.JeelinkProtocol(), o.opts['port'], reactor,
        baudrate=int(o.opts['baudrate']))
    reactor.run()
