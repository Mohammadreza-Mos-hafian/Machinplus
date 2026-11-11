from django.contrib import admin
from django.utils.html import format_html

from .models import Product, ProductFeature, ProductImage, Seller


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = (
        "image",
        "image_preview",
        "title",
        "alt_text",
        "display_order",
    )
    readonly_fields = ("image_preview",)
    ordering = ("display_order", "id")

    @admin.display(description="Preview")
    def image_preview(self, obj):
        if not obj or not obj.image:
            return "No image"

        return format_html(
            '<img src="{}" width="100" height="70" '
            'style="object-fit: cover; border-radius: 6px;" />',
            obj.image.url,
        )


class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1
    fields = (
        "name",
        "value",
        "display_order",
    )
    ordering = ("display_order", "id")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "main_image_preview",
        "seller_count",
        "feature_count",
        "gallery_image_count",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "title",
        "summary",
        "description",
        "sellers__name",
    )

    filter_horizontal = ("sellers",)

    readonly_fields = (
        "main_image_preview",
        "seller_count",
        "feature_count",
        "gallery_image_count",
        "created_at",
        "updated_at",
    )

    fields = (
        "title",
        "main_image",
        "main_image_preview",
        "summary",
        "description",
        "sellers",
        "is_active",
        "seller_count",
        "feature_count",
        "gallery_image_count",
        "created_at",
        "updated_at",
    )

    inlines = (
        ProductFeatureInline,
        ProductImageInline,
    )

    ordering = ("-created_at",)
    list_per_page = 25
    save_on_top = True

    @admin.display(description="Main Image")
    def main_image_preview(self, obj):
        if not obj or not obj.main_image:
            return "No image"

        return format_html(
            '<img src="{}" width="120" height="80" '
            'style="object-fit: cover; border-radius: 6px;" />',
            obj.main_image.url,
        )

    @admin.display(description="Sellers")
    def seller_count(self, obj):
        return obj.sellers.count()

    @admin.display(description="Features")
    def feature_count(self, obj):
        return obj.features.count()

    @admin.display(description="Gallery Images")
    def gallery_image_count(self, obj):
        return obj.gallery_images.count()


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "website",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "phone",
        "website",
    )

    ordering = ("name",)
    list_per_page = 25


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "image_preview",
        "title",
        "display_order",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "product__title",
        "title",
        "alt_text",
    )

    readonly_fields = (
        "image_preview",
        "created_at",
    )

    ordering = (
        "product",
        "display_order",
        "id",
    )

    @admin.display(description="Preview")
    def image_preview(self, obj):
        if not obj or not obj.image:
            return "No image"

        return format_html(
            '<img src="{}" width="120" height="80" '
            'style="object-fit: cover; border-radius: 6px;" />',
            obj.image.url,
        )


@admin.register(ProductFeature)
class ProductFeatureAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "value",
        "display_order",
    )

    search_fields = (
        "product__title",
        "value",
    )

    list_filter = (
        "product",
    )

    ordering = (
        "product",
        "display_order",
        "id",
    )
