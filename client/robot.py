# -*- coding: utf-8-*-
import requests
import json
import logging
from uuid import getnode as get_mac
from app_utils import sendToUser
from abc import ABCMeta, abstractmethod
from client import config

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from app_utils import wechatUser

class AbstractRobot(object):

    __metaclass__ = ABCMeta

    @classmethod
    def get_instance(cls, mic, profile, wxbot=None):
        instance = cls(mic, profile, wxbot)
        cls.mic = mic
        # cls.wxbot = wxbot
        return instance

    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)

    @abstractmethod
    def chat(self, texts):
        pass


class TulingRobot(AbstractRobot):

    SLUG = "tuling"

    def __init__(self, mic, profile, wxbot=None):
        """
        图灵机器人
        """
        super(self.__class__, self).__init__()
        self.mic = mic
        self.profile = profile
        # self.wxbot = wxbot
        self.tuling_key = self.get_key()

    def get_key(self):
        # FIXME: Replace this as soon as we have a config module
        # Try to get baidu_yuyin config from config
        if 'tuling' in self.profile:
            if 'tuling_key' in self.profile['tuling']:
                tuling_key = \
                        self.profile['tuling']['tuling_key']
        return tuling_key

    def chat(self, texts):
        """
        使用图灵机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = ''.join(texts)
        try:
            url = "http://www.tuling123.com/openapi/api"
            userid = str(get_mac())[:32]
            body = {'key': self.tuling_key, 'info': msg, 'userid': userid}
            r = requests.post(url, data=body)
            respond = json.loads(r.text)
            notSay = False
            result = ''
            if respond['code'] == 100000:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')
            elif respond['code'] == 200000:
                result = respond['url']
                notSay = True
            elif respond['code'] == 302000:
                for k in respond['list']:
                    result = result + u"【" + k['source'] + u"】 " +\
                             k['article'] + "\t" + k['detailurl'] + "\n"
                notSay = True
            else:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')
                notSay = True
            max_length = 200
            if 'max_length' in self.profile:
                max_length = self.profile['max_length']
            if notSay or (len(result) > max_length and \
               self.profile['read_long_content'] is not None and \
               not self.profile['read_long_content']):
                wxbot = config.get_uni_obj('wxbot')
                if wxbot is not None:
                     t =self.mic.asyncSay(u'结果将发送到您的微信')
                     wechatUser(self.profile, wxbot, "" , result)
                     t.join()
                else:
                    self.mic.say(u'请扫码登录微信，结果将发送到您的微信')
            else:
                self.mic.say(result)
        except Exception:
            self._logger.critical("Tuling robot failed to responsed for %r",
                                  msg, exc_info=True)
            self.mic.say("抱歉, 我的大脑短路了 " +
                         "请稍后再试试.")


def get_robot_by_slug(slug):
    """
    Returns:
        A robot implementation available on the current platform
    """
    if not slug or type(slug) is not str:
        raise TypeError("Invalid slug '%s'", slug)

    selected_robots = filter(lambda robot: hasattr(robot, "SLUG") and
                             robot.SLUG == slug, get_robots())
    if len(selected_robots) == 0:
        raise ValueError("No robot found for slug '%s'" % slug)
    else:
        if len(selected_robots) > 1:
            print("WARNING: Multiple robots found for slug '%s'. " +
                  "This is most certainly a bug." % slug)
        robot = selected_robots[0]
        return robot


def get_robots():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses
    return [robot for robot in
            list(get_subclasses(AbstractRobot))
            if hasattr(robot, 'SLUG') and robot.SLUG]
