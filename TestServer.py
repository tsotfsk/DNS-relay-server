from UDPAsyncServer import *
from DNSMessage import *
from DataBase import *
import threading
import time
import logging

class DnsHandler(BaseRequestHandler):

    def handle(self):
        message = self.request[0]
        m = Message()
        m.fromStr(message)
        print(m.header.id, m.header.qdCount, m.queries[0].name, m.queries[0].type)

        if m.header.answer == 0  # 查询包
            if m.queries[0].type not in DEALLIST: # 无法处理的类型就转发
                delay(message, addr)
            else:
                # TODO 查找数据库
                pass          
        else:  # 应答包
            if len(m.authority) == 0 and len(m.additional) == 0:  # 没有authority和additional字段
                for rr in m.answers:
                    if rr.type not in DEALLIST:
                        relayClient = socket(AF_INET, SOCK_DGRAM,0)
                        relayClient.sendto(message, (ADDR, PORT))
                        return 
                for rr in m.answers:
                    # TODO 放到数据库中
                    pass

    def funcname(self, parameter_list):
        pass
        
    def delay(mess, addr):
        relayClient = socket(AF_INET, SOCK_DGRAM,0)
        relayClient.sendto(message, addr)

    def packMessage():
        pass

    def unpackMessage():
        pass



if __name__ == "__main__":

    # # 获取命令行参数
    # cmd = sys.argv
    # debug = cmd[1]
    # nameServerAddr = cmd[2]
    # setting = cmd[3]

    idTransDict = {}  # 消息ID转换的字典

    # 开启一个线程用作UDP干活,似乎主线程很闲，没必要这么做哦
    with UDPServer(('127.0.0.1', 60000), DnsHandler) as dnsServer:
        serverThread = threading.Thread(target = dnsServer.server_forever)
        serverThread.daemon = True
        serverThread.start()
        print('DnsServer is runnng in thread', serverThread.name)

        while True:
            1 == 2 