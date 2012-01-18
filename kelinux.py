#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, cherrypy
from ke_config import *
from ke_base import *
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from jinja2 import Environment, FileSystemLoader
from jinja2_custom_filters import *
from cherrypy.process import wspbus, plugins
from cherrypy.process.plugins import PIDFile, Daemonizer
from datetime import datetime


class SAEnginePlugin(plugins.SimplePlugin):
    def __init__(self, bus):
        plugins.SimplePlugin.__init__(self, bus)
        self.sa_engine = None
        self.bus.subscribe("bind", self.bind)
    
    def start(self):
        # creamos el engine para sqlalchemy
        self.sa_engine = create_engine("mysql://%s:%s@%s:%s/%s" % (MYSQL_USER, MYSQL_PASS, MYSQL_HOST, MYSQL_PORT, MYSQL_DBNAME),
                                       encoding='utf-8', convert_unicode=True, echo=APP_DEBUG)
        # creamos/comprobamos la estructura de tablas
        Base.metadata.create_all(self.sa_engine)
    
    def stop(self):
        if self.sa_engine:
            self.sa_engine.dispose()
            self.sa_engine = None
    
    def bind(self, session):
        session.configure(bind=self.sa_engine)


class SATool(cherrypy.Tool):
    def __init__(self):
        cherrypy.Tool.__init__(self, 'on_start_resource', self.bind_session, priority=20)
        self.session = scoped_session(sessionmaker(autoflush=False, autocommit=False))
    
    def _setup(self):
        cherrypy.Tool._setup(self)
        cherrypy.request.hooks.attach('on_end_resource', self.commit_transaction, priority=80)
    
    def bind_session(self):
        cherrypy.engine.publish('bind', self.session)
        cherrypy.request.db = self.session
    
    def commit_transaction(self):
        cherrypy.request.db = None
        self.session.remove()


# nos guardamos el path
Ke_current_path = os.getcwd()

# cargamos las templates para jinja2
env = Environment(loader=FileSystemLoader(Ke_current_path+'/templates'))

# añadimos los filtros personalizados
env.filters['timesince'] = timesince
env.filters['highlight_page'] = highlight_page
env.filters['linebreaks'] = linebreaks
env.filters['highlight_order'] = highlight_order
env.filters['partial_ip'] = partial_ip

# definimos la configuración de cherrypy
cp_config = {
    'global': {
        'server.socket_host': '0.0.0.0',
        'server.socket_port': APP_PORT,
        'server.thread_pool': APP_THREAD_POOL,
        'server.socket_queue_size': APP_SOCKET_QUEUE_SIZE,
        'log.access_file': Ke_current_path+'/logs/access.'+str(datetime.today().isoformat(' '))+'.log',
        'log.error_file': Ke_current_path+'/logs/error.'+str(datetime.today().isoformat(' '))+'.log',
        'tools.encode.on': True,
        'toots.encode.encoding': 'utf-8',
        'tools.decode.on': True,
        'tools.db.on': True
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
    def index(self, **params):
        self.first_step('index')
        tmpl = env.get_template('main.html')
        return tmpl.render(question_list=self.get_front_questions(),
                           community_list=self.get_all_communities(),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def default(self, attr='', **params):
        self.first_step('error')
        tmpl = env.get_template('error.html')
        return tmpl.render(ke_data=self.ke_data)
    
    @cherrypy.expose
    def log_in(self, option='', email='', nick='', passwd='', passwd2='', npasswd='', npasswd2='', **params):
        self.first_step('log_in')
        if cherrypy.request.method == 'POST':
            if option == 'log_in':
                self.do_log_in(email, passwd)
            elif option == 'register':
                self.register(email, nick, passwd, passwd2)
            elif option == 'update':
                self.update_user(email, passwd, npasswd, npasswd2)
            elif option == 'log_out':
                self.do_log_out()
        tmpl = env.get_template('log_in.html')
        return tmpl.render(ke_data=self.ke_data)
    
    @cherrypy.expose
    def new_password(self, email='', passwd='', **params):
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
    def finder(self, query='', **params):
        self.first_step('finder')
        self.ke_data['query'] = query
        self.run_onload('document.f_finder.query.focus()')
        tmpl = env.get_template('finder.html')
        return tmpl.render(questions=self.new_search(query),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def create(self, option='', name='', description='', text='', **params):
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
    def community_list(self, **params):
        self.first_step('community_list')
        tmpl = env.get_template('community_list.html')
        return tmpl.render(community_list=self.get_all_communities(),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def community(self, name='', order='updated', num=0, **params):
        self.first_step('community')
        community = self.get_community_by_name(name)
        if community.exists():
            self.set_page_description( community.description )
            try:
                num = int(num)
            except:
                num = 0
            if num < 0:
                num = 0
            try:
                query1 = cherrypy.request.db.query(Ke_question).join((Ke_community, Ke_question.communities)).filter(Ke_question.communities.any(Ke_community.id==community.id))
                if order == 'updated':
                    questions = query1.order_by(Ke_question.updated.desc())[num:num+50]
                elif order == 'reward':
                    questions = query1.order_by(Ke_question.reward.desc())[num:num+50]
                elif order == 'status':
                    questions = query1.order_by(Ke_question.status)[num:num+50]
                elif order == 'author':
                    questions = query1.order_by(Ke_question.user_id)[num:num+50]
                else:
                    questions = query1.order_by(Ke_question.id.desc())[num:num+50]
            except:
                questions = []
            tmpl = env.get_template('community.html')
            return tmpl.render(community=community,
                               questions=questions,
                               order=order,
                               prevp=(num-50),
                               nextp=(num+50),
                               ke_data=self.ke_data)
        else:
            raise cherrypy.HTTPRedirect('/error_404')
    
    @cherrypy.expose
    def edit_community(self, idc='', name='', description='', **params):
        self.first_step('edit community')
        community = self.get_community_by_id(idc)
        if community.exists():
            if self.current_user.is_admin():
                if params.get('remove', '') == str(community.id):
                    cherrypy.request.db.delete(community)
                    try:
                        cherrypy.request.db.commit()
                    except:
                        cherrypy.request.db.rollback()
                        self.ke_data['errormsg'] = u'error al borrar la comunidad de la base de datos'
                    if not self.ke_data['errormsg']:
                        raise cherrypy.HTTPRedirect('/community_list')
                elif description != '':
                    if not community.set_description(description):
                        cherrypy.request.db.rollback()
                        self.ke_data['errormsg'] = u'la descripción no es válida'
                    else:
                        try:
                            cherrypy.request.db.commit()
                            self.ke_data['message'] = u'comunidad modificada correctamente'
                        except:
                            cherrypy.request.db.rollback()
                            self.ke_data['errormsg'] = u'error al guardar las modificaciones en la base de datos'
            self.set_page_description( community.description )
            tmpl = env.get_template('edit_community.html')
            return tmpl.render(community=community, ke_data=self.ke_data)
        else:
            raise cherrypy.HTTPRedirect('/error_404')
    
    @cherrypy.expose
    def join_community(self, name='', **params):
        self.first_step('community')
        if self.current_user.logged_on:
            community = self.get_community_by_name(name)
            if community:
                if self.current_user in community.users:
                    community.users.remove(self.current_user)
                else:
                    community.users.append(self.current_user)
                community.num_users = len( community.users )
                try:
                    cherrypy.request.db.commit()
                except:
                    cherrypy.request.db.rollback()
                raise cherrypy.HTTPRedirect('/community/'+name)
            else:
                raise cherrypy.HTTPRedirect('/community_list')
        else:
            raise cherrypy.HTTPRedirect('/log_in')
    
    @cherrypy.expose
    def question_list(self, order='created', num=0, **params):
        self.first_step('question_list')
        try:
            num = int(num)
        except:
            num = 0
        if num < 0:
            num = 0
        tmpl = env.get_template('question_list.html')
        return tmpl.render(question_list=self.get_all_questions(order, num),
                           order=order,
                           prevp=(num-50),
                           nextp=(num+50),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def question(self, idq='', **params):
        self.first_step('question')
        self.run_onload('load_answers()')
        question = self.get_question_by_id(idq)
        if question.exists():
            self.set_page_description( question.get_resume() )
            tmpl = env.get_template('question.html')
            return tmpl.render(question=question, ke_data=self.ke_data)
        else:
            raise cherrypy.HTTPRedirect('/error_404')
    
    @cherrypy.expose
    def edit_question(self, idq='', **params):
        self.first_step('edit question')
        question = self.get_question_by_id(idq)
        if question.exists():
            communities = []
            if self.current_user.is_admin():
                for c in self.get_all_communities():
                    communities.append(c)
            else:
                for c in question.communities:
                    communities.append(c)
                for c in self.current_user.communities:
                    if c not in communities:
                        communities.append(c)
            if self.current_user.id == question.user.id or self.current_user.is_admin():
                if params.get('remove', '') == str(question.id): # ¿Borramos la pregunta?
                    cherrypy.request.db.delete(question)
                    try:
                        cherrypy.request.db.commit()
                    except:
                        cherrypy.request.db.rollback()
                        self.ke_data['errormsg'] = u'error al borrar la pregunta de la base de datos'
                    if not self.ke_data['errormsg']:
                        raise cherrypy.HTTPRedirect('/question_list')
                elif params.get('text', '') != '': # ¿Modificamos la pregunta?
                    if not question.set_text( params.get('text', '') ):
                        cherrypy.request.db.rollback()
                        self.ke_data['errormsg'] = u'El texto no es válido'
                    elif not question.set_status( params.get('status', 0) ):
                        cherrypy.request.db.rollback()
                        self.ke_data['errormsg'] = u'Estado no válido'
                    else:
                        del question.communities[:]
                        s_comm = params.get('communities', [])
                        for c in communities:
                            if isinstance(s_comm, unicode):
                                if str(c.id) == s_comm:
                                    question.communities.append(c)
                                    break
                            else:
                                if str(c.id) in s_comm:
                                    question.communities.append(c)
                        try:
                            cherrypy.request.db.commit()
                            self.ke_data['message'] = u'pregunta modificada correctamente'
                        except:
                            cherrypy.request.db.rollback()
                            self.ke_data['errormsg'] = u'error al guardar las modificaciones en la base de datos'
            self.set_page_description( question.get_resume() )
            tmpl = env.get_template('edit_question.html')
            return tmpl.render(question=question,
                               communities=communities,
                               ke_data=self.ke_data)
        else:
            raise cherrypy.HTTPRedirect('/error_404')
    
    @cherrypy.expose
    def question_reward(self, idq='', **params):
        self.first_step('question')
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return self.add_reward2question(idq)
    
    @cherrypy.expose
    def answers(self, idq='', order='grade', text='', **params):
        self.first_step('question')
        question,answer = self.new_answer(idq, text)
        answers = self.get_answers(idq, order)
        tmpl = env.get_template('answers.html')
        return tmpl.render(question=question, answer=answer, answers=answers, ke_data=self.ke_data)
    
    @cherrypy.expose
    def vote_answers(self, option='', ida='', **params):
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
    def user_list(self, **params):
        self.first_step('user_list')
        tmpl = env.get_template('user_list.html')
        return tmpl.render(user_list=self.get_all_users(),
                           ke_data=self.ke_data)
    
    @cherrypy.expose
    def user(self, nick='', order='updated', num=0, **params):
        self.first_step('user')
        user = self.get_user_by_nick(nick)
        if user.exists():
            try:
                num = int(num)
            except:
                num = 0
            if num < 0:
                num = 0
            try:
                query1 = cherrypy.request.db.query(Ke_question).filter_by(user_id=user.id)
                query2 = cherrypy.request.db.query(Ke_question).join((Ke_answer, Ke_question.answers)).filter(Ke_question.answers.any(Ke_answer.user==user))
                if order == 'updated':
                    questions = query1.union(query2).order_by(Ke_question.updated.desc())[num:num+50]
                elif order == 'reward':
                    questions = query1.union(query2).order_by(Ke_question.reward.desc())[num:num+50]
                elif order == 'status':
                    questions = query1.union(query2).order_by(Ke_question.status)[num:num+50]
                elif order == 'author':
                    questions = query1.union(query2).order_by(Ke_question.user_id)[num:num+50]
                else:
                    questions = query1.union(query2).order_by(Ke_question.id.desc())[num:num+50]
            except:
                questions = []
            tmpl = env.get_template('user.html')
            return tmpl.render(user=user,
                               questions=questions,
                               order=order,
                               prevp=(num-50),
                               nextp=(num+50),
                               ke_data=self.ke_data)
        else:
            raise cherrypy.HTTPRedirect('/error_404')
    
    @cherrypy.expose
    def stats(self, **params):
        self.first_step('stats')
        tmpl = env.get_template('stats.html')
        return tmpl.render(searches=self.get_searches(), ke_data=self.ke_data)
    
    @cherrypy.expose
    def chat_room(self, text='', **params):
        self.first_step('chat_room')
        self.run_onload('load_chat_log()')
        if cherrypy.request.method == 'POST':
            self.new_chat_msg(text)
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            tmpl = env.get_template('chat_log.html')
            return tmpl.render(chat_log=self.chat_log, chat_users=self.chat_user_alive())
        else:
            tmpl = env.get_template('chat_room.html')
            return tmpl.render(ke_data=self.ke_data)
    
    @cherrypy.expose
    def sitemap(self, **params):
        self.first_step('sitemap')
        communities = self.get_all_communities()
        questions = self.get_front_questions()
        users = self.get_all_users()
        document = "<?xml version='1.0' encoding='UTF-8'?>\n"
        document += "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"
        for c in communities:
            document += "<url><loc>" + c.get_link() + "</loc><lastmod>" + str(c.created).split(' ')[0] + "</lastmod><changefreq>always</changefreq><priority>0.8</priority></url>\n"
        for q in questions:
            document += "<url><loc>" + q.get_link() + "</loc><lastmod>" + str(q.created).split(' ')[0] + "</lastmod><changefreq>always</changefreq><priority>0.8</priority></url>\n"
        for u in users:
            document += "<url><loc>" + u.get_link() + "</loc><lastmod>" + str(u.created).split(' ')[0] + "</lastmod><changefreq>always</changefreq><priority>0.8</priority></url>\n"
        document += "</urlset>\n"
        cherrypy.response.headers['Content-Type']='text/xml; charset=utf-8'
        return document

if __name__ == "__main__":
    SAEnginePlugin(cherrypy.engine).subscribe()
    cherrypy.tools.db = SATool()
    if APP_RUN_AS_DAEMON:
        d = Daemonizer(cherrypy.engine)
        d.subscribe()
        p = PIDFile(cherrypy.engine, Ke_current_path+"/kelinux.pid")
        p.subscribe()
        cp_config['global']['log.screen'] = False
    cherrypy.quickstart(Main_web(), config=cp_config)
