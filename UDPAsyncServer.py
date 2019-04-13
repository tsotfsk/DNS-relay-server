

__version__ = '0.0'

import socket
import selectors
import os
import errno
import sys
import threading
from time import monotonic as time

__all__ = ["UDPServer", "BaseRequestHandler"]
_ServerSelector = selectors.SelectSelector

class UDPServer:

    timeout = None
    allowReuseAddress = False
    daemonThreads = False
    _blockOnClose = False
    _threads = None

    def __init__(self, serverAddress, HandleClass):

        self.serverAddress = serverAddress
        self.HandleClass = HandleClass  # 处理事务专用类
        self.__isShutDown = threading.Event()
        self.__isShutDownRequest = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.maxPacketSize = 8192  # 一般socket缓冲区是8K

        try:
            self.serverBind()
        except:
            self.serverClose()
            raise

    def serverBind(self):
        '''
            nothing
        '''
        if self.allowReuseAddress:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.serverAddress)
        self.serverAddress = self.socket.getsockname()

    def server_forever(self, pollInterval = 0.5):

        self.__isShutDown.clear()
        try:
            # XXX: polling is not good
            with _ServerSelector() as selector:
                selector.register(self, selectors.EVENT_READ)
                while not self.__isShutDownRequest:
                    ready = selector.select(pollInterval)
                    if ready:
                        self._handleRequestNoblock()

                        self.serviceActions()
        finally:
            self.__isShutDownRequest = False
            self.__isShutDown.set()

    def fileno(self):
        return self.socket.fileno()

    def shutdown(self):
        
        self.__isShutDownRequest = True
        self.__isShutDown.wait()
    
    def serviceActions(self):
        pass

    def _handleRequestNoblock(self):
        try:
            request, clientAddress = self.getRequest()
        except OSError:
            return
        
        if self.verifyRequest(request, clientAddress):
            try:
                self.processRequest(request, clientAddress)
            except Exception:
                self.handleError(request, clientAddress)
                self.shutDownRequest(request)
            except:
                self.shutDownRequest(request)
                raise
        else:
            self.shutDownRequest(request)

    def handleTimeout(self):
        pass

    def getRequest(self):
        data, clientAddr = self.socket.recvfrom(self.maxPacketSize)
        return (data, self.socket), clientAddr

    def verifyRequest(self, request, clientAddress):
        return True

    def processRequestThread(self, request, client_address):

        # print(threading.current_thread(), threading.active_count())
        try:
            self.finishRequest(request, client_address)
        except Exception:
            self.handleError(request, client_address)
        finally:
            self.shutDownRequest(request)

    def processRequest(self, request, clientAddress):
        """Start a new thread to process the request."""
        t = threading.Thread(target = self.processRequestThread,
                             args = (request, clientAddress))
        t.daemon = self.daemonThreads
        if not t.daemon and self._blockOnClose:
            if self._threads is None:
                self._threads = []
            self._threads.append(t)
        t.start()

    def serverClose(self):
        if self._blockOnClose:
            threads = self._threads
            self._threads = None
            if threads:
                for thread in threads:
                    thread.join()

    def finishRequest(self, request, clientAddress):
        self.HandleClass(request, clientAddress, self)

    def shutDownRequest(self, request):
        self.closeRequest(request)

    def closeRequest(self, request):
        pass

    def handleError(self, request, clientAddress):
        print('-' * 40, file = sys.stderr)
        print('Exception happened during processing of request from',
            clientAddress, file = sys.stderr)
        import traceback
        traceback.print_exc()
        print('-' * 40, file = sys.stderr)    

    def __enter__(self):
        return self

    def __exit__(self, *qrgs):
        self.serverClose()

class BaseRequestHandler:

    def __init__(self, request, clientAddress, server):
        self.request = request
        self.clientAddress = clientAddress
        self.server = server
        self.setup()
        try:
            self.handle()
        finally:
            self.finish()

    def setup(self):
        pass

    def handle(self):
        pass

    def finish(self):
        pass
   

