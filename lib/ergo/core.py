#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
Core components.
"""


import glob
import logging
import logging.handlers
import os
import threading
import time
import sys
import yaml


from aochat import (
    Chat, ChatError,
    
    AOSP_CHANNEL_JOIN,
    
    AOSP_PRIVATE_MESSAGE,
    AOSP_PRIVATE_CHANNEL_MESSAGE,
    AOSP_CHANNEL_MESSAGE,
)


COMMANDS = {
    # Dummy
}


class Error(Exception):
    """
    Base exception class.
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
        
        smtp_handler = logging.handlers.SMTPHandler(
            mailhost    = (config["general"]["smtp_host"], config["general"]["smtp_port"],),
            credentials = (config["general"]["smtp_username"], config["general"]["smtp_password"],),
            fromaddr    = config["general"]["smtp_from"],
            toaddrs     = config["general"]["smtp_to"],
            subject     = "Occurrence of an error",
        )
        
        smtp_handler.setLevel(logging.ERROR)
        smtp_handler.setFormatter(format)
        
        self.setLevel(logging.getLevelName(level.upper()))
        
        self.addHandler(handler)
        self.addHandler(smtp_handler)


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
                    log.critical("Unknown character: %s" % self.character_name)
                    break
                
                # Check if online
                if character.online:
                    log.critical("Character is online: %s" % character.name)
                    break
                
                self.character_id = character.id
                
                # Login and listen chat
                chat.login(character.id)
                chat.start(self.callback)
            except (SystemExit, KeyboardInterrupt,):
                break
            except ChatError, error:
                log.error(error)
                continue
            except Exception, error:
                log.exception(error)
                continue
            finally:
                time.sleep(1)
    
    def reply_private(self, chat, player, message):
        chat.send_private_message(player.id, message)
    
    def reply_group(self, chat, message):
        chat.send_private_channel_message(self.character_id, message)
    
    def reply_clan(self, chat, message):
        chat.send_channel_message(self.clan_channel_id, message)
    
    def command(self, name, chat, player, args = []):
        """
        Execute command.
        """
        
        try:
            COMMANDS[name].callback(chat, self, player, args)
        except KeyError:
            self.reply_private(chat, player, "Unknown command: %s. Type 'help' for list commands." % name)
        except Exception, error:
            self.reply_private(chat, player, "Unexpected error occurred. Please, try again later.")
            log.exception(error)
    
    def callback(self, chat, packet):
        """
        Callback for incoming packet.
        """
        
        # Log packet
        log.debug(repr(packet))
        
        # Private message
        if packet.type == AOSP_PRIVATE_MESSAGE.type:
            prefix = config["chat"]["prefix_private"]
        # Private channel message
        elif packet.type == AOSP_PRIVATE_CHANNEL_MESSAGE.type:
            prefix = config["chat"]["prefix_group"]
        # Channel message
        elif packet.type == AOSP_CHANNEL_MESSAGE.type and packet.channel_id == self.clan_channel_id:
            prefix = config["chat"]["prefix_clan"]
        # Other packet
        else:
            if packet.type == AOSP_CHANNEL_JOIN.type and packet.channel_name == "Clan (name unknown)":
                self.clan_channel_id = packet.channel_id
            
            return
        
        player  = Player(packet.character_id)
        message = packet.message.strip()
        
        # Parse message
        if message.startswith(prefix):
            args    = filter(len, message.split(" "))
            command = args.pop(0).lstrip(prefix)
            
            if not command:
                return
        else:
            return
        
        # Execute command
        self.command(command, chat, player, args)


class Player(object):
    """
    Player.
    """
    
    def __init__(self, id):
        self.id = id


class Command(object):
    """
    Command interpreter.
    """
    
    def __init__(self, name, desc, callback, help = None):
        self.name     = name
        self.desc     = desc
        self.callback = callback
        self.help     = help
        
        # Register command
        COMMANDS[name] = self
