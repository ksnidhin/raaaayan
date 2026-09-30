#!/usr/local/bin/python3
# coding: utf-8

# Raayan - __init__.py
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0

import logging

from dotenv import load_dotenv

load_dotenv()

from config.config import *
from config.constant import *

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
