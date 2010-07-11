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
    if not callable(cmd['function']):
        if debugger.bend.connected():
            try:
                debugger.bend.command(cmd['function'])
            except (EOFError, socket.error):
                debugger.disable()
    elif cmd['options'].get('plain', False):
        cmd['function'](plain)
    else:
        cmd['function'](*args)
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
        if url.isdigit():
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
            debugger.init_vim()
            global _commands
            _commands = debugger.commands()
            debugger.start_url(url)
            return
    urls = load_urls()
    if not urls:
        print 'No saved sessions'
    for i, url in enumerate(urls):
        print '    %d) %s' % (i, url)
    print 'usage: start [url or number]'

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

