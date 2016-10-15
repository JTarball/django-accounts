"""
    django_accounts.test_models.py
    ==========================

    Test Models for Blog App
    - ensure model integrity
    - permissions for models work correctly
"""
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse

from django_dynamic_fixture import G
from django_dynamic_fixture.ddf import BadDataError
from rest_framework.test import APIClient, APITestCase

from tests.models import AccountsUser


class AccountsModelTests(APITestCase):

    def setUp(self):
        self.user = G(AccountsUser, is_superuser=False, is_staff=False)
        self.staff = G(AccountsUser, is_superuser=False, is_staff=True)
        self.superadmin = G(AccountsUser, is_superuser=True, is_staff=True)
        self.superadmin_not_staff = G(AccountsUser, is_superuser=True, is_staff=False)
        self.client = APIClient()

    def test_model_example(self):
        """ Example of model test for django_accounts app. """
        #example = G(Example, content="This is a test example.", author=self.staff)
        self.assertEquals(True, True, "This shouldnt happen!")
