from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from account.models import User


# Create your models here.
class ChatMessage(models.Model):
    """
    Chat messages Model.
    ForeignKey with User Model.
    """
    user = models.ForeignKey(to=User, verbose_name=_('کاربر', ), on_delete=models.CASCADE, null=True, blank=True)
    user_message = models.TextField(verbose_name=_('پیام کاربر'))
    bot_message = models.TextField(verbose_name=_('پیام بات'))
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_message


class SystemPrompt(models.Model):
    title = models.CharField(max_length=100, verbose_name=_("Title"))
    content = models.TextField(verbose_name=_("Prompt Content"))
    priority = models.IntegerField(default=0, help_text=_("Lower numbers come first"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        verbose_name = _("System Prompt")
        verbose_name_plural = _("System Prompts")
        ordering = ['priority']

    def __str__(self):
        return self.title


class InquiryForm(models.Model):
    STATUS_CHOICES = (
        ('read', 'خوانده شده'),
        ('in_review', 'در مرحله بررسی'),
        ('reviewed', 'بررسی شده'),
    )
    full_name = models.CharField(max_length=200, verbose_name="۱۳. نام و نام خانوادگی")
    phone_number = models.CharField(max_length=20, verbose_name="۱۴. شماره تلفن")

    q1 = models.CharField(max_length=255, null=True, blank=True, verbose_name="۱. هدف اصلی از تامین ماشین‌آلات")
    q2 = models.CharField(max_length=255, null=True, blank=True, verbose_name="۲. بازه زمانی تصمیم‌گیری")
    q3 = models.CharField(max_length=255, null=True, blank=True, verbose_name="۳. وضعیت تامین بودجه")
    q4 = models.CharField(max_length=255, null=True, blank=True, verbose_name="۴. حجم سرمایه‌گذاری")
    q5 = models.CharField(max_length=255, null=True, blank=True, verbose_name="۵. نقش شما در پروسه تصمیم‌گیری")
    q6 = models.CharField(max_length=255, null=True, blank=True, verbose_name="۶. وضعیت حقوقی و فعالیت صنعتی")
    q7 = models.CharField(max_length=255, null=True, blank=True, verbose_name="۷. وضعیت زیرساخت‌ها")
    q8 = models.CharField(max_length=255, null=True, blank=True, verbose_name="۸. اولویت اصلی انتخاب")
    q9 = models.CharField(max_length=255, null=True, blank=True, verbose_name="۹. نوع خرید مد نظر")
    q10 = models.CharField(max_length=255, null=True, blank=True, verbose_name="۱۰. زمان مشاوره حضوری")

    q11 = models.TextField(verbose_name="۱۱. نام دقیق و مشخصات فنی ماشین‌آلات")
    q12 = models.TextField(verbose_name="۱۲. شرایط خاص یا سفارشی‌سازی")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_review', verbose_name="وضعیت")
    review_result = models.TextField(blank=True, null=True, verbose_name="نتیجه بررسی")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        verbose_name = "پرسشنامه ماشین پلاس"
        verbose_name_plural = "پرسشنامه‌های دریافتی"

    def __str__(self):
        return f"{self.full_name} - {self.phone_number}"
