#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy, hashlib, random, re, cgi, smtplib
from sqlalchemy import Table, Column, ForeignKey, BigInteger, Integer, String, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
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
        if self.email != '' and self.nick != '':
            return True
        else:
            return False
    
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
        if self.nick in APP_ADMINS:
            return True
        else:
            return False
    
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
        if len(self.text) > 200:
            return self.text[:200]+'...'
        else:
            return self.text
    
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
        if self.status > 10:
            return True
        else:
            return False
    
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
    
    def get_link(self, full=False):
        if full:
            return 'http://'+APP_DOMAIN+'/question/'+str(self.question_id)
        else:
            return '/question/'+str(self.question_id)


class Ke_mail:
    def __init__(self):
        if not APP_DEBUG:
            self.server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            self.server.ehlo()
            if SMTP_TTLS:
                self.server.starttls()
            self.server.ehlo()
            self.server.login(SMTP_USER, SMTP_PASS)
    
    def send(self, email='', subject='', msg=''):
        if APP_DEBUG:
            self.test(email, subject, msg)
        elif email != '' and msg != '':
            mmsg = MIMEMultipart("alternative")
            mmsg['Subject'] = subject
            mmsg['From'] = APP_ADMIN_EMAIL
            mmsg['To'] = email
            part1 = MIMEText(msg, "plain", "utf-8")
            mmsg.attach(part1)
            self.server.sendmail(APP_ADMIN_EMAIL, email, mmsg.as_string().encode('ascii'))
    
    def test(self, email='', subject='', msg=''):
        if email != '' and msg != '':
            mmsg = MIMEMultipart("alternative")
            mmsg['Subject'] = subject
            mmsg['From'] = APP_ADMIN_EMAIL
            mmsg['To'] = email
            part1 = MIMEText(msg, "plain", "utf-8")
            mmsg.attach(part1)
            print '------------------------------------------------------------------'
            print email+' - '+subject
            print msg
            print '------------------------------------------------------------------'
    
    def __del__(self):
        if not APP_DEBUG:
            self.server.quit()


class Ke_web:
    current_user = Ke_user()
    ke_data = ke_data = {
        'appname': APP_NAME,
        'appdomain': APP_DOMAIN,
        'appadminemail': APP_ADMIN_EMAIL,
        'analyticsid': GOOGLE_ANALYTICS_ID,
        'adsenses': GOOGLE_ADSENSE_SQUARE_HTML,
        'description': APP_NAME,
        'user': current_user,
        'stats': {
            'uptime': datetime.now(),
            'served_pages': 0,
            'users': 0,
            'communities': 0,
            'questions': 0,
            'searches': 0,
            'chat_users': 0
        }
    }
    chat_log = []
    chat_users = []
    searches = []
    
    def first_step(self, title):
        # reiniciamos la sesión con la base de datos
        self.ke_data['rpage'] = title
        self.ke_data['description'] = title
        self.ke_data['errormsg'] = False
        self.ke_data['message'] = False
        self.ke_data['runonload'] = False
        self.ke_data['query'] = ''
        self.ke_data['stats']['served_pages'] += 1
        self.get_stats()
        self.fast_log_in()
    
    def set_current_user(self, user):
        self.current_user = user
        self.ke_data['user'] = self.current_user
    
    def set_page_description(self, desc):
        self.ke_data['description'] = desc
    
    def run_onload(self, f):
        self.ke_data['runonload'] = f
    
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
        req_cookie[name]['path'] = '/'
    
    def get_user_by_id(self, i):
        try:
            user = cherrypy.request.db.query(Ke_user).filter_by(id=int(i)).first()
            if user.exists():
                self.give_points2user(user)
                return user
        except:
            return Ke_user()
    
    def get_user_by_email(self, email):
        try:
            user = cherrypy.request.db.query(Ke_user).filter_by(email=email).first()
            if user.exists():
                self.give_points2user(user)
                return user
        except:
            return Ke_user()
    
    def get_user_by_nick(self, nick):
        try:
            user = cherrypy.request.db.query(Ke_user).filter_by(nick=nick).first()
            if user.exists():
                self.give_points2user(user)
                return user
        except:
            return Ke_user()
    
    def get_all_users(self):
        try:
            return cherrypy.request.db.query(Ke_user).order_by(Ke_user.nick).all()
        except:
            return []
    
    def give_points2user(self, u):
        if u.exists() and random.randint(0, 149) == 0:
            u.add_points(1)
            try:
                cherrypy.request.db.commit()
            except:
                cherrypy.request.db.rollback()
    
    def get_community_by_id(self, idc):
        try:
            community = cherrypy.request.db.query(Ke_community).filter_by(id=int(idc)).first()
            if community.exists():
                return community
        except:
            return Ke_community()
    
    def get_community_by_name(self, n):
        try:
            community = cherrypy.request.db.query(Ke_community).filter_by(name=n).first()
            if community.exists():
                return community
        except:
            return Ke_community()
    
    def get_all_communities(self):
        try:
            return cherrypy.request.db.query(Ke_community).order_by(Ke_community.name).all()
        except:
            return []
    
    def get_question_by_id(self, i):
        try:
            question = cherrypy.request.db.query(Ke_question).filter_by(id=int(i)).first()
            if question.exists():
                self.increase_reward2question(question)
                return question
        except:
            return Ke_question()
    
    def get_all_questions(self, order='created', num=0):
        try:
            query = cherrypy.request.db.query(Ke_question)
            if order == 'updated':
                return query.order_by(Ke_question.updated.desc())[num:num+50]
            elif order == 'reward':
                return query.order_by(Ke_question.reward.desc())[num:num+50]
            elif order == 'status':
                return query.order_by(Ke_question.status)[num:num+50]
            elif order == 'author':
                return query.order_by(Ke_question.user_id)[num:num+50]
            else:
                return query.order_by(Ke_question.id.desc())[num:num+50]
        except:
            return []
    
    def increase_reward2question(self, q):
        if q.exists() and not q.is_solved() and random.randint(0, 99) == 0:
            q.add_reward(1)
            try:
                cherrypy.request.db.commit()
            except:
                cherrypy.request.db.rollback()
    
    def new_chat_msg(self, text=''):
        if len(self.chat_log) > 100:
            del self.chat_log[75:]
        else:
            i = 0
            while i < len(self.chat_log):
                if self.chat_log[i][0] < (datetime.today() - timedelta(hours=3)):
                    del self.chat_log[i]
                else:
                    i += 1
        if text != '':
            if not self.current_user.exists():
                ip = cherrypy.request.remote.ip.split('.')
                try:
                    nick = '%s %s.%s.X.%s' % (self.current_user.nick, ip[0], ip[1], ip[3])
                except:
                    nick = '%s %s' % (self.current_user.nick, cherrypy.request.remote.ip)
            else:
                nick = self.current_user.nick
            self.chat_log.insert(0, [datetime.now(), nick, cgi.escape(text.strip(), True)])
    
    def chat_user_alive(self):
        encontrado = False
        for c in self.chat_users:
            if c[0] == cherrypy.request.remote.ip and c[1] == self.current_user.nick:
                encontrado = True
                c[3] = datetime.today()
                break
        self.check_chat_users()
        if not encontrado:
            self.chat_users.append([cherrypy.request.remote.ip,
                                    self.current_user.nick,
                                    self.current_user.get_link(),
                                    datetime.today()])
        return self.chat_users
    
    def check_chat_users(self):
        i = 0
        while i < len(self.chat_users):
            if self.chat_users[i][3] < (datetime.today() - timedelta(minutes=2)):
                del self.chat_users[i]
            else:
                i += 1
    
    def new_search(self, query):
        query = query.strip()
        if query != '':
            encontrada = False
            for s in self.searches:
                if s[0] == query:
                    s[1] += 1
                    encontrada = True
                    break
            if not encontrada:
                self.searches.append([query, 1])
            try:
                return cherrypy.request.db.query(Ke_question).filter(Ke_question.text.like('%'+query+'%'))[:20]
            except:
                return []
        else:
            return []
    
    def get_searches(self):
        for s in self.searches:
            self.ke_data['stats']['searches'] += s[1]
        return reversed(sorted(self.searches, key=lambda x: x[1]))
    
    def get_stats(self):
        self.check_chat_users()
        self.ke_data['stats']['chat_users'] = len(self.chat_users)
        if random.randint(0, 19) == 0:
            try:
                self.ke_data['stats']['users'] = cherrypy.request.db.query(Ke_user).count()
                self.ke_data['stats']['communities'] = cherrypy.request.db.query(Ke_community).count()
                self.ke_data['stats']['questions'] = cherrypy.request.db.query(Ke_question).count()
            except:
                self.ke_data['stats']['users'] = 0
                self.ke_data['stats']['communities'] = 0
                self.ke_data['stats']['questions'] = 0
            self.ke_data['stats']['searches'] = 0
    
    def do_log_in(self, email='', passwd=''):
        if email == '':
            self.ke_data['errormsg'] = 'introduce el email'
        elif passwd == '':
            self.ke_data['errormsg'] = u'introduce la contraseña'
        else:
            try:
                user = cherrypy.request.db.query(Ke_user).filter_by(email=email).first()
                if not user:
                    self.ke_data['errormsg'] = 'usuario no encontrado'
                elif user.password == hashlib.sha1(passwd).hexdigest():
                    user.new_log_key()
                    cherrypy.request.db.commit()
                    self.set_current_user(user)
                    self.set_cookie('user_id', user.id)
                    self.set_cookie('log_key', user.log_key)
                else:
                    self.ke_data['errormsg'] = u'contraseña incorrecta'
            except:
                cherrypy.request.db.rollback()
                self.ke_data['errormsg'] = 'error al leer la base de datos'
        if not self.ke_data['errormsg']:
            raise cherrypy.HTTPRedirect('/')
    
    def fast_log_in(self):
        user = Ke_user()
        user_id = self.get_cookie('user_id')
        log_key = self.get_cookie('log_key')
        if user_id != '' and log_key != '':
            user2 = self.get_user_by_id(user_id)
            if user2.exists():
                if user2.log_key == log_key:
                    user = user2
                    user.logged_on = True
                else:
                    self.ke_data['errormsg'] = u'cookie no válida, debes volver a iniciar sesión'
                    self.do_log_out()
            else:
                self.ke_data['errormsg'] = 'tienes la cookie de un usuario que ya no existe'
                self.do_log_out()
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
        elif self.get_user_by_email(email).exists():
            self.ke_data['errormsg'] = 'el email <b>'+email+u'</b> ya está asociado a una cuenta, si ha olvidado la contraseña use el formulario de la izquierda'
        elif self.get_user_by_nick(nick).exists():
            self.ke_data['errormsg'] = 'el nick <b>'+nick+u'</b> ya está asignado a un usuario'
        else:
            user = Ke_user()
            if not user.set_email(email):
                self.ke_data['errormsg'] = u'el email no es válido'
            elif not user.set_password(passwd):
                self.ke_data['errormsg'] = u'la contraseña no es válida (debe contener entre 4 y 20 caracteres alfanuméricos)'
            elif not user.set_nick(nick):
                self.ke_data['errormsg'] = u'el nombre de usuario no es válido (debe contener entre 4 y 16 caracteres alfanuméricos)'
            else:
                try:
                    user.new_log_key()
                    cherrypy.request.db.add(user)
                    cherrypy.request.db.commit()
                    self.set_current_user(user)
                    self.set_cookie('user_id', user.id)
                    self.set_cookie('log_key', user.log_key)
                except:
                    cherrypy.request.db.rollback()
                    self.ke_data['errormsg'] = 'error al guardar el usuario en la base de datos'
        if not self.ke_data['errormsg']:
            raise cherrypy.HTTPRedirect('/')
    
    def update_user(self, email='', passwd='', npasswd='', npasswd2=''):
        if not self.current_user.logged_on:
            self.ke_data['errormsg'] = u'debes iniciar sesión o crear una cuenta'
        elif email == '':
            self.ke_data['errormsg'] = 'introduce un email'
        elif not self.current_user.set_email(email):
            cherrypy.request.db.rollback()
            self.ke_data['errormsg'] = u'el email no es válido o ya existe'
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
                cherrypy.request.db.commit()
                self.ke_data['message'] = 'usuario modificado correctamente'
            except:
                cherrypy.request.db.rollback()
                self.ke_data['errormsg'] = 'error al guardar el usuario en la base de datos'
    
    def do_log_out(self):
        self.set_cookie('user_id', '', 0)
        self.set_cookie('log_key', '', 0)
        self.set_current_user( Ke_user() )
    
    def forgotten_password_email(self, email=''):
        if email != '':
            user = self.get_user_by_email(email)
            if user.exists():
                kmail = Ke_mail()
                kmail.send(user.email, u"Contraseña olvidada", u"Hola %s, te enviamos este email porque tienes problemas para entrar en %s. Haz clic en este enlace %s para iniciar sesión, y posteriormente cambiar la contraseña. Bye!" % (user.nick, APP_DOMAIN, 'http://'+APP_DOMAIN+'/forgotten_password/'+str(user.id)+'/'+user.password))
                return u"<div class='message'>se ha enviado un email con las instrucciones</div>"
            else:
                return u"<div class='error'>el email que has proporcionado no está en nuestra base de datos</div>"
        else:
            return u"<div class='error'>no has introducido ningún email</div>"
    
    def forgotten_password_log_in(self, idu='', passwd=''):
        errormsg = ''
        if idu != '' and passwd != '':
            user = self.get_user_by_id(idu)
            if user.exists():
                if user.password == passwd:
                    try:
                        user.new_log_key()
                        cherrypy.request.db.commit()
                        self.set_current_user(user)
                        self.set_cookie('user_id', user.id)
                        self.set_cookie('log_key', user.log_key)
                    except:
                        cherrypy.request.db.rollback()
                        errormsg = 'error al guardar el usuario en la base de datos'
                else:
                    errormsg = 'Datos incorrectos'
            else:
                errormsg = 'El usuario no existe'
        else:
            errormsg = 'No, no, no.'
        return errormsg
    
    def new_community(self, n='', d=''):
        community = Ke_community()
        if n == '':
            self.ke_data['errormsg'] = 'introduce un nombre para la comunidad'
        elif d == '':
            self.ke_data['errormsg'] = u'introduce una descripción para la comunidad'
        elif not self.current_user.logged_on:
            self.ke_data['errormsg'] = u'debes iniciar sesión o crear una cuenta'
        elif self.current_user.points < 1:
            self.ke_data['errormsg'] = 'no tienes suficientes puntos'
        elif self.get_community_by_name(n).exists():
            self.ke_data['errormsg'] = 'la comunidad ya existe'
        else:
            community = Ke_community()
            if not community.set_name(n):
                self.ke_data['errormsg'] = u'introduce un nombre válido (debe contener entre 3 y 20 caracteres alfanuméricos)'
            elif not community.set_description(d):
                self.ke_data['errormsg'] = u'introduce una descripción válida'
            else:
                try:
                    cherrypy.request.db.add(community)
                    self.current_user.add_points(-1)
                    cherrypy.request.db.commit()
                except:
                    cherrypy.request.db.rollback()
                    self.ke_data['errormsg'] = 'error al guardar la comunidad en la base de datos'
        return community
    
    def new_question(self, text=''):
        question = Ke_question()
        if text == '':
            self.ke_data['errormsg'] = 'introduce algo de texto!'
        elif not self.current_user.logged_on:
            self.ke_data['errormsg'] = u'debes iniciar sesión o crear una cuenta'
        else:
            if not question.set_text(text):
                self.ke_data['errormsg'] = u'introduce texto válido'
            else:
                question.user = self.current_user
                for c in self.current_user.communities:
                    question.communities.append(c)
                try:
                    cherrypy.request.db.add(question)
                    cherrypy.request.db.commit()
                except:
                    cherrypy.request.db.rollback()
                    self.ke_data['errormsg'] = 'error al guardar la pregunta en la base de datos'
        return question
    
    def add_reward2question(self, idq=''):
        if self.current_user.logged_on:
            if self.current_user.points > 0:
                question = self.get_question_by_id(idq)
                if question.exists():
                    if not question.is_solved():
                        question.add_reward(1)
                        self.current_user.add_points(-1)
                        try:
                            cherrypy.request.db.commit()
                            return 'OK;'+str(question.reward)+';'+str(self.current_user.points)
                        except:
                            cherrypy.request.db.rollback()
                            return u'Error al procesar la petición'
                    else:
                        return u'No puedes añadir recompensa a un pregunta solucionada'
                else:
                    return 'Pregunta no encontrada'
            else:
                return 'No tienes suficientes puntos'
        else:
            return u'Debes iniciar sesión o crear una cuenta'
    
    def get_front_questions(self):
        finalmix = []
        mixto = []
        try:
            # últimas actualizaciones
            for q in cherrypy.request.db.query(Ke_question).order_by(Ke_question.updated.desc())[0:10]:
                mixto.append(q)
            # preguntas con mayor recompensa
            for q in cherrypy.request.db.query(Ke_question).order_by(Ke_question.reward.desc())[0:10]:
                if q not in mixto:
                    mixto.append(q)
            # preguntas del usuario
            if self.current_user.logged_on:
                for q in self.current_user.questions[-5:]:
                    if q.updated > (datetime.today() - timedelta(days=7)) and q not in mixto:
                        mixto.append(q)
        except:
            pass
        # ordenamos por fecha pero dejando las preguntas solucionadas al final
        while len(mixto) > 0:
            seleccion = mixto[0]
            for m in mixto:
                if seleccion.is_solved():
                    seleccion = m
                elif m.updated > seleccion.updated:
                    seleccion = m
            mixto.remove(seleccion)
            finalmix.append(seleccion)
        return finalmix
    
    def get_answers(self, idq, order='normal'):
        answers = []
        try:
            aux = cherrypy.request.db.query(Ke_answer).filter_by(question_id=idq).order_by(Ke_answer.created).all()
        except:
            aux = False
        if aux:
            # numeramos
            mgrade = 0
            i = 0
            while i < len(aux):
                aux[i].num = i+1
                if aux[i].grade > 0:
                    mgrade = aux[i].grade
                i += 1
            if order == 'grade':
                # ordenamos teniendo en cuenta las meciones.
                while len(aux) > 0:
                    # seleccionar
                    i = len(aux)-1
                    answer = aux[0]
                    while i > 0:
                        if aux[i].grade > answer.grade:
                            answer = aux[i]
                        i -= 1
                    aux.remove(answer)
                    # dónde la meto?
                    if len(answers) < 1:
                        answers.append(answer)
                    else:
                        # ha sido mencionada por alguna pregunta previamente seleccionada?
                        mention = False
                        position = 0
                        for a in answers:
                            if a.text.find('@'+str(answer.num)+' ') != -1:
                                # si, ha sido mencionada
                                mention = True
                                answers.insert(position, answer)
                                break
                            position += 1
                        if not mention:
                            # menciona alguna respuesta previamente seleccionada?
                            position = 0
                            for a in answers:
                                if answer.text.find('@'+str(a.num)+' ') != -1:
                                    # si, si que menciona alguna
                                    mention = True
                                    answers.insert(position+1, answer)
                                    break
                                position += 1
                        # nada de nada?
                        if not mention:
                            answers.append(answer)
            else: # orden por fecha
                answers = aux
        return answers
    
    def new_answer(self, idq='', text=''):
        question = self.get_question_by_id(idq)
        answer = Ke_answer()
        if question.exists():
            if text != '':
                if self.current_user.logged_on:
                    if answer.set_text(text):
                        answer.user = self.current_user
                        answer.question = question
                        question.num_answers = len( question.answers )
                        question.updated = datetime.today()
                        if question.status == 0:
                            question.set_status(1)
                        try:
                            cherrypy.request.db.add(answer)
                            cherrypy.request.db.commit()
                            self.ke_data['message'] = u'respuesta guardada correctamente <a href="#'+str(len(question.answers))+'">@'+str(len(question.answers))+'</a>'
                        except:
                            cherrypy.request.db.rollback()
                            self.ke_data['errormsg'] = u'error al guardar la respuesta en la base de datos'
                    else:
                        self.ke_data['errormsg'] = u'introduce texto válido'
                else:
                    self.ke_data['errormsg'] = u'debes <a href="/log_in">iniciar sesión</a> o <a href="/log_in">crear una cuenta</a>'
        else:
            self.ke_data['errormsg'] = u'pregunta no encontrada'
        return question,answer
    
    def new_vote2answer(self, ida='', points=1):
        message = ''
        try:
            answer = cherrypy.request.db.query(Ke_answer).filter_by(id=ida).first()
        except:
            answer = False
        if answer:
            if self.current_user.exists() and self.current_user.logged_on:
                if self.current_user.points > 0:
                    if self.current_user.id != answer.user.id:
                        self.current_user.add_points(-1)
                        if points > 0:
                            answer.grade += 1
                            answer.user.add_points(1)
                            message = 'OK;'+ida+';'+str(answer.grade)+';'+str(self.current_user.points)
                        elif points < 0:
                            answer.grade -= 1
                            answer.question.add_reward(1)
                            message = 'OK;'+ida+';'+str(answer.grade)+';'+str(self.current_user.points)
                        else:
                            self.current_user.add_points(1)
                            message = u'voto incorrecto'
                        try:
                            cherrypy.request.db.commit()
                        except:
                            cherrypy.request.db.rollback()
                            message = u'Error al guardar los datos en la base de datos'
                    else:
                        message = u'¿Pretendes votarte a ti mismo?'
                else:
                    message = u'No tienes suficientes puntos'
            else:
                message = u'Debes iniciar sesión o crear una cuenta'
        else:
            message = u'respuesta no encontrada'
        return message
    
    def mark_answer_as_solution(self, ida=''):
        message = ''
        try:
            answer = cherrypy.request.db.query(Ke_answer).filter_by(id=ida).first()
        except:
            answer = False
        if answer:
            if self.current_user.exists() and self.current_user.logged_on:
                if self.current_user == answer.user or self.current_user.is_admin():
                    if not answer.question.is_solved():
                        answer.grade += answer.question.reward
                        answer.user.add_points( answer.question.reward )
                        answer.question.reward = 0
                        answer.question.set_status(11)
                        answer.question.updated = datetime.today()
                        self.current_user.add_points(5)
                        try:
                            cherrypy.request.db.commit()
                            message = u'OK'
                        except:
                            cherrypy.request.db.rollback()
                            message = u'Error al guardar los datos en la base de datos'
                    else:
                        message = u'La pregunta ya está marcada como solucionada'
                else:
                    message = u'Tu no puedes hacer esto, chaval!'
            else:
                message = u'Debes iniciar sesión o crear una cuenta'
        else:
            message = u'respuesta no encontrada'
        return message
