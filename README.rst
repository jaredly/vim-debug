.. Maintainer: Jared Forsyth <jared@jaredforsyth.com>
.. Source: http://github.com/jabapyth/vim-phpdebug

This plugin creates an integrated debugging environment in VIM.

Features:

- integration with xdebug
- step (into/over/out)
- live stack view
- breakpoint set/remove

**New:**

- watch expressions!
- live scope view

**New things that your average user probably won't appreciate, but anyone
wanting to hack at it should:**

- It's now in a true python package
- modularized
- cleaned up, substantially rewritted for consistency

Planned:

- conditional breakpoints

To start your debug session, use the following variants::

   Usage: Dbg - (no auto start)
          Dbg . (autostart current file -- python)
          Dbg url (autostart a URL -- PHP)
          Dbg num (autostart a past url -- PHP)

For PHP urls, vim-debug keeps track of the last 5 urls you debugged -- so you
don't have to keep typing them in.

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

To disable the default mappings you can set the "g:vim_debug_disable_mappings" to a value
different than 0 in the debugger.vim file.

Note: The debugger.vim file is installed by the install-vim-debug.py command in the ``$VIM/plugins/`` directory.

Screenshot: `[full size]
<http://jaredforsyth.com/media/uploads/images/vim_debug.jpeg>`_

.. image:: http://jaredforsyth.com/media/uploads/images/vim_debug.jpeg
   :width: 450

`xdebug docs <http://www.xdebug.org/docs-dbgp.php>`_

**Credits:**

:Sam Ghods: `(last activity 6/21/07) <http://www.vim.org/scripts/script.php?script_id=1929>`_
:Seung Woo Shin: `(last activity 12/7/04) <http://www.vim.org/scripts/script.php?script_id=1152>`_

