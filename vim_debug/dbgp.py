import socket
import base64
import xml.dom.minidom

class DBGP:
    """ DBGp Procotol class """
    def __init__(self, options, log=lambda text:None, type=None):
        self.sock = PacketSocket(options)
        self.cid = 0
        self.received = 0
        self.handlers = {}
        self.addCommandHandler = self.handlers.__setitem__
        self.connect = self.sock.accept
        self.close = self.sock.close
        self.log = log
        self._type = type

    def connected(self):
        return self.sock.connected

    def command(self, cmd, *args, **kargs):
        tpl = '%s -i %d%s%s'
        self.cid += 1
        data = kargs.pop('data', '')
        str_args = ''.join(' -%s %s' % arg for arg in zip(args[::2], args[1::2])) # args.iteritems())
        if data:
            b64data = ' -- ' + base64.encodestring(data)[:-1]
            if self._type == 'python':
                str_args += ' -l %d' % (len(b64data)-4)
        else:
            b64data = ''
        cmd = tpl % (cmd, self.cid, str_args, b64data)
        self.log('SEND: %s' % cmd)
        self.sock.send(cmd)
        if not kargs.get('suppress', False):
            self.get_packets()
        return self.cid
    
    def get_packets(self, force=0):
        while self.received < self.cid or force > 0:
            force -= 1
            if not self.sock.sock:
                return
            packet = self.sock.read_packet()
            # print 'packet:', self.received, self.cid
            # print packet.toprettyxml(indent='   ')
            self.log('RECV: %s' % packet.toprettyxml(indent='   '))
            if packet.tagName == 'response':
                if packet.getAttribute('transaction_id') == '':
                    self.handlers['error'](packet.firstChild)
                    continue
                id = int(packet.getAttribute('transaction_id'))
                if id > self.received:
                    self.received = id
                else:
                    print 'weird -- received is greater than the id I just got: %d %d' % (self.received, id)
                cmd = packet.getAttribute('command')
                if cmd in self.handlers:
                    self.handlers[cmd](packet)
                else:
                    raise TypeError('invalid packet type:', cmd)
            elif packet.tagName == 'stream':
                if '<stream>' in self.handlers and packet.firstChild is not None:
                    text = base64.decodestring(packet.firstChild.data)
                    self.handlers['<stream>'](packet.getAttribute('type'), text)
            elif packet.tagName == 'init':
                self.handlers['<init>'](packet)
            else:
                print 'tagname', packet.tagName

class PacketSocket:
    def __init__(self, options):
        self.options = options
        self.sock = None
        self.connected = False

    def accept(self):
        # print 'waiting for a new connection on port %d for %d seconds...' % (self.options.get('port', 9000),
        #                                                                      self.options.get('wait', 5))
        self.connected = False
        serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(20)
        serv.settimeout(5)
        try:
            serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            serv.bind(('', self.options.get('port', 9000)))
            serv.listen(self.options.get('listens', 5))
            print 'waiting for a connection'
            (self.sock, address) = serv.accept()
        except socket.timeout:
            serv.close()
            return False

        # print 'connection from ', address
        self.connected = True
        serv.close()
        return True
    
    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None
        self.connected = False

    def read(self, size):
        '''main receiving class...'''
        text = ''
        while size > 0:
            buf = self.sock.recv(size)
            if buf == '':
                self.close()
                raise EOFError, 'Socket Closed'
            text += buf
            size -= len(buf)
        return text

    def read_number(self):
        length = ''
        while 1:
            if not self.sock:
                raise EOFError, 'Socket Closed'
            c = self.sock.recv(1)
            if c == '':
                self.close()
                raise EOFError, 'Socket Closed'
            if c == '\0':
                return int(length)
            if c.isdigit():
                length += c

    def read_null(self):
        '''read a null byte'''
        c = self.sock.recv(1)
        if c != '\0':
            raise Exception('invalid response from debug server')
        '''
        while 1:
            c = self.sock.recv(1)
            if c == '':
                self.close()
                raise EOFError, 'Socket Closed'
            if c == '\0':
                return
                '''

    def read_packet(self):
        '''read a packet from the server and return the xml tree'''
        length = self.read_number()
        body = self.read(length)
        self.read_null()
        return xml.dom.minidom.parseString(body).firstChild

    def send(self, cmd):
        self.sock.send(cmd + '\0')

# vim: et sw=4 sts=4
