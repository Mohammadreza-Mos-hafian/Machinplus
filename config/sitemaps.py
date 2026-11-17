from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import Magazine
from shop.models import Product


class StaticViewSitemap(Sitemap):
    priority = 0.7
    changefreq = "monthly"

    def items(self):
        return [
            "core:home",
            "core:catalog",
            "core:inquiry",
            "core:contact-us",
            "core:terms",
            "blog:list",
            "shop:product_list",
        ]

    def location(self, item):
        return reverse(item)


class MagazineSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Magazine.objects.filter(
            status="published",
            published_at__isnull=False,
        ).order_by("-published_at")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse(
            "blog:detail",
            kwargs={
                "pk": obj.pk,
                "title": obj.title,
            },
        )


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.filter(
            is_active=True,
            is_available=True,
        ).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse(
            "shop:product_detail",
            kwargs={"slug": obj.slug},
        )
