#!/usr/bin/env python
"""
    django_accounts.registration.urls
    ========================================

    urls for user registration

"""
from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from .views import RegisterView, VerifyEmailView


urlpatterns = patterns(
    '',
    url(r'^$', RegisterView.as_view(), name='rest_register'),
    url(r'^verify-email/$', VerifyEmailView.as_view(), name='rest_verify_email'),


    # We dont currently use this but:
    # This url is used by django-allauth and empty TemplateView is
    # defined just to allow reverse() call inside app, for example when email
    # with verification link is being sent, then it's required to render email
    # content.

    # account_confirm_email - You should override this view to handle it in
    # your API client somehow and then, send post to /verify-email/ endpoint
    # with proper key.
    # If you don't want to use API on that step, then just use ConfirmEmailView
    # view from:
    # from allauth.account.views import ConfirmEmailView
    # djang-allauth https://github.com/pennersr/django-allauth/blob/master/allauth/account/views.py#L190
    # url(r'^account-confirm-email/(?P<key>\w+)/$', ConfirmEmailView.as_view(),
    #    name='account_confirm_email'),

    # This URL will need to sort out by the frontend client
    # the frontend will need GET or POST to rest_verify_email
    url(r'^account-confirm-email/(?P<key>[-:\w]+)/$', TemplateView.as_view(),
        name='account_confirm_email'),
)
