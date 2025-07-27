# siparis/admin.py

from django.contrib import admin
from .models import Siparis, Odeme

class OdemeInline(admin.TabularInline):
    # Bu sınıf, Sipariş detay sayfasında ödemeleri doğrudan eklemeye/görmeye yarar
    model = Odeme
    extra = 1 # Varsayılan olarak 1 boş satır gösterir
    fields = ('miktar', 'odeme_sekli', 'odeme_tarihi', 'notlar')
    readonly_fields = ('odeme_tarihi',) # Ödeme tarihini sadece okunur yapar
    can_delete = True # Ödemelerin silinmesine izin verir

@admin.register(Siparis)
class SiparisAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'musteri_adi_soyadi',
        'siparis_tarihi',
        'toplam_tutar',
        'odenen_toplam_tutar', # Dinamik olarak hesaplanan ödenen tutar
        'alinacak_tutar',
        'durum',
        'teslimat_tarihi_formatted'
    )
    list_filter = ('durum', 'siparis_tarihi', 'teslimat_tarihi')
    search_fields = ('musteri__ad', 'musteri__soyad', 'notlar')
    date_hierarchy = 'siparis_tarihi'
    ordering = ('-siparis_tarihi',)
    inlines = [OdemeInline] # Ödeme kayıtlarını Sipariş detayında gösterir

    fieldsets = (
        (None, {
            'fields': ('musteri', 'toplam_tutar', 'durum', 'notlar', 'teslimat_tarihi')
        }),
        ('Ödeme Durumu', {
            'fields': ('odenen_toplam_tutar', 'alinacak_tutar'), # Artık 'odenmis_tutar' yerine bu property'ler var
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('siparis_tarihi', 'odenen_toplam_tutar', 'alinacak_tutar')

    def musteri_adi_soyadi(self, obj):
        if obj.musteri:
            return f"{obj.musteri.ad} {obj.musteri.soyad}"
        return "Belirtilmemiş"
    musteri_adi_soyadi.short_description = "Müşteri"

    def odenen_toplam_tutar(self, obj):
        return obj.odenen_toplam_tutar
    odenen_toplam_tutar.short_description = "Ödenen Toplam Tutar"
    odenen_toplam_tutar.admin_order_field = 'odenen_toplam_tutar' # Sıralama için

    def alinacak_tutar(self, obj):
        return obj.alinacak_tutar
    alinacak_tutar.short_description = "Alınacak Tutar"
    alinacak_tutar.admin_order_field = 'alinacak_tutar' # Sıralama için

    def teslimat_tarihi_formatted(self, obj):
        return obj.teslimat_tarihi.strftime('%Y-%m-%d') if obj.teslimat_tarihi else 'Belirtilmemiş'
    teslimat_tarihi_formatted.short_description = "Teslimat Tarihi"