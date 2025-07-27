# satis/models.py

from django.db import models
from musteri.models import Musteri
from urun.models import Urun
from decimal import Decimal # Bu satırı ekleyin!

class Satis(models.Model):
    musteri = models.ForeignKey(
        Musteri,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Müşteri"
    )
    satis_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Satış Tarihi")
    toplam_tutar = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Toplam Tutar (Manuel/Hesaplanan)")
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
    notlar = models.TextField(blank=True, null=True, verbose_name="Notlar")

    class Meta:
        verbose_name = "Satış"
        verbose_name_plural = "Satışlar"
        ordering = ['-satis_tarihi']

    def __str__(self):
        return f"Satış #{self.id} - {self.satis_tarihi.strftime('%Y-%m-%d %H:%M')}"

    @property
    def hesaplanan_toplam_tutar(self):
        total = self.satis_urunleri.aggregate(total_price=models.Sum(models.F('adet') * models.F('birim_fiyat')))['total_price']
        # 'models.Decimal' yerine 'Decimal' kullanın
        return total if total is not None else Decimal('0.00')

    @property
    def odenen_toplam_tutar(self):
        # 'models.Decimal' yerine 'Decimal' kullanın
        return self.satis_odemeleri.aggregate(models.Sum('miktar'))['miktar__sum'] or Decimal('0.00')

    @property
    def alinacak_tutar(self):
        return self.hesaplanan_toplam_tutar - self.odenen_toplam_tutar

class SatisUrun(models.Model):
    satis = models.ForeignKey(
        Satis,
        on_delete=models.CASCADE,
        related_name='satis_urunleri',
        verbose_name="Satış"
    )
    urun = models.ForeignKey(
        Urun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ürün"
    )
    adet = models.PositiveIntegerField(default=1, verbose_name="Adet")
    birim_fiyat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Birim Fiyat")

    class Meta:
        verbose_name = "Satış Ürünü"
        verbose_name_plural = "Satış Ürünleri"
        unique_together = ('satis', 'urun')

    def __str__(self):
        return f"Satış #{self.satis.id} - {self.urun.ad if self.urun else 'Silinmiş Ürün'} ({self.adet} adet)"

    @property
    def toplam_urun_fiyati(self):
        return self.adet * self.birim_fiyat

    def save(self, *args, **kwargs):
        if self.pk:
            original_satis_urun = SatisUrun.objects.get(pk=self.pk)
            original_adet = original_satis_urun.adet
            adet_farki = self.adet - original_adet

            if self.urun:
                if self.urun.stok_adedi > 0 or adet_farki > 0:
                    self.urun.stok_adedi -= adet_farki
                    self.urun.save()
        else:
            if self.urun and self.urun.stok_adedi > 0:
                self.urun.stok_adedi -= self.adet
                self.urun.save()

        if self.urun and (self.birim_fiyat == 0.00 or self.birim_fiyat is None):
            self.birim_fiyat = self.urun.satis_fiyati

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.urun:
            self.urun.stok_adedi += self.adet
            self.urun.save()
        super().delete(*args, **kwargs)


class SatisOdeme(models.Model):
    satis = models.ForeignKey(
        Satis,
        on_delete=models.CASCADE,
        related_name='satis_odemeleri',
        verbose_name="İlgili Satış"
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
        verbose_name = "Satış Ödemesi"
        verbose_name_plural = "Satış Ödemeleri"
        ordering = ['-odeme_tarihi']

    def __str__(self):
        return f"Satış #{self.satis.id} için {self.miktar} TL ödeme ({self.odeme_tarihi.strftime('%Y-%m-%d %H:%M')})"