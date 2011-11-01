#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
Main module.
"""


import __builtin__

import getopt
import pkg_resources
import sys

from ergo.core import Config as ErgoConfig, Logger as ErgoLogger

import ergo.commands


def show_error(message):
    """
    Show error message.
    """
    
    print >> sys.stderr, message[0].upper() + message[1:]
    
    return 1


def show_help():
    """
    Show help.
    """
    
    print >> sys.stdout, """
Usage:
    ergo [options]

Options:
    -C, --config    Use specified configuration file.
    -D, --debug     Force debug mode.
    
    -?, --help      Show this help.
"""
    
    return 0


def init(argv = []):
    """
    Initializer.
    """
    
    # Command line options
    try:
        opts, args = getopt.getopt(argv, "C:D?", ["config=", "debug", "help"])
    except getopt.GetoptError, error:
        show_error(error.msg)
        return show_help()
    else:
        opts = dict(opts)
    
    # Show help
    if "-?" in opts or "--help" in opts:
        return show_help()
    
    # Config
    __builtin__.config = ErgoConfig(opts.get("-C", opts.get("--config")))
    
    # Logger
    if "-D" in opts or "--debug" in opts:
        log_level = "debug"
    else:
        log_level = config["general"]["log_level"]
    
    __builtin__.log = ErgoLogger(log_level, config["general"]["log_filename"])
    
    # Load plugins
    for plugin in pkg_resources.iter_entry_points("ergo.plugins"):
        plugin.load()
    
    return 1


if __name__ == "__main__":
    status = init(sys.argv[1:])
    sys.exit(status)
