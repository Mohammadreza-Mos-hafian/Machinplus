"""
crm_sync.py — ارسال لید به CRM (Google Sheets) از طریق وب‌هوک.

محل فایل: کنار views.py و models.py (همان اپ inquiry).
 lse
"""
import logging
import threading
from decouple import config

import requests
from django.conf import settings
from django.utils import timezone

log = logging.getLogger(__name__)

CRM_WEBHOOK_URL = config('CRM_WEBHOOK_URL', default='')
CRM_WEBHOOK_TOKEN = config('CRM_WEBHOOK_TOKEN', default='')
CRM_SYNC_ENABLED = True


def build_payload(lead):
    """
    نکته مهم: path و budget در دیتابیس «کلید» ذخیره می‌شوند (production / p_2_5)،
    ولی CRM متن فارسی را می‌خواهد؛ پس از get_..._display() استفاده می‌کنیم.
    """
    notes = [
        "ویدیوی معرفی: " + ("کامل دید" if lead.intro_watched else "کامل ندید"),
        "ویدیوی مسیر: " + ("کامل دید" if lead.path_watched else "کامل ندید"),
    ]
    return {
        "name": lead.name,
        "mobile": lead.phone,
        "city": lead.city,
        "path": lead.get_path_display(),        # «راه‌اندازی خط تولید (بالای ۲ میلیارد)» / «بازرگانی (زیر ۲ میلیارد)»
        "capital": lead.get_budget_display(),   # «۲ تا ۵ میلیارد تومان» و ...
        "utm_source": lead.utm_source,
        "utm_campaign": lead.utm_campaign,
        # created_at در دیتابیس UTC است؛ به ساعت محلی (settings.TIME_ZONE) تبدیل می‌کنیم
        "created_at": timezone.localtime(lead.created_at).strftime("%Y-%m-%d %H:%M"),
        "note": " | ".join(notes),
    }


def _post(payload, tries=3):
    url = CRM_WEBHOOK_URL
    token = CRM_WEBHOOK_TOKEN
    for attempt in range(1, tries + 1):
        try:
            # requests ریدایرکت ۳۰۲ گوگل را خودش دنبال می‌کند
            resp = requests.post(url, params={"token": token}, json=payload, timeout=30)
            body = resp.json()
            if resp.ok and body.get("ok"):
                log.info("CRM sync ok: %s", body)
                return True
            log.warning("CRM sync rejected (try %s): %s", attempt, resp.text[:300])
            if body.get("error") == "unauthorized":
                return False        # تکرار بی‌فایده است؛ توکن اشتباه است
        except (requests.RequestException, ValueError) as exc:
            log.warning("CRM sync error (try %s): %s", attempt, exc)
    log.error("CRM sync FAILED for mobile=%s", payload.get("mobile"))
    return False


def push_lead_to_crm(lead):
    """
    بعد از هر ثبت فرم صدا زده شود (چه لید جدید، چه تکراری).
    هرگز استثنا پرتاب نمی‌کند و کاربر را معطل نمی‌کند.
    """
    if not CRM_SYNC_ENABLED or not CRM_WEBHOOK_URL:
        return
    try:
        payload = build_payload(lead)   # قبل از ساخت thread، تا thread به دیتابیس دست نزند
    except Exception:
        log.exception("CRM payload build failed")
        return
    threading.Thread(target=_post, args=(payload,), daemon=True).start()