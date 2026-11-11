from django.db import models


# Create your models here.
class Contact(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="نام")
    last_name = models.CharField(max_length=100, verbose_name="نام خانوادگی")
    phone_number = models.CharField(
        max_length=20, unique=True, verbose_name="شماره تماس"
    )

    company_name = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="نام شرکت"
    )
    email = models.EmailField(
        blank=True, null=True, verbose_name="ایمیل"
    )
    address = models.TextField(
        blank=True, null=True, verbose_name="آدرس"
    )
    notes = models.TextField(
        blank=True, null=True, verbose_name="توضیحات و یادداشت"
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="تاریخ ایجاد"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="تاریخ آخرین ویرایش"
    )

    class Meta:
        verbose_name = "مخاطب"
        verbose_name_plural = "1. مخاطبین"
        ordering = ["-created_at"]

    def __str__(self):
        if self.company_name:
            return f"{self.first_name} {self.last_name} ({self.company_name}) - {self.phone_number}"
        return f"{self.first_name} {self.last_name} - {self.phone_number}"


class DemandData(models.Model):
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="demands",
        verbose_name="مخاطب (مشتری)",
    )
    required_machinery = models.TextField(
        verbose_name="ماشین‌آلات مورد نیاز"
    )
    financial_terms = models.TextField(
        verbose_name="شرایط مالی / نحوه پرداخت",
        blank=True,
        null=True,
    )
    next_follow_up = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="پیگیری بعدی",
        help_text="زمان برنامه‌ریزی‌شده برای تماس یا جلسه بعدی"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="تاریخ ثبت تقاضا"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="تاریخ آخرین ویرایش"
    )

    class Meta:
        verbose_name = "مشتری (Demand)"
        verbose_name_plural = "2. تماس با مشتری"
        ordering = ["-created_at"]

    def __str__(self):
        return f"تقاضای {self.contact} - {self.created_at.strftime('%Y/%m/%d')}"


class SupplyData(models.Model):
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="supplies",
        verbose_name="مخاطب (تامین‌کننده)",
    )
    product_specifications = models.TextField(
        verbose_name="مشخصات محصولات / ماشین‌آلات تامین‌کننده"
    )
    financial_terms = models.TextField(
        verbose_name="شرایط مالی فروش / تسویه",
        blank=True,
        null=True,
    )
    next_follow_up = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="پیگیری بعدی",
        help_text="زمان برنامه‌ریزی‌شده برای تماس یا جلسه بعدی"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="تاریخ ثبت تامین"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="تاریخ آخرین ویرایش"
    )

    class Meta:
        verbose_name = "تامین کننده (Supply)"
        verbose_name_plural = "3. تماس با تامین کننده"
        ordering = ["-created_at"]

    def __str__(self):
        return f"تامین {self.contact} - {self.created_at.strftime('%Y/%m/%d')}"
