import uuid

from django.db import models
from django.conf import settings
from django.db.models import Q
from django.core.validators import MinValueValidator


def generate_order_number():
    from django.utils import timezone

    date_part = timezone.localdate().strftime('%Y%m%d')
    random_part = uuid.uuid4().hex[:8].upper()

    return f'MP-{date_part}-{random_part}'


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='carts',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='کاربر',
    )

    session_key = models.CharField(
        max_length=40,
        unique=True,
        null=True,
        blank=True,
        verbose_name='شناسه نشست'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        editable=False,
    )

    class Meta:
        verbose_name = 'سبد خرید'
        verbose_name_plural = 'سبدهای خرید'

    constraints = [
        models.UniqueConstraint(
            fields=["user"],
            condition=Q(user__isnull=False),
            name="unique_cart_per_user"
        ),
        models.CheckConstraint(
            condition=(
                    Q(user__isnull=False, session_key__isnull=True) |
                    Q(user__isnull=True, session_key__isnull=False)
            ),
            name="cart_has_exactly_one_owner"
        )
    ]

    def __str__(self):
        return self.user.username


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='سبد خرید',
    )

    product = models.ForeignKey(
        'shop.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='محصول',
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='تعداد',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        editable=False,
    )

    class Meta:
        verbose_name = 'محصول سبد خرید'
        verbose_name_plural = 'محصولات سبد خرید'

        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_product_per_cart"
            )
        ]

    def __str__(self):
        return f"Cart-{self.cart.pk}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('shipped', 'ارسال شده'),
        ('cancelled', 'لغو شده'),
    ]

    order_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name='شماره سفارش',
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='کاربر',
    )

    first_name = models.CharField(
        max_length=100,
        verbose_name='نام',
    )

    last_name = models.CharField(
        max_length=100,
        verbose_name='نام خانوادگی',
    )

    phone = models.CharField(
        max_length=15,
        verbose_name='شماره تماس',
    )

    email = models.EmailField(
        blank=True,
        verbose_name='ایمیل',
    )

    postal_code = models.CharField(
        max_length=10,
        verbose_name='کد پستی',
    )

    recipient = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='نام تحویل‌گیرنده',
    )

    address = models.TextField(
        verbose_name='آدرس',
    )

    delivery_description = models.TextField(
        blank=True,
        verbose_name='توضیحات تحویل',
    )

    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name='مبلغ کالاها',
    )

    shipping_cost = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name='هزینه ارسال',
    )

    total = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name='مبلغ نهایی',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت سفارش',
    )

    checkout_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='شناسه یکتای تسویه‌حساب',
    )

    stock_reserved = models.BooleanField(
        default=False,
        verbose_name='موجودی رزرو شده است',
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان انقضای پرداخت',
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان پرداخت',
    )

    stock_released_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='زمان آزادسازی موجودی',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ثبت سفارش',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='آخرین بروزرسانی',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارش‌ها'

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()

        super().save(*args, **kwargs)

    def __str__(self):
        return f'سفارش {self.order_number} - {self.first_name} {self.last_name}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='سفارش',
    )

    product = models.ForeignKey(
        'shop.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
        verbose_name='محصول',
    )

    product_name = models.CharField(
        max_length=255,
        verbose_name='نام محصول در زمان خرید',
    )

    product_sku = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='شناسه محصول در زمان خرید',
    )

    quantity = models.PositiveIntegerField(
        verbose_name='تعداد',
    )

    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name='قیمت واحد در زمان خرید',
    )

    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name='قیمت کل',
    )

    class Meta:
        verbose_name = 'قلم سفارش'
        verbose_name_plural = 'اقلام سفارش'

    def __str__(self):
        return f'{self.product_name} × {self.quantity}'
