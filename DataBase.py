import sqlite3
import logging
from DBUtils.PooledDB import PooledDB
from DNSMessage import *
sqlite3.threadsafety = 2

class DataBase:
    
    def __init__(self, mincached, maxcached, maxconnections, database):

        self.linkPoll = PooledDB(sqlite3, mincached=mincached, maxcached=maxcached, 
                                          maxconnections=maxconnections, blocking=True, database=database, check_same_thread=False) 
        self.create()

    def open(self):
        conn = self.linkPoll.connection(shareable=False)
        cursor = conn.cursor()
        return conn, cursor

    def close(self, conn, cursor):
        cursor.close()
        conn.commit()
        conn.close()

    def fetchall(self, sqlStr, value):
        conn, cursor = self.open()
        try:
            cursor.execute(sqlStr, value)
            result = cursor.fetchall()
        except Exception as e:
            logging.error(e)
            result=[]
        self.close(conn, cursor)
        return result
    
    def create(self):
        pass

class DNSDataBase(DataBase):

    # def __init__(self, mincached, maxcached, maxconnections, database):
    #     DataBase.__init__(self, mincached, maxcached, maxconnections, database)

    # 数据库创建操作
    def create(self):
        conn, cursor = self.open()
        # XXX: 由于sqlite3支持的数据类型只有五种,可能不是一个很好的选择，比如其无法识别UNSIGNED，依旧可以插入负数，所以后面做了一些小小的限制
        try:
            cursor.execute('''CREATE TABLE DNS
                (
                NAME            TEXT            NOT NULL,
                TYPE        SMALLINT            CHECK(TYPE >= 0 AND TYPE <= 65535),
                CLASS       SMALLINT            CHECK(CLASS >= 0 AND CLASS <= 65535),
                TTL              INT            CHECK(TTL >= 0),
                RDATA           TEXT            NOT NULL,
                PRIMARY KEY     (NAME, TYPE, CLASS, RDATA));''')
        except Exception as e:
            logging.error(e)
    
        self.close(conn, cursor)

    # 书库读取的一行转化为资源记录
    def toRR(self, item):
        if item[1] == A:
            rr =  ResourceRecord(item[0].encode('ascii'), item[1], item[2], item[3], address=item[4])
        elif item[1] == CNAME:
            rr = ResourceRecord(item[0].encode('ascii'), item[1], item[2], item[3], cname=item[4].encode('ascii'))
        elif item[1] == NS:
            rr = ResourceRecord(item[0].encode('ascii'), item[1], item[2], item[3], nname=item[4].encode('ascii'))
        elif item[1] == MX:
            rList = item[4].split('|')
            rr =  ResourceRecord(item[0].encode('ascii'), item[1], item[2], item[3], preference=int(rList[0]), exchange=rList[1].encode('utf-8'))
        return rr

if __name__ == "__main__":
    database = DNSDataBase(mincached=0, maxcached=0, maxconnections=10, database='DNSDataBase.db')
    rr = database.toRR(('www.baidu.com', CNAME, IN, 201, 'www.a.fen.com'))
    