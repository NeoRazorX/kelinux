#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy, os, hashlib, random, re, cgi
from sqlalchemy import create_engine, Column, ForeignKey, Integer, String, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from datetime import datetime
from ke_config import *

# iniciamos la clase declarativa para poder crear clases ya mapeadas
Base = declarative_base()

# creamos el engine para sqlalchemy
Ke_engine = create_engine("mysql://%s:%s@%s:%s/%s" % (MYSQL_USER, MYSQL_PASS, MYSQL_HOST, MYSQL_PORT, MYSQL_DBNAME),
                          encoding='utf-8', convert_unicode=True, echo=APP_DEBUG)

# Iniciamos la sesión QUE DEBEMOS INSTANCIAR cada vez que queramos hablar con la base de datos
Ke_session = sessionmaker(bind=Ke_engine)

# clase de usuario ya mapeada con sqlalchemy
class Ke_user(Base):
    __tablename__ = 'users'
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(Integer, primary_key=True)
    email = Column(String(50))
    password = Column(String(40))
    nick = Column(String(18))
    admin = Column(Boolean)
    loggin_key = Column(String(40))
    
    logged_on = False
    
    def __init__(self, e='', p='', n='anonymous', a=False):
        self.email = e
        self.password = p
        self.nick = n
        self.admin = a
    
    def __repr__(self):
        return "<Ke_user('%s','%s')>" % (self.email, self.nick)
    
    def set_nick(self, n):
        if re.match("^[a-zA-Z0-9_]{4,18}$", n):
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
    
    def set_admin(self, a):
        self.admin = a
    
    def new_loggin_key(self):
        self.loggin_key = hashlib.sha1( str(random.randint(0, 999999)) ).hexdigest()
        self.logged_on = True
    
    def set_logged_on(self, l):
        self.logged_on = l


# clase de comunidad ya mapeada con sqlalchemy
class Ke_community(Base):
    __tablename__ = 'communities'
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    num_users = Column(Integer, default=0)
    
    def __init__(self, n=''):
        self.name = n
        self.num_users = 0
    
    def __repr__(self):
        return "<Ke_community('%s')>" % (self.name)
    
    def set_name(self, n):
        if re.match("^[a-zA-Z0-9_]{3,20}$", n):
            self.name = n
            return True
        else:
            return False


# clase de pregunta ya mapeada con sqlalchemy
class Ke_question(Base):
    __tablename__ = 'questions'
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(DateTime, default=datetime.now())
    num_responses = Column(Integer, default=0)
    
    nick = ''
    
    def __init__(self, t='', e=''):
        self.text = t
        self.date = datetime.now()
        self.num_responses = 0
    
    def __repr__(self):
        return "<Ke_question('%s', '%s')>" % (self.resume, self.email)
    
    def set_text(self, t):
        if t.strip() != '':
            self.text = cgi.escape(t, True)
            return True
        else:
            return False
    
    def get_resume(self):
        return self.text[:200]
    
    def set_user(self, u=Ke_user()):
        if u.logged_on:
            self.user_id = u.id
            self.nick = i.nick
            return True
        else:
            return False


class Super_cache:
    users = []
    communities = []
    questions = []
    chat_log = []
    chat_users = []
    stats = {
        'uptime': datetime.now(),
        'served_pages': 0,
        'users': 0,
        'communities': 0,
        'questions': 0
    }
    
    def get_user_by_id(self, i):
        encontrado = False
        for u in self.users:
            if u.id == i:
                user = u
                encontrado = True
                break
        if not encontrado:
            session = Ke_session()
            user = session.query(Ke_user).filter_by(id=i).first()
            if user:
                self.users.append(user)
            session.close()
        return user
    
    def get_user_by_email(self, email):
        encontrado = False
        for u in self.users:
            if u.email == email:
                user = u
                encontrado = True
                break
        if not encontrado:
            session = Ke_session()
            user = session.query(Ke_user).filter_by(email=email).first()
            if user:
                self.users.append(user)
            session.close()
        return user
    
    def get_all_users(self):
        session = Ke_session()
        users = session.query(Ke_user).order_by(Ke_user.nick).all()
        session.close()
        return users
    
    def get_cookie(self, name):
        value = ''
        try:
            value = cherrypy.request.cookie[name].value
        except:
            pass
        return value
    
    def set_cookie(self, name, value, expires=APP_DEFAULT_COOKIE_EXPIRATION):
        req_cookie = cherrypy.response.cookie
        req_cookie[name] = value
        req_cookie[name]['expires'] = expires
    
    def loggin(self, email='', passwd=''):
        user = False
        error_msg = False
        if email == '':
            error_msg = 'introduce el email'
        elif passwd == '':
            error_msg = 'introduce la contrasenya'
        else:
            session = Ke_session()
            user = session.query(Ke_user).filter_by(email=email).first()
            if not user:
                error_msg = 'usuario no encontrado'
            elif user.password == hashlib.sha1(passwd).hexdigest():
                user.new_loggin_key()
                session.commit()
                self.set_cookie('email', user.email)
                self.set_cookie('loggin_key', user.loggin_key)
            else:
                error_msg = 'contrasenya incorrecta'
            session.close()
        return user,error_msg
    
    def fast_loggin(self):
        user = Ke_user()
        email = self.get_cookie('email')
        loggin_key = self.get_cookie('loggin_key')
        if email != '' and loggin_key != '':
            user2 = self.get_user_by_email(email)
            if user2:
                if user2.loggin_key == loggin_key:
                    user = user2
                    user.set_logged_on(True)
        return user
    
    def register(self, email='', nick='', passwd='', passwd2=''):
        user = False
        error_msg = False
        if email == '':
            error_msg = 'introduce un email'
        elif nick == '':
            error_msg = 'introduce un nombre de usuario'
        elif passwd == '':
            error_msg = 'introduce una contrasenya'
        elif passwd != passwd2:
            error_msg = 'las contrasenyas no coinciden'
        else:
            user = self.get_user_by_email(email)
            if user:
                error_msg = 'el usuario ya existe, elige otro email'
            else:
                session = Ke_session()
                user = Ke_user()
                if not user.set_email(email):
                    error_msg = 'el email no es valido'
                elif not user.set_password(passwd):
                    error_msg = 'la contraseña no es valida'
                elif not user.set_nick(nick):
                    error_msg = 'el nombre de usuario no es valido'
                else:
                    if user.nick == APP_OWNER:
                        user.set_admin(True)
                    try:
                        user.new_loggin_key()
                        session.add(user)
                        session.commit()
                        self.set_cookie('email', user.email)
                        self.set_cookie('loggin_key', user.loggin_key)
                    except:
                        error_msg = 'error al guardar el usuario en la base de datos'
                session.close()
        return user,error_msg
    
    def loggout(self):
        self.set_cookie('email', '', 0)
        self.set_cookie('loggin_key', '', 0)
    
    def get_community_by_name(self, n):
        encontrado = False
        for c in self.communities:
            if c.name == n:
                community = c
                encontrado = True
                break
        if not encontrado:
            session = Ke_session()
            community = session.query(Ke_community).filter_by(name=n).first()
            if community:
                self.communities.append(community)
            session.close()
        return community
    
    def get_all_communities(self):
        session = Ke_session()
        communities = session.query(Ke_community).order_by(Ke_community.name).all()
        session.close()
        return communities
    
    def new_community(self, n=''):
        community = False
        error_msg = False
        if n == '':
            error_msg = 'introduce un nombre'
        else:
            community = self.get_community_by_name(n)
            if community:
                error_msg = 'la comunidad ya existe'
            else:
                community = Ke_community()
                if not community.set_name(n):
                    error_msg = 'introduce un nombre valido'
                else:
                    try:
                        session = Ke_session()
                        session.add(community)
                        session.commit()
                        session.close()
                    except:
                        error_msg = 'error al guardar la comunidad en la base de datos'
        return community,error_msg
    
    def get_question_by_id(self, i):
        encontrado = False
        for q in self.questions:
            if q.id == i:
                question = q
                encontrado = True
                break
        if not encontrado:
            session = Ke_session()
            questions = session.query(Ke_question).filter_by(id=i).first()
            if question:
                self.questions.append(question)
            session.close()
        return question
    
    def get_all_questions(self):
        session = Ke_session()
        questions = session.query(Ke_question).all()
        session.close()
        return questions
    
    def new_question(self, text='', user=Ke_user()):
        question = False
        error_msg = False
        if text == '':
            error_msg = 'introduce algo de texto'
        else:
            question = Ke_question()
            if not question.set_text(text):
                error_msg = 'introduce texto valido'
            elif not question.set_user(user):
                error_msg = 'usuario no valido: '+user.nick
            else:
                try:
                    session = Ke_session()
                    session.add(question)
                    session.commit()
                    session.close()
                except:
                    error_msg = 'error al guardar la pregunta en la base de datos'
        return question,error_msg
    
    def get_front(self):
        session = Ke_session()
        questions = session.query(Ke_question)[0:20]
        session.close()
        return questions
    
    def get_chat_log(self):
        return self.chat_log
    
    def new_chat_msg(self, text='', nick='anonymous'):
        if len(self.chat_log) > 100:
            i = 0
            while i < len(self.chat_log):
                if i > 75:
                    self.chat_log.remove( self.chat_log[i] )
                else:
                    i += 1
        text = cgi.escape(text.strip(), True)
        self.chat_log.insert(0, [datetime.now(), nick, text])
    
    def chat_user_alive(self, nick, ip):
        encontrado = False
        for cu in self.chat_users:
            if cu[0] == ip and cu[1] == nick:
                encontrado = True
                cu[2] = 20
            else:
                cu[2] -= 1
        if not encontrado:
            self.chat_users.append([ip, nick, 20])
        return self.chat_users
    
    def get_stats(self):
        self.stats['users'] = len(self.users)
        self.stats['communities'] = len(self.communities)
        self.stats['questions'] = len(self.questions)
        return self.stats
    
    def sum_served_pages(self):
        self.stats['served_pages'] += 1


class Ke_web:
    sc = Super_cache()
    
    def get_current_user(self):
        return self.sc.fast_loggin()
    
    # devuelve un array con toda la información necesaria para las templates
    def get_kedata(self, rpage='', user=False):
        if not user:
            user = self.sc.fast_loggin()
        ke_data = {
            'appname': APP_NAME,
            'appdomain': APP_DOMAIN,
            'stats': self.sc.get_stats(),
            'user': user,
            'rpage': rpage
        }
        return ke_data
