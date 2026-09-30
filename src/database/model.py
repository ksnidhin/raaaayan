#!/usr/bin/env python3
# coding: utf-8

# Raayan - model.py
# Upstream: ytdlbot (https://github.com/tgbot-collection/ytdlbot)
# Original author: Benny <benny.think@gmail.com>
# License: Apache 2.0

import logging
import math
import os
from contextlib import contextmanager
from typing import Literal

from sqlalchemy import (
    BigInteger,
    Column,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from config import DB_DSN, ENABLE_VIP, FREE_DOWNLOAD


class PaymentStatus:
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)  # telegram user id
    free = Column(Integer, default=FREE_DOWNLOAD)
    paid = Column(Integer, default=0)
    config = Column(JSON)

    settings = relationship("Setting", back_populates="user", cascade="all, delete-orphan", uselist=False)
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quality = Column(Enum("high", "medium", "low", "audio", "custom"), nullable=False, default="high")
    format = Column(Enum("video", "audio", "document"), nullable=False, default="video")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="settings")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    method = Column(String(50))
    amount = Column(Float)
    status = Column(Enum("pending", "completed", "failed", "refunded"), default="pending")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="payments")


# ---- Engine / Session setup ----

_engine = None
_Session = None


def _get_engine():
    global _engine
    if _engine is None:
        if not DB_DSN:
            raise RuntimeError("DB_DSN environment variable is not set")
        _engine = create_engine(DB_DSN, pool_pre_ping=True)
        Base.metadata.create_all(_engine)
        logging.info("Database tables created/verified")
    return _engine


def _get_session():
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=_get_engine())
    return _Session


@contextmanager
def _session_scope():
    Session = _get_session()
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---- Public API functions (called from main.py / engine) ----

def init_user(user_id: int):
    with _session_scope() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            user = User(user_id=user_id, free=FREE_DOWNLOAD, paid=0)
            session.add(user)
            session.flush()
            setting = Setting(user_id=user.id)
            session.add(setting)
            logging.info("New user initialized: %s", user_id)


def get_free_quota(user_id: int) -> int:
    with _session_scope() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            return user.free
        return 0


def get_paid_quota(user_id: int) -> int:
    with _session_scope() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            return user.paid
        return 0


def check_quota(user_id: int) -> bool:
    """Returns True if user has quota remaining."""
    free = get_free_quota(user_id)
    paid = get_paid_quota(user_id)
    return (free + paid) > 0


def use_quota(user_id: int):
    """Deduct one download from user quota (paid first, then free)."""
    with _session_scope() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            if user.paid > 0:
                user.paid -= 1
            elif user.free > 0:
                user.free -= 1
            else:
                raise Exception("No quota remaining")


def credit_account(user_id: int, amount: int):
    with _session_scope() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.paid += amount


def reset_free(user_id: int = None):
    """Reset free quota. If user_id is None, reset all users."""
    with _session_scope() as session:
        if user_id:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.free = FREE_DOWNLOAD
        else:
            session.query(User).update({User.free: FREE_DOWNLOAD})
            logging.info("Reset free quota for all users")


def get_quality_settings(user_id: int) -> str:
    with _session_scope() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user and user.settings:
            return user.settings.quality
        return "high"


def get_format_settings(user_id: int) -> str:
    with _session_scope() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user and user.settings:
            return user.settings.format
        return "video"


def set_user_settings(user_id: int, quality: str = None, format_: str = None):
    with _session_scope() as session:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            if user.settings is None:
                user.settings = Setting(user_id=user.id)
                session.add(user.settings)
            if quality:
                user.settings.quality = quality
            if format_:
                user.settings.format = format_
