#!/usr/bin/env python
"""
    django_accounts.app_settings
    ============================

    Add some app specific settings

"""


class AppSettings(object):

    def __init__(self, prefix):
        self.prefix = prefix

    def _setting(self, name, dflt):
        from django.conf import settings
        getter = getattr(settings,
                         'ACCOUNTS_SETTING_GETTER',
                         lambda name, dflt: getattr(settings, name, dflt))
        return getter(self.prefix + name, dflt)

    @property
    def REGISTRATION_OPEN(self):
        """
        Gets settings REGISTRATION_OPEN. It defines whether registration is allowed.
        Defaults to True if setting doesnt exist.
        """
        return self._setting('REGISTRATION_OPEN', True)  # Defaults to True (if doesnt exist)


# Ugly? Guido recommends this himself ...
# http://mail.python.org/pipermail/python-ideas/2012-May/014969.html
import sys
app_settings = AppSettings('ACCOUNTS_')
app_settings.__name__ = __name__
sys.modules[__name__] = app_settings