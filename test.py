import sys
from io import BytesIO
import socket
from time import monotonic as time

from DNSMessage import *
from UDPAsyncServer import *


# message的request封包测试
def testEncodeRequestMessage():
    h = Header(id=0x9ace, answer=0, opCode=0, recDes=0,
               recAv=1, authority=0, rCode=OK, trunc=0,
               qdCount=1, anCount=0, nsCount=0, arCount=0)
    q = Query(b'www.baidu.com', A, IN)
    m = Message(h)
    m.addQuery(q)
    strio = BytesIO()
    m.encode(strio)
    print(strio.getvalue())
    return m

# message的request拆包测试
def testDecodeRequestMessage():
    m = Message()
    message = b'\x9a\xce\x00\x80\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x05baidu\x03com\x00\x00\x01\x00\x01'
    strio = BytesIO(message)
    m.decode(strio)
    print(m.header.id, m.header.answer, m.header.opCode, m.header.recDes, 
          m.header.recAv, m.header.authority, m.header.rCode, m.header.trunc,
          m.header.qdCount, m.header.anCount, m.header.nsCount, m.header.arCount)
    print(m.queries[0].name, m.queries[0].type, m.queries[0].cls)

# message的response包封包测试
def testEncodeResponseMessage():
    h = Header(id=0x9ace, answer=1, opCode=0, recDes=0,
               recAv=1, authority=0, rCode=OK, trunc=0,
               qdCount=1, anCount=1, nsCount=0, arCount=0)
    q = Query(b'www.baidu.com', A, IN)
    rr = ResourceRecord(b'www.baidu.com', A, IN, 201, address='127.0.0.1')
    m = Message(h)
    m.addQuery(q)
    m.addAnswer(rr)
    strio = BytesIO()
    m.encode(strio)
    print(strio.getvalue())
    return m

# message的response包拆包测试
def testDecodeResponseMessage():
    m = Message()
    message = b'\x9a\xce\x80\x80\x00\x01\x00\x01\x00\x00\x00\x00\x03www\x05baidu\x03com\x00\x00\x01\x00\x01\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\xc9\x00\x04\x7f\x00\x00\x01'
    strio = BytesIO(message)
    m.decode(strio)
    print(m.header.id, m.header.answer, m.header.opCode, m.header.recDes, 
        m.header.recAv, m.header.authority, m.header.rCode, m.header.trunc,
        m.header.qdCount, m.header.anCount, m.header.nsCount, m.header.arCount)
    print(m.queries[0].name, m.queries[0].type, m.queries[0].cls)
    print(m.answers[0].name, m.answers[0].cls, m.answers[0].type, m.answers[0].ttl, m.answers[0].rdlength, m.answers[0].rdata.address)

# header封包测试
def testEncodeHeader():
    h = Header(id=0x9ace, answer=0, opCode=0, recDes=0,
               recAv=1, authority=0, rCode=OK, trunc=0,
               qdCount=1, anCount=0, nsCount=0, arCount=0)
    strio = BytesIO()
    h.encode(strio)
    print(strio.getvalue())

# header拆包测试
def testDecodeHeader():
    h = Header()
    header = b'\x9a\xce\x00\x80\x00\x01\x00\x00\x00\x00\x00\x00'
    strio = BytesIO(header)
    h.decode(strio)
    print(h.id, h.answer, h.opCode, h.recDes, h.recAv, h.authority, h.rCode, h.trunc, h.qdCount, h.anCount, h.nsCount, h.arCount)

# query封包测试
def testEncodeQuery():
    q = Query(b'www.baidu.com', A, IN)
    strio = BytesIO()
    q.encode(strio)
    print(strio.getvalue())

# query拆包测试
def testDecodeQuery():
    query = b'\x03www\x05baidu\x03com\x00\x00\x01\x00\x01'
    q = Query()
    strio = BytesIO(query)
    q.decode(strio)
    print(q.name, q.type, q.cls)

# name封包测试
def testEncodeName():
    name = b'www.baidu.com'
    n = Name(name)
    strio = BytesIO()
    nameDict = {}
    n.encode(strio, nameDict)  # 测试名字未在dict中出现
    n.encode(strio, nameDict)  # 测试名字在dict中出现
    print(strio.getvalue())


# name拆包测试
def testDecodeName():
    name = b'\x03www\x05baidu\x03com\x00'
    n = Name()
    strio = BytesIO(name)
    n.decode(strio)
    print(n.name)

# Arecord封包测试
def testEncodeARecord():
    testRR = ResourceRecord(b'www.baidu.com', A, IN, 0, address='127.0.0.1')
    strio = BytesIO()
    testRR.encode(strio)
    print(strio.getvalue())


# Arecord拆包测试
def testDecodeARecord():
    record = b'\x03www\x05baidu\x03com\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x04\x7f\x00\x00\x01'
    strio = BytesIO(record)
    testRR = ResourceRecord()
    testRR.decode(strio)
    print(testRR.name, testRR.cls, testRR.type, testRR.ttl, testRR.rdlength, testRR.rdata.address)

# MXrecord

# request包发送测试
def testSendRequest():
    strio = BytesIO()
    m = testEncodeRequestMessage()
    m.encode(strio)
    addr = ('127.0.0.1', 60000)
    testClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    testClient.sendto(strio.getvalue(), addr)
    testClient.close()

# request包接收测试
def testRecvRequest():
    '''
        sendRequest的结果发往本地拆包，在TestServer中被拆包
    '''
    pass

# response包发送测试
def testSendResponse():
    strio = BytesIO()
    m = testEncodeResponseMessage()
    m.encode(strio)
    addr = ('123.125.81.6', PORT)
    testClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    testClient.sendto(strio.getvalue(), addr)
    testClient.close()

# response包接收测试
def testRecvResponse():
    '''
        sendRequest的结果发往本地拆包，在TestServer中被拆包
    '''
    pass

# testUDPAsyncServer 测试并发性
def testConcurrency():
    strio = BytesIO()
    m = testEncodeRequestMessage()
    m.encode(strio)
    addr = ('10.201.8.53', 60000)
    testClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 连续发100次测试，观察活跃线程数来测试并发效果
    for i in range(1):
        testClient.sendto(strio.getvalue(), addr)
    testClient.close()

if __name__ == "__main__":
    testConcurrency()