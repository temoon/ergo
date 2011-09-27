#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
ERGO
Commands (plugins)
"""


import __builtin__


if hasattr(__builtin__, "config") and issubclass(type(config), dict):
    __all__ = config.get("commands", {}).keys()


from ergo.commands import *
