from django.conf.urls import patterns, include, url

from django_accounts import urls as urls_django_accounts


urlpatterns = patterns('',
    url(r'^django_accounts/', include(urls_django_accounts, namespace="django_accounts")),
)
