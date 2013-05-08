import base64
import urllib

import tornado.web

from handlers.base import BaseHandler

import tornado.httpclient
import tornado.escape
import tornado.gen

class XmppRegisterHandler( BaseHandler ):
	'''Show register page for xmpp accounts.
	'''
	@tornado.web.authenticated
	def get(self):
		username =  self.get_argument("username", default="")
		if self.get_argument("success", default=None ):		# Registration was successful
			text = "Successfully registered " + username + "@" + self.settings["xmpp_domain"]
			self.render("../templates/xmpp/register_success.html",
				title="XMPP registration",
				text=text,
				)
			return

		error = self.get_argument("error", default=None)
		if self.get_argument("passmiss", default=None):
			text = "The passwords you entered don't match."
		elif self.get_argument("empty", default=None):
			text = "Please provide a username and a password."
		elif error:
			# Errors from mod_register_json
			if error == "401":
				text="Registration failed and still pending, please wait 5 minutes or choose another name."
			elif error == "403":
				text="Blacklisted: please contact the admin."
			elif error == "406":
				text="The username contains invalid characters, see RFC 6122."
			elif error == "409":
				text="The username already exists or there is another account for your email address."
			elif error == "503":
				text="You are retrying to rapidly, please chill the fuck out."
			else:
				text = "Something went wrong. Sorry. Please contact the admin."
		else:
			text =  "Register your xmpp address for " + self.settings["xmpp_domain"] +":"
	
		username =  self.get_argument("username", default="")
		self.render("../templates/xmpp/register_form.html",
			title="XMPP registration",
			action="/xmpp_register",
			text=text,
			username=username
			)
		

	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		username=self.get_argument("username", default="")
		password=self.get_argument("password", default="")
		password2=self.get_argument("password2", default="")
	
		if username=="" or password == "":
			self.redirect(
				self.request.uri + "?empty=true&username=" \
					+ tornado.escape.url_escape( username )
				)
			return
		if password != password2:
			self.redirect(
				self.request.uri + "?passmiss=true&username=" \
					+ tornado.escape.url_escape( username )
				)
			return
		
		email = self.get_secure_cookie("email")

		http_client = tornado.httpclient.AsyncHTTPClient()
		
		body = tornado.escape.json_encode(	# Request for mod_register_json
			 {	"username": username,
				"password": password,
				"auth_token": self.settings["xmpp_token"],
				"mail": email,
				"host": self.settings["xmpp_domain"],
				"ip":self.request.remote_ip}
			)
		encodedBody = base64.urlsafe_b64encode(body)

		request = tornado.httpclient.HTTPRequest(
			self.settings["xmpp_registerurl"],
			method="POST",
			headers= {
				"Content-Type": "application/encoded",
				"Content-Transfer-Encoding": "base64"
				},
			body=encodedBody,
			)
		try:
			response = yield http_client.fetch(request)
		except tornado.httpclient.HTTPError as e:
			self.redirect(
				self.request.uri + "?error=" + str(e.code) \
					+"&username="+tornado.escape.url_escape(username)
				)
			return
		
		#	I don't want to modify mod_register_json to keep updates easy,
		#	therfore I still have the email verification mechanism in here,
		#	but don't use it, as the email is verified by google or facebook.
		uuid = response.body	# Verification code
		
		body = {"uuid": uuid}
		encodedBody = urllib.urlencode(body)

		request = tornado.httpclient.HTTPRequest(
			self.settings["xmpp_registerurl"] + "verify/",
			method="POST",
			body=encodedBody
			)
		try:
			response = yield http_client.fetch(request)	# send verification code right back to prosody
		except tornado.httpclient.HTTPError as e:
			self.redirect(
				self.request.uri + "?error=" + str(e.code) \
					+"&username="+tornado.escape.url_escape(username)
				)
			return
		
		self.redirect(
			self.request.uri + "?success=true" \
				+"&username="+tornado.escape.url_escape(username)
			)
