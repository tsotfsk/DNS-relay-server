from UDPAsyncServer import *
from DnsMessage import *
import threading
import time

class DnsHandler(BaseRequestHandler):

    def handle(self):
        mess = self.request[0]
        strio = BytesIO(mess)
        h = Header()
        m = Message(h)
        m.decode(strio)
        print(m.header.id, m.header.qdCount, m.queries[0].name, m.queries[0].cls)


if __name__ == "__main__":

    # 获取命令行参数
    cmd = sys.argv
    debug = cmd[1]
    nameServerAddr = cmd[2]
    setting = cmd[3]

    # 开启一个线程用作UDP干活,似乎主线程很闲，没必要这么做哦
    with UDPServer(('127.0.0.1', 60000), DnsHandler) as dnsServer:
        serverThread = threading.Thread(target = dnsServer.server_forever)
        serverThread.daemon = True
        serverThread.start()
        print('DnsServer is runnng in thread', serverThread.name)

        while True:
            1 == 2 