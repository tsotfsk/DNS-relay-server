import socket
import sys
import DnsMessage
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
def testEncodeAReocord():
    testRR = DnsMessage.ResourceRecord(b'www.baidu.com', DnsMessage.A, DnsMessage.IN, 0, '127.0.0.1')
    strio = BytesIO()
    testRR.encode(strio)
    print(strio.getvalue())


# Arecord拆包测试
def testDecodeARecord():
    pass

# MXrecord


# response包封包测试
def  testEncodeResp():
    pass
    
if __name__ == "__main__":
    testEncodeAReocord()
    
        