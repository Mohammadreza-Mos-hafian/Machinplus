from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Category, Magazine, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "articles_count", "created_at")
    search_fields = ("title", "description")
    list_per_page = 20

    @admin.display(description="تعداد مقالات")
    def articles_count(self, obj):
        return obj.articles.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Magazine)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "cover_preview",
        "title",
        "category",
        "writer",
        "status_badge",
        "created_at",
    )
    list_filter = ("status", "category", "created_at", "published_at")
    search_fields = ("title", "summary", "body", "writer__username", "writer__first_name", "writer__last_name")
    autocomplete_fields = ["category", "writer"]
    list_select_related = ["category", "writer"]
    date_hierarchy = "created_at"
    list_per_page = 20

    fieldsets = (
        ("اطلاعات اصلی", {
            "fields": ("title", "category", "tags", "writer", "cover_image", "summary")
        }),
        ("محتوای اصلی مقاله", {
            "fields": ("body",)
        }),
        ("تنظیمات انتشار و آمار", {
            "fields": ("status", "published_at"),
        }),
        ("اطلاعات سیستمی", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="تصویر کاور")
    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 35px; object-fit: cover; border-radius: 4px;" />',
                obj.cover_image.url,
            )
        return format_html('<span style="color: #999;">بدون تصویر</span>')

    @admin.display(description="وضعیت", ordering="status")
    def status_badge(self, obj):
        colors = {
            'draft': '#f0ad4e',  # زرد
            'published': '#5cb85c',  # سبز
            'archived': '#d9534f',  # قرمز
        }
        color = colors.get(obj.status, '#777')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display()
        )

    def save_model(self, request, obj, form, change):
        if not change and not obj.writer_id:
            obj.writer = request.user
        if obj.status == 'published' and not obj.published_at:
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)
