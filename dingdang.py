#!/usr/bin/env python2
# -*- coding: utf-8-*-

import os
import sys
import logging
import time
import random
import yaml
import argparse
import threading
from client import config
from client import tts
from client import stt
from client import dingdangpath
from client import diagnose
from client.wxbot import WXBot
from client.conversation import Conversation
from client.tts import SimpleMp3Player
# Add dingdangpath.LIB_PATH to sys.path
sys.path.append(dingdangpath.LIB_PATH)

parser = argparse.ArgumentParser(description='Dingdang Voice Control Center')
parser.add_argument('--local', action='store_true',
                    help='Use text input instead of a real microphone')
parser.add_argument('--no-network-check', action='store_true',
                    help='Disable the network connection check')
parser.add_argument('--diagnose', action='store_true',
                    help='Run diagnose and exit')
parser.add_argument('--debug', action='store_true', help='Show debug messages')
parser.add_argument('--info', action='store_true', help='Show info messages')
args = parser.parse_args()

if args.local:
    from client.local_mic import Mic
else:
    from client.mic import Mic


class WechatBot(WXBot):
    def __init__(self, brain):
        WXBot.__init__(self)
        self.brain = brain
        self.music_mode = None
        self.last = time.time()

    def handle_msg_all(self, msg):
        # ignore the msg when handling plugins
        if msg['msg_type_id'] == 1 and \
           msg['to_user_id'] == self.my_account['UserName']:  # reply to self

            if msg['content']['type'] == 0:
                msg_data = msg['content']['data']
                if self.music_mode is not None:
                    # avoid repeating command
                    now = time.time()
                    if (now - self.last) > 0.5:
                        # stop passive listening
                        self.brain.mic.stopPassiveListen()
                        self.last = now
                        if not self.music_mode.delegating:
                            self.music_mode.delegating = True
                            self.music_mode.delegateInput(msg_data, True)
                            if self.music_mode is not None:
                                self.music_mode.delegating = False
                    return
                self.brain.query([msg_data], self, True)
            elif msg['content']['type'] == 4:  # echo voice
                player = SimpleMp3Player()
                player.play_mp3('./temp/voice_%s.mp3' % msg['msg_id'])


class Dingdang(object):
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.config = config.profile

        try:
            stt_engine_slug = self.config['stt_engine']
        except KeyError:
            stt_engine_slug = 'snowboy-stt'
            logger.warning("stt_engine not specified in profile, defaulting " +
                           "to '%s'", stt_engine_slug)
        stt_engine_class = stt.get_engine_by_slug(stt_engine_slug)

        try:
            slug = self.config['stt_passive_engine']
            stt_passive_engine_class = stt.get_engine_by_slug(slug)
        except KeyError:
            stt_passive_engine_class = stt_engine_class

        try:
            tts_engine_slug = self.config['tts_engine']
        except KeyError:
            tts_engine_slug = tts.get_default_engine_slug()
            logger.warning("tts_engine not specified in profile, defaulting " +
                           "to '%s'", tts_engine_slug)
        tts_engine_class = tts.get_engine_by_slug(tts_engine_slug)

        # Initialize Mic
        self.mic = Mic(
            self.config,
            tts_engine_class.get_instance(),
            stt_passive_engine_class.get_passive_instance(),
            stt_engine_class.get_active_instance())

    def start_wxbot(self):
        self.wxBot.run(self.mic)

    def run(self):
        persona = '小安'
        if 'robot_name' in self.config:
            persona = self.config["robot_name"]
        master = "主人"
        if 'master_name' in self.config:
            master = self.config["master_name"]

        salutation = random.choice(["%s,%s 竭诚为您服务?" % (master, persona), "%s，请尽情吩咐 %s" % (master, persona)])

        conversation = Conversation(persona, self.mic, self.config)

        # create wechat robot
        if self.config['wechat']:
            self.wxBot = WechatBot(conversation.brain)
            self.wxBot.DEBUG = True
            self.wxBot.conf['qr'] = 'tty'
            conversation.wxbot = self.wxBot
            t = threading.Thread(target=self.start_wxbot)
            t.start()

        self.mic.say(salutation)
        conversation.handleForever()


if __name__ == "__main__":

    print("*******************************************************")
    print("*                   安格瑞，正在启动中                  *")
    print("*                                                     *")
    print("*                                                     *")
    print("*******************************************************")

    logging.basicConfig()
    logger = logging.getLogger()
    logger.getChild("client.stt").setLevel(logging.INFO)

    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.info:
        logger.setLevel(logging.INFO)

    if not args.no_network_check and not diagnose.check_network_connection():
        logger.warning("Network not connected. This may prevent Dingdang " +
                       "from running properly.")

    if args.diagnose:
        failed_checks = diagnose.run()
        sys.exit(0 if not failed_checks else 1)

    try:
        app = Dingdang()
    except Exception:
        logger.error("Error occured!", exc_info=True)
        sys.exit(1)

    app.run()
