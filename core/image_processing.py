from io import BytesIO
from pathlib import PurePosixPath

from PIL import Image, ImageOps
from django.core.files.base import ContentFile

from .image_specs import IMAGE_SPECS


def get_variant_path(original_path, variant_name):
    path = PurePosixPath(original_path)

    return str(
        PurePosixPath("optimized")
        / path.parent
        / f"{path.stem}_{variant_name}.webp"
    )


def generate_image_variants(image_field):
    if not image_field:
        return

    storage = image_field.storage

    try:
        with storage.open(image_field.name, "rb") as file:
            image_data = file.read()

        with Image.open(BytesIO(image_data)) as source:
            source = ImageOps.exif_transpose(source)
            source.load()

            has_alpha = (
                    source.mode in ("RGBA", "LA")
                    or "transparency" in source.info
            )

            if has_alpha:
                source = source.convert("RGBA")
            else:
                source = source.convert("RGB")

            for name, config in IMAGE_SPECS.items():
                output = source.copy()

                output.thumbnail(
                    config["size"],
                    Image.Resampling.LANCZOS,
                )

                buffer = BytesIO()

                output.save(
                    buffer,
                    format="WEBP",
                    quality=config["quality"],
                    method=6,
                )

                variant_path = get_variant_path(
                    image_field.name,
                    name,
                )

                if storage.exists(variant_path):
                    storage.delete(variant_path)

                storage.save(
                    variant_path,
                    ContentFile(buffer.getvalue()),
                )

    except Exception:
        raise


def get_responsive_image_data(image_field):
    """
    Return optimized image URLs and actual dimensions
    for responsive image rendering.
    """

    if not image_field or not image_field.name:
        return {
            "src": "",
            "srcset": "",
        }

    storage = image_field.storage
    variants = {}

    priority = {
        "thumbnail": 1,
        "card": 2,
        "large": 3,
    }

    for variant_name in IMAGE_SPECS:
        variant_path = get_variant_path(
            image_field.name,
            variant_name,
        )

        try:
            if not storage.exists(variant_path):
                continue

            with storage.open(variant_path, "rb") as file:
                with Image.open(file) as image:
                    width = image.width

            if (
                    width not in variants
                    or priority[variant_name] > variants[width][0]
            ):
                variants[width] = (
                    priority[variant_name],
                    storage.url(variant_path),
                )

        except (OSError, KeyError):
            continue

    card_path = get_variant_path(
        image_field.name,
        "card",
    )

    if storage.exists(card_path):
        src = storage.url(card_path)
    else:
        src = image_field.url

    srcset = ", ".join(
        f"{url} {width}w"
        for width, (_, url) in sorted(variants.items())
    )

    return {
        "src": src,
        "srcset": srcset,
    }
