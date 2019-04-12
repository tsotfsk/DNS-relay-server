import sqlite3
import queue

# class DatabaseLinkPool:

#     def __init__(self, database, count = 20):
#         self.database = database
#         self.count = count
#         self._queue = queue.Queue(count)
#         for i in range(count):
#             dbLink = sqlite3.connect('DnsDataBase.db')
#             self._queue.put(dbLink)

#     def getDbLink(self):
#         if self._queue.get(block = False):


#     def __enter__(self):

def selectDB(sqlStr, value):
    conn = sqlite3.connect('DnsDataBase.db')
    print ("Opened database successfully")
    c = conn.cursor()
    c.execute(sqlStr,value)
    print("Table DnsDataBase selected successfully")
    conn.commit()
    result = c.fetchall()  
    conn.close()
    return result

#数据库插入操作
def insertDB(sqlStr,value):
    conn = sqlite3.connect('DnsDataBase.db')
    c = conn.cursor()
    c.execute(sqlStr,value)
    print("Table DnsDataBase inserted successfully")
    conn.commit()
    conn.close()

#数据库创建操作
def createDB():
    conn = sqlite3.connect('DnsDataBase.db')
    print ("Opened database successfully")
    c = conn.cursor()
    # XXX: 由于sqlite3支持的数据类型只有五种,可能不是一个很好的选择，比如其无法识别UNSIGNED，依旧可以插入负数，所以后面做了一些小小的限制
    c.execute('''CREATE TABLE DNS
        (
        NAME            TXET            NOT NULL,
        TYPE        SMALLINT            CHECK(TYPE >= 0 AND TYPE <= 65535),
        CLASS       SMALLINT            CHECK(TYPE >= 0 AND TYPE <= 65535),
        TTL              INT            CHECK(TTL >= 0),
        RDLENGTH    SMALLINT            CHECK(RDLENGTH >=0 AND RDLENGTH <= 65535),
        RDATA           TEXT            ,
        PRIMARY KEY     (NAME, TYPE, CLASS, TTL, RDLENGTH, RDATA));''')
    print("Table DNS created successfully")
    conn.commit()
    conn.close()


#更新数据库
def updateDB(sqlStr, value):
    conn = sqlite3.connect('DnsDataBase.db')
    print ("Opened database successfully")
    c = conn.cursor()
    c.execute(sqlStr, value)
    conn.commit()
    conn.close()
    print("Table DnsDataBase updated successfully")

#删除内容
def deleteDB(sqlStr, value):
    conn = sqlite3.connect('DnsDataBase.db')
    print ("Opened database successfully")
    c = conn.cursor()
    c.execute(sqlStr, value)
    conn.commit()
    conn.close()
    print("Table DnsDataBase deleted successfully")

if __name__ == "__main__":
    createDB()