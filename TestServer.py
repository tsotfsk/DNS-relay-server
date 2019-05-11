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
        try:
            strio = BytesIO(message)
            header =  Header()
            header.decode(strio)

            query = Query()
            query.decode(strio)
        except Exception as e:
            print(e)
            return
        print('收到的消息的ID以及请求内容', header.id, query.name, TYPEDICT[query.type],
            header.qdCount, header.anCount, header.nsCount, header.arCount)

        if header.answer == 0:  # 查询包
            print('该包是查询包')
            self.handleRequest(message)         
        else:  # 应答包
            print('该包是响应包')
            self.handleResponse(message, query, header)

    def handleRequest(self, message):

        '''请求报文的处理'''
        m = Message()
        m.fromStr(message)
        if m.queries[0].type not in DEALLIST: # 无法处理的类型就转发
            message = self.transform(m)  # 消息id转换
            self.relay(message, (ADDR, PORT))  # 转发
            print('请求消息不在可处理范围内,转发数据包到DNS服务器','\n')
        else:
            # self.searchRR(m.queries[0].name.name.decode('ascii'), m.queries[0].type)
            # 查找数据库中是否有对应记录
            sqlStr = 'select * from  DNS where NAME = ? and TYPE = ?'
            value = (m.queries[0].name.name.decode('ascii'), m.queries[0].type)
            result = database.fetchall(sqlStr, value)  
            
            if len(result) == 0:  # 查不到结果就查CNAME
                resultCname = []
                if(m.queries[0].type != CNAME):  # 当请求不是CNAME的时候才去查CNAME
                    sqlStr = 'select * from  DNS where NAME = ? and TYPE = ?'
                    value = (m.queries[0].name.name.decode('ascii'), CNAME)
                    resultCname = database.fetchall(sqlStr, value)

                # CNAME也没查到就转发了
                if(len(resultCname) == 0):
                    message = self.transform(m)
                    print('类型可以处理，但在数据库中查找不到对应的资源记录')
                    self.relay(message, (ADDR, PORT))
                    return
                else:
                    print('CNAME的列表是', resultCname)
                    result = []
                    for item in resultCname:  # 找到所有的Cname
                        sqlStr = 'select * from  DNS where NAME = ? and TYPE = ?'
                        value = (item[4], m.queries[0].type)
                        resultTemp = database.fetchall(sqlStr, value)
                        result.append(item)
                        result.extend(resultTemp)
                    if(len(result) <= len(resultCname)):  # 不存在要被找的记录就转发
                        message = self.transform(m)
                        print('类型可以处理，但在数据库中查找不到对应的资源记录')
                        self.relay(message, (ADDR, PORT))
                        return

            # 自己pack包
            print('数据库中查到了对应的资源记录,整个的result表是', result)
            # 整理包
            for item in result:
                # print('the rr:', item[0], item[1], item[2], item[3], item[4])
                rr = database.toRR(item)
                m.addAnswer(rr)
            m.answer = 1
            m.header.anCount = len(result)
            # TODO 改包的header之类的
            message = m.toStr()
            self.relay(message, self.clientAddress)
                
    def handleResponse(self, message, query, header):

        message, addr, timeStamp = self.inverseTransform(message, header)  # 反变换得到ip和时间戳
        # 如果超时就return了,不再转发
        curtime = time()
        if curtime - timeStamp > TIMEOUT:
            return

        print('数据包未超时，转发成功')
        self.relay(message, addr)

        # 之后把包内数据插入或更新到数据库
        if query.type in DEALLIST:
            if header.arCount == 0 and header.nsCount == 0:  # 没有authority和additional字段才缓存, 有的话不缓存包
                m = Message()
                m.fromStr(message)
                print('转化后的数据包ID为', m.header.id)
                for rr in m.answers:    
                    # TODO 放到数据库
                    sqlStr = 'insert into DNS values (?,?,?,?,?)'
                    if rr.type == MX:
                        print(rr.rdata.preference, type(rr.rdata.preference))
                        rdata = str(rr.rdata.preference) + '|' + rr.rdata.name.name.decode('ascii')              
                    elif rr.type == A:
                        rdata = socket.inet_ntoa(rr.rdata.address)
                    else:
                        rdata = rr.rdata.name.name.decode('ascii')
                    value = (rr.name.name.decode('ascii'), rr.type, rr.cls, rr.ttl, rdata)
                    database.fetchall(sqlStr, value)
            else:
                print('存在权威字段和附加字段，不存储数据包到数据库中')
        else:
            print('要处理的类型属于A,CNAME,MX,NS, 不存储数据包到数据库中')

    # ID变换
    def transform(self, m):

        global idTransDict
        global packID

        #id以及dict在各个线程之间要互斥的访问
        idLock.acquire()
        dictLock.acquire()
        idTransDict[packID]=(self.clientAddress, m.header.id, time())
        print('packID is', packID, 'mapping is', idTransDict[packID])
        m.header.id = packID
        packID = self.incID(packID)
        idLock.release()
        dictLock.release()
        return m.toStr()

    # ID反变换
    def inverseTransform(self, message, header):

        global idTransDict
        global packID
        # 检索消息映射
        dictLock.acquire()
        addr, preID, timeStamp = idTransDict[header.id]
        idTransDict.pop(header.id)
        header.id = preID
        dictLock.release()

        # 重写ID
        strio = BytesIO(message)
        strio.seek(0)
        header.encode(strio)

        return strio.getvalue(), addr, timeStamp

    def relay(self, message, addr):
        self.server.socket.sendto(message, addr)
        
    def packMessage(self, message):  # 这里message是参考
        pass

    def unpackMessage(self, message):  # 这里message是拆包对象
        pass

    def incID(self, packID):

        if packID == 65535:
            return 0
        else:
            return packID + 1

if __name__ == "__main__":

    # # 获取命令行参数
    # cmd = sys.argv
    # debug = cmd[1]
    # nameServerAddr = cmd[2]
    # setting = cmd[3]

    idTransDict = {}  # 消息ID转换的字典
    dictLock = threading.Lock()

    packID = 0  # 消息id在各线程之间的产生也要互斥访问
    idLock = threading.Lock()

    database = DNSDataBase(mincached=0, maxcached=0, maxconnections=0, database='DNSDataBase.db')
    # 开启一个线程用作UDP干活,似乎主线程很闲，没必要这么做哦
    with UDPServer((CLIENT, 53), DnsHandler) as dnsServer:
        serverThread = threading.Thread(target = dnsServer.server_forever)
        serverThread.daemon = True
        serverThread.start()
        print('DnsServer is runnng in thread', serverThread.name , serverThread.ident)

        while True:
            1 == 2 