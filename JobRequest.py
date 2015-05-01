__author__ = 'mshepher'
# Author: Micha Shepher  <mshepher@chellomedia.com>
#
# This File is part of the COD workflow application.
#
# Please be advised that the COD workflow application and all of its files
# are currently in development and should not be seen as a finished application.
#
# Until documentation is available please contact the author for support.


#####################################################################################
## The following is needed to initialize the Django settings file.
## This is not necessary in the django application, just in scripts.
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'testdb.settings'
## end django tailoring.
#####################################################################################

import django
import time
import xml.etree.ElementTree as ET
import ctypes
from datetime import datetime
import dicttoxml

from pycod.models import STVAssets, Client, AudioTrack

class CurrentClient(object):
    def __init__(self, client):
        self.client = client
        self.languages = AudioTrack.objects.filter(client = self.client)

    def get_lang0(self):
        return self.languages[0].preferedlang, self.languages[0].alternativelang # lang0 and lang0_1

    def get_lang1(self):
        return self.languages[1].preferedlang, self.languages[1].alternativelang # lang1 and lang1_1

    def get_channel(self):
        return self.client.channel.strip()

ctypes.windll.kernel32.SetConsoleTitleA("COD Title Query")
vers='version 0.3.6'

# TODO: remains to determine output path: In the database????
wfolder = '//10.99.16.56/d$/Scripts/Zone/encoding/'
#outdir = os.path.join(wfolder + 'Data/Request/')
outdir='C:/Users/mshepher/Develop/testdb/'

# TODO: consider adding the methods is_txid, is_lang, is_age, is_upn to client. This will decouple the property from the code.
CLIENTS_REQUIRE_TXID = ['UPC', 'UPCPOL', 'UPCHUN', 'UPCGAS','UPCCZ','UPCIE','NOVA', 'FOX', 'ASTER']
CLIENTS_REQUIRE_LANG = CLIENTS_REQUIRE_TXID + ['ZIGGO']
CLIENTS_REQUIRE_UPN =  ['BELGAC', 'BELGACOM', 'CABOVI', 'DSMART', 'FREE', 'KPN', 'NUMERI', 'ONO',
                        'OSN', 'POLSAT', 'ROMTEL', 'ROS_TELECOM', 'SFR', 'TELECO', 'TELENE',
                        'TELENET', 'TOYA', 'VECTRA', 'ZIGGO']
CLIENTS_REQUIRE_AGE = ['VECTRA']

#
# TODO: this channel mapper is not complete.
#
channeldict = { 'jim':'JimJam',
                'cbs reality':'CBSReality',
                'cbs drama': 'CBSDrama',
                'cbs action': 'CBSAction',
                'food': 'FOOD',
                'outdoor': 'OUTDOOR',
                'fine': 'FLN',
                'film': 'FILM1',
                'extreme': 'EXTREME',
                'fox': 'FoxLife'   ,
                'mgm': 'MGM'        ,
                'natgeo': 'NatGeo',
                'nat geo': 'NatGeo' ,
                'the history': 'HISTORY',
                'sundance': 'Sundance',
                'Nat Geo Poland': 'NatGeo'}

# TODO: find a neater way to do this.
def channelmapper(channel):
    channel = channel.strip()
    if channeldict.has_key(channel):
        return channeldict[channel]
    else:
        return channel

# TODO: Don't understand the need for this function.
def Strip(s):
    return s.strip()

def get_client(platform, channel):
    client  = None
    query_set = Client.objects.filter(name=platform)
    for cl in query_set:
        if cl.channel.split(':')[1] == channelmapper(channel):
            client = CurrentClient(cl)
            break # don't know what the f@#$% to do with any other clients.

    return client

class Ibms(object):
    ''' object to interface with ibms database.
    This is required to fix the timestamps.
    '''
    def __init__(self, TXiD):
        import cx_Oracle
        db_name = "ibmslive"
        db_user = "vod"
        db_pass = "vod"
        connect_string = r"{0}/{1}@{2}.chellomedia.com/{2}".format(db_user, db_pass, db_name)
        IBMSDB = cx_Oracle.connect(connect_string)
        orac = IBMSDB.cursor()
        query = orac.var(cx_Oracle.STRING)
        orac.callfunc('getIngestTCs', query, [TXiD])
        times = query.getvalue().split(',')
        self.intime  = time.strptime(times[0].split('.')[0],'%H:%M:%S')
        self.outtime = time.strptime(times[-1].split('.')[0],'%H:%M:%S')
        self.duration = self.duration()
        orac.close()

    def duration(self):
        return str(datetime(*self.outtime[:6])-datetime(*self.intime[:6]))


def alternativexml(client, Platform, row, AgeR, lang, outname):
    Lang_0, Lang_0_1 = client.get_lang0()
    Lang_1, Lang_1_1 = client.get_lang1()
    partdict = []
    d =             {'Platform':            Platform,
                     'TXiD':                Strip(row.txid),
                     'UPN':                 Strip(row.upn),
                     'Channel':             Strip(row.channel),
                     'SeriesName':          Strip(row.seriesname),
                     'ProgramName':         Strip(row.programname),
                     'OutputFileName':      Strip(row.outname),
                     'AgeRating':           str(AgeR),
                     'AspectRatio':         row.aspectratio,
                     'AudioConfiguration': 'Single',
                     "SubtitleLanguages":   row.sublang,
                     "SubtitleID":          row.subtitleid,
                     "ForcedResolution":    "",
                     "CreationDate":        time.strftime("%d/%m/%Y"),
                     "CreationTime":        time.strftime("%H:%M:%S"),
                     "ModifiedDate":        "",
                     "ModifiedTime":        "",
                     "Status":              "",
                     "parts":               partdict
                     }
    d['STV_xml'] = d
    attr = dicttoxml.make_attrstring({'TrackLanguage_0':Lang_0}) if lang else ''
    if audiotrack(row.txid, Lang_0):
        mainlang = Lang_0
    elif client.get_channel() == 'OSN:JimJam' and Lang_0 == 'ARA' \
            and not audiotrack(row.txid, Lang_0) and audiotrack(row.txid, 'CZE'):
        mainlang = 'ARA'
        alt1 = 'CZE'
    else:
        mainlang = 'ENG'

    d['TrackLanguage_0'] = '{} {}'.format(mainlang, attr)

    if audiotrack(row.txid, Lang_1):
        # Todo: this is wierd.(!) This is 100% sure wrong as hell.
        if client.get_channel() == 'OSN:JimJam' and Lang_1 == 'ARA' \
                and (not audiotrack(row.txid, Lang_1)) and audiotrack(row.txid, 'CZE'):
            print('using cze audio for OSN')
            mainlang = 'ARA'
            d['AudioConfiguration'] = 'dual'
            alt2 = 'CZE'
        elif audiotrack(row.txid, Lang_1_1):
            mainlang = Lang_1_1
            d['AudioConfiguration'] = 'dual'
        else:
            mainlang = Lang_1

        d['TrackLanguage_1'] = mainlang




# TODO: what to do with more clients?
# TODO: current implementation is for the first client in the list.
# TODO: function too long. Break up to regular and language track related??
# TODO: Replace this with dicttoxml
def xmlcreator(client, Platform, row, AgeR, lang, outname ):
    '''
    create an xml file from the query result.
    :param Platform:  platform from the client
    :param row: the query_set row to be saved
    :param AgeR: age restriction, if exists
    :param lang: 3 letter abbr for language
    :param outname:
    :return:
    '''
    alt1 = None
    alt2 = None
    root = ET.Element("STV_xml")
    Lang_0, Lang_0_1 = client.get_lang0()
    Lang_1, Lang_1_1 = client.get_lang1()
    xmldata_00 = ET.SubElement(root, "Platform")
    xmldata_00.text = Platform
    xmldata_01 = ET.SubElement(root, "TXiD")
    xmldata_01.text = Strip(row.txid)
    xmldata_02 = ET.SubElement(root, "UPN")
    xmldata_02.text = row.upn
    xmldata_03 = ET.SubElement(root, "Channel")
    xmldata_03.text = Strip(row.channel)
    xmldata_04 = ET.SubElement(root, "SeriesName")
    xmldata_04.text = row.seriesname
    xmldata_05 = ET.SubElement(root, "ProgramName")
    xmldata_05.text = row.programname
    xmldata_07 = ET.SubElement(root, "OutputFileName")
    xmldata_07.text = outname
    xmldata_15 = ET.SubElement(root, "AgeRating")
    xmldata_15.text = str(AgeR)
    xmldata_06 = ET.SubElement(root, "AspectRatio")
    xmldata_06.text = row.aspectratio
    xmldata_06 = ET.SubElement(root, "AudioConfiguration")
    xmldata_06.text = 'Single'
    # TODO: Very inefficient calling audio track so often.
    if audiotrack(row.txid, 'CZE'): # TODO: what the f!@#?
        print('cze check OK')
    if audiotrack(row.txid, Lang_0):
        xmldata_08 = ET.SubElement(root, "TrackLanguage_0")
        xmldata_08.text = Lang_0
        if lang:
            xmldata_08.attrib['OverrideLang'] = lang
    # TODO: what the f!@# is that???? This has got to be wrong somehow.
    elif client.get_channel() == 'OSN:JimJam' and Lang_0 == 'ARA' and not audiotrack(row.txid, Lang_0) and audiotrack(row.txid, 'CZE'):
        print('using cze audio for OSN')
        xmldata_08 = ET.SubElement(root, "TrackLanguage_0")
        xmldata_08.text = 'ARA'
        alt1 = 'CZE'
        if lang is not None:
            xmldata_08.attrib['OverrideLang'] = lang
    else:
        xmldata_08 = ET.SubElement(root, "TrackLanguage_0")
        xmldata_08.text = "eng"
        if lang != None:
            xmldata_08.attrib['OverrideLang'] = lang
    if audiotrack(row.txid, Lang_1):
        xmldata_09 = ET.SubElement(root, "TrackLanguage_1")
        xmldata_09.text = Lang_1
        xmldata_06.text = 'Dual'

    if audiotrack(row.txid, Lang_1):
        # Todo: this is wierd.(!) This is 100% sure wrong as hell.
        if client.get_channel() == 'OSN:JimJam' and Lang_1 == 'ARA' and (not audiotrack(row.txid, Lang_1)) and audiotrack(row.txid, 'CZE'):
            print('using cze audio for OSN')
            xmldata_09 = ET.SubElement(root, "TrackLanguage_1")
            xmldata_09.text = 'ARA'
            xmldata_06.text = 'Dual'
            alt2 = 'CZE'
        elif audiotrack(row.txid, Lang_1_1):
            xmldata_09 = ET.SubElement(root, "TrackLanguage_1")
            xmldata_09.text = Lang_1_1
            xmldata_06.text = 'Dual'
    Parts = ET.SubElement(root, "Parts")
    Parts.text = ''
    xmldata_14 = ET.SubElement(root, "SubtitleLanguages")
    xmldata_14.text = row.sublang
    xmldata_14 = ET.SubElement(root, "SubtitleID")
    xmldata_14.text = row.subtitleid
    xmldata_94 = ET.SubElement(root, "ForcedResolution")
    xmldata_94.text = ""
    xmldata_95 = ET.SubElement(root, "CreationDate")
    xmldata_95.text = time.strftime("%d/%m/%Y")
    xmldata_96 = ET.SubElement(root, "CreationTime")
    xmldata_96.text = time.strftime("%H:%M:%S")
    xmldata_97 = ET.SubElement(root, "ModifiedDate")
    xmldata_97.text = ""
    xmldata_98 = ET.SubElement(root, "ModifiedTime")
    xmldata_98.text = ""
    xmldata_99 = ET.SubElement(root, "Status")
    xmldata_99.text = ""
    # TODO: This code is probably wrong. It is a nightmare to test.
    if not row.txid.isdigit():
        cnt = 1
        Parts.append(partscheck(client, row.txid, row.upn, cnt=cnt, alt_audio1=alt1, alt_audio2=alt2))
    else:
        # TODO: This won't work if there is more than one leading zero.
        if row.txid[0] == '0':
            txstart = row.txid[0]
            txtail = int(row.txid[1:])
        else:
            txstart = ''
            txtail = int(row.txid)
        cnt = 0
        # TODO: Messy.
        while (partscheck(client, txstart + str(txtail), row.upn, cnt=str(txstart + str(txtail))[6], alt_audio1=alt1, alt_audio2=alt2)):
            Parts.append(partscheck(client, txstart + str(txtail), row.upn, alt_audio1=alt1, alt_audio2=alt2))
            txtail += 10
            cnt += 1
    Parts.text = str(cnt)
    tree = ET.ElementTree(root)
    print 'dumping file {}{}_{}(date).xml'.format(outdir, row.upn, Platform)
    tree.write(outdir + row.upn + '_' + Platform + '_' + time.strftime("%d%m%Y_%H%M%S") + ".xml")
    return True

# TODO: There could be more tracks of a specific language associated with this txid.

def audiotrack(TX, Lang):
    query_set = STVAssets.objects.filter(txid= TX, tracklanguage = Lang)
    if len(query_set) > 0:
        return Strip(query_set[0].tracknumber)
    else:
        return ''

def partscheckalt(client, TX, UPN, cnt=1, alt_audio1=None, alt_audio2=None):
    '''identical, but builds a dict instead.'''
    Lang_0, Lang_0_1 = client.get_lang0()
    Lang_1, Lang_1_1 = client.get_lang1()

    query_set = STVAssets.objects.filter(txid= TX, upn = UPN)
    for row in query_set:
        d = {
            'TXiD':         Strip(row.txid),
            'STV_SOM':      Strip(row.stv_som),
            '': ''
        }
def partscheck(client, TX, UPN, cnt=1, alt_audio1=None, alt_audio2=None):
    part = 'Part_' + str(cnt)

    Lang_0, Lang_0_1 = client.get_lang0()
    Lang_1, Lang_1_1 = client.get_lang1()
    query_set = STVAssets.objects.filter(txid= TX, upn = UPN)
    for row in query_set:
        print('part found: {0}'.format(row.txid))
        if not None:
            root = ET.Element(part)
            xmldata_01 = ET.SubElement(root, "TXiD")
            xmldata_01.text = Strip(row.txid)
            xmldata_04 = ET.SubElement(root, "STV_SOM")
            xmldata_04.text = Strip(row.stv_som)
            ibms = Ibms(Strip(row.txid))
            xmldata_05 = ET.SubElement(root, "IBMS_SOM")
            ibms.intime = time.strftime('%H:%M:%S', ibms.intime)+'.00'
            print '%%%%'+ibms.intime
            if ibms.intime == '00:00:00.00':
                xmldata_05.text = Strip(row.ibms_som)
            else:
                xmldata_05.text = ibms.intime
            xmldata_06 = ET.SubElement(root, "IBMS_DUR")
            xmldata_06.text = ibms.duration
            xmldata_02 = ET.SubElement(root, "TrackNumber_0")
            # TODO: alt_audio can never be ''!.
            if not alt_audio1 or alt_audio1 == '':
                A1 = Lang_0
            else:
                A1 = alt_audio1
            if not alt_audio2 or alt_audio2 == '':
                A2 = Lang_1
            else:
                A2 = alt_audio2
            # TODO: Huh??!
            if audiotrack(TX, A1) != '' and audiotrack(TX, A1) is not None:
                xmldata_02.text = audiotrack(TX, A1)
            else:
                xmldata_02.text = audiotrack(TX, Lang_0)
            if audiotrack(TX, A2) is not None:
                xmldata_03 = ET.SubElement(root, "TrackNumber_1")
                xmldata_03.text = audiotrack(TX, A2)
            elif audiotrack(TX, A2) is None:
                if not audiotrack(TX, Lang_1_1) is None:
                    xmldata_03 = ET.SubElement(root, "TrackNumber_1")
                    xmldata_03.text = audiotrack(TX, Lang_1_1)
            return root

# TODO: if not AgeR logic is faulty. AgeR is never None.
# TODO: typical unreachable code case.
# TODO: special case for FILM1 seems futile.
def UPNretrieve(id, platform, AgeR=0, lang=None):
    '''
    :param id: txid 8 digit magic code
    :param platform: from client database. Used only in the output
    :param AgeR: Age restriction, in current version not used.
    :param lang: language 3 letter spec
    :return: xml record from SQLreader.
    '''
    query_set = STVAssets.objects.filter(txid = id)
    for upnfind in query_set:
        # print '!{}'.format(upnfind)
        chan = channelmapper(upnfind.channel)
        if not lang:
          if AgeR > 0:
              if chan == 'FILM1':
                  SQLreader(upnfind.upn, 'ZIGGO')
              return SQLreader(upnfind.upn, platform)
          else:
              if chan == 'FILM1':
                  SQLreader(upnfind.upn, 'ZIGGO', AgeR=AgeR)
              return SQLreader(upnfind.upn, platform, AgeR=AgeR)
        else:
          if AgeR > 0:
              if chan == 'FILM1':
                  SQLreader(upnfind.upn, 'ZIGGO', lang=lang)
              return SQLreader(upnfind.upn, platform, lang=lang)
          else:
              if chan == 'FILM1':
                  SQLreader(upnfind.upn, 'ZIGGO', lang=lang, AgeR=AgeR)
              return SQLreader(upnfind.upn, platform, lang=lang, AgeR=AgeR)



# TODO: why the underscore split?
def SQLreader(id, platform, AgeR=0, lang=None, outname=None):
    '''
    :param id: upn to select
    :param platform: platform (from client)
    :param AgeR: age restriction, not used in this version
    :param lang: language 3 letter abbreviation
    :param outname:
    :return:
    '''
    id = id.split('_')[0]
    print 'SQLreader query on upn={}'.format(id)
    # raw_input()
    query_set = STVAssets.objects.filter(upn=id)
    for row in query_set:
        print Strip(row.channel)
        client = get_client(platform, row.channel)
        if client:
            return xmlcreator(client, platform, row, AgeR, lang, outname )
        else:
            return False

def main():
    query_set = Client.objects.all()
    clients = [x.name for x in query_set]
    clients = sorted(list( set( clients )))
    for num, c in enumerate(clients):
        print '{:>2} : {}'.format(num, c)
    platnum = raw_input("Please enter platform number: ")
    plat = clients[int(platnum)]
    while True:

        if  plat in CLIENTS_REQUIRE_UPN:
            txid = raw_input("enter UPN: ")
        else:
            if plat in CLIENTS_REQUIRE_TXID:
                txid = raw_input("enter TXiD: ")
            else:
                print 'The entered platform seems incorrect!\nPlease re-enter'
                main()
        if  len(txid) > 5:
            if plat in  CLIENTS_REQUIRE_AGE:
                try:
                    AgeR=raw_input("enter Age Rating (if applicable): ")
                except:
                    AgeR=0
                print SQLreader(txid, plat, AgeR)
            elif plat in CLIENTS_REQUIRE_LANG:
                try:
                    lang=raw_input("enter language descriptor: ")
                except:
                    lang = None
                print UPNretrieve(txid, plat, lang=lang)
                if plat == 'UPCPOL': # TODO: looks suspicious
                    print UPNretrieve(txid, 'ASTER', lang=lang)
            else:
                print SQLreader(txid, plat)
        else:
            if txid == "":
                txid = "nothing"
                print "you entered %s; this is to short to be a valid TXID.\nPlease enter a valid TXID!" % txid

if __name__ == "__main__":
    # if this does not work, check the (relative) location of settings.py
    django.setup()
    print 'Use the keyboard combination Ctrl-C to restart the application.'
    try:
        main()
    except KeyboardInterrupt:
        time.sleep(1)
        main()
