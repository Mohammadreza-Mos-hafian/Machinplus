from django.db.models import Count
from django.views.generic import ListView, DetailView, TemplateView

from shop.models import Product


# Create your views here.
class ProductListView(ListView):
    """Paginated list of active products for the shop frontend."""

    model = Product
    template_name = "shop/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        """Return active products with useful counters for the template."""
        return (
            super()
            .get_queryset()
            .filter(is_active=True)
            .annotate(
                seller_count=Count("sellers", distinct=True),
                feature_count=Count("features", distinct=True),
            )
            .prefetch_related("gallery_images")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # دادهٔ خام (لیست/دیکشنری) را می‌دهیم، نه رشتهٔ JSON
        context["products_json"] = self.build_products_data()
        return context

    def build_products_data(self):
        """لیستی از همهٔ محصولات فعال با ساختار مناسب برای PRODUCTS در JS"""

        products = Product.objects.filter(is_active=True).prefetch_related(
            "gallery_images", "features", "sellers"
        )

        data = []
        for product in products:
            seller = product.sellers.first()  # اولین فروشنده

            data.append(
                {
                    "id": product.pk,
                    "title": product.title,
                    "slug": product.title.replace(' ', '-'),
                    "desc": product.summary,
                    "image": product.main_image.url if product.main_image else "",
                    "category": getattr(product, "category", ""),
                    "location": getattr(product, "location", ""),
                    "condition": "new",
                    "price": getattr(product, "price", 0),
                    "old_price": getattr(product, "old_price", 0),
                    "price_on_request": getattr(product, "price_on_request", None),
                    "stock": getattr(product, "stock", 0),
                    "is_available": getattr(product, "is_available", None),
                    "brand": getattr(product, "brand", ""),
                    "gallery": [
                        img.image.url
                        for img in product.gallery_images.all()
                        if img.image
                    ],
                    "specs": [
                        {"label": feature.name, "value": feature.value}
                        for feature in product.features.all()[:2]
                    ],
                    "seller": {
                        "company": getattr(seller, "name", "") if seller else "",
                        "location": getattr(seller, "location", "") if seller else "",
                        "verified": getattr(seller, "verified", False) if seller else False,
                        "rating": getattr(seller, "rating", "") if seller else "",
                    },
                }
            )

        return data


class ProductDetailView(DetailView):
    """Detail page of a single active product with all related data."""

    model = Product
    template_name = "shop/product_detail.html"
    context_object_name = "product"

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
        context["product_json"] = self.build_product_data()
        context["related_json"] = self.build_related_products()
        return context

    def build_product_data(self):
        product = self.object

        seller = product.sellers.first()

        data = {
            "id": product.pk,
            "slug": product.title.replace(" ", "-"),
            "title": product.title,
            "desc": product.summary,
            "image": product.main_image.url if product.main_image else "",
            "category": getattr(product, "category", ""),
            "location": getattr(product, "location", ""),
            "condition": "new",
            "price": getattr(product, "price", 0),
            "old_price": getattr(product, "old_price", 0),
            "price_on_request": getattr(product, "price_on_request", None),
            "stock": getattr(product, "stock", 0),
            "is_available": getattr(product, "is_available", None),
            "brand": getattr(product, "brand", ""),
            "gallery": [
                img.image.url
                for img in product.gallery_images.all()
                if img.image
            ],
            "specs": [
                {"label": feature.name, "value": feature.value}
                for feature in product.features.all()
            ],
            "seller": {
                "company": getattr(seller, "name", "") if seller else "",
                "phone": seller.phone,
                "location": "کرج",
                "verified": True,
                "rating": "5",
            }
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
                "slug": product.title.replace(" ", "-"),
                "desc": product.summary,
                "image": product.main_image.url if product.main_image else "",
            })

        return data


class CartListView(TemplateView):
    template_name = 'shop/cart.html'


class CheckoutView(TemplateView):
    template_name = 'shop/checkout.html'


class PaymentView(TemplateView):
    template_name = 'shop/payment.html'


class PaymentResultView(TemplateView):
    template_name = 'shop/payment_result.html'
