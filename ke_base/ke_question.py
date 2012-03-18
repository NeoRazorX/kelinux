#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgi
from sqlalchemy import Table, Column, ForeignKey, BigInteger, Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timedelta
from ke_config import *
from ke_user import *
from ke_community import *


# tabla necesaria para la relación muchos a muchos entre Ke_community y Ke_question
Ke_community_question_table = Table('community_question', Base.metadata,
    Column('communities_id', BigInteger, ForeignKey('communities.id')),
    Column('questions_id', BigInteger, ForeignKey('questions.id'))
)


# clase de pregunta ya mapeada con sqlalchemy
class Ke_question(Base):
    __tablename__ = 'questions'
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(BigInteger, primary_key=True)
    text = Column(Text)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    created = Column(DateTime, default=datetime.now())
    updated = Column(DateTime, default=datetime.now())
    num_answers = Column(Integer, default=0)
    status = Column(Integer, default=0)
    reward = Column(Integer, default=1)
    user = relationship('Ke_user', backref=backref('questions'))
    communities = relationship("Ke_community", secondary=Ke_community_question_table, backref=backref('questions'))
    
    def __init__(self):
        self.text = ''
        self.created = datetime.now()
        self.updated = datetime.now()
        self.num_answers = 0
        self.status = 0
        self.reward = 1
    
    def exists(self):
        return (self.text != '')
    
    def set_text(self, t):
        if t.strip() != '':
            self.text = cgi.escape(t, True)
            return True
        else:
            return False
    
    def get_resume(self):
        if len(self.text) > 200:
            return self.text[:200].replace("\n",' ')+'...'
        else:
            return self.text.replace("\n",' ')
    
    def set_status(self, s=-1):
        try:
            s = int(s)
        except:
            s = -1
        if self.get_status(s) != 'estado desconocido':
            self.status = s
            return True
        else:
            return False
    
    def get_status(self, s=None):
        if s is None:
            s = self.status
        if s == 0:
            return 'nueva'
        elif s == 1:
            return 'abierta'
        elif s == 2:
            return 'incompleta'
        elif s == 9:
            return 'parcialmente solucionada'
        elif s == 10:
            return u'pendiente de confirmación'
        elif s == 11:
            return 'solucionada'
        elif s == 20:
            return 'duplicada'
        elif s == 21:
            return 'erronea'
        elif s == 22:
            return 'antigua'
        else:
            return 'estado desconocido'
    
    def is_solved(self):
        return (self.status > 10)
    
    def add_reward(self, p):
        try:
            p = int(p)
        except:
            p = 0
        if p > 0:
            self.reward += p
    
    def get_link(self, full=False):
        if full:
            return 'http://'+APP_DOMAIN+'/question/'+str(self.id)
        else:
            return '/question/'+str(self.id)
