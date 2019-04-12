from UDPAsyncServer import *
import threading
import time
import sys
import sqlite3
from setting import *
__version__ = '0.0'

class DnsHandler(BaseRequestHandler):

    def handle(self):
        data = self.request[0].decode()
        print(data)
        self.server.socket.sendto(bytes('hello',encoding = 'utf-8'), self.clientAddress)
        

if __name__ == "__main__":

    # 开启一个线程用作UDP干活
    with UDPServer(('127.0.0.1', 60000), DnsHandler) as dnsServer:
        serverThread = threading.Thread(target = dnsServer.server_forever)
        serverThread.daemon = True
        serverThread.start()
        print('DnsServer is runnng in thread', serverThread.name)

        while True:
            1==2

