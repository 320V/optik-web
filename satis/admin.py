# satis/admin.py

from django.contrib import admin
from .models import Satis, SatisUrun, SatisOdeme
from django.db.models import Sum, F

class SatisUrunInline(admin.TabularInline):
    model = SatisUrun
    extra = 1
    fields = ('urun', 'adet', 'birim_fiyat', 'toplam_urun_fiyati')
    readonly_fields = ('birim_fiyat', 'toplam_urun_fiyati',)
    can_delete = True
    verbose_name_plural = "Ürünler" # Burası güncellendi

class SatisOdemeInline(admin.TabularInline):
    model = SatisOdeme
    extra = 1
    fields = ('miktar', 'odeme_sekli', 'odeme_tarihi', 'notlar')
    readonly_fields = ('odeme_tarihi',)
    can_delete = True
    verbose_name_plural = "Ödemeler" # Burası güncellendi

@admin.register(Satis)
class SatisAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'musteri_adi_soyadi',
        'satis_tarihi',
        'hesaplanan_toplam_tutar_display',
        'odenen_toplam_tutar_display',
        'alinacak_tutar_display',
        'odeme_sekli'
    )
    list_filter = ('satis_tarihi', 'odeme_sekli')
    search_fields = ('musteri__ad', 'musteri__soyad', 'notlar')
    date_hierarchy = 'satis_tarihi'
    ordering = ('-satis_tarihi',)
    inlines = [SatisUrunInline, SatisOdemeInline]

    fieldsets = (
        ("Satış Bilgileri", {
            'fields': (
                'musteri',
                'odeme_sekli',
                'notlar',
                'hesaplanan_toplam_tutar_display',
                'odenen_toplam_tutar_display',
                'alinacak_tutar_display',
            )
        }),
    )

    readonly_fields = (
        'satis_tarihi',
        'hesaplanan_toplam_tutar_display',
        'odenen_toplam_tutar_display',
        'alinacak_tutar_display'
    )

    def musteri_adi_soyadi(self, obj):
        if obj.musteri:
            return f"{obj.musteri.ad} {obj.musteri.soyad}"
        return "Belirtilmemiş"
    musteri_adi_soyadi.short_description = "Müşteri"

    def hesaplanan_toplam_tutar_display(self, obj):
        return obj.hesaplanan_toplam_tutar
    hesaplanan_toplam_tutar_display.short_description = "Toplam Tutar"
    hesaplanan_toplam_tutar_display.admin_order_field = 'hesaplanan_toplam_tutar'

    def odenen_toplam_tutar_display(self, obj):
        return obj.odenen_toplam_tutar
    odenen_toplam_tutar_display.short_description = "Ödenen Toplam Tutar"
    odenen_toplam_tutar_display.admin_order_field = 'odenen_toplam_tutar'

    def alinacak_tutar_display(self, obj):
        return obj.alinacak_tutar
    alinacak_tutar_display.short_description = "Alınacak Tutar"
    alinacak_tutar_display.admin_order_field = 'alinacak_tutar'