from flask import url_for

from config import webapp_settings


def url_for_ep(func_name, **values):
    return webapp_settings['protocol'] + webapp_settings['domain'] + url_for(func_name, **values)
