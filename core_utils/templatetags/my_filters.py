from django import template

register = template.Library()

@register.filter
def get_item(collection, key):
    """
    Sözlükten veya listeden belirli bir anahtar veya indekse göre öğe alır.
    Varsayılan olarak None döndürür, bu da floatformat ile sorun yaşanmasını önler.
    """
    try:
        if isinstance(collection, dict):
            return collection.get(key)
        elif isinstance(collection, list):
            # Eğer anahtar geçerli bir indeks değilse None dönsün
            if isinstance(key, int) and 0 <= key < len(collection):
                return collection[key]
            return None # Geçersiz indeks
        return None # Ne sözlük ne de liste
    except (TypeError, IndexError, KeyError):
        return None