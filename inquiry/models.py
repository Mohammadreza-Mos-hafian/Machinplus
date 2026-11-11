from django.db import models


class Lead(models.Model):
    class Path(models.TextChoices):
        PRODUCTION = "production", "راه‌اندازی خط تولید (بالای ۲ میلیارد)"
        TRADING = "trading", "بازرگانی (زیر ۲ میلیارد)"

    class Budget(models.TextChoices):
        # production path
        P_2_5 = "p_2_5", "۲ تا ۵ میلیارد تومان"
        P_5_10 = "p_5_10", "۵ تا ۱۰ میلیارد تومان"
        P_10_PLUS = "p_10_plus", "بالای ۱۰ میلیارد تومان"
        # trading path
        T_LT_500M = "t_lt_500m", "زیر ۵۰۰ میلیون تومان"
        T_500M_1B = "t_500m_1b", "۵۰۰ میلیون تا ۱ میلیارد تومان"
        T_1_2B = "t_1_2b", "۱ تا ۲ میلیارد تومان"

    class Status(models.TextChoices):
        NEW = "new", "جدید"
        CALLED = "called", "تماس گرفته شد"
        NO_ANSWER = "no_answer", "پاسخ نداد"
        QUALIFIED = "qualified", "مشتری جدی"
        LOST = "lost", "منصرف شد"

    name = models.CharField("نام", max_length=120)
    phone = models.CharField("موبایل", max_length=11, db_index=True)
    city = models.CharField("شهر", max_length=60)
    path = models.CharField("مسیر", max_length=20, choices=Path.choices, db_index=True)
    budget = models.CharField("سرمایه", max_length=20, choices=Budget.choices)

    status = models.CharField("وضعیت", max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    note = models.TextField("یادداشت کارشناس", blank=True)
    submissions = models.PositiveSmallIntegerField("دفعات ثبت", default=1)

    # where the lead came from / what they watched
    intro_watched = models.BooleanField("ویدیوی معرفی را کامل دید", default=False)
    path_watched = models.BooleanField("ویدیوی مسیر را کامل دید", default=False)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    referrer = models.URLField(max_length=500, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)

    created_at = models.DateTimeField("زمان ثبت", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "درخواست مشاوره"
        verbose_name_plural = "درخواست‌های مشاوره"

    def __str__(self):
        return f"{self.name} · {self.phone}"


# Which budget ranges belong to which path (used by form validation and the template).
BUDGETS_BY_PATH = {
    Lead.Path.PRODUCTION: [Lead.Budget.P_2_5, Lead.Budget.P_5_10, Lead.Budget.P_10_PLUS],
    Lead.Path.TRADING: [Lead.Budget.T_LT_500M, Lead.Budget.T_500M_1B, Lead.Budget.T_1_2B],
}
