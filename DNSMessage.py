import struct
from io import BytesIO
import sys, socket

# 端口
PORT = 53

# Opcode
QUERY, IQUERY, STATUS = range(3)

# RCODE
OK, FROMATERROR, SERVERERROR, NAMEERROR, UNDEFINITION, REFUSE = range(6)

# QTYPE
A, NS, MD, MF, CNAME, SOA, MB, MG, MR, NULL, WKS, PTR, HINFO, MINFO, MX, TXT = range(1, 17)
IXFR, AXFR, MAILB, MAILA, ALLRECORDS = range(251, 256)

# QCLASS
IN, CS, CH, HS, ALLCLASS = range(1, 6)

# 调用函数时用
# recordTypes = {}
# for name in globals():
#     if name.startswith('Record'):
#         recordTypes[globals()[name].type] = globals()[name]

class Message:
    """
    All communications inside of the domain protocol are carried in a single
    format called a message.  The top level format of message is divided
    into 5 sections (some of which are empty in certain cases) shown below:

    +---------------------+
    |        Header       |
    +---------------------+
    |       Question      | the question for the name server
    +---------------------+
    |        Answer       | RRs answering the question
    +---------------------+
    |      Authority      | RRs pointing toward an authority
    +---------------------+
    |      Additional     | RRs holding additional information
    +---------------------+
    """

    def __init__(self, header):
        self.header = header
        self.queries = []
        self.answers = []
        self.authority = []
        self.additional = []

    def encode(self, strio):
        self.header.encode(strio)
        nameDict = {}
        for query in self.queries:
            query.encode(strio)

        for rr in self.answers:
            rr.encode(strio, nameDict)

        for rr in self.authority:
            rr.encode(strio, nameDict)

        for rr in self.additional:
            rr.encode(strio, nameDict)

    def decode(self, strio, length=None):
        self.header = Header()
        self.header.decode(strio)
        for i in range(self.header.qdCount):
            q = Query()
            q.decode(strio)
            self.queries.append(q)

        for i in range(self.header.anCount):
            rr = ResourceRecord()
            rr.decode(strio)
            self.answers.append(q)

        for i in range(self.header.anCount):
            rr = ResourceRecord()
            rr.decode(strio)
            self.answers.append(q)

        for i in range(self.header.anCount):
            rr = ResourceRecord()
            rr.decode(strio)
            self.answers.append(q)

    def addQuery(self, query):
        self.queries.append(query)

    def toStr(self):
        strio = BytesIO()
        self.encode(strio)
        return strio.getvalue()

    def fromStr(self, str):
        strio = BytesIO(str)
        self.decode(strio)

class Query:
    """
                                      1  1  1  1  1  1
      0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                                               |
    /                     QNAME                     /
    /                                               /
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                     QTYPE                     |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                     QCLASS                    |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    """

    def __init__(self, name=b'', type=A, cls=IN):
        self.name = Name(name)
        self.type = type
        self.cls = cls

    def encode(self, strio):
        self.name.encode(strio)
        strio.write(struct.pack('!HH', self.type, self.cls))

    def decode(self, strio):
        self.name.decode(strio)
        self.type, self.cls = struct.unpack('!HH', strio.read(4))


class Header:
    """
                                    1  1  1  1  1  1
      0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                      ID                       |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |QR|   Opcode  |AA|TC|RD|RA|   Z    |   RCODE   |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                    QDCOUNT                    |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                    ANCOUNT                    |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                    NSCOUNT                    |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                    ARCOUNT                    |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    """

    fmt = '!H2B4H'  # 按照2bytes,2*byte,4bytes的网路字节序构造header
    size = struct.calcsize(fmt)

    def __init__(self, id=0, answer=0, opCode=0, recDes=0,
                 recAv=0, authority=0, rCode=OK, trunc=0,
                 qdCount=0, anCount=0, nsCount=0, arCount=0):

        self.id = id
        self.answer = answer
        self.opCode = opCode
        self.authority = authority
        self.trunc = trunc
        self.recDes = recDes
        self.recAv = recAv
        self.rCode = rCode
        self.qdCount = qdCount
        self.anCount = anCount
        self.nsCount = nsCount
        self.arCount = arCount

    def encode(self, strio):
        byte3 = ( (self.answer & 1) << 7 
                | (self.opCode & 15) << 3 
                | (self.authority & 1) << 2 
                | (self.trunc & 1) << 1
                | self.recDes & 1)
        byte4 = ( (self.recAv & 1) << 7 
                | self.rCode & 15)
        strio.write(struct.pack(Header.fmt, self.id, byte3, byte4, self.qdCount, self.anCount, self.nsCount, self.arCount))

    def decode(self, strio):
        header = strio.read(Header.size)
        r = struct.unpack(Header.fmt, header)
        self.id, byte3, byte4, self.qdCount, self.anCount, self.nsCount, self.arCount = r
        self.answer = (byte3 >> 7) & 1
        self.opCode = (byte3 >> 3) & 15
        self.authority = (byte3 >> 2) & 1
        self.trunc = (byte3 >> 1) & 1
        self.recDes = byte3 & 1
        self.recAv = (byte4 >> 7) & 1
        self.rCode = byte4 & 15


class Name:
    """
        域名的类
    """

    def __init__(self, name=b''):
        self.name = name

    def encode(self, strio, nameDict=None):
        """
            eg: www.baidu.com ----> b'\x03www\x05baidu\x03com\x00'

            如果name在前面出现过，则通过\xc000 | name在strio的位置来表示name

            比如query中询问的是www.baidu.com 那么在response包中answer字段会出现\xc00c来代替
        """
        # 通过将name放到dict中来缩减包所占的空间
        name = self.name
        while name:
            if nameDict is not None:
                if name in nameDict:
                    strio.write(struct.pack('!H', 0xc000 | nameDict[name]))  # 0xc0是指针，后面14位是偏移量
                    return
                nameDict[name] = strio.tell() + Header.size
            ind = name.find(b'.')
            if ind > 0:  # 不是最后一段
                label, name = name[:ind], name[ind + 1:]
            else:
                label = name
                name = None
                ind = len(label)
            strio.write(bytes([ind]))
            strio.write(label)

        strio.write(b'\x00')  # 结束的标志

    def decode(self, strio, length=None):
        """
            把name从报文中解析出来
            eg:b'\x03www\x05baidu\x03com\x00 -----> www.baidu.com
        """

        self.name = b''
        pos = 0
        while 1:
            l = ord(strio.read(1))
            if l == 0:  # 读到名字结束了 
                if pos > 0:  # 返回原来位置
                    strio.seek(pos)
                return 
            # 遇到指针的处理
            if l >> 6 == 3:  # 遇到0xc0则后面会紧跟一个偏移量
                offset = (l & 63) << 8 | ord(strio.read(1)) # 得到14位偏移量 
                if pos == 0:
                    pos = strio.tell()  # 记录当前位置
                strio.seek(offset)
                continue
            # 以下是遇到名字的处理
            label = strio.read(l)
            if self.name == b'':
                self.name = label
            else:
                self.name = self.name + b'.' + label

    def __str__(self):  # 方便测试输出
        return self.name.decode('ascii')


class ResourceRecord:
    """
                                    1  1  1  1  1  1
      0  1  2  3  4  5  6  7  8  9  0  1  2  3  4  5
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                                               |
    /                                               /
    /                      NAME                     /
    |                                               |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                      TYPE                     |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                     CLASS                     |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                      TTL                      |
    |                                               |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    |                   RDLENGTH                    |
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--|
    /                     RDATA                     /
    /                                               /
    +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
    """
    headFmt = '!2HIH'
    headSize = struct.calcsize(headFmt)

    def __init__(self, name=b'', type=A, cls=IN, ttl=0, rdata=None):
        self.name = Name(name)
        self.type = type
        self.cls = cls
        self.ttl = ttl
        if self.type == A and rdata is not None:
            self.rdata = RecordA(rdata)
        else:
            pass

    def encode(self, strio, nameDict=None):
        self.name.encode(strio, nameDict)
        strio.write(struct.pack(ResourceRecord.headFmt, self.type, self.cls, self.ttl, 0))
        begin = strio.tell()  # 记录此时的位置
        self.rdata.encode(strio)
        end = strio.tell()  # 记录写完数据时的位置
        strio.seek(begin - 2)  
        strio.write(struct.pack('!H',end - begin)) #
        strio.seek(end)

    def decode(self, strio, nameDict=None):
        self.name.decode(strio, nameDict)
        self.type, self.cls, self.ttl, self.rdlength = struct.unpack(ResourceRecord.headFmt, strio.read(ResourceRecord.headSize))
        if self.type == A:
            self.rdata = RecordA()
            self.rdata.decode(strio)

class RecordA:
    """
        A记录主要记录一个域名
    """
    typ = A
    def __init__(self, address='0.0.0.0'):
        address = socket.inet_aton(address)  # 将字符串的ip地址转化为网络字节序的ip 
        self.address = address

    def encode(self, strio):
        strio.write(self.address)

    def decode(self, strio):
        address = strio.read(4)
        # self.address = socket.inet_ntoa(address)


class RecordMX:
    """
        Mail exchange.
    """
    typ = MX

    def __init__(self, preference=0, name=b'', **kwargs):
        self.preference = int(preference)
        self.name = Name(kwargs.get('exchange', name))

    def encode(self, strio, nameDict=None):
        strio.write(struct.pack('!H', self.preference))
        self.name.encode(strio, nameDict)

    def decode(self, strio, length=None):
        self.preference = struct.unpack('!H', readPrecisely(strio, 2))[0]
        self.name = Name()
        self.name.decode(strio)


class RecordNS:

    typ =  NS
    def __init__(self):
        pass


class RecordCNAME:

    typ = CNAME
    def __init__(self):
        pass