# giderler/admin.py

from django.contrib import admin
from .models import GiderKategorisi, Gider

@admin.register(GiderKategorisi)
class GiderKategorisiAdmin(admin.ModelAdmin):
    list_display = ('ad', 'aciklama')
    search_fields = ('ad',)
    ordering = ('ad',)

@admin.register(Gider)
class GiderAdmin(admin.ModelAdmin):
    list_display = (
        'kategori',
        'miktar',
        'gider_tarihi',
        'kullanicilar_display', # Hangi kullanıcılar için harcandığını gösterecek
        'notlar'
    )
    list_filter = ('kategori', 'gider_tarihi', 'harcanan_kullanicilar')
    search_fields = ('notlar', 'kategori__ad')
    date_hierarchy = 'gider_tarihi'
    ordering = ('-gider_tarihi',)
    filter_horizontal = ('harcanan_kullanicilar',) # ManyToMany alanı için güzel bir arayüz sağlar

    fieldsets = (
        (None, {
            'fields': ('kategori', 'miktar', 'notlar', 'harcanan_kullanicilar')
        }),
    )
    readonly_fields = ('gider_tarihi',)

    def kullanicilar_display(self, obj):
        # İlgili kullanıcıları virgülle ayrılmış bir string olarak göster
        return ", ".join([user.get_full_name() or user.username for user in obj.harcanan_kullanicilar.all()])
    kullanicilar_display.short_description = "İlgili Kullanıcılar"