#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, ke_base, random
from ke_config import *
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from xml.etree.ElementTree import ElementTree
from datetime import datetime, timedelta


class ubufaq2kelinux:
    engine = create_engine("mysql://%s:%s@%s:%s/%s" % (MYSQL_USER, MYSQL_PASS, MYSQL_HOST, MYSQL_PORT, MYSQL_DBNAME),
                           encoding='utf-8', convert_unicode=True, echo=APP_DEBUG)
    ubufaq_user = ke_base.Ke_user()
    mail = ke_base.Ke_mail()
    
    def __init__(self, filename=''):
        # creamos la sesión con la base de datos
        self.session = scoped_session(sessionmaker(bind=self.engine))
        
        # creamos/comprobamos la estructura de tablas
        ke_base.Base.metadata.create_all(self.engine)
        
        continuar = False
        self.ubufaq_user = self.get_user_by_email( UBUNTUFAQ_USER_EMAIL )
        if not self.ubufaq_user.exists():
            if not self.ubufaq_user.set_nick( UBUNTUFAQ_USER_NICK ):
                print u'UBUNTUFAQ_USER_NICK no válido'
            elif not self.ubufaq_user.set_email( UBUNTUFAQ_USER_EMAIL ):
                print u'UBUNTUFAQ_USER_EMAIL no válido'
            else:
                try:
                    self.session.add( self.ubufaq_user )
                    self.session.commit()
                    continuar = True
                except:
                    self.session.rollback()
                    print 'error al guardar el usuario UBUNTUFAQ_USER_NICK en la base de datos'
        else:
            continuar = True
        if continuar:
            self.process_file(filename)
    
    def get_user_by_email(self, email):
        try:
            user = self.session.query(ke_base.Ke_user).filter_by(email=email).first()
            if user.exists():
                return user
        except:
            return ke_base.Ke_user()
    
    def get_user(self, email=''):
        usuario = self.ubufaq_user
        if email:
            usuario = self.get_user_by_email(email)
            if not usuario.exists():
                new_pass = str(random.randint(0, 999999))
                if not usuario.set_email(email):
                    usuario = self.ubufaq_user
                elif not usuario.set_nick( email.split('@')[0] ):
                    usuario = self.ubufaq_user
                elif not usuario.set_password( new_pass ):
                    usuario = self.ubufaq_user
                else:
                    for c in self.ubufaq_user.communities:
                        usuario.communities.append(c)
                    try:
                        self.session.add(usuario)
                        self.session.commit()
                    except:
                        self.session.rollback()
                        print 'error al guardar el usuario '+email+' en la base de datos'
                    finally:
                        self.mail.send(usuario.email, u"Migración de Ubuntu FAQ a kelinux.net", u"Hola %s, te enviamos este email para informarte de que Ubuntu FAQ es ahora %s. Hemos migrado todos los datos al nuevo servidor y hemos generado nuevas contraseñas, la tuya es '%s'. Haz clic en este enlace %s para iniciar sesión, y posteriormente cambiar la contraseña. Bye!" % (usuario.nick, APP_DOMAIN, new_pass, 'http://'+APP_DOMAIN+'/log_in'))
        return usuario
            
    
    def process_file(self, filename=''):
        doc = ElementTree()
        doc.parse(filename)
        for node in doc.getroot():
            question = ke_base.Ke_question()
            question.user = self.ubufaq_user
            for c in self.ubufaq_user.communities:
                question.communities.append(c)
            for n in node:
                if n.tag == 'email':
                    question.user = self.get_user( n.text )
                elif n.tag == 'date':
                    question.created = datetime.strptime(n.text, '%Y-%m-%d %H:%M')
                    question.updated = datetime.strptime(n.text, '%Y-%m-%d %H:%M')
                elif n.tag == 'title':
                    question.text = n.text
                elif n.tag == 'text':
                    question.text += ' ' + n.text
                elif n.tag == 'answer':
                    answer = ke_base.Ke_answer()
                    answer.user = self.ubufaq_user
                    answer.question = question
                    for a in n:
                        if a.tag == 'email':
                            answer.user = self.get_user( a.text )
                        elif a.tag == 'date':
                            answer.created = datetime.strptime(a.text, '%Y-%m-%d %H:%M')
                        elif a.tag == 'text':
                            answer.text = a.text
                    question.num_answers = len( question.answers )
                    self.session.add(answer)
            self.session.add(question)
            try:
                self.session.commit()
            except:
                self.session.rollback()

if __name__ == "__main__":
    if len( sys.argv ) == 2:
        u2k = ubufaq2kelinux( sys.argv[1] )
    else:
        print 'uso: ubufaq2kelinux questions.xml'
