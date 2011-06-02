import twilio
import settings

class TwilioHelper(object):
    @classmethod
    def send_sms_for_note(klass, note):
        tw = twilio.Account(settings.TWILIO_SID, settings.TWILIO_TOKEN)
        sms_params = {
            'From':settings.TWILIO_NUMBER,
            'To':settings.SHREYANS_NUMBER,
            'Body':note[0:140]
        }
        post_url = '/%s/Accounts/%s/SMS/Messages' % (settings.TWILIO_API_VERSION,
                                                     settings.TWILIO_SID)
        try:
            tw.request(post_url, 'POST', sms_params)
            return True
        except Exception, e:
            print e
            print e.read()
            return False
