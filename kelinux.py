#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, cherrypy
from ke_config import *
from ke_base import *
from sqlalchemy import MetaData
from jinja2 import Environment, FileSystemLoader
from jinja2_custom_filters import *
from cherrypy.process.plugins import PIDFile, Daemonizer
from datetime import datetime

# nos guardamos el path
Ke_current_path = os.getcwd()

# comprobamos la estructura de tablas de la base de datos
Ke_user().metadata.create_all(Ke_engine)
Ke_community().metadata.create_all(Ke_engine)
Ke_question().metadata.create_all(Ke_engine)
Ke_answer().metadata.create_all(Ke_engine)

# cargamos las templates para jinja2
env = Environment(loader=FileSystemLoader(Ke_current_path+'/templates'))

# añadimos los filtros personalizados
env.filters['timesince'] = timesince
env.filters['highlight_page'] = highlight_page
env.filters['linebreaks'] = linebreaks

# definimos la configuración de cherrypy
cp_config = {
    'global': {
        'server.socket_host': '0.0.0.0',
        'server.socket_port': APP_PORT,
        'log.access_file': Ke_current_path+'/logs/kelinux_access.'+str(datetime.today().isoformat(' '))+'.log',
        'log.error_file': Ke_current_path+'/logs/kelinux_error.'+str(datetime.today().isoformat(' '))+'.log',
        'tools.encode.on': True,
        'toots.encode.encoding': 'utf-8',
        'tools.decode.on': True
    },
    '/favicon.ico': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': Ke_current_path+'/img/favicon.ico',
    },
    '/robots.txt': {
        'tools.staticfile.on': True,
        'tools.staticfile.filename': Ke_current_path+'/robots.txt',
    },
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(Ke_current_path, 'static')
    },
    '/img': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(Ke_current_path, 'img')
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
        errormsg = ''
        if cherrypy.request.method == 'POST':
            errormsg = self.send_mail_new_user_password(email)
        else:
            errormsg = self.new_user_password(email, passwd)
        if errormsg == '':
            raise cherrypy.HTTPRedirect('/')
        else:
            return errormsg
    
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
    def community(self, name='', order='updated', num=0):
        self.first_step('community')
        community = self.sc.get_community_by_name(name)
        if community.exists():
            self.set_page_description( community.description )
            try:
                num = int(num)
            except:
                num = 0
            if num < 0:
                num = 0
            if order == 'updated':
                questions = Ke_session.query(Ke_question).join((Ke_community, Ke_question.communities)).filter(Ke_question.communities.any(Ke_community.id==community.id)).order_by(Ke_question.updated.desc())[num:num+50]
            elif order == 'reward':
                questions = Ke_session.query(Ke_question).join((Ke_community, Ke_question.communities)).filter(Ke_question.communities.any(Ke_community.id==community.id)).order_by(Ke_question.reward.desc())[num:num+50]
            elif order == 'status':
                questions = Ke_session.query(Ke_question).join((Ke_community, Ke_question.communities)).filter(Ke_question.communities.any(Ke_community.id==community.id)).order_by(Ke_question.status)[num:num+50]
            else:
                questions = Ke_session.query(Ke_question).join((Ke_community, Ke_question.communities)).filter(Ke_question.communities.any(Ke_community.id==community.id)).order_by(Ke_question.id.desc())[num:num+50]
            tmpl = env.get_template('community.html')
            return tmpl.render(community=community,
                               questions=questions,
                               order=order,
                               prevp=(num-50),
                               nextp=(num+50),
                               ke_data=self.ke_data)
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
    def question_list(self, order='created', num=0):
        self.first_step('question_list')
        try:
            num = int(num)
        except:
            num = 0
        if num < 0:
            num = 0
        tmpl = env.get_template('question_list.html')
        return tmpl.render(question_list=self.sc.get_all_questions(order, num),
                           order=order,
                           prevp=(num-50),
                           nextp=(num+50),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def question(self, idq=''):
        self.first_step('question')
        self.run_onload('load_answers()')
        question = self.sc.get_question_by_id(idq)
        if question.exists():
            self.set_page_description( question.get_resume() )
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
    def answers(self, idq='', order='grade', text=''):
        self.first_step('question')
        question,answer = self.new_answer(idq, text)
        answers = self.get_answers(idq, order)
        tmpl = env.get_template('answers.html')
        return tmpl.render(question=question, answer=answer, answers=answers, ke_data=self.ke_data)
    
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
    def user(self, idu='', order='updated', num=0):
        self.first_step('user')
        user = self.sc.get_user_by_id(idu)
        if user.exists():
            try:
                num = int(num)
            except:
                num = 0
            if num < 0:
                num = 0
            if order == 'updated':
                questions = Ke_session.query(Ke_question).filter_by(user_id=user.id).order_by(Ke_question.updated.desc())[num:num+50]
            elif order == 'reward':
                questions = Ke_session.query(Ke_question).filter_by(user_id=user.id).order_by(Ke_question.reward.desc())[num:num+50]
            elif order == 'status':
                questions = Ke_session.query(Ke_question).filter_by(user_id=user.id).order_by(Ke_question.status)[num:num+50]
            else:
                questions = Ke_session.query(Ke_question).filter_by(user_id=user.id).order_by(Ke_question.id.desc())[num:num+50]
            tmpl = env.get_template('user.html')
            return tmpl.render(user=user,
                               questions=questions,
                               order=order,
                               prevp=(num-50),
                               nextp=(num+50),
                               ke_data=self.ke_data)
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
        self.run_onload('load_chat_log()')
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
    
    @cherrypy.expose
    def sitemap(self):
        self.first_step('sitemap')
        questions = self.get_front_questions()
        document = "Content-Type: text/xml\n\n"
        document += "<?xml version='1.0' encoding='UTF-8'?>\n"
        document += "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"
        for q in questions:
            document += "<url><loc>" + q.get_link() + "</loc><lastmod>" + str(q.created).split(' ')[0] + "</lastmod><changefreq>always</changefreq><priority>0.8</priority></url>\n"
        document += "</urlset>\n"
        return document

if __name__ == "__main__":
    if APP_RUN_AS_DAEMON:
        d = Daemonizer(cherrypy.engine)
        d.subscribe()
        p = PIDFile(cherrypy.engine, Ke_current_path+"/kelinux.pid")
        p.subscribe()
        cp_config['global']['log.screen'] = False
    cherrypy.quickstart(Main_web(), config=cp_config)
    Ke_session.close()
