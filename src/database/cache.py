#!/usr/bin/env python3
# coding: utf-8

# Raayan - cache.py
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0

import logging

import fakeredis
import redis

from config import REDIS_HOST


class Redis:
    def __init__(self):
        try:
            self.r = redis.StrictRedis(host=REDIS_HOST, db=1, decode_responses=True)
            self.r.ping()
            logging.info("Connected to Redis at %s", REDIS_HOST)
        except Exception:
            logging.warning("Redis not available, falling back to fakeredis")
            self.r = fakeredis.FakeRedis(decode_responses=True)

    def get(self, key):
        return self.r.get(key)

    def set(self, key, value, ex=None):
        return self.r.set(key, value, ex=ex)

    def delete(self, key):
        return self.r.delete(key)

    def exists(self, key):
        return self.r.exists(key)
