#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from ke_config import *
from ke_base import *
from sqlalchemy import MetaData
from xml.etree.ElementTree import ElementTree

# comprobamos la estructura de tablas de la base de datos
Ke_user().metadata.create_all(Ke_engine)
Ke_community().metadata.create_all(Ke_engine)
Ke_question().metadata.create_all(Ke_engine)
Ke_answer().metadata.create_all(Ke_engine)

class ubufaq2kelinux:
    sc = Super_cache()
    ubufaq_user = Ke_user()
    
    def __init__(self, filename=''):
        continuar = False
        self.ubufaq_user = self.sc.get_user_by_nick( UBUNTUFAQ_USER_NICK )
        if not self.ubufaq_user.exists():
            if not self.ubufaq_user.set_nick( UBUNTUFAQ_USER_NICK ):
                print u'UBUNTUFAQ_USER_NICK no válido'
            elif not self.ubufaq_user.set_email( UBUNTUFAQ_USER_EMAIL ):
                print u'UBUNTUFAQ_USER_EMAIL no válido'
            else:
                try:
                    Ke_session.add( self.ubufaq_user )
                    Ke_session.commit()
                    continuar = True
                except:
                    Ke_session.rollback()
                    print 'error al guardar el usuario UBUNTUFAQ_USER_NICK en la base de datos'
        else:
            continuar = True
        if continuar:
            self.process_file(filename)
    
    def get_user(self, email=''):
        usuario = self.ubufaq_user
        if email:
            usuario = self.sc.get_user_by_email(email)
            if not usuario.exists():
                if not usuario.set_email(email):
                    usuario = self.ubufaq_user
                elif not usuario.set_nick( email.split('@')[0] ):
                    usuario = self.ubufaq_user
                else:
                    for c in self.ubufaq_user.communities:
                        usuario.communities.append(c)
                    try:
                        Ke_session.add(usuario)
                        Ke_session.commit()
                    except:
                        Ke_session.rollback()
                        print 'error al guardar el usuario '+email+' en la base de datos'
        return usuario
            
    
    def process_file(self, filename=''):
        doc = ElementTree()
        doc.parse(filename)
        for node in doc.getroot():
            question = Ke_question()
            question.user = self.ubufaq_user
            for c in self.ubufaq_user.communities:
                question.communities.append(c)
            Ke_session.add(question)
            for n in node:
                if n.tag == 'email':
                    question.user = self.get_user( n.text )
                elif n.tag == 'title':
                    question.text = n.text
                elif n.tag == 'text':
                    question.text += ' ' + n.text
                elif n.tag == 'answer':
                    answer = Ke_answer()
                    answer.user = self.ubufaq_user
                    answer.question = question
                    Ke_session.add(answer)
                    for a in n:
                        if a.tag == 'email':
                            answer.user = self.get_user( a.text )
                        elif a.tag == 'text':
                            answer.text = a.text
                    question.num_answers = len( question.answers )
                    Ke_session.add(answer)
                    Ke_session.add(question)
            Ke_session.commit()

if __name__ == "__main__":
    if len( sys.argv ) == 2:
        u2k = ubufaq2kelinux( sys.argv[1] )
    else:
        print 'uso: ubufaq2kelinux questions.xml'
    Ke_session.close()
