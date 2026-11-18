import json
from urllib.parse import urljoin, urlencode

from django.conf import settings
from django.db.models import Count, Prefetch
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import ListView, DetailView

from shop.models import Product, Seller
from utils.functions import get_user_cart, toman_to_rial


class ProductStructuredDataMixin:
    """Shared helpers for product URLs and structured data."""

    def get_site_url(self):
        if settings.DEBUG:
            return self.request.build_absolute_uri("/").rstrip("/")

        return "https://machinplus.ir"

    def get_product_url(self, product):
        product_path = reverse(
            "shop:product_detail",
            kwargs={"slug": product.slug},
        )

        return urljoin(
            f"{self.get_site_url()}/",
            product_path.lstrip("/"),
        )

    def get_availability(self, product):
        if product.is_available and product.stock > 0:
            return "https://schema.org/InStock"

        return "https://schema.org/OutOfStock"

    def build_offer_data(self, product):
        """
        Build an Offer only when the product has a specified price.
        Product prices are stored in Toman and converted to Rial.
        """

        if product.price_on_request or product.price is None:
            return None

        return {
            "@type": "Offer",
            "url": self.get_product_url(product),
            "price": toman_to_rial(product.price),
            "priceCurrency": "IRR",
            "availability": self.get_availability(product),
        }

    @staticmethod
    def serialize_json_ld(data):
        """Safely serialize JSON-LD for an HTML script element."""

        json_data = json.dumps(data, ensure_ascii=False)

        json_data = (
            json_data
            .replace("<", "\\u003C")
            .replace(">", "\\u003E")
            .replace("&", "\\u0026")
        )

        return mark_safe(json_data)


class ProductListView(ProductStructuredDataMixin, ListView):
    """Paginated list of active products for the shop frontend."""

    model = Product
    template_name = "shop/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
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
                Prefetch(
                    "sellers",
                    queryset=Seller.objects.filter(is_active=True),
                ),
            )
        )

    def get_product_list_url(self, page_obj):
        """
        Return the canonical URL of the current pagination page.
        Page 1 uses the base URL; subsequent pages include ?page=N.
        """

        path = self.request.path

        if page_obj and page_obj.number > 1:
            path = f"{path}?{urlencode({'page': page_obj.number})}"

        return urljoin(
            f"{self.get_site_url()}/",
            path.lstrip("/"),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart = get_user_cart(self.request)
        products = context["products"]
        page_obj = context["page_obj"]

        context["products_json"] = self.build_products_data(
            products,
            cart,
        )

        context["cart_items_count"] = (
            cart.items.count() if cart else 0
        )

        product_list_url = self.get_product_list_url(page_obj)

        context["seo_title"] = (
            "فروشگاه ماشین‌آلات صنعتی | ماشین پلاس"
        )

        context["seo_description"] = (
            "مرور و خرید ماشین‌آلات صنعتی، قطعات یدکی و تجهیزات تولید "
            "از تأمین‌کنندگان معتبر در ماشین پلاس."
        )

        context["seo_type"] = "website"
        context["seo_url"] = product_list_url

        collection_data = self.build_collection_json_ld(
            products=products,
            page_obj=page_obj,
            product_list_url=product_list_url,
        )

        context["product_collection_json_ld"] = (
            self.serialize_json_ld(collection_data)
        )

        return context

    def build_products_data(self, products, cart):
        """Build frontend data for products on the current page."""

        data = []

        for product in products:
            seller = product.sellers.first()

            data.append({
                "id": product.pk,
                "title": product.title,
                "slug": product.slug,
                "desc": product.summary,
                "image": (
                    product.main_image.url
                    if product.main_image
                    else ""
                ),

                # These fields are retained for frontend compatibility.
                # They remain empty because Product has no such fields.
                "category": "",
                "location": "",
                "condition": "",
                "brand": "",

                "price": product.price,
                "old_price": product.old_price,
                "price_on_request": (
                        product.price_on_request
                        or product.price is None
                ),
                "stock": product.stock,
                "is_available": product.is_available,

                "gallery": [
                    image.image.url
                    for image in product.gallery_images.all()
                    if image.image
                ],

                "specs": [
                    {
                        "label": feature.name or "",
                        "value": feature.value,
                    }
                    for feature in product.features.all()[:2]
                ],

                "seller": {
                    "company": seller.name if seller else "",
                    "phone": seller.phone if seller else "",
                    "website": seller.website if seller else "",
                    "location": "",
                    "verified": None,
                    "rating": "",
                },

                "is_in_cart": (
                    product.cart_items.filter(cart=cart).exists()
                    if cart
                    else False
                ),
            })

        return data

    def build_collection_json_ld(
            self,
            products,
            page_obj,
            product_list_url,
    ):
        site_url = self.get_site_url()

        item_list = []

        start_position = (
            page_obj.start_index()
            if page_obj
            else 1
        )

        for position, product in enumerate(
                products,
                start=start_position,
        ):
            product_url = self.get_product_url(product)

            product_data = {
                "@type": "Product",
                "@id": f"{product_url}#product",
                "name": product.title,
                "url": product_url,
            }

            if product.sku:
                product_data["sku"] = product.sku

            if product.summary:
                product_data["description"] = product.summary

            if product.main_image:
                product_data["image"] = self.request.build_absolute_uri(
                    product.main_image.url
                )

            offer_data = self.build_offer_data(product)

            if offer_data:
                product_data["offers"] = offer_data

            item_list.append({
                "@type": "ListItem",
                "position": position,
                "item": product_data,
            })

        return {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "@id": f"{product_list_url}#collection",
            "url": product_list_url,
            "name": "فروشگاه ماشین‌آلات صنعتی | ماشین پلاس",
            "description": (
                "مرور ماشین‌آلات صنعتی، قطعات یدکی و تجهیزات تولید "
                "در فروشگاه ماشین پلاس."
            ),
            "inLanguage": "fa-IR",
            "isPartOf": {
                "@id": f"{site_url}/#website",
            },
            "publisher": {
                "@id": f"{site_url}/#organization",
            },
            "mainEntity": {
                "@type": "ItemList",
                "@id": f"{product_list_url}#product-list",
                "numberOfItems": (
                    page_obj.paginator.count
                    if page_obj
                    else len(item_list)
                ),
                "itemListElement": item_list,
            },
        }


class ProductDetailView(ProductStructuredDataMixin, DetailView):
    """Detail page of a single active product with related data."""

    model = Product
    template_name = "shop/product_detail.html"
    context_object_name = "product"

    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_active=True)
            .prefetch_related(
                "gallery_images",
                "features",
                Prefetch(
                    "sellers",
                    queryset=Seller.objects.filter(is_active=True),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        product = self.object
        cart = get_user_cart(self.request)

        context["is_in_cart"] = (
            product.cart_items.filter(cart=cart).exists()
            if cart
            else False
        )

        discount_percentage = 0

        if (
                product.price is not None
                and product.old_price is not None
                and product.old_price > product.price
        ):
            discount_percentage = round(
                (product.old_price - product.price)
                / product.old_price * 100
            )

        context["discount_percentage"] = discount_percentage
        context["cart_items_count"] = (
            cart.items.count() if cart else 0
        )

        context["product_json"] = self.build_product_data()
        context["related_json"] = self.build_related_products()

        context["product_structured_data"] = (
            self.build_product_structured_data()
        )
        context["product_breadcrumb_json_ld"] = self.build_breadcrumb_json_ld()

        product_url = self.get_product_url(product)

        # SEO metadata
        context["seo_title"] = product.title
        context["seo_description"] = (
                product.summary or product.title
        )
        context["seo_type"] = "website"
        context["seo_url"] = product_url

        context["seo_image"] = (
            self.request.build_absolute_uri(product.main_image.url)
            if product.main_image
            else ""
        )

        return context

    def build_product_data(self):
        product = self.object
        seller = product.sellers.first()
        cart = get_user_cart(self.request)

        return {
            "id": product.pk,
            "slug": product.slug,
            "title": product.title,
            "desc": product.summary,
            "image": (
                product.main_image.url
                if product.main_image
                else ""
            ),

            # No corresponding fields currently exist in Product.
            "category": "",
            "location": "",
            "condition": "",
            "brand": "",

            "price": product.price,
            "old_price": product.old_price,
            "price_on_request": (
                    product.price_on_request
                    or product.price is None
            ),
            "stock": product.stock,
            "is_available": product.is_available,

            "gallery": [
                image.image.url
                for image in product.gallery_images.all()
                if image.image
            ],

            "specs": [
                {
                    "label": feature.name or "",
                    "value": feature.value,
                }
                for feature in product.features.all()
            ],

            "seller": {
                "company": seller.name if seller else "",
                "phone": seller.phone if seller else "",
                "website": seller.website if seller else "",
                "location": "",
                "verified": None,
                "rating": "",
            },

            "is_in_cart": (
                product.cart_items.filter(cart=cart).exists()
                if cart
                else False
            ),
        }

    def build_related_products(self, limit=3):
        current = self.object

        others = (
            Product.objects
            .filter(is_active=True)
            .exclude(pk=current.pk)
            .order_by("-created_at")[:limit]
        )

        data = []

        for product in others:
            data.append({
                "id": product.pk,
                "title": product.title,
                "slug": product.slug,
                "desc": product.summary,
                "image": (
                    product.main_image.url
                    if product.main_image
                    else ""
                ),
                "condition": "",
                "price": product.price,
                "old_price": product.old_price,
                "price_on_request": (
                        product.price_on_request
                        or product.price is None
                ),
                "stock": product.stock,
                "is_available": product.is_available,
            })

        return data

    def build_product_structured_data(self):
        product = self.object
        product_url = self.get_product_url(product)

        data = {
            "@context": "https://schema.org",
            "@type": "Product",
            "@id": f"{product_url}#product",
            "name": product.title,
            "url": product_url,
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": product_url,
            },
        }

        if product.sku:
            data["sku"] = product.sku

        if product.summary:
            data["description"] = product.summary

        images = []

        if product.main_image:
            images.append(
                self.request.build_absolute_uri(
                    product.main_image.url
                )
            )

        for image in product.gallery_images.all():
            if image.image:
                images.append(
                    self.request.build_absolute_uri(
                        image.image.url
                    )
                )

        if images:
            data["image"] = images

        offer_data = self.build_offer_data(product)

        if offer_data:
            data["offers"] = offer_data

        return self.serialize_json_ld(data)

    def build_breadcrumb_json_ld(self):
        product_url = self.get_product_url(self.object)

        data = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "خانه",
                    "item": f"{self.get_site_url()}/",
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "محصولات",
                    "item": urljoin(self.get_site_url() + "/", reverse("shop:product_list").lstrip("/")),
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": self.object.title,
                    "item": product_url,
                },
            ],
        }

        return self.serialize_json_ld(data)
