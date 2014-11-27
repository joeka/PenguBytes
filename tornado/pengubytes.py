import daemon
import sys
import os
import argparse

import locale

import tornado.ioloop
import tornado.web
import tornado.httpserver

import motor

from settings import settings

from handlers.base import BaseHandler
from handlers.auth import *
from handlers.pages import PagesHandler
from handlers.blog import BlogHandler
from handlers.error import ErrorHandler
from handlers.xmppregister import XmppRegisterHandler
from handlers.directxmpp import DirectXmppHandler

application = tornado.web.Application([
    (r"/", BlogHandler),
    (r"/auth", LoginHandler),
    (r"/auth_google", GoogleLoginHandler),
    (r"/auth_facebook", FacebookLoginHandler),
    (r"/logout", LogoutHandler),
    (r"/xmpp_register", XmppRegisterHandler),
    (r"/blog", BlogHandler),
    (r"/blog/([a-zA-Z0-9_-]+)", BlogHandler),           # Single posts
    (r"/blog/([a-zA-Z0-9_-]+)/([a-zA-Z0-9\\.\\+]+)", BlogHandler),  # used for tags
    (r"/contact/xmpp", DirectXmppHandler),
    (r"/([a-zA-Z0-9_-]+)", PagesHandler),
    (r"/.*", ErrorHandler)
], **settings)

    
#if __name__ == "__main__":  # for testing
with daemon.DaemonContext( ):  # to use with an init script
    parser = argparse.ArgumentParser(description='pengubytes.de tornado server')
    parser.add_argument('--port', default=8888, type=int)
    
    args = parser.parse_args()

    locale.setlocale(locale.LC_TIME, "en_GB.UTF8")  # didn't like the us format

    application.listen(args.port)
    application.settings["db"] = motor.MotorClient()[
        application.settings["db_name"]]
    

    tornado.ioloop.IOLoop.instance().start()

