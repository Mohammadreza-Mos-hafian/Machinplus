"""Optional instant notification to the sales team when a lead comes in.

Works with any Telegram-compatible bot API. Bale (bale.ai) is the default because
Telegram's API is not reachable from most servers hosted in Iran.

settings.py:
    INQUIRY_NOTIFY_BOT_TOKEN = "123456:ABC..."        # empty = disabled
    INQUIRY_NOTIFY_CHAT_IDS = ["123456789"]           # one or more chats/groups
    INQUIRY_NOTIFY_API = "https://tapi.bale.ai/bot{token}/sendMessage"   # default
"""
import json
import logging
import threading
import urllib.request

from django.conf import settings
from decouple import config, Csv

log = logging.getLogger(__name__)

BOT_TOKEN = config('INQUIRY_NOTIFY_BOT_TOKEN', default='')

CHAT_IDS = config(
    'INQUIRY_NOTIFY_CHAT_IDS',
    default='',
    cast=Csv()
)

API_URL = config(
    'INQUIRY_NOTIFY_API',
    default='https://tapi.bale.ai/bot{token}/sendMessage'
)


def _send(url, chat_id, text):
    body = json.dumps({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=8).read()
    except Exception:  # never let a notification failure lose the lead
        log.exception("inquiry: notification failed")


def notify_new_lead(lead, is_repeat=False):
    token = BOT_TOKEN
    chats = CHAT_IDS
    if not token or not chats:
        return
    api = API_URL
    title = "ثبت دوباره(در CRM  ثبت شد)" if is_repeat else "درخواست مشاوره جدید (در CRM ثبت شد)"
    text = (
        f"{title}\n"
        f"نام: {lead.name}\n"
        f"موبایل: {lead.phone}\n"
        f"شهر: {lead.city}\n"
        f"مسیر: {lead.get_path_display()}\n"
        f"سرمایه: {lead.get_budget_display()}"
    )
    url = api.format(token=token)
    for chat_id in chats:
        threading.Thread(target=_send, args=(url, chat_id, text), daemon=True).start()
