import os
import vim

from subwindows import StackWindow, WatchWindow, TraceWindow, HelpWindow

class DebugUI:
    """ DEBUGUI class """
    def __init__(self, minibufexpl = 0):
        """ initialize object """
        self.watchwin = WatchWindow()
        self.stackwin = StackWindow()
        self.tracewin = TraceWindow()
        self.helpwin  = HelpWindow('HELP__WINDOW')
        self.mode     = 0 # normal mode
        self.file     = None
        self.line     = None
        self.winbuf   = {}
        self.cursign  = None
        self.sessfile = "/tmp/debugger_vim_saved_session." + str(os.getpid())
        self.minibufexpl = minibufexpl

    def debug_mode(self):
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
        self.file = None
        self.line = None
        self.mode = 0
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

        self.line = line
        self.cursign = nextsign

# vim: et sw=4 sts=4
