# Web/Web/urls.py

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, F, Q
from datetime import timedelta, date, datetime
from django.utils import timezone
from decimal import Decimal
import calendar
from collections import defaultdict

# İhtiyaç duyacağınız modelleri import edin
from siparis.models import Siparis, Odeme
from satis.models import Satis, SatisOdeme, SatisUrun
from giderler.models import Gider, GiderKategorisi
from urun.models import Urun, StokAyarlari

# Türkçe gün ve ay çevirileri için sözlükler
weekday_to_turkish = {
    'Mon': 'Pzt', 'Tue': 'Sal', 'Wed': 'Çar', 'Thu': 'Per',
    'Fri': 'Cum', 'Sat': 'Cmt', 'Sun': 'Paz'
}

month_to_turkish = {
    'Jan': 'Oca', 'Feb': 'Şub', 'Mar': 'Mar', 'Apr': 'Nis',
    'May': 'May', 'Jun': 'Haz', 'Jul': 'Tem', 'Aug': 'Ağu',
    'Sep': 'Eyl', 'Oct': 'Eki', 'Nov': 'Kas', 'Dec': 'Ara' # 'Dec: 'Ara' olarak düzeltildi
}


# --- Custom Admin Dashboard View Fonksiyonu ---
@staff_member_required
def custom_admin_dashboard(request):
    # Süper kullanıcı değilse, sipariş listesine yönlendir
    if not request.user.is_superuser:
        return redirect('admin:siparis_siparis_changelist')

    now = timezone.now() # Mevcut zaman, saat dilimi farkındalıklı
    current_year = now.year
    current_month = now.month
    current_day = now.day

    # Sipariş Durumları Verileri
    uretimde_siparis_sayisi = Siparis.objects.filter(durum='Onaylandı').count()
    teslimata_hazir_siparis_sayisi = Siparis.objects.filter(durum='Hazır').count()

    # Ortak Net Kazanç Hesaplama Fonksiyonu
    def calculate_net_kazanc(start_date_obj, end_date_obj):
        # Parametrelerin aware datetime nesneleri olduğundan emin olun
        if start_date_obj.tzinfo is None:
            start_date_obj = timezone.make_aware(start_date_obj)
        if end_date_obj.tzinfo is None:
            end_date_obj = timezone.make_aware(end_date_obj)

        satis_kazanci = SatisUrun.objects.filter(
            satis__satis_tarihi__gte=start_date_obj,
            satis__satis_tarihi__lte=end_date_obj
        ).aggregate(total=Sum(F('adet') * F('birim_fiyat')))['total'] or Decimal('0.00')

        # 'Teslim Edildi' ve 'Tamamlandı' durumundaki sipariş ödemelerini dahil et
        siparis_odeme_geliri = Odeme.objects.filter(
            odeme_tarihi__gte=start_date_obj,
            odeme_tarihi__lte=end_date_obj,
            siparis__durum__in=['Teslim Edildi', 'Tamamlandı'] # Sadece tamamlanmış sipariş ödemeleri kazanca dahil edilir
        ).aggregate(total=Sum('miktar'))['total'] or Decimal('0.00')

        toplam_giderler = Gider.objects.filter(
            gider_tarihi__gte=start_date_obj,
            gider_tarihi__lte=end_date_obj
        ).aggregate(total=Sum('miktar'))['total'] or Decimal('0.00')

        return (satis_kazanci + siparis_odeme_geliri) - toplam_giderler

    # Ortak Gider Hesaplama Fonksiyonu
    def calculate_gider(start_date_obj, end_date_obj):
        if start_date_obj.tzinfo is None:
            start_date_obj = timezone.make_aware(start_date_obj)
        if end_date_obj.tzinfo is None:
            end_date_obj = timezone.make_aware(end_date_obj)

        toplam_gider = Gider.objects.filter(
            gider_tarihi__gte=start_date_obj,
            gider_tarihi__lte=end_date_obj
        ).aggregate(total=Sum('miktar'))['total'] or Decimal('0.00')
        return toplam_gider


    # --- Net Kazanç Verileri ---
    # Haftalık Net Kazanç (Pazartesiden Pazar'a dahil)
    haftalik_labels = []
    haftalik_values = []
    start_of_week = now - timedelta(days=now.weekday()) # Pazartesi
    for i in range(7):
        target_date = start_of_week + timedelta(days=i)
        start_of_day = timezone.make_aware(datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0))
        end_of_day = timezone.make_aware(datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, 999999))
        
        net_kazanc = calculate_net_kazanc(start_of_day, end_of_day)
        # Türkçe çeviri kullan
        haftalik_labels.append(weekday_to_turkish.get(target_date.strftime('%a'), target_date.strftime('%a')))
        haftalik_values.append(float(net_kazanc))
    
    haftalik_net_kazanc_data = {
        'labels': haftalik_labels,
        'values': haftalik_values,
        'title': 'Haftalık Net Kazanç'
    }

    # Aylık Net Kazanç (Ayın 1'inden son gününe)
    aylik_labels = []
    aylik_values = []
    # calendar.monthrange(year, month)[1] -> ilgili ayın son gününü verir
    num_days_in_month = calendar.monthrange(current_year, current_month)[1]
    
    for i in range(1, num_days_in_month + 1):
        target_date = datetime(current_year, current_month, i)
        start_of_day = timezone.make_aware(datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0))
        end_of_day = timezone.make_aware(datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, 999999))
        
        net_kazanc = calculate_net_kazanc(start_of_day, end_of_day)
        aylik_labels.append(str(i)) # Ayın günleri '1', '2' şeklinde
        aylik_values.append(float(net_kazanc))
    
    aylik_net_kazanc_data = {
        'labels': aylik_labels,
        'values': aylik_values,
        'title': 'Aylık Net Kazanç'
    }

    # Dinamik zaman dilimli veri hesaplayıcı (Son 3, 6, 12 Ay ve Tüm Zamanlar için)
    def get_monthly_data(num_months_ago, include_current_month=True, for_gider=False):
        labels = []
        values = []
        
        months_to_process = []
        for i in range(num_months_ago):
            # Mevcut aydan geriye doğru ay ve yıl hesaplaması
            target_month = current_month - i
            target_year = current_year
            
            while target_month <= 0:
                target_month += 12
                target_year -= 1

            start_date_obj = timezone.make_aware(datetime(target_year, target_month, 1, 0, 0, 0))
            last_day = calendar.monthrange(target_year, target_month)[1]
            end_date_obj = timezone.make_aware(datetime(target_year, target_month, last_day, 23, 59, 59, 999999))
            
            # Eğer şu anki ay ise ve include_current_month True ise, bugüne kadar al
            if i == 0 and include_current_month:
                end_date_obj = now 

            # Türkçe ay adı çevirisi
            month_abbr = start_date_obj.strftime('%b')
            turkish_month_abbr = month_to_turkish.get(month_abbr, month_abbr)
            label_text = f"{turkish_month_abbr} {target_year}"

            months_to_process.insert(0, {'start': start_date_obj, 'end': end_date_obj, 'label': label_text})

        # Her ay için hesaplamayı yap
        for month_info in months_to_process:
            if for_gider:
                amount = calculate_gider(month_info['start'], month_info['end'])
            else:
                amount = calculate_net_kazanc(month_info['start'], month_info['end'])
            labels.append(month_info['label'])
            values.append(float(amount))
        
        return {'labels': labels, 'values': values}

    # 3 Aylık Net Kazanç
    uc_aylik_net_kazanc_data = get_monthly_data(3, include_current_month=True)
    uc_aylik_net_kazanc_data['title'] = 'Son 3 Ay Net Kazanç'

    # 6 Aylık Net Kazanç
    alti_aylik_net_kazanc_data = get_monthly_data(6, include_current_month=True)
    alti_aylik_net_kazanc_data['title'] = 'Son 6 Ay Net Kazanç'
    
    # Yıllık Net Kazanç (Son 12 Ayın aylık bazda)
    yillik_net_kazanc_data = get_monthly_data(12, include_current_month=True)
    yillik_net_kazanc_data['title'] = 'Son 12 Ay Net Kazanç'

    # Tüm Zamanlar Net Kazanç (Yıllara göre)
    tum_zamanlar_net_kazanc = defaultdict(Decimal)
    
    # En eski ve en yeni yıl
    min_year_in_data = current_year
    max_year_in_data = current_year

    first_siparis_date = Siparis.objects.order_by('siparis_tarihi').values_list('siparis_tarihi', flat=True).first()
    first_satis_date = Satis.objects.order_by('satis_tarihi').values_list('satis_tarihi', flat=True).first()
    first_gider_date = Gider.objects.order_by('gider_tarihi').values_list('gider_tarihi', flat=True).first()

    dates = [d for d in [first_siparis_date, first_satis_date, first_gider_date] if d is not None]
    if dates:
        min_year_in_data = min(d.year for d in dates)
    
    all_years_net_kazanc = list(range(min_year_in_data, max_year_in_data + 1))

    for year in all_years_net_kazanc:
        start_of_year = timezone.make_aware(datetime(year, 1, 1, 0, 0, 0))
        end_of_year = timezone.make_aware(datetime(year, 12, 31, 23, 59, 59, 999999))
        net_kazanc = calculate_net_kazanc(start_of_year, end_of_year)
        tum_zamanlar_net_kazanc[str(year)] = net_kazanc

    tum_zamanlar_net_kazanc_data = {
        'labels': all_years_net_kazanc,
        'values': [float(tum_zamanlar_net_kazanc.get(str(y), Decimal('0.00'))) for y in all_years_net_kazanc],
        'title': 'Tüm Zamanlar Net Kazanç'
    }


    # --- Giderler Dinamik Grafik Verileri ---
    haftalik_gider_labels = []
    haftalik_gider_values = []
    start_of_week_gider = now - timedelta(days=now.weekday()) # Pazartesi
    for i in range(7):
        target_date_gider = start_of_week_gider + timedelta(days=i)
        start_of_day_gider = timezone.make_aware(datetime(target_date_gider.year, target_date_gider.month, target_date_gider.day, 0, 0, 0))
        end_of_day_gider = timezone.make_aware(datetime(target_date_gider.year, target_date_gider.month, target_date_gider.day, 23, 59, 59, 999999))
        
        gider_toplami = calculate_gider(start_of_day_gider, end_of_day_gider)
        # Türkçe çeviri kullan
        haftalik_gider_labels.append(weekday_to_turkish.get(target_date_gider.strftime('%a'), target_date_gider.strftime('%a')))
        haftalik_gider_values.append(float(gider_toplami))
    
    haftalik_gider_data = {
        'labels': haftalik_gider_labels,
        'values': haftalik_gider_values,
        'title': 'Haftalık Giderler'
    }

    aylik_gider_labels = []
    aylik_gider_values = []
    num_days_in_month_gider = calendar.monthrange(current_year, current_month)[1]
    
    for i in range(1, num_days_in_month_gider + 1):
        target_date_gider = datetime(current_year, current_month, i)
        start_of_day_gider = timezone.make_aware(datetime(target_date_gider.year, target_date_gider.month, target_date_gider.day, 0, 0, 0))
        end_of_day_gider = timezone.make_aware(datetime(target_date_gider.year, target_date_gider.month, target_date_gider.day, 23, 59, 59, 999999))
        
        gider_toplami = calculate_gider(start_of_day_gider, end_of_day_gider)
        aylik_gider_labels.append(str(i))
        aylik_gider_values.append(float(gider_toplami))
    
    aylik_gider_data = {
        'labels': aylik_gider_labels,
        'values': aylik_gider_values,
        'title': 'Aylık Giderler'
    }

    uc_aylik_gider_data = get_monthly_data(3, include_current_month=True, for_gider=True)
    uc_aylik_gider_data['title'] = 'Son 3 Ay Giderler'

    alti_aylik_gider_data = get_monthly_data(6, include_current_month=True, for_gider=True)
    alti_aylik_gider_data['title'] = 'Son 6 Ay Giderler'

    yillik_gider_data = get_monthly_data(12, include_current_month=True, for_gider=True)
    yillik_gider_data['title'] = 'Son 12 Ay Giderler'
    
    # Tüm Zamanlar Giderler (Yıl Bazında)
    tum_zamanlar_gider = defaultdict(Decimal)
    
    if dates: # 'dates' listesi yukarıda tanımlanmıştı
        min_year_gider_data = min(d.year for d in dates)
    else:
        min_year_gider_data = current_year
    
    all_years_gider = list(range(min_year_gider_data, current_year + 1))

    for year in all_years_gider:
        start_of_year = timezone.make_aware(datetime(year, 1, 1, 0, 0, 0))
        end_of_year = timezone.make_aware(datetime(year, 12, 31, 23, 59, 59, 999999))
        gider = calculate_gider(start_of_year, end_of_year)
        tum_zamanlar_gider[str(year)] = gider

    tum_zamanlar_gider_data = {
        'labels': all_years_gider,
        'values': [float(tum_zamanlar_gider.get(str(y), Decimal('0.00'))) for y in all_years_gider],
        'title': 'Tüm Zamanlar Giderler'
    }


    # --- Giderler Tablosu Verisi (Kategorilere göre aylık) ---
    gider_kategorileri = GiderKategorisi.objects.all().order_by('ad')
    giderler_aylik_data = {}
    
    # Son 6 ayı alalım (mevcut ay dahil 6 ay)
    for i in range(6): 
        # Mevcut aydan geriye doğru git
        target_date_month = (current_month - i - 1 + 12) % 12 + 1
        target_date_year = current_year if (current_month - i) > 0 else current_year - 1
        
        month_start = timezone.make_aware(datetime(target_date_year, target_date_month, 1, 0, 0, 0))
        last_day_of_month = calendar.monthrange(target_date_year, target_date_month)[1]
        month_end = timezone.make_aware(datetime(target_date_year, target_date_month, last_day_of_month, 23, 59, 59, 999999))

        month_str = month_start.strftime('%Y-%m')
        giderler_aylik_data[month_str] = {}
        
        for kategori in gider_kategorileri:
            aylik_gider = Gider.objects.filter(
                gider_tarihi__gte=month_start,
                gider_tarihi__lte=month_end,
                kategori=kategori
            ).aggregate(total=Sum('miktar'))['total'] or Decimal('0.00')
            giderler_aylik_data[month_str][kategori.ad] = float(aylik_gider)

    # Veresiye Tutarı Verisi - SİPARİŞLER
    alinacak_tutar_siparis = Decimal('0.00')
    # Sipariş modelinde doğrudan 'Veresiye' durumu olmadığı için,
    # 'alinacak_tutar'ı (yani kalan borcu) pozitif olan tüm siparişleri dikkate alıyoruz.
    # Eğer 'Veresiye' durumunu özel olarak takip etmek isterseniz,
    # Siparis modelinize bu durumu eklemeli ve buradaki filtreyi buna göre değiştirmelisiniz.
    for siparis in Siparis.objects.all():
        if siparis.alinacak_tutar > Decimal('0.00'):
            alinacak_tutar_siparis += siparis.alinacak_tutar
    alinacak_tutar_siparis = max(Decimal('0.00'), alinacak_tutar_siparis) # Negatif olmamalı

    # Veresiye Tutarı Verisi - SATIŞLAR
    alinacak_tutar_satis = Decimal('0.00')
    # Satis modelinde zaten tanımlı olan 'alinacak_tutar' property'sini kullanıyoruz.
    for satis in Satis.objects.all():
        if satis.alinacak_tutar > Decimal('0.00'):
            alinacak_tutar_satis += satis.alinacak_tutar
    alinacak_tutar_satis = max(Decimal('0.00'), alinacak_tutar_satis) # Negatif olmamalı

    toplam_veresiye_alinacak_data = {
        'siparis_veresiye': float(alinacak_tutar_siparis),
        'satis_veresiye': float(alinacak_tutar_satis)
    }

    toplam_veresiye_alinacak_data = {
        'siparis_veresiye': float(alinacak_tutar_siparis),
        'satis_veresiye': float(alinacak_tutar_satis)
    }

    # Stok Bilgileri
    stokta_olmayan_urun_sayisi = Urun.objects.filter(stok_adedi=0).count()
    
    dusuk_stok_urun_sayisi = 0
    dusuk_stok_esigi = 0
    stok_ayarlari = StokAyarlari.objects.first()
    if stok_ayarlari:
        dusuk_stok_esigi = stok_ayarlari.dusuk_stok_esik_1
        dusuk_stok_urun_sayisi = Urun.objects.filter(
            stok_adedi__gt=0, stok_adedi__lte=dusuk_stok_esigi
        ).count()
    
    context = {
        'uretimde_siparis_sayisi': uretimde_siparis_sayisi,
        'teslimata_hazir_siparis_sayisi': teslimata_hazir_siparis_sayisi,
        
        'haftalik_net_kazanc_data': haftalik_net_kazanc_data,
        'aylik_net_kazanc_data': aylik_net_kazanc_data,
        'uc_aylik_net_kazanc_data': uc_aylik_net_kazanc_data,
        'alti_aylik_net_kazanc_data': alti_aylik_net_kazanc_data,
        'yillik_net_kazanc_data': yillik_net_kazanc_data,
        'tum_zamanlar_net_kazanc_data': tum_zamanlar_net_kazanc_data,
        
        'toplam_veresiye_alinacak_data': toplam_veresiye_alinacak_data,
        
        'stokta_olmayan_urun_sayisi': stokta_olmayan_urun_sayisi,
        'dusuk_stok_urun_sayisi': dusuk_stok_urun_sayisi,
        'dusuk_stok_esigi': dusuk_stok_esigi, 

        'haftalik_gider_data': haftalik_gider_data,
        'aylik_gider_data': aylik_gider_data,
        'uc_aylik_gider_data': uc_aylik_gider_data,
        'alti_aylik_gider_data': alti_aylik_gider_data,
        'yillik_gider_data': yillik_gider_data,
        'tum_zamanlar_gider_data': tum_zamanlar_gider_data,
        
        'giderler_aylik_data': giderler_aylik_data,
        'gider_kategorileri': [kategori.ad for kategori in gider_kategorileri],
    }
    return render(request, 'admin/custom_dashboard.html', context)


# admin.site.index'i Kendi Dashboard View'ımızla Değiştirme
admin.site.index = custom_admin_dashboard
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/admin/', permanent=False))
]

# Geliştirme ortamında static ve media dosyalarını servis etmek için
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)