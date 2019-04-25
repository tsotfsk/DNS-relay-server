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
        try:
            m.fromStr(message)
        except Exception:
            return

        if m.header.answer == 0:  # 查询包
            print(m.header.id, m.queries[0].name, m.queries[0].type, m.header.qdCount, m.header.anCount)
            self.handleRequest(m)         
        else:  # 应答包
            print(m.header.id, m.queries[0].name, m.queries[0].type, m.header.qdCount, m.header.anCount)
            self.handleResponse(m)

    def handleRequest(self, m):
        if m.queries[0].type not in DEALLIST: # 无法处理的类型就转发
            message = self.transform(m)  # 消息id转换
            self.relay(message, (ADDR, PORT))  # 转发
        else:
            sqlStr = 'select * from  DNS where NAME = ? and TYPE = ?'
            value = (m.queries[0].name.name, CNAME)
            result = database.fetchall(sqlStr, value)  
            print(result) 
            rr = ResourceRecord(result[0], result[1], result[2], result[3], result[])                
            if len(result) == 0:  # 查不到结果就把请求转发出去
                message = self.transform(m)  
                self.relay(message, (ADDR, PORT))
            else:  # 自己pack包
                m.addAnswer(rr)
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
                sqlStr = 'insert into DNS values (?,?,?,?,?,?)'
                if rr.type == MX:
                    rdata = str(rr.rdata.preference) + '|' + rr.rdata.name.name               
                elif rr.type == A:
                    rdata = socket.inet_ntoa(rr.rdata.address)
                else:
                    rdata = rr.rdata.name.name
                print(rdata)
                value = (rr.name.name, rr.type, rr.cls, rr.ttl, rr.rdlength, rdata)
                database.fetchall(sqlStr, value)

    def transform(self, m):
        randID = random.randint(0, 65535)
        # 加入到消息转换字典中
        lock.acquire()
        if self.clientAddress in idTransDict:
            idTransDict[self.clientAddress].append((m.header.id, randID, time()))# 字典记录消息id转换的对应关系,一个IP一个dict,一对消息转换对应其中一个键值对
        else:
            idTransDict[self.clientAddress] = []
            idTransDict[self.clientAddress].append((m.header.id, randID, time()))
        m.header.id = randID
        lock.release()
        return m.toStr()

    def inverseTransform(self, m):
        lock.acquire()
        for addr, transList in idTransDict.items():
            for (front, back, timeStamp) in transList:
                if m.header.id == back:
                    m.header.id = front
                    idTransDict.pop(addr)
                    lock.release()
                    return m.toStr(), addr, timeStamp

    def relay(self, message, addr):
        self.server.socket.sendto(message, addr)

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
    database = DNSDataBase(mincached=2, maxcached=5, maxconnections=10, database='DNSDataBase.db')
    # 开启一个线程用作UDP干活,似乎主线程很闲，没必要这么做哦
    with UDPServer(('10.28.128.174', 60000), DnsHandler) as dnsServer:
        serverThread = threading.Thread(target = dnsServer.server_forever)
        serverThread.daemon = True
        serverThread.start()
        print('DnsServer is runnng in thread', serverThread.name , serverThread.ident)

        while True:
            1 == 2 