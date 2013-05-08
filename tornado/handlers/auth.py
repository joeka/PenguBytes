import tornado.gen
import tornado.web
import tornado.auth

from handlers.base import BaseHandler

'''Handle logins.
	class GoogleLoginHandler: Login using Google.
	class FacebookLoginHandler: Login using Facebook.
'''
 

class GoogleLoginHandler(	BaseHandler,
				tornado.auth.GoogleMixin):
	'''Handle Google logins.
		Redirects user to a google login page.
		Later saves his name and email address in a secure cookie.
	'''

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def get(self):
		if self.get_argument("openid.mode", None):
			user = yield self.get_authenticated_user()	# get user data
			self.set_secure_cookie("email", user["email"])
			self.set_secure_cookie("name", user["name"])
			
			next = self.get_argument("next", None)
			if next:
				self.redirect(next)	# back to the page that redirected the user to the login_url
			else:
				self.redirect("/")
		else:
			if self.get_current_user():	# already logged in -> back to "/"
				self.redirect("/")	
			else:
				self.authenticate_redirect(callback_uri=	# to google openid login
					self.request.full_url().replace(	
						'http://', 'https://' ))	# I use nginx for ssl so to be sure always convert to https

class FacebookLoginHandler(	BaseHandler,
				tornado.auth.FacebookGraphMixin):
	'''Handle Google logins.
		Redirects user to a facebook login page.
		Later saves his name and email address in a secure cookie.
	'''

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def get(self):
		if self.get_argument("code", False):
			user_login = yield self.get_authenticated_user(		# get user data for his name
				redirect_uri=self.request.full_url().replace(	
                                        'http://', 'https://' ),		# always return to https
				client_id=self.settings["facebook_api_key"],
				client_secret=self.settings["facebook_secret"],
				code=self.get_argument("code")
				)
			user_data= yield self.facebook_request(			# get additional data to get the email address
				"/me",
				get_args={"field": "email"},
				access_token=user_login["access_token"]
				)

			self.set_secure_cookie("email", user_data["email"])
			self.set_secure_cookie("name", user_login["name"])

			next = self.get_argument("next", None)
			if next:
				self.redirect(next)
			else:
				self.redirect("/")
		else:
			if self.get_current_user():
				self.redirect("/")
			else:
				self.authorize_redirect(
					redirect_uri=self.request.full_url().replace(	# to facebook login page
						'http://', 'https://' ),		# always return to https
						client_id=self.settings["facebook_api_key"],
						extra_params={"scope": "email"}		# want users email
						)

class LoginHandler( BaseHandler ):
	'''Show login page.'''
	def get(self):
		if self.get_current_user():	# already logged in
			self.redirect("/")
		else:
			next = self.get_argument("next", None)	# where to redirect the user after login

			if next:
				args="?next=" + next
			else:
				args=""
			
			self.render("auth.html", args=args)

class LogoutHandler( BaseHandler ):
	'''Handle logout.
		Deletes user cookies for this site.
	'''
	def get(self):
		self.clear_cookie("email")
		self.clear_cookie("name")
		self.redirect("/")

