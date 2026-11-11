import re

from django import forms

from .models import BUDGETS_BY_PATH, Lead

_FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_phone(value: str) -> str:
    """'+98 912 123 4567', '۰۹۱۲۱۲۳۴۵۶۷', '9121234567' -> '09121234567'."""
    digits = re.sub(r"\D", "", (value or "").translate(_FA))
    if digits.startswith("0098"):
        digits = digits[4:]
    elif digits.startswith("98"):
        digits = digits[2:]
    if len(digits) == 10 and digits.startswith("9"):
        digits = "0" + digits
    return digits


class LeadForm(forms.Form):
    name = forms.CharField(max_length=120, error_messages={"required": "نام را وارد کنید."})
    phone = forms.CharField(max_length=20, error_messages={"required": "شماره موبایل را وارد کنید."})
    city = forms.CharField(max_length=60, error_messages={"required": "شهر را وارد کنید."})
    path = forms.ChoiceField(choices=Lead.Path.choices, error_messages={"required": "مسیر را انتخاب کنید.", "invalid_choice": "مسیر نامعتبر است."})
    budget = forms.ChoiceField(choices=Lead.Budget.choices, error_messages={"required": "بازه سرمایه را انتخاب کنید.", "invalid_choice": "بازه سرمایه نامعتبر است."})

    intro_watched = forms.BooleanField(required=False)
    path_watched = forms.BooleanField(required=False)
    utm_source = forms.CharField(max_length=100, required=False)
    utm_medium = forms.CharField(max_length=100, required=False)
    utm_campaign = forms.CharField(max_length=100, required=False)
    referrer = forms.CharField(max_length=500, required=False)

    # honeypot: real users never see or fill this
    website = forms.CharField(required=False)

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if len(name) < 2:
            raise forms.ValidationError("نام را حداقل با ۲ حرف وارد کنید.")
        return name

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data["phone"])
        if not re.fullmatch(r"09\d{9}", phone):
            raise forms.ValidationError("شماره موبایل باید ۱۱ رقم و با ۰۹ شروع شود.")
        return phone

    def clean_city(self):
        return " ".join(self.cleaned_data["city"].split())

    def clean_referrer(self):
        ref = self.cleaned_data.get("referrer", "")
        return ref if ref.startswith(("http://", "https://")) else ""

    def clean(self):
        data = super().clean()
        path, budget = data.get("path"), data.get("budget")
        if path and budget and budget not in BUDGETS_BY_PATH[path]:
            self.add_error("budget", "این بازه سرمایه با مسیر انتخابی جور نیست.")
        return data
