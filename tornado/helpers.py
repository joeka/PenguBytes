import unicodedata
import re
import functools
import tornado.web

def slugify( title ):
	'''Create a slug from a title.
		
		Argument: string title
		Returns: string slug
	'''
	slug = unicodedata.normalize("NFKD", unicode(title)).encode(
		"ascii", "ignore")
	slug = re.sub(r"[^\w]+", " ", slug)
	slug = "-".join(slug.lower().strip().split())
	return slug

def admin(method):
	'''Decorator to check if the current user is an admin.
		Redirects to login_url if not logged in (using @tornado.web.authenticated ).
		Redirects to "/" if logged in but not admin.
	'''
	@functools.wraps(method)
	@tornado.web.authenticated
	def wrapper(self, *args, **kwargs):
		if self.current_user != self.settings["author"]: # put your way of checking for an admin here
			self.redirect("/")
		else:
			return method(self, *args, **kwargs)
	return wrapper
