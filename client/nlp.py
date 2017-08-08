# -*- coding: utf-8-*-
import requests
import json
import logging
import diagnose
from uuid import getnode as get_mac
from app_utils import sendToUser
from abc import ABCMeta, abstractmethod

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class AbstractNlp(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_config(self):
        pass
    @classmethod
    def get_instance(cls):
        config = cls.get_config()
        instance = cls(**config)
        return instance

    def __init__(self, **kwargs):
        self._logger = logging.getLogger(__name__)

    @abstractmethod
    def lexer(self, texts):
        pass

    @abstractmethod
    def simnet(self, texts):
        pass


class BaiduNlp(AbstractNlp):

    SLUG = "baidu"
    
    @abstractmethod
    def get_config(self):
        pass

    @classmethod
    def get_config(cls):
        # FIXME: Replace this as soon as we have a config module
        config = {}
        # Try to get baidu_yuyin config from config
        profile_path = dingdangpath.config('profile.yml')
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'baidu_yuyin' in profile:
                    if 'api_key' in profile['baidu_yuyin']:
                        config['api_key'] = \
                            profile['baidu_yuyin']['api_key']
                    if 'secret_key' in profile['baidu_yuyin']:
                        config['secret_key'] = \
                            profile['baidu_yuyin']['secret_key']
                    if 'per' in profile['baidu_yuyin']:
                        config['per'] = \
                            profile['baidu_yuyin']['per']
        return config

    @classmethod
    def is_available(cls):
        return diagnose.check_network_connection()




    def __init__(self, api_key, secret_key):
        """
        Baidu NLP
        """
        super(self.__class__, self).__init__()
        self.mic = mic
        self.profile = profile
        self.wxbot = wxbot
        self.tuling_key = self.get_key()

   
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
