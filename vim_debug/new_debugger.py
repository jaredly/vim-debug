import subprocess
import textwrap
import socket
import vim
import sys
import os
import imp

from ui import DebugUI
from dbgp import DBGP

def vim_init():
    '''put DBG specific keybindings here -- e.g F1, whatever'''
    vim.command('ca dbg Dbg')

def vim_quit():
    '''remove DBG specific keybindings'''
    vim.command('cuna dbg')

def get_vim(name, default, fn=str):
    if vim.eval('exists("%s")' % name) == '1':
        return vim.eval(name)
    return default

import types
class Registrar:
    def __init__(self, args=(), kwds=(), named=True):
        if named:
            self.reg = {}
        else:
            self.reg = []
        self.args = args
        self.kwds = kwds
        self.named = named

    def register(self, *args, **kwds):
        def meta(func):
            self.add(func, args, kwds)

        return meta

    def add(self, func, args, kwds):
        if self.named:
            self.reg[args[0]] = {'function':func, 'args':args[1:], 'kwds':kwds}
        else:
            self.reg.append({'function':func, 'args':args, 'kwds':kwds})
        return func

    def bind(self, inst):
        res = {}
        for key, value in self.reg.iteritems():
            value = value.copy()
            res[key] = value
            if callable(value['function']):
                value['function'] = types.MethodType(value['function'], inst, inst.__class__)
        return res

    __call__ = register

class CmdRegistrar(Registrar):
    def add(self, func, args, kwds):
        lead = kwds.get('lead', '')

        disabled_mappings = False
        if vim.eval("exists('g:vim_debug_disable_mappings')") != "0":
            disabled_mappings = vim.eval("g:vim_debug_disable_mappings") != "0"

        if lead and not disabled_mappings:
            vim.command('map <Leader>%s :Dbg %s<cr>' % (lead, args[0]))
        dct = {'function':func, 'options':kwds}
        for name in args:
            self.reg[name] = dct

class Debugger:
    ''' This is the main debugger class... '''
    options = {'port':9000, 'max_children':32, 'max_data':'1024', 'minbufexpl':0, 'max_depth':1}
    def __init__(self):
        self.started = False
        self.watching = {}
        self._type = None

    def init_vim(self):
        self.ui = DebugUI()
        self.settings = {}
        for k,v in self.options.iteritems():
            self.settings[k] = get_vim(k, v, type(v))
        vim_init()

    def start_url(self, url):
        if '?' in url:
            url += '&'
        else:
            url += '?'
        url += 'XDEBUG_SESSION_START=vim_phpdebug'
        self._type = 'php'
        # only linux and mac supported atm
        command = 'xdg-open' if sys.platform.startswith('linux') else 'open'
        try:
            subprocess.Popen((command, url), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            print 'failed to start a browser. aborting debug session'
            return
        return self.start()

    def start_py(self, fname):
        if os.name == 'nt':
            _,PYDBGP,_ = imp.find_module('dbgp')
            PYDBGP = PYDBGP + '/../EGG-INFO/scripts/pydbgp.py'
            subprocess.Popen(('python.exe',PYDBGP, '-d', 'localhost:9000', fname), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            subprocess.Popen(('pydbgp.py', '-d', 'localhost:9000', fname), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self._type = 'python'
        return self.start()

    def start(self):
        ## self.breaks = BreakPointManager()
        self.started = True
        self.bend = DBGP(self.settings, self.ui.windows['log'].write, self._type)
        for key, value in self.handle.bind(self).iteritems():
            if callable(value['function']):
                fn = value['function']
            else:
                tmp = self
                for item in value['function'].split('.'):
                    tmp = getattr(tmp, item)
                fn = tmp
            self.bend.addCommandHandler(key, fn)
        self.bend.addCommandHandler('<stream>', self.ui.windows['output'].add)
        if not self.bend.connect():
            print textwrap.dedent('''\
                Unable to connect to debug server. Things to check:
                    - you refreshed the page during the 5 second
                        period
                    - you have the xdebug extension installed (apt-get
                        install php5-xdebug on ubuntu)
                    - you set the XDEBUG_SESSION_START cookie
                    - "xdebug.remote_enable = 1" is in php.ini (not
                        enabled by default)
                If you have any questions, look at
                    http://tech.blog.box.net/2007/06/20/how-to-debug-php-with-vim-and-xdebug-on-linux/
                ''')
            return False
        self.ui.startup()

        self.bend.get_packets(1)

        self.bend.command('feature_set', 'n', 'max_children', 'v', self.settings['max_children'])
        self.bend.command('feature_set', 'n', 'max_data', 'v', self.settings['max_data'])
        self.bend.command('feature_set', 'n', 'max_depth', 'v', self.settings['max_depth'])
        self.bend.command('stdout', 'c', '1')
        self.bend.command('stderr', 'c', '1')
        for name in ('max_children', 'max_data', 'max_depth'):
            self.bend.command('feature_set', 'n', name, 'v', self.settings[name], suppress=True)

        self.bend.command('step_into')
        self.bend.command('context_get')
        self.bend.command('stack_get')
        self.bend.command('status')

        self.ui.go_srcview()

    def set_status(self, status):
        self.status = status
        # self.party

    ''' setup + register vim commands '''
    cmd = CmdRegistrar()

    cmd('over', help='step over next function call', lead='o')('step_over')
    cmd('into', help='step into next function call', lead='i')('step_into')
    cmd('out', help='step out of current function call', lead='t')('step_out')
    cmd('run', help='continue execution until a breakpoint is reached or the program ends', lead='r')('run')

    @cmd('eval', help='eval some code', plain=True)
    def eval_(self, code):
        self.bend.command('eval', data=code)
        self.bend.command('context_get')

    @cmd('quit', 'stop', 'exit', help='exit the debugger')
    def quit(self):
        self.bend.close()
        self.ui.close()
        vim_quit()

    @cmd('up', help='go up the stack', lead='u')
    def up(self):
        self.ui.stack_up()

    @cmd('down', help='go down the stack', lead='d')
    def down(self):
        self.ui.stack_down()

    @cmd('watch', help='execute watch functions', lead='w')
    def watch(self):
        lines = self.ui.windows['watch'].expressions.buffer
        self.watching = {}
        for i, line in enumerate(lines[1:]):
            if not line.strip():continue
            # self.ui.windows['log'].write('evalling:' + line)
            tid = self.bend.command('eval', data=line, suppress=True)
            self.watching[tid] = i+1
        self.bend.get_packets()

    @cmd('break', help='set a breakpoint', lead='b')
    def break_(self):
        (row, col) = vim.current.window.cursor
        file = os.path.abspath(vim.current.buffer.name)
        if not os.path.exists(file):
            print 'Not in a file'
            return
        bid = self.ui.break_at(file, row)
        if bid == -1:
            tid = self.bend.cid + 1
            self.ui.queue_break(tid, file, row)
            self.bend.command('breakpoint_set', 't', 'line', 'f', 'file://' + file, 'n', row, data='')
        else:
            tid = self.bend.cid + 1
            self.ui.queue_break_remove(tid, bid)
            self.bend.command('breakpoint_remove', 'd', bid)

    @cmd('here', help='continue execution until the cursor (tmp breakpoint)', lead='h')
    def here(self):
        (row, col) = vim.current.window.cursor
        file = os.path.abspath(vim.current.buffer.name)
        if not os.path.exists(file):
            print 'Not in a file'
            return
        tid = self.bend.cid + 1
        # self.ui.queue_break(tid, file, row)
        self.bend.command('breakpoint_set', 't', 'line', 'r', '1', 'f', 'file://' + file, 'n', row, data='')
        self.bend.command('run')

    def commands(self):
        self._commands = self.cmd.bind(self)
        return self._commands

    handle = Registrar()
    @handle('stack_get')
    def _stack_get(self, node):
        line = self.ui.windows['stack'].refresh(node)
        self.ui.set_srcview(line[2], line[3])

    @handle('breakpoint_set')
    def _breakpoint_set(self, node):
        self.ui.set_break(int(node.getAttribute('transaction_id')), node.getAttribute('id'))
        self.ui.go_srcview()

    @handle('breakpoint_remove')
    def _breakpoint_remove(self, node):
        self.ui.clear_break(int(node.getAttribute('transaction_id')))
        self.ui.go_srcview()

    def _status(self, node):
        if node.getAttribute('reason') == 'ok':
            self.set_status(node.getAttribute('status'))

    def _change(self, node):
        if node.getAttribute('reason') == 'ok':
            self.set_status(node.getAttribute('status'))
            if self.status != 'stopping':
                try:
                    self.bend.command('context_get')
                    self.bend.command('stack_get')
                except (EOFError, socket.error):
                    self.disable()
            else:
                self.disable()

    def disable(self):
        print 'Execution has ended; connection closed. type :Dbg quit to exit debugger'
        self.ui.unhighlight()
        for cmd in self._commands.keys():
            if cmd not in ('quit', 'close'):
                self._commands.pop(cmd)

    @handle('<init>')
    def _init(self, node):
        file = node.getAttribute('fileuri')
        self.ui.set_srcview(file, 1)

    handle('status')(_status)
    handle('stdout')(_status)
    handle('stderr')(_status)
    handle('step_into')(_change)
    handle('step_out')(_change)
    handle('step_over')(_change)
    handle('run')(_change)

    def _log(self, node):
        self.ui.windows['log'].write(node.toprettyxml(indent='   '))
        pass # print node

    @handle('eval')
    def _eval(self, node):
        id = int(node.getAttribute('transaction_id'))
        if id in self.watching:
            self.ui.windows['watch'].set_result(self.watching.pop(id), node)
            self.ui.windows['watch'].expressions.focus()

    handle('property_get')(_log)
    handle('property_set')(_log)

    @handle('context_get')
    def _context_get(self, node):
        self.ui.windows['scope'].refresh(node)

    handle('feature_set')(_log)

# vim: et sw=4 sts=4
