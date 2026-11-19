from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from blog.models import Magazine
from shop.models import Product, ProductImage

from .image_processing import generate_image_variants

IMAGE_MODELS = {
    Magazine: ("cover_image",),
    Product: ("main_image",),
    ProductImage: ("image",),
}


@receiver(pre_save)
def track_image_changes(sender, instance, **kwargs):
    if sender not in IMAGE_MODELS:
        return

    if not instance.pk:
        instance._changed_image_fields = set(
            IMAGE_MODELS[sender]
        )
        return

    old_instance = sender.objects.filter(
        pk=instance.pk
    ).only(*IMAGE_MODELS[sender]).first()

    changed_fields = set()

    if old_instance:
        for field_name in IMAGE_MODELS[sender]:
            old_file = getattr(old_instance, field_name)
            new_file = getattr(instance, field_name)

            old_name = old_file.name if old_file else None
            new_name = new_file.name if new_file else None

            if old_name != new_name:
                changed_fields.add(field_name)

    instance._changed_image_fields = changed_fields


@receiver(post_save)
def process_uploaded_images(sender, instance, **kwargs):
    if sender not in IMAGE_MODELS:
        return

    changed_fields = getattr(
        instance,
        "_changed_image_fields",
        set(),
    )

    for field_name in changed_fields:
        image_field = getattr(instance, field_name)

        if image_field:
            generate_image_variants(image_field)
