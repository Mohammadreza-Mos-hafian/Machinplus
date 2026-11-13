from django import template

register = template.Library()

TRANSLATION_TABLE = str.maketrans(
    "0123456789",
    "۰۱۲۳۴۵۶۷۸۹"
)


@register.filter
def persian_numbers(value):
    if value is None:
        return value

    return str(value).translate(TRANSLATION_TABLE)
