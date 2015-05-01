from django.db import models
from pycountry import languages

def lang_choices():
    '''return the iso 639 language list'''
    tup = []
    for lang in languages:
        if hasattr(lang, 'terminology'):
            tup.append((lang.terminology, lang.terminology.upper()))

    return tuple(tup)

class STVAssets(models.Model):
    '''this table resides on the external SQL server. This must not be changed!
       No save actions are allowed here.
    '''
    stvassetsid = models.AutoField(db_column='STVAssetsID', primary_key=True)  # Field name made lowercase.
    txid        = models.CharField(db_column='TxID', max_length=50, blank=True, null=True)  # Field name made lowercase.
    location    = models.CharField(db_column='Location', max_length=50, blank=True, null=True)  # Field name made lowercase.
    channel     = models.CharField(db_column='Channel', max_length=50, blank=True, null=True)  # Field name made lowercase.
    seriesname  = models.CharField(db_column='SeriesName', max_length=100, blank=True, null=True)  # Field name made lowercase.
    programname = models.CharField(db_column='ProgramName', max_length=100, blank=True, null=True)  # Field name made lowercase.
    subtitleid  = models.CharField(db_column='SubtitleID', max_length=100, blank=True, null=True)  # Field name made lowercase.
    sublang     = models.CharField(db_column='SubLang', max_length=100, blank=True, null=True)  # Field name made lowercase.
    upn         = models.CharField(db_column='UPN', max_length=50, blank=True, null=True)  # Field name made lowercase.
    aspectratio = models.CharField(db_column='AspectRatio', max_length=50, blank=True, null=True)  # Field name made lowercase.
    tracktype   = models.CharField(db_column='TrackType', max_length=50, blank=True, null=True)  # Field name made lowercase.
    tracknumber = models.CharField(db_column='TrackNumber', max_length=50, blank=True, null=True)  # Field name made lowercase.
    tracklanguage = models.CharField(db_column='TrackLanguage', max_length=50, blank=True, null=True)  # Field name made lowercase.
    trackstatus = models.CharField(db_column='TrackStatus', max_length=50, blank=True, null=True)  # Field name made lowercase.
    stv_som     = models.CharField(db_column='STV_SOM', max_length=50, blank=True, null=True)  # Field name made lowercase.
    stv_eom     = models.CharField(db_column='STV_EOM', max_length=50, blank=True, null=True)  # Field name made lowercase.
    stv_duration = models.CharField(db_column='STV_Duration', max_length=50, blank=True, null=True)  # Field name made lowercase.
    ibms_som    = models.CharField(db_column='IBMS_SOM', max_length=50, blank=True, null=True)  # Field name made lowercase.
    ibms_eom    = models.CharField(db_column='IBMS_EOM', max_length=50, blank=True, null=True)  # Field name made lowercase.
    ibms_duration = models.CharField(db_column='IBMS_Duration', max_length=50, blank=True, null=True)  # Field name made lowercase.

    def __unicode__(self):
        return u'{}: {}-{}'.format(self.channel, self.seriesname, self.programname)

    class Meta:
        '''refers to an original table.'''
        managed = False
        db_table = 'STVAssets'

class Part(models.Model):
    '''A part of an asset is optionally used when the asset is too long and must be broken to parts.
    The times in this part must be patched from the data in STV repository.
    When this is done, timepatched is set to true.
    '''
    stvassetid  = models.ForeignKey('STVAssets')
    partnumber  = models.CharField( max_length = 50, primary_key = True, null = False, default='-1')
    timepatched = models.BooleanField(default=False)
    ibms_som    = models.CharField( max_length=50, blank=True, null=True)
    ibms_eom    = models.CharField( max_length=50, blank=True, null=True)
    ibms_duration = models.CharField( max_length=50, blank=True, null=True)
#
    def __unicode__(self):
        return u'{}: {}'.format(self.partnumber, self.ibms_duration)
#
class Track(models.Model):
    '''each asset may have one or more lang related audio tracks.
    '''
    stvassetid = models.ForeignKey('STVAssets')
    partnumber  = models.CharField( max_length = 50, primary_key = True, null = False, default='-1')
    timepatched = models.BooleanField(default=False)
    tracknumber = models.IntegerField()
    lang   = models.CharField(max_length=10, choices=lang_choices())
#
    def __unicode__(self):
        return u'{}: {}-{}'.format(self.partnumber, self.tracknumber, self.lang)

class LogoProfile(models.Model):
    '''Logo determines the properties of a logo displayed (or not). This is a profile relation (one to one).'''
    POS_CHOICES = (('LEFT', 'LEFT'),
                   ('RIGHT','RIGHT'))
    name = models.CharField(max_length=50)
    required = models.BooleanField(default = False)
    position = models.CharField(max_length=10, choices=POS_CHOICES)
    size     = models.DecimalField(max_digits=15, decimal_places=2)
    offset   = models.DecimalField(max_digits=15, decimal_places=2)
    sizeHD   = models.DecimalField(max_digits=15, decimal_places=2)
    offsetHD = models.DecimalField(max_digits=15, decimal_places=2)
    alternativeHD = models.CharField(max_length=50)
    logofile = models.CharField(max_length=50)

    def __unicode__(self):
        return u'{}'.format(self.name)

class Client(models.Model):
    '''a client is actually a client-channel join. For convenience we call this simply Client.'''
    FORMAT_CHOICES = (('SD','SD'),
                      ('HD','HD'),)
    name      = models.CharField(max_length=50)
    channel   = models.CharField(max_length=50)
    territory = models.CharField(max_length=50, blank=True, null=True)
    namingconvention    = models.CharField(max_length=20)
    format              = models.CharField(max_length=20,choices=FORMAT_CHOICES)
    HDprofile           = models.CharField(max_length=20, blank=True, null=True)
    SDprofile           = models.CharField(max_length=20, blank=True, null=True)
    Logo                = models.ForeignKey('LogoProfile')
    AgeRating           = models.BooleanField()
    dualaudio           = models.BooleanField()
    BumperFront         = models.CharField(max_length=20, blank=True, null=True)
    BumperBack          = models.CharField(max_length=20, blank=True, null=True)

    def __unicode__(self):
        return u'{}'.format(self.channel)

class Subtitle(models.Model):
    '''subtitle are the channel's subtitle rules. This is typically a client profile table.'''
    SUB_CHOICES = (('BURNIN','BURNIN'),
                   ('PAC','PAC'),
                   ('BVB','BVB'))
    client = models.ForeignKey('Client')
    lang   = models.CharField(max_length=10, choices=lang_choices())
    type   = models.CharField(max_length=10, choices=SUB_CHOICES)

    def __unicode__(self):
        return u'{}-{}'.format(self.client,self.lang)

class AudioTrack(models.Model):
    '''Audio are the channel's Audio rules. This is typically a client profile table.'''
    AUDIO_CHOICES =(('Stereo','Stereo'),
                    ('Surround', 'Surround'))

    client = models.ForeignKey('Client')
    preferedlang    = models.CharField(max_length=10, choices=lang_choices(), null=True)
    alternativelang = models.CharField(max_length=10, choices=lang_choices(), null=True)
    type   = models.CharField(max_length=10, choices=AUDIO_CHOICES, null=True)

    def __unicode__(self):
        return u'{}-{}'.format(self.client,self.preferedlang)
