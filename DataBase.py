import sqlite3
import queue
from DBUtils.PooledDB import PooledDB
sqlite3.threadsafety = 2
class DNSDataBase:
    
    def __init__(self, database, mincached, maxcached, maxconnections):
        self.linkPoll = PooledDB(sqlite3, mincached=mincached, maxcached=maxcached, 
                                          maxconnections=maxconnections, blocking=True, database=database, check_same_thread=False)                               
        try:
            self.create()
        except Exception as e:
            # TODO 加入调试信息范畴
            pass

    def open(self):
        conn = self.linkPoll.connection(shareable=False)
        cursor = conn.cursor()
        return conn, cursor

    def close(self, conn, cursor):
        conn.commit()
        cursor.close()
        conn.close()

    def fetchall(self, sqlStr, value):
        conn, cursor = self.open()
        try:
            cursor.execute(sqlStr, value)
            result = cursor.fetchall()
        except Exception as e:
            print(e)
            return
        self.close(conn, cursor)
        return result

    # 数据库创建操作
    def create(self):
        conn, cursor = self.open()
        # XXX: 由于sqlite3支持的数据类型只有五种,可能不是一个很好的选择，比如其无法识别UNSIGNED，依旧可以插入负数，所以后面做了一些小小的限制
        cursor.execute('''CREATE TABLE DNS
            (
            NAME            TXET            NOT NULL,
            TYPE        SMALLINT            CHECK(TYPE >= 0 AND TYPE <= 65535),
            CLASS       SMALLINT            CHECK(TYPE >= 0 AND TYPE <= 65535),
            TTL              INT            CHECK(TTL >= 0),
            RDLENGTH    SMALLINT            CHECK(RDLENGTH >=0 AND RDLENGTH <= 65535),
            RDATA           TEXT            NOT NULL,
            PRIMARY KEY     (NAME, TYPE, CLASS, RDLENGTH, RDATA));''')
        self.close(conn, cursor)

if __name__ == "__main__":
    database = DNSDataBase(mincached=2, maxcached=5, maxconnections=10, database='DNSDataBase.db')