from django.urls import path
from .views import home, contact_view, chatbot_view, inquiry_view, terms

app_name = "core"
urlpatterns = [
    path("", home, name="home"),
    path("inquiry/", inquiry_view, name="inquiry"),
    path("contact-us/", contact_view, name="contact-us"),
    path("terms/", terms, name="terms"),
    path("chat/", chatbot_view, name="chatbot"),
]
