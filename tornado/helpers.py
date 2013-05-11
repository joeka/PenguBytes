import unicodedata
import re
import functools
import tornado.web

def stripHtml( text ):
    '''Strips everything that begins with "<" and end with ">"
        Don't use this for complicated stuff, something will probably go wrong.
    '''
    return re.sub('<[^<]+?>', '', text)

def excerpt( text, length=300 ):
    '''Returns an excerpt from a text
        Uses very simple method to strip html tags -> maybe not reliable
    '''
    text = stripHtml( text )
    if len( text ) > length:
        text = text[:length] + " [...]"
    
    return text

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
		if self.current_user != self.settings["admin"]: # put your way of checking for an admin here
			self.redirect("/")
		else:
			return method(self, *args, **kwargs)
	return wrapper
