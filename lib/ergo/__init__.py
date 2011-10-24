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

from aochat import (
    Chat, ChatError,
    
    AOSP_PRIVATE_MESSAGE,
    AOSP_PRIVATE_CHANNEL_MESSAGE,
    AOSP_CHANNEL_MESSAGE,
    AOSP_CHANNEL_JOIN,
)


COMMANDS = {
    # Dummy
}


class ErgoError(Exception):
    """
    You should show message if exists else show help.
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
                "help": None,
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
        self.character_id = 0
        self.character_name = character
        self.clan_channel_id = 0
    
    def run(self):
        while True:
            try:
                # Connect to dimension
                chat = Chat(self.username, self.password, self.host, self.port)
                
                # Select character by name
                for character in chat.characters:
                    if character.name == self.character_name:
                        break
                else:
                    log.critical("Unknown character: %s" % self.character)
                    break
                
                # Check if online
                if character.online:
                    log.critical("Character is online: %s" % character.name)
                    break
                
                self.character_id = character.id
                
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
        
        # Log packet
        log.debug(repr(packet))
        
        # Private message
        if packet.type == AOSP_PRIVATE_MESSAGE.type:
            prefix = "!"
            message = packet.message.strip()
            send_message = lambda msg: chat.send_private_message(packet.character_id, msg)
        # Private channel message
        elif packet.type == AOSP_PRIVATE_CHANNEL_MESSAGE.type:
            prefix = "!"
            message = packet.message.strip()
            send_message = lambda msg: chat.send_private_channel_message(self.character_id, msg)
        # Channel message
        elif packet.type == AOSP_CHANNEL_MESSAGE.type and packet.channel_id == self.clan_channel_id:
            prefix = "!"
            message = packet.message.strip()
            send_message = lambda msg: chat.send_channel_message(packet.channel_id, msg)
        # Other packet
        else:
            if packet.type == AOSP_CHANNEL_JOIN.type and packet.channel_name == "Clan (name unknown)":
                self.clan_channel_id = packet.channel_id
                log.debug("Clan channel ID: %s" % self.clan_channel_id)
            
            return
        
        # Parse message
        if message.strip().startswith(prefix):
            args = filter(len, message.split(" "))
            command = args.pop(0).lstrip(prefix)
            
            if not command:
                return
        else:
            return
        
        try:
            # Execute command
            try:
                output = COMMANDS[command].callback(chat, packet, args)
            except KeyError:
                send_message("Unknown command: %s" % command)
            else:
                # Send output to player
                if output:
                    send_message(output)
        except Exception, error:
            send_message("Unexpected error occurred. Please, try again later.")
            log.exception(error)


class ErgoCommand(object):
    """
    Command interpreter.
    """
    
    def __init__(self, name, desc, callback, help_callback = None):
        self.name          = name
        self.desc          = desc
        self.callback      = callback
        self.help_callback = help_callback
        
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
