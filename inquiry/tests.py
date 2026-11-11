import json

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import normalize_phone
from .models import Lead

VALID = {"name": "علی رضایی", "phone": "۰۹۱۲ ۱۲۳ ۴۵۶۷", "city": "کرج", "path": "production", "budget": "p_5_10",
         "intro_watched": True, "path_watched": True, "utm_source": "instagram"}


class InquiryTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("inquiry:inquiry")

    def post(self, data, **extra):
        return self.client.post(self.url, json.dumps(data), content_type="application/json", **extra)

    def test_page_renders_with_csrf_cookie(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertIn("csrftoken", r.cookies)
        self.assertContains(r, "budgets-data")

    def test_valid_lead_saved_and_normalized(self):
        r = self.post(VALID)
        self.assertEqual(r.status_code, 201)
        lead = Lead.objects.get()
        self.assertEqual(lead.phone, "09121234567")
        self.assertEqual(lead.path, "production")
        self.assertTrue(lead.intro_watched)
        self.assertEqual(lead.utm_source, "instagram")

    def test_phone_normalization(self):
        for raw in ["+98 912 123 4567", "00989121234567", "9121234567", "۰۹۱۲۱۲۳۴۵۶۷"]:
            self.assertEqual(normalize_phone(raw), "09121234567")

    def test_field_errors_returned(self):
        r = self.post({**VALID, "phone": "123", "name": ""})
        self.assertEqual(r.status_code, 400)
        errs = r.json()["errors"]
        self.assertIn("phone", errs)
        self.assertIn("name", errs)

    def test_budget_must_match_path(self):
        r = self.post({**VALID, "path": "trading", "budget": "p_5_10"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("budget", r.json()["errors"])

    def test_same_phone_within_24h_updates_existing(self):
        self.post(VALID)
        r = self.post({**VALID, "path": "trading", "budget": "t_1_2b"})
        self.assertTrue(r.json()["repeat"])
        self.assertEqual(Lead.objects.count(), 1)
        lead = Lead.objects.get()
        self.assertEqual(lead.submissions, 2)
        self.assertEqual(lead.path, "trading")

    def test_honeypot_stores_nothing(self):
        r = self.post({**VALID, "website": "http://spam"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Lead.objects.count(), 0)

    @override_settings(INQUIRY_RATE_LIMIT=2)
    def test_rate_limit(self):
        from . import views
        views.RATE_LIMIT = 2
        try:
            self.post({**VALID, "phone": "09120000001"})
            self.post({**VALID, "phone": "09120000002"})
            r = self.post({**VALID, "phone": "09120000003"})
            self.assertEqual(r.status_code, 429)
        finally:
            views.RATE_LIMIT = 5

    def test_csrf_enforced(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        r = c.post(self.url, json.dumps(VALID), content_type="application/json")
        self.assertEqual(r.status_code, 403)
        c.get(self.url)
        token = c.cookies["csrftoken"].value
        r = c.post(self.url, json.dumps(VALID), content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r.status_code, 201)

    def test_bad_json(self):
        r = self.client.post(self.url, "not json", content_type="application/json")
        self.assertEqual(r.status_code, 400)
