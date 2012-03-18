#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ke_config import *


class Ke_mail:
    def __init__(self):
        if not APP_DEBUG:
            self.server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            self.server.ehlo()
            if SMTP_TTLS:
                self.server.starttls()
            self.server.ehlo()
            self.server.login(SMTP_USER, SMTP_PASS)
    
    def send(self, email='', subject='', msg=''):
        if APP_DEBUG:
            self.test(email, subject, msg)
        elif email != '' and msg != '':
            mmsg = MIMEMultipart("alternative")
            mmsg['Subject'] = subject
            mmsg['From'] = APP_ADMIN_EMAIL
            mmsg['To'] = email
            part1 = MIMEText(msg, "plain", "utf-8")
            mmsg.attach(part1)
            self.server.sendmail(APP_ADMIN_EMAIL, email, mmsg.as_string().encode('ascii'))
    
    def test(self, email='', subject='', msg=''):
        if email != '' and msg != '':
            mmsg = MIMEMultipart("alternative")
            mmsg['Subject'] = subject
            mmsg['From'] = APP_ADMIN_EMAIL
            mmsg['To'] = email
            part1 = MIMEText(msg, "plain", "utf-8")
            mmsg.attach(part1)
            print '------------------------------------------------------------------'
            print email+' - '+subject
            print msg
            print '------------------------------------------------------------------'
    
    def __del__(self):
        if not APP_DEBUG:
            self.server.quit()
