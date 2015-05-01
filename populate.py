__author__ = 'mshepher'
#####################################################################################
##
##  Project COD scripting
##  initial populate database
##
#####################################################################################

#####################################################################################
## The following is needed to initialize the Django settings file.
## This is not necessary in the django application, just in scripts.
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'testdb.settings'
## end django tailoring.
#####################################################################################

from pycod.models import STVAssets, Part, Track, Client, LogoProfile, Subtitle, AudioTrack
import xmltodict as x2d
import re
import django
import collections
import traceback


#####################################################################################
#
#####################################################################################
class Populate(object):

    #-----------------------
    def __init__(self):

        self.pat = re.compile('track(\d+)')

    #-----------------------
    def populate_logo(self, name, client, logo):
        name     = 'Logo-{}'.format(name)

        required = False
        position = 'LEFT'
        size = '0'
        sizeHD = '0'
        offset ='0'
        offsetHD='0'
        alternativeHD = ''
        logofile = ''
        if logo.has_key('@required'):
            required = logo['@required']
        if logo.has_key('@position'):
            position = logo['@position']
        if logo.has_key('@size'):
            size = logo['@size']
        if logo.has_key('@offset'):
            offset   = logo['@offset']
        if logo.has_key('@sizeHD'):
            sizeHD   = logo['@sizeHD']
        if logo.has_key('@offsetHD'):
            offsetHD = logo['@offsetHD']
        if logo.has_key('@alternativeHD'):
            alternativeHD = logo['@alternativeHD']
        if logo.has_key('#text'):
            text = logo['#text']
            if text in ['False', 'True']:
                logofile = 'FixMeAgeRating-{}'.format(name)
            else:
                logofile = logo['#text']

        if LogoProfile.objects.filter(name=name).exists():
            l =  LogoProfile.objects.get(name=name)
        else:
            l = LogoProfile()

        l.name=name
        l.required = required
        l.position = position.upper()
        l.size     = size
        l.offset   = offset
        l.sizeHD   = sizeHD
        l.offsetHD = offsetHD
        l.alternativeHD = alternativeHD
        l.logofile = logofile

        try:
            l.save()
        except ValueError:
            print 'ERROR SAVING ', l.name, l.position,  l.required, l.size, l.offset, l.sizeHD, l.offsetHD, l.alternativeHD, l.logofile
            l.offset,l.size,l.offsetHD,l.sizeHD=('0.0',)*4
            l.save()

        return l

    #-----------------------
    def populate_track(self, client, track, number):
        '''populate a client audio track if possible.'''
        altkey = 'track{}_1'.format(number)
        if track.has_key(altkey):
            _alternativelang = track[altkey]
            if _alternativelang and type(_alternativelang) != type(u'micha'):
                _alternativelang = _alternativelang['#text']
        else:
            _alternativelang = ''
        if track.has_key('#text'):
            _preferedlang = track['#text']
        else:
            _preferedlang = 'notext'
        if track.has_key('@format'):
            _type = track['@format']
        else:
            _type = 'Stereo'
        t = AudioTrack(client = client,
                       preferedlang = _preferedlang,
                       alternativelang = _alternativelang,
                       type = _type)
        try:
            t.save()
        except:
            print 'cannot saved malformed track: {} {} {} {}'.format(client, _preferedlang, _alternativelang, _type)

    #-----------------------
    def populate_subtitles(self, client, subtitles):
        if Subtitle.objects.filter(client=client).exists():
            s = Subtitle.objects.get(client=client)
        else:
            s = Subtitle(client=client)

        if subtitles.has_key('@required'):
            _required =  subtitles['@required'] == u'True'
        else:
            _required = False

        if subtitles.has_key('#text'):
            _type = subtitles['#text']
        else:
            _type = 'PAC'

        _lang = ''
        for i in range(4):
            sub = 'subtitle_{}'.format(i)
            if subtitles.has_key(sub):
                if subtitles[sub].has_key('#text'):
                    _lang += (subtitles[sub]['#text'] + ':')

        if len(_lang) > 0 and _lang[-1] == ':':
            _lang = _lang[:-1]

        s.lang = _lang
        s.type = _type

        try:
            s.save()
        except:
            print 'cannot save subtitle for client {}'.format(client)

    #-----------------------

    def populate_parts(self):
        '''
        get all parts of a specific title and save them.
        '''
        Part.objects.all().delete()
        for asset in STVAssets.objects.all():
            subpart = asset.txid[:-2]
            if STVAssets.objects.filter(txid__startswith = subpart).count() > 1:
                print 'part {} found.'.format(asset.txid)
                partset = STVAssets.objects.filter(txid__startswith = subpart)
                txids = {}
                for part in partset:
                    if txids.has_key(part.txid):
                        txids[part.txid] += 1
                    else:
                        txids[part.txid] = 1
                if len(txids) > 1:
                    for key in txids.keys():
                        print 'trying to save part {} {}'.format(key, part.programname)
                        p = Part( stvassetid = part, partnumber = part.txid, timepatched = False,
                                  ibms_som = part.som, ibms_eom = part.eom, ibms_duration = part.ibms_duration)
                        p.save()
                        print 'part {} saved.'.format(part)
                else:
                    print '.',
            else:
                print '-',

    def populate_client(self, name, channel, client):


        # query_set = STVAssets.objects.filter(client = name)
        # print len(query_set)
        _name = name
        _channel = '{}:{}'.format(name,channel)

        if Client.objects.filter(name=_name, channel=_channel).exists():
            c = Client.objects.get(name=_name, channel=_channel)
        else:
            c = Client(name = _name,
                       channel = _channel)
        _namingconvention = client['namingconvention']
        _format = client['format']['#text']
        _hdprofile = client['HDprofile']
        _sdprofile = client['SDprofile']
        _logo = self.populate_logo(_channel, client, client['Logo']) # creates the LogoProfile if necessary
        _agerating = self.populate_logo('{}-age rating'.format(_channel), client, client['AgeRating'])
        _dualaudio = client['dualaudio']['#text'] == u'True'
        _bumperfront = client['Bumper']['@front']
        _bumperback = client['Bumper']['@back']

        c.namingconvention = _namingconvention
        c.format = _format
        c.HDprofile = _hdprofile
        c.SDprofile = _sdprofile
        c.Logo = _logo
        c.AgeRating = _agerating
        c.dualaudio = _dualaudio
        c.BumperBack = _bumperback
        c.BumperFront = _bumperfront

        c.save()

        for track in client.keys(): # trap all track fields of the client.
            match = self.pat.match(track)
            if match:
                self.populate_track(c, client[track], match.group(1))

        self.populate_subtitles(c, client['subtitles'])

        return True

def start():
    clientfilename = 'client.conf'
    clients = x2d.parse(file(clientfilename, 'r').read())['ClientConfigurations']
    Client.objects.all().delete()
    LogoProfile.objects.all().delete()
    AudioTrack.objects.all().delete()
    popu = Populate()
    for name in clients.keys():
        print name
        for channel in clients[name]:
            if popu.populate_client(name, channel, clients[name][channel]):
                print 'succesfully saving client {}:{}.'.format(name,channel)


#####################################################################################
#
#####################################################################################
if __name__ == '__main__':


    django.setup()
    # populate_clients()
    Populate().populate_parts()

