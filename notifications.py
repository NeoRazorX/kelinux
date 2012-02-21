#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ke_config import *
from ke_base import *
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

class notifications:
    engine = create_engine("mysql://%s:%s@%s:%s/%s" % (MYSQL_USER, MYSQL_PASS, MYSQL_HOST, MYSQL_PORT, MYSQL_DBNAME),
                           encoding='utf-8', convert_unicode=True, echo=APP_DEBUG)
    mail = Ke_mail()
    
    def __init__(self):
        # creamos la sesión con la base de datos
        self.session = scoped_session(sessionmaker(bind=self.engine))
        
        # creamos/comprobamos la estructura de tablas
        Base.metadata.create_all(self.engine)
        
        notis = self.session.query(Ke_notification).filter_by(sendmail=True).all()
        if notis:
            for n in notis:
                subject = n.text[:50]+'...'
                body = u"""Notificación de %s.\n\n%s - %s\n\nSi no desea recibir más emails marque la casilla en su perfil.
Atentamente el cron de %s.""" % (APP_DOMAIN, n.text, n.get_link(True), APP_NAME)
                try:
                    if not n.user.no_emails:
                        self.mail.send(n.user.email, subject, body)
                    n.sendmail = False
                    self.session.commit()
                except:
                    self.session.rollback()

if __name__ == "__main__":
    n = notifications()
