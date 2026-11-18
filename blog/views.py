import re
import json
import jdatetime

from django.conf import settings
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView
from urllib.parse import urljoin

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

    def get_site_url(self):
        if settings.DEBUG:
            return self.request.build_absolute_uri("/").rstrip("/")

        return "https://machinplus.ir"

    def get_queryset(self):
        qs = (
            Magazine.objects.filter(
                status="published",
                published_at__lte=timezone.now()
            )
            .select_related("category", "writer")
            .prefetch_related("tags")
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

        articles = self.object_list

        context["articles_json"] = self.build_articles_data(articles)

        # SEO metadata
        site_url = self.get_site_url()
        magazine_url = urljoin(
            f"{site_url}/",
            reverse("blog:list").lstrip("/")
        )

        context["seo_title"] = (
            "مجله صنعت | مقالات ماشین‌آلات و تجهیزات — ماشین پلاس"
        )
        context["seo_description"] = (
            "مقالات تخصصی درباره خرید ماشین‌آلات صنعتی، نگهداری و تعمیرات، "
            "تحلیل بازار و فناوری‌های نوین تولید به زبان فارسی."
        )
        context["seo_type"] = "website"
        context["seo_url"] = magazine_url

        # JSON-LD
        collection_data = self.build_collection_json_ld(
            articles=articles,
            magazine_url=magazine_url,
        )

        serialized_data = json.dumps(collection_data, ensure_ascii=False)
        serialized_data = (
            serialized_data
            .replace("<", "\\u003C")
            .replace(">", "\\u003E")
            .replace("&", "\\u0026")
        )

        context["collection_json_ld"] = serialized_data

        return context

    def build_articles_data(self, articles):
        data = []

        site_url = self.get_site_url()

        for art in articles:
            image_url = ""

            if art.cover_image:
                image_url = urljoin(
                    f"{site_url}/",
                    art.cover_image.url.lstrip("/")
                )

            data.append({
                "id": art.id,
                "slug": art.slug,
                "title": art.title,
                "excerpt": art.summary or "",
                "image": image_url,
                "category": art.category.title if art.category else "",
                "author": "مجله ماشین پلاس",
                "authorRole": "مجله ماشین پلاس",
                "date": (
                    art.published_at.strftime("%Y-%m-%d")
                    if art.published_at else ""
                ),
                "dateFa": (
                    to_jalali_str(art.published_at)
                    if art.published_at else ""
                ),
                "readingMinutes": get_reading_minutes(art.body),
                "tags": [tag.name for tag in art.tags.all()],
            })

        return data

    def build_collection_json_ld(self, articles, magazine_url):
        site_url = self.get_site_url()

        item_list = []

        visible_articles = articles[:6]

        for position, article in enumerate(visible_articles, start=1):
            article_path = reverse(
                "blog:detail",
                kwargs={"slug": article.slug}
            )

            article_url = urljoin(
                f"{site_url}/",
                article_path.lstrip("/")
            )

            article_data = {
                "@type": "BlogPosting",
                "@id": f"{article_url}#article",
                "url": article_url,
                "headline": article.title,
            }

            if article.summary:
                article_data["description"] = article.summary

            if article.cover_image:
                article_data["image"] = urljoin(
                    f"{site_url}/",
                    article.cover_image.url.lstrip("/")
                )

            item_list.append({
                "@type": "ListItem",
                "position": position,
                "item": article_data,
            })

        return {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "@id": f"{magazine_url}#collection",
            "url": magazine_url,
            "name": "مجله صنعت | ماشین پلاس",
            "description": (
                "مقالات تخصصی درباره خرید ماشین‌آلات صنعتی، "
                "نگهداری و تعمیرات و فناوری‌های نوین تولید."
            ),
            "inLanguage": "fa-IR",
            "isPartOf": {
                "@id": f"{site_url}/#website"
            },
            "publisher": {
                "@id": f"{site_url}/#organization"
            },
            "mainEntity": {
                "@type": "ItemList",
                "@id": f"{magazine_url}#article-list",
                "itemListOrder": "https://schema.org/ItemListOrderDescending",
                "numberOfItems": len(item_list),
                "itemListElement": item_list,
            },
        }


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

        article = self.object

        context["article_json"] = self.build_article_data()
        context["related_articles_json"] = self.build_related_articles(limit=3)

        context["seo_title"] = article.title
        context["seo_description"] = article.summary or article.title
        context["seo_type"] = "article"
        context["seo_url"] = self.request.build_absolute_uri()

        context["seo_image"] = (
            self.request.build_absolute_uri(article.cover_image.url)
            if article.cover_image
            else ""
        )

        context["seo_published_time"] = article.published_at
        context["seo_modified_time"] = article.updated_at

        article_url = self.request.build_absolute_uri(
            reverse("blog:detail", kwargs={"slug": article.slug})
        )

        context["article_json_ld"] = self.build_article_json_ld(
            article=article,
            article_url=article_url,
        )

        context["breadcrumb_json_ld"] = self.build_breadcrumb_json_ld(
            article=article,
            article_url=article_url,
        )

        return context

    def build_article_data(self):
        art = self.object
        return {
            "id": art.id,
            "slug": art.slug,
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
                    "slug": item.slug,
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

    def build_article_json_ld(self, article, article_url):
        writer_name = (
                article.writer.get_full_name().strip()
                or article.writer.username
        )

        description = article.summary or article.title

        data = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "@id": f"{article_url}#article",
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": article_url,
            },
            "headline": article.title,
            "description": description,
            "inLanguage": "fa-IR",
            "author": {
                "@type": "Person",
                "name": writer_name,
            },
            "publisher": {
                "@id": "https://machinplus.ir/#organization"
            },
        }

        if article.cover_image:
            data["image"] = [
                self.request.build_absolute_uri(article.cover_image.url)
            ]

        if article.published_at:
            data["datePublished"] = article.published_at.isoformat()

        if article.updated_at:
            data["dateModified"] = article.updated_at.isoformat()

        return data

    def build_breadcrumb_json_ld(self, article, article_url):
        magazine_url = self.request.build_absolute_uri(
            reverse("blog:list")
        )

        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "@id": f"{article_url}#breadcrumb",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "خانه",
                    "item": "https://machinplus.ir/",
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "مجله",
                    "item": magazine_url,
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": article.title,
                    "item": article_url,
                },
            ],
        }
