import os
import vim

from subwindows import WatchWindow, StackWindow, ScopeWindow, OutputWindow, LogWindow

class DebugUI:
    """ DEBUGUI class """
    def __init__(self, minibufexpl = 0):
        """ initialize object """
        self.windows = {
            'watch':WatchWindow(),
            'stack':StackWindow(),
            'scope':ScopeWindow(),
            'output':OutputWindow(),
            'log':LogWindow(),
            # 'status':StatusWindow()
        }
        self.mode     = 0 # normal mode
        self.file     = None
        self.line     = None
        self.winbuf   = {}
        self.breaks   = {}
        self.waiting  = {}
        self.toremove = {}
        self.cursign  = None
        self.sessfile = "/tmp/debugger_vim_saved_session." + str(os.getpid())
        self.minibufexpl = minibufexpl

    def startup(self):
        """ change mode to debug """
        if self.mode == 1: # is debug mode ?
            return
        self.mode = 1
        if self.minibufexpl == 1:
            vim.command('CMiniBufExplorer')         # close minibufexplorer if it is open
        # save session
        vim.command('mksession! ' + self.sessfile)
        for i in range(1, len(vim.windows)+1):
            vim.command(str(i)+'wincmd w')
            self.winbuf[i] = vim.eval('bufnr("%")') # save buffer number, mksession does not do job perfectly
                                                    # when buffer is not saved at all.

        vim.command('silent topleft new')           # create srcview window (winnr=1)
        for i in range(2, len(vim.windows)+1):
            vim.command(str(i)+'wincmd w')
            vim.command('hide')
        self.create()
        vim.command('1wincmd w') # goto srcview window(nr=1, top-left)
        self.cursign = '1'

        self.set_highlight()

    def close(self):
        """ restore mode to normal """
        if self.mode == 0: # is normal mode ?
            return

        vim.command('sign unplace 1')
        vim.command('sign unplace 2')
        for bid in self.breaks.keys():
            file, line, tid = self.breaks.pop(bid)
            vim.command('sign unplace %d file=%s' % (tid, file))

        # destory all created windows
        self.destroy()

        # restore session
        vim.command('source ' + self.sessfile)
        os.system('rm -f ' + self.sessfile)

        self.set_highlight()

        self.winbuf.clear()
        self.file = None
        self.line = None
        self.mode = 0
        self.cursign = None

        if self.minibufexpl == 1:
            vim.command('MiniBufExplorer')                 # close minibufexplorer if it is open

    def create(self):
        """ create windows """
        self.windows['output'].create('vertical belowright new')
        self.windows['scope'].create('aboveleft new')
        self.windows['log'].create('aboveleft new')
        self.windows['stack'].create('aboveleft new')
        self.windows['watch'].create('aboveleft new')
        width = self.windows['output'].width + self.windows['scope'].width
        self.windows['output'].command('vertical res %d' % (width/2))
        self.windows['watch'].results.command('vertical res %d' % (width/4))

    def set_highlight(self):
        """ set vim highlight of debugger sign """
        vim.command("highlight DbgCurrent term=reverse ctermfg=White ctermbg=Red gui=reverse")
        vim.command("highlight DbgBreakPt term=reverse ctermfg=White ctermbg=Green gui=reverse")

    def unhighlight(self):
        self.windows['stack'].clear()
        self.windows['stack'].write('\n\n!!!!!---- Debugging has ended. Type `:dbg quit` to exit ----!!!!!\n\n')
        self.windows['stack'].command('syntax clear')
        self.windows['stack'].command('syntax region CurStack start="^!!!!!---- " end="$"')
        self.go_srcview()
        vim.command('sign unplace ' + self.cursign)

    def stack_up(self):
        stack = self.windows['stack']
        if stack.at > 0:
            stack.at -= 1
            stack.highlight(stack.at)
            item = stack.stack[stack.at]
            self.set_srcview(item[2], item[3])

    def stack_down(self):
        stack = self.windows['stack']
        if stack.at < len(stack.stack)-1:
            stack.at += 1
            stack.highlight(stack.at)
            item = stack.stack[stack.at]
            self.set_srcview(item[2], item[3])

    def queue_break(self, tid, file, line):
        self.waiting[tid] = file, line

    def queue_break_remove(self, tid, bid):
        self.toremove[tid] = bid

    def set_break(self, tid, bid):
        if tid in self.waiting:
            file, line = self.waiting[tid]
            self.breaks[bid] = file, line, tid
            vim.command('sign place %d name=breakpt line=%d file=%s' % (tid, line, file))
        else:
            pass # print 'failed to set breakpoint... %d : %s' % (tid, self.waiting)

    def clear_break(self, tid):
        bid = self.toremove.pop(tid)
        if bid in self.breaks:
            file, line, tid = self.breaks.pop(bid)
            vim.command('sign unplace %d file=%s' % (tid, file))
        else:
            print 'failed to remove', bid

    def break_at(self, file, line):
        # self.windows['log'].write('looking for %s line %s in %s' % (file, line, self.breaks))
        for bid, value in self.breaks.iteritems():
            if value[:2] == (file, line):
                return bid
        return -1

    def destroy(self):
        """ destroy windows """
        for window in self.windows.values():
            window.destroy()

    def go_srcview(self):
        vim.command('1wincmd w')

    def next_sign(self):
        if self.cursign == '1':
            return '2'
        else:
            return '1'

    def set_srcview(self, file, line):
        """ set srcview windows to file:line and replace current sign """
        if os.name == 'nt':
            file = os.path.normpath(file)
            file = file[6:]
        else:
            pass

        if file.startswith('file:'):
            file = file[len('file:'):]
            if file.startswith('///'):
                file = file[2:]

        if file == self.file and self.line == line:
            return

        nextsign = self.next_sign()

        if file != self.file:
            self.file = file
            self.go_srcview()
            vim.command('silent edit! ' + file)

        cmd = 'sign place %s name=current line=%s file=%s' % (nextsign, line, file)

        vim.command(str(cmd))
        vim.command('sign unplace ' + self.cursign)

        vim.command('sign jump ' + nextsign + ' file='+file)
        #vim.command('normal z.')

        self.line = line
        self.cursign = nextsign

# vim: et sw=4 sts=4
