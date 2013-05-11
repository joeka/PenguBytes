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

