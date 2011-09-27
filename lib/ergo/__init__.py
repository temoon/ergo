#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
ERGO
Main module
"""


import __builtin__

import getopt
import glob
import logging
import os
import sys
import threading
import time
import yaml

from aochat import Chat, ChatError


COMMANDS = {
    # Dummy
}


class ErgoError(Exception):
    """
    Show message if exists else show help.
    """
    
    pass


class ErgoConfig(dict):
    """
    Config.
    """
    
    def __init__(self, filename):
        dimensions = {
            "rk1": {
                "host": "chat.d1.funcom.com",
                "port": 7101,
                "name": "Atlantean",
            },
            
            "rk2": {
                "host": "chat.d2.funcom.com",
                "port": 7102,
                "name": "Rimor",
            },
        }
        
        config = {
            "general": {
                "include": "ergo.d",
                
                "log_level": "info",
                "log_filename": None,
            },
            
            "ao": {
                "dimensions": [
                    dimensions["rk1"],
                    dimensions["rk2"],
                ],
                
                "accounts": [
                    {
                        "username": "ergo",
                        "password": "",
                        "dimension": dimensions["rk1"],
                        "character": "Ergo",
                    },
                ],
            },
            
            "commands": {
                # Dummy
            },
        }
        
        # Read settings
        if filename:
            config = self.merge(self.read(filename), config)
        
        # Merge command settings
        for filename in filter(os.path.isfile, glob.glob(os.path.join(config["general"]["include"], "*.conf"))):
            config = self.merge(config, self.read(filename))
        
        dict.__init__(self, config)
    
    @staticmethod
    def read(filename):
        """
        Reads YAML file.
        """
        
        try:
            config = yaml.load(file(filename, "r")) or {}
        except IOError, error:
            raise ErgoError("Config '%s' reading error [%d]: %s" % (filename, error.errno, error.strerror))
        except yaml.YAMLError, error:
            raise ErgoError("Config '%s' parsing error in position (%s:%s): %s" % (filename, error.problem_mark.line + 1, error.problem_mark.column + 1, error.problem))
        
        return config
    
    @staticmethod
    def merge(original, default):
        """
        Merges two configs.
        """
        
        if issubclass(type(original), dict) and issubclass(type(default), dict):
            for key in default:
                if key in original:
                    original[key] = ErgoConfig.merge(original[key], default[key])
                else:
                    original[key] = default[key]
        
        return original


class ErgoLogger(logging.Logger):
    """
    Logger.
    """
    
    def __init__(self, level, filename):
        logging.Logger.__init__(self, "ergo")
        
        format = logging.Formatter("[%(asctime)s] %(threadName)s: %(message)s", "%Y-%m-%d %H:%M:%S %Z")
        
        handler = logging.FileHandler(filename) if filename else logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(format)
        
        self.setLevel(logging.getLevelName(level.upper()))
        self.addHandler(handler)


class ErgoThread(threading.Thread):
    """
    Bot instance.
    """
    
    def __init__(self, username, password, host, port, character, dimension):
        threading.Thread.__init__(self)
        
        # Thread settings
        self.name = "%s, %s" % (character, dimension,)
        
        # AO chat connection settings
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.character = character
    
    def run(self):
        while True:
            try:
                # Connect to dimension
                chat = Chat(self.username, self.password, self.host, self.port)
                
                # Select character by name
                for character in chat.characters:
                    if character.name == self.character:
                        break
                else:
                    log.critical("Unknown character: %s" % self.character)
                    break
                
                # Check if online
                if character.online:
                    log.critical("Character is online: %s" % character.name)
                    break
                
                # Login and listen chat
                chat.login(character.id)
                chat.start(self.callback)
            except ChatError, error:
                log.error(error)
                continue
            except SystemExit:
                break
            except Exception, error:
                log.exception(error)
                continue
            finally:
                time.sleep(1)
    
    def callback(self, chat, packet):
        """
        Callback on incoming packet.
        """
        
        # Log incoming packets
        log.debug(repr(packet))


class ErgoCommand(object):
    """
    Command interpreter.
    """
    
    def __init__(self, name):
        # Register command
        COMMANDS[name] = self


def show_error(message):
    """
    Show error message.
    """
    
    print >> sys.stderr, str(message).capitalize()
    
    return 1


def show_help(name = "ergo"):
    """
    Show help.
    """
    
    print >> sys.stdout, """
Usage:
    %s [options]

Options:
    -C, --config    Use specified configuration file.
    -D, --debug     Force debug mode.
    
    -L, --commands  List all commands.
    
    -?, --help      Show this help.
""" % name
    
    return 0


def init(argv = []):
    """
    Initializer.
    """
    
    # Command line options
    try:
        opts, args = getopt.getopt(argv, "C:DL?", ["config=", "debug", "commands", "help"])
    except getopt.GetoptError:
        raise ErgoError()
    else:
        opts = dict(opts)
    
    if "-?" in opts or "--help" in opts:
        raise ErgoError()
    
    # Config
    __builtin__.config = ErgoConfig(opts.get("-C", opts.get("--config", None)))
    
    # Logger
    __builtin__.log = ErgoLogger("debug" if opts.get("-D", opts.get("--debug")) else config["general"]["log_level"], config["general"]["log_filename"])
    
    # Load commands
    import ergo.commands
    
    return args
