#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy, os, hashlib, random, re, cgi
from sqlalchemy import create_engine, Table, Column, ForeignKey, BigInteger, Integer, String, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from datetime import datetime, timedelta
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
    
    id = Column(BigInteger, primary_key=True)
    email = Column(String(50))
    password = Column(String(40))
    nick = Column(String(16))
    log_key = Column(String(40))
    points = Column(Integer, default=10)
    created = Column(DateTime, default=datetime.now())
    last_log_in = Column(DateTime, default=datetime.now())
    logged_on = False
    
    def __init__(self):
        self.email = ''
        self.password = ''
        self.nick = 'anonymous'
        self.log_key = ''
        self.points = 10
        self.created = datetime.now()
        self.last_log_in = datetime.now()
    
    def exists(self):
        if self.email != '' and self.password != '':
            return True
        else:
            return False
    
    def set_nick(self, n):
        if re.match("^[a-zA-Z0-9_]{4,16}$", n) and n != 'anonymous':
            if n == self.nick:
                return True
            elif not Ke_session.query(Ke_user).filter_by(nick=n).first():
                self.nick = n
                return True
            else:
                return False
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
            if e == self.email:
                return True
            elif not Ke_session.query(Ke_user).filter_by(email=e).first():
                self.email = e
                return True
            else:
                return False
        else:
            return False
    
    def is_admin(self):
        if self.nick in APP_ADMINS:
            return True
        else:
            return False
    
    def new_log_key(self):
        self.log_key = hashlib.sha1( str(random.randint(0, 999999)) ).hexdigest()
        self.last_log_in = datetime.now()
        self.logged_on = True
    
    def add_points(self, p):
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
            self.description = cgi.escape(t[:200], True)
            return True
        else:
            return False
    
    def get_link(self, full=False):
        if full:
            return APPDOMAIN+'/community/'+self.name
        else:
            return '/community/'+self.name


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
    
    def get_resume(self):
        return self.text[:200]
    
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
    
    def add_reward(self, p):
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
    
    def __init__(self):
        self.text = ''
        self.created = datetime.now()
        self.grade = 0
    
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
    
    def add_grade(self, p):
        try:
            v = int(p)
        except:
            v = 0
        if v != 0:
            self.grade += v
    
    def get_link(self, full=False):
        if full:
            return APPDOMAIN+'/question/'+str(self.question_id)
        else:
            return '/question/'+str(self.question_id)


class Super_cache:
    users = []
    communities = []
    questions = []
    chat_log = []
    chat_users = []
    searches = []
    stats = {
        'uptime': datetime.now(),
        'served_pages': 0,
        'users': 0,
        'users_m': 0,
        'communities': 0,
        'communities_m': 0,
        'questions': 0,
        'questions_m': 0,
        'searches': 0
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
                    self.give_points2user(u)
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
                self.give_points2user(u)
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
                self.give_points2user(u)
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
    
    def give_points2user(self, u):
        if u.logged_on and random.randint(0, 99) == 0:
            u.add_points(+1)
            try:
                Ke_session.add(u)
                Ke_session.commit()
            except:
                Ke_session.rollback()
    
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
                    self.increase_reward2question(q)
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
    
    def increase_reward2question(self, q):
        if q.exists() and random.randint(0, 99) == 0:
            q.add_reward(1)
            try:
                Ke_session.add(q)
                Ke_session.commit()
            except:
                Ke_session.rollback()
    
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
            if self.chat_users[i][0] == ip and self.chat_users[i][1].nick == user.nick:
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
    
    def new_search(self, query):
        encontrada = False
        for s in self.searches:
            if s[0] == query:
                s[1] += 1
                encontrada = True
                break
        if not encontrada:
            self.searches.append([query, 1])
        return Ke_session.query(Ke_question).filter(Ke_question.text.like('%'+query+'%'))
    
    def get_searches(self):
        return self.searches
    
    def get_stats(self):
        self.stats['users_m'] = len(self.users)
        self.stats['communities_m'] = len(self.communities)
        self.stats['questions_m'] = len(self.questions)
        return self.stats
    
    def get_full_stats(self):
        if random.randint(0, 9) == 0:
            self.stats['users'] = Ke_session.query(Ke_user).count()
            self.stats['users_m'] = len(self.users)
            self.stats['communities'] = Ke_session.query(Ke_community).count()
            self.stats['communities_m'] = len(self.communities)
            self.stats['questions'] = Ke_session.query(Ke_question).count()
            self.stats['questions_m'] = len(self.questions)
            self.stats['searches'] = 0
            for s in self.searches:
                self.stats['searches'] += s[1]
        return self.stats
    
    def add_served_pages(self):
        self.stats['served_pages'] += 1


class Ke_web:
    sc = Super_cache()
    current_user = Ke_user()
    ke_data = ke_data = {
        'appname': APP_NAME,
        'appdomain': APP_DOMAIN,
        'user': current_user
    }
    
    def first_step(self, title):
        self.fast_log_in()
        self.sc.add_served_pages()
        if title == 'stats':
            self.ke_data['stats'] = self.sc.get_full_stats()
        else:
            self.ke_data['stats'] = self.sc.get_stats()
        self.ke_data['rpage'] = title
        self.ke_data['errormsg'] = False
        self.ke_data['message'] = False
    
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
                try:
                    Ke_session.add(user)
                    Ke_session.commit()
                    self.set_current_user(user)
                    self.set_cookie('user_id', user.id)
                    self.set_cookie('log_key', user.log_key)
                except:
                    Ke_session.rollback()
                    self.ke_data['errormsg'] = 'error al actualizar la base de datos'
            else:
                self.ke_data['errormsg'] = u'contraseña incorrecta'
        if not self.ke_data['errormsg']:
            raise cherrypy.HTTPRedirect('/')
    
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
            user = Ke_user()
            if not user.set_email(email):
                self.ke_data['errormsg'] = u'el email no es válido o ya existe'
            elif not user.set_password(passwd):
                self.ke_data['errormsg'] = u'la contraseña no es válida (debe contener entre 4 y 20 caracteres alfanuméricos)'
            elif not user.set_nick(nick):
                self.ke_data['errormsg'] = u'el nombre de usuario no es válido (debe contener entre 4 y 16 caracteres alfanuméricos) o ya existe'
            else:
                try:
                    user.new_log_key()
                    self.set_current_user(user)
                    Ke_session.add(user)
                    Ke_session.commit()
                    self.set_cookie('user_id', user.id)
                    self.set_cookie('log_key', user.log_key)
                except:
                    Ke_session.rollback()
                    self.ke_data['errormsg'] = 'error al guardar el usuario en la base de datos'
        if not self.ke_data['errormsg']:
            raise cherrypy.HTTPRedirect('/')
    
    def update_user(self, email='', nick='', passwd='', npasswd='', npasswd2=''):
        if email == '':
            self.ke_data['errormsg'] = 'introduce un email'
        elif nick == '':
            self.ke_data['errormsg'] = 'introduce un nombre de usuario'
        elif not self.current_user.set_email(email):
            self.ke_data['errormsg'] = u'el email no es válido o ya existe'
        elif not self.current_user.set_nick(nick):
            self.ke_data['errormsg'] = u'el nombre de usuario no es válido (debe contener entre 4 y 16 caracteres alfanuméricos) o ya existe'
        else:
            if passwd != '':
                if self.current_user.password != hashlib.sha1(passwd).hexdigest():
                    self.ke_data['errormsg'] = u'introduce tu actual contraseña'
                elif npasswd == '' or npasswd2 == '':
                    self.ke_data['errormsg'] = u'introduce la nueva contraseña (dos veces)'
                elif npasswd != npasswd2:
                    self.ke_data['errormsg'] = u'las nuevas contraseñas no coinciden'
                elif not self.current_user.set_password(npasswd):
                    self.ke_data['errormsg'] = u'la contraseña no es válida (debe contener entre 4 y 20 caracteres alfanuméricos)'
            try:
                Ke_session.add(self.current_user)
                Ke_session.commit()
                self.ke_data['message'] = 'usuario modificado correctamente'
            except:
                Ke_session.rollback()
                self.ke_data['errormsg'] = 'error al guardar el usuario en la base de datos'
    
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
                        self.current_user.add_points(-1)
                        Ke_session.add(self.current_user)
                        Ke_session.commit()
                    except:
                        Ke_session.rollback()
                        self.ke_data['errormsg'] = 'error al guardar la comunidad en la base de datos'
        return community
    
    def new_question(self, text=''):
        question = Ke_question()
        if text == '':
            self.ke_data['errormsg'] = 'introduce algo de texto!'
        else:
            if not question.set_text(text):
                self.ke_data['errormsg'] = u'introduce texto válido'
            else:
                question.user = self.current_user
                for c in self.current_user.communities:
                    question.communities.append(c)
                try:
                    Ke_session.add(question)
                    Ke_session.commit()
                except:
                    Ke_session.rollback()
                    self.ke_data['errormsg'] = 'error al guardar la pregunta en la base de datos'
        return question
    
    def add_reward2question(self, idq=''):
        if self.current_user.logged_on:
            if self.current_user.points > 0:
                question = self.sc.get_question_by_id(idq)
                if question:
                    question.add_reward(1)
                    self.current_user.add_points(-1)
                    try:
                        Ke_session.commit()
                        return 'OK;'+str(question.reward)+';'+str(self.current_user.points)
                    except:
                        Ke_session.rollback()
                        return u'Error al procesar la petición'
                else:
                    return 'Pregunta no encontrada'
            else:
                return 'No tienes suficientes puntos'
        else:
            return u'Debes iniciar sesión'
    
    def get_front_questions(self):
        mixto = []
        if self.current_user.logged_on:
            for q in self.current_user.questions[-10:]:
                if q.updated > (datetime.today() - timedelta(days=7)):
                    mixto.insert(0, q)
        choice = random.randint(0, 2)
        if choice == 0:
            for q in Ke_session.query(Ke_question).order_by(Ke_question.id.desc())[0:20]:
                if q not in mixto:
                    mixto.append(q)
        elif choice == 1:
            for q in Ke_session.query(Ke_question).order_by(Ke_question.reward.desc())[0:20]:
                if q not in mixto:
                    mixto.append(q)
        else:
            for q in Ke_session.query(Ke_question).order_by(Ke_question.num_answers)[0:20]:
                if q not in mixto:
                    mixto.append(q)
        return mixto
    
    def new_answer(self, idq='', text=''):
        question = self.sc.get_question_by_id(idq)
        if question.exists():
            if text != '':
                answer = Ke_answer()
                if answer.set_text(text):
                    answer.user = self.current_user
                    answer.question = question
                    question.num_answers = len( question.answers )
                    if question.status == 0:
                        question.set_status(1)
                    try:
                        Ke_session.add(answer)
                        Ke_session.add(question)
                        Ke_session.commit()
                        self.ke_data['message'] = 'respuesta guardada correctamente'
                    except:
                        Ke_session.rollback()
                        self.ke_data['errormsg'] = 'error al guardar la respuesta en la base de datos'
                else:
                    self.ke_data['errormsg'] = u'introduce texto válido'
        else:
            self.ke_data['errormsg'] = 'pregunta no encontrada'
        return question
