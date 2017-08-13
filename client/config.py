# -*- coding: utf-8-*-
import dingdangpath
import logging
import os
import yaml
import threading

uni_lock = threading.Lock()

logger = logging.getLogger(__name__)


def get_config():
        # Create config dir if it does not exist yet
        if not os.path.exists(dingdangpath.CONFIG_PATH):
            try:
                os.makedirs(dingdangpath.CONFIG_PATH)
            except OSError:
                logger.error("Could not create config dir: '%s'",
                                   dingdangpath.CONFIG_PATH, exc_info=True)
                raise

        # Check if config dir is writable
        if not os.access(dingdangpath.CONFIG_PATH, os.W_OK):
            logger.critical("Config dir %s is not writable. Dingdang " +
                                  "won't work correctly.",
                                  dingdangpath.CONFIG_PATH)

        config_file = dingdangpath.config('profile.yml')
        # Read config
        logger.debug("Trying to read config file: '%s'", config_file)
        try:
            with open(config_file, "r") as f:
                return yaml.safe_load(f)
        except OSError:
            logger.error("Can't open config file: '%s'", config_file)
            raise

profile = get_config()

uni_obj = {}

def set_uni_obj(k, v):
    with uni_lock:
        uni_obj[k] = v


def get_uni_obj(k):
    with uni_lock:
        if uni_obj[k]:
            return uni_obj[k]
        return None

profile.set_uni_obj = set_uni_obj
profile.get_uni_obj = get_uni_obj