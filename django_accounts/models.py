"""
    django_accounts.models
    ===========

    Models file for a basic Blog App

"""
import logging
import datetime
from dateutil import relativedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.template.defaultfilters import slugify

from utils import toTimeAgo


# Get instance of logger
logger = logging.getLogger('__name__')


class ExampleManager(models.Manager):
    use_for_related_fields = True

    def live(self):
        """ Returns all published blog articles. """
        return self.model.objects.filter(published=True)

    def by_year(self, year):
        return self.model.objects.filter(updated_at__year=year)

    def live_by_year(self, year):
        return self.model.objects.filter(updated_at__year=year, published=True)

    def by_tag(self, tag):
        return self.model.objects.filter(tags__name__in=[tag]).distinct()

    def live_by_tag(self, tag):
        return self.model.objects.filter(tags__name__in=[tag], published=True).distinct()

    def by_user(self, user):
        try:
            user_id = get_user_model().objects.get(username=user).id
        except:
            user_id = None
        return self.model.objects.filter(author_id=user_id)

    def live_by_user(self, user):
        try:
            user_id = get_user_model().objects.get(username=user).id
        except:
            user_id = None
        return self.model.objects.filter(author_id=user_id, published=True)


class Example(models.Model):
    """ Accounts Example Model. """
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    updated_ago = models.CharField(blank=True, max_length=255)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    # add our custom model manager
    objects = ExampleManager()

    def __unicode__(self):
        return self.title

    def timeAgo(self):
        return toTimeAgo(relativedelta.relativedelta(datetime.datetime.now(), self.updated_at))

    @models.permalink
    def get_absolute_url(self):
        return ("django_accounts:detail", (), {"slug": self.slug})

    def save(self, *args, **kwargs):
        self.updated_ago = self.timeAgo()
        if not self.slug:
            self.slug = slugify(self.title)
        super(Example, self).save(*args, **kwargs)
