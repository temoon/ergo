#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
ERGO
Command: help
"""


from ergo import ErgoCommand, COMMANDS


def callback(chat, packet, args):
    """
    Command callback.
    """
    
    # Command specified help
    if args:
        try:
            command = args.pop(0)
            command = COMMANDS[command]
        except KeyError:
            return "Unknown command: %s" % command
        
        if command.help_callback:
            return command.help_callback(args)
        else:
            return "No help available for command '%s'" % command.name
    # General help information
    else:
        return help_callback()


def help_callback(args = []):
    """
    Help callback.
    """
    
    return "Type 'help &lt;command&gt;' for command specified help. Available commands: %s" % ", ".join(COMMANDS)


ErgoCommand(
    name = "help",
    desc = "Usage information",
    
    callback = callback,
    help_callback = help_callback,
)
