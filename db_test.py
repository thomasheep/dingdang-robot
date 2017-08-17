# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from client import db
print db.get_instance().is_need_update()

import time
t1 = time.time()
code = db.get_instance().get_stock_code('波导股份')
t2 = time.time()
name = db.get_instance().get_stock_name('600130')
t3 = time.time()
print "%s:%s  %f  %f"%(code, name, t2-t1, t3-t2)

print db.get_instance().is_table_exist("notext")
print db.get_instance().get_stock_name("000776")
db.get_instance().remove_notify("000776")
db.get_instance().add_notify("000776", "广发证券")
print db.get_instance().get_notify_list()
print db.get_instance().check_notify("000776")
db.get_instance().update_notify("000776", "2017-08-14 15:05:03")
print db.get_instance().get_notify_list()
db.get_instance().remove_notify("000776")
print db.get_instance().get_notify_list()
