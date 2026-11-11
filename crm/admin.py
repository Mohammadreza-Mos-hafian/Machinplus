from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Contact, DemandData, SupplyData


class DemandDataInline(admin.TabularInline):
    model = DemandData
    extra = 0
    fields = ("required_machinery", "financial_terms", "next_follow_up", "created_at")
    readonly_fields = ("created_at",)
    show_change_link = True


class SupplyDataInline(admin.TabularInline):
    model = SupplyData
    extra = 0
    fields = ("product_specifications", "financial_terms", "next_follow_up", "created_at")
    readonly_fields = ("created_at",)
    show_change_link = True


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "phone_number",
        "company_name",
        "demands_count",
        "supplies_count",
        "created_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = (
        "first_name",
        "last_name",
        "phone_number",
        "company_name",
        "address",
    )
    inlines = [DemandDataInline, SupplyDataInline]
    date_hierarchy = "created_at"
    list_per_page = 25

    fieldsets = (
        ("اطلاعات هویتی و تماس", {
            "fields": (("first_name", "last_name"), "phone_number", "company_name", "email")
        }),
        ("جزئیات و یادداشت‌ها", {
            "fields": ("address", "notes"),
        }),
        ("اطلاعات زمانی", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="نام و نام خانوادگی", ordering="last_name")
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    @admin.display(description="تعداد تقاضا")
    def demands_count(self, obj):
        return obj.demands.count()

    @admin.display(description="تعداد تامین")
    def supplies_count(self, obj):
        return obj.supplies.count()


@admin.register(DemandData)
class DemandDataAdmin(admin.ModelAdmin):
    list_display = (
        "contact_link",
        "contact_phone",
        "short_machinery",
        "follow_up_status",
        "created_at",
    )
    list_filter = ("next_follow_up", "created_at")
    search_fields = (
        "contact__first_name",
        "contact__last_name",
        "contact__phone_number",
        "contact__company_name",
        "required_machinery",
        "financial_terms",
    )
    autocomplete_fields = ["contact"]  # جستجوی سریع و ایجکسی مخاطب
    list_select_related = ["contact"]  # بهینه‌سازی کوئری دیتابیس (حل مشکل N+1)
    date_hierarchy = "next_follow_up"
    list_per_page = 25

    fieldsets = (
        ("اطلاعات مشتری", {
            "fields": ("contact",)
        }),
        ("نیازمندی‌ها و شرایط", {
            "fields": ("required_machinery", "financial_terms")
        }),
        ("پیگیری و زمان‌بندی", {
            "fields": ("next_follow_up", ("created_at", "updated_at"))
        }),
    )
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="مخاطب", ordering="contact__last_name")
    def contact_link(self, obj):
        return f"{obj.contact.first_name} {obj.contact.last_name}"

    @admin.display(description="شماره تماس", ordering="contact__phone_number")
    def contact_phone(self, obj):
        return obj.contact.phone_number

    @admin.display(description="ماشین‌آلات درخواستی")
    def short_machinery(self, obj):
        return (obj.required_machinery[:50] + "...") if len(obj.required_machinery) > 50 else obj.required_machinery

    @admin.display(description="وضعیت پیگیری", ordering="next_follow_up")
    def follow_up_status(self, obj):
        if not obj.next_follow_up:
            return format_html('<span style="color: gray;">تعیین نشده</span>')

        now = timezone.now()
        date_str = obj.next_follow_up.strftime("%Y/%m/%d %H:%M")

        if obj.next_follow_up < now:
            # زمان پیگیری گذشته (قرمز)
            return format_html('<span style="color: #d9534f; font-weight: bold;">⚠️ عقب افتاده: {}</span>', date_str)
        # پیگیری آینده (سبز)
        return format_html('<span style="color: #5cb85c; font-weight: bold;">📅 {}</span>', date_str)


@admin.register(SupplyData)
class SupplyDataAdmin(admin.ModelAdmin):
    list_display = (
        "contact_link",
        "contact_phone",
        "short_specifications",
        "follow_up_status",
        "created_at",
    )
    list_filter = ("next_follow_up", "created_at")
    search_fields = (
        "contact__first_name",
        "contact__last_name",
        "contact__phone_number",
        "contact__company_name",
        "product_specifications",
        "financial_terms",
    )
    autocomplete_fields = ["contact"]  # جستجوی سریع و ایجکسی مخاطب
    list_select_related = ["contact"]  # بهینه‌سازی کوئری دیتابیس
    date_hierarchy = "next_follow_up"
    list_per_page = 25

    fieldsets = (
        ("اطلاعات تامین‌کننده", {
            "fields": ("contact",)
        }),
        ("مشخصات و شرایط فروش", {
            "fields": ("product_specifications", "financial_terms")
        }),
        ("پیگیری و زمان‌بندی", {
            "fields": ("next_follow_up", ("created_at", "updated_at"))
        }),
    )
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="مخاطب", ordering="contact__last_name")
    def contact_link(self, obj):
        return f"{obj.contact.first_name} {obj.contact.last_name}"

    @admin.display(description="شماره تماس", ordering="contact__phone_number")
    def contact_phone(self, obj):
        return obj.contact.phone_number

    @admin.display(description="مشخصات محصولات")
    def short_specifications(self, obj):
        return (obj.product_specifications[:50] + "...") if len(
            obj.product_specifications) > 50 else obj.product_specifications

    @admin.display(description="وضعیت پیگیری", ordering="next_follow_up")
    def follow_up_status(self, obj):
        if not obj.next_follow_up:
            return format_html('<span style="color: gray;">تعیین نشده</span>')

        now = timezone.now()
        date_str = obj.next_follow_up.strftime("%Y/%m/%d %H:%M")

        if obj.next_follow_up < now:
            return format_html('<span style="color: #d9534f; font-weight: bold;">⚠️ عقب افتاده: {}</span>', date_str)
        return format_html('<span style="color: #5cb85c; font-weight: bold;">📅 {}</span>', date_str)
