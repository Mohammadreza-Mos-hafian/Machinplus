from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models

from account.models import User
from django.utils.text import slugify


# Create your models here.
class Category(models.Model):
    title = models.CharField(max_length=150, unique=True, verbose_name="عنوان دسته‌بندی")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات کوتاه")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["title"]

    def __str__(self):
        return self.title


class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="نام برچسب"
    )

    class Meta:
        verbose_name = "برچسب"
        verbose_name_plural = "برچسب‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Magazine(models.Model):
    STATUS_CHOICES = (
        ('draft', 'پیش‌نویس'),
        ('published', 'منتشر شده'),
        ('archived', 'بایگانی'),
    )

    title = models.CharField(max_length=255, verbose_name="عنوان مقاله")

    slug = models.SlugField(
        max_length=255,
        unique=True,
        allow_unicode=True,
        null=True,
        blank=True,
        verbose_name="آدرس اختصاصی",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="articles",
        verbose_name="دسته‌بندی",
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="articles",
        verbose_name="برچسب‌ها",
    )
    writer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name="نویسنده",
    )
    cover_image = models.ImageField(
        upload_to="articles/covers/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="تصویر شاخص (کاور)",
    )
    summary = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="چکیده / خلاصه مقاله",
        help_text="خلاصه‌ای برای نمایش در کارت مقاله یا متاتگ‌های SEO",
    )
    body = RichTextUploadingField(
        verbose_name="متن کامل مقاله"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="وضعیت انتشار",
    )
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="تاریخ و ساعت انتشار"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ نگارش")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ آخرین به‌روزرسانی")

    class Meta:
        verbose_name = "مقاله"
        verbose_name_plural = "مقالات"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True)
            slug = base_slug or "product"
            counter = 2

            while Magazine.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug or 'product'}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
