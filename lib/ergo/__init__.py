#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
ERGO - Anarchy Online chat bot libraries
"""


import logging
import threading

from aochat import Chat, ChatError


class Bot(threading.Thread):
    """
    Bot instance.
    """
    
    def __init__(self, username, password, host, port, character, dimension_name):
        threading.Thread.__init__(self)
        
        # Handlers
        self.name      = "%s, %s" % (character, dimension_name,)
        self.log       = logging.getLogger("ergo")
        
        # AO chat connection options
        self.username  = username
        self.password  = password
        self.host      = host
        self.port      = port
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
                    self.log.critical("Unknown character '%s'" % self.character)
                    break
                
                # Check if online
                if character.online:
                    self.log.critical("Character '%s' is online" % character.name)
                    break
                
                # Login and listen chat
                chat.login(character.id)
                chat.start(self.callback)
            except ChatError, error:
                self.log.error(error)
                continue
            except SystemExit:
                break
            except Exception, error:
                self.log.exception(error)
                continue
    
    def callback(self, chat, packet):
        # Log incoming packets
        self.log.debug(repr(packet))
        
        # TODO: ...
