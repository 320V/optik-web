# giderler/models.py

from django.db import models
from django.conf import settings # Django'nun User modeline erişmek için

class GiderKategorisi(models.Model):
    ad = models.CharField(max_length=100, unique=True, verbose_name="Gider Kategorisi Adı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")

    class Meta:
        verbose_name = "Gider Kategorisi"
        verbose_name_plural = "Gider Kategorileri"
        ordering = ['ad']

    def __str__(self):
        return self.ad

class Gider(models.Model):
    kategori = models.ForeignKey(
        GiderKategorisi,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Gider Kategorisi"
    )
    miktar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tutar")
    gider_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Gider Tarihi")
    notlar = models.TextField(blank=True, null=True, verbose_name="Notlar")
    # Hangi kullanıcılar için harcandı (tekil veya çoğul olabilir)
    # settings.AUTH_USER_MODEL, projenin User modelini dinamik olarak referans alır.
    harcanan_kullanicilar = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True, # Zorunlu değil
        verbose_name="Harcayan Kullanıcı(lar)",
        related_name="giderler" # User modelinden giderlere erişim için
    )

    class Meta:
        verbose_name = "Gider"
        verbose_name_plural = "Giderler"
        ordering = ['-gider_tarihi'] # En yeni gideri en üstte göster

    def __str__(self):
        return f"{self.kategori.ad if self.kategori else 'Genel Gider'} - {self.miktar} TL ({self.gider_tarihi.strftime('%Y-%m-%d')})"