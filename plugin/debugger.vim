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

" set this to 0 to enable the automatic mappings
" any other value will disable the mappings
let g:vim_debug_disable_mappings = 0
let g:has_debug = 0

python << EOF
import vim
import sys
import os.path

pylib_dir = os.path.join(vim.eval("expand('<sfile>:p:h')"), '..')
pylib_dir = os.path.abspath(pylib_dir)
sys.path.insert(0, pylib_dir)
try:
    from vim_debug.commands import debugger_cmd
    vim.command('let g:has_debug = 1')
except ImportError as e:
    print 'python module vim_debug not found...'
    raise
EOF

if !g:has_debug
    finish
endif

command! -nargs=* Dbg python debugger_cmd('<args>')

" Debugger highlighting
hi DbgCurrent term=reverse ctermfg=White ctermbg=Red gui=reverse
hi DbgBreakPt term=reverse ctermfg=White ctermbg=Green gui=reverse
sign define current text=->  texthl=DbgCurrent linehl=DbgCurrent
sign define breakpt text=B>  texthl=DbgBreakPt linehl=DbgBreakPt
