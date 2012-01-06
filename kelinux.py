#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, cherrypy
from ke_config import *
from ke_base import *
from sqlalchemy import MetaData
from jinja2 import Environment, FileSystemLoader
from jinja2_custom_filters import *

# comprobamos la estructura de tablas de la base de datos
Ke_user().metadata.create_all(Ke_engine)
Ke_community().metadata.create_all(Ke_engine)
Ke_question().metadata.create_all(Ke_engine)
Ke_answer().metadata.create_all(Ke_engine)

# cargamos las templates para jinja2
env = Environment(loader=FileSystemLoader('templates'))

# añadimos los filtros personalizados
env.filters['timesince'] = timesince
env.filters['highlight_page'] = highlight_page
env.filters['linebreaks'] = linebreaks

# definimos la configuración de cherrypy
cp_config = {
    'global': {
        'server.socket_host': '0.0.0.0',
        'server.socket_port': APP_PORT,
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
    def new_password(self, email='', passwd=''):
        self.first_step('new_password')
        if cherrypy.request.method == 'POST':
            return self.send_mail_new_user_password(email)
        else:
            return self.new_user_password(email, passwd)
    
    @cherrypy.expose
    def finder(self, query=''):
        self.first_step('create_msg')
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        tmpl = env.get_template('finder_log.html')
        return tmpl.render(questions=self.sc.new_search(query),
                           query=query)
    
    @cherrypy.expose
    def create(self, option='', name='', description='', text=''):
        self.first_step('create_msg')
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        tmpl = env.get_template('create_msg.html')
        if option == 'community':
            return tmpl.render(community=self.new_community(name, description),
                               ke_data=self.ke_data,
                               option='community')
        elif option == 'question':
            return tmpl.render(question=self.new_question(text),
                               ke_data=self.ke_data,
                               option='question')
        else:
            raise cherrypy.HTTPRedirect('/log_in')
    
    @cherrypy.expose
    def community_list(self):
        self.first_step('community_list')
        tmpl = env.get_template('community_list.html')
        return tmpl.render(community_list=self.sc.get_all_communities(),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def community(self, name=''):
        self.first_step('community')
        community = self.sc.get_community_by_name(name)
        if community.exists():
            tmpl = env.get_template('community.html')
            return tmpl.render(community=community, ke_data=self.ke_data)
        else:
            raise cherrypy.HTTPRedirect('/community_list')
    
    @cherrypy.expose
    def join_community(self, name=''):
        self.first_step('community')
        if self.current_user.logged_on:
            community = self.sc.get_community_by_name(name)
            if community:
                if self.current_user in community.users:
                    community.users.remove(self.current_user)
                else:
                    community.users.append(self.current_user)
                community.num_users = len( community.users )
                try:
                    Ke_session.add(community)
                    Ke_session.commit()
                except:
                    Ke_session.rollback()
                raise cherrypy.HTTPRedirect('/community/'+name)
            else:
                raise cherrypy.HTTPRedirect('/community_list')
        else:
            raise cherrypy.HTTPRedirect('/log_in')
    
    @cherrypy.expose
    def question_list(self):
        self.first_step('question_list')
        tmpl = env.get_template('question_list.html')
        return tmpl.render(question_list=self.sc.get_all_questions(),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def question(self, idq=''):
        self.first_step('question')
        question = self.sc.get_question_by_id(idq)
        if question.exists():
            tmpl = env.get_template('question.html')
            return tmpl.render(question=question, ke_data=self.ke_data)
        else:
            raise cherrypy.HTTPRedirect('/question_list')
    
    @cherrypy.expose
    def question_reward(self, idq=''):
        self.first_step('question')
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return self.add_reward2question(idq)
    
    @cherrypy.expose
    def answers(self, idq='', text=''):
        self.first_step('question')
        tmpl = env.get_template('answers.html')
        return tmpl.render(question=self.new_answer(idq, text),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def vote_answers(self, option='', ida=''):
        self.first_step('question')
        if option == 'positive':
            return self.new_vote2answer(ida, 1)
        elif option == 'negative':
            return self.new_vote2answer(ida, -1)
        elif option == 'solution':
            return self.mark_answer_as_solution(ida)
        else:
            return u'opción desconocida'
    
    @cherrypy.expose
    def user_list(self):
        self.first_step('user_list')
        tmpl = env.get_template('user_list.html')
        return tmpl.render(user_list=self.sc.get_all_users(),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def user(self, idu=''):
        self.first_step('user')
        user = self.sc.get_user_by_id(idu)
        if user.exists():
            tmpl = env.get_template('user.html')
            return tmpl.render(user=user, ke_data=self.ke_data)
        else:
            raise cherrypy.HTTPRedirect('/user_list')
    
    @cherrypy.expose
    def stats(self):
        self.first_step('stats')
        tmpl = env.get_template('stats.html')
        return tmpl.render(searches=self.sc.get_searches(),
                           ke_data=self.ke_data)
    
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
