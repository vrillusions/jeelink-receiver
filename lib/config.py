#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Python Template.

As this is a separate module it gives a basic singleton or global config object.
"""
from configparser import ConfigParser


class Config (ConfigParser):
    default_config = None
    user_config = None

    def __init__(self, interpolation=None):
        ConfigParser.__init__(self, interpolation=interpolation)
        self.read_file(open(self.default_config))
        self.read(self.user_config)
