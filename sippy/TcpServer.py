from threading import Condition
import socket
# import traceback
from threading import Thread
from time import sleep
from errno import ECONNRESET, ENOTCONN, ESHUTDOWN, EBADF, EINTR
from sippy.Time.MonoTime import MonoTime
from sippy.Core.Exceptions import dump_exception
from sippy.Core.EventDispatcher import ED2
import random
from sippy.Time.Timeout import Timeout
from sippy.Network_server import Network_server, Remote_address
from sippy.SipConf import MyPort


class TcpConnection(Thread):
    daemon = True
    userv = None

    def __init__(self, userv):
        Thread.__init__(self)
        self.userv = userv
        print(type(self.userv))
        self.start()
        self.c = None

    def run(self):
        self.c, address = self.userv.skt.accept()
        print('TcpReceiver connected to {}'.format(address))

        maxemptydata = 100
        while True:
            try:
                data, addr = self.c.recvfrom(8192)
                if not data:
                    # Ugly hack to detect socket being closed under us on Linux.
                    # The problem is that even call on non-closed socket can
                    # sometimes return empty data buffer, making AsyncReceiver
                    # to exit prematurely.
                    maxemptydata -= 1
                    if maxemptydata == 0:
                        print('this is the end')
                        break
                    continue
                else:
                    maxemptydata = 100
                rtime = MonoTime()
            except Exception as why:
                if isinstance(why, socket.error) and why.errno in (ECONNRESET, ENOTCONN, ESHUTDOWN, EBADF):
                    print('TcpReceiver: socket error {}'.format(why))
                    break
                if isinstance(why, socket.error) and why.errno in (EINTR,):
                    continue
                else:
                    dump_exception(
                        'Udp_server: unhandled exception when receiving incoming data')
                    sleep(1)
                    continue
            print('TcpReceiver received data {}'.format(data))
            print('TcpReceiver received address {}'.format(address))
            if self.userv.uopts.family == socket.AF_INET6:
                address = ('[%s]' % address[0], address[1])
            if not self.userv.uopts.direct_dispatch:
                # address = Remote_address(address, self.userv.transport)
                ED2.callFromThread(self.userv.handle_read,
                                   data, address, rtime)
            else:
                self.userv.handle_read(data, address, rtime)
        self.userv = None
        self.c.close()

    def send(self, data):
        print('TcpReceiver send {}'.format(data))
        self.c.send(data)


class TcpServer(Network_server):
    transport = 'tcp'

    def __init__(self, global_config, uopts):
        self.uopts = uopts.getCopy()
        print('TcpServer {}'.format(self.uopts.laddress))
        self.skt = socket.socket(self.uopts.family, socket.SOCK_STREAM)
        if self.uopts.laddress is not None:
            print('laddress is not None' + str(self.uopts.laddress) +
                  ' ' + str(self.uopts.family))
            ai = socket.getaddrinfo(
                self.uopts.laddress[0], None, self.uopts.family)
            if self.uopts.family == socket.AF_INET:
                address = (ai[0][4][0], self.uopts.laddress[1])
            else:
                address = (ai[0][4][0], self.uopts.laddress[1],
                           ai[0][4][2], ai[0][4][3])
            for so_val in self.uopts.getSockOpts():
                self.skt.setsockopt(*so_val)
            if isinstance(address[1], MyPort):
                # XXX with some python 3.10 version I am getting
                # TypeError: 'MyPort' object cannot be interpreted as an integer
                # might be something inside socket.bind?
                address = (address[0], int(address[1]))

            # bind and listen
            self.skt.bind(address)
            self.skt.listen(5)

            if self.uopts.laddress[1] == 0:
                self.uopts.laddress = self.skt.getsockname()
        self.sendqueue = []
        self.stats = [0, 0, 0]
        self.wi_available = Condition()
        self.wi = []
        self.areceivers = []
        self.areceivers.append(TcpConnection(self))

    def getSIPaddr(self):
        print('getSIPaddr')
        return (('[%s]' % self.uopts.laddress[0], self.uopts.laddress[1]), self.transport)

    def send_to(self, data, address, delayed=False):
        print('send_to {} {} {}'.format(data, address, delayed))
        if not isinstance(data, bytes):
            data = data.encode('utf-8')
        self.areceivers[0].send(data)

    def shutdown(self):
        pass

    def join(self):
        pass

    def handle_read(self, data, address, rtime, delayed=False):
        if len(data) > 0 and self.uopts.data_callback != None:
            self.stats[2] += 1
            if self.uopts.ploss_in_rate > 0.0 and not delayed:
                if random() < self.uopts.ploss_in_rate:
                    return
            if self.uopts.pdelay_in_max > 0.0 and not delayed:
                pdelay = self.uopts.pdelay_in_max * random()
                Timeout(self.handle_read, pdelay, 1, data,
                        address, rtime.getOffsetCopy(pdelay), True)
                return
            try:
                self.uopts.data_callback(data, address, self, rtime)
            except Exception as ex:
                if isinstance(ex, SystemExit):
                    raise
                dump_exception(
                    'Udp_server: unhandled exception when processing incoming data')
