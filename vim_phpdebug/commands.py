import sys
import vim
import traceback
from debugger import Debugger

def debugger_init(debug = 0):
    global debugger

    # get needed vim variables

    # port that the engine will connect on
    port = int(vim.eval('debuggerPort'))
    if port == 0:
        port = 9000

    # the max_depth variable to set in the engine
    max_children = vim.eval('debuggerMaxChildren')
    if max_children == '':
        max_children = '32'

    max_data = vim.eval('debuggerMaxData')
    if max_data == '':
        max_data = '1024'

    max_depth = vim.eval('debuggerMaxDepth')
    if max_depth == '':
        max_depth = '1'

    minibufexpl = int(vim.eval('debuggerMiniBufExpl'))
    if minibufexpl == 0:
        minibufexpl = 0

    debugger = Debugger(port, max_children, max_data, max_depth, minibufexpl, debug)

def debugger_command(msg, arg1 = '', arg2 = ''):
    try:
        debugger.command(msg, arg1, arg2)
        if debugger.status != 'stopped':
            debugger.command('stack_get')
    except:
        debugger.ui.tracewin.write(sys.exc_info())
        debugger.ui.tracewin.write("".join(traceback.format_tb( sys.exc_info()[2])))
        debugger.stop()
        print 'Connection closed, stop debugging', sys.exc_info()

def debugger_run():
    try:
        debugger.run()
    except:
        debugger.ui.tracewin.write(sys.exc_info())
        debugger.ui.tracewin.write("".join(traceback.format_tb( sys.exc_info()[2])))
        debugger.stop()
        print 'Connection closed, stop debugging', sys.exc_info()

def debugger_watch_input(cmd, arg = ''):
    try:
        if arg == '<cword>':
            arg = vim.eval('expand("<cword>")')
        debugger.watch_input(cmd, arg)
    except:
        debugger.ui.tracewin.write( sys.exc_info() )
        debugger.ui.tracewin.write( "".join(traceback.format_tb(sys.exc_info()[2])) )
        debugger.stop()
        print 'Connection closed, stop debugging'

def debugger_context():
    try:
        debugger.command('context_get')
    except:
        debugger.ui.tracewin.write(sys.exc_info())
        debugger.ui.tracewin.write("".join(traceback.format_tb( sys.exc_info()[2])))
        debugger.stop()
        print 'Connection closed, stop debugging'

def debugger_property(name = ''):
    try:
        debugger.property_get()
    except:
        debugger.ui.tracewin.write(sys.exc_info())
        debugger.ui.tracewin.write("".join(traceback.format_tb( sys.exc_info()[2])))
        debugger.stop()
        print 'Connection closed, stop debugging', sys.exc_info()

def debugger_mark(exp = ''):
    try:
        debugger.mark(exp)
    except:
        debugger.ui.tracewin.write(sys.exc_info())
        debugger.ui.tracewin.write("".join(traceback.format_tb( sys.exc_info()[2])))
        debugger.stop()
        print 'Connection closed, stop debugging', sys.exc_info()

def debugger_up():
    try:
        debugger.up()
    except:
        debugger.ui.tracewin.write(sys.exc_info())
        debugger.ui.tracewin.write("".join(traceback.format_tb( sys.exc_info()[2])))
        debugger.stop()
        print 'Connection closed, stop debugging', sys.exc_info()

def debugger_down():
    try:
        debugger.down()
    except:
        debugger.ui.tracewin.write(sys.exc_info())
        debugger.ui.tracewin.write("".join(traceback.format_tb( sys.exc_info()[2])))
        debugger.stop()
        print 'Connection closed, stop debugging', sys.exc_info()

def debugger_quit():
    global debugger
    debugger.quit()

mode = 0
def debugger_resize():
    global mode
    mode = mode + 1
    if mode >= 3:
        mode = 0

    if mode == 0:
        vim.command("wincmd =")
    elif mode == 1:
        vim.command("wincmd |")
    if mode == 2:
        vim.command("wincmd _")

# vim: et sw=4 sts=4
