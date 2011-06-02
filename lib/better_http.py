import pycurl
import cStringIO
import urllib
import logging

HTTP_TIMEOUT = 500
HTTP_FOLLOW_REDIRECTS = True
HTTP_MAX_REDIRECTS = 5

def urlencode(query, doseq=0):
    """ 
    Simple wrapper function that converts all parameters to utf-8 strings before
    passing to urllib.urlencode
    """
    if hasattr(query,"items"):
        query = query.items()
    
    cleaned = []
    for el in query:
        key = el[0].encode('utf-8')
        val = el[1]
        if val == None:
            val = ''
        if isinstance(val,list):
            cleaned_val = []
            for val_el in val:
                cleaned_val.append(val_el.encode('utf-8'))
            val = cleaned_val
        else:
            if not type(val) in [float, int, long, bool]:
                try:
                    val = val.encode('utf-8')
                except:
                    pass
            
        cleaned.append((key,val))

    return urllib.urlencode(cleaned, doseq)
    

def get(url, timeout=HTTP_TIMEOUT, follow_location=HTTP_FOLLOW_REDIRECTS, max_redirects=HTTP_MAX_REDIRECTS, return_http_status_code=False, cookie_file_name=None):
    """
    Simple wrapper function to perform HTTP GET requests with pycurl.
    Exceptions caught will perform pycurl cleanup before being re-raised.
    """
    
    result = None
    
    try:
        buffer = cStringIO.StringIO()
        
    	curl = pycurl.Curl()
    	curl.setopt(pycurl.TIMEOUT_MS, timeout)
    	curl.setopt(pycurl.URL, str(url))
    	curl.setopt(pycurl.FOLLOWLOCATION, follow_location)
    	curl.setopt(pycurl.MAXREDIRS, max_redirects)
    	curl.setopt(pycurl.WRITEFUNCTION, buffer.write)
        curl.setopt(pycurl.NOSIGNAL, 1)
        if cookie_file_name:
            # Option -b/--cookie <name=string/file> Cookie string or file to read cookies from
            # Note: must be a string, not a file object.
            curl.setopt(pycurl.COOKIEFILE, cookie_file_name)
            
            # Option -c/--cookie-jar <file> Write cookies to this file after operation
            # Note: must be a string, not a file object.
            curl.setopt(pycurl.COOKIEJAR, cookie_file_name)
        
        
    	curl.perform()
    	result = buffer.getvalue()
    	buffer.close()
    	http_status_code = None
    	if return_http_status_code:
    	    http_status_code = curl.getinfo(pycurl.HTTP_CODE)
    	curl.close()
    except:
        try:
    		curl.close()
    	except:
    		pass
    		
    	raise
    if return_http_status_code:
        return {"http_status_code": http_status_code, "result": result}
    else:
        return result


def post(url, post_data={}, timeout=HTTP_TIMEOUT, follow_location=HTTP_FOLLOW_REDIRECTS, max_redirects=HTTP_MAX_REDIRECTS, username=None, password=None, return_http_status_code=False, cookie_file_name=None, insecure=False, headers={}, debug=False):
    """
    Simple wrapper function to perform HTTP POST requests with pycurl.
    Exceptions caught will perform pycurl cleanup before being re-raised.
    """
    
    result = None
    buffer = cStringIO.StringIO()

    curl = pycurl.Curl()

    curl.setopt(pycurl.POST, 1)
    if not post_data:
        post_data = {}
    if isinstance(post_data, dict):
        post_data = urlencode(post_data)
    try:
        curl.setopt(pycurl.POSTFIELDS, post_data)
    except TypeError, e:
        logging.error("POSTFIELDS failed, post_data (%s): %s" % (type(post_data), post_data))
        if type(post_data) == unicode:
            post_data = post_data.encode('utf8')
        curl.setopt(pycurl.POSTFIELDS, post_data) # do this again so it bubbles up


    curl.setopt(pycurl.TIMEOUT_MS, timeout)
    curl.setopt(pycurl.URL, str(url))
    curl.setopt(pycurl.FOLLOWLOCATION, follow_location)
    curl.setopt(pycurl.MAXREDIRS, max_redirects)
    curl.setopt(pycurl.WRITEFUNCTION, buffer.write)
    curl.setopt(pycurl.NOSIGNAL, 1)
    
    if headers == {}:
        pass
    elif isinstance(headers, dict):
        hd = headers
        headers = []
        for k,v in hd.iteritems():
            headers.append("%s: %s" % (k,v))
        curl.setopt(pycurl.HTTPHEADER, headers)
    else:
        curl.setopt(pycurl.HTTPHEADER, headers)
    if insecure:
        curl.setopt(pycurl.SSL_VERIFYPEER, False)
    
    if cookie_file_name:
        # Option -b/--cookie <name=string/file> Cookie string or file to read cookies from
        # Note: must be a string, not a file object.
        curl.setopt(pycurl.COOKIEFILE, cookie_file_name)
        
        # Option -c/--cookie-jar <file> Write cookies to this file after operation
        # Note: must be a string, not a file object.
        curl.setopt(pycurl.COOKIEJAR, cookie_file_name)
    
    if username and password:
        curl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_BASIC)
        if hasattr(pycurl, 'USERNAME'):
            curl.setopt(pycurl.USERNAME, username)
            curl.setopt(pycurl.PASSWORD, password)
        else:
            up = "%s:%s" % (username, password)
            curl.setopt(pycurl.USERPWD, up)
    http_status_code = None
    if debug:
        logging.debug(url)
        logging.debug(post_data)
    try:
        curl.perform()
        result = buffer.getvalue()
        buffer.close()
        if return_http_status_code:
            http_status_code = curl.getinfo(pycurl.HTTP_CODE)
        curl.close()
    except pycurl.error, e:
        logging.error("curl error occured %s" % e.args[1])
        buffer.close()
        if return_http_status_code:
            http_status_code = curl.getinfo(pycurl.HTTP_CODE)
        curl.close()
        raise e
    if return_http_status_code:
        return {"http_status_code": http_status_code, "result": result}
    else:
        return result
    
