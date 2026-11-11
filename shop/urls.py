from django.urls import path

from .views import ProductListView, ProductDetailView

app_name = "shop"
urlpatterns = [
    path("products/", ProductListView.as_view(), name="product_list"),
    path("products/<int:pk>/<str:title>", ProductDetailView.as_view(), name="product_detail"),
]
