from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator

from ckeditor_uploader.fields import RichTextUploadingField


# Create your models here.
class Product(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name="عنوان محصول"
    )

    sku = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name='کد اختصاصی'
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

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='قیمت',
        validators=[
            MinValueValidator(0)
        ]
    )

    old_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='قیمت قدیمی',
        validators=[
            MinValueValidator(0)
        ]
    )

    stock = models.PositiveIntegerField(
        default=0,
        verbose_name='موجودی'
    )

    price_on_request = models.BooleanField(
        default=False,
        verbose_name='قیمت با استعلام'
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
