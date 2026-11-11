from django.urls import path

from blog.views import MagazineListView, MagazineDetailView

app_name = 'blog'
urlpatterns = [
    path("", MagazineListView.as_view(), name="list"),
    path("<int:pk>/<str:title>", MagazineDetailView.as_view(), name="detail"),
]
