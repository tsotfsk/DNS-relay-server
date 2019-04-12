import socket
import sys
 DnsMessage
from io import BytesIO

# message封包测试
def testEncodeMessage():
    pass

# message拆包测试
def testDecodeMessage():
    pass

# header封包测试
def testEncodeHeader():
    pass

# header拆包测试
def testDecodeHeader():
    pass

# query封包测试
def testEncodeQuery():
    pass

# query拆包测试
def testDecodeQuery():
    pass

# name封包测试
def testEncodeName():
    pass

# name拆包测试
def testDecodeNmae():
    pass

# Arecord封包测试
def testEncodeARecord():
    testRR = DnsMessage.ResourceRecord(b'www.baidu.com', DnsMessage.A, DnsMessage.IN, 0, '127.0.0.1')
    strio = BytesIO()
    testRR.encode(strio)
    print(strio.getvalue())


# Arecord拆包测试
def testDecodeARecord():
    record = b'\x03www\x05baidu\x03com\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x04\x7f\x00\x00\x01'
    strio = BytesIO(record)
    testRR = DnsMessage.ResourceRecord()
    testRR.decode(strio)
    print(testRR.name, testRR.cls, testRR.type, testRR.ttl, testRR.rdlength, testRR.rdata.address)

# MXrecord


# response包封包测试
def  testEncodeResp():
    pass
    
if __name__ == "__main__":
    testDecodeARecord()
    
        