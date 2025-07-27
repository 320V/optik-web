# urun/models.py

from django.db import models

class Kategori(models.Model):
    ad = models.CharField(max_length=100, unique=True, verbose_name="Kategori Adı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"
        ordering = ['ad']

    def __str__(self):
        return self.ad

class Urun(models.Model):
    ad = models.CharField(max_length=200, verbose_name="Ürün Adı")
    kategori = models.ForeignKey(
        Kategori,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kategori"
    )
    marka = models.CharField(max_length=100, blank=True, null=True, verbose_name="Marka")
    model_kodu = models.CharField(max_length=100, blank=True, null=True, verbose_name="Model Kodu")
    stok_adedi = models.IntegerField(default=0, verbose_name="Stok Adedi")
    alis_fiyati = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Alış Fiyatı")
    satis_fiyati = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Satış Fiyatı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    eklenme_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Eklenme Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ['ad']

    def __str__(self):
        return f"{self.ad} ({self.marka if self.marka else 'Yok'})"

class StokAyarlari(models.Model):
    # Bu model, stok bildirim eşiklerini tutar ve tek bir kayıt olmalıdır.
    dusuk_stok_esik_1 = models.PositiveIntegerField(default=20, verbose_name="Düşük Stok Eşiği (Uyarı 1 - Örn: 20)")
    dusuk_stok_esik_2 = models.PositiveIntegerField(default=50, verbose_name="Düşük Stok Eşiği (Uyarı 2 - Örn: 50)")

    class Meta:
        verbose_name = "Stok Ayarı"
        verbose_name_plural = "Stok Ayarları"

    def __str__(self):
        return "Genel Stok Ayarları"

    def save(self, *args, **kwargs):
        # Sadece tek bir StokAyarlari kaydı olmasına izin ver
        if StokAyarlari.objects.exists() and not self.pk:
            raise ValueError("Sadece bir Stok Ayarları kaydı oluşturulabilir.")
        super().save(*args, **kwargs)