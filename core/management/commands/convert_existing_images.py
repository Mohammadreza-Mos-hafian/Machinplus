from django.core.management.base import BaseCommand

from blog.models import Magazine
from shop.models import Product, ProductImage

from core.image_processing import (
    generate_image_variants,
    get_variant_path,
)
from core.image_specs import IMAGE_SPECS


class BaseImageProcessor:
    """
    Shared logic for checking and processing image fields.
    """

    @staticmethod
    def has_all_variants(image):
        storage = image.storage

        for variant_name in IMAGE_SPECS:
            variant_path = get_variant_path(
                image.name,
                variant_name,
            )

            if not storage.exists(variant_path):
                return False

        return True


class Command(BaseCommand):
    help = "Convert existing images to optimized WebP variants."

    IMAGE_FIELDS = [
        (Magazine, "cover_image"),
        (Product, "main_image"),
        (ProductImage, "image"),
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only show which images would be processed.",
        )

        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenerate all variants, even if they already exist.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]

        total = 0
        processed = 0
        skipped = 0
        failed = 0

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN: No files will be generated."
                )
            )

        for model, field_name in self.IMAGE_FIELDS:
            self.stdout.write(
                f"\nProcessing {model.__name__}.{field_name}"
            )

            objects = (
                model.objects
                .only("pk", field_name)
                .iterator(chunk_size=200)
            )

            for obj in objects:
                total += 1

                image = getattr(obj, field_name)

                if not image or not image.name:
                    skipped += 1
                    continue

                if not image.storage.exists(image.name):
                    skipped += 1

                    self.stdout.write(
                        self.style.WARNING(
                            f"Missing source: {image.name}"
                        )
                    )
                    continue

                if (
                        not force
                        and BaseImageProcessor.has_all_variants(image)
                ):
                    skipped += 1
                    continue

                if dry_run:
                    self.stdout.write(
                        f"Would process: {image.name}"
                    )
                    continue

                try:
                    generate_image_variants(image)

                    processed += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Processed: {image.name}"
                        )
                    )

                except Exception as exc:
                    failed += 1

                    self.stderr.write(
                        self.style.ERROR(
                            f"Failed: {image.name} | {exc}"
                        )
                    )

        self.stdout.write("\n" + "-" * 50)

        self.stdout.write(
            f"Total checked: {total}"
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed: {processed}"
            )
        )

        self.stdout.write(
            f"Skipped: {skipped}"
        )

        if failed:
            self.stdout.write(
                self.style.ERROR(
                    f"Failed: {failed}"
                )
            )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\nDry run completed. No images were modified."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nImage conversion completed."
                )
            )
