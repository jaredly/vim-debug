
import socket
import base64

class DbgProtocol:
    """ DBGp Procotol class """
    def __init__(self, port = 9000):
        socket.setdefaulttimeout(5)
        self.port = port
        self.sock = None
        self.isconned = False
    def isconnected(self):
        return self.isconned
    def accept(self):
        print 'waiting for a new connection on port '+str(self.port)+' for 5 seconds...'
        self.isconned = False
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
            return False

        print 'connection from ', address
        self.isconned = True
        serv.close()
        return True
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
        body = self.recv_body(length)
        self.recv_null()
        return body
    def send_msg(self, cmd):
        self.sock.send(cmd + '\0')


# vim: et sw=4 sts=4
