#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Listener for jeelink device."""
import sys
import time
import logging

from twisted.internet import reactor, task
from twisted.python import log
from twisted.protocols import basic


if sys.platform == 'win32':
    # win32 serial does not work yet!
    raise NotImplementedError, "The SerialPort transport does not currently support Win32"
    from twisted.internet import win32eventreactor
    win32eventreactor.install()


class JeelinkProtocol(basic.LineReceiver):
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.line_id = 0
        self.message_types = {
            'DF': self._parse_data_flash,
            'OK': self._parse_node_data,
        }
        self.log.debug("Logging thread stats every 300 seconds")
        log.msg("Logging thread stats every 300 seconds")
        loop_thread_stats = task.LoopingCall(self._log_thread_stats)
        loop_thread_stats.start(300)

    def _log_thread_stats(self):
        if reactor.threadpool:
            idle = len(reactor.threadpool.waiters)
            active = len(reactor.threadpool.working)
            total = len(reactor.threadpool.threads)
            log.msg("Thread count: idle={0} active={1} total={2}".
                format(idle, active, total))

    def _parse_data_flash(self, line):
        line_id = self.line_id
        self.log.debug("({0}) process dataflash value".format(line_id))
        #self.log.debug("({0}) sleeping for 90 seconds".format(line_id))
        #time.sleep(90)
        #self.log.debug("({0}) done sleeping".format(line_id))

    def _parse_node_data(self, line):
        line_id = self.line_id
        self.log.debug("({0}) process node data".format(line_id))
        #self.log.debug("({0}) sleeping for 90 seconds".format(line_id))
        #time.sleep(90)
        #self.log.debug("({0}) done sleeping".format(line_id))

    def lineReceived(self, line):
        # BUG: if a thread is stuck it may take a while to stop twisted
        # BUG: line_id needs to be specified as another parameter to
        #   callInThread or it won't be accurate. Not doing it right now as
        #   there's probably a better way to do it
        self.line_id = self.line_id + 1
        self.log.debug("({0}) received: {1}".format(self.line_id, line))
        message_type = line[:2]
        if message_type in self.message_types:
            reactor.callInThread(self.message_types[line[:2]], line)
