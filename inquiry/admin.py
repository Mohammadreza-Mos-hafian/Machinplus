import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "city", "path", "budget", "status", "submissions", "intro_watched", "path_watched", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "path", "budget", "intro_watched", "path_watched", "utm_source", "created_at")
    search_fields = ("name", "phone", "city", "utm_campaign")
    date_hierarchy = "created_at"
    list_per_page = 50
    readonly_fields = ("submissions", "intro_watched", "path_watched", "utm_source", "utm_medium", "utm_campaign",
                       "referrer", "ip", "user_agent", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "phone", "city", "path", "budget")}),
        ("پیگیری", {"fields": ("status", "note", "submissions")}),
        ("منبع و رفتار", {"classes": ("collapse",), "fields": ("intro_watched", "path_watched", "utm_source", "utm_medium",
                                                         "utm_campaign", "referrer", "ip", "user_agent", "created_at", "updated_at")}),
    )
    actions = ("mark_called", "export_csv")

    @admin.action(description="علامت «تماس گرفته شد»")
    def mark_called(self, request, queryset):
        n = queryset.update(status=Lead.Status.CALLED)
        self.message_user(request, f"{n} مورد به‌روز شد.")

    @admin.action(description="خروجی اکسل (CSV)")
    def export_csv(self, request, queryset):
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="leads-{timezone.localdate()}.csv"'
        resp.write("﻿")  # BOM so Excel shows Persian correctly
        w = csv.writer(resp)
        w.writerow(["نام", "موبایل", "شهر", "مسیر", "سرمایه", "وضعیت", "یادداشت", "دفعات ثبت", "utm_source", "utm_campaign", "زمان ثبت"])
        for l in queryset:
            w.writerow([l.name, l.phone, l.city, l.get_path_display(), l.get_budget_display(), l.get_status_display(),
                        l.note, l.submissions, l.utm_source, l.utm_campaign, timezone.localtime(l.created_at).strftime("%Y-%m-%d %H:%M")])
        return resp
