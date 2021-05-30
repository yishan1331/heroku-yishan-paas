# -*- coding: utf-8 -*-
import time
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from authlib.integrations.sqla_oauth2 import (
    OAuth2ClientMixin,
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
)
# import redis

Base = declarative_base()

#客戶API主帳號列表
class SystemList(Base):
    __tablename__ = 'system_list'

    id = Column(Integer, primary_key=True)
    system_name = Column(String(40), unique=True)
    system_info = Column(String(128))

    def __str__(self):
        return self.system_name

    def get_system_id(self):
        return self.id

    def check_password(self, password):
        return password == 'valid'

#客戶API主帳號Oauth2 Client列表(client_id&client_secret....)
class OAuth2Client(Base, OAuth2ClientMixin):
    __tablename__ = 'oauth2_client'

    id = Column(Integer, primary_key=True)
    system_id = Column(
        Integer, ForeignKey('system_list.id', ondelete='CASCADE'))
    sub_account_counts = Column(Integer, nullable=False, default=0)
    system_list = relationship('SystemList')


# class OAuth2AuthorizationCode(Base, OAuth2AuthorizationCodeMixin):
#     __tablename__ = 'oauth2_code'

#     id = Column(Integer, primary_key=True)
#     system_id = Column(
#         Integer, ForeignKey('system_list.id', ondelete='CASCADE'))
#     system_list = relationship('SystemList')


class OAuth2Token(Base, OAuth2TokenMixin):
    __tablename__ = 'oauth2_token'

    id = Column(Integer, primary_key=True)
    system_id = Column(
        Integer, ForeignKey('system_list.id', ondelete='CASCADE'))
    system_list = relationship('SystemList')

    def is_refresh_token_active(self):
        if self.revoked:
            return False
        expires_at = self.issued_at + self.expires_in * 2
        return expires_at >= time.time()


# POOL = redis.ConnectionPool(host='192.168.88.75', port=6379, db=0,password="sapido")
# Yishan_dbRedis = redis.Redis(connection_pool=POOL)