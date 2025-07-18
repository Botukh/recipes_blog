from django import template

register = template.Library()

UNITS = {
    'банка': ['банка', 'банки', 'банок'],
    'батон': ['батон', 'батона', 'батонов'],
    'веточка': ['веточка', 'веточки', 'веточек'],
    'г': ['г', 'г', 'г'],
    'горсть': ['горсть', 'горсти', 'горстей'],
    'капля': ['капля', 'капли', 'капель'],
    'кусок': ['кусок', 'куска', 'кусков'],
    'мл': ['мл', 'мл', 'мл'],
    'стакан': ['стакан', 'стакана', 'стаканов'],
    'ст. л.': ['ст. л.', 'ст. л.', 'ст. л.'],
    'ч. л.': ['ч. л.', 'ч. л.', 'ч. л.'],
    'шт.': ['шт.', 'шт.', 'шт.'],
    'щепотка': ['щепотка', 'щепотки', 'щепоток'],
}


@register.filter
def pluralize_unit(unit, amount):
    """Склоняет единицу измерения в зависимости от количества."""
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return unit

    forms = UNITS.get(unit.lower())
    if not forms:
        return unit

    n = int(amount)
    if n % 10 == 1 and n % 100 != 11:
        return forms[0]
    elif 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return forms[1]
    else:
        return forms[2]
