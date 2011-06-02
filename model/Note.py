import sys
sys.path.append("../")
import logging
import uuid
import datetime
import MongoMixIn

class Note(MongoMixIn.MongoMixIn):    
    MONGO_DB_NAME           = 'note'
    MONGO_COLLECTION_NAME   = 'note_c'
    
    A_ID                    = 'id'
    A_TEXT                  = 'text'
    A_LOC                   = 'loc'
    A_DT                    = 'dt'
    A_EXP_DATE              = 'exp_date'
    A_INACTIVE              = 'inactive'
    A_LAT                   = 'lat'
    A_LON                   = 'lon'
    A_DISTANCE              = 'distance'
    A_DT_LAST_SENT          = 'dt_last_sent'
    A_RESEND_INTERVAL       = 'resend_interval'

    A_REQ_PLACE_ID          = 'place_id'
    A_REQ_KEYWORDS          = 'req_keywords'
    A_REQ_MAX_DISTANCE      = 'req_max_distance'
    A_REQ_MAX_DISTANCE_FROM = 'req_max_distance_from'

    DATE_STR_FORMAT         = "%Y-%m-%d"
    DEFAULT_RESEND_INTERVAL = 24                        # hours
    RADIUS_OF_THE_EARTH     = 6378.1                    # Km

    @classmethod
    def setup_mongo_indexes(klass):
        from pymongo import GEO2D
        coll = klass.mdbc()
        coll.ensure_index([ (klass.A_LOC, GEO2D)], unique=False)
    
    @classmethod
    def find_notes_near_location(klass, lat, lon, radius=None, limit=50):
        loc = [float(lat), float(lon)]
        if radius:
            spec = {klass.A_LOC:{"$within":{"$center":[loc, radius]}}}
        else:
            spec = {klass.A_LOC:{"$near":loc}}
        cursor = klass.mdbc().find(spec).limit(limit)
        return klass.list_from_cursor(cursor)

    @classmethod
    def mark_note_as_inactive(klass, note_id):
        spec = {klass.A_ID:note_id}
        doc = {klass.A_INACTIVE:1}
        klass.mdbc().update(spec=spec, document={"$set":doc}, upsert=True, safe=True)

    @classmethod
    def create_or_update_note(klass, doc=None):      
        if not doc: doc = {}

        note_id = doc.get(klass.A_ID)
        if not note_id:
            note_id = str(uuid.uuid4())
        spec = {klass.A_ID:note_id}

        lat = doc.get(klass.A_LAT)
        lon = doc.get(klass.A_LON)
        if lat and lon:
            doc[klass.A_LOC] = [float(lat), float(lon)]
            del doc[klass.A_LAT]
            del doc[klass.A_LON]

        doc[klass.A_DT] = datetime.datetime.now()

        oid = doc.get('_id')
        if oid: del doc['_id']

        try:
            klass.mdbc().update(spec=spec, document={"$set": doc}, upsert=True, safe=True)
            return note_id
        except Exception, e:
            logging.error("COULD NOT UPSERT document in model.Rebate. Exception: %s" % e.message)
        return None

