import re

import jdatetime
from django.db.models import Count
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .models import Category, Magazine


def get_reading_minutes(text):
    word_count = len(re.findall(r'\w+', text))
    return max(1, word_count // 200)


def to_jalali_str(dt):
    if not dt: return ""
    return jdatetime.date.fromgregorian(date=dt.date()).strftime("%Y/%m/%d")


class MagazineListView(ListView):
    model = Magazine
    template_name = "blog/blog_list.html"
    context_object_name = "articles"
    paginate_by = 9

    def get_queryset(self):
        qs = (
            Magazine.objects.filter(
                status="published", published_at__lte=timezone.now()
            )
            .select_related("category", "writer")
            .order_by("-published_at", "-created_at")
        )
        category_id = self.request.GET.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["categories"] = Category.objects.annotate(
            article_count=Count("articles")
        ).filter(article_count__gt=0)

        context["articles_json"] = self.build_articles_data()
        return context

    def build_articles_data(self):
        articles = self.get_queryset()
        data = []
        for art in articles:
            data.append({
                "id": art.id,
                "slug": art.title.replace(" ", "-"),
                "title": art.title,
                "excerpt": art.summary or "",
                "image": art.cover_image.url if art.cover_image else "",
                "category": art.category.title if art.category else "",
                "author": "مجله ماشین پلاس",
                "authorRole": "مجله ماشین پلاس",
                "date": art.published_at.strftime("%Y-%m-%d") if art.published_at else "",
                "dateFa": to_jalali_str(art.published_at),
                "readingMinutes": get_reading_minutes(art.body),
                "tags": [tag.name for tag in art.tags.all()] if hasattr(art, 'tags') else [],
            })
        return data


class MagazineDetailView(DetailView):
    model = Magazine
    template_name = "blog/blog_detail.html"
    context_object_name = "article"

    def get_queryset(self):
        return Magazine.objects.filter(
            status="published", published_at__lte=timezone.now()
        ).select_related("category", "writer")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["article_json"] = self.build_article_data()
        context["related_articles_json"] = self.build_related_articles(limit=3)
        return context

    def build_article_data(self):
        art = self.object
        return {
            "id": art.id,
            "slug": art.title.replace(" ", "-"),
            "title": art.title,
            "excerpt": art.summary or "",
            "image": art.cover_image.url if art.cover_image else "",
            "category": art.category.title if art.category else "",
            "author": "مجله ماشین پلاس",
            "authorRole": "مجله ماشین پلاس",
            "date": art.published_at.strftime("%Y-%m-%d") if art.published_at else "",
            "dateFa": to_jalali_str(art.published_at),
            "readingMinutes": get_reading_minutes(art.body),
            "tags": [tag.name for tag in art.tags.all()] if hasattr(art, 'tags') else [],
            "body": [{
                "type": "html",
                "content": art.body
            }]
        }

    def build_related_articles(self, limit=3):
        current = self.object
        related_qs = (
            Magazine.objects.filter(
                status="published",
                published_at__lte=timezone.now(),
                category=current.category,
            )
            .exclude(pk=current.pk)
            .select_related("writer", "category")
            .order_by("-published_at")[:limit]
        )
        if not related_qs.exists():
            related_qs = (
                Magazine.objects.filter(
                    status="published", published_at__lte=timezone.now()
                )
                .exclude(pk=current.pk)
                .select_related("writer", "category")
                .order_by("-published_at")[:limit]
            )

        data = []
        for item in related_qs:
            writer_name = item.writer.get_full_name() or item.writer.username
            data.append(
                {
                    "id": item.id,
                    "slug": item.title.replace(" ", "-"),
                    "title": item.title,
                    "excerpt": item.summary or "",
                    "image": item.cover_image.url if item.cover_image else "",
                    "category": item.category.title if item.category else "",
                    "author": "مجله ماشین پلاس",
                    "authorRole": "مجله ماشین پلاس",
                    "date": item.published_at.strftime("%Y-%m-%d") if item.published_at else "",
                    "dateFa": to_jalali_str(item.published_at),
                    "readingMinutes": get_reading_minutes(item.body),
                    "tags": [tag.name for tag in item.tags.all()] if hasattr(item, 'tags') else [],
                }
            )

        return data
