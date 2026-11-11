from django.db import models
from django.utils import timezone


class PublishedArticleManager(models.Manager):
    """
    Published shop manager.
    """

    def get_queryset(self):
        return super(PublishedArticleManager, self).get_queryset().filter(
            status='p', publish_time__lte=timezone.now()
        )
