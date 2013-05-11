import xmpp
import time

def dict2node( payload ):
    """Convert dict to a node with atom content"""
    node = xmpp.simplexml.Node( tag = "entry" )
    for tag, value in payload.iteritems():
        if tag == "link":
            node.addChild( name="link",  attrs={"rel": "alternate", 'type': 'text/html', 'href': value })
        elif tag == "author":
            node.T.author = ""
            for author_tag, author_value in value.iteritems():
                node.T.author.setTagData( author_tag, author_value )
        else:
            node.setTagData( tag, value )
    
    node.namespace = 'http://www.w3.org/2005/Atom'
    return node

def publish(node, payload, settings):
    """Publishes (atom) item to pubsub node"""
    entry = dict2node(payload)
    iq = build_iq(node, entry, settings)
    send_message(iq, settings)

def build_iq(node, entry, settings):
    iq = xmpp.protocol.Iq(typ='set',
			frm=settings['xmpp_jid']+"/server",
            to=settings['xmpp_pubsub_host'], )
    iq.NT.pubsub
    iq.T.pubsub.namespace = xmpp.protocol.NS_PUBSUB
    iq.T.pubsub.NT.publish
    iq.T.pubsub.T.publish['node'] = node
    iq.T.pubsub.T.publish.NT.item
    iq.T.pubsub.T.publish.T.item.addChild( node = entry )
    return iq

def send_message(msg, settings):
    """Sends a message using xmpppy
    msg should be a xmpp.protocol.Message instance
    """
    from_jid = xmpp.protocol.JID(settings['xmpp_jid'])
    passwd = settings['xmpp_password']

    client = xmpp.Client(from_jid.getDomain(), debug=[])
    if client.connect():
        if client.auth(from_jid.getNode(), passwd):
            client.send(msg)
        client.disconnect()
