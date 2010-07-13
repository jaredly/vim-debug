import vim

class VimWindow:
    """ wrapper class of window of vim """
    name = 'DEBUG_WINDOW'
    dtext = ''
    def __init__(self, name = None, special=True, height=0):
        """ initialize """
        if name is not None:
            self.name = name
        self.buffer = None
        self.height = height
        self.firstwrite = 1
        self.special = special

    def isprepared(self):
        """ check window is OK """
        if self.buffer == None or len(dir(self.buffer)) == 0 or self.getwinnr() == -1:
            return 0
        return 1
    def prepare(self):
        """ check window is OK, if not then create """
        if not self.isprepared():
            self.create()
    def on_create(self):
        pass
    def getwinnr(self):
        return int(vim.eval("bufwinnr('"+self.name+"')"))

    def write(self, msg):
        """ append last """
        self.writelines(msg.splitlines())

    def writelines(self, lines):
        # print 'writing', lines
        lines = list(str(item) for item in lines)
        self.prepare()
        # if self.firstwrite == 1:
        #     self.firstwrite = 0
        #     self.buffer[:] = lines
        # else:
        self.buffer.append(lines)
        self.command('normal G')
        #self.window.cursor = (len(self.buffer), 1)

    def create(self, method = 'new'):
        """ create window """
        vim.command('silent ' + method + ' ' + self.name)
        vim.command("setlocal buftype=nofile")
        vim.command("setlocal nobuflisted")
        # vim.command("setlocal nomodifiable")
        self.buffer = vim.current.buffer
        self.buffer[:] = [self.dtext]
        self.buffer.append('')
        if self.height != 0:
            vim.command('res %d' % self.height)
        self.width = int( vim.eval("winwidth(0)") )
        self.height = int( vim.eval("winheight(0)") )
        self.on_create()

    def destroy(self):
        """ destroy window """
        if self.buffer == None or len(dir(self.buffer)) == 0:
            return
        self.command('bd %d' % self.buffer.number)
        self.firstwrite = 1

    def clear(self):
        """ clean all datas in buffer """
        self.prepare()
        self.buffer[:] = [self.dtext]
        self.firstwrite = 1

    def command(self, cmd):
        """ go to my window & execute command """
        self.prepare()
        winnr = self.getwinnr()
        if winnr != int(vim.eval("winnr()")):
            vim.command(str(winnr) + 'wincmd w')
        vim.command(cmd)

    def focus(self):
        self.prepare()
        winnr = self.getwinnr()
        if winnr != int(vim.eval("winnr()")):
            vim.command(str(winnr) + 'wincmd w')

# vim: et sw=4 sts=4
