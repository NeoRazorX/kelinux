#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cherrypy, os, hashlib, random, re
from sqlalchemy import create_engine, Column, Integer, String, Boolean
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
    
    loggin_key = ''
    logged_on = False
    
    def __init__(self, e='', p='', n='', a=False):
        self.email = e
        self.password = p
        self.nick = n
        self.admin = a
    
    def __repr__(self):
        return "<Ke_user('%s','%s')>" % (self.email, self.nick)
    
    def get_id(self):
        return self.db_id
    
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

class Super_cache:
    users = []
    stats = {
        'uptime': datetime.now(),
        'served_pages': 0,
        'users': 0
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
        users = session.query(Ke_user).all()
        session.close()
        return users
    
    def user2memory(self, user):
        encontrado = False
        for u in self.users:
            if u.get_email() == user.get_email():
                encontrado = True
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
        session = Ke_session()
        if email == '':
            error_msg = 'introduce el email'
        elif passwd == '':
            error_msg = 'introduce la contrasenya'
        else:
            user = self.get_user_by_email(email)
            if not user:
                error_msg = 'usuario no encontrado'
            elif user.get_password() == hashlib.sha1(passwd).hexdigest():
                user.new_loggin_key()
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
        return user
    
    def register(self, email='', nick='', passwd='', passwd2=''):
        user = False
        error_msg = False
        session = Ke_session()
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
                        session.add(user)
                        session.commit()
                        user.new_loggin_key()
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
    
    def get_stats(self):
        self.stats['users'] = len(self.users)
        return self.stats
    
    def sum_served_pages(self):
        self.stats['served_pages'] += 1


class Ke_page:
    sc = Super_cache()
    
    # devuelve un array con toda la información necesaria para las templates
    def get_kedata(self, rpage='', user=False, error_msg=False):
        if not user:
            user = self.sc.fast_loggin()
        ke_data = {
            'appname': APP_NAME,
            'appdomain': APP_DOMAIN,
            'stats': self.sc.get_stats(),
            'user': user,
            'rpage': rpage
        }
        if error_msg:
            ke_data['errormsg'] = error_msg
        return ke_data
