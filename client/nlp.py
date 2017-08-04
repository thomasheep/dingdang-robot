# -*- coding: utf-8-*-
import requests
import json
import logging
from uuid import getnode as get_mac
from app_utils import sendToUser
from abc import ABCMeta, abstractmethod

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class AbstractNlp(object):

    __metaclass__ = ABCMeta

    @classmethod
    def get_instance(cls, mic, profile, wxbot=None):
        instance = cls(mic, profile, wxbot)
        cls.mic = mic
        cls.wxbot = wxbot
        return instance

    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)

    @abstractmethod
    def lexer(self, texts):
        pass

    @abstractmethod
    def (self, texts):
        pass


class BaiduNlp(AbstractNlp):

    SLUG = "baidu"

    def __init__(self, mic, profile, wxbot=None):
        """
        图灵机器人
        """
        super(self.__class__, self).__init__()
        self.mic = mic
        self.profile = profile
        self.wxbot = wxbot
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
            result = ''
            if respond['code'] == 100000:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')
            elif respond['code'] == 200000:
                result = respond['url']
            elif respond['code'] == 302000:
                for k in respond['list']:
                    result = result + u"【" + k['source'] + u"】 " +\
                             k['article'] + "\t" + k['detailurl'] + "\n"
            else:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')
            max_length = 200
            if 'max_length' in self.profile:
                max_length = self.profile['max_length']
            if len(result) > max_length and \
               self.profile['read_long_content'] is not None and \
               not self.profile['read_long_content']:
                target = '邮件'
                if self.wxbot is not None and self.wxbot.my_account != {} \
                   and not self.profile['prefers_email']:
                    target = '微信'
                self.mic.say(u'一言难尽啊，我给您发%s吧' % target)
                if sendToUser(self.profile, self.wxbot, u'回答%s' % msg, result):
                    self.mic.say(u'%s发送成功！' % target)
                else:
                    self.mic.say(u'抱歉，%s发送失败了！' % target)
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
