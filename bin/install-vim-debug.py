#!/usr/bin/env python

text = '''\
" DBGp client: a remote debugger interface to the DBGp protocol
"
" Script Info and Documentation  {{{
"=============================================================================
"    Copyright: Copyright (C) 2010 Jared Forsyth
"      License:	The MIT License

" Do not source this script when python is not compiled in.
if !has("python")
    finish
endif

python << EOF
import vim
try:
    from vim_debug.commands import debugger_cmd
    vim.command('let has_debug = 1')
except ImportError, e:
    vim.command('let has_debug = 0')
    print 'python module vim_debug not found...'
EOF

if !has_debug
    finish
endif

command! -nargs=* Dbg python debugger_cmd('<args>')

" Debugger highlighting
hi DbgCurrent term=reverse ctermfg=White ctermbg=Red gui=reverse
hi DbgBreakPt term=reverse ctermfg=White ctermbg=Green gui=reverse
sign define current text=->  texthl=DbgCurrent linehl=DbgCurrent
sign define breakpt text=B>  texthl=DbgBreakPt linehl=DbgBreakPt
'''

import os, platform, sys
which = platform.system()
user = os.path.expanduser('~')
if which == 'Linux':
    vim_dir = os.path.join(user, '.vim')
elif which == 'Windows':
    vim_dir = os.path.join(user, 'vimfiles')
else:
    print>>sys.stderr, 'No $VIM directory found'
    sys.exit(1)
vim_dir = os.path.join(vim_dir, 'plugin')
fname = os.path.join(vim_dir, 'debugger.vim')
if os.path.exists(fname):
    print>>sys.stderr, 'Looks like it\'s already installed (at %s)' % fname
    sys.exit(2)
print 'installing to %s' % fname
open(fname, 'w').write(text)
print 'finished'




# vim: et sw=4 sts=4
