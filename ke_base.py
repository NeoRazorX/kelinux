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

# Iniciamos la sesión con la base de datos
sql_session = sessionmaker(bind=Ke_engine)
Ke_session = sql_session()

# clase de usuario ya mapeada con sqlalchemy
class Ke_user(Base):
    __tablename__ = 'users'
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(Integer, primary_key=True)
    email = Column(String(50))
    password = Column(String(40))
    nick = Column(String(16))
    admin = Column(Boolean, default=False)
    log_key = Column(String(40))
    points = Column(Integer, default=10)
    created = Column(DateTime, default=datetime.now())
    last_log_in = Column(DateTime, default=datetime.now())
    
    logged_on = False
    
    def __init__(self, e='', p='', n='anonymous', a=False, pts=10):
        self.email = e
        self.password = p
        self.nick = n
        self.admin = a
        self.log_key = ''
        self.points = pts
        self.created = datetime.now()
        self.last_log_in = datetime.now()
    
    def __repr__(self):
        return "<Ke_user('%s','%s')>" % (self.email, self.nick)
    
    def exists(self):
        if self.email != '' and self.password != '':
            return True
        else:
            return False
    
    def set_nick(self, n):
        if re.match("^[a-zA-Z0-9_]{4,16}$", n):
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
    
    def new_log_key(self):
        self.log_key = hashlib.sha1( str(random.randint(0, 999999)) ).hexdigest()
        self.last_log_in = datetime.now()
        self.logged_on = True
    
    def sum_points(self, p):
        try:
            v = int(p)
        except:
            v = 0
        if v != 0:
            self.points += v
            if self.points < 0:
                self.points = 0
    
    def get_link(self, full=False):
        if full:
            return APPDOMAIN+'/user/'+str(self.id)
        else:
            return '/user/'+str(self.id)
    
    def get_questions(self):
        return Ke_session.query(Ke_question).filter_by(user_id=self.id).order_by(Ke_question.id.desc()).all()


# clase de comunidad ya mapeada con sqlalchemy
class Ke_community(Base):
    __tablename__ = 'communities'
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    description = Column(String(200))
    created = Column(DateTime, default=datetime.now())
    num_users = Column(Integer, default=0)
    
    def __init__(self, n='', d=''):
        self.name = n
        self.description = d
        self.created = datetime.now()
        self.num_users = 0
    
    def __repr__(self):
        return "<Ke_community('%s')>" % (self.name)
    
    def exists(self):
        if self.name != '' and self.description != '':
            return True
        else:
            return False
    
    def set_name(self, n):
        if re.match("^[a-zA-Z0-9_]{3,20}$", n):
            self.name = n
            return True
        else:
            return False
    
    def set_description(self, t):
        if t.strip() != '':
            self.description = cgi.escape(t, True)
            return True
        else:
            return False
    
    def get_link(self, full=False):
        if full:
            return APPDOMAIN+'/community/'+self.name
        else:
            return '/community/'+self.name


# clase de pregunta ya mapeada con sqlalchemy
class Ke_question(Base):
    __tablename__ = 'questions'
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset': 'utf8'}
    
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    created = Column(DateTime, default=datetime.now())
    updated = Column(DateTime, default=datetime.now())
    num_answers = Column(Integer, default=0)
    status = Column(Integer, default=0)
    reward = Column(Integer, default=1)
    
    def __init__(self, t='', u=Ke_user()):
        self.text = t
        self.user_id = u.id
        self.created = datetime.now()
        self.updated = datetime.now()
        self.num_answers = 0
        self.status = 0
        self.reward = 1
    
    def __repr__(self):
        return "<Ke_question('%s', '%s')>" % (self.resume, self.email)
    
    def exists(self):
        if self.text != '':
            return True
        else:
            return False
    
    def set_text(self, t):
        if t.strip() != '':
            self.text = cgi.escape(t, True)
            return True
        else:
            return False
    
    def set_user(self, u):
        if u.logged_on:
            self.user_id = u.id
            return True
        else:
            return False
    
    def get_resume(self):
        return self.text[:200]
    
    def get_user(self):
        user = Ke_user()
        if self.user_id != 0:
            user2 = Ke_session.query(Ke_user).filter_by(id=self.user_id).first()
            try:
                if user2.exists():
                    user = user2
            except:
                pass
        return user
    
    def set_status(self, s):
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
    
    def sum_reward(self, p):
        try:
            v = int(p)
        except:
            v = 0
        if v > 0:
            self.reward += v
    
    def get_link(self, full=False):
        if full:
            return APPDOMAIN+'/question/'+str(self.id)
        else:
            return '/question/'+str(self.id)


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
        try:
            i2 = int(i)
        except:
            i2 = -1
        if i2 <= 0:
            user = Ke_user()
        else:
            encontrado = False
            for u in self.users:
                if u.id == i2:
                    user = u
                    encontrado = True
                    break
            if not encontrado:
                user = Ke_session.query(Ke_user).filter_by(id=i2).first()
                try:
                    if user.exists():
                        self.users.append(user)
                except:
                    user = Ke_user()
        return user
    
    def get_user_by_email(self, email):
        encontrado = False
        for u in self.users:
            if u.email == email:
                user = u
                encontrado = True
                break
        if not encontrado:
            user = Ke_session.query(Ke_user).filter_by(email=email).first()
            try:
                if user.exists():
                    self.users.append(user)
            except:
                user = Ke_user()
        return user
    
    def get_user_by_nick(self, nick):
        encontrado = False
        for u in self.users:
            if u.nick == nick:
                user = u
                encontrado = True
                break
        if not encontrado:
            user = Ke_session.query(Ke_user).filter_by(nick=nick).first()
            try:
                if user.exists():
                    self.users.append(user)
            except:
                user = Ke_user()
        return user
    
    def get_all_users(self):
        return Ke_session.query(Ke_user).order_by(Ke_user.nick).all()
    
    def get_community_by_name(self, n):
        encontrado = False
        for c in self.communities:
            if c.name == n:
                community = c
                encontrado = True
                break
        if not encontrado:
            community = Ke_session.query(Ke_community).filter_by(name=n).first()
            try:
                if community.exists():
                    self.communities.append(community)
            except:
                community = Ke_community()
        return community
    
    def get_all_communities(self):
        return Ke_session.query(Ke_community).order_by(Ke_community.name).all()
    
    def get_question_by_id(self, i):
        try:
            i2 = int(i)
        except:
            i2 = -1
        if i2 <= 0:
            question = Ke_question()
        else:
            encontrado = False
            for q in self.questions:
                if q.id == i2:
                    question = q
                    encontrado = True
                    break
            if not encontrado:
                question = Ke_session.query(Ke_question).filter_by(id=i2).first()
                try:
                    if question.exists():
                        self.questions.append(question)
                except:
                    question = Ke_question()
        return question
    
    def get_all_questions(self):
        return Ke_session.query(Ke_question).order_by(Ke_question.id.desc()).all()
    
    def get_front(self):
        return Ke_session.query(Ke_question).order_by(Ke_question.id.desc())[0:20]
    
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
    
    def chat_user_alive(self, user, ip):
        encontrado = False
        i = 0
        while i < len(self.chat_users):
            if self.chat_users[i][0] == ip and self.chat_users[i][1] == user:
                encontrado = True
                self.chat_users[i][2] = 20
            else:
                self.chat_users[i][2] -= 1
            if self.chat_users[i][2] < 1:
                self.chat_users.remove( self.chat_users[i] )
            else:
                i += 1
        if not encontrado:
            self.chat_users.append([ip, user, 20])
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
    current_user = Ke_user()
    ke_data = ke_data = {
        'appname': APP_NAME,
        'appdomain': APP_DOMAIN,
        'user': current_user
    }
    
    def first_step(self, tittle):
        self.fast_log_in()
        self.sc.sum_served_pages()
        self.ke_data['stats'] = self.sc.get_stats()
        self.ke_data['rpage'] = tittle
        self.ke_data['errormsg'] = False
    
    def set_current_user(self, user):
        self.current_user = user
        self.ke_data['user'] = self.current_user
    
    def get_cookie(self, name):
        try:
            value = cherrypy.request.cookie[name].value
        except:
            value = ''
        return value
    
    def set_cookie(self, name, value, expires=APP_DEFAULT_COOKIE_EXPIRATION):
        req_cookie = cherrypy.response.cookie
        req_cookie[name] = value
        req_cookie[name]['expires'] = expires
    
    def do_log_in(self, email='', passwd=''):
        if email == '':
            self.ke_data['errormsg'] = 'introduce el email'
        elif passwd == '':
            self.ke_data['errormsg'] = u'introduce la contraseña'
        else:
            user = Ke_session.query(Ke_user).filter_by(email=email).first()
            if not user:
                self.ke_data['errormsg'] = 'usuario no encontrado'
            elif user.password == hashlib.sha1(passwd).hexdigest():
                user.new_log_key()
                Ke_session.add(user)
                Ke_session.commit()
                self.set_current_user(user)
                self.set_cookie('user_id', user.id)
                self.set_cookie('log_key', user.log_key)
                raise cherrypy.HTTPRedirect('/')
            else:
                self.ke_data['errormsg'] = u'contraseña incorrecta'
    
    def fast_log_in(self):
        user = Ke_user()
        user_id = self.get_cookie('user_id')
        log_key = self.get_cookie('log_key')
        if user_id != '' and log_key != '':
            user2 = self.sc.get_user_by_id(user_id)
            if user2.exists():
                if user2.log_key == log_key:
                    user = user2
                    user.logged_on = True
                else:
                    self.ke_data['errormsg'] = u'cookie no válida, debes volver a iniciar sesión'
            else:
                self.ke_data['errormsg'] = 'tienes la cookie de un usuario que ya no existe'
        self.set_current_user(user)
    
    def register(self, email='', nick='', passwd='', passwd2=''):
        if email == '':
            self.ke_data['errormsg'] = 'introduce un email'
        elif nick == '':
            self.ke_data['errormsg'] = 'introduce un nombre de usuario'
        elif passwd == '':
            self.ke_data['errormsg'] = u'introduce una contraseña'
        elif passwd != passwd2:
            self.ke_data['errormsg'] = u'las contraseñas no coinciden'
        else:
            user = self.sc.get_user_by_email(email)
            if user.exists():
                self.ke_data['errormsg'] = 'el usuario ya existe, elige otro email'
            else:
                user = Ke_user()
                if not user.set_email(email):
                    self.ke_data['errormsg'] = u'el email no es válido'
                elif not user.set_password(passwd):
                    self.ke_data['errormsg'] = u'la contraseña no es válida (debe contener entre 4 y 20 caracteres alfanuméricos)'
                elif not user.set_nick(nick):
                    self.ke_data['errormsg'] = u'el nombre de usuario no es válido (debe contener entre 4 y 16 caracteres alfanuméricos)'
                else:
                    if user.nick == APP_OWNER:
                        user.set_admin(True)
                    try:
                        user.new_log_key()
                        self.set_current_user(user)
                        Ke_session.add(user)
                        Ke_session.commit()
                        self.set_cookie('user_id', user.id)
                        self.set_cookie('log_key', user.log_key)
                    except:
                        self.ke_data['errormsg'] = 'error al guardar el usuario en la base de datos'
            if not self.ke_data['errormsg']:
                raise cherrypy.HTTPRedirect('/')
    
    def do_log_out(self):
        self.set_cookie('user_id', '', 0)
        self.set_cookie('log_key', '', 0)
        self.set_current_user( Ke_user() )
    
    def new_community(self, n='', d=''):
        community = Ke_community()
        if n == '':
            self.ke_data['errormsg'] = 'introduce un nombre para la comunidad'
        elif d == '':
            self.ke_data['errormsg'] = u'introduce una descripción para la comunidad'
        elif self.current_user.points < 1:
            self.ke_data['errormsg'] = 'no tienes suficientes puntos'
        else:
            community = self.sc.get_community_by_name(n)
            if community.exists():
                self.ke_data['errormsg'] = 'la comunidad ya existe'
            else:
                if not community.set_name(n):
                    self.ke_data['errormsg'] = u'introduce un nombre válido (debe contener entre 3 y 20 caracteres alfanuméricos)'
                elif not community.set_description(d):
                    self.ke_data['errormsg'] = u'introduce una descripción válida'
                else:
                    try:
                        Ke_session.add(community)
                        self.current_user.sum_points(-1)
                        Ke_session.add(self.current_user)
                        Ke_session.commit()
                    except:
                        self.ke_data['errormsg'] = 'error al guardar la comunidad en la base de datos'
        return community
    
    def new_question(self, text=''):
        question = Ke_question()
        if text == '':
            self.ke_data['errormsg'] = 'introduce algo de texto!'
        else:
            if not question.set_text(text):
                self.ke_data['errormsg'] = u'introduce texto válido'
            elif not question.set_user( self.current_user ):
                self.ke_data['errormsg'] = u'usuario no válido: '+self.current_user.nick
            else:
                try:
                    Ke_session.add(question)
                    Ke_session.commit()
                except:
                    self.ke_data['errormsg'] = 'error al guardar la pregunta en la base de datos'
        return question
