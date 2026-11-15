import json

from urllib.parse import unquote
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.views.generic import ListView, DetailView

from django.utils.safestring import mark_safe
from shop.models import Product

from utils.functions import get_user_cart


class ProductListView(ListView):
    """Paginated list of active products for the shop frontend."""

    model = Product
    template_name = "shop/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_object(self, queryset=None):
        queryset = queryset or self.get_queryset()

        slug = unquote(self.kwargs[self.slug_url_kwarg])

        return get_object_or_404(
            queryset,
            **{self.slug_field: slug}
        )

    def get_queryset(self):
        """Return active products with related data loaded efficiently."""
        return (
            super()
            .get_queryset()
            .filter(is_active=True)
            .annotate(
                seller_count=Count("sellers", distinct=True),
                feature_count=Count("features", distinct=True),
            )
            .prefetch_related(
                "gallery_images",
                "features",
                "sellers",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart = get_user_cart(self.request)

        # فقط محصولات صفحه جاری به JavaScript ارسال می‌شوند.
        context["products_json"] = self.build_products_data(
            context["products"],
            cart,
        )

        # تعداد آیتم‌های سبد خرید، نه مجموع تعداد هر محصول
        context["cart_items_count"] = cart.items.count() if cart else 0

        return context

    def build_products_data(self, products, cart):
        """
        Build product data for the JavaScript frontend.
        Only products belonging to the current pagination page are processed.
        """

        data = []

        for product in products:
            seller = product.sellers.first()

            data.append(
                {
                    "id": product.pk,
                    "title": product.title,
                    "slug": product.slug,
                    "desc": product.summary,
                    "image": (
                        product.main_image.url
                        if product.main_image
                        else ""
                    ),
                    "category": getattr(product, "category", ""),
                    "location": getattr(product, "location", ""),
                    "condition": "new",
                    "price": getattr(product, "price", 0),
                    "old_price": getattr(product, "old_price", 0),
                    "price_on_request": getattr(
                        product,
                        "price_on_request",
                        None,
                    ),
                    "stock": getattr(product, "stock", 0),
                    "is_available": getattr(
                        product,
                        "is_available",
                        None,
                    ),
                    "brand": getattr(product, "brand", ""),
                    "gallery": [
                        img.image.url
                        for img in product.gallery_images.all()
                        if img.image
                    ],
                    "specs": [
                        {
                            "label": feature.name,
                            "value": feature.value,
                        }
                        for feature in product.features.all()[:2]
                    ],
                    "seller": {
                        "company": (
                            getattr(seller, "name", "")
                            if seller
                            else ""
                        ),
                        "location": (
                            getattr(seller, "location", "")
                            if seller
                            else ""
                        ),
                        "verified": (
                            getattr(seller, "verified", False)
                            if seller
                            else False
                        ),
                        "rating": (
                            getattr(seller, "rating", "")
                            if seller
                            else ""
                        ),
                    },
                    "is_in_cart": (
                        product.cart_items.filter(cart=cart).exists()
                        if cart
                        else False
                    ),
                }
            )

        return data


class ProductDetailView(DetailView):
    """Detail page of a single active product with all related data."""

    model = Product
    template_name = "shop/product_detail.html"
    context_object_name = "product"

    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        """Load gallery, features and sellers in a few optimized queries."""
        return (
            super()
            .get_queryset()
            .filter(is_active=True)
            .prefetch_related("gallery_images", "features", "sellers")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_user_cart(self.request)

        context["is_in_cart"] = (
            self.object.cart_items.filter(cart=cart).exists()
            if cart
            else False
        )

        product = self.object

        discount_percentage = 0

        if (
                product.price
                and product.old_price
                and product.old_price > product.price
        ):
            discount_percentage = round(
                (product.old_price - product.price)
                / product.old_price * 100
            )

        context["discount_percentage"] = discount_percentage
        context["cart_items_count"] = cart.items.count() if cart else 0
        context["product_json"] = self.build_product_data()
        context["related_json"] = self.build_related_products()
        context["product_structured_data"] = self.build_product_structured_data()

        return context

    def build_product_data(self):
        product = self.object
        seller = product.sellers.first()
        cart = get_user_cart(self.request)

        price = product.price
        price_on_request = bool(product.price_on_request) or price is None

        data = {
            "id": product.pk,
            "slug": product.slug,
            "title": product.title,
            "desc": product.summary,
            "image": product.main_image.url if product.main_image else "",
            "category": getattr(product, "category", ""),
            "location": getattr(product, "location", ""),
            "condition": "new",
            "price": price,
            "old_price": getattr(product, "old_price", 0),
            "price_on_request": price_on_request,
            "stock": getattr(product, "stock", 0),
            "is_available": getattr(product, "is_available", None),
            "brand": getattr(product, "brand", ""),
            "gallery": [
                img.image.url
                for img in product.gallery_images.all()
                if img.image
            ],
            "specs": [
                {
                    "label": feature.name,
                    "value": feature.value,
                }
                for feature in product.features.all()
            ],
            "seller": {
                "company": getattr(seller, "name", "") if seller else "",
                "phone": seller.phone if seller else "",
                "location": "کرج",
                "verified": True,
                "rating": "5",
            },
            "is_in_cart": (
                product.cart_items.filter(cart=cart).exists()
                if cart
                else False
            ),
        }

        return data

    def build_related_products(self, limit=3):
        current = self.object

        others = (
            Product.objects
            .filter(is_active=True)
            .exclude(pk=current.pk)  # بجز محصول فعلی
            .select_related()
            .prefetch_related("gallery_images", "features", "sellers")
            .order_by("-id")[:limit]  # سه آیتم آخر/جدیدترین
        )

        data = []
        for product in others:
            seller = product.sellers.first()

            data.append({
                "id": product.pk,
                "title": product.title,
                "slug": product.slug,
                "desc": product.summary,
                "image": product.main_image.url if product.main_image else "",
                "condition": "new",
                "price": product.price,
                "price_on_request": (
                        bool(product.price_on_request)
                        or product.price is None
                ),
                "stock": getattr(product, "stock", 0),
                "is_available": getattr(product, "is_available", None),
                "category": getattr(product, "category", ""),
            })

        return data

    def build_product_structured_data(self):
        product = self.object

        data = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": product.title,
            "sku": product.sku,
        }

        if product.summary:
            data["description"] = product.summary

        if product.main_image:
            data["image"] = [
                self.request.build_absolute_uri(product.main_image.url)
            ]

        # محصولات دارای قیمت مشخص
        if not product.price_on_request and product.price is not None:
            if (
                    product.is_active
                    and product.is_available
                    and product.stock > 0
            ):
                availability = "https://schema.org/InStock"
            else:
                availability = "https://schema.org/OutOfStock"

            data["offers"] = {
                "@type": "Offer",
                "url": self.request.build_absolute_uri(self.request.path),
                "price": int(product.price) * 10,
                "priceCurrency": "IRR",
                "availability": availability,
            }

        # جلوگیری از تفسیر محتوای محصول به‌عنوان HTML داخل script
        json_data = json.dumps(data, ensure_ascii=False)

        json_data = (
            json_data
            .replace("<", "\\u003C")
            .replace(">", "\\u003E")
            .replace("&", "\\u0026")
        )

        return mark_safe(json_data)
