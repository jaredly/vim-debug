#!/usr/bin/env python

from distutils.core import setup
import os

setup(
    name='vim-debug',
    author="Shane Caraveo, Trent Mick",
    author_email="komodo-feedback@ActiveState.com",
    maintainer='Jared Forsyth',
    maintainer_email='jared@jaredforsyth.com',
    version='1.2',
    url='http://jabapyth.github.com/pydbgp/',
    packages=['vim_debug'],
    description='a plugin for vim that creates an integrated debugging environment',
    scripts=['bin/install-vim-debug.py'],
)

# vim: et sw=4 sts=4
