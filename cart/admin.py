from django.contrib import admin
from django.utils.html import format_html

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False

    fields = (
        "product_name",
        "product_sku",
        "quantity",
        "unit_price",
        "total_price",
    )

    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer",
        "phone",
        "total_display",
        "status_display",
        "stock_reserved",
        "created_at",
    )

    list_filter = (
        "status",
        "stock_reserved",
        "created_at",
    )

    search_fields = (
        "order_number",
        "first_name",
        "last_name",
        "phone",
        "email",
        "user__username",
    )

    readonly_fields = (
        "order_number",
        "user",
        "checkout_token",
        "subtotal",
        "shipping_cost",
        "total",
        "created_at",
        "updated_at",
        "paid_at",
        "expires_at",
        "stock_released_at",
    )

    fieldsets = (
        ("اطلاعات سفارش", {
            "fields": (
                "order_number",
                "user",
                "status",
                "created_at",
                "updated_at",
            )
        }),
        ("اطلاعات مشتری", {
            "fields": (
                "first_name",
                "last_name",
                "phone",
                "email",
            )
        }),
        ("اطلاعات ارسال", {
            "fields": (
                "recipient",
                "postal_code",
                "address",
                "delivery_description",
            )
        }),
        ("اطلاعات مالی", {
            "fields": (
                "subtotal",
                "shipping_cost",
                "total",
                "paid_at",
            )
        }),
        ("مدیریت موجودی و پرداخت", {
            "fields": (
                "stock_reserved",
                "expires_at",
                "stock_released_at",
                "checkout_token",
            )
        }),
    )

    inlines = (OrderItemInline,)

    ordering = ("-created_at",)
    list_per_page = 25
    date_hierarchy = "created_at"

    @admin.display(description="مشتری", ordering="last_name")
    def customer(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    @admin.display(description="مبلغ نهایی", ordering="total")
    def total_display(self, obj):
        return f"{obj.total:,.0f} تومان"

    @admin.display(description="وضعیت سفارش", ordering="status")
    def status_display(self, obj):
        colors = {
            "pending": "#d97706",
            "paid": "#16a34a",
            "shipped": "#2563eb",
            "cancelled": "#dc2626",
        }

        color = colors.get(obj.status, "#6b7280")

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "product_name",
        "product_sku",
        "order",
        "quantity",
        "unit_price",
        "total_price",
    )

    search_fields = (
        "product_name",
        "product_sku",
        "order__order_number",
    )

    readonly_fields = (
        "order",
        "product",
        "product_name",
        "product_sku",
        "quantity",
        "unit_price",
        "total_price",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
