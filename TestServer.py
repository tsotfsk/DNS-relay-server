from UDPAsyncServer import *
from DNSMessage import *
from DataBase import *
import threading
from time import monotonic as time
import logging
import random


class DnsHandler(BaseRequestHandler):

    def handle(self):
        message = self.request[0]
        m = Message()
        m.fromStr(message)
        print(m.header.id, m.header.qdCount, m.queries[0].name, m.queries[0].type)

        if m.header.answer == 0: # 查询包
            self.handleRequest(m)         
        else:  # 应答包
            self.handleResponse(m)

    def handleRequest(self, m):
        if m.queries[0].type not in DEALLIST: # 无法处理的类型就转发
            message = self.transform(m)  # 消息id转换
            self.relay(message, (ADDR, PORT))  # 转发
        else:
            # TODO 查找数据库
            result = None
            if result is None:  # 查不到结果就把请求转发出去
                message = self.transform(m)  
                self.relay(message, (ADDR, PORT))
            else:  # 自己pack包
                m.answers = result
                m.answer = 1
                # TODO 改包的header之类的
                message = m.toStr()
                self.relay(message, slef.clientAddress)
                
    def handleResponse(self, m):

        message, addr, timeStamp = self.inverseTransform(m)  # 反变换得到ip和消息

        # 如果超时就return了,不再转发
        curtime = time()
        if curtime - timeStamp > 3:
            return

        self.relay(message, addr) 
        # 之后把包内数据插入或更新到数据库
        if len(m.authority) == 0 and len(m.additional) == 0:  # 没有authority和additional字段才缓存, 有的话不缓存包
            for rr in m.answers: 
                if rr.type not in DEALLIST:  # 如果answer字段也出现了要求之外的type,也不缓存包
                    return
            for rr in m.answers:    
                # TODO 放到数据库
                pass

    def transform(self, m):
        randID = random.randint(0, 65535) 
        m.id = randID
        # 加入到消息转换字典中
        lock.acquire()
        if self.clientAddress[0] in idTransDict:
            idTransDict[self.clientAddress[0]].append((m,id, randID, time()))# 字典记录消息id转换的对应关系,一个IP一个dict,一对消息转换对应其中一个键值对
        else:
            idTransDict[self.clientAddress[0]] = []
            idTransDict[self.clientAddress[0]].append((m,id, randID, time()))
        lock.release()
        return m.toStr()

    def inverseTransform(self, m):
        lock.acquire()
        for ip, transList in idTransDict.items():
            for (front, back, timeStamp) in transList:
                if m.id == back:
                    m.id = front
                    lock.release()
                    return m.toStr(), ip, timeStamp

    def relay(self, message, addr):
        relayClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,0)
        relayClient.sendto(message, addr)
        relayClient.close()

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
    lock = threading.Lock()

    # 开启一个线程用作UDP干活,似乎主线程很闲，没必要这么做哦
    with UDPServer(('127.0.0.1', 60000), DnsHandler) as dnsServer:
        serverThread = threading.Thread(target = dnsServer.server_forever)
        serverThread.daemon = True
        serverThread.start()
        print('DnsServer is runnng in thread', serverThread.name)

        while True:
            1 == 2 