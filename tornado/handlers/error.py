import tornado.web
from handlers.base import BaseHandler

class ErrorHandler(BaseHandler):
    '''Handles requests not served by any handler.'''
    def get(self):
        '''Show error page.'''
        raise tornado.web.HTTPError(404)
