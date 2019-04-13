from UDPAsyncServer import *
from DNSMessage import *
from DataBase import *
import threading
import time
import logging
import random

class DnsHandler(BaseRequestHandler):

    def handle(self):
        message = self.request[0]
        m = Message()
        m.fromStr(message)
        print(m.header.id, m.header.qdCount, m.queries[0].name, m.queries[0].type)

        if m.header.answer == 0: # 查询包
            handleRequest(m)          
        else:  # 应答包
            handleResponse(m)

    def handleRequest(self, m):
        if m.queries[0].type not in DEALLIST: # 无法处理的类型就转发
            message = transform(m)  # 这是中继到名字服务器的转发
            relay(message, (ADDR,PORT))
        else:
            # TODO 查找数据库
            result = None
            if result is None:  # 查不到结果就把请求转发出去
                transform(message)  
                relay(message, (ADDR,PORT))
            else:  # 自己pack包
                m.answers = result
                m.answer = 1
                # TODO 改一些包的的头，之类的
                message = m.toStr()
                relay(message, slef.clientAddress)
                

    def handleResponse(self, m):

        # 首先发结果转发出去
        message, addr = inverseTransform(m)  # 反变换得到ip和消息
        relay(message, addr)
        
        # 之后把包内数据插入或更新到数据库
        if len(m.authority) == 0 and len(m.additional) == 0:  # 没有authority和additional字段, 有的话不缓存包
            for rr in m.answers: 
                if rr.type not in DEALLIST:  # 如果answer字段也出现了要求之外的type,也不缓存包
                    return
            for rr in m.answers:    
                # TODO 放到数据库


    def transform(self, m):
        randID = random.randint(0, 65535) 
        m.id = randID
        # 加入到消息转换字典中
        if self.clientAddress[0] in idTransDict:
            idTransDict[self.clientAddress[0]].append((m,id, randID))# 字典记录消息id转换的对应关系,一个IP一个dict,一对消息转换对应其中一个键值对
        else:
            idTransDict[self.clientAddress[0]] = []
            idTransDict[self.clientAddress[0]].append((m,id, randID))
        return m.toStr()

    def inverseTransform(self, m):
        for ip, transList in idTransDict.items():
            for (front, back) in idTransDict[]:
                if(m.id == back):
                    m.id = front
                    return m.toStr(), ip

    def relay(self, mess, addr):
        relayClient = socket(AF_INET, SOCK_DGRAM,0)
        relayClient.sendto(message, addr)

    def packMessage(self, message):  # 这里message是参考
        pass

    def unpackMessage(self, message):  # 这里message是拆包对象
        pass



if __name__ == "__main__":

    # # 获取命令行参数
    # cmd = sys.argv
    # debug = cmd[1]
    # nameServerAddr = cmd[2]
    # setting = cmd[3]

    idTransDict = {}  # 消息ID转换的字典
    idTransDict.
    # 开启一个线程用作UDP干活,似乎主线程很闲，没必要这么做哦
    with UDPServer(('127.0.0.1', 60000), DnsHandler) as dnsServer:
        serverThread = threading.Thread(target = dnsServer.server_forever)
        serverThread.daemon = True
        serverThread.start()
        print('DnsServer is runnng in thread', serverThread.name)

        while True:
            1 == 2 