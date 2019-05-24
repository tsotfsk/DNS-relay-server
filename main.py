import argparse
import logging
import threading
from time import time

from database import *
from message import *
from udpserver import *


class DnsHandler(BaseRequestHandler):

    def handle(self):
        message = self.request[0]
        try:
            # 看看包头
            strio = BytesIO(message)
            header =  Header()
            header.decode(strio)

            # 看看查询
            query = Query()
            query.decode(strio)
        except Exception as e:
            logging.error(e)
            return
        
        # 看在不在屏蔽表里
        if query.type == A:
            # print(query.name.name.decode('ascii'), query.type )
            if self.isShield(query.name.name.decode('ascii')):
                logging.debug('请求域名{}存在于屏蔽表中,拒绝访问'.format(query.name))
                header.answer = 1
                header.rCode = 3
                strio = BytesIO(message)
                strio.seek(0)
                header.encode(strio)
                self.relay(strio.getvalue(), self.clientAddress)
                return

        if header.answer == 0:  # 查询包
            logging.info('收到来自{}的请求报文，请求报文消息ID:{},查询域名:{},查询类型:{}'.format(
                        self.clientAddress, header.id, query.name, TYPEDICT[query.type]))
            self.handleRequest(message)         
        else:  # 应答包
            logging.info('收到来自{}的响应报文，响应报文消息ID:{},查询域名:{},查询类型:{}'.format(
                        self.clientAddress, header.id, query.name, TYPEDICT[query.type]))
            self.handleResponse(message, query, header)

    def handleRequest(self, message):

        '''请求报文的处理'''
        m = Message()
        m.fromStr(message)
        curtime = time()
        if m.queries[0].type not in DEALLIST: # 无法处理的类型就转发
            message = self.transform(m)  # 消息id转换
            logging.debug('请求消息不在可处理范围内,转发数据包到DNS服务器')
            self.relay(message, (argDict['dns_server_ipaddr'], PORT))  # 转发
        else:
            # 查找数据库中是否有对应记录
            sqlStr = 'select * from  DNS where NAME = ? and TYPE = ?'
            value = (m.queries[0].name.name.decode('ascii'), m.queries[0].type)
            result = database.selectRR(curtime, sqlStr, value)  
            
            if len(result) == 0:  # 查不到结果就查CNAME
                resultCname = []
                if(m.queries[0].type != CNAME):  # 当请求不是CNAME的时候才去查CNAME
                    sqlStr = 'select * from  DNS where NAME = ? and TYPE = ?'
                    value = (m.queries[0].name.name.decode('ascii'), CNAME)
                    resultCname = database.selectRR(curtime, sqlStr, value)

                # CNAME也没查到就转发了
                if len(resultCname) == 0:
                    message = self.transform(m)
                    logging.debug('类型可以处理，但在数据库中查找不到对应的资源记录')
                    self.relay(message, (argDict['dns_server_ipaddr'], PORT))
                    return
                else:
                    result = []
                    for item in resultCname:  # 找到所有的Cname
                        sqlStr = 'select * from  DNS where NAME = ? and TYPE = ?'
                        value = (item[4], m.queries[0].type)
                        resultTemp = database.selectRR(curtime, sqlStr, value)
                        if len(resultTemp) > 0:  # 只有对应的cname查找到了对应的记录才会加入结果列表中 
                            result.append(item)
                            result.extend(resultTemp)
                    if len(result) <= len(resultCname):  # 不存在要被找的记录就转发
                        message = self.transform(m)
                        logging.debug('类型可以处理，但在数据库中查找不到对应的资源记录')
                        self.relay(message, (argDict['dns_server_ipaddr'], PORT))
                        return

            # 自己pack包
            logging.debug('数据库中查到了对应的资源记录')
            for item in result:
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
            logging.debug('数据包超时,不做转发')
            return

        logging.debug('数据包未超时')
        self.relay(message, addr)

        # 之后把包内数据插入或更新到数据库
        if query.type in DEALLIST:
            if header.arCount == 0 and header.nsCount == 0:  # 没有authority和additional字段才缓存, 有的话不缓存包
                m = Message()
                m.fromStr(message)
                for rr in m.answers:    
                    # TODO 放到数据库
                    sqlStr = 'insert into DNS values (?,?,?,?,?,?)'
                    if rr.type == MX:
                        rdata = str(rr.rdata.preference) + '|' + rr.rdata.name.name.decode('ascii')              
                    elif rr.type == A:
                        rdata = socket.inet_ntoa(rr.rdata.address)
                    else:
                        rdata = rr.rdata.name.name.decode('ascii')
                    value = (rr.name.name.decode('ascii'), rr.type, rr.cls, rr.ttl, rdata, curtime)
                    database.fetchall(sqlStr, value)
            else:
                pass
                logging.debug('存在权威字段和附加字段, 不存储资源记录到数据库中')
        else:
            pass
            logging.debug('要处理的类型不属于A,CNAME,MX,NS, 不存储相关资源记录到数据库中')

    # ID变换
    def transform(self, m):

        global idTransDict
        global packID

        #id以及dict在各个线程之间要互斥的访问
        idLock.acquire()
        dictLock.acquire()
        idTransDict[packID]=(self.clientAddress, m.header.id, time())
        # print('packID is', packID, 'mapping is', idTransDict[packID])
        m.header.id = packID
        packID = self.incID(packID)
        idLock.release()
        dictLock.release()
        return m.toStr()

    # ID反变换
    def inverseTransform(self, message, header):

        global idTransDict

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
        logging.debug('转发成功，目标地址是:{}'.format(addr))

    def incID(self, packID):

        if packID == 65535:
            return 0
        return packID + 1

    def isShield(self, name):

        sqlStr = 'select RDATA from  DNS where NAME = ? AND TYPE = ?'
        value = (name, A)
        result = database.fetchall(sqlStr, value)
        # print('查询屏蔽表的结果是', result)
        if len(result) > 0:
            for item in result:
                # print('查找的屏蔽表IP', item[0])
                if item[0] == '0.0.0.0':
                    return True
        return False

def getOpt():

    # 获取命令行参数
    parser = argparse.ArgumentParser(prog="dns-relay-server")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-dd', action='store_true', help='调试信息级别1(仅输出时间坐标，序号，客户端IP地址，查询的域名)')
    group.add_argument('-d', action='store_true', help='调试信息级别2(输出冗长的调试信息)')
    parser.add_argument('dns_server_ipaddr', nargs='?', default='10.9.3.4', help='指定的名字服务器')
    parser.add_argument('filename', nargs='?', default='dnslog.log', help='指定的日志文件')

    # 得到参数字典
    args = parser.parse_args()
    argDict = vars(args)
    return argDict

if __name__ == "__main__":

    # 获取并识别命令行参数
    argDict = getOpt()

    if argDict['d']:  # 输出INFO级别以及以上的信息
        logging.basicConfig(level=logging.INFO,
                            # filename=argDict['filename'],
                            format='%(asctime)s - %(levelname)s: %(message)s')
    elif argDict['dd']:  # 输出DEBUG级别以及以上的信息
        logging.basicConfig(level=logging.DEBUG,
                            # filename=argDict['filename'],
                            format='%(asctime)s - %(filename)s[line:%(lineno)d][%(threadName)s] - %(levelname)s: %(message)s')
    else:
        logging.basicConfig()

    # id转换表各线程之间要互斥访问
    idTransDict = {}  # 消息ID转换的字典
    dictLock = threading.Lock()

    # 转化id递增生成，线程之间也要互斥访问
    packID = 0  
    idLock = threading.Lock()
    
    # 实例化一个带连接池的数据库，支持最大20各连接，初始生成5个连接，最大空闲连接数量是10
    database = DNSDataBase(mincached=5, maxcached=10, maxconnections=20, database='dns.db')

    # 在主线程启动UDPAsyncServer
    with UDPServer(('0.0.0.0', 53), DnsHandler) as dnsServer:
        logging.info('DNS中继服务器启动于线程:{},当前活跃线程数:{}'.format(threading.current_thread().ident, threading.active_count()))
        dnsServer.serverForever()
