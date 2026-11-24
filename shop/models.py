from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator

from ckeditor_uploader.fields import RichTextUploadingField
from django.db.models import Q, F
from django.utils.text import slugify


class ProductCategory(models.Model):
    code = models.CharField(
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        verbose_name='کد اختصاصی'
    )

    name = models.CharField(
        max_length=32,
        verbose_name='نام دسته بندی',
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='توضیحات',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ آخرین بروزرسانی',
    )

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    STATUS_CHOICES = [
        ('new', 'نو'),
        ('used', 'کارکرده'),
    ]

    title = models.CharField(
        max_length=255,
        verbose_name="عنوان محصول"
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
        allow_unicode=True,
        null=True,
        blank=True,
        verbose_name="آدرس اختصاصی",
        help_text="مثال: volvo-fh16 یا روغن-موتور"
    )

    sku = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        verbose_name='کد اختصاصی'
    )

    category = models.ForeignKey(
        ProductCategory,
        related_name='products',
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        verbose_name='دسته بندی',
    )

    main_image = models.ImageField(
        upload_to="products/main/",
        verbose_name="تصویر اصلی محصول",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "webp"]
            )
        ]
    )

    summary = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="خلاصه محصول"
    )

    description = RichTextUploadingField(
        verbose_name="توضیحات محصول"
    )

    sellers = models.ManyToManyField(
        "Seller",
        blank=True,
        related_name="products",
        verbose_name="فروشندگان محصول"
    )

    price = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name='قیمت (تومان)'
    )

    old_price = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name='قیمت قبلی (تومان)'
    )

    stock = models.PositiveIntegerField(
        default=0,
        verbose_name='موجودی'
    )

    price_on_request = models.BooleanField(
        default=False,
        verbose_name='قیمت با استعلام'
    )

    status = models.CharField(
        max_length=8,
        choices=STATUS_CHOICES,
        null=True,
        blank=True,
        verbose_name='وضعیت',
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name="قابل دسترس"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین ویرایش"
    )

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ["-created_at"]

        constraints = [
            models.CheckConstraint(
                condition=(
                        Q(price_on_request=True, price__isnull=True)
                        |
                        Q(price_on_request=False, price__gt=0)
                ),
                name='product_valid_price_state',
            ),

            models.CheckConstraint(
                condition=(
                        Q(old_price__isnull=True)
                        |
                        (
                                Q(price__isnull=False)
                                & Q(old_price__gt=F('price'))
                        )
                ),
                name='product_old_price_greater_than_price',
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True)
            slug = base_slug or "product"
            counter = 2

            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug or 'product'}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="gallery_images",
        verbose_name="محصول"
    )

    image = models.ImageField(
        upload_to="products/gallery/",
        verbose_name="تصویر گالری",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "webp"]
            )
        ]
    )

    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="عنوان تصویر"
    )

    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="متن جایگزین تصویر"
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصولات"
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return f"{self.product.title} - تصویر {self.pk}"


class ProductFeature(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="features",
        verbose_name="محصول="
    )

    name = models.CharField(
        max_length=500,
        null=True,
        verbose_name="نام ویژگی"
    )

    value = models.CharField(
        max_length=500,
        verbose_name="مقدار ویژگی"
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )

    class Meta:
        verbose_name = "ویژگی محصول"
        verbose_name_plural = "ویژگی‌های محصولات"
        ordering = ["display_order", "id"]

    def __str__(self):
        return f"{self.name}: {self.value}"


class Seller(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="نام فروشنده"
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="شماره تماس"
    )

    website = models.URLField(
        blank=True,
        verbose_name="وب‌سایت"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحاتوضیحات فروشنده"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    class Meta:
        verbose_name = "فروشنده"
        verbose_name_plural = "فروشندگان"
        ordering = ["name"]

    def __str__(self):
        return self.name
