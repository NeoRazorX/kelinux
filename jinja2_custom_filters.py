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
    return value.replace('\n', '<br />')

def timesince(t):
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
    return time_str

def highlight_page(name, selection=''):
    if name == selection:
        return "class='selected'"
    else:
        return ''

