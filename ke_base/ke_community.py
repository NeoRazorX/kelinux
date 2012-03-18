#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, cgi
from sqlalchemy import Table, Column, ForeignKey, BigInteger, Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timedelta
from ke_config import *
from ke_user import *


# tabla necesaria para la relación muchos a muchos entre Ke_user y Ke_community
Ke_user_community_table = Table('user_community', Base.metadata,
    Column('users_id', BigInteger, ForeignKey('users.id')),
    Column('communities_id', BigInteger, ForeignKey('communities.id'))
)


# clase de comunidad ya mapeada con sqlalchemy
class Ke_community(Base):
    __tablename__ = 'communities'
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(BigInteger, primary_key=True)
    name = Column(String(20))
    description = Column(String(200))
    created = Column(DateTime, default=datetime.now())
    num_users = Column(Integer, default=0)
    users = relationship("Ke_user", secondary=Ke_user_community_table, backref=backref('communities'))
    
    def __init__(self):
        self.name = ''
        self.description = ''
        self.created = datetime.now()
        self.num_users = 0
    
    def exists(self):
        return (self.name != '' and self.description != '')
    
    def set_name(self, n):
        n = n.lower()
        if re.match("^[a-zA-Z0-9_]{3,20}$", n):
            self.name = n
            return True
        else:
            return False
    
    def set_description(self, t):
        if t.strip() != '':
            self.description = cgi.escape(t[:200], True)
            return True
        else:
            return False
    
    def get_link(self, full=False):
        if full:
            return 'http://'+APP_DOMAIN+'/community/'+self.name
        else:
            return '/community/'+self.name
