# -*- coding: utf-8-*-

import os
import subprocess
import time
import sys
import tushare as ts
PRIORITY = 9
WORDS = [u"电影"]
SLUG = "film"


def handle(text, mic, profile, wxbot=None):
    """

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
                   number)
        wxbot -- wechat bot instance
    """
    sys.path.append(mic.dingdangpath.LIB_PATH)
    from app_utils import wechatUser
    df = ts.realtime_boxoffice()

    rs = []
    # rs.append("实时票房（万）")
    # rs.append("排名")
    # rs.append("影片名")
    # rs.append("票房占比 （%）")
    # rs.append("上映天数")
    # rs.append("累计票房（万）")
    # rs.append("数据获取时间")
    # rs.append("\n")
    for index, row in df.iterrows():
        for col_name in df.columns:
            if col_name=="BoxOffice":
                rs.append("实时票房:"+row[col_name]+"万")
            elif col_name=="Irank":
                rs.append("排名:"+row[col_name])
            elif col_name=="MovieName":
                rs.append("片名:"+row[col_name])
            elif col_name=="boxPer":
                rs.append("票房占比:"+row[col_name])
            elif col_name=="movieDay":
                rs.append("上映天数:"+row[col_name])
            elif col_name=="sumBoxOffice":
                rs.append("累计票房:"+row[col_name])
            elif col_name=="time":
                rs.append("获取时间:"+row[col_name])
        rs.append('\n')
    msg = ' '.join(rs)
    tit = "电影票房实时排行榜"
    t = mic.asyncSay("已获取"+tit+"," + ('将发送到您的微信'if wxbot != None else "篇幅较长，请登录微信收取"))
    if wxbot != None:
        wechatUser(profile, wxbot,tit , msg)
    t.join()



def isValid(text):
    """
        Returns True if input is related to the time.

        Arguments:
        text -- user-input, typically transcribed speech
    """
    return all(word in text for word in [u"电影", u"票房", u"排行榜"]) 
