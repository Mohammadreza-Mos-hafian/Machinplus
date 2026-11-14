from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from shop.models import Product
from .models import Cart, CartItem, Order


def get_cart_for_request(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(
            user=request.user
        )

        return cart

    if not request.session.session_key:
        request.session.create()

    cart, _ = Cart.objects.get_or_create(
        session_key=request.session.session_key
    )

    return cart


def get_item_warnings(item, final_quantity):
    """
    بررسی وضعیت محصول و تولید هشدارهای لازم.
    تعداد محصول را تغییر نمی‌دهد.
    """

    product = item.product
    warnings = []

    if not product.is_active:
        warnings.append({
            "code": "product_inactive",
            "message": "این محصول غیرفعال شده است.",
        })

    if not product.is_available:
        warnings.append({
            "code": "product_unavailable",
            "message": "این محصول در حال حاضر قابل عرضه نیست.",
        })

    if product.price_on_request:
        warnings.append({
            "code": "price_on_request",
            "message": "قیمت این محصول نیازمند استعلام است.",
        })

    if final_quantity > product.stock:
        warnings.append({
            "code": "insufficient_stock",
            "message": "تعداد درخواستی بیشتر از موجودی محصول است.",
            "requested_quantity": final_quantity,
            "available_stock": product.stock,
        })

    if not warnings:
        return None

    return {
        "product_id": product.pk,
        "product_title": product.title,
        "warnings": warnings,
    }


@transaction.atomic
def merge_guest_cart_to_user(user, guest_session_key):
    """
    انتقال یا ادغام سبد خرید مهمان با سبد خرید کاربر.

    سیاست تعداد:
    در صورت بیشتر بودن مجموع تعداد از موجودی،
    تعداد درخواستی حفظ می‌شود و هشدار برگردانده می‌شود.
    """

    if not user.is_authenticated:
        raise ValueError("کاربر باید وارد حساب خود شده باشد.")

    if not guest_session_key:
        return {
            "status": "no_guest_session",
            "transferred_items": 0,
            "merged_items": 0,
            "item_warnings": [],
        }

    User = get_user_model()

    # قفل رکورد کاربر برای هماهنگ کردن درخواست‌های ادغام
    locked_user = (
        User.objects
        .select_for_update()
        .get(pk=user.pk)
    )

    # پیدا کردن و قفل کردن سبد مهمان
    guest_cart = (
        Cart.objects
        .select_for_update()
        .filter(
            session_key=guest_session_key,
            user__isnull=True,
        )
        .first()
    )

    if guest_cart is None:
        return {
            "status": "no_guest_cart",
            "transferred_items": 0,
            "merged_items": 0,
            "item_warnings": [],
        }

    # دریافت و قفل کردن اقلام سبد مهمان
    guest_items = list(
        CartItem.objects
        .select_for_update()
        .filter(cart=guest_cart)
        .select_related("product")
    )

    # پیدا کردن و قفل کردن سبد کاربر
    user_cart = (
        Cart.objects
        .select_for_update()
        .filter(user=locked_user)
        .first()
    )

    # حالت اول: کاربر سبد خرید ندارد
    if user_cart is None:

        item_warnings = []

        for item in guest_items:
            warning = get_item_warnings(
                item=item,
                final_quantity=item.quantity,
            )

            if warning:
                item_warnings.append(warning)

        # انتقال مالکیت سبد مهمان به کاربر
        guest_cart.user = locked_user
        guest_cart.session_key = None

        guest_cart.save(
            update_fields=[
                "user",
                "session_key",
                "updated_at",
            ]
        )

        return {
            "status": "transferred",
            "transferred_items": len(guest_items),
            "merged_items": 0,
            "item_warnings": item_warnings,
        }

    # حالت دوم: هر دو سبد وجود دارند
    transferred_items = 0
    merged_items = 0
    item_warnings = []

    for guest_item in guest_items:

        # بررسی وجود محصول در سبد کاربر
        user_item = (
            CartItem.objects
            .select_for_update()
            .filter(
                cart=user_cart,
                product_id=guest_item.product_id,
            )
            .first()
        )

        if user_item:
            # محصول در هر دو سبد وجود دارد
            final_quantity = (
                    user_item.quantity + guest_item.quantity
            )

            user_item.quantity = final_quantity

            user_item.save(
                update_fields=[
                    "quantity",
                    "updated_at",
                ]
            )

            merged_items += 1

        else:
            # محصول فقط در سبد مهمان وجود دارد
            final_quantity = guest_item.quantity

            guest_item.cart = user_cart

            guest_item.save(
                update_fields=[
                    "cart",
                    "updated_at",
                ]
            )

            transferred_items += 1

        # بررسی وضعیت محصول پس از تعیین تعداد نهایی
        warning = get_item_warnings(
            item=guest_item,
            final_quantity=final_quantity,
        )

        if warning:
            item_warnings.append(warning)

    # حذف سبد مهمان و اقلام باقی‌مانده آن
    guest_cart.delete()

    return {
        "status": "merged",
        "transferred_items": transferred_items,
        "merged_items": merged_items,
        "item_warnings": item_warnings,
    }


@transaction.atomic
def release_order_stock(order_id):
    """
    آزادسازی موجودی رزروشده سفارش منقضی‌شده.

    - فقط سفارش pending قابل لغو است.
    - سفارش قبل از زمان انقضا آزاد نمی‌شود.
    - موجودی فقط یک بار بازگردانده می‌شود.
    """

    order = (
        Order.objects
        .select_for_update()
        .get(pk=order_id)
    )

    now = timezone.now()

    if order.status != 'pending':
        return order

    if not order.expires_at or order.expires_at > now:
        return order

    if order.stock_reserved and not order.stock_released_at:

        order_items = list(
            order.items.all().order_by('product_id')
        )

        product_ids = sorted({
            item.product_id
            for item in order_items
            if item.product_id is not None
        })

        products = (
            Product.objects
            .select_for_update()
            .filter(pk__in=product_ids)
            .order_by('pk')
        )

        products_by_id = {
            product.pk: product
            for product in products
        }

        for item in order_items:
            if item.product_id is None:
                continue

            product = products_by_id.get(item.product_id)

            if product is None:
                continue

            product.stock += item.quantity

            product.save(
                update_fields=['stock']
            )

    order.status = 'cancelled'
    order.stock_reserved = False
    order.stock_released_at = now

    order.save(
        update_fields=[
            'status',
            'stock_reserved',
            'stock_released_at',
            'updated_at',
        ]
    )

    return order
