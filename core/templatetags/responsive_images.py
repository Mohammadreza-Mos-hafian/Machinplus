from django import template
from django.utils.html import format_html_join

from core.image_processing import get_variant_path
from core.image_specs import IMAGE_SPECS

register = template.Library()


@register.simple_tag
def webp_url(image, variant="card"):
    if not image:
        return ""

    if variant not in IMAGE_SPECS:
        return ""

    path = get_variant_path(image.name, variant)

    return image.storage.url(path)


@register.simple_tag
def webp_srcset(image):
    if not image:
        return ""

    items = []

    for name, config in IMAGE_SPECS.items():
        path = get_variant_path(image.name, name)

        url = image.storage.url(path)
        width = config["size"][0]

        items.append((url, width))

    return format_html_join(
        ", ",
        "{} {}w",
        items,
    )
