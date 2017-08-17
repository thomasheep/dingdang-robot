# -*- coding: utf-8-*-

import os
import subprocess
import time
import sys
import pipes
import logging
import re
import math
import tempfile
PRIORITY = 10

logger = logging.getLogger(__name__)


WORDS = [u"音量"]
SLUG = "volume"


outres = "Simple mixer control 'Speaker',0\n\
  Capabilities: pvolume pswitch pswitch-joined\n\
  Playback channels: Front Left - Front Right\n\
  Limits: Playback 0 - 30\n\
  Mono:\n\
  Front Left: Playback 12 [40%] [-27.00dB] [on]\n\
  Front Right: Playback 12 [40%] [-27.00dB] [on]\n"

maxpt = re.compile(ur'^.*Limits: Playback 0 - (\d{2})',re.MULTILINE)
curpt = re.compile(ur'^.*Front Left: Playback (\d{1,2}) \[',re.MULTILINE)

def getVolume():
    cmd = ['amixer', 'sget', 'Speaker']
    logger.info('Executing %s', ' '.join([pipes.quote(arg)for arg in cmd]))
    with tempfile.TemporaryFile() as f:
        subprocess.call(cmd, stdout=f, stderr=f)
        f.seek(0)
        output = f.read()
        output = output.decode('utf-8')
        m1 = maxpt.search(output)
        m2 = curpt.search(output)
        return m1.group(1), m2.group(1)

def setVolume(v):
    cmd = ['amixer', 'sset', 'Speaker', str(v)]
    logger.info('Executing %s', ' '.join([pipes.quote(arg)for arg in cmd]))
    with tempfile.TemporaryFile() as f:
        subprocess.call(cmd, stdout=f, stderr=f)
        f.seek(0)
        output = f.read()
        logger.info('amixer sget Speaker output %s'%output)
            


res = getVolume()
max_volume = int(res[0])
min_volume = math.floor(max_volume*0.5)
cur_volume = int(res[1])
step_voluem = math.floor(max_volume*0.1)

if cur_volume < min_volume:
    setVolume(min_volume)
    cur_volume = min_volume

def addVolume():
    global cur_volume 
    cur_volume = cur_volume + step_voluem
    if cur_volume > max_volume:
        cur_volume = max_volume
    setVolume(cur_volume)
    return str(math.ceil(cur_volume/max_volume*100))+'%'

def decVolume():
    global cur_volume 
    cur_volume = cur_volume - step_voluem
    if cur_volume < min_volume:
        cur_volume = min_volume
    setVolume(cur_volume)
    return str(math.ceil(cur_volume/max_volume*100))+'%'

def setMax():
    setVolume(max_volume)
    return '100%'

def setMin():
    setVolume(min_volume)
    return '50%'


# command amixer sset Speaker 100%

def handle(text, mic, profile, wxbot=None):
    """
        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
                   number)
        wxbot -- wechat bot instance
    """
    r = None
    if any(word in text for word in [u"最大"]):
        r = setMax()
    elif any(word in text for word in [u"最小"]):
        r = setMin()
    elif any(word in text for word in [u"增加", u"增大",u"加大"]):
        r = addVolume()
    elif any(word in text for word in [u"减小", u"减少",u'降低']):
        r = decVolume()
    if r:
        mic.say("音量调整到"+r)


def isValid(text):
    """

        Arguments:
        text -- user-input, typically transcribed speech
    """
    return any(word in text for word in [u"音量", u"声音"]) and any(word in text for word in [u"调整", u"调节", u"增加", u"增大",u"加大", u"减小", u"减少",u'降低', u"最大", u"最小"]) 

