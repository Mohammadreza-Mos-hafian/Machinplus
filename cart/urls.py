from django.urls import path

from .views import (
    CartDetailView,
    CheckoutView,
    PaymentView,
    PaymentResultView,
    add_to_cart,
    delete_item,
    update_item_quantity,
)

app_name = 'cart'

urlpatterns = [
    path('', CartDetailView.as_view(), name='cart_detail'),

    path(
        'add_to_cart/',
        add_to_cart,
        name='add_to_cart',
    ),

    path(
        'delete_item/',
        delete_item,
        name='delete_item',
    ),

    path(
        'update_item_quantity/<int:item_id>/',
        update_item_quantity,
        name='update_item_quantity',
    ),

    path(
        'checkout/',
        CheckoutView.as_view(),
        name='checkout',
    ),

    path(
        'payment/',
        PaymentView.as_view(),
        name='payment',
    ),

    path(
        'payment_result/',
        PaymentResultView.as_view(),
        name='payment_result',
    ),
]
