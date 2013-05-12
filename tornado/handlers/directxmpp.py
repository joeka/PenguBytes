from handlers.base import BaseHandler

class DirectXmppHandler(BaseHandler):
    '''Handler for xmpp contact form (chat).'''
    def get(self):
        '''Display it.'''
        bosh_service = self.settings["xmpp_bosh_service"]
        contact_jid = self.settings["xmpp_contact_jid"]
        xmpp_host = self.settings["xmpp_anon_host"]
        self.render("directxmpp.html",
            bosh_service=bosh_service, contact_jid=contact_jid, xmpp_host=xmpp_host)
