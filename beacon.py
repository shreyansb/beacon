import re
import urlparse
import urllib
from urlparse import parse_qs, parse_qsl
import oauth2 as oauth

import tornado.httpserver
import tornado.ioloop
import tornado.web

import settings

from model.Kv import Kv
from lib.NoteHelper import NoteHelper
from lib import geo_utils

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        lat, lon, map_url = geo_utils.get_current_city()
        if not lat or not lon or not map_url:
            return self.redirect('/beacon/oauth/latitude')
        nearby_notes = []
        nearby_places = []
        self.render('templates/beacon.html', 
                    map_url=map_url, 
                    nearby_places=nearby_places,
                    nearby_notes=nearby_notes)


class ManageNotesHandler(tornado.web.RequestHandler):
    def get(self):
        if re.match('^/beacon/view.*$', self.request.uri):
            pass
        elif re.match('^/beacon/add.*$', self.request.uri):
            return self.add_note_form()
        else:
            return self.redirect('/beacon')

    def post(self):
        if re.match('^/beacon/add$', self.request.uri):
            return self.add_note()

    def add_note_form(self):
        if re.match('^.*?success=1$', self.request.uri):
            status = "success"
        elif re.match('^.*?failed=1$', self.request.uri):
            status = "failed"
        else:
            status = None
        self.render('templates/add_note.html', status=status)

    def add_note(self):
        lat = self.get_argument('lat')
        lon = self.get_argument('lon')
        note_text = self.get_argument('note_text')
        max_distance = self.get_argument('max_distance')
        if not (lat and lon and note_text):
            return self.redirect('/beacon/add')
        if not max_distance:
            max_distance = 150
        else:
            max_distance = int(max_distance)
        lat = float(lat)
        lon = float(lon)
        NoteHelper.add_note(lat, lon, note_text, max_distance_in_meters=max_distance)
        return self.redirect('/beacon/add?success=1')

class LatitudeOAuthHandler(tornado.web.RequestHandler):
    def get(self):
        if re.match('^/beacon/oauth/latitude/callback.*$',self.request.uri):
            return self.oauth_callback()
        return self.oauth_start()

    def oauth_start(self):
        # get oauth client
        consumer = oauth.Consumer(settings.LAT_CONSUMER_KEY,
                                  settings.LAT_CONSUMER_SECRET)
        client = oauth.Client(consumer)
        
        # get request token
        request_body = urllib.urlencode(settings.LAT_PARAMETERS, True)
        resp, content = client.request(settings.LAT_REQUEST_TOKEN_URL, 
                                       'POST', 
                                       headers=settings.LAT_HEADERS, 
                                       body=request_body)
        if resp.get('status') != '200':
            raise Exception('Invalid response %s.' % resp.get('status'))

        request_token = dict(parse_qsl(content))
        ns = Kv.NS_LAT_OAUTH
        key = 'shreyans'
        Kv.create_or_update_from_ns_and_key(ns, key, request_token)

        # redirect user to authorization url
        base_url = urlparse.urlparse(settings.LAT_AUTHORIZE_URL)
        query = parse_qs(base_url.query)
        query['oauth_token'] = request_token.get('oauth_token')
        url = (base_url.scheme, base_url.netloc, base_url.path, base_url.params, urllib.urlencode(query, True), base_url.fragment)
        authorize_url = urlparse.urlunparse(url)
        self.redirect(authorize_url)

    def oauth_callback(self):
        oauth_verifier = self.get_argument('oauth_verifier', None)
        oauth_token = self.get_argument('oauth_token', None)
        if not oauth_verifier or not oauth_token:
            return self.write("One or more of the following were missing: oauth_verifier, oauth_token")
        
        ns = Kv.NS_LAT_OAUTH
        key = 'shreyans'
        request_token = Kv.find_by_ns_and_key(ns, key)
        if not request_token:
            return self.write("Request token not found for key: %s" % key)

        token = oauth.Token(request_token.get('oauth_token'), request_token.get('oauth_token_secret'))
        token.set_verifier(oauth_verifier)
        consumer = oauth.Consumer(settings.LAT_CONSUMER_KEY,
                                  settings.LAT_CONSUMER_SECRET)
        client = oauth.Client(consumer, token)
        request_body = urllib.urlencode(settings.LAT_PARAMETERS, True)
        resp, content = client.request(settings.LAT_ACCESS_TOKEN_URL, 'POST',
                                       headers=settings.LAT_HEADERS,
                                       body=request_body)
        access_token = dict(parse_qsl(content))
        
        Kv.create_or_update_from_ns_and_key(ns, key, access_token)

        self.redirect("/beacon")


application = tornado.web.Application([
    (r"/beacon", MainHandler),
    (r"/beacon/add.*", ManageNotesHandler),
    (r"/beacon/view.*", ManageNotesHandler),
    (r"/beacon/oauth/latitude.*", LatitudeOAuthHandler),
])

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8883)
    tornado.ioloop.IOLoop.instance().start()
