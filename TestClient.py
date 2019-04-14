from socket import * 

if __name__ == "__main__":
    addr = ('10.3.9.5', 53)
    testClient = socket(AF_INET, SOCK_DGRAM,0)
    while True:
        inp = input('数据：').strip()
        if inp == 'exit':
            break
        testClient.sendto(bytes(inp, encoding = "utf-8"), addr)
        testClient.sendto(bytes(inp, encoding = "utf-8"), addr)
        testClient.sendto(bytes(inp, encoding = "utf-8"), addr)
        
        data, address = testClient.recvfrom(1024)
        print('recv {}'.format(data.decode()))
    testClient.close()