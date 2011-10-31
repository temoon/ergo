#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
Main module.
"""


import __builtin__

import getopt
import glob
import logging
import os
import pkg_resources
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

from ergo.commands import Command, COMMANDS


class Error(Exception):
    """
    Base exception.
    """
    
    pass


class Config(dict):
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
                "include":      "ergo.d",
                
                "log_level":    "info",
                "log_filename": None,
            },
            
            "chat": {
                "prefix_private": "",
                "prefix_group":   "#",
            },
            
            "ao": {
                "dimensions": [
                    dimensions["rk1"],
                    dimensions["rk2"],
                ],
                
                "accounts": [
                    {
                        "username":  "ergo",
                        "password":  "",
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
        Read YAML config.
        """
        
        try:
            config = yaml.load(file(filename, "r")) or {}
        except IOError, error:
            raise Error("Config '%s' reading error [%d]: %s" % (filename, error.errno, error.strerror))
        except yaml.YAMLError, error:
            raise Error("Config '%s' parsing error in position (%s:%s): %s" % (filename, error.problem_mark.line + 1, error.problem_mark.column + 1, error.problem))
        
        return config
    
    @staticmethod
    def merge(original, default):
        """
        Merge two configs.
        """
        
        if issubclass(type(original), dict) and issubclass(type(default), dict):
            for key in default:
                if key in original:
                    original[key] = Config.merge(original[key], default[key])
                else:
                    original[key] = default[key]
        
        return original


class Logger(logging.Logger):
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


class Instance(threading.Thread):
    """
    Bot instance.
    """
    
    def __init__(self, username, password, host, port, character, dimension):
        threading.Thread.__init__(self)
        
        # Thread settings
        self.name            = "%s, %s" % (character, dimension,)
        
        # AO chat connection settings
        self.username        = username
        self.password        = password
        self.host            = host
        self.port            = port
        self.character_id    = 0
        self.character_name  = character
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
        Callback for incoming packet.
        """
        
        def send_private_message(message):
            chat.send_private_message(packet.character_id, message)
        
        def send_private_channel_message(message):
            chat.send_private_channel_message(self.character_id, message)
        
        def send_channel_message(message):
            chat.send_channel_message(packet.channel_id, message)
        
        # Log packet
        log.debug(repr(packet))
        
        message = packet.message.strip()
        
        # Private message
        if packet.type == AOSP_PRIVATE_MESSAGE.type:
            prefix       = config["chat"]["prefix_private"]
            send_message = send_private_message
        # Private channel message
        elif packet.type == AOSP_PRIVATE_CHANNEL_MESSAGE.type:
            prefix       = config["chat"]["prefix_group"]
            send_message = send_private_channel_message
        # Channel message
        elif packet.type == AOSP_CHANNEL_MESSAGE.type and packet.channel_id == self.clan_channel_id:
            prefix       = config["chat"]["prefix_group"]
            send_message = send_channel_message
        # Other packet
        else:
            if packet.type == AOSP_CHANNEL_JOIN.type and packet.channel_name == "Clan (name unknown)":
                self.clan_channel_id = packet.channel_id
            
            return
        
        # Parse message
        if message.strip().startswith(prefix):
            args    = filter(len, message.split(" "))
            command = args.pop(0).lstrip(prefix)
            
            if not command:
                return
        else:
            return
        
        # Execute command
        try:
            try:
                output = COMMANDS[command].callback(chat, packet, args)
                
                if output:
                    send_message(output)
            except KeyError:
                send_message("Unknown command: %s. Type 'help' for list commands." % command)
                return
        except Exception, error:
            send_message("Unexpected error occurred. Please, try again later.")
            log.exception(error)


def show_error(message):
    """
    Show error message.
    """
    
    print >> sys.stderr, message
    
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
    
    -L, --commands  List all commands.
    
    -?, --help      Show this help.
"""
    
    return 0


def show_commands():
    """
    List commands.
    """
    
    for command in sorted(COMMANDS):
        print >> sys.stdout, "\x1b[01m%s\x1b[0m - %s" % (COMMANDS[command].name, COMMANDS[command].desc)
    
    return 0


def init(argv = []):
    """
    Initializer.
    """
    
    # Command line options
    try:
        opts, args = getopt.getopt(argv, "C:DL?", ["config=", "debug", "commands", "help"])
    except getopt.GetoptError:
        return show_help()
    else:
        opts = dict(opts)
    
    if "-?" in opts or "--help" in opts:
        return show_help()
    
    # Config
    __builtin__.config = Config(opts.get("-C", opts.get("--config")))
    
    # Logger
    if "-D" in opts or "--debug" in opts:
        log_level = "debug"
    else:
        log_level = config["general"]["log_level"]
    
    __builtin__.log = Logger(log_level, config["general"]["log_filename"])
    
    # Load plugins
    for e in pkg_resources.iter_entry_points("ergo.commands"):
        ergo.commands.__dict__[e.name] = e.load()
    
    # List commands
    if "-L" in opts or "--commands" in opts:
        return show_commands()
    
    return 1
