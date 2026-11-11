import json
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

from .forms import LeadForm
from .models import BUDGETS_BY_PATH, Lead
from .notify import notify_new_lead

RATE_LIMIT = getattr(settings, "INQUIRY_RATE_LIMIT", 5)            # submissions
RATE_WINDOW = getattr(settings, "INQUIRY_RATE_WINDOW", 10 * 60)    # seconds, per IP
DEDUPE_HOURS = getattr(settings, "INQUIRY_DEDUPE_HOURS", 24)       # same phone -> update, not a new row


def client_ip(request):
    if getattr(settings, "INQUIRY_TRUST_X_FORWARDED_FOR", False):
        fwd = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def budgets_for_template():
    return {
        path: [{"value": b.value, "label": b.label.replace(" تومان", "")} for b in budgets]
        for path, budgets in BUDGETS_BY_PATH.items()
    }


@method_decorator(ensure_csrf_cookie, name="dispatch")
class InquiryView(View):
    template_name = "inquiry/inquiry.html"

    def get(self, request):
        return render(request, self.template_name, {"budgets": budgets_for_template()})

    def post(self, request):
        try:
            payload = json.loads(request.body or b"{}")
            if not isinstance(payload, dict):
                raise ValueError
        except ValueError:
            return JsonResponse({"ok": False, "message": "درخواست نامعتبر است."}, status=400)

        form = LeadForm(payload)
        if not form.is_valid():
            errors = {field: errs[0] for field, errs in form.errors.items()}
            return JsonResponse({"ok": False, "message": "لطفاً خطاهای فرم را برطرف کنید.", "errors": errors}, status=400)
        data = form.cleaned_data

        # bots fill the hidden field: pretend success, store nothing
        if data.get("website"):
            return JsonResponse({"ok": True})

        ip = client_ip(request)
        key = f"inquiry:rl:{ip}"
        hits = cache.get(key, 0)
        if hits >= RATE_LIMIT:
            return JsonResponse({"ok": False, "message": "تعداد درخواست‌ها زیاد است. چند دقیقه دیگر دوباره تلاش کنید."}, status=429)
        cache.set(key, hits + 1, RATE_WINDOW)

        fields = {
            "name": data["name"], "city": data["city"], "path": data["path"], "budget": data["budget"],
            "intro_watched": data["intro_watched"], "path_watched": data["path_watched"],
            "utm_source": data["utm_source"], "utm_medium": data["utm_medium"], "utm_campaign": data["utm_campaign"],
            "referrer": data["referrer"], "ip": ip,
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:300],
        }

        since = timezone.now() - timedelta(hours=DEDUPE_HOURS)
        existing = Lead.objects.filter(phone=data["phone"], created_at__gte=since).first()
        if existing:
            Lead.objects.filter(pk=existing.pk).update(**fields, submissions=F("submissions") + 1, updated_at=timezone.now())
            existing.refresh_from_db()
            notify_new_lead(existing, is_repeat=True)
            return JsonResponse({"ok": True, "id": existing.pk, "repeat": True})

        lead = Lead.objects.create(phone=data["phone"], **fields)
        notify_new_lead(lead)
        return JsonResponse({"ok": True, "id": lead.pk}, status=201)
