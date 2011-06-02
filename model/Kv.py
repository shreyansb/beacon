import sys
sys.path.append("../")
import logging
import MongoMixIn

class Kv(MongoMixIn.MongoMixIn):
    MONGO_DB_NAME           = 'kv'
    MONGO_COLLECTION_NAME   = 'kv_c'

    A_KEY                   = 'key'
    A_NS                    = 'ns'
    A_DT_C                  = 'dt_c'

    NS_LAT_OAUTH            = 'lat_oauth'

    @classmethod
    def setup_mongo_indexes(klass):
        from pymongo import ASCENDING, DESCENDING
        collection = klass.mdbc()
        collection.ensure_index([(klass.A_NS, ASCENDING),(klass.A_KEY, ASCENDING)], unique=True)
        collection.ensure_index([(klass.A_DT_C, DESCENDING)], unique=False)
        
    @classmethod
    def create_or_update_from_ns_and_key(klass, ns, key, data={}, raise_exception_on_fail=True):
        if not isinstance(data, dict):
           pass 

        document = {}
        document['ns'] = ns
        document['key'] = key
        for k,v in data.iteritems():
            document[k] = v

        try:
            klass.mdbc().update(spec={"ns":ns, "key":key}, document={"$set": document}, upsert=True, safe=True)
        except Exception, e:
            logging.error("COULD NOT UPSERT document in Kv. Exception: %s" % e.message)
            if raise_exception_on_fail:
                raise e

    @classmethod
    def find_by_ns_and_key(klass, ns, key):
        kv = klass.mdbc().find_one({"ns":ns, "key":key})
        if kv:
            return kv
        else:
            return None
            
    @classmethod
    def delete_by_ns_and_key(klass, ns, key):
        key = str(key)
        klass.mdbc().remove({"ns":ns, "key":key})
