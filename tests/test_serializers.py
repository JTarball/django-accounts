"""
    tests.test_serializers
    ======================

    Test Views for accounts App

    Tests the REST API calls.

    Add more specific serializer/validation tests

    registration is handled by allauth
"""
from collections import OrderedDict

from django.test import TestCase
from django.contrib.auth import get_user_model

from django_accounts.serializers import LoginSerializer
from allauth.account.models import EmailAddress
from allauth.account import app_settings
from django.conf import settings


# Temporary check - we only tests username authentication at the moment
if settings.ACCOUNT_AUTHENTICATION_METHOD != app_settings.AuthenticationMethod.USERNAME:
    raise NotImplementedError('Tests only support ACCOUNT_AUTHENTICATION_METHOD = "username"')


class LoginSerializerTests (TestCase):

    def setUp(self):
        self.email = 'jtarball@example.com'
        self.username = 'jtarball'
        self.password = 'password12'

        self.data = {
            'username': self.username,
            'password': self.password,
            'email': self.email,
        }
        # Create verified signup
        self.user = self._create_user(**self.data)
        self._create_email(self.user, self.data['email'])

    def _create_user(self, username, email, password):
        return get_user_model().objects.create_user(
            username,
            email,
            password
        )

    def _create_email(self, user, email, verified=True):
        return EmailAddress.objects.create(
            user=user,
            email=email,
            verified=verified,
            primary=True
        )

    def test_serializer(self):
        """ Basic Check of serializer. """
        serializer = LoginSerializer()
        expected = {
            'username': "",
            'password': "",
            'email': "",
        }

        self.assertEqual(serializer.data, expected)

    def test_serializer_only_username_password(self):
        """
        Tests we can validate/serializer with only username and password.
        We only require username and password for login for ACCOUNT_AUTHENTICATION_METHOD = 'username'
        """
        del self.data['email']
        serializer = LoginSerializer(data=self.data)
        self.assertEqual(serializer.is_valid(), True, serializer.errors)
        self.assertEqual(serializer.errors, {})
        self.assertEqual(
            serializer.validated_data,
            OrderedDict([
                (u'username', self.username),
                (u'password', self.password),
                ('user', self.user)
            ])
        )

    def test_serializer_added_email(self):
        serializer = LoginSerializer(data=self.data)
        self.assertEqual(serializer.is_valid(), True, serializer.errors)
        self.assertEqual(serializer.errors, {})
        self.assertEqual(
            serializer.validated_data,
            OrderedDict([
                (u'username', self.username),
                (u'email', self.email),
                (u'password', self.password),
                ('user', self.user)
            ])
        )

    def test_serializer_added_invalidate_email(self):
        self.data['email'] = 'jtarball'
        serializer = LoginSerializer(data=self.data)
        self.assertEqual(serializer.is_valid(), False, serializer.errors)
        self.assertEqual(
            serializer.errors,
            {'email': [u'Enter a valid email address.']}
        )
        self.assertEqual(serializer.validated_data, {})

    def test_serializer_added_incomplete_email(self):
        self.data['email'] = 'jtarball@example'
        serializer = LoginSerializer(data=self.data)
        self.assertEqual(serializer.is_valid(), False, serializer.errors)
        self.assertEqual(
            serializer.errors,
            {'email': [u'Enter a valid email address.']}
        )
        self.assertEqual(serializer.validated_data, {})

    def test_serializer_username_caps(self):
        data_caps = {
            'username': self.username.capitalize(),
            'password': self.password,
        }

        serializer = LoginSerializer(data=data_caps)
        self.assertEqual(serializer.is_valid(), True, serializer.errors)
        self.assertEqual(serializer.errors, {})
        self.assertEqual(
            serializer.validated_data,
            OrderedDict([
                (u'username', self.username.capitalize()),
                (u'password', self.password),
                ('user', self.user)
            ])
        )
