.. |vim-debug-logo| image:: https://raw.github.com/jabapyth/vim-debug/master/logo.png

|vim-debug-logo| vim-debug
=========================

.. Maintainer: Jared Forsyth <jared@jaredforsyth.com>
.. Source: http://github.com/jabapyth/vim-phpdebug

This plugin creates an integrated debugging environment in VIM.

It supports python and php.


Features
--------

* Integration with xdebug

* Step (into/over/out)

* Live stack view

* Breakpoint set/remove

* Watch expressions

* Live scope view

* Some improvements to make it easier to hack

  * It's now in a true python package

  * Modularized

  * Cleaned up, substantially rewritten for consistency


Planned:

* Conditional breakpoints


Usage
-----

To start your debug session, use the following variants::

   Usage: Dbg - (no auto start)
          Dbg . (autostart current file -- python)
          Dbg url (autostart a URL -- PHP)
          Dbg num (autostart a past url -- PHP)

Note: for PHP urls, vim-debug keeps track of the last 5 urls you debugged --
so you don't have to keep typing them in.

Debugger commands::

   [usage:] dbg command [options]
   - quit    :: exit the debugger
   - run     :: continue execution until a breakpoint is reached or the program ends
            default shortcut: \r
   - stop    :: exit the debugger
   - over    :: step over next function call
            default shortcut: \o
   - watch   :: execute watch functions
            default shortcut: \w
   - up      :: go up the stack
            default shortcut: \u
   - here    :: continue execution until the cursor (tmp breakpoint)
            default shortcut: \h
   - down    :: go down the stack
            default shortcut: \d
   - exit    :: exit the debugger
   - eval    :: eval some code
   - break   :: set a breakpoint
            default shortcut: \b
   - into    :: step into next function call
            default shortcut: \i
   - out     :: step out of current function call
            default shortcut: \t

To disable the default mappings, set the variable ``g:vim_debug_disable_mappings`` to a value
different than 0 in the debugger.vim file.

For example::

    let g:vim_debug_disable_mappings = 1


Installation
------------

Execute the following commands::

    sudo pip install dbgp vim-debug
    install-vim-debug.py

Note: the ``install-vim-debug.py`` command installs the ``debugger.vim`` in your ``$VIM/plugins/`` directory.

Take a look
----------------------

Screenshot: `[full size]
<http://jaredforsyth.com/media/uploads/images/vim_debug.jpeg>`_

.. image:: http://jaredforsyth.com/media/uploads/images/vim_debug.jpeg
   :width: 450

A screencast tutorial: https://www.youtube.com/watch?v=kairdgZCD1U


Some links of interest
----------------------

`Python package installer <http://pypi.python.org/pypi/pip>`_

`Xdebug docs <http://www.xdebug.org/docs-dbgp.php>`_


Credits
-------

:Sam Ghods: `(last activity 6/21/07) <http://www.vim.org/scripts/script.php?script_id=1929>`_
:Seung Woo Shin: `(last activity 12/7/04) <http://www.vim.org/scripts/script.php?script_id=1152>`_

