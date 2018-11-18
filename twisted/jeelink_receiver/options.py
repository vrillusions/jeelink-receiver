#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Listener for jeelink device."""
from twisted.python import usage


class Options(usage.Options):
    # TODO:2015-01-10:teddy: add a -v optflag to set log level to debug
    optParameters = [
        ['port', 'p', '/dev/ttyUSB0', 'Device for serial mouse'],
        ['baudrate', 'b', '57600', 'Baudrate for serial mouse'],
        ['outfile', 'o', None, 'Logfile [default: sys.stdout]'],
    ]
