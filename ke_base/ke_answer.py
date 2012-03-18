#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgi
from sqlalchemy import Table, Column, ForeignKey, BigInteger, Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timedelta
from ke_config import *
from ke_user import *
from ke_question import *


# clase de respuesta ya mapeada con sqlalchemy
class Ke_answer(Base):
    __tablename__ = 'answers'
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(BigInteger, primary_key=True)
    text = Column(Text)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    question_id = Column(BigInteger, ForeignKey('questions.id'))
    created = Column(DateTime, default=datetime.now())
    grade = Column(Integer, default=0)
    user = relationship('Ke_user', backref=backref('answers'))
    question = relationship('Ke_question', backref=backref('answers'))
    num = 1
    
    def __init__(self):
        self.text = ''
        self.created = datetime.now()
        self.grade = 0
    
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
    
    def get_link(self, full=False):
        if full:
            return 'http://'+APP_DOMAIN+'/question/'+str(self.question_id)
        else:
            return '/question/'+str(self.question_id)
