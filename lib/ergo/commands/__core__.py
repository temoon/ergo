#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
ERGO
Core commands
"""


from ergo import ErgoCommand, COMMANDS


### CALLBACKS ##################################################################

def help_callback(chat, player, args):
    if args and args[0] in COMMANDS:
        command = COMMANDS[args[0]]
        return "%s - %s" % (command.name, command.desc,)
    
    return "Type 'help &lt;command&gt;' for command specified help. Available commands: %s" % ", ".join(COMMANDS)

def join_callback(chat, player, args):
    chat.private_channel_invite(player.id)

def leave_callback(chat, player, args):
    chat.private_channel_kick(player.id)


### COMMANDS ###################################################################

help  = ErgoCommand(name = "help", desc = "Usage information.", callback = help_callback)
join  = ErgoCommand(name = "join", desc = "Join private channel.", callback = join_callback)
leave = ErgoCommand(name = "leave", desc = "Leave private channel.", callback = leave_callback)
