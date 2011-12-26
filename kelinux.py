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

class Portada(Ke_page):
    @cherrypy.expose
    def index(self):
        self.sc.sum_served_pages()
        tmpl = env.get_template('main.html')
        return tmpl.render( ke_data=self.get_kedata('index') ).encode('utf-8')
    
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
            return tmpl.render( ke_data=self.get_kedata('loggin', user, error_msg) ).encode('utf-8')
        else:
            return tmpl.render( ke_data=self.get_kedata('loggin') ).encode('utf-8')
    
    @cherrypy.expose
    def community_list(self):
        self.sc.sum_served_pages()
        tmpl = env.get_template('community_list.html')
        return tmpl.render(ke_data=self.get_kedata('community_list') ).encode('utf-8')
    
    @cherrypy.expose
    def user_list(self):
        self.sc.sum_served_pages()
        tmpl = env.get_template('user_list.html')
        return tmpl.render(ke_data=self.get_kedata('user_list'), user_list=self.sc.get_all_users() ).encode('utf-8')
    
    @cherrypy.expose
    def stats(self):
        self.sc.sum_served_pages()
        tmpl = env.get_template('stats.html')
        return tmpl.render( ke_data=self.get_kedata('stats') ).encode('utf-8')

if __name__ == "__main__":
    cherrypy.quickstart(Portada(), config=cp_config)

