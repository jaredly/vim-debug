# -*- c--oding: ko_KR.UTF-8 -*-
# remote PHP debugger : remote debugger interface to DBGp protocol
#
# Copyright (c) 2010 Jared Forsyth
#
# The MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#
# Authors:
#    Seung Woo Shin <segv <at> sayclub.com>
#    Sam Ghods <sam <at> box.net>
#    Jared Forsyth <jared@jaredforsyth.com>

"""
	debugger.py -- DBGp client: a remote debugger interface to DBGp protocol

    Usage:
        Use with the debugger.vim vim plugin

    This debugger is designed to be used with debugger.vim,
	a vim plugin which provides a full debugging environment
	right inside vim.

	CHECK DEBUGGER.VIM FOR THE FULL DOCUMENTATION.

    Example usage:
        Place inside <source vim directory>/plugin/ along with
		debugger.py.
"""

import os
import sys
import vim
import socket
import base64
import traceback
import xml.dom.minidom

from window import VimWindow

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
                desc = ' : '+error_msg[int(node.getAttribute('code'))]
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

class DebugUI:
    """ DEBUGUI class """
    def __init__(self, minibufexpl = 0):
        """ initialize object """
        self.watchwin = WatchWindow()
        self.stackwin = StackWindow()
        self.tracewin = TraceWindow()
        self.helpwin    = HelpWindow('HELP__WINDOW')
        self.mode         = 0 # normal mode
        self.file         = None
        self.line         = None
        self.winbuf     = {}
        self.cursign    = None
        self.sessfile = "/tmp/debugger_vim_saved_session." + str(os.getpid())
        self.minibufexpl = minibufexpl

    def debug_mode(self):
        """ change mode to debug """
        if self.mode == 1: # is debug mode ?
            return
        self.mode = 1
        if self.minibufexpl == 1:
            vim.command('CMiniBufExplorer')                 # close minibufexplorer if it is open
        # save session
        vim.command('mksession! ' + self.sessfile)
        for i in range(1, len(vim.windows)+1):
            vim.command(str(i)+'wincmd w')
            self.winbuf[i] = vim.eval('bufnr("%")') # save buffer number, mksession does not do job perfectly
                                                                                            # when buffer is not saved at all.

        vim.command('silent topleft new')                                # create srcview window (winnr=1)
        for i in range(2, len(vim.windows)+1):
            vim.command(str(i)+'wincmd w')
            vim.command('hide')
        self.create()
        vim.command('1wincmd w') # goto srcview window(nr=1, top-left)
        self.cursign = '1'

        self.set_highlight()

    def normal_mode(self):
        """ restore mode to normal """
        if self.mode == 0: # is normal mode ?
            return

        vim.command('sign unplace 1')
        vim.command('sign unplace 2')

        # destory all created windows
        self.destroy()

        # restore session
        vim.command('source ' + self.sessfile)
        os.system('rm -f ' + self.sessfile)

        self.set_highlight()


        self.winbuf.clear()
        self.file        = None
        self.line        = None
        self.mode        = 0
        self.cursign = None

        if self.minibufexpl == 1:
            vim.command('MiniBufExplorer')                 # close minibufexplorer if it is open

    def create(self):
        """ create windows """
        self.watchwin.create('vertical belowright new')
        self.helpwin.create('belowright new')
        self.stackwin.create('belowright new')
        self.tracewin.create('belowright new')

    def set_highlight(self):
        """ set vim highlight of debugger sign """
        vim.command("highlight DbgCurrent term=reverse ctermfg=White ctermbg=Red gui=reverse")
        vim.command("highlight DbgBreakPt term=reverse ctermfg=White ctermbg=Green gui=reverse")

    def destroy(self):
        """ destroy windows """
        self.helpwin.destroy()
        self.watchwin.destroy()
        self.stackwin.destroy()
        self.tracewin.destroy()
    def go_srcview(self):
        vim.command('1wincmd w')
    def next_sign(self):
        if self.cursign == '1':
            return '2'
        else:
            return '1'
    def set_srcview(self, file, line):
        """ set srcview windows to file:line and replace current sign """

        if file == self.file and self.line == line:
            return

        nextsign = self.next_sign()

        if file != self.file:
            self.file = file
            self.go_srcview()
            vim.command('silent edit ' + file)

        vim.command('sign place ' + nextsign + ' name=current line='+str(line)+' file='+file)
        vim.command('sign unplace ' + self.cursign)

        vim.command('sign jump ' + nextsign + ' file='+file)
        #vim.command('normal z.')

        self.line        = line
        self.cursign = nextsign

class DbgProtocol:
    """ DBGp Procotol class """
    def __init__(self, port = 9000):
        self.port         = port
        self.sock         = None
        self.isconned = 0
    def isconnected(self):
        return self.isconned
    def accept(self):
        print 'waiting for a new connection on port '+str(self.port)+' for 5 seconds...'
        serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            serv.bind(('', self.port))
            serv.listen(5)
            (self.sock, address) = serv.accept()
        except socket.timeout:
            serv.close()
            self.close()
            # self.stop()
            print 'timeout'
            return

        print 'connection from ', address
        self.isconned = 1
        serv.close()
    def close(self):
        if self.sock != None:
            self.sock.close()
            self.sock = None
        self.isconned = 0
    def recv_length(self):
        #print '* recv len'
        length = ''
        while 1:
            c = self.sock.recv(1)
            if c == '':
                self.close()
                raise EOFError, 'Socket Closed'
            #print '    GET(',c, ':', ord(c), ') : length=', len(c)
            if c == '\0':
                return int(length)
            if c.isdigit():
                length = length + c
    def recv_null(self):
        while 1:
            c = self.sock.recv(1)
            if c == '':
                self.close()
                raise EOFError, 'Socket Closed'
            if c == '\0':
                return
    def recv_body(self, to_recv):
        body = ''
        while to_recv > 0:
            buf = self.sock.recv(to_recv)
            if buf == '':
                self.close()
                raise EOFError, 'Socket Closed'
            to_recv -= len(buf)
            body = body + buf
        return body
    def recv_msg(self):
        length = self.recv_length()
        body     = self.recv_body(length)
        self.recv_null()
        return body
    def send_msg(self, cmd):
        self.sock.send(cmd + '\0')

class BreakPoint:
    """ Breakpoint class """
    def __init__(self):
        """ initalize """
        self.breakpt    = {}
        self.revmap     = {}
        self.startbno = 10000
        self.maxbno     = self.startbno
    def clear(self):
        """ clear of breakpoint number """
        self.breakpt.clear()
        self.revmap.clear()
        self.maxbno = self.startbno
    def add(self, file, line, exp = ''):
        """ add break point at file:line """
        self.maxbno = self.maxbno + 1
        self.breakpt[self.maxbno] = { 'file':file, 'line':line, 'exp':exp, 'id':None }
        return self.maxbno
    def remove(self, bno):
        """ remove break point numbered with bno """
        del self.breakpt[bno]
    def find(self, file, line):
        """ find break point and return bno(breakpoint number) """
        for bno in self.breakpt.keys():
            if self.breakpt[bno]['file'] == file and self.breakpt[bno]['line'] == line:
                return bno
        return None
    def getfile(self, bno):
        """ get file name of breakpoint numbered with bno """
        return self.breakpt[bno]['file']
    def getline(self, bno):
        """ get line number of breakpoint numbered with bno """
        return self.breakpt[bno]['line']
    def getexp(self, bno):
        """ get expression of breakpoint numbered with bno """
        return self.breakpt[bno]['exp']
    def getid(self, bno):
        """ get Debug Server's breakpoint numbered with bno """
        return self.breakpt[bno]['id']
    def setid(self, bno, id):
        """ get Debug Server's breakpoint numbered with bno """
        self.breakpt[bno]['id'] = id
    def list(self):
        """ return list of breakpoint number """
        return self.breakpt.keys()

class Debugger:
    """ Main Debugger class """


    #################################################################################################################
    # Internal functions
    #
    def __init__(self, port = 9000, max_children = '32', max_data = '1024', max_depth = '1', minibufexpl = '0', debug = 0):
        """ initialize Debugger """
        socket.setdefaulttimeout(5)
        self.port             = port
        self.debug            = debug

        self.current        = None
        self.file             = None
        self.lasterror    = None
        self.msgid            = 0
        self.running        = 0
        self.stacks         = []
        self.curstack     = 0
        self.laststack    = 0
        self.bptsetlst    = {} 

        self.status                = None
        self.max_children    = max_children
        self.max_data            = max_data
        self.max_depth         = max_depth

        self.protocol     = DbgProtocol(self.port)

        self.ui                 = DebugUI(minibufexpl)
        self.breakpt        = BreakPoint()

        vim.command('sign unplace *')

    def clear(self):
        self.current     = None
        self.lasterror = None
        self.msgid         = 0
        self.running     = 0
        self.stacks        = []
        self.curstack    = 0
        self.laststack = 0
        self.bptsetlst = {} 

        self.protocol.close()

    def send(self, msg):
        """ send message """
        self.protocol.send_msg(msg)
        # log message
        if self.debug:
            self.ui.tracewin.write(str(self.msgid) + ' : send =====> ' + msg)
    def recv(self, count=10000):
        """ receive message until response is last transaction id or received count's message """
        while count>0:
            count = count - 1
            # recv message and convert to XML object
            txt = self.protocol.recv_msg()
            res = xml.dom.minidom.parseString(txt)
            # log messages {{{
            if self.debug:
                self.ui.tracewin.write( str(self.msgid) + ' : recv <===== {{{     ' + txt)
                self.ui.tracewin.write('}}}')
            # handle message
            self.handle_msg(res)
            # exit, if response's transaction id == last transaction id
            try:
                if int(res.firstChild.getAttribute('transaction_id')) == int(self.msgid):
                    return
            except:
                pass
    def send_command(self, cmd, arg1 = '', arg2 = ''):
        """ send command (do not receive response) """
        self.msgid = self.msgid + 1
        line = cmd + ' -i ' + str(self.msgid)
        if arg1 != '':
            line = line + ' ' + arg1
        if arg2 != '':
            line = line + ' -- ' + base64.encodestring(arg2)[0:-1]
        self.send(line)
        return self.msgid
    #
    #
    #################################################################################################################

    #################################################################################################################
    # Internal message handlers
    #
    def handle_msg(self, res):
        """ call appropraite message handler member function, handle_XXX() """
        fc = res.firstChild
        try:
            handler = getattr(self, 'handle_' + fc.tagName)
            handler(res)
        except AttributeError:
            print 'Debugger.handle_'+fc.tagName+'() not found, please see the LOG___WINDOW'
        self.ui.go_srcview()
    def handle_response(self, res):
        """ call appropraite response message handler member function, handle_response_XXX() """
        if res.firstChild.hasAttribute('reason') and res.firstChild.getAttribute('reason') == 'error':
            self.handle_response_error(res)
            return
        errors    = res.getElementsByTagName('error')
        if len(errors)>0:
            self.handle_response_error(res)
            return

        command = res.firstChild.getAttribute('command')
        try:
            handler = getattr(self, 'handle_response_' + command)
        except AttributeError:
            print 'Debugger.handle_response_'+command+'() not found, please see the LOG___WINDOW'
            return
        handler(res)
        return

    def handle_init(self, res):
        """handle <init> tag
        <init appid="7035" fileuri="file:///home/segv/htdocs/index.php" language="PHP" protocol_version="1.0">
            <engine version="2.0.0beta1">
                Xdebug
            </engine>
            <author>
                Derick Rethans
            </author>
            <url>
                http://xdebug.org
            </url>
            <copyright>
                Copyright (c) 2002-2004 by Derick Rethans
            </copyright>
        </init>"""
     
        file = res.firstChild.getAttribute('fileuri')[7:]
        self.ui.set_srcview(file, 1)

    def handle_response_error(self, res):
        """ handle <error> tag """
        self.ui.tracewin.write_xml_childs(res)
#        print 'ERROR!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
#        print res.toprettyxml()
#        print '------------------------------------'
#
#        errors    = res.getElementsByTagName('error')
#        #print 'list: ', len(errors), errors
#        if len(errors)>0:
#            return
#        for error in errors:
#            code = error.getAttribute('code')
#            print 'error code=', code
#        print res

    def handle_response_stack_get(self, res):
        """handle <response command=stack_get> tag
        <response command="stack_get" transaction_id="1 ">
            <stack filename="file:///home/segv/htdocs/index.php" level="0" lineno="41" where="{main}"/>
        </response>"""

        stacks = res.getElementsByTagName('stack')
        if len(stacks)>0:
            self.curstack    = 0
            self.laststack = len(stacks) - 1

            self.stacks        = []
            for s in stacks:
                self.stacks.append( {'file':    s.getAttribute('filename')[7:], \
                                                         'line':    int(s.getAttribute('lineno')),    \
                                                         'where': s.getAttribute('where'),                \
                                                         'level': int(s.getAttribute('level'))
                                                         } )

            self.ui.stackwin.clean()
            self.ui.stackwin.highlight_stack(self.curstack)

            self.ui.stackwin.write_xml_childs(res.firstChild) #str(res.toprettyxml()))
            self.ui.set_srcview( self.stacks[self.curstack]['file'], self.stacks[self.curstack]['line'] )


    def handle_response_step_out(self, res):
        """handle <response command=step_out> tag
        <response command="step_out" reason="ok" status="break" transaction_id="1 "/>"""
        if res.firstChild.hasAttribute('reason') and res.firstChild.getAttribute('reason') == 'ok':
            if res.firstChild.hasAttribute('status'):
                self.status = res.firstChild.getAttribute('status')
            return
        else:
            print res.toprettyxml()
    def handle_response_step_over(self, res):
        """handle <response command=step_over> tag
        <response command="step_over" reason="ok" status="break" transaction_id="1 "/>"""
        if res.firstChild.hasAttribute('reason') and res.firstChild.getAttribute('reason') == 'ok':
            if res.firstChild.hasAttribute('status'):
                self.status = res.firstChild.getAttribute('status')
            return
        else:
            print res.toprettyxml()
    def handle_response_step_into(self, res):
        """handle <response command=step_into> tag
        <response command="step_into" reason="ok" status="break" transaction_id="1 "/>"""
        if res.firstChild.hasAttribute('reason') and res.firstChild.getAttribute('reason') == 'ok':
            if res.firstChild.hasAttribute('status'):
                self.status = res.firstChild.getAttribute('status')
            return
        else:
            print res.toprettyxml()
    def handle_response_run(self, res):
        """handle <response command=run> tag
        <response command="step_over" reason="ok" status="break" transaction_id="1 "/>"""
        if res.firstChild.hasAttribute('status'):
            self.status = res.firstChild.getAttribute('status')
            return
    def handle_response_breakpoint_set(self, res):
        """handle <response command=breakpoint_set> tag
        <responsponse command="breakpoint_set" id="110180001" transaction_id="1"/>"""
        if res.firstChild.hasAttribute('id'):
            tid = int(res.firstChild.getAttribute('transaction_id'))
            bno = self.bptsetlst[tid]
            del self.bptsetlst[tid]
            self.breakpt.setid(bno, str(res.firstChild.getAttribute('id')))
            #try:
            #except:
            #    print "can't find bptsetlst tid=", tid
            #    pass
    def handle_response_eval(self, res):
        """handle <response command=eval> tag """
        self.ui.watchwin.write_xml_childs(res)
    def handle_response_property_get(self, res):
        """handle <response command=property_get> tag """
        self.ui.watchwin.write_xml_childs(res)
    def handle_response_context_get(self, res):
        """handle <response command=context_get> tag """
        self.ui.watchwin.write_xml_childs(res)
    def handle_response_feature_set(self, res):
        """handle <response command=feature_set> tag """
        self.ui.watchwin.write_xml_childs(res)
    def handle_response_default(self, res):
        """handle <response command=context_get> tag """
        print res.toprettyxml()
    #
    #
    #################################################################################################################

    #################################################################################################################
    # debugger command functions
    #
    #     usage:
    #
    #     dbg = Debugger()                    # create Debugger Object
    #     dbg.run()                                 # run() method initialize windows, debugger connection and send breakpoints, ...
    #     dbg.run()                                 # run() method sends 'run -i ...' message
    #     dbg.command('step_into')    # sends 'step_into' message
    #     dbg.stop()                                # stop debugger
    #

    def command(self, cmd, arg1 = '', arg2 = ''):
        """ general command sender (receive response too) """
        if self.running == 0:
            print "Not connected\n"
            return
        msgid = self.send_command(cmd, arg1, arg2)
        self.recv()
        return msgid
    def run(self):
        """ start debugger or continue """
        if self.protocol.isconnected():
            self.command('run')
            if self.status != 'stopped':
                self.command('stack_get')
        else:
            self.clear()
            self.protocol.accept()
            self.ui.debug_mode()
            self.running = 1

            self.recv(1)

            # set max data to get with eval results
            self.command('feature_set', '-n max_children -v ' + self.max_children)
            self.command('feature_set', '-n max_data -v ' + self.max_data)
            self.command('feature_set', '-n max_depth -v ' + self.max_depth)

            self.command('step_into')

            flag = 0
            for bno in self.breakpt.list():
                msgid = self.send_command('breakpoint_set', \
                                                                    '-t line -f ' + self.breakpt.getfile(bno) + ' -n ' + str(self.breakpt.getline(bno)) + ' -s enabled', \
                                                                    self.breakpt.getexp(bno))
                self.bptsetlst[msgid] = bno
                flag = 1
            if flag:
                self.recv()

            self.ui.go_srcview()

    def quit(self):
        self.ui.normal_mode()
        self.clear()
        #vim.command('MiniBufExplorer')

    def stop(self):
        self.clear()

    def up(self):
        if self.curstack > 0:
            self.curstack -= 1
            self.ui.stackwin.highlight_stack(self.curstack)
            self.ui.set_srcview(self.stacks[self.curstack]['file'], self.stacks[self.curstack]['line'])

    def down(self):
        if self.curstack < self.laststack:
            self.curstack += 1
            self.ui.stackwin.highlight_stack(self.curstack)
            self.ui.set_srcview(self.stacks[self.curstack]['file'], self.stacks[self.curstack]['line'])

    def mark(self, exp = ''):
        (row, rol) = vim.current.window.cursor
        file             = vim.current.buffer.name

        bno = self.breakpt.find(file, row)
        if bno != None:
            id = self.breakpt.getid(bno)
            self.breakpt.remove(bno)
            vim.command('sign unplace ' + str(bno))
            if self.protocol.isconnected():
                self.send_command('breakpoint_remove', '-d ' + str(id))
                self.recv()
        else:
            bno = self.breakpt.add(file, row, exp)
            vim.command('sign place ' + str(bno) + ' name=breakpt line=' + str(row) + ' file=' + file)
            if self.protocol.isconnected():
                msgid = self.send_command('breakpoint_set', \
                                                                    '-t line -f ' + self.breakpt.getfile(bno) + ' -n ' + str(self.breakpt.getline(bno)), \
                                                                    self.breakpt.getexp(bno))
                self.bptsetlst[msgid] = bno
                self.recv()

    def watch_input(self, mode, arg = ''):
        self.ui.watchwin.input(mode, arg)

    def property_get(self, name = ''):
        if name == '':
            name = vim.eval('expand("<cword>")')
        self.ui.watchwin.write('--> property_get: '+name)
        self.command('property_get', '-n '+name)
        
    def watch_execute(self):
        """ execute command in watch window """
        (cmd, expr) = self.ui.watchwin.get_command()
        if cmd == 'exec':
            self.command('exec', '', expr)
            print cmd, '--', expr
        elif cmd == 'eval':
            self.command('eval', '', expr)
            print cmd, '--', expr
        elif cmd == 'property_get':
            self.command('property_get', '-d %d -n %s' % (self.curstack,    expr))
            print cmd, '-n ', expr
        elif cmd == 'context_get':
            self.command('context_get', ('-d %d' % self.curstack))
            print cmd
        else:
            print "no commands", cmd, expr


    #
    #
    #################################################################################################################

