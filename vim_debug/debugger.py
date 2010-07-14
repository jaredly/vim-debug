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

import os
import sys
import vim
import base64
import textwrap
import xml.dom.minidom

from ui import DebugUI
from protocol import DbgProtocol

class BreakPointManager:
    """ Breakpoint manager class """
    def __init__(self):
        """ initalize """
        self.breakpt = {}
        self.revmap = {}
        self.startbno = 10000
        self.maxbno = self.startbno
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
        self.debug = debug

        self.current = None
        self.file = None
        self.lasterror = None
        self.msgid = 0
        self.running = 0
        self.stacks = []
        self.curstack = 0
        self.laststack = 0
        self.bptsetlst = {} 

        self.status = None
        self.max_children = max_children
        self.max_data = max_data
        self.max_depth = max_depth

        self.protocol = DbgProtocol(port)

        self.ui = DebugUI(minibufexpl)
        self.breakpt = BreakPointManager()

        vim.command('sign unplace *')

    def clear(self):
        self.current = None
        self.lasterror = None
        self.msgid = 0
        self.running = 0
        self.stacks = []
        self.curstack = 0
        self.laststack = 0
        self.bptsetlst = {} 

        self.protocol.close()

    def send(self, msg):
        """ send message """
        self.protocol.send_msg(msg)
        # log message
        if self.debug:
            self.ui.windows['trace'].write(str(self.msgid) + ' : send =====> ' + msg)
    def recv(self, count=10000):
        """ receive message until response is last transaction id or received count's message """
        while count>0:
            count = count - 1
            # recv message and convert to XML object
            txt = self.protocol.recv_msg()
            res = xml.dom.minidom.parseString(txt)
            # log messages {{{
            if self.debug:
                self.ui.windows['trace'].write( str(self.msgid) + ' : recv <===== {{{     ' + txt)
                self.ui.windows['trace'].write('}}}')
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
        errors = res.getElementsByTagName('error')
        if len(errors)>0:
            self.handle_response_error(res)
            return

        command = res.firstChild.getAttribute('command')
        try:
            handler = getattr(self, 'handle_response_' + command)
        except AttributeError:
            print res.toprettyxml()
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
     
        file = res.firstChild.getAttribute('fileuri')
        self.ui.set_srcview(file, 1)

    def handle_response_error(self, res):
        """ handle <error> tag """
        self.ui.windows['trace'].write_xml_childs(res)

    def handle_response_stack_get(self, res):
        """handle <response command=stack_get> tag
        <response command="stack_get" transaction_id="1 ">
            <stack filename="file:///home/segv/htdocs/index.php" level="0" lineno="41" where="{main}"/>
        </response>"""

        stacks = res.getElementsByTagName('stack')
        if len(stacks)>0:
            self.curstack = 0
            self.laststack = len(stacks) - 1

            self.stacks = []
            for s in stacks:
                self.stacks.append( {'file': s.getAttribute('filename'),
                                     'line': int(s.getAttribute('lineno')),
                                     'where': s.getAttribute('where'),
                                     'level': int(s.getAttribute('level'))
                                     } )

            self.ui.windows['stack'].clean()
            self.ui.windows['stack'].highlight_stack(self.curstack)

            self.ui.windows['stack'].write_xml_childs(res.firstChild) #str(res.toprettyxml()))
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
        self.ui.windows['watch'].write_xml_childs(res)
    def handle_response_property_get(self, res):
        """handle <response command=property_get> tag """
        self.ui.windows['watch'].write_xml_childs(res)
    def handle_response_context_get(self, res):
        """handle <response command=context_get> tag """
        self.ui.windows['watch'].write_xml_childs(res)
    def handle_response_feature_set(self, res):
        """handle <response command=feature_set> tag """
        self.ui.windows['watch'].write_xml_childs(res)
    def handle_response_status(self, res):
        self.status = res.firstChild.getAttribute('status')
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
            self.update()
        else:
            self.clear()
            if not self.protocol.accept():
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
                msgid = self.send_command('breakpoint_set',
                 '-t line -f ' + self.breakpt.getfile(bno) + ' -n ' + str(self.breakpt.getline(bno)) + ' -s enabled',
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
            self.ui.windows['stack'].highlight_stack(self.curstack)
            self.ui.set_srcview(self.stacks[self.curstack]['file'], self.stacks[self.curstack]['line'])

    def down(self):
        if self.curstack < self.laststack:
            self.curstack += 1
            self.ui.windows['stack'].highlight_stack(self.curstack)
            self.ui.set_srcview(self.stacks[self.curstack]['file'], self.stacks[self.curstack]['line'])

    def mark(self, exp = ''):
        (row, rol) = vim.current.window.cursor
        file = vim.current.buffer.name

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
        self.ui.windows['watch'].input(mode, arg)

    def property_get(self, name = ''):
        if name == '':
            name = vim.eval('expand("<cword>")')
        self.ui.windows['watch'].write('--> property_get: '+name)
        self.command('property_get', '-n '+name)
        
    def watch_execute(self):
        """ execute command in watch window """
        (cmd, expr) = self.ui.windows['watch'].get_command()
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

    def update(self):
        self.command('status')
        if self.status == 'break':
            self.command('stack_get')
        elif self.status == 'stopping':
            print 'Program has finished running. (exiting)'
            vim.command(':!')
            self.quit()
        elif self.status == 'starting':
            print 'Execution hasn\'t started yet...'
        elif self.status == 'running':
            print 'Code is running right now...'
        elif self.status == 'stopped':
            print 'We\'ve been disconnected! (exiting)'
            vim.command(':!')
            self.quit()

    #
    #
    #################################################################################################################

