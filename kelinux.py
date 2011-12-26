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
        self.sc.sum_served_pages()
        tmpl = env.get_template('main.html')
        return tmpl.render(ke_data=self.get_kedata('index'),
                           front_list=self.sc.get_front()).encode('utf-8')
    
    @cherrypy.expose
    def loggin(self, option='', email='', nick='', passwd='', passwd2=''):
        self.sc.sum_served_pages()
        tmpl = env.get_template('loggin.html')
        if cherrypy.request.method == 'POST':
            if option == 'loggin':
                user,error_msg = self.sc.loggin(email, passwd)
            elif option == 'register':
                user,error_msg = self.sc.register(email, nick, passwd, passwd2)
            elif option == 'loggout':
                error_msg = self.sc.loggout()
                user = Ke_user()
            else:
                error_msg = False
                user = self.sc.fast_loggin()
            return tmpl.render(ke_data=self.get_kedata('loggin', user),
                               error_msg=error_msg).encode('utf-8')
        else:
            return tmpl.render( ke_data=self.get_kedata('loggin') ).encode('utf-8')
    
    @cherrypy.expose
    def community_list(self, name=''):
        self.sc.sum_served_pages()
        tmpl = env.get_template('community_list.html')
        if cherrypy.request.method == 'POST':
            community,error_msg = self.sc.new_community(name)
            return tmpl.render(ke_data=self.get_kedata('community_list'),
                               error_msg=error_msg,
                               community_list=self.sc.get_all_communities()).encode('utf-8')
        else:
            return tmpl.render(ke_data=self.get_kedata('community_list'),
                               community_list=self.sc.get_all_communities()).encode('utf-8')
    
    @cherrypy.expose
    def question_list(self, text='', email=''):
        self.sc.sum_served_pages()
        tmpl = env.get_template('question_list.html')
        if cherrypy.request.method == 'POST':
            question,error_msg = self.sc.new_question(text, email)
            return tmpl.render(ke_data=self.get_kedata('question_list'),
                               error_msg=error_msg,
                               question_list=self.sc.get_all_questions()).encode('utf-8')
        else:
            return tmpl.render(ke_data=self.get_kedata('question_list'),
                               question_list=self.sc.get_all_questions()).encode('utf-8')
    
    @cherrypy.expose
    def user_list(self):
        self.sc.sum_served_pages()
        tmpl = env.get_template('user_list.html')
        return tmpl.render(ke_data=self.get_kedata('user_list'),
                           user_list=self.sc.get_all_users() ).encode('utf-8')
    
    @cherrypy.expose
    def stats(self):
        self.sc.sum_served_pages()
        tmpl = env.get_template('stats.html')
        return tmpl.render( ke_data=self.get_kedata('stats') ).encode('utf-8')
    
    @cherrypy.expose
    def chat_room(self, text=''):
        self.sc.sum_served_pages()
        ke_data = self.get_kedata('chat_room')
        if cherrypy.request.method == 'POST':
            if text != '':
                self.sc.new_chat_msg(text, self.get_current_user().get_nick())
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            return self.sc.get_chat_log()
        else:
            tmpl = env.get_template('chat_room.html')
            return tmpl.render(ke_data=ke_data).encode('utf-8')

if __name__ == "__main__":
    cherrypy.quickstart(Portada(), config=cp_config)

