#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy, os, hashlib, random, re, cgi
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from ke_config import *

# iniciamos la clase declarativa para poder crear clases ya mapeadas
Base = declarative_base()

# creamos el engine para sqlalchemy
Ke_engine = create_engine("mysql://%s:%s@%s:%s/%s" % (MYSQL_USER, MYSQL_PASS, MYSQL_HOST, MYSQL_PORT, MYSQL_DBNAME),
                          encoding='utf-8', echo=APP_DEBUG)

# Iniciamos la sesión QUE DEBEMOS INSTANCIAR cada vez que queramos hablar con la base de datos
Ke_session = sessionmaker(bind=Ke_engine)

# clase de usuario ya mapeada con sqlalchemy
class Ke_user(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(50))
    password = Column(String(40))
    nick = Column(String(20))
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
    
    def get_id(self):
        return self.id
    
    def get_nick(self):
        return self.nick
    
    def set_nick(self, n):
        if re.match("^[a-zA-Z0-9_]{4,20}$", n):
            self.nick = n
            return True
        else:
            return False
    
    def get_password(self):
        return self.password
    
    def set_password(self, p):
        if re.match("^[a-zA-Z0-9_]{4,20}$", p):
            self.password = hashlib.sha1(p).hexdigest()
            return True
        else:
            return False
    
    def get_email(self):
        return self.email
    
    def set_email(self, e):
        if re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", e):
            self.email = e
            return True
        else:
            return False
    
    def is_admin(self):
        return self.admin
    
    def set_admin(self, a):
        self.admin = a
    
    def get_loggin_key(self):
        return self.loggin_key
    
    def new_loggin_key(self):
        self.loggin_key = hashlib.sha1( str(random.randint(0, 999999)) ).hexdigest()
        self.logged_on = True
    
    def is_logged_on(self):
        return self.logged_on
    
    def set_logged_on(self, l):
        self.logged_on = l


# clase de comunidad ya mapeada con sqlalchemy
class Ke_community(Base):
    __tablename__ = 'communities'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    
    def __init__(self, n=''):
        self.name = n
    
    def __repr__(self):
        return "<Ke_community('%s')>" % (self.name)
    
    def get_id(self):
        return self.id
    
    def get_name(self):
        return self.name
    
    def set_name(self, n):
        if re.match("^[a-zA-Z0-9_]{3,20}$", n):
            self.name = n
            return True
        else:
            return False


# clase de pregunta ya mapeada con sqlalchemy
class Ke_question(Base):
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    resume = Column(String(200))
    email = Column(String(50))
    
    def __init__(self, t='', e=''):
        self.text = t
        self.resume = t[:200]
        self.email = e
    
    def __repr__(self):
        return "<Ke_question('%s', '%s')>" % (self.resume, self.email)
    
    def get_text(self):
        return self.text
    
    def set_text(self, t):
        if t.strip() != '':
            self.text = cgi.escape(t, True)
            return True
        else:
            return False
    
    def get_resume(self):
        return self.resume
    
    def set_resume(self, r):
        if r.strip() != '':
            self.resume = cgi.escape(r[:200], True)
            return True
        else:
            return False
    
    def get_email(self):
        return self.email
    
    def set_email(self, e):
        if re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", e):
            self.email = e
            return True
        else:
            return False


class Super_cache:
    users = []
    communities = []
    questions = []
    chat_log = []
    stats = {
        'uptime': datetime.now(),
        'served_pages': 0,
        'users': 0,
        'communities': 0,
        'questions': 0
    }
    
    def get_user_by_email(self, email):
        encontrado = False
        for u in self.users:
            if u.get_email() == email:
                user = u
                encontrado = True
                break
        if not encontrado:
            session = Ke_session()
            user = session.query(Ke_user).filter_by(email=email).first()
            session.close()
        return user
    
    def get_all_users(self):
        session = Ke_session()
        users = session.query(Ke_user).order_by(Ke_user.nick).all()
        session.close()
        return users
    
    def user2memory(self, user):
        encontrado = False
        for u in self.users:
            if u.get_email() == user.get_email():
                encontrado = True
                u = user
                break
        if not encontrado:
            self.users.append(user)
    
    def get_cookie(self, name):
        value = ''
        try:
            value = cherrypy.request.cookie[name].value
        except:
            pass
        return value
    
    def set_cookie(self, name, value, expires=3600):
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
            elif user.get_password() == hashlib.sha1(passwd).hexdigest():
                user.new_loggin_key()
                session.commit()
                self.user2memory(user)
                self.set_cookie('email', user.get_email(), 3600)
                self.set_cookie('loggin_key', user.get_loggin_key(), 3600)
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
                if user2.get_loggin_key() == loggin_key:
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
                    if user.get_nick() == APP_OWNER:
                        user.set_admin(True)
                    try:
                        user.new_loggin_key()
                        session.add(user)
                        session.commit()
                        self.user2memory(user)
                        self.set_cookie('email', user.get_email(), 3600)
                        self.set_cookie('loggin_key', user.get_loggin_key(), 3600)
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
            if c.get_name() == n:
                community = c
                encontrado = True
                break
        if not encontrado:
            session = Ke_session()
            community = session.query(Ke_community).filter_by(name=n).first()
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
    
    def get_all_questions(self):
        session = Ke_session()
        questions = session.query(Ke_question).all()
        session.close()
        return questions
    
    def new_question(self, text='', email=''):
        question = False
        error_msg = False
        if text == '':
            error_msg = 'introduce algo de texto'
        else:
            question = Ke_question()
            if not question.set_text(text):
                error_msg = 'introduce texto valido'
            elif not question.set_resume(text):
                error_msg = 'introduce texto valido'
            elif not question.set_email(email):
                error_msg = 'introduce un email valido'
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
        text = cgi.escape(text.strip(), True)
        self.chat_log.append('<i>' + str(datetime.now()) + '</i> - <b>' + nick + '</b>&gt; ' + text + '<br/>')
    
    def get_stats(self):
        self.stats['users'] = len(self.users)
        self.stats['communities'] = len(self.communities)
        self.stats['questions'] = len(self.questions)
        return self.stats
    
    def sum_served_pages(self):
        self.stats['served_pages'] += 1


class Ke_web:
    sc = Super_cache()
    current_user = Ke_user()
    
    def get_current_user(self):
        return self.current_user
    
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
        if user:
            self.current_user = user
        return ke_data
