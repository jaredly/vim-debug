from window import VimWindow
import errors
import base64

class StackWindow(VimWindow):
    '''Keeps track of the current execution stack'''
    name = 'STACK'
    dtext = '[[Execution Stack - most recent call first]]'
    def __init__(self, name = None):
        VimWindow.__init__(self, name)
        self.at = 0

    def refresh(self, node):
        self.at = 0
        stack = node.getElementsByTagName('stack')
        self.stack = list(map(item.getAttribute, ('level', 'where', 'filename', 'lineno')) for item in stack)
        self.clear()
        tpl = '%-2s %-15s %s:%s' 
        lines = list(tpl % tuple(item) for item in self.stack)
        self.writelines(lines)
        self.highlight(0)
        return self.stack[0]

    def on_create(self):
        self.command('highlight CurStack term=reverse ctermfg=White ctermbg=Red gui=reverse')
        self.highlight(0)

    def highlight(self, num):
        self.command('syntax clear')
        self.command('syntax region CurStack start="^%d " end="$"' % num)

class LogWindow(VimWindow):
    '''I don't actually know what this does...'''
    name = 'LOG'
    dtext = '[[Logs all traffic]]'

    def on_create(self):
        self.command('set nowrap fdm=marker fmr={{{,}}} fdl=0')

class OutputWindow(VimWindow):
    '''Logs the stdout + stderr'''
    name = 'STDOUT_STDERR'
    dtext = '[[Stdout and Stderr are copied here for your convenience]]'

    def on_create(self):
        self.command('set wrap fdm=marker fmr={{{,}}} fdl=0')
        self.command('setlocal wfw')

    def add(self, type, text):
        # TODO: highlight stderr
        self.write(text)

class WatchWindow:
    ''' window for watch expressions '''

    def __init__(self):
        self.expressions = VimWindow('WATCH')
        self.expressions.dtext = '[[Type expressions here]]'
        self.results = VimWindow('RESULTS')
        self.results.dtext = '[[type \w for them to be evaluated]]'

    def create(self, where=None):
        self.expressions.create('leftabove new')
        self.results.create('vertical belowright new')

    def destroy(self):
        self.expressions.destroy()
        self.results.destroy()

def get_text(node):
    data = node.firstChild.data
    if node.getAttribute('encoding') == 'base64':
        return base64.decodestring(data)
    return data

def get_child_text(node, child_tag):
    return get_text(node.getElementsByTagName(child_tag)[0])

class ScopeWindow(VimWindow):
    ''' lists the current scope (context) '''

    name = 'SCOPE'
    dtext = '[[Current scope variables...]]'

    def refresh(self, node):
        self.clear()
        for child in node.getElementsByTagName('property'):
            name = child.getAttribute('fullname')
            type = child.getAttribute('type')
            children = child.getAttribute('children')
            if not name and children == '0':
                text = get_child_text(child, 'value')
                name = get_child_text(child, 'fullname')
            else:
                if not child.firstChild:
                    text = ''
                elif hasattr(child.firstChild, 'data'):
                    text = child.firstChild.data
                else:
                    text = ''
                if child.hasAttribute('encoding') and child.getAttribute('encoding') == 'base64':
                    text = base64.decodestring(text)
            self.write('%-20s = %-10s /* type: %s */' % (name, text, type))

help_text = '''\
[ Function Keys ]                 |                      
  <F1>   resize                   | [ Normal Mode ]      
  <F2>   step into                |   ,e  eval           
  <F3>   step over                |                      
  <F4>   step out                 |                      
  <F5>   run                      | [ Command Mode ]     
  <F6>   quit debugging           | :Bp toggle breakpoint
                                  | :Up stack up         
  <F11>  get all context          | :Dn stack down       
  <F12>  get property at cursor   |                      
'''

# vim: et sw=4 sts=4
