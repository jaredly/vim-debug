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

        if file == self.file and self.line == line:
            return

        nextsign = self.next_sign()

        if file != self.file:
            self.file = file
            self.go_srcview()
            vim.command('silent edit ' + file)

        cmd = 'sign place %s name=current line=%s file=%s' % (nextsign, line, file)
        vim.command(str(cmd))
        vim.command('sign unplace ' + self.cursign)

        vim.command('sign jump ' + nextsign + ' file='+file)
        #vim.command('normal z.')

        self.line = line
        self.cursign = nextsign

# vim: et sw=4 sts=4
