from django.urls import path

from blog.views import MagazineListView, MagazineDetailView

app_name = 'blog'
urlpatterns = [
    path("", MagazineListView.as_view(), name="list"),
    path("<persian_slug:slug>/", MagazineDetailView.as_view(), name="detail"),
]
