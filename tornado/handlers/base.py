import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    '''Base handler to define useful functions for all handlers'''
    
    def get_current_user(self):
        '''Returns email address of current user.'''
        return self.get_secure_cookie("email")
    def get_current_name(self):
        '''Returns name of current user.'''
        return self.get_secure_cookie("name")

    def is_admin(self):
        '''Check if the current user is the admin.'''
        return self.current_user and self.current_user == self.settings["admin"]


    def write_error(self, status_code, **kwargs):
        """Override to implement custom error pages.

        ``write_error`` may call `write`, `render`, `set_header`, etc
        to produce output as usual.

        If this error was caused by an uncaught exception (including
        HTTPError), an ``exc_info`` triple will be available as
        ``kwargs["exc_info"]``.  Note that this exception may not be
        the "current" exception for purposes of methods like
        ``sys.exc_info()`` or ``traceback.format_exc``.
        """
        if self.settings.get("debug") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            traceback = ""
            for line in traceback.format_exception(*kwargs["exc_info"]):
                traceback += line
            self.render("error.html", status_code=status_code, reason=self._reason,
                traceback = traceback)
        else:
            self.render("error.html", status_code=status_code, reason=self._reason,
                traceback = None)
