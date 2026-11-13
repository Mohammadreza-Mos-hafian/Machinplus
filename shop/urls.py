from django.urls import path

from .views import ProductListView, ProductDetailView, CartListView, CheckoutView, PaymentView, PaymentResultView

app_name = "shop"
urlpatterns = [
    path("products/", ProductListView.as_view(), name="product_list"),
    path("products/<int:pk>/<str:title>", ProductDetailView.as_view(), name="product_detail"),
    path("cart/", CartListView.as_view(), name="cart_list"),
    path("cart/checkout/", CheckoutView.as_view(), name="checkout"),
    path("cart/payment/", PaymentView.as_view(), name="payment"),
    path("payment_result/", PaymentResultView.as_view(), name="payment_result"),

]
