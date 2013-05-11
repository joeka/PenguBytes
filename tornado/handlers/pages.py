import datetime
import tornado.web
import motor
from helpers import admin, excerpt
from pubsub import publish
from handlers.base import BaseHandler

class PagesHandler(BaseHandler):
    '''Handle regular pages.
        Handles updating / creating / deleting too
    '''
    @admin
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def editPage(self, name=None):
        '''Edit page.
            Optional: string name
            Name must be provided here or by http argument
            name can also be "new" or "edit", this is not good but I want a pretty way
                to make /edit urls and in other cases this part of the url is the name.
        '''
        new = name == "new" or self.get_argument("new", False)  # create new page?
        if name != "new" and name != "edit":    # name not used for a command
            page_name = name    
        else:
            page_name = self.get_argument( "name", "")  # alternatively get name from http argument
        if not new and (not page_name or page_name == ""):
            raise tornado.web.HTTPError( 400, "Don't know what to edit" )
        
        page_title = self.get_argument("title", "")
        page_text = self.get_argument("text", "")
        if not new and page_title=="" and page_text=="":
            # if the user hasn't already sent new title or text, load it from the db
            db = self.settings["db"]
            page = yield motor.Op( db.pages.find_one, {'name': page_name })
            if not page:
                raise tornado.web.HTTPError(500, "Database error")
            
            page_title = page['title']
            page_text = page['text']
        
        if self.get_argument("text_missing", False):
            message = "Please provide a text"
        elif self.get_argument("title_missing", False):
            message = "Please provide a title"
        elif self.get_argument("name_missing", False):
            message = "Please provide a name"
        else:
            message = ""

        if new:
            action = "/new"
            title = "Create page"
        else:
            action = "/"+page_name+"?edit=true"
            title = "Edit page"

        self.render("edit_page.html",
            title = title,
            message = message,
            action = action,
            page_name = page_name,
            page_title = page_title,
            page_text = page_text)


    @admin
    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def deletePage(self, name=None):
        '''Delete page.
            Optional: string name
                Optional for the function, not for the success of it.
        '''
        if not name:    # No page specified
            raise tornado.web.HTTPError(400, "Delete what?")

        db = self.settings['db']
        response = yield motor.Op( db.pages.remove, { 'name': name })
        if not response:
            raise tornado.web.HTTPError(500, "Database error")
        else:
            self.redirect("/")


        
    @tornado.web.asynchronous
    def get(self, page):
        '''Show page.
            Argument: string page
        '''
        if page == "new" or self.get_argument('edit', False):
            self.editPage(name=page)    # modify or create a page
        elif self.get_argument('delete', False):
            self.deletePage(name=page)  # delete oage
        else:
            db = self.settings['db']
            db.pages.find_one( {'name': page}, callback=self._on_response )
            # rendering page in _on_response after callback from database
        
    def _on_response(self, response, error):
        '''Response for database query in get.
            Handles errors and renders the page
        '''
        if error:
            raise tornado.web.HTTPError( 500, error )

        if not response:
            raise tornado.web.HTTPError(404)

        self.render("page.html", page=response, editable=self.is_admin())

    @admin
    @tornado.web.asynchronous
    def post(self, page):
        '''Handle post requests for create / edit / delete functions.
            Argument: string page
        '''
        new = page  == "new"    # create new page?
        
        title = self.get_argument('title', None)
        text = self.get_argument('text', None)

        name = self.get_argument('name', None)

        if new:
            if not name:
                self.redirect( "/new?name_missing=true&title="
                    +tornado.escape.url_escape(title or "")
                    +"&text="+ tornado.escape.url_escape(text or "")
                    +"&new=true")
            if not title:
                self.redirect( "/new?title_missing=true&name="
                    +tornado.escape.url_escape(name or "")
                    +"&text="+tornado.escape.url_escape(text or "")
                    +"&new=true")
            if not text:
                self.redirect( "/new?text_missing=true&name="
                    +tornado.escape.url_escape(name or "")
                    +"&title="+tornado.escape.url_escape(title or "")
                    +"&new=true")

            pubsubData = {}
            pubsubData['title'] = title 
            pubsubData['summary'] = excerpt( text )
            pubsubData['author'] = { 'name': self.settings["author_name"], 'email': self.settings["author_email"]}
            pubsubData['updated'] = datetime.datetime.utcnow().isoformat() + "Z"
            pubsubData['id'] = pubsubData['link'] = "http://%s/%s"%(self.settings["domain"], name)
            publish("pages", pubsubData, self.settings) # publish through xmpp pubsub

            update = { "name": name, "title": title, "text": text }
            db = self.settings['db']
            db.pages.insert( update,
                callback=lambda response, error: self._on_post(
                    response, error, name=name) )
                # lambda used as way to specify callback with arguments
                # Database callback to _on_post

        else:
            if not name:
                self.redirect( "/"+page+"?name_missing=true&title="
                    +tornado.escape.url_escape(title or "")
                    +"&text="+ tornado.escape.url_escape(text or "")
                    +"&edit=true")
            if not title:
                self.redirect( "/"+page*"?title_missing=true&name="
                    +tornado.escape.url_escape(name or "")
                    +"&text="+tornado.escape.url_escape(text or "")
                    +"&edit=true")
            if not text:
                self.redirect( "/"+page+"?text_missing=true&name="
                    +tornado.escape.url_escape(name or "")
                    +"&title="+tornado.escape.url_escape(title or "")
                    +"&edit=true")

            pubsubData = {}
            pubsubData['title'] = title 
            pubsubData['summary'] = excerpt( text )
            pubsubData['author'] = { 'name': self.settings["author_name"], 'email': self.settings["author_email"]}
            pubsubData['updated'] = datetime.datetime.utcnow().isoformat() + "Z"
            pubsubData['id'] = pubsubData['link'] = "http://%s/%s"%(self.settings["domain"], name)
            publish("pages", pubsubData, self.settings) # publish through xmpp pubsub

            update = { "name": name, "title": title, "text": text }
            db = self.settings['db']
            db.pages.update( {'name': page},
                { '$set': update},
                callback=lambda response, error: self._on_post(
                    response, error, name=name) )
                # lambda used as way to specify callback with arguments
                # Database callback to _on_post


    def _on_post(self, response, error, name=None):
        '''Callback for mongodb insert and update operations of post.'''
        if error:
            raise tornado.web.HTTPError( 500, error )
        
        if name:
            self.redirect("/"+name) # to the created/updated page
        else:
            self.redirect("/") 

