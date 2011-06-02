import datetime

from model.Note import Note
from lib import geo_utils
from lib.TwilioHelper import TwilioHelper

class NoteHelper(object):
    
    @classmethod
    def add_note(klass, lat, lon, text, max_distance_in_meters=None, resend_interval=None):
        doc = {
            Note.A_LAT:float(lat),
            Note.A_LON:float(lon),
            Note.A_TEXT:text
        }
        if max_distance_in_meters:
            doc[Note.A_REQ_MAX_DISTANCE] = float(max_distance_in_meters)/1000.0
        if resend_interval:
            doc[Note.A_RESEND_INTERVAL] = resend_interval
        return Note.create_or_update_note(doc)

    @classmethod
    def get_and_send_best_note(klass):
        notes = klass.get_notes_near_current_location()
        if notes:
            note = notes[0]
            # send SMS re note
            resp = TwilioHelper.send_sms_for_note(note.get(Note.A_TEXT))
            if resp:
                note[Note.A_DT_LAST_SENT] = datetime.datetime.now()
                Note.create_or_update_note(note)

    @classmethod
    def get_notes_near_current_location(klass):
        lat, lon = geo_utils.get_current_location()
        return klass.get_notes_near_location(lat, lon)

    @classmethod
    def get_notes_near_location(klass, lat, lon, radius=None):
        notes = Note.find_notes_near_location(lat, lon, radius)
        print "found %s notes" % len(notes)
        filtered_notes = []
        for n in notes:
            print "note: %s" % n.get(Note.A_TEXT)

            append = True

            # take out inactive notes
            if append:
                if n.get(Note.A_INACTIVE):
                    append = False
                    print "inactive, skipping"

            # has the note been sent within the last day?
            if append:
                dt_last_sent = n.get(Note.A_DT_LAST_SENT)
                if dt_last_sent:
                    i = n.get(Note.A_RESEND_INTERVAL) or Note.DEFAULT_RESEND_INTERVAL
                    resend_window = datetime.datetime.now() - datetime.timedelta(hours=i)
                    if dt_last_sent > resend_window:
                        append = False
                        print "too old, skipping"

            # is the note within an acceptable distance from the current point?
            if append:
                nloc = n.get(Note.A_LOC)
                nlat = nloc[0]
                nlon = nloc[1]
                distance = geo_utils.distance_between_two_points((lat, lon), (nlat, nlon))
                print "distance is: %s" % distance
                n[Note.A_DISTANCE] = distance
                req_max_distance = n.get(Note.A_REQ_MAX_DISTANCE)
                print "max_distance is: %s" % req_max_distance
                if req_max_distance:
                    if distance > req_max_distance:
                        append = False
                        print "too far, skipping"
                
                print "append: %s" % append

            if append:
                filtered_notes.append(n)
        
        return filtered_notes

