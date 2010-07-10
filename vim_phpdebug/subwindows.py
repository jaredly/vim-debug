from window import VimWindow
import errors
import base64

class StackWindow(VimWindow):
    '''Keeps track of the current execution stack'''
    name = 'STACK_WINDOW'
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
    name = 'LOG_WINDOW'

    def on_create(self):
        self.command('set nowrap fdm=marker fmr={{{,}}} fdl=0')
        self.write('logging...?')

class OutputWindow(VimWindow):
    '''Logs the stdout + stderr'''
    name = 'OUTPUT_WINDOW'

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
        self.results = VimWindow('RESULTS')

    def create(self, where=None):
        self.expressions.create('leftabove new')
        self.results.create('vertical belowright new')

    def destroy(self):
        self.expressions.destroy()
        self.results.destroy()

class ScopeWindow(VimWindow):
    ''' lists the current scope (context) '''

    name = 'SCOPE_WINDOW'

    def refresh(self, node):
        self.clear()
        for child in node.getElementsByTagName('property'):
            name = child.getAttribute('fullname')
            if not child.firstChild:
                text = ''
            else:
                text = child.firstChild.data
            type = child.getAttribute('type')
            if child.hasAttribute('encoding') and child.getAttribute('encoding') == 'base64':
                text = base64.decodestring(text)
            self.write('%-10s = %s /* type: %s */' % (name, text, type))

class WatchWindow_(VimWindow):
    '''apparently watches stuff...shows eval results, context values...'''
    def __init__(self, name = 'WATCH_WINDOW'):
        VimWindow.__init__(self, name)
    def fixup_single(self, line, node, level):
        return ''.ljust(level*1) + line + '\n'
    def fixup_childs(self, line, node, level):
        global z
        if len(node.childNodes)            == 1                            and \
             (node.firstChild.nodeType == node.TEXT_NODE    or \
             node.firstChild.nodeType    == node.CDATA_SECTION_NODE):
            line = str(''.ljust(level*1) + line)
            encoding = node.getAttribute('encoding')
            if encoding == 'base64':
                line += "'" + base64.decodestring(str(node.firstChild.data)) + "';\n"
            elif encoding == '':
                line += str(node.firstChild.data) + ';\n'
            else:
                line += '(e:'+encoding+') ' + str(node.firstChild.data) + ';\n'
        else:
            if level == 0:
                line = ''.ljust(level*1) + str(line) + ';' + '\n'
                line += self.xml_stringfy_childs(node, level+1)
                line += '/*}}}1*/\n'
            else:
                line = (''.ljust(level*1) + str(line) + ';').ljust(self.width-20) + ''.ljust(level*1) + '/*{{{' + str(level+1) + '*/' + '\n'
                line += str(self.xml_stringfy_childs(node, level+1))
                line += (''.ljust(level*1) + ''.ljust(level*1)).ljust(self.width-20) + ''.ljust(level*1) + '/*}}}' + str(level+1) + '*/\n'
        return line
    def xml_on_element(self, node):
        if node.nodeName == 'property':
            self.type = node.getAttribute('type')

            name            = node.getAttribute('name')
            fullname    = node.getAttribute('fullname')
            if name == '':
                name = 'EVAL_RESULT'
            if fullname == '':
                fullname = 'EVAL_RESULT'

            if self.type == 'uninitialized':
                return str(('%-20s' % name) + " = /* uninitialized */'';")
            else:
                return str('%-20s' % fullname) + ' = (' + self.type + ') '
        elif node.nodeName == 'response':
            return "$command = '" + node.getAttribute('command') + "'"
        else:
            return VimWindow.xml_on_element(self, node)

    def xml_on_text(self, node):
        if self.type == 'string':
            return "'" + str(node.data) + "'"
        else:
            return str(node.data)
    def xml_on_cdata_section(self, node):
        if self.type == 'string':
            return "'" + str(node.data) + "'"
        else:
            return str(node.data)
    def on_create(self):
        self.write('<?')
        self.command('inoremap <buffer> <cr> <esc>:python debugger.watch_execute()<cr>')
        self.command('set noai nocin')
        self.command('set nowrap fdm=marker fmr={{{,}}} ft=php fdl=1')
    def input(self, mode, arg = ''):
        line = self.buffer[-1]
        if line[:len(mode)+1] == '/*{{{1*/ => '+mode+':':
            self.buffer[-1] = line + arg
        else:
            self.buffer.append('/*{{{1*/ => '+mode+': '+arg)
        self.command('normal G')

    def get_command(self):
        line = self.buffer[-1]
        if line[0:17] == '/*{{{1*/ => exec:':
            print "exec does not supported by xdebug now."
            return ('none', '')
            #return ('exec', line[17:].strip(' '))
        elif line[0:17] == '/*{{{1*/ => eval:':
            return ('eval', line[17:].strip(' '))
        elif line[0:25] == '/*{{{1*/ => property_get:':
            return ('property_get', line[25:].strip(' '))
        elif line[0:24] == '/*{{{1*/ => context_get:':
            return ('context_get', line[24:].strip(' '))
        else:
            return ('none', '')

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
