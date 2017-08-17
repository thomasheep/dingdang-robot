# -*- coding: utf-8-*-

import os
import subprocess
import time
import sys
import tushare as ts
import re
from client import db

WORDS = [u"股票"]
SLUG = "stock"

pattern = re.compile(ur'.*关注(股票)?(代码)?(\d{6}|)(的)?(股价|价格|股票价格).*')


def nlpHandle(nlp, mic, profile, wxbot=None):
    """

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
                   number)
        wxbot -- wechat bot instance
    """

    text = nlp['text']
    items = nlp['items']
    orgName = None
    code = None
    for item in items:
        if item['ne'] == u'ORG':
            orgName = item['item']
            break
    if orgName:
        code = db.get_instance().get_stock_code(orgName)
    else:
        m = pattern.search(text)
        if m:
            code = m.group(3)
    
    if code :
        orgName = db.get_instance().get_stock_name(code)
        if not orgName:
            mic.say("股票代码可能不存在")
            return
        if any(word in text for word in [u"不在关注", u"取消关注", u"不在关注"]):
            if db.get_instance().check_notify(code):
                db.get_instance().remove_notify(code)
                mic.say("已取消关注股票:%s，代码:%s"%(orgName, code))
            else:
                mic.say("股票:%s，代码:%s，尚未在关注列表中"%(orgName, code))
        else:
            if not db.get_instance().check_notify(code):
                db.get_instance().add_notify(code,orgName)
                mic.say("已关注股票:%s，代码:%s"%(orgName, code))
            else:
                mic.say("股票:%s，代码:%s，已在关注列表中"%(orgName, code))
    else:
        mic.say("没能获取股票代码")
def isNlpValid(nlp):
    """
        Returns True if input is related to the time.

        Arguments:
        text -- user-input, typically transcribed speech
    """
    text = nlp['text']
    return all(word in text for word in [u"关注", u"股价"]) or all(word in text for word in [u"关注", u"价格"])or all(word in text for word in [u"关注", u"股票价格"])
