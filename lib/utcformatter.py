
# -*- coding: utf-8 -*-
from __future__ import (division, absolute_import, print_function,
                        unicode_literals)
import logging
import time


class UTCFormatter(logging.Formatter):
    converter = time.gmtime
