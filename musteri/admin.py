# musteri/admin.py

from django.contrib import admin
from .models import Musteri

@admin.register(Musteri)
class MusteriAdmin(admin.ModelAdmin):
    list_display = ('ad', 'soyad', 'telefon', 'eposta', 'kayit_tarihi')
    search_fields = ('ad', 'soyad', 'telefon', 'eposta')
    list_filter = ('kayit_tarihi',)
    date_hierarchy = 'kayit_tarihi'
    ordering = ('-kayit_tarihi',)