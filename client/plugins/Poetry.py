# -*- coding: utf-8-*-
import os 

import subprocess 

import random
  

  
INTERPRETER = "/usr/bin/python"
  
  

    
  


WORDS = ["古诗"]
SLUG = "poetry"
PRIORITY = 6

poetry_file = 'poetry.new'

poetry_gen = 'poetry_gen.py'

pargs = [INTERPRETER, poetry_gen] 

def getPoetry():
    with open(poetry_file, "r") as f:
        return f.read()

def handle(text, mic, profile, wxbot=None):
    """
        Reports the current time based on the user's timezone.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
                   number)
        wxBot -- wechat robot
    """
    t = mic.asyncSay(random.choice(["请给我三步的时间","请给我七步的时间。"]))
    subprocess.Popen(pargs) 
    p = getPoetry()
    t.join()
    mic.say(p)


def isValid(text):
    """
        Returns True if input is related to the time.

        Arguments:
        text -- user-input, typically transcribed speech
    """
    return all(word in text for word in [u"古诗", u"首"]) and any(word in text for word in [u"作", u"做", u"生成"])
