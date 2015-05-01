from django.contrib import admin

from .models import STVAssets, Part, Client, LogoProfile, Subtitle, AudioTrack

admin.site.register((Client, Part, LogoProfile, Subtitle, AudioTrack))

@admin.register(STVAssets)
class STVAssetsAdmin(admin.ModelAdmin):
    list_filter = ('channel',)
    search_fields = ('txid', 'upn')
# Register your models here.
