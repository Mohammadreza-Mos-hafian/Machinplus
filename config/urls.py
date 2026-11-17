"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls.py import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls.py'))
"""
from django.contrib import admin
from django.conf.urls.static import static
from config import settings
from django.urls import path, include, register_converter
from django.contrib.sitemaps.views import sitemap
from .sitemaps import (
    StaticViewSitemap,
    MagazineSitemap,
    ProductSitemap,
)

from django.urls.converters import StringConverter
from urllib.parse import unquote


class PersianSlugConverter(StringConverter):
    regex = r"(?:[-\w\u0600-\u06FF]|%[0-9A-Fa-f]{2})+"

    def to_python(self, value):
        return unquote(value)


register_converter(PersianSlugConverter, 'persian_slug')

urlpatterns = [
    path("", include('core.urls')),
    path("account/", include('account.urls')),
    path("blog/", include('blog.urls')),
    path("shop/", include('shop.urls')),
    path("campaign/", include("inquiry.urls")),
    path("cart/", include("cart.urls")),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path("management-panel/", admin.site.urls),
]

sitemaps = {
    "static": StaticViewSitemap,
    "articles": MagazineSitemap,
    "products": ProductSitemap,
}

urlpatterns += [
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "core.views.custom_404"
handler500 = "core.views.custom_500"
