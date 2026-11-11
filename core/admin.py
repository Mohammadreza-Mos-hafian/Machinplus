from django.contrib import admin, messages

from core.models import ChatMessage, SystemPrompt, InquiryForm


# Register your models here.
# @admin.register(ChatMessage)
# class ChatMessageAdmin(admin.ModelAdmin):
#     pass
#
#
# @admin.register(SystemPrompt)
# class SystemPromptAdmin(admin.ModelAdmin):
#     list_display = ('title', 'priority', 'is_active')
#     list_editable = ('priority', 'is_active')

@admin.register(InquiryForm)
class InquiryFormAdmin(admin.ModelAdmin):
    def has_add_permission(self, request): return False

    list_display = ('full_name', 'phone_number', 'status', 'created_at')
    list_filter = ('status', 'created_at')

    readonly_fields = (
        'full_name', 'phone_number', 'q1', 'q2', 'q3', 'q4', 'q5',
        'q6', 'q7', 'q8', 'q9', 'q10', 'q11', 'q12', 'created_at'
    )

    fieldsets = (
        ('اطلاعات تماس', {
            'fields': ('full_name', 'phone_number', 'created_at')
        }),
        ('پاسخ‌های کاربر', {
            'fields': ('q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9', 'q10', 'q11', 'q12')
        }),
        ('بخش داخلی (مدیریت)', {
            'fields': ('status', 'review_result')
        }),
    )

    actions = [
        'mark_as_in_progress',
        'mark_as_reviewed',
        'mark_as_pending'
    ]

    @admin.action(description='تغییر وضعیت به: خوانده شده')
    def mark_as_in_progress(self, request, queryset):
        updated_count = queryset.update(status='read')
        self.message_user(
            request,
            f'وضعیت {updated_count} پرسشنامه به "خوانده شده" تغییر یافت.',
            messages.SUCCESS
        )

    @admin.action(description='تغییر وضعیت به: درحال بررسی')
    def mark_as_reviewed(self, request, queryset):
        updated_count = queryset.update(status='in_review')
        self.message_user(
            request,
            f'وضعیت {updated_count} پرسشنامه به "درحال بررسی" تغییر یافت.',
            messages.SUCCESS
        )

    @admin.action(description='تغییر وضعیت به: بررسی شده')
    def mark_as_pending(self, request, queryset):
        updated_count = queryset.update(status='reviewed')
        self.message_user(
            request,
            f'وضعیت {updated_count} پرسشنامه به "بررسی شده" تغییر یافت.',
            messages.INFO
        )
