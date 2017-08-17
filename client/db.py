# -*- coding: utf-8-*-
import os
import sqlite3
import tushare as ts
import time


class DB:
    def __init__(self):
        """
       
        """
        self.db_file = 'data.db'
        
        self.stock_basics_table = 'stock_basics'
        if not self.is_table_exist('stock_watch'):
            with sqlite3.connect(self.db_file) as conn:
                conn.text_factory = str
                cursor = conn.cursor()
                create_table_sql = "CREATE TABLE stock_watch (\
                                   code varchar(20) primary key,\
                                   name varchar(20) NOT NULL,\
                                   lastmodify varchar(32) DEFAULT NULL\
                                 )"
                cursor.execute(create_table_sql)
                conn.commit()


    def __del__(self):
        pass

    def is_need_update(self):
        return not self.is_table_exist(self.stock_basics_table)
    
    def is_table_exist(self, name):
        with sqlite3.connect(self.db_file) as conn:
            conn.text_factory = str
            cursor = conn.cursor()
            cursor.execute("select count(*) as 'count' from sqlite_master where type ='table' and name = ?", (name,))
            res = cursor.fetchall()
            return res[0][0]!=0

    def updata_stock_basics(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.text_factory = str
            stock_basics = ts.get_stock_basics()
            stock_basics.to_sql(self.stock_basics_table, conn, if_exists='replace')

    def get_stock_name(self, code):
        with sqlite3.connect(self.db_file) as conn:
            conn.text_factory = str
            cursor = conn.cursor()
            cursor.execute('select name, code  from stock_basics where code = ?', (code,))
            res = cursor.fetchall()
            if len(res)>0:
                return res[0][0]
            return None
            

    def get_stock_code(self,name):
        with sqlite3.connect(self.db_file) as conn:
            conn.text_factory = str
            cursor = conn.cursor()
            cursor.execute('select name, code  from stock_basics where name = ?', (name,))
            res = cursor.fetchall()
            if len(res)>0:
                return res[0][1]
            return None

    def add_notify(self, code, name):
        with sqlite3.connect(self.db_file) as conn:
            conn.text_factory = str
            cursor = conn.cursor()
            cursor.execute('insert into stock_watch values(?, ?, NULL)', (code, name,))
            conn.commit()


    def remove_notify(self, code):
        with sqlite3.connect(self.db_file) as conn:
            conn.text_factory = str
            cursor = conn.cursor()
            cursor.execute('delete from stock_watch where code = ?', (code,))
            conn.commit()
    
    def update_notify(self, code, dt):
        with sqlite3.connect(self.db_file) as conn:
            conn.text_factory = str
            cursor = conn.cursor()
            cursor.execute('update stock_watch set lastmodify = ? where code = ? ', (dt, code,))
            conn.commit()
    
    def check_notify(self, code):
        with sqlite3.connect(self.db_file) as conn:
            conn.text_factory = str
            cursor = conn.cursor()
            cursor.execute('select code  from stock_watch where code = ?', (code,))
            res = cursor.fetchall()
            if len(res) > 0:
                return True
            return False


    def get_notify_list(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.text_factory = str
            cursor = conn.cursor()
            cursor.execute('select code, lastmodify  from stock_watch')
            res = cursor.fetchall()
            v = {}
            v["codelist"] = []
            v["lastmodifylist"] = []
            for i in res:
                v["codelist"].append(i[0])
                v["lastmodifylist"].append(i[1])
            
            return v


db = DB()

def get_instance():
    return db