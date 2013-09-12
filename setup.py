#!/usr/bin/env python

from distutils.core import setup
import os

setup(
    name='vim-debug',
    maintainer='Jared Forsyth',
    maintainer_email='jared@jaredforsyth.com',
    version='1.5.4',
    url='http://jaredforsyth.com/projects/vim-debug/',
    packages=['vim_debug'],
    description='a plugin for vim that creates an integrated debugging environment',
    scripts=['bin/install-vim-debug.py'],
)

# vim: et sw=4 sts=4
