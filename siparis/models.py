# siparis/models.py

from django.db import models
from musteri.models import Musteri

class Siparis(models.Model):
    musteri = models.ForeignKey(
        Musteri,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Müşteri"
    )
    siparis_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Sipariş Tarihi")
    toplam_tutar = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Toplam Tutar")
    # 'odenmis_tutar' artık dinamik olarak Odeme modelinden hesaplanacak,
    # ancak kolaylık için manuel güncellenebilir bir alan olarak da tutulabilir.
    # Şimdilik Otomatik hesaplama için kaldırıyoruz.
    # odenmis_tutar = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Ödenen Tutar")

    SIPARIS_DURUM_SECENEKLERI = [
        ('Beklemede', 'Beklemede (Ödeme Bekleniyor)'),
        ('Onaylandı', 'Onaylandı (Üretim/Hazırlık Aşamasında)'),
        ('Hazır', 'Hazır (Teslimata Hazır)'),
        ('Teslim Edildi', 'Teslim Edildi'),
        ('İptal Edildi', 'İptal Edildi'),
    ]
    durum = models.CharField(
        max_length=50,
        choices=SIPARIS_DURUM_SECENEKLERI,
        default='Beklemede',
        verbose_name="Durum"
    )
    notlar = models.TextField(blank=True, null=True, verbose_name="Notlar")
    teslimat_tarihi = models.DateField(blank=True, null=True, verbose_name="Tahmini/Gerçek Teslimat Tarihi")

    class Meta:
        verbose_name = "Sipariş"
        verbose_name_plural = "Siparişler"
        ordering = ['-siparis_tarihi']

    def __str__(self):
        return f"Sipariş #{self.id} - {self.musteri.ad if self.musteri else 'Belirtilmemiş Müşteri'}"

    @property
    def odenen_toplam_tutar(self):
        # Bu siparişe yapılan tüm ödemelerin toplamını dinamik olarak hesaplar
        return self.odemeler.aggregate(models.Sum('miktar'))['miktar__sum'] or models.Decimal('0.00')

    @property
    def alinacak_tutar(self):
        # Toplam tutardan ödenen toplam tutarı çıkarır
        return self.toplam_tutar - self.odenen_toplam_tutar

class Odeme(models.Model):
    siparis = models.ForeignKey(
        Siparis,
        on_delete=models.CASCADE,
        related_name='odemeler', # Siparişten ödemelere erişim için kullanılacak isim
        verbose_name="İlgili Sipariş"
    )
    miktar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ödenen Miktar")
    odeme_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Ödeme Tarihi")
    odeme_sekli = models.CharField(
        max_length=50,
        choices=[
            ('Nakit', 'Nakit'),
            ('Kredi Kartı', 'Kredi Kartı'),
            ('Havale/EFT', 'Havale/EFT'),
            ('Diğer', 'Diğer'),
        ],
        default='Nakit',
        verbose_name="Ödeme Şekli"
    )
    notlar = models.TextField(blank=True, null=True, verbose_name="Ödeme Notu")

    class Meta:
        verbose_name = "Ödeme"
        verbose_name_plural = "Ödemeler"
        ordering = ['-odeme_tarihi']

    def __str__(self):
        return f"Sipariş #{self.siparis.id} için {self.miktar} TL ödeme ({self.odeme_tarihi.strftime('%Y-%m-%d %H:%M')})"