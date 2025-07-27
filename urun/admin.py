# urun/admin.py

from django.contrib import admin
from django.utils.html import format_html # format_html'i import edin
from .models import Kategori, Urun, StokAyarlari

@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ('ad', 'aciklama')
    search_fields = ('ad',)

@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ('ad', 'kategori', 'marka', 'stok_adedi', 'satis_fiyati', 'eklenme_tarihi', 'stok_bildirimleri')
    list_filter = ('kategori', 'marka', 'eklenme_tarihi')
    search_fields = ('ad', 'marka', 'model_kodu', 'aciklama')
    ordering = ('ad',)
    readonly_fields = ('eklenme_tarihi', 'guncelleme_tarihi')
    fieldsets = (
        (None, {
            'fields': ('ad', 'kategori', 'marka', 'model_kodu', 'aciklama')
        }),
        ('Fiyat ve Stok Bilgileri', {
            'fields': ('stok_adedi', 'alis_fiyati', 'satis_fiyati')
        }),
        ('Tarih Bilgileri', {
            'fields': ('eklenme_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',),
        }),
    )

    def stok_bildirimleri(self, obj):
        stok_ayarlari = StokAyarlari.objects.first()
        if not stok_ayarlari:
            return "Ayarlar Tanımlanmamış"

        esik_1 = stok_ayarlari.dusuk_stok_esik_1
        esik_2 = stok_ayarlari.dusuk_stok_esik_2

        if obj.stok_adedi == 0:
            return format_html("<strong><span style='color: red;'>Stokta Yok!</span></strong>")
        elif obj.stok_adedi < esik_1:
            return format_html(f"<span style='color: orange;'>Stok Kritik</span>")
        elif obj.stok_adedi < esik_2:
            return format_html(f"<span style='color: blue;'>Stok Az</span>")
        else:
            return ""
    stok_bildirimleri.short_description = "Bildirimler"
    # allow_tags artık format_html kullanıldığı için gerekli değil ama zararı da yok.
    # Yine de güvenlik için format_html kullanmak daha iyidir.
    # stok_bildirimleri.allow_tags = True

@admin.register(StokAyarlari)
class StokAyarlariAdmin(admin.ModelAdmin):
    list_display = ('dusuk_stok_esik_1', 'dusuk_stok_esik_2')
    def has_add_permission(self, request):
        return not StokAyarlari.objects.exists()

    def changelist_view(self, request, extra_context=None):
        if StokAyarlari.objects.count() == 1:
            obj = StokAyarlari.objects.first()
            return self.change_view(request, str(obj.pk))
        return super().changelist_view(request, extra_context)