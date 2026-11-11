from django.urls import path

from .views import InquiryView

app_name = "inquiry"

urlpatterns = [
    path("", InquiryView.as_view(), name="inquiry"),  # GET page, POST JSON lead
]
