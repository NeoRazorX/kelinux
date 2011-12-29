#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, cherrypy, simplejson
from ke_config import *
from ke_base import *
from sqlalchemy import MetaData
from jinja2 import Environment, FileSystemLoader
from jinja2_custom_filters import *

# comprobamos la estructura de tablas de la base de datos
Ke_user().metadata.create_all(Ke_engine)
Ke_community().metadata.create_all(Ke_engine)
Ke_question().metadata.create_all(Ke_engine)

# cargamos las templates para jinja2
env = Environment(loader=FileSystemLoader('templates'))

# añadimos los filtros personalizados
env.filters['timesince'] = timesince
env.filters['resaltar_pagina'] = resaltar_pagina

# definimos la configuración de cherrypy
cp_config = {
    'global': {
        'tools.encode.on': True,
        'toots.encode.encoding': 'utf-8',
        'tools.decode.on': True
    },
    '/favicon.ico': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': os.getcwd()+'/img/favicon.ico',
    },
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(os.getcwd(), 'static')
    },
    '/img': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(os.getcwd(), 'img')
    }
}

class Portada(Ke_web):
    @cherrypy.expose
    def index(self):
        self.first_step('index')
        tmpl = env.get_template('main.html')
        return tmpl.render(question_list=self.sc.get_front(),
                           community_list=self.sc.get_all_communities(),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def log_in(self, option='', email='', nick='', passwd='', passwd2=''):
        self.first_step('log_in')
        if cherrypy.request.method == 'POST':
            if option == 'log_in':
                self.do_log_in(email, passwd)
            elif option == 'register':
                self.register(email, nick, passwd, passwd2)
            elif option == 'log_out':
                self.do_log_out()
        tmpl = env.get_template('log_in.html')
        return tmpl.render(ke_data=self.ke_data)
    
    @cherrypy.expose
    def community_list(self, name='', description=''):
        self.first_step('community_list')
        tmpl = env.get_template('community_list.html')
        if cherrypy.request.method == 'POST':
            return tmpl.render(community=self.new_community(name, description),
                               community_list=self.sc.get_all_communities(),
                               ke_data=self.ke_data)
        else:
            return tmpl.render(community_list=self.sc.get_all_communities(),
                               ke_data=self.ke_data)
    
    @cherrypy.expose
    def question_list(self, text='', email=''):
        self.first_step('question_list')
        tmpl = env.get_template('question_list.html')
        if cherrypy.request.method == 'POST':
            return tmpl.render(question=self.new_question(text),
                               question_list=self.sc.get_all_questions(),
                               ke_data=self.ke_data)
        else:
            return tmpl.render(question_list=self.sc.get_all_questions(),
                               ke_data=self.ke_data)
    
    @cherrypy.expose
    def user_list(self):
        self.first_step('user_list')
        tmpl = env.get_template('user_list.html')
        return tmpl.render(user_list=self.sc.get_all_users(),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def stats(self):
        self.first_step('stats')
        tmpl = env.get_template('stats.html')
        return tmpl.render(ke_data=self.ke_data)
    
    @cherrypy.expose
    def chat_room(self, text=''):
        self.first_step('chat_room')
        if cherrypy.request.method == 'POST':
            if text != '':
                self.sc.new_chat_msg(text, self.current_user.nick)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            tmpl = env.get_template('chat_log.html')
            return tmpl.render(chat_log=self.sc.get_chat_log(),
                               chat_users=self.sc.chat_user_alive(self.current_user.nick,
                                                                  cherrypy.request.remote.ip))
        else:
            tmpl = env.get_template('chat_room.html')
            return tmpl.render(ke_data=self.ke_data)

if __name__ == "__main__":
    cherrypy.quickstart(Portada(), config=cp_config)
