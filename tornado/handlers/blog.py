# -*- coding: utf-8 -*-
import datetime
import pytz

import tornado.web
import tornado.gen
import motor

from helpers import admin, slugify, excerpt
from pubsub import publish
from handlers.base import BaseHandler

class BlogHandler(BaseHandler):
    '''Handles the blog, single blog posts, edit / create / delete...
        Well this one is a mess.
    '''
    def formatDate( self, date ):
        '''Format date.
            Used to convert and format UTC date and time returned by mongodb.
            It is here and not in helpers to easily use it in the templates.
        '''
        date=date.replace(tzinfo=pytz.utc).astimezone(pytz.timezone( 
            self.settings["timezone"] ))    # you could also use the users timezone here
        return date.strftime("%c")

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def updateTagList(self, limit=42):
        '''Creates a list of the most used tags and saves it to the db.
            Argument: int limit
                limit specifies the length of the created list.
        '''
        db = self.settings['db']
        result = yield db.posts.aggregate( [
            { '$unwind' : "$tags" },
            { '$group': { '_id': "$tags", 'count': { '$sum': 1}}},
            { '$sort': {'count': -1 }}, { '$limit': limit } ]  )
        if result and 'result' in result:
            try:
                yield db.tags.rename( 
                    "tagsBackup", dropTarget=True ) # backup of the old list
            except:
                print "No tags collection"
            
            yield db.tags.insert(
                result['result'] )


    @admin
    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def editArticle(self, slug=None, new=False):
        '''Edit a blog post.
            Optional: string slug
            Optional: boolean new
                new: create new post.
                To edit slug must be specified as argument or http argument
        '''
        if not slug:
            slug = self.get_argument('slug', None)
        if not new and not slug:
            raise tornado.web.HTTPError(400, "Field slug missing")
        else:
            article_title = self.get_argument('title', "")
            article_text = self.get_argument('text', "")
            article_tags = self.get_argument('tags', "")
            
            if not new:
                if article_text == "" and  article_title == "" and  article_tags == "":
                    # if the users hasn't already provided new text etc. get it from the db
                    db = self.settings["db"]
                    article = yield db.posts.find_one( { 'slug': slug })
                    if not article:
                        raise tornado.web.HTTPError(500, "Database error")
                    else:
                        article_text = article["text"]
                        article_title = article["title"]
                        if "tags" in article:   
                            article_tags = " ".join(article["tags"])

            if self.get_argument("text_missing", False):
                message = "Please provide a text."
            elif self.get_argument("title_missing", False):
                message = "Please make up a fancy title."
            else:
                message = ""
            if new:
                action = "/blog?new=true"
                title = "New blog post"
            else:
                action = "/blog?slug="+slug
                title = "Edit blog post"
            
            self.render("edit_article.html",
                title = title,
                message = message,
                article_text = article_text,
                article_title = article_title,
                article_tags = article_tags,
                action= action,
                new=new)

    @admin
    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def deleteArticle(self, slug=None):
        '''Delete blog post.
            Optional: string slug
                slug must be provided as argument or http arument.
        '''
        if not slug:
            slug = self.get_argument("slug")    # will output http error if necessary

        db = self.settings['db']
        response = yield db.posts.remove( { 'slug': slug })
        if not response:
            raise tornado.web.HTTPError(500, "Database error")
        else:
            self.updateTagList()
            self.redirect("/blog")

    @tornado.web.asynchronous
    def get(self, post=None, tags=None):
        '''Show the blog or blog posts, edit / create form...
            Optional: string post
            Optionas: tags
        '''
        db = self.settings["db"]
        
        if self.get_argument("delete", False):
            self.deleteArticle(slug=post)
        elif self.get_argument("edit", False):
            self.editArticle(slug=post)
        else:
            if post == "tags":
                if tags:
                    tags = tags.split(" ")  # multiple tags can be provided connected by "+"
                    filter ={ 'tags': { '$in': tags } } # Filter blog post for tags
                post=None
            else:
                filter = {}

            if not post:    # no single post or other operation is selected -> show multiple posts
                show=int(self.get_argument("s", self.settings["articles_limit"]))# amount of posts shown per page
                if show < 1 or show > 50:       # hard coded max limit, you probably want to change this
                    show = 5
                page=int(self.get_argument("p", 1)) # current page
                if page < 1:
                    page = 1
                skip = show * (page - 1)
                db.posts.find(filter, skip=skip, limit=show).sort( 
                    'date', -1 ).to_list(
                    callback=lambda response, error: self._on_response(response, error, page=page, show=show, filter=filter, tags=tags), length=None)
                    # used lambda to provide a callback with arguments
                    # db callback to _on_response

            elif post == "new":
                self.editArticle(new=True)  # create new post
            else:
                db.posts.find_one({ 'slug': post }, callback=self._on_single)   # get and show a single post


    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def _on_single(self, response, error):
        '''Database callback for getting a single post in get.
            Handles errors and shows a single blog post.
        '''
        if error:
            raise tornado.web.HTTPError(500, error)

        if response:
            db = self.settings['db']
            cursor = db.tags.find(limit=16)
            tagList = yield cursor.to_list(length=16) # get list of most used tags (list created in updateTagList)

            self.render("blog.html", 
                title="blög: " + tornado.escape.native_str(response["title"]),
                # You may want to change the blog title, I'm tired of creating new options right now
                articles = [response], editable=self.is_admin(), formatDate=self.formatDate, tagList=tagList, nav_right=None, nav_left=None )
        else:
            raise tornado.web.HTTPError(404)

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def _on_response(self, response, error, page=1, show=5, filter={}, tags=None):
        '''Database callback for multiple blog posts in get.
            Handle errors and show multiple blog posts.
        '''
        if error:
            raise tornado.web.HTTPError(500, str(error))

        db = self.settings['db']
        cursor = db.tags.find(limit=16)
        tagList = yield cursor.to_list(length=16)    # get list of most used tags (list created in updateTagList)"
        cursor = db.posts.find(filter)      # filter is provided by get and used to search by tag(s)
        count = yield cursor.count()
        if count > show:
            if tags:
                nav_url ="/blog/tags/"+"+".joint(tags)
            else:
                nav_url = "/blog"

            if page > 1:
                nav_left = nav_url + "?p=" + str(page - 1) \
                    + "&s=" + str(show)
            else:
                nav_left = None
            if page < (count - 1 + show) / show:    # more pages to come?
                nav_right = nav_url + "?p=" +str(page + 1) \
                    + "&s=" + str(show)
            else:
                nav_right = None
        else:
            nav_left = None
            nav_right = None

        self.render("blog.html", title="blög",
            articles = response, editable=self.is_admin(), formatDate=self.formatDate, tagList=tagList, page=page, nav_left=nav_left, nav_right=nav_right)

    @admin
    @tornado.web.asynchronous
    def post(self):
        '''Handle post requests to create / edit blog posts'''
        new = self.get_argument('new', False)
        title = self.get_argument('title', None)
        text = self.get_argument('text', None)
        slug = self.get_argument('slug', None)
        tags = self.get_argument('tags', None).lower()

                
        if new:
            if not text:
                self.redirect("/blog/new?title="
                    +tornado.escape.url_escape(title or "")
                    +"&tags="+tornado.escape.url_escape(tags or "")
                    +"&text_missing=true")
                return
            elif not title:
                self.redirect("/blog/new?text="
                    +tornado.escape.url_escape(text or "")
                    +"&tags="+tornado.escape.url_escape(tags or "")
                    +"&title_missing=true")
                return
            else:
                slug = slugify( title ) # creates something to be used as 'id' and part of the url for the post


        else:   # edit post
            if not slug or slug=="undefined":
                raise tornado.web.HTTPError(400, "Post field slug missing")
            if not text:
                self.redirect("/blog/edit?title="
                    +tornado.escape.url_escape(title or "")
                    +"&slug="+slug
                    +"&tags="+tornado.escape.url_escape(tags or "")
                    +"&text_missing=true")
                return
            elif not title:
                self.redirect("/blog/new?text="
                    +tornado.escape.url_escape(text or "")
                    +"&slug="+slug
                    +"&tags="+tornado.escape.url_escape(tags or "")
                    +"&title_missing=true")
                return

        update = {}
        pubsubData = {}
        newSlug = slug
        if title:
            update['title'] = title
            if new or self.get_argument('change_slug', False):
                # change_slug is an extra option because you probably don't want to do this
                # by default as it breaks external links
                update['slug'] = slugify( title )
                newSlug = update['slug']
            
            pubsubData['title'] = title 

        if text:
            update['text'] = text
            pubsubData['summary'] = excerpt( text )
        if tags:
            update['tags'] = tags.split(" ")
       
        pubsubData['author'] = { 'name': self.settings["author_name"], 'email': self.settings["author_email"]}
        pubsubData['updated'] = datetime.datetime.utcnow().isoformat() + "Z"
        pubsubData['id'] = pubsubData['link'] = "http://%s/blog/%s"%(self.settings["domain"], newSlug)
        
        publish("blog", pubsubData, self.settings) # publish through xmpp pubsub
      
        db = self.settings["db"]
        if new:
            update['date'] =  datetime.datetime.utcnow()
            db.posts.insert( update,
                callback=lambda response, error: self._on_edit(response, error, slug=slug))
        
        else:
            db.posts.update( {'slug': slug},
                { '$set': update },
                callback=lambda response, error: self._on_edit(response, error, slug=newSlug))
            

    def _on_edit(self, response, error, slug=None):
        '''Database callback for insert and update operations in editArticle.
            Optional: string slug
                slug is used to redirect the user to the new / updated blog post.
        '''
        if error:
            raise tornado.web.HTTPError( 500, error )
        else:
            self.updateTagList()
        
        if slug:
            self.redirect( "/blog/" + slug )
        else:
            self.redirect( "/blog" )

