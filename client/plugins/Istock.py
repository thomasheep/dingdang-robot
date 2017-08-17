# -*- coding: utf-8-*-

import os
import subprocess
import time
import sys

WORDS = [u"证券信息技术"]
SLUG = "istock"


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
    from app_utils import sendToUser
    pass



def isValid(text):
    """
        Returns True if input is related to the time.

        Arguments:
        text -- user-input, typically transcribed speech
    """
    return False
