from django.contrib import admin

from .models import STVAssets, Part, Track, Client, LogoProfile, Subtitle, AudioTrack

admin.site.register((Part, Track, Client, LogoProfile, Subtitle, AudioTrack))

@admin.register(STVAssets)
class STVAssetsAdmin(admin.ModelAdmin):
    list_filter = ('location', 'channel', 'seriesname', 'programname', 'stv_duration')
    search_fields = ('location', 'channel', 'seriesname', 'programname')
# Register your models here.
