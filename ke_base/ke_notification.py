#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import Table, Column, ForeignKey, BigInteger, Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timedelta
from ke_config import *
from ke_user import *


# clase de notificación ya mapeada con sqlalchemy
class Ke_notification(Base):
    __tablename__ = 'notifications'
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    date = Column(DateTime, default=datetime.now())
    text = Column(Text)
    link = Column(String(250))
    sendmail = Column(Boolean, default=True)
    readed = Column(Boolean, default=False)
    user = relationship('Ke_user', backref=backref('notifications'))
    
    def __init__(self):
        self.date = datetime.now()
        self.text = ''
        self.link = APP_DOMAIN
        self.sendmail = True
        self.readed = False
    
    def get_link(self, full=False):
        if full:
            return 'http://'+APP_DOMAIN+self.link
        else:
            return self.link
