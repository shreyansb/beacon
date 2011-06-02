import os
import logging
import re
import time
import pprint
from pymongo.objectid import ObjectId

class MongoMixIn(object):
    A_OBJECT_ID             = '_id'
    
    DATE_STR_FORMAT         = "%Y-%m-%d"
    DATE_STR_FORMAT_SHORT   = "%Y%m%d"
    
    @classmethod
    def its(klass):
        return int(time.time())

    @classmethod
    def current_timestamp(klass):
        return klass.its()
    
    @classmethod
    def row_attributes(klass, prefix=None):
        ats = []
        for a in dir(klass):
            if not prefix: 
                prefix = "A_"
            reg_exp = "^%s.*$" % prefix
            if re.search(reg_exp, a):
                ats.append(a)
        return ats
    
    @classmethod
    def klass_name(klass):
        return klass.__name__

    @classmethod
    def indexes(klass):
        return klass.mdbc().index_information()

    @classmethod
    def datetime_to_timestamp(klass, datetime_ob):
        return time.mktime(datetime_ob.timetuple())
    
    @classmethod
    def mdbc(klass):
        """ returns a pointer to the DB collection"""
        if not getattr(klass, 'MONGO_COLL_POINTER', None):
            from pymongo.connection import Connection
            connection = Connection()
            db = connection[klass.MONGO_DB_NAME]
            klass.MONGO_COLL_POINTER = db[klass.MONGO_COLLECTION_NAME]
        return klass.MONGO_COLL_POINTER
    
    @classmethod
    def mdb(klass):
        """ returns a pointer to the DB 
            This allows you to run commands using klass.mdb().command('<command goes here>')
        """
        if not getattr(klass, 'MONGO_DB_POINTER', None):
            from pymongo.connection import Connection
            connection = Connection()
            db = connection[klass.MONGO_DB_NAME]
            klass.MONGO_DB_POINTER = db
        return klass.MONGO_DB_POINTER
    
    @classmethod
    def dict_from_cursor(klass, cursor, key):
        r = {}
        try: 
            if cursor: 
                for c in cursor: 
                    r[c.get(key)] = c
        except: pass
        return r
                
    
    @classmethod
    def list_from_cursor(klass, cursor):
        r = []
        if cursor:
            for c in cursor:
                r.append(c)
        return r

    @classmethod
    def find_by_m_id(klass, id):
        if type(id) in [str, unicode]:
            id = re.sub(r"[\W]+", "", id)
        if type(id) in [str, unicode, int]:
            id = ObjectId(id)
        return klass.mdbc().find_one({"_id": id})
        
    @classmethod
    def objectId_from_object_id_string(klass, object_id_str):
        if type(object_id_str) in [str, unicode]:
            objectId = base_helper.objectId_from_string(object_id_str)
        else:
            objectId = object_id_str
        return objectId
        
    @classmethod
    def find_by_object_id(klass, object_id):
        objectId = klass.objectId_from_object_id_string(object_id)
        return klass.mdbc().find_one(objectId)
    
    @classmethod
    def remove_by_object_id(klass, object_id):
        objectId = klass.objectId_from_object_id_string(object_id)
        try:
            klass.mdbc().remove(objectId)
        except Exception, e:
            logging.error("Could NOT REMOVE document with id %s from model.%s Exception: %s" % (object_id, klass.__name__, e.message))
        
    @classmethod
    def update_by_object_id(klass, object_id, doc):
        objectId = klass.objectId_from_object_id_string(object_id)
        try:
            klass.mdbc().update(spec={klass.A_OBJECT_ID:objectId}, document={"$set": doc}, upsert=True, safe=True)
        except Exception, e:
            logging.error("Could NOT UPDATE document with id %s from model.%s Exception: %s" % (object_id, klass.__name__, e.message))

    @classmethod
    def find_by_user_id(klass, user_id):
        spec = {klass.A_USER_ID:int(user_id)}
        docs = klass.mdbc().find(spec)
        return klass.list_from_cursor(docs)

    @classmethod
    def create_or_update_by_user_id(klass, user_id, doc, upsert=True):
        if '_id' in doc:
            del doc['_id']
        spec = {klass.A_USER_ID:int(user_id)}
        try:
            klass.mdbc().update(spec, {"$set":doc}, upsert=upsert, safe=True)
            return True
        except Exception, e:
            logging.error("[%s.create_or_update_by_user_id] Error: %s" % (klass.klass_name, e))
            return False

    @classmethod
    def find_and_modify(klass, spec, doc, new=True):
        if not spec or not doc:
            return
        from pymongo.son import SON
        cmd = SON([('findandmodify',klass.MONGO_COLLECTION_NAME),('query',spec),('update',{'$set':doc}),('new',new)])
        try:
            output = klass.mdb().command(cmd)
            return output.get('value')
        except Exception, e:
            raise ApiMessage.MONGO_ERROR_DURING_FIND_AND_MODIFY(subs=e)

    @classmethod
    def strings_to_keywords(klass, strings, allowed_specials=[], ignore_default_allowed_specials=False):
        if not ignore_default_allowed_specials:
            allowed_specials += ["'"]
        
        allowed_specials = list(set(allowed_specials))
        specials_reg = "".join(["\\" + s for s in allowed_specials])
        reg = "[^\w\s%s]+" % specials_reg
        reg = re.compile(reg)
        
        cleaned_strings = []
        if type(strings) in [str, unicode]:
            strings = [strings]
        for s in strings:
            if s:
                s = smart_str(s)
                s = re.sub(reg, " ", s)
                s = re.sub(r"\s+", " ", s)
                s = s.strip()
                s = s.lower()
                if len(s) > 1:
                    cleaned_strings.append(s)
        big_string = " ".join(cleaned_strings)
        keywords = big_string.split(" ")
        return list(set(keywords))
