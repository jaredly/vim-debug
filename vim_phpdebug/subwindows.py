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
    dtext = '[[Stdout and Stderr are copied here for your convenience]]\n'

    def on_create(self):
        self.command('set wrap fdm=marker fmr={{{,}}} fdl=0')
        self.command('setlocal wfw')
        self.last = 'stdout'

    def add(self, type, text):
        # TODO: highlight stderr
        if type != self.last:
            self.last = type
            if type == 'stderr':
                self.write('[[STDERR]]')
            else:
                self.write('[[STDOUT]]')
        lines = text.split('\n')
        self.buffer[-1] += lines[0]
        for line in lines[1:]:
            self.buffer.append(line)
        self.command('normal G')

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

    def set_result(self, line, node):
        l = len(self.results.buffer)
        for a in range(len(self.results.buffer)-1, line):
            self.results.buffer.append('')
        errors = node.getElementsByTagName('error')
        if len(errors):
            res = 'ERROR: ' + str(get_child_text(errors[0], 'message'))
        else:
            prop = node.getElementsByTagName('property')[0]
            res = str(get_text(prop))
            if not res:
                res = str(get_child_text(prop, 'value'))
        self.results.buffer[line] = res

def get_text(node):
    if not hasattr(node.firstChild, 'data'):
        return ''
    data = node.firstChild.data
    if node.getAttribute('encoding') == 'base64':
        return base64.decodestring(data)
    return data

def get_child_text(node, child_tag):
    tags = node.getElementsByTagName(child_tag)
    if not tags:
        return ''
    return get_text(tags[0])

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
            if not name:
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
