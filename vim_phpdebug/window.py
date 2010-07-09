import vim

class VimWindow:
    """ wrapper class of window of vim """
    def __init__(self, name = 'DEBUG_WINDOW', special=True, height=0):
        """ initialize """
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

    def xml_on_element(self, node):
        line = str(node.nodeName)
        if node.hasAttributes():
            for (n,v) in node.attributes.items():
                line += str(' %s=%s' % (n,v))
        return line
    def xml_on_attribute(self, node):
        return str(node.nodeName)
    def xml_on_entity(self, node):
        return 'entity node'
    def xml_on_comment(self, node):
        return 'comment node'
    def xml_on_document(self, node):
        return '#document'
    def xml_on_document_type(self, node):
        return 'document type node'
    def xml_on_notation(self, node):
        return 'notation node'
    def xml_on_text(self, node):
        return node.data
    def xml_on_processing_instruction(self, node):
        return 'processing instruction'
    def xml_on_cdata_section(self, node):
        return node.data

    def write(self, msg):
        """ append last """
        self.prepare()
        # cn = vim.current.buffer.number
        # vim.command('b! %d' % self.buffer.number)
        # vim.command("setlocal modifiable")
        if self.firstwrite == 1:
            self.firstwrite = 0
            self.buffer[:] = str(msg).split('\n')
        else:
            self.buffer.append(str(msg).split('\n'))
        # vim.command("setlocal nomodifiable")
        # vim.command('b! %d' % cn)
        self.command('normal G')
        #self.window.cursor = (len(self.buffer), 1)

    def create(self, method = 'new'):
        """ create window """
        vim.command('silent ' + method + ' ' + self.name)
        #if self.name != 'LOG___WINDOW':
        vim.command("setlocal buftype=nofile")
        vim.command("setlocal nobuflisted")
        # vim.command("setlocal nomodifiable")
        self.buffer = vim.current.buffer
        if self.height != 0:
            vim.command('res %d' % self.height)
        self.width = int( vim.eval("winwidth(0)") )
        self.height = int( vim.eval("winheight(0)") )
        self.on_create()

    def destroy(self):
        """ destroy window """
        if self.buffer == None or len(dir(self.buffer)) == 0:
            return
        #if self.name == 'LOG___WINDOW':
        #    self.command('hide')
        #else:
        self.command('bd %d' % self.buffer.number)
        self.firstwrite = 1

    def clean(self):
        """ clean all datas in buffer """
        self.prepare()
        self.buffer[:] = []
        self.firstwrite = 1

    def command(self, cmd):
        """ go to my window & execute command """
        self.prepare()
        winnr = self.getwinnr()
        if winnr != int(vim.eval("winnr()")):
            vim.command(str(winnr) + 'wincmd w')
        vim.command(cmd)

    def _xml_stringfy(self, node, level = 0, encoding = None):
        if node.nodeType == node.ELEMENT_NODE:
            line = self.xml_on_element(node)

        elif node.nodeType == node.ATTRIBUTE_NODE:
            line = self.xml_on_attribute(node)

        elif node.nodeType == node.ENTITY_NODE:
            line = self.xml_on_entity(node)

        elif node.nodeType == node.COMMENT_NODE:
            line = self.xml_on_comment(node)

        elif node.nodeType == node.DOCUMENT_NODE:
            line = self.xml_on_document(node)

        elif node.nodeType == node.DOCUMENT_TYPE_NODE:
            line = self.xml_on_document_type(node)

        elif node.nodeType == node.NOTATION_NODE:
            line = self.xml_on_notation(node)

        elif node.nodeType == node.PROCESSING_INSTRUCTION_NODE:
            line = self.xml_on_processing_instruction(node)

        elif node.nodeType == node.CDATA_SECTION_NODE:
            line = self.xml_on_cdata_section(node)

        elif node.nodeType == node.TEXT_NODE:
            line = self.xml_on_text(node)

        else:
            line = 'unknown node type'

        if node.hasChildNodes():
            #print ''.ljust(level*4) + '{{{' + str(level+1)
            #print ''.ljust(level*4) + line
            return self.fixup_childs(line, node, level)
        else:
            return self.fixup_single(line, node, level)

        return line

    def fixup_childs(self, line, node, level):
        line = ''.ljust(level*4) + line +    '\n'
        line += self.xml_stringfy_childs(node, level+1)
        return line
    def fixup_single(self, line, node, level):
        return ''.ljust(level*4) + line + '\n'

    def xml_stringfy(self, xml):
        return self._xml_stringfy(xml)
    def xml_stringfy_childs(self, node, level = 0):
        line = ''
        for cnode in node.childNodes:
            line = str(line)
            line += str(self._xml_stringfy(cnode, level))
        return line

    def write_xml(self, xml):
        self.write(self.xml_stringfy(xml))
    def write_xml_childs(self, xml):
        self.write(self.xml_stringfy_childs(xml))


# vim: et sw=4 sts=4
