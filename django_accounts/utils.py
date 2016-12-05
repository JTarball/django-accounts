#!/usr/bin/env python
"""
    django_accounts.utils
    =====================

    Common utility functions

"""
from six import string_types
import sys
if sys.version_info < (2, 7):
    from django.utils.importlib import import_module
else:
    from importlib import import_module

from django.contrib.auth import get_user_model


def import_callable(path_or_callable):
    if hasattr(path_or_callable, '__call__'):
        return path_or_callable
    else:
        assert isinstance(path_or_callable, string_types)
        package, attr = path_or_callable.rsplit('.', 1)
        return getattr(import_module(package), attr)


def email_address_exists(email, exclude_user=None):
    from allauth.account import app_settings as account_settings
    from allauth.account.models import EmailAddress

    emailaddresses = EmailAddress.objects
    if exclude_user:
        emailaddresses = emailaddresses.exclude(user=exclude_user)
    ret = emailaddresses.filter(email__iexact=email).exists()
    if not ret:
        email_field = account_settings.USER_MODEL_EMAIL_FIELD
        if email_field:
            users = get_user_model().objects
            if exclude_user:
                users = users.exclude(pk=exclude_user.pk)
            ret = users.filter(**{email_field+'__iexact': email}).exists()
    return ret
