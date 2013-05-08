PenguBytes
==========
Website using tornado


This is something I made in the last week or so and it's my first "experiment" with tornado and therefore you should probably not use it to host your website, but maybe you can find something in there that is of use for you.

tornado/pengubytes.py:
	Main script to start it. Use "--port" so that you can run multiple instances e. g. behind nginx.

tornado/settings.py:
	Settings go here.

tornado/handlers/ is were the work gets done.

tornado/templates/ well... templates.

static/ contains css and javascript


If you would want to use it, even if it's not pretty at all:

* Move settings.example.py to settings.py and change everything.
* Replace the hardcode stuff in the templates (I guess one would want to change these anyway).
* Find the hardcoded stuff in the handlers :)

I also used https://github.com/kswedberg/jquery-expander (put it with jquery in static/js/)

and for blog / page editing http://www.tinymce.com (in static/tinymce/).

Oh well and for the xmpp part you would need a recent version of prosody with mod_register_json.

See it in action: https://pengubytes.de
