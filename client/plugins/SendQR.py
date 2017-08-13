# -*- coding: utf-8-*-

import os
import sys
from client import config
import time


WORDS = ["微信", "二维码"]
SLUG = "sendqr"


def handle(text, mic, profile, wxbot=None):
    """
        Reports the current time based on the user's timezone.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
                   number)
        wxbot -- wechat bot instance
    """
    
    if 'wechat' not in profile or not profile['wechat']:
        mic.say(u'请先在配置文件中开启微信接入功能')
        return
    if 'email' not in profile or ('enable' in profile['email']
                                  and not profile['email']):
        mic.say(u'请先配置好邮箱功能')
        return
    sys.path.append(mic.dingdangpath.LIB_PATH)
    from app_utils import emailUser

    # dest_file = os.path.join(mic.dingdangpath.TEMP_PATH, 'wxqr.png')
    app = config.get_uni_obj('app')
    wxbot = app.start_wxbot()
    t = mic.asyncSay("正在获取微信二维码")
    tryTimes = 30
    while tryTimes>0:
        tryTimes = tryTimes-1
        if wxbot.qr_file == None:
            time.sleep(0.1)
            continue
        with wxbot.qr_lock:
            if os.path.exists(wxbot.qr_file):
                t = mic.asyncSay(u'正在发送微信登录二维码到您的邮箱')
                if emailUser(profile, u"这是您的微信登录二维码", "", [wxbot.qr_file]):
                    t = mic.asyncSay(u'发送成功')
                    return
                else:
                    t = mic.asyncSay(u'发送失败')
                    return
                    
        time.sleep(0.1)
    t.join()
    mic.say(u"获取登录二维码失败，请重新尝试")
    

def isValid(text):
    """
        Returns True if input is related to the time.

        Arguments:
        text -- user-input, typically transcribed speech
    """
    return all(word in text for word in [u"微信", u"二维码"])
