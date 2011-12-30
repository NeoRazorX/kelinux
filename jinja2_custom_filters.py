#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

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

