#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
ERGO
Core commands
"""


from aochat.aoml import *
from ergo import Command as ErgoCommand, COMMANDS


### CALLBACKS ##################################################################

def help_callback(chat, player, args):
    if args and args[0] in COMMANDS:
        command = COMMANDS[args[0]]
        
        window = text(
            "Help on %s command:%s%s%s%s" % (
                command.name, br(2),
                command.desc, br(2),
                command.help() if command.help else "No help available."
            ),
            
            command.name
        )
        
        return "Help on command: %s" % window
    
    return "Type 'help &lt;command&gt;' for command specified help: %s." % text(help_help(), "available commands")

def help_help():
    return "Available commands:%s%s" % (
        br(),
        br().join(map(lambda name: text(COMMANDS[name].help(), name), filter(lambda name: name != "help", sorted(COMMANDS))))
    ),


def join_callback(chat, player, args):
    chat.private_channel_invite(player.id)

def join_help():
    return "Bot will invite you to private channel."


def leave_callback(chat, player, args):
    chat.private_channel_kick(player.id)

def leave_help():
    return "Bot will kick you from private channel."


### COMMANDS ###################################################################

help = ErgoCommand(
    name     = "help",
    desc     = "Usage information",
    callback = help_callback,
    help     = help_help,
)

join  = ErgoCommand(
    name     = "join",
    desc     = "Join private channel",
    callback = join_callback,
    help     = join_help,
)

leave = ErgoCommand(
    name     = "leave",
    desc     = "Leave private channel",
    callback = leave_callback,
    help     = leave_help,
)
