"""
Tunneled SSH client module

Usage:
- {cmd} connect ssh <deviceName> [ssh-arguments...]
- {cmd} :ssh <deviceName> [ssh-arguments...] - shorthand for the above


Examples:
- {cmd} :ssh@foo ondevice/test -l root
  Login to the SSH service named `foo` on `ondevice`'s test device as user `root`
"""


from ondevice.core.connection import Connection, Response
from ondevice.modules import TunnelClient, TunnelService

import codecs
import logging
import socket
import subprocess
import sys
import threading

info = 'Connect to your devices\' SSH server'
encrypted = True

class Client(TunnelClient):
    """ Endpoint stub that simply invokes 'ssh' with the ProxyCommand set to
    'onclient connect ssh:tunnel' """
    def __init__(self, devId, protocol, svcName, *args, auth=None):
        TunnelClient.__init__(self, devId, protocol, svcName, auth=None)
        self._sshArgs = list(args)

    def runLocal(self):
        params = self._params
        devId = params['devId']
        protocol = params['protocol']
        svcName = params['svcName']

        # TODO use the dynamic module name
        proxyCmd = [ sys.argv[0], 'connect', '{0}:tunnel@{1}'.format(protocol, svcName), devId ]
        if 'auth' in params:
            proxyCmd.append('auth={0}'.format(params['auth']))

        ssh = subprocess.Popen(['ssh', '-o', 'ProxyCommand={0}'.format(' '.join(proxyCmd))]+self._sshArgs+['ondevice:{0}'.format(devId)], stdin=None, stdout=None, stderr=None)
        ssh.wait()

    def startRemote(self):
        pass # we don't need a remote connection; Client_tunnel does that for us

class Client_tunnel(TunnelClient):
    def gotData(self, data):
        logging.debug("gotData: %s", repr(data))
        stream = self.getConsoleBuffer(sys.stdout)
        stream.write(data)
        stream.flush()

    def runLocal(self):
        while True:
            # read1() only invokes the underlying read function only once (and
            # in contrast to read() returns as soon as there's data available,
            # not just when 8192 bytes have actually been read)
            stream = self.getConsoleBuffer(sys.stdin)
            data = stream.read1(8192)
            if data:
                logging.debug("sndData: %s", repr(data))
                self._conn.send(data)
            else:
                logging.info("Local EOF, closing connection")
                self._conn.sendEOF()
                return

class Service(TunnelService):
    def runLocal(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TODO make me configurable
        # TODO use a timeout; raise an exception on error
        self._sock.connect(('localhost', 22))

        while True:
            data = self._sock.recv(8192)
            if data:
                logging.debug("sndData: %s", repr(data))
                self._conn.send(data)
            else:
                self._conn.sendEOF()
                return

    def gotData(self, data):
        logging.debug("gotData: %s", repr(data))
        self._sock.send(data)
