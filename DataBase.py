import sqlite3
import logging
from DBUtils.PooledDB import PooledDB
from DNSMessage import *
from time import time

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
        except:
            try:
                if 'insert' in sqlStr: # 插入出错，也就是不满足完整性约束，那么就采取更新的策略
                    newSqlStr = 'update DNS set TTL = ? , RDATA = ?, TIMESTAMP = ? where Name = ? and TYPE = ? and CLASS = ? and RDATA = ?'
                    newValue = (value[3], value[4], value[5], value[0], value[1], value[2], value[4])
                    cursor.execute(newSqlStr, newValue)
                    result = cursor.fetchall()
                else:
                    result=[]
            except Exception as e:
                result = []
                logging.error(e)
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
                TIMESTAMP     DOUBLE            CHECK(TIMESTAMP > 0),
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

    def selectRR(self, curtime, sqlStr, value):
        '''
            自带删除的查询
        '''
        result = self.fetchall(sqlStr, value)
        resultTemp = result[:]
        for item in resultTemp:
            if item[3] + item[5] < curtime:
                self.deleteRR(item)
                result.remove(item)
                logging.debug('删除了一个资源记录{}'.format(tuple(item)))
        return result

    def deleteRR(self, item):
        '''
            主要是删除已经过期的消息
        '''
        sqlStr = 'delete from DNS where Name = ? and TYPE = ? and CLASS = ? and TTL = ? and RDATA = ? and TIMESTAMP = ?'
        value = tuple(item)
        self.fetchall(sqlStr, value)

if __name__ == "__main__":
    database = DNSDataBase(mincached=0, maxcached=0, maxconnections=10, database='DNSDataBase.db')
    rr = database.toRR(('www.baidu.com', CNAME, IN, 201, 'www.a.fen.com'))

    