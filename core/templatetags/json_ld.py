import json

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def json_ld(value):
    result = json.dumps(value, ensure_ascii=False)

    result = (
        result
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )

    return mark_safe(result)
