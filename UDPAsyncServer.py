__version__ = '0.0'

import socket
import selectors
import os
import errno
import sys
import threading
import logging

from time import monotonic as time2

__all__ = ["UDPServer", "BaseRequestHandler"]

ServerSelector = selectors.SelectSelector

class UDPServer:
    '''
        一个采用多路I/O复用的UDP服务器
    '''
    daemonThreads = False
    threads = None

    def __init__(self, serverAddress, HandleClass):

        self.serverAddress = serverAddress
        self.HandleClass = HandleClass  # 处理事务专用
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.maxPacketSize = 8192  # 一般socket缓冲区是8K

        try:
            self.serverBind()
        except:
            self.serverClose()
            raise

    def serverBind(self):

        self.socket.bind(self.serverAddress)
        self.serverAddress = self.socket.getsockname()

    def serverForever(self, pollInterval = 0.5):
        '''
            服务器启动,pollInterval指的是轮询的超时时间
        '''
        try:
            # XXX: 轮询不好，而且实际上poll如果有多条消息到来还是串行读取，所以此处通过多线程来提高效率
            with ServerSelector() as selector:
                selector.register(self, selectors.EVENT_READ)
                while True:
                    ready = selector.select(pollInterval)
                    if ready:
                        self.handleRequestNoblock()
        except Exception as e:
            logging.error(e)

    def fileno(self):
        '''
            select需要的文件描述符
        '''
        return self.socket.fileno()

    def handleRequestNoblock(self):
        try:
            request, clientAddress = self.getRequest()
        except OSError:
            return
        
        try:
            self.processRequest(request, clientAddress)
        except Exception as e:
            logging.error(e)

    def getRequest(self):
        data, clientAddr = self.socket.recvfrom(self.maxPacketSize)
        return (data, self.socket), clientAddr

    def processRequestThread(self, request, client_address):

        logging.info('正在处理的线程ID:{}, 当前活跃线程数:{}'.format(threading.current_thread().ident, threading.active_count()))
        try:
            self.finishRequest(request, client_address)
        except Exception as e:
            logging.error(e)

    def processRequest(self, request, clientAddress):
        """开启一个线程去处理消息"""
        t = threading.Thread(target = self.processRequestThread,
                             args = (request, clientAddress))
        t.daemon = self.daemonThreads
        if not t.daemon :
            if self.threads is None:
                self.threads = []
            self.threads.append(t)
        t.start()

    def serverClose(self):

        # 阻塞式的关闭
        threads = self.threads
        self.threads = None
        if threads:
            for thread in threads:
                thread.join()

    def finishRequest(self, request, clientAddress):
        self.HandleClass(request, clientAddress, self) 

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
   

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                            # filename=argDict['filename'],
                            format='%(asctime)s - %(filename)s-%(lineno)s[%(threadName)s] - %(levelname)s: %(message)s')
    with UDPServer(('0.0.0.0', 53), BaseRequestHandler) as dnsServer:
        logging.debug('running')
        dnsServer.serverForever()