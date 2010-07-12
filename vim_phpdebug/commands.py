import os
import sys
import vim
import socket
import traceback
from new_debugger import Debugger

import shlex

_old_commands = _commands = {}
def debugger_cmd(plain):
    global _commands, debugger
    if not _commands:
        return start(*shlex.split(plain))
    if ' ' in plain:
        name, plain = plain.split(' ', 1)
        args = shlex.split(plain)
    else:
        name = plain
        plain = ''
        args = []
    if name not in _commands:
        print '[usage:] dbg command [options]'
        for command in _commands:
            print ' - ', command, '      ::', _commands[command]['options'].get('help', '')
        return
    cmd = _commands[name]
    try:
        if not callable(cmd['function']):
            if debugger.bend.connected():
                    debugger.bend.command(cmd['function'])
        elif cmd['options'].get('plain', False):
            cmd['function'](plain)
        else:
            cmd['function'](*args)
    except (EOFError, socket.error):
        if debugger is not None:
            debugger.disable()
    if name == 'quit':
        _commands = None
        debugger = None

def cmd(name, help='', plain=False):
    def decor(fn):
        _commands[name] = {'function':fn, 'options': {'help':help, 'plain':plain}}
        return fn
    return decor

debugger = None

def start(url = None):
    global debugger
    if debugger and debugger.started:
        return
    if url is not None:
        if url == '.':
            pass
        elif url.isdigit():
            urls = load_urls()
            num = int(url)
            if num < 0 or num >= len(urls):
                print 'invalid session number'
                url = None
            else:
                url = urls.pop(num)
                urls.insert(0, url)
        else:
            save_url(url)
        if url is not None:
            debugger = Debugger()
            if url == '.':
                fname = vim.current.buffer.name
                if not (os.path.exists(fname) and fname.endswith('.py')):
                    print 'Current file is not python (or doesn\'t exist on your hard drive)'
                    return
            debugger.init_vim()
            global _commands
            _commands = debugger.commands()
            if url == '.':
                debugger.start_py(fname)
            else:
                debugger.start_url(url)
            return
    urls = load_urls()
    if not urls:
        print 'No saved sessions'
    for i, url in enumerate(urls):
        print '    %d) %s' % (i, url)
    print 'usage: dbg [url or number]'

session_path = os.path.expanduser('~/.vim/vim_phpdebug.sess')

def load_urls():
    if os.path.exists(session_path):
        return open(session_path).read().split('\n')
    return []

def save_url(url):
    urls = load_urls()
    urls.insert(0, url)
    urls = urls[:5]
    open(session_path, 'w').write('\n'.join(urls))

