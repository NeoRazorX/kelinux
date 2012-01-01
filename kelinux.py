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
env.filters['highlight_page'] = highlight_page
env.filters['linebreaks'] = linebreaks

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

class Main_web(Ke_web):
    @cherrypy.expose
    def index(self):
        self.first_step('index')
        tmpl = env.get_template('main.html')
        return tmpl.render(question_list=self.get_front_questions(),
                           community_list=self.sc.get_all_communities(),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def default(self, attr=''):
        self.first_step('error')
        tmpl = env.get_template('error.html')
        return tmpl.render(ke_data=self.ke_data)
    
    @cherrypy.expose
    def log_in(self, option='', email='', nick='', passwd='', passwd2='', npasswd='', npasswd2=''):
        self.first_step('log_in')
        if cherrypy.request.method == 'POST':
            if option == 'log_in':
                self.do_log_in(email, passwd)
            elif option == 'register':
                self.register(email, nick, passwd, passwd2)
            elif option == 'update':
                self.update_user(email, nick, passwd, npasswd, npasswd2)
            elif option == 'log_out':
                self.do_log_out()
        tmpl = env.get_template('log_in.html')
        return tmpl.render(ke_data=self.ke_data)
    
    @cherrypy.expose
    def create(self, option='', name='', description='', text=''):
        self.first_step('create_msg')
        tmpl = env.get_template('create_msg.html')
        if cherrypy.request.method == 'POST':
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            if option == 'community':
                return tmpl.render(community=self.new_community(name, description),
                                   ke_data=self.ke_data,
                                   option='community')
            elif option == 'question':
                return tmpl.render(question=self.new_question(text),
                                   ke_data=self.ke_data,
                                   option='question')
            else:
                raise cherrypy.HTTPRedirect('/')
        else:
            raise cherrypy.HTTPRedirect('/')
    
    @cherrypy.expose
    def community_list(self, name='', description=''):
        self.first_step('community_list')
        tmpl = env.get_template('community_list.html')
        return tmpl.render(community_list=self.sc.get_all_communities(),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def community(self, name=''):
        self.first_step('community')
        tmpl = env.get_template('community.html')
        return tmpl.render(community=self.sc.get_community_by_name(name),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def question_list(self, text='', email=''):
        self.first_step('question_list')
        tmpl = env.get_template('question_list.html')
        return tmpl.render(question_list=self.sc.get_all_questions(),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def question(self, idq=''):
        self.first_step('question')
        tmpl = env.get_template('question.html')
        return tmpl.render(question=self.sc.get_question_by_id(idq),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def question_reward(self, idq=''):
        self.first_step('question')
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        if self.current_user.logged_on:
            if self.current_user.points > 0:
                question = self.sc.get_question_by_id(idq)
                if question:
                    question.add_reward(1)
                    self.current_user.add_points(-1)
                    try:
                        Ke_session.add(question)
                        Ke_session.add(self.current_user)
                        return 'OK;'+str(question.reward)+';'+str(self.current_user.points)
                    except:
                        return u'Error al procesar la petición'
                else:
                    return 'Pregunta no encontrada'
            else:
                return 'No tienes suficientes puntos'
        else:
            return u'Debes iniciar sesión'
    
    @cherrypy.expose
    def user_list(self):
        self.first_step('user_list')
        tmpl = env.get_template('user_list.html')
        return tmpl.render(user_list=self.sc.get_all_users(),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def user(self, idu=''):
        self.first_step('user')
        tmpl = env.get_template('user.html')
        return tmpl.render(user=self.sc.get_user_by_id(idu),
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
                               chat_users=self.sc.chat_user_alive(self.current_user,
                                                                  cherrypy.request.remote.ip))
        else:
            tmpl = env.get_template('chat_room.html')
            return tmpl.render(ke_data=self.ke_data)

if __name__ == "__main__":
    cherrypy.quickstart(Main_web(), config=cp_config)
    Ke_session.close()
