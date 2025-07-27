# musteri/models.py

from django.db import models

class Musteri(models.Model):
    ad = models.CharField(max_length=100, verbose_name="Adı")
    soyad = models.CharField(max_length=100, verbose_name="Soyadı")
    telefon = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    eposta = models.EmailField(blank=True, null=True, verbose_name="E-posta")
    dogum_tarihi = models.DateField(blank=True, null=True, verbose_name="Doğum Tarihi")
    adres = models.TextField(blank=True, null=True, verbose_name="Adres")
    notlar = models.TextField(blank=True, null=True, verbose_name="Notlar")
    kayit_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")

    class Meta:
        verbose_name = "Müşteri"
        verbose_name_plural = "Müşteriler"
        ordering = ['-kayit_tarihi'] # En yeni müşteriyi en üstte göster

    def __str__(self):
        return f"{self.ad} {self.soyad}"