import subprocess
import textwrap
import gconf
import vim

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
        lead = kwds.pop('lead', '')
        if lead:
            vim.command('map <Leader>%s :Dbg %s<cr>' % (lead, args[0]))
        dct = {'function':func, 'options':kwds}
        for name in args:
            self.reg[name] = dct

class Debugger:
    ''' This is the main debugger class... '''
    options = {'port':9000, 'max_children':32, 'max_data':'1024', 'minbufexpl':0, 'max_depth':1}
    def __init__(self):
        self.started = False
        pass
    
    def init_vim(self):
        self.ui = DebugUI()
        self.settings = {}
        for k,v in self.options.iteritems():
            self.settings[k] = get_vim(k, v, type(v))
        vim_init()

    def start_url(self, url):
        print 'starting'
        if '?' in url:
            url += '&'
        else:
            url += '?'
        url += 'XDEBUG_SESSION_START=vim_phpdebug'
        try:
            import gconf
            browser = gconf.Client().get_string('/desktop/gnome/applications/browser/exec')
            if browser is None:
                raise ValueError
            subprocess.Popen((browser, url))
        except ImportError: # don't have gconf
            print 'gconf not found...',
        except ValueError:
            print 'no default browser found...',
        except OSError:
            print 'default browser failed...',
        else:
            return self.start()
        # TODO: allow custom browsers
        print 'trying chrome, firefox'
        try:
            subprocess.Popen(('google-chrome', url))
        except OSError:
            try:
                subprocess.Popen(('firefox', url))
            except OSError:
                print 'neither chrome nor firefox were found. failed to start debug session.'
                return
        return self.start()

    def start(self):
        ## self.breaks = BreakPointManager()
        self.started = True
        self.bend = DBGP(self.settings, self.ui.windows['log'].write)
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

    cmd('o', 'over', help='step over next function call', lead='o')('step_over')
    cmd('i', 'into', help='step into next function call', lead='i')('step_into')
    cmd('out', help='step out of current function call', lead='t')('step_out')
    
    @cmd('e', 'eval', help='eval some code', plain=True)
    def eval_(self, code):
        self.bend.command('eval', data=code)
        self.bend.command('context_get')

    @cmd('quit', 'stop', help='exit the debugger')
    def quit(self):
        self.bend.close()
        self.ui.close()
        vim_quit()

    @cmd('u', 'up', help='go up the stack', lead='u')
    def up(self):
        self.ui.stack_up()

    @cmd('d', 'down', help='go down the stack', lead='d')
    def down(self):
        self.ui.stack_down()
    
    def commands(self):
        return self.cmd.bind(self)

    handle = Registrar()
    @handle('stack_get')
    def _stack_get(self, node):
        line = self.ui.windows['stack'].refresh(node)
        self.ui.set_srcview(line[2][7:], line[3])

    def _status(self, node):
        if node.getAttribute('reason') == 'ok':
            self.set_status(node.getAttribute('status'))

    def _change(self, node):
        if node.getAttribute('reason') == 'ok':
            self.set_status(node.getAttribute('status'))
            self.bend.command('context_get')
            self.bend.command('stack_get')

    @handle('<init>')
    def _init(self, node):
        file = node.getAttribute('fileuri')[7:]
        self.ui.set_srcview(file, 1)

    handle('status')(_status)
    handle('stdout')(_status)
    handle('stderr')(_status)
    handle('step_into')(_change)
    handle('step_out')(_change)
    handle('step_over')(_change)
    handle('run')(_status)

    @handle('breakpoint_set')
    def _breakpoint_set(self, node):
        tid = node.getAttribute('id')
        self.ui.breaks.set_pending(tid)

    def _log(self, node):
        self.ui.windows['log'].write(node.toprettyxml(indent='   '))
        pass # print node

    handle('eval')(_log)
    handle('property_get')(_log)
    handle('property_set')(_log)

    @handle('context_get')
    def _context_get(self, node):
        self.ui.windows['scope'].refresh(node)

    handle('feature_set')(_log)

# vim: et sw=4 sts=4
