#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Setup for AO Chat.
"""


from distutils.core import setup


setup(
    name         = "ergo",
    version      = "0.1.0.1pa",
    description  = "ERGO - Anarchy Online chat bot",
    author       = "Tema Novikov",
    author_email = "temoon@temoon.pp.ru",
    download_url = "https://github.com/temoon/ergo",
    
    scripts = (
        "bin/ergo",
    ),
    
    packages = (
    ),
    
    package_dir = {
    },
    
    classifiers = (
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2.7",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ),
)
