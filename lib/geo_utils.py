import logging
import urllib
import simplejson
import math

import settings

from lib import oauth_wrap
from lib import better_http

from model.Kv import Kv

def get_current_city():
    return get_current_location(return_map_url=True, granularity='city')

def get_current_location(return_map_url=False, granularity='best'):
    ns = Kv.NS_LAT_OAUTH
    key = 'shreyans'
    lat_oauth_token_dict = Kv.find_by_ns_and_key(ns, key)
    if not lat_oauth_token_dict:
        return None, None, None

    http = oauth_wrap.get_wrapped_http(lat_oauth_token_dict)
    url = settings.LAT_ENDPOINT % 'currentLocation'
    params = {
        'granularity':granularity,
    }
    url = url + "?" + urllib.urlencode(params)
    resp, content = http.request(url)

    if resp.get('status') != '200':
        return None, None, None

    content = simplejson.loads(content)

    lat = content.get('data').get('latitude')
    lon = content.get('data').get('longitude')
    map_url = static_map_from_lat_lon(lat, lon)

    if return_map_url:
        return lat, lon, map_url
    else:
        return lat, lon

def get_nearby_places(lat, lon, query=None, limit=50, timeout=9000, sort_by_distance=False):
    url = "https://api.foursquare.com/v2/venues/search"
    params = {
        "ll": "%s,%s" % (lat, lon),
        "client_id": settings.FOURSQUARE_CONSUMER_KEY,
        "client_secret": settings.FOURSQUARE_CONSUMER_SECRET
    }
    if query not in [None, '']:
        params['query'] = query
    if limit not in [None, '']:
        params['limit'] = int(limit)

    logging.debug("params for foursquare nearby places search: %s " % params)

    qs = better_http.urlencode(params)
    url = "%s?%s" % (url, qs)
    logging.info(url);
    resp = better_http.get(url, timeout=timeout)
    try:
        resp = simplejson.loads(resp)
    except:
        logging.error("error parsing json response from foursquare %s" % locals());
        return []

    if resp and resp.get('response') and resp.get('response').get('groups'):
        places = []
        place_ids_set = set()
        groups = resp['response']['groups']
        for g in groups:
            for p in g.get('items'):
                i = p.get('id')
                if not i or i in place_ids_set:
                    continue
                else:
                    places.append(p)
                    place_ids_set.add(i)
        if sort_by_distance:
            places.sort(key=lambda x: x.get('location').get('distance'))
        return places
    else:
        logging.warning("No place results %s" % locals());
        return []

def distance_between_two_points(loc1, loc2):
    lat1 = loc1[0]
    lon1 = loc1[1]
    lat2 = loc2[0]
    lon2 = loc2[1]
    #
    # http://www.geesblog.com/2009/01/calculating-distance-between-latitude-longitude-pairs-in-python/
    # The following formulas are adapted from the Aviation Formulary
    # http://williams.best.vwh.net/avform.htm
    #
    nauticalMilePerLat = 60.00721
    nauticalMilePerLongitude = 60.10793
    rad = math.pi / 180.0
    #milesPerNauticalMile = 1.15078
    kmPerNauticalMile = 1.85200
    yDistance = (lat2 - lat1) * nauticalMilePerLat
    xDistance = (math.cos(lat1 * rad) + math.cos(lat2 * rad)) * (lon2 - lon1) * (nauticalMilePerLongitude / 2)
    distance = math.sqrt( yDistance**2 + xDistance**2 )
    return distance * kmPerNauticalMile

def static_map_from_lat_lon(lat, lon, width=600, height=400, zoom=15):
    url = "http://maps.google.com/maps/api/staticmap?"
    url += "center=%s,%s" % (lat, lon)
    url += "&zoom=%s&size=%sx%s&maptype=roadmap" % ( zoom, width, height )
    url += "&markers=color:blue|label:$|%s,%s" % (lat, lon) 
    url += "&sensor=false"
    return url
