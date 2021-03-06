#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from datetime import datetime, timedelta

def linebreaks(value):
    bbdata = [
        (r'\[b\](.+?)\[/b\]', r'<b>\1</b>'),
        (r'\[i\](.+?)\[/i\]', r'<i>\1</i>'),
        (r'\[u\](.+?)\[/u\]', r'<u>\1</u>'),
        (r'\[code\](.+?)\[/code\]', r'<div class="code">\1</div>'),
        (r'\[big\](.+?)\[/big\]', r'<big>\1</big>'),
        (r'\[small\](.+?)\[/small\]', r'<small>\1</small>')
    ]
    for bbset in bbdata:
        p = re.compile(bbset[0], re.DOTALL)
        value = p.sub(bbset[1], value)
    # mentions
    aux_mentions = re.findall(r'@[0-9]+\b', value)
    for mention in aux_mentions:
        value = value.replace(mention, '<a href="#'+mention[1:]+'">'+mention+'</a>')
    return value.replace('\n', '<br />')

def timesince(t, since=True):
    time_str = 'ahora mismo'
    now = datetime.now()
    diff = now - t
    periods = (
        (diff.days / 365, u"año", u"años"),
        (diff.days / 30, "mes", "meses"),
        (diff.days / 7, "semana", "semanas"),
        (diff.days, u"día", u"días"),
        (diff.seconds / 3600, "hora", "horas"),
        (diff.seconds / 60, "minuto", "minutos"),
        (diff.seconds, "segundo", "segundos")
    )
    for period, singular, plural in periods:
        if period:
            time_str = "%d %s" % (period, singular if period == 1 else plural)
            break
    if since:
        return 'hace ' + time_str
    else:
        return time_str

def highlight_page(name, selection=''):
    if name == selection:
        return "class='selected'"
    else:
        return ''

def highlight_order(name, order=''):
    if name == order:
        return "class='selected'"
    else:
        return ''

def partial_ip(value=''):
    try:
        ip = value.split('.')
        return '%s.%s.X.%s' % (ip[0], ip[1], ip[3])
    except:
        return value

