import asyncio
import socket
from sippy.Time.MonoTime import MonoTime
from sippy.Core.Exceptions import dump_exception


class EchoServerProtocol:
    def __init__(self, on_data):
        self.on_data = on_data

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self.on_data(data, addr)


class Udp_server(object):
    def __init__(self, global_config, uopts):
        self.uopts = uopts.getCopy()
        self.transport = None
        self.protocol = None
        self.task = None

    def send_to(self, data, address, delayed=False):
        if not isinstance(data, bytes):
            data = data.encode('utf-8')
        print(self.transport)
        if self.transport:
            self.transport.sendto(data, address)

    def shutdown(self):
        if self.transport:
            self.transport.close()

    def handle_datagram(self, data, addr):
        rtime = MonoTime()
        try:
            self.uopts.data_callback(data, addr, self, rtime)
        except Exception as ex:
            if isinstance(ex, SystemExit):
                raise
            dump_exception(
                'Udp_server: unhandled exception when processing incoming data')

    async def create_server(self):
        # Get a reference to the event loop as we plan to use
        # low-level APIs.
        loop = asyncio.get_event_loop()  # get_running_loop
        if loop.is_closed():
            loop = asyncio.new_event_loop()

        self.transport, self.protocol = await loop.create_datagram_endpoint(
            lambda: EchoServerProtocol(self.handle_datagram),
            local_addr=self.uopts.laddress)  # (self.host, self.port))

        print(f"UDP server started on {
              self.transport.get_extra_info('sockname')}")
        print(self.transport)

    def start_server(self):
        event_loop = asyncio.get_event_loop()
        self.ask = event_loop.create_task(self.create_server())


_DEFAULT_FLAGS = socket.SO_REUSEADDR
if hasattr(socket, 'SO_REUSEPORT'):
    _DEFAULT_FLAGS |= socket.SO_REUSEPORT
_DEFAULT_NWORKERS = 30


class Udp_server_opts(object):
    laddress = None
    data_callback = None
    family = None
    flags = _DEFAULT_FLAGS
    nworkers = _DEFAULT_NWORKERS
    ploss_out_rate = 0.0
    pdelay_out_max = 0.0
    ploss_in_rate = 0.0
    pdelay_in_max = 0.0

    def __init__(self, laddress, data_callback, family=None, o=None):
        if o is not None:
            self.laddress, self.data_callback, self.family, self.nworkers, self.flags, \
                self.ploss_out_rate, self.pdelay_out_max, self.ploss_in_rate, \
                self.pdelay_in_max = o.laddress, o.data_callback, o.family, \
                o.nworkers, o.flags, o.ploss_out_rate, o.pdelay_out_max, o.ploss_in_rate, \
                o.pdelay_in_max
            return
        if family is None:
            if laddress is not None and laddress[0].startswith('['):
                family = socket.AF_INET6
                laddress = (laddress[0][1:-1], laddress[1])
            else:
                family = socket.AF_INET
        self.family = family
        self.laddress = laddress
        self.data_callback = data_callback

    def getSockOpts(self):
        sockopts = []
        if self.family == socket.AF_INET6 and self.isWildCard():
            sockopts.append((socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1))
        if (self.flags & socket.SO_REUSEADDR) != 0:
            sockopts.append((socket.SOL_SOCKET, socket.SO_REUSEADDR, 1))
        if self.nworkers > 1 and hasattr(socket, 'SO_REUSEPORT') and \
                (self.flags & socket.SO_REUSEPORT) != 0:
            sockopts.append((socket.SOL_SOCKET, socket.SO_REUSEPORT, 1))
        return sockopts

    def getCopy(self):
        return self.__class__(None, None, o=self)

    def getSIPaddr(self):
        if self.family == socket.AF_INET:
            return self.laddress
        return (('[%s]' % self.laddress[0], self.laddress[1]))

    def isWildCard(self):
        if (self.family, self.laddress[0]) in ((socket.AF_INET, '0.0.0.0'),
                                               (socket.AF_INET6, '::')):
            return True
        return False
