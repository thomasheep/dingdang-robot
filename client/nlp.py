# -*- coding: utf-8-*-
import requests
import json
import logging
import diagnose
from uuid import getnode as get_mac
from app_utils import sendToUser
from abc import ABCMeta, abstractmethod
import config
from aip import AipNlp

class AbstractNlp(object):
    """
    Generic parent class for all NLP engines
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_config(self):
        pass

    @classmethod
    def get_instance(cls):
        config = cls.get_config()
        instance = cls(**config)
        return instance

    @abstractmethod
    def lexer(self, texts):
        pass

    @abstractmethod
    def simnet(self, text1, text2):
        pass


class BaiduNlp(AbstractNlp):
    """
    百度的NLP API.
    要使用本模块, 首先到百度注册一个开发者账号,
    之后创建一个新应用, 然后在应用管理的"查看key"中获得 AppID, API Key 和 Secret Key
    填入 profile.xml 中.
    """
    SLUG = "baidu"

    @classmethod
    def get_config(cls):
        # FIXME: Replace this as soon as we have a config module
        cfg = {}
        # Try to get baidu_yuyin config from config
        cfg['app_id'] = config.profile['baidu_nlp']['app_id']
        cfg['api_key'] = config.profile['baidu_nlp']['api_key']
        cfg['secret_key'] = config.profile['baidu_nlp']['secret_key']
        return cfg

    def __init__(self, app_id, api_key, secret_key):
        """
        Baidu NLP
        """
        self.nlp =  AipNlp(app_id, api_key, secret_key)
 
    def lexer(self, texts):
        return self.nlp.lexer(texts)

  
    def simnet(self, text1, text2):
        return self.nlp.simnet(text1, text2)



def get_nlp_by_slug(slug):
    """
    Returns:
        A nlp implementation available on the current platform
    """
    if not slug or type(slug) is not str:
        raise TypeError("Invalid slug '%s'", slug)

    selected_robots = filter(lambda robot: hasattr(robot, "SLUG") and
                             robot.SLUG == slug, get_nlps())
    if len(selected_robots) == 0:
        raise ValueError("No nlp found for slug '%s'" % slug)
    else:
        if len(selected_robots) > 1:
            print("WARNING: Multiple nlps found for slug '%s'. " +
                  "This is most certainly a bug." % slug)
        robot = selected_robots[0]
        return robot


def get_nlps():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses
    return [nlp for nlp in
            list(get_subclasses(AbstractNlp))
            if hasattr(nlp, 'SLUG') and nlp.SLUG]
