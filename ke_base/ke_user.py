#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib, random, re
from sqlalchemy import Column, BigInteger, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from ke_config import *

# iniciamos la clase declarativa para poder crear clases ya mapeadas
Base = declarative_base()

# clase de usuario ya mapeada con sqlalchemy
class Ke_user(Base):
    __tablename__ = 'users'
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(BigInteger, primary_key=True)
    email = Column(String(50))
    password = Column(String(40))
    nick = Column(String(16))
    log_key = Column(String(40))
    points = Column(Integer, default=10)
    created = Column(DateTime, default=datetime.now())
    last_log_in = Column(DateTime, default=datetime.now())
    no_emails = Column(Boolean, default=False)
    logged_on = False
    
    def __init__(self):
        self.email = ''
        self.password = ''
        self.nick = 'anonymous'
        self.log_key = ''
        self.points = 10
        self.created = datetime.now()
        self.last_log_in = datetime.now()
        self.no_emails = False
    
    def exists(self):
        return (self.email != '' and self.nick != '')
    
    def set_nick(self, n):
        n = n.lower()
        if re.match("^[a-zA-Z0-9_]{4,16}$", n) and n != 'anonymous':
            self.nick = n
            return True
        else:
            return False
    
    def set_password(self, p):
        if re.match("^[a-zA-Z0-9_]{4,20}$", p):
            self.password = hashlib.sha1(p).hexdigest()
            return True
        else:
            return False
    
    def set_email(self, e):
        if re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", e):
            self.email = e
            return True
        else:
            return False
    
    def is_admin(self):
        return (self.nick in APP_ADMINS)
    
    def new_log_key(self):
        self.log_key = hashlib.sha1( str(random.randint(0, 999999)) ).hexdigest()
        self.last_log_in = datetime.now()
        self.logged_on = True
    
    def add_points(self, p=0):
        try:
            p = int(p)
        except:
            p = 0
        if p != 0:
            self.points += p
            if self.is_admin() and self.points <= 0:
                self.points = 1
            elif self.points < 0:
                self.points = 0
    
    def get_link(self, full=False):
        if full:
            return 'http://'+APP_DOMAIN+'/user/'+self.nick
        else:
            return '/user/'+self.nick
