# -*- coding: utf-8-*-

import os
import subprocess
import time
import sys
import re
import tushare as ts
from client import db
PRIORITY = 11
WORDS = [u"新闻"]
SLUG = "news"

pattern = re.compile(ur'.*股票(代码)?(\d{6})(的)?信息地雷.*')

def nlpHandle(nlp, mic, profile, wxbot=None):
    """

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
                   number)
        wxbot -- wechat bot instance
    """
    def get_news(data):
        rs = []
        for index, row in data.iterrows():
            rs.append(str(index+1))
            for col_name in data.columns:
                rs.append(row[col_name])
            rs.append('\n')
        return ' '.join(rs)



    sys.path.append(mic.dingdangpath.LIB_PATH)
    from app_utils import wechatUser
    text = nlp['text']
    if any(word in text for word in [u"财经新闻"]):
        news = ts.get_latest_news(top=10,show_content=False)
        t = mic.asyncSay("已获取财经新闻," + ('将发送到您的微信'if wxbot != None else "篇幅较长，请登录微信获取"))
        if wxbot != None:
            wechatUser(profile, wxbot, '财经新闻', get_news(news))
        t.join()
    elif any(word in text for word in [u"信息地雷"]):
        orgName = None
        code = None
        items = nlp['items']
        for item in items:
            if item['ne']==u'ORG':
                orgName = item['item']
                break
        if orgName:
            code = db.get_instance().get_stock_code(orgName)
        else:
            m = pattern.search(text)
            if m:
                code = m.group(2)
        
        if code :
            orgName = db.get_instance().get_stock_name(code)
            if not orgName:
                mic.say("股票代码可能不存在")
                return
            notices = ts.get_notices(code)
            notices = notices[0:10]
            tit = orgName+'的信息地雷'
            t = mic.asyncSay("已获取"+tit+"," + ('将发送到您的微信'if wxbot != None else "篇幅较长，请登录微信获取"))
            if wxbot != None:
                wechatUser(profile, wxbot, tit , get_news(notices))
            t.join()
        else:
            mic.say("没能获取股票代码")
            


               



def isNlpValid(nlp):
    """
        Returns True if input is related to the news.

        Arguments:
        text -- user-input, typically transcribed speech
    """
    text = nlp['text']
    return  any(word in text for word in [u"财经新闻", u"信息地雷"])
