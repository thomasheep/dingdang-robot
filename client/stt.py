#!/usr/bin/env python2
# -*- coding: utf-8-*-
import os
import base64
import wave
import json
import tempfile
import logging
import urllib
from abc import ABCMeta, abstractmethod
import requests
import yaml
import dingdangpath
import diagnose
import vocabcompiler
from uuid import getnode as get_mac

import sys
import time
reload(sys)
sys.setdefaultencoding('utf8')


class AbstractSTTEngine(object):
    """
    Generic parent class for all STT engines
    """

    __metaclass__ = ABCMeta
    VOCABULARY_TYPE = None

    @classmethod
    def get_config(cls):
        return {}

    @classmethod
    def get_instance(cls, vocabulary_name, phrases):
        config = cls.get_config()
        if cls.VOCABULARY_TYPE:
            vocabulary = cls.VOCABULARY_TYPE(vocabulary_name,
                                             path=dingdangpath.config(
                                                 'vocabularies'))
            if not vocabulary.matches_phrases(phrases):
                vocabulary.compile(phrases)
            config['vocabulary'] = vocabulary
        instance = cls(**config)
        return instance

    @classmethod
    def get_passive_instance(cls):
        phrases = vocabcompiler.get_keyword_phrases()
        return cls.get_instance('keyword', phrases)

    @classmethod
    def get_active_instance(cls):
        phrases = vocabcompiler.get_all_phrases()
        return cls.get_instance('default', phrases)

    @classmethod
    def get_music_instance(cls):
        phrases = vocabcompiler.get_all_phrases()
        return cls.get_instance('music', phrases)

    @classmethod
    @abstractmethod
    def is_available(cls):
        return True

    @abstractmethod
    def transcribe(self, fp):
        pass


class PocketSphinxSTT(AbstractSTTEngine):
    """
    The default Speech-to-Text implementation which relies on PocketSphinx.
    """

    SLUG = 'sphinx'
    VOCABULARY_TYPE = vocabcompiler.PocketsphinxVocabulary

    def __init__(self, vocabulary, hmm_dir="/usr/local/share/" +
                 "pocketsphinx/model/hmm/en_US/hub4wsj_sc_8k"):

        """
        Initiates the pocketsphinx instance.

        Arguments:
            vocabulary -- a PocketsphinxVocabulary instance
            hmm_dir -- the path of the Hidden Markov Model (HMM)
        """

        self._logger = logging.getLogger(__name__)

        # quirky bug where first import doesn't work
        try:
            import pocketsphinx as ps
        except:
            import pocketsphinx as ps

        with tempfile.NamedTemporaryFile(prefix='psdecoder_',
                                         suffix='.log', delete=False) as f:
            self._logfile = f.name

        self._logger.debug("Initializing PocketSphinx Decoder with hmm_dir " +
                           "'%s'", hmm_dir)

        # Perform some checks on the hmm_dir so that we can display more
        # meaningful error messages if neccessary
        if not os.path.exists(hmm_dir):
            msg = ("hmm_dir '%s' does not exist! Please make sure that you " +
                   "have set the correct hmm_dir in your profile.") % hmm_dir
            self._logger.error(msg)
            raise RuntimeError(msg)
        # Lets check if all required files are there. Refer to:
        # http://cmusphinx.sourceforge.net/wiki/acousticmodelformat
        # for details
        missing_hmm_files = []
        for fname in ('mdef', 'feat.params', 'means', 'noisedict',
                      'transition_matrices', 'variances'):
            if not os.path.exists(os.path.join(hmm_dir, fname)):
                missing_hmm_files.append(fname)
        mixweights = os.path.exists(os.path.join(hmm_dir, 'mixture_weights'))
        sendump = os.path.exists(os.path.join(hmm_dir, 'sendump'))
        if not mixweights and not sendump:
            # We only need mixture_weights OR sendump
            missing_hmm_files.append('mixture_weights or sendump')
        if missing_hmm_files:
            self._logger.warning("hmm_dir '%s' is missing files: %s. Please " +
                                 "make sure that you have set the correct " +
                                 "hmm_dir in your profile.",
                                 hmm_dir, ', '.join(missing_hmm_files))

        self._decoder = ps.Decoder(hmm=hmm_dir, logfn=self._logfile,
                                   **vocabulary.decoder_kwargs)

    def __del__(self):
        os.remove(self._logfile)

    @classmethod
    def get_config(cls):
        # FIXME: Replace this as soon as we have a config module
        config = {}
        # HMM dir
        # Try to get hmm_dir from config
        profile_path = dingdangpath.config('profile.yml')

        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profile = yaml.safe_load(f)
                try:
                    config['hmm_dir'] = profile['pocketsphinx']['hmm_dir']
                except KeyError:
                    pass

        return config

    def transcribe(self, fp):
        """
        Performs STT, transcribing an audio file and returning the result.

        Arguments:
            fp -- a file object containing audio data
        """

        fp.seek(44)

        # FIXME: Can't use the Decoder.decode_raw() here, because
        # pocketsphinx segfaults with tempfile.SpooledTemporaryFile()
        data = fp.read()
        self._decoder.start_utt()
        self._decoder.process_raw(data, False, True)
        self._decoder.end_utt()

        result = self._decoder.get_hyp()
        with open(self._logfile, 'r+') as f:
            for line in f:
                self._logger.debug(line.strip())
            f.truncate()

        transcribed = [result[0]]
        self._logger.info('Transcribed: %s', transcribed)
        return transcribed

    @classmethod
    def is_available(cls):
        return diagnose.check_python_import('pocketsphinx')


class BaiduSTT(AbstractSTTEngine):
    """
    百度的语音识别API.
    要使用本模块, 首先到 yuyin.baidu.com 注册一个开发者账号,
    之后创建一个新应用, 然后在应用管理的"查看key"中获得 API Key 和 Secret Key
    填入 profile.xml 中.

        ...
        baidu_yuyin: 'AIzaSyDoHmTEToZUQrltmORWS4Ott0OHVA62tw8'
            api_key: 'LMFYhLdXSSthxCNLR7uxFszQ'
            secret_key: '14dbd10057xu7b256e537455698c0e4e'
        ...
    """

    SLUG = "baidu-stt"

    def __init__(self, api_key, secret_key):
        self._logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.secret_key = secret_key
        self.token = ''

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
        return config

    def get_token(self):
        URL = 'http://openapi.baidu.com/oauth/2.0/token'
        params = urllib.urlencode({'grant_type': 'client_credentials',
                                   'client_id': self.api_key,
                                   'client_secret': self.secret_key})
        r = requests.get(URL, params=params)
        try:
            r.raise_for_status()
            token = r.json()['access_token']
            return token
        except requests.exceptions.HTTPError:
            self._logger.critical('Token request failed with response: %s',
                                  r.text,
                                  exc_info=True)
            return ''

    def transcribe(self, fp):
        
        try:
            wav_file = wave.open(fp, 'rb')
        except IOError:
            self._logger.critical('wav file not found: %s',
                                  fp,
                                  exc_info=True)
            return []
        t1 = time.time()
        n_frames = wav_file.getnframes()
        frame_rate = wav_file.getframerate()
        audio = wav_file.readframes(n_frames)
        base_data = base64.b64encode(audio)
        if self.token == '':
            self.token = self.get_token()
        data = {"format": "wav",
                "token": self.token,
                "len": len(audio),
                "rate": frame_rate,
                "speech": base_data,
                "cuid": str(get_mac())[:32],
                "channel": 1}
        data = json.dumps(data)
        r = requests.post('http://vop.baidu.com/server_api',
                          data=data,
                          headers={'content-type': 'application/json'})
        try:
            r.raise_for_status()
            text = ''
            if 'result' in r.json():
                text = r.json()['result'][0].encode('utf-8')
        except requests.exceptions.HTTPError:
            self._logger.critical('Request failed with response: %s',
                                  r.text,
                                  exc_info=True)
            return []
        except requests.exceptions.RequestException:
            self._logger.critical('Request failed.', exc_info=True)
            return []
        except ValueError as e:
            self._logger.critical('Cannot parse response: %s',
                                  e.args[0])
            return []
        except KeyError:
            self._logger.critical('Cannot parse response.',
                                  exc_info=True)
            return []
        else:
            transcribed = []
            if text:
                transcribed.append(text.upper())
            t2 = time.time()
            self._logger.info(u'baidu-stt Transcribed: %s, time:%fs' % (text, t2-t1))
            return transcribed

    @classmethod
    def is_available(cls):
        return diagnose.check_network_connection()


class SnowboySTT(AbstractSTTEngine):
    """
    Snowboy STT 离线识别引擎（只适用于离线唤醒）
        ...
        snowboy:
            model: '/home/pi/.dingdang/snowboy/dingdangdingdang.pmdl'  # 唤醒词模型
            sensitivity: "0.5"  # 敏感度
        ...
    """

    SLUG = "snowboy-stt"

    def __init__(self, sensitivity, model, hotword):
        self._logger = logging.getLogger(__name__)
        self.sensitivity = sensitivity
        self.hotword = hotword
        self.model = model
        self.resource_file = os.path.join(dingdangpath.LIB_PATH,
                                          'snowboy/common.res')
        try:
            from snowboy import snowboydetect
        except Exception, e:
            self._logger.critical(e)
            if 'libf77blas.so' in e.message:
                self._logger.critical("您可能需要安装一个so包加载库：" +
                                      "sudo apt-get install libatlas-base-dev")
            return
        self.detector = snowboydetect.SnowboyDetect(
            resource_filename=self.resource_file,
            model_str=self.model)
        self.detector.SetAudioGain(1)
        self.detector.SetSensitivity(self.sensitivity)

    @classmethod
    def get_config(cls):
        # FIXME: Replace this as soon as we have a config module
        config = {}
        # Try to get snowboy config from config
        profile_path = dingdangpath.config('profile.yml')
        if os.path.exists(profile_path):
            with open(profile_path, 'r') as f:
                profile = yaml.safe_load(f)
                if 'snowboy' in profile:
                    if 'model' in profile['snowboy']:
                        config['model'] = \
                            profile['snowboy']['model']
                    else:
                        config['model'] = os.path.join(
                            dingdangpath.LIB_PATH, 'snowboy/dingdang.pmdl')
                    if 'sensitivity' in profile['snowboy']:
                        config['sensitivity'] = \
                            profile['snowboy']['sensitivity']
                    else:
                        config['sensitivity'] = "0.5"
                    if 'robot_name' in profile:
                        config['hotword'] = profile['robot_name']
                    else:
                        config['hotword'] = 'DINGDANG'
        return config

    def transcribe(self, fp):
        t1 = time.time()
        fp.seek(44)
        data = fp.read()
        ans = self.detector.RunDetection(data)
        t2 = time.time()
        if ans > 0:
            self._logger.info(u'nowboy Transcribed: %s , Time:%fs'%(self.hotword, t2-t1))
            return [self.hotword]
        else:
            return []

    @classmethod
    def is_available(cls):
        return diagnose.check_python_import('snowboy.snowboydetect')


def get_engine_by_slug(slug=None):
    """
    Returns:
        An STT Engine implementation available on the current platform

    Raises:
        ValueError if no speaker implementation is supported on this platform
    """

    if not slug or type(slug) is not str:
        raise TypeError("Invalid slug '%s'", slug)

    selected_engines = filter(lambda engine: hasattr(engine, "SLUG") and
                              engine.SLUG == slug, get_engines())
    if len(selected_engines) == 0:
        raise ValueError("No STT engine found for slug '%s'" % slug)
    else:
        if len(selected_engines) > 1:
            print(("WARNING: Multiple STT engines found for slug '%s'. " +
                   "This is most certainly a bug.") % slug)
        engine = selected_engines[0]
        if not engine.is_available():
            raise ValueError(("STT engine '%s' is not available (due to " +
                              "missing dependencies, missing " +
                              "dependencies, etc.)") % slug)
        return engine


def get_engines():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses
    return [tts_engine for tts_engine in
            list(get_subclasses(AbstractSTTEngine))
            if hasattr(tts_engine, 'SLUG') and tts_engine.SLUG]
