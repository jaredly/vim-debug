from window import VimWindow
import errors

class StackWindow(VimWindow):
    '''Keeps track of the current execution stack'''
    def __init__(self, name = 'STACK_WINDOW'):
        VimWindow.__init__(self, name)
    def xml_on_element(self, node):
        if node.nodeName != 'stack':
            return VimWindow.xml_on_element(self, node)
        else:
            if node.getAttribute('where') != '{main}':
                fmark = '()'
            else:
                fmark = ''
            return str('%-2s %-15s %s:%s' % (            \
                    node.getAttribute('level'),                \
                    node.getAttribute('where')+fmark,    \
                    node.getAttribute('filename')[7:], \
                    node.getAttribute('lineno')))
    def on_create(self):
        self.command('highlight CurStack term=reverse ctermfg=White ctermbg=Red gui=reverse')
        self.highlight_stack(0)
    def highlight_stack(self, no):
        self.command('syntax clear')
        self.command('syntax region CurStack start="^' +str(no)+ ' " end="$"')

class LogWindow(VimWindow):
    '''I don't actually know what this does...'''
    def __init__(self, name = 'LOG___WINDOW'):
        VimWindow.__init__(self, name)
    def on_create(self):
        self.command('set nowrap fdm=marker fmr={{{,}}} fdl=0')
        self.write('asdfasdf')

class TraceWindow(VimWindow):
    '''Logs all communication with the debug server'''
    def __init__(self, name = 'TRACE_WINDOW'):
        VimWindow.__init__(self, name)
    def xml_on_element(self, node):
        if node.nodeName != 'error':
            return VimWindow.xml_on_element(self, node)
        else:
            desc = ''
            if node.hasAttribute('code'):
                desc = ' : '+errors.error_msg[int(node.getAttribute('code'))]
            return VimWindow.xml_on_element(self, node) + desc
    def on_create(self):
        self.command('set nowrap fdm=marker fmr={{{,}}} fdl=0')

class WatchWindow(VimWindow):
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

class HelpWindow(VimWindow):
    '''Displays the help page'''
    def __init__(self, name = 'HELP__WINDOW'):
        VimWindow.__init__(self, name)
    def on_create(self):
        ## wouldn't this be better as a file?
        self.write(                                                                                                                    \
        '[ Function Keys ]                 |                       \n'
        '  <F1>   resize                   | [ Normal Mode ]       \n'
        '  <F2>   step into                |   ,e  eval            \n'
        '  <F3>   step over                |                       \n'
        '  <F4>   step out                 |                       \n'
        '  <F5>   run                      | [ Command Mode ]      \n'
        '  <F6>   quit debugging           | :Bp toggle breakpoint \n'
        '                                  | :Up stack up          \n'
        '  <F11>  get all context          | :Dn stack down        \n'
        '  <F12>  get property at cursor   |                       \n'
        '\n')
        self.command('1')

# vim: et sw=4 sts=4
