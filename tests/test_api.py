"""
    tests.test_views.py
    ==================

    Test Views for accounts App

    Tests the REST API calls.

    Add more specific social registration tests
"""
import datetime

import responses
import copy
from freezegun import freeze_time
import pytest
from django_dynamic_fixture import G

from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from django.utils.timezone import now

from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from allauth.account import app_settings
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.facebook.provider import GRAPH_API_URL
from allauth.account.models import EmailAddress, EmailConfirmation, EmailConfirmationHMAC

from django_accounts.models import AccountsUser
from django_accounts.serializers import LoginSerializer

from django.conf import settings


######
# ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_USERNAME_REQUIRED = True
# ACCOUNT_EMAIL_VERIFICATION = "mandatory"
# ACCOUNT_AUTHENTICATION_METHOD = "username"
# ACCOUNT_EMAIL_CONFIRMATION_HMAC = True
# # Note if set to true - tests will fail as we need to recreate db every test
# ACCOUNT_UNIQUE_EMAIL = False
# ACCOUNT_ADAPTER = "django_accounts.adapter.DefaultAccountAdapter"

# AUTH_USER_MODEL = 'django_accounts.AccountsUser'
# REGISTRATION_OPEN = True
# ACCOUNT_AUTHENTICATION_METHOD = "username"


class EmailConfirmationTests(APITestCase):
    """
    Tests Email Confirmation

    tests confirmation of email

    ACCOUNT_EMAIL_CONFIRMATION_HMAC (=True)
    In order to verify an email address a key is mailed identifying the email
    address to be verified. In previous versions, a record was stored in the
    database for each ongoing email confirmation, keeping track of these keys.
    Current versions use HMAC based keys that do not require server side state.
    """
    def setUp(self):
        self.verify_url = reverse('accounts:rest_verify_email')

        self.client = APIClient()

        self.reusable_user_data = {
            'username': 'admin',
            'email': 'admin@email.com',
            'password': 'password12'
        }
        self.reusable_email = 'admin@email.com'
        self.reusable_register_user_data = {
            'username': 'admin',
            'email': self.reusable_email,
            'password1': 'password12',
            'password2': 'password12'
        }
        self.resuable_login_data = {
            'username': 'admin', 'password': 'password12'
        }

    ############################################################################
    # Helper Functions
    ############################################################################
    def _create_user(self):
        return get_user_model().objects.create_user(
            'admin',
            'admin@email.com',
            'password12'
        )

    def _create_email(self, user):
        return EmailAddress.objects.create(
            user=user,
            email='admin@email.com',
            verified=False,
            primary=True
        )
    ############################################################################

    @override_settings(ACCOUNT_EMAIL_CONFIRMATION_HMAC=True)
    def test_hmac(self):
        """ Tests Verification of User with HMAC. """
        user = self._create_user()
        email = self._create_email(user)
        confirmation = EmailConfirmationHMAC(email)
        confirmation.send()
        self.assertEqual(len(mail.outbox), 1)

        response = self.client.post(
            self.verify_url,
            {'key': confirmation.key},
            format='json'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        email = EmailAddress.objects.get(pk=email.pk)
        self.assertTrue(email.verified)

    @override_settings(
        ACCOUNT_EMAIL_CONFIRMATION_HMAC=True,
        ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS=0,
    )
    def test_hmac_confirmation_closed(self):
        """ Test Verification Fails if Expiration has timed out.
            HMAC signing will fail if expired
        """
        user = self._create_user()
        email = self._create_email(user)
        confirmation = EmailConfirmationHMAC(email)
        confirmation.send()
        self.assertEqual(len(mail.outbox), 1)

        response = self.client.post(
            self.verify_url,
            {'key': confirmation.key},
            format='json'
        )
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
        email = EmailAddress.objects.get(pk=email.pk)
        self.assertFalse(email.verified)

    @override_settings(
        ACCOUNT_EMAIL_CONFIRMATION_HMAC=True,
    )
    def test_hmac_fall_back(self):
        """ Tests Verification of User with HMAC off.
        The key for verification is recorded in the db.
        """
        user = self._create_user()
        email = self._create_email(user)

        confirmation = EmailConfirmation.create(email)
        confirmation.sent = now()
        confirmation.send()

        self.assertEqual(len(mail.outbox), 1)

        response = self.client.post(
            self.verify_url,
            {'key': confirmation.key},
            format='json'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        email = EmailAddress.objects.get(pk=email.pk)
        self.assertTrue(email.verified)


class EmailVerificationTests(APITestCase):
    """
    Tests Email Verification

    you must verify the email by clicking the email link before logging in
    depending on ACCOUNT_EMAIL_VERIFICATION

    ACCOUNT_EMAIL_VERIFICATION (='optional')
    Determines the e-mail verification method during signup  choose one of
    'mandatory', 'optional', or 'none'. When set to 'mandatory' the user is
    blocked from logging in until the email address is verified. Choose
    'optional' or 'none' to allow logins with an unverified e-mail address.
    In case of 'optional', the e-mail verification mail is still sent, whereas
    in case of 'none' no e-mail verification mails are sent.
    """
    def setUp(self):
        self.register_url = reverse('accounts:rest_register')
        self.verify_url = reverse('accounts:rest_verify_email')
        self.login_url = reverse('accounts:rest_login')

        self.client = APIClient()

        self.reusable_email = 'admin@email.com'
        self.reusable_user_data = {
            'username': 'admin',
            'email': self.reusable_email,
            'password': 'password12'
        }
        self.reusable_register_user_data = {
            'username': 'admin',
            'email': self.reusable_email,
            'password1': 'password12',
            'password2': 'password12'
        }
        self.resuable_login_data = {
            'username': 'admin', 'password': 'password12'
        }

    ############################################################################
    # Helper Functions
    ############################################################################
    def _signup_user(self):
        response = self.client.post(
            self.register_url,
            self.reusable_register_user_data,
            format='json'
        )
        self.assertEquals(
            response.status_code,
            status.HTTP_201_CREATED,
            response.content
        )
        return response

    def _login_user(self, check_ok_response=True):
        response = self.client.post(
            self.login_url,
            self.resuable_login_data,
            format='json'
        )
        if check_ok_response:
            self.assertEquals(response.status_code, status.HTTP_200_OK)
        return response
    ############################################################################

    @override_settings(ACCOUNT_EMAIL_VERIFICATION="none")
    def test_verification_none(self):
        """ Tests verification is not needed when no-email verifications mails are sent. """
        # when email verification is set to "none" no verification emails will be sent.
        # Allowed to log in with unverified email
        mail_count = len(mail.outbox)
        self._signup_user()
        self.assertEqual(len(mail.outbox), mail_count)

        self._login_user()

    @override_settings(ACCOUNT_EMAIL_VERIFICATION="optional")
    def test_verification_optional(self):
        """ Tests verification is not needed when email verification is optional. """
        # when email verification is set to "optional" a verification email will be sent.
        # Allowed to log in with unverified email
        mail_count = len(mail.outbox)
        self._signup_user()
        self.assertEqual(len(mail.outbox), mail_count + 1)

        self._login_user()

    @override_settings(ACCOUNT_EMAIL_VERIFICATION="mandatory")
    def test_verification_mandatory(self):
        """ Tests verification is mandatory. """
        # when email verification is set to "mandatory" a verification email will be sent.
        # NOT allowed to log in with unverified email
        mail_count = len(mail.outbox)
        self._signup_user()
        self.assertEqual(len(mail.outbox), mail_count + 1)

        response = self._login_user(check_ok_response=False)
        self.assertEquals(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.content
        )
        self.assertEquals(
            response.content,
            '{"non_field_errors":["E-mail is not verified."]}'
        )

    @override_settings(ACCOUNT_EMAIL_VERIFICATION="mandatory")
    def test_verification_mandatory_get_verify_ok(self):
        """ Tests verification is mandatory. """
        # when email verification is set to "mandatory" a verification email will be sent.
        # NOT allowed to log in with unverified email
        mail_count = len(mail.outbox)
        self._signup_user()
        self.assertEqual(len(mail.outbox), mail_count + 1)

        response = self._login_user(check_ok_response=False)
        self.assertEquals(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.content
        )
        self.assertEquals(
            response.content,
            '{"non_field_errors":["E-mail is not verified."]}'
        )


class TestRegistrations(APITestCase):
    """
    Tests Registration.

    Signup of an user.

    Assumes:
    ACCOUNT_AUTHENTICATION_METHOD = "username"


    Custom App Configuration
    ========================
    ACCOUNTS_REGISTRATION_OPEN
    Specifies whether registration is allowed.

    AllAuth Configuration
    =====================
    ACCOUNT_USERNAME_REQUIRED (=True)
    The user is required to enter a username when signing up. Note that the user
    will be asked to do so even if ACCOUNT_AUTHENTICATION_METHOD is set to email.S
    et to False when you do not wish to prompt the user to enter a username.

    ACCOUNT_EMAIL_REQUIRED (=False)
    The user is required to hand over an e-mail address when signing up.

    ACCOUNT_UNIQUE_EMAIL (=True)
    Enforce uniqueness of e-mail addresses. The emailaddress.email model field
    is set to UNIQUE. Forms prevent a user from registering with or adding an
    additional email address if that email address is in use by another account.

    """
    def setUp(self):
        self.login_url = reverse('accounts:rest_login')
        self.logout_url = reverse('accounts:rest_logout')
        self.register_url = reverse('accounts:rest_register')
        self.password_reset_url = reverse('accounts:rest_password_reset')
        self.rest_password_reset_confirm_url = reverse('accounts:rest_password_reset_confirm')
        self.password_change_url = reverse('accounts:rest_password_change')
        self.verify_url = reverse('accounts:rest_verify_email')
        self.user_url = reverse('accounts:rest_user_details')
        self.client = APIClient()
        self.reusable_user_data = {'username': 'admin', 'email': 'admin@email.com', 'password': 'password12'}
        self.reusable_user_data_change_password = {'username': 'admin', 'email': 'admin@email.com', 'password': 'password_same'}
        self.reusable_register_user_data = {'username': 'admin', 'email': 'admin@email.com', 'password1': 'password12', 'password2': 'password12'}
        self.resuable_login_data = {'username': 'admin', 'password': 'password12'}

        self.reusable_register_user_data_different_email = {'username': 'admin', 'email': 'admin@email.com', 'password1': 'password12', 'password2': 'password12'}
        self.reusable_register_user_data_different_username = {'username': 'admin1', 'email': 'admin@email.com', 'password1': 'password12', 'password2': 'password12'}
        self.reusable_register_user_data_no_username = {'email': 'admin@email.com', 'password1': 'password12', 'password2': 'password12'}
        self.reusable_register_user_data_no_email = {'username': 'admin', 'password1': 'password12', 'password2': 'password12'}
        self.change_password_data_incorrect = {"password1": "password_not_same", "password2": "password_same"}
        self.change_password_data = {"password1": "password_same", "password2": "password_same"}
        self.change_password_data_old_password_field_enabled = {"old_password": "password12", "password1": "password_same", "password2": "password_same"}



        self.reusable_username = 'user_new'
        self.reusable_user_pass = 'password12'
        self.reusable_email = 'admin@email.com'

        self.reusable_register_signup = {
            'username': self.reusable_username,
            'email': self.reusable_email,
            'password1': self.reusable_user_pass,
            'password2': self.reusable_user_pass
        }

    def tearDown(self):
        print "tearDown"
        return super(TestRegistrations, self).tearDown()
        get_user_model().objects.all().delete()

    def create_verified_signed_up_reusable_user(self):
            user = get_user_model().objects.create(username=self.reusable_username)
            user.set_password(self.reusable_user_pass)
            user.save()
            EmailAddress.objects.create(
                user=user,
                email=self.reusable_email,
                primary=True,
                verified=True
            )

    def common_test_registration_ok(self, data):
        response = self.client.post(self.register_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_201_CREATED, response.content)
        return response

    def common_test_registration_400(self, data, check_content):
        response = self.client.post(self.register_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
        self.assertEquals(response.content, check_content)
        return response

    # Basic registration tests
    # ========================
    @override_settings(ACCOUNTS_REGISTRATION_OPEN=True)
    def test_registration(self):
        """ Tests basic registration. """
        self.common_test_registration_ok(self.reusable_register_signup)

    @override_settings(ACCOUNT_USERNAME_REQUIRED=True)
    def test_registration_username_missing_and_is_required(self):
        """ Tests username is required during registration when ACCOUNT_USERNAME_REQUIRED is set. """
        self.reusable_register_signup['username'] = ''
        self.common_test_registration_400(
            self.reusable_register_signup,
            '{"username":["This field is required."]}'
        )

    @override_settings(ACCOUNT_USERNAME_REQUIRED=False)
    def test_registration_username_missing(self):
        """ Tests username is not required during registration when ACCOUNT_USERNAME_REQUIRED is False. """
        self.reusable_register_signup['username'] = ''
        self.common_test_registration_ok(self.reusable_register_signup)

    @override_settings(ACCOUNT_EMAIL_REQUIRED=True)
    def test_registration_email_missing_and_is_required(self):
        """ Tests email is required during registration when ACCOUNT_EMAIL_REQUIRED is set. """
        self.reusable_register_signup['email'] = ''
        self.common_test_registration_400(
            self.reusable_register_signup,
            '{"email":["This field is required."]}'
        )

    @override_settings(ACCOUNT_EMAIL_REQUIRED=False)
    def test_registration_email_missing(self):
        """ Tests email is not required during registration when ACCOUNT_EMAIL_REQUIRED is False. """
        self.reusable_register_signup['email'] = ''
        self.common_test_registration_ok(self.reusable_register_signup)

    @override_settings(ACCOUNT_UNIQUE_EMAIL=True)
    def test_registration_email_needs_to_be_unique(self):
        """ Tests registration needs an unique email when ACCOUNT_UNIQUE_EMAIL is set. """
        self.create_verified_signed_up_reusable_user()

        self.reusable_register_signup['username'] = 'different_username'
        self.common_test_registration_400(
            self.reusable_register_signup,
            '{"email":["A user is already registered with this e-mail address."]}'
        )

    # @override_settings(ACCOUNT_UNIQUE_EMAIL=False)
    # def test_registration_email_does_not_need_to_be_unique(self):
    #     """ Tests registration does NOT needs an unique email when ACCOUNT_UNIQUE_EMAIL is False. """
    #     self.create_verified_signed_up_reusable_user()

    #     self.reusable_register_signup['username'] = 'different_username'
    #     self.common_test_registration_ok(self.reusable_register_signup)

    @override_settings(ACCOUNT_EMAIL_REQUIRED=True, ACCOUNT_USERNAME_REQUIRED=True)
    def test_registration_email_and_username_required(self):
        """ Tests email and username is required for registration. """
        self.reusable_register_signup['username'] = ''
        self.reusable_register_signup['email'] = ''
        self.common_test_registration_400(
            self.reusable_register_signup,
            '{"username":["This field is required."],"email":["This field is required."]}'
        )

    @override_settings(ACCOUNTS_REGISTRATION_OPEN=False)
    def test_registration_basic_registration_not_open(self):
        """ Tests basic registration fails if registration is closed. """
        self.common_test_registration_400(
            self.reusable_register_signup,
            '{"message":"Registration is current closed. Please try again soon."}'
        )


class TestPasswordResets(APITestCase):
    def setUp(self):
        self.login_url = reverse('accounts:rest_login')
        self.password_reset_url = reverse('accounts:rest_password_reset')
        self.rest_password_reset_confirm_url = reverse('accounts:rest_password_reset_confirm')
        self.client = APIClient()

        self.email = 'jtarball@example.com'
        self.username = 'jtarball'
        self.password = 'password12'

        self.data = {
            'username': self.username,
            'password': self.password,
            'email': self.email,
        }

        self.user = self._create_verified_user()

    def _generate_uid_and_token(self, user):
        result = {}
        from django.utils.encoding import force_bytes
        from django.contrib.auth.tokens import default_token_generator
        from django import VERSION
        if VERSION[1] == 5:
            from django.utils.http import int_to_base36
            result['uid'] = int_to_base36(user.pk)
        else:
            from django.utils.http import urlsafe_base64_encode
            result['uid'] = urlsafe_base64_encode(force_bytes(user.pk))
        result['token'] = default_token_generator.make_token(user)
        return result

    def _create_verified_user(self):
        user = get_user_model().objects.create_user(**self.data)
        EmailAddress.objects.create(
            user=user,
            email=self.email,
            verified=True,
            primary=True
        )
        return user

    """
        Password Reset Tests
        ====================
    """
    def test_password_reset(self):
        """ Test basic functionality of password reset. """
        initial_mail_count = len(mail.outbox)
        response = self.client.post(self.password_reset_url, {'email': self.email}, format='json')

        self.assertEqual(len(mail.outbox), initial_mail_count + 1)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.content, '{"success":"Password reset e-mail has been sent."}')

    def test_password_reset_user_not_in_system(self):
        """ Test basic functionality of password reset fails when there is no email (user) on record. """
        payload = {'email': 'admin@email.com'}
        response = self.client.post(self.password_reset_url, payload, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(response.content, '{"email":["Validation Error {\'email\': [u\'The e-mail address is not assigned to any user account\']}"]}')

    # Password Reset Confirm
    # ======================
    def test_password_reset_confirm_login(self):
        """ Tests password reset confirm works -> can login afterwards. """
        url_kwargs = self._generate_uid_and_token(self.user)
        data = {
            'password1': 'new_password',
            'password2': 'new_password',
            'uid': url_kwargs['uid'],
            'token': url_kwargs['token']
        }
        response = self.client.post(self.rest_password_reset_confirm_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.data['password'] = 'new_password'
        response = self.client.post(self.login_url, self.data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_password_reset_confirm_fail_invalid_token(self):
        """ Test password reset confirm fails if token is invalid. """
        url_kwargs = self._generate_uid_and_token(self.user)
        data = {
            'password1': 'new_password',
            'password2': 'new_password',
            'uid': url_kwargs['uid'],
            'token': '-wrong-token-'
        }
        response = self.client.post(self.rest_password_reset_confirm_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(response.content, '{"token":["Invalid value"]}')

    def test_password_reset_confirm_fail_invalid_uid(self):
        """ Test password reset confirm fails if uid is invalid. """
        url_kwargs = self._generate_uid_and_token(self.user)
        data = {
            'password1': 'new_password',
            'password2': 'new_password',
            'uid': 0,
            'token': url_kwargs['token']
        }
        response = self.client.post(self.rest_password_reset_confirm_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(response.content, '{"uid":["Invalid value"]}')

    def test_password_reset_confirm_fail_passwords_not_the_same(self):
        """ Test password reset confirm fails if passwords are not the same. """
        url_kwargs = self._generate_uid_and_token(self.user)
        data = {
            'password1': 'new_password',
            'password2': 'new_not_the_same_password',
            'uid': url_kwargs['uid'],
            'token': url_kwargs['token']
        }
        response = self.client.post(self.rest_password_reset_confirm_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(response.content, '{"password2":["You must type the same password each time."]}')

    def test_password_reset_confirm_login_fails_with_old_password(self):
        """ Tests password reset confirm fails login with old password. """
        url_kwargs = self._generate_uid_and_token(self.user)
        data = {
            'password1': 'new_password',
            'password2': 'new_password',
            'uid': url_kwargs['uid'],
            'token': url_kwargs['token']
        }
        response = self.client.post(self.rest_password_reset_confirm_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK, response.content)
        response = self.client.post(self.login_url, self.data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestLogins(APITestCase):
    """ Tests login functionality. """
    def setUp(self):
        self.login_url = reverse('accounts:rest_login')
        self.logout_url = reverse('accounts:rest_logout')
        self.client = APIClient()

        self.email = 'jtarball@example.com'
        self.username = 'jtarball'
        self.password = 'password12'

        self.data = {
            'username': self.username,
            'password': self.password,
            'email': self.email,
        }

        self.user = self._create_verified_user()

    def _create_verified_user(self):
        user = get_user_model().objects.create_user(**self.data)
        EmailAddress.objects.create(
            user=user,
            email=self.email,
            verified=True,
            primary=True
        )
        return user

    @override_settings(
        ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.EMAIL,
        ACCOUNT_EMAIL_VERIFICATION="none"
    )
    def test_login_account_authentication_method_email(self):
        """ Tests authentication is email works when AUTHENTICATION_AUTHENTICATION_METHOD is set to email. """
        response = self.client.post(
            self.login_url,
            {'email': self.email, 'password': self.password},
            format='json'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    @override_settings(
        ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.EMAIL,
        ACCOUNT_EMAIL_VERIFICATION="none"
    )
    def test_login_account_authentication_method_email_username_attempted(self):
        """ Tests authentication is not username when AUTHENTICATION_AUTHENTICATION_METHOD is set to email. """
        response = self.client.post(
            self.login_url,
            {'username': self.username, 'password': self.password},
            format='json'
        )
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(response.content, '{"non_field_errors":["Must include \\"email\\" and \\"password\\"."]}')

    @override_settings(
        ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.USERNAME,
        ACCOUNT_EMAIL_VERIFICATION="none"
    )
    def test_login_account_authentication_method_username(self):
        response = self.client.post(
            self.login_url,
            {'username': self.username, 'password': self.password},
            format='json'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    @override_settings(
        ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.USERNAME,
        ACCOUNT_EMAIL_VERIFICATION="none"
    )
    def test_login_account_authentication_method_username_email_attempted(self):
        response = self.client.post(
            self.login_url,
            {'email': self.email, 'password': self.password},
            format='json'
        )
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(
            response.content,
            '{"non_field_errors":["Must include \\"username\\" and \\"password\\"."]}'
        )

    @override_settings(
        ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.USERNAME_EMAIL,
        ACCOUNT_EMAIL_VERIFICATION="none"
    )
    def test_registration_account_authentication_method_username_email(self):
        response = self.client.post(
            self.login_url,
            {'email': self.email, 'password': self.password},
            format='json'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        response = self.client.post(self.logout_url, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            self.login_url,
            {'username': self.username, 'password': self.password},
            format='json'
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)














class TestNormalUseCases(APITestCase):
    """ Tests normal use - non social login. """

    def setUp(self):
        self.login_url = reverse('accounts:rest_login')
        self.logout_url = reverse('accounts:rest_logout')
        self.register_url = reverse('accounts:rest_register')
        self.password_reset_url = reverse('accounts:rest_password_reset')
        self.rest_password_reset_confirm_url = reverse('accounts:rest_password_reset_confirm')
        self.password_change_url = reverse('accounts:rest_password_change')
        self.verify_url = reverse('accounts:rest_verify_email')
        self.user_url = reverse('accounts:rest_user_details')
        self.client = APIClient()
        self.reusable_user_data = {'username': 'admin', 'email': 'admin@email.com', 'password': 'password12'}
        self.reusable_user_data_change_password = {'username': 'admin', 'email': 'admin@email.com', 'password': 'password_same'}
        self.reusable_register_user_data = {'username': 'admin', 'email': 'admin@email.com', 'password1': 'password12', 'password2': 'password12'}
        self.reusable_register_user_data1 = {'username': 'admin1', 'email': 'admin1@email.com', 'password1': 'password12', 'password2': 'password12'}
        self.reusable_register_user_data_no_username = {'email': 'admin@email.com', 'password1': 'password12', 'password2': 'password12'}
        self.reusable_register_user_data_no_email = {'username': 'admin', 'password1': 'password12', 'password2': 'password12'}
        self.change_password_data_incorrect = {"password1": "password_not_same", "password2": "password_same"}
        self.change_password_data = {"password1": "password_same", "password2": "password_same"}
        self.change_password_data_old_password_field_enabled = {"old_password": "password12", "password1": "password_same", "password2": "password_same"}

    def create_user_and_login(self):
        """ Helper function to create a basic user, login and assign token credentials. """
        user = get_user_model().objects.create_user('admin', 'admin@email.com', 'password12')
        EmailAddress.objects.create(
            user=user,
            email='admin@email.com',
            verified=True,
            primary=True
        )
        response = self.client.post(self.login_url, self.reusable_user_data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK, "Snap! Basic Login has failed with a helper function 'create_user_and_login'. Something is really wrong here.")
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + response.data['key'])



    def cleanUp(self):
        pass

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.USERNAME)
    def test_login_basic_username_auth_method(self):
        """ Tests basic functionality of login with authentication method of username. """
        # Assumes you provide username,password and returns a token
        user = get_user_model().objects.create_user('admin3', '', 'password12')
        EmailAddress.objects.create(
            user=user,
            email="",
            verified=True,
            primary=True
        )
        data = {"username": 'admin3', "email": "", "password": 'password12'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertIn('key', response.content)

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.EMAIL,
                       ACCOUNT_EMAIL_REQUIRED=True)
    def test_login_basic_email_auth_method(self):
        """ Tests basic functionality of login with authentication method of email. """
        # Assumes you provide username,password and returns a token
        user = get_user_model().objects.create_user('admin', 'email.login@gmail.com', 'password12')
        data = {"username": '', "email": "email.login@gmail.com", "password": 'password12'}
        EmailAddress.objects.create(
            user=user,
            email="email.login@gmail.com",
            verified=True,
            primary=True
        )
        response = self.client.post(self.login_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertIn('key', response.content)

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.USERNAME_EMAIL)
    def test_login_basic_username_email_auth_method(self):
        """ Tests basic functionality of login with authentication method of username or email. """
        # Assumes you provide username,password and returns a token
        user = get_user_model().objects.create_user('admin', 'email.login@gmail.com', 'password12')
        EmailAddress.objects.create(
            user=user,
            email="email.login@gmail.com",
            verified=True,
            primary=True
        )
        # Check email
        data = {"username": '', "email": "email.login@gmail.com", "password": 'password12'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        # Check username
        data = {"username": 'admin', "email": '', "password": 'password12'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertIn('key', response.content)

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.USERNAME)
    def test_login_auth_method_username_fail_no_users_in_db(self):
        """ Tests login fails with a 400 when no users in db for login auth method of 'username'. """
        serializer = LoginSerializer({'username': 'admin', 'password': 'password12'})
        response = self.client.post(self.login_url, serializer.data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.EMAIL)
    def test_login_email_auth_method_fail_no_users_in_db(self):
        """ Tests login fails with a 400 when no users in db for login auth method of 'email'. """
        serializer = LoginSerializer({'username': 'admin', 'password': 'password12'})
        response = self.client.post(self.login_url, serializer.data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.USERNAME_EMAIL)
    def test_login_username_email_auth_method_fail_no_users_in_db(self):
        """ Tests login fails with a 400 when no users in db for login auth method of 'username_email'. """
        serializer = LoginSerializer({'username': 'admin', 'password': 'password12'})
        response = self.client.post(self.login_url, serializer.data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def common_test_login_fail_incorrect_change(self):
        # Create user, login and try and change password INCORRECTLY
        self.create_user_and_login()
        self.client.post(self.password_change_url, data=self.change_password_data_incorrect, format='json')
        # Remove credentials
        self.client.credentials()
        response = self.client.post(self.login_url, self.reusable_user_data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertIn('key', response.content)

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.USERNAME)
    def test_login_username_auth_method_fail_incorrect_password_change(self):
        """ Tests login fails with an incorrect/invalid password change (login auth username). """
        self.common_test_login_fail_incorrect_change()

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.EMAIL)
    def test_login_email_auth_method_fail_incorrect_password_change(self):
        """ Tests login fails with an incorrect/invalid password change (login auth email). """
        self.common_test_login_fail_incorrect_change()

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.USERNAME_EMAIL)
    def test_login_username_email_auth_method_fail_incorrect_password_change(self):
        """ Tests login fails with an incorrect/invalid password change (login auth username_email). """
        self.common_test_login_fail_incorrect_change()

    def common_test_login_correct_password_change(self):
        # Create user, login and try and change password successfully
        self.create_user_and_login()
        response = self.client.post(self.password_change_url, data=self.change_password_data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        # Remove credentials
        self.client.credentials()
        response = self.client.post(self.login_url, self.reusable_user_data_change_password, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertIn('key', response.content)

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.USERNAME)
    def test_login_username_auth_method_correct_password_change(self):
        """ Tests login is succesful with a correct password change (login auth username). """
        self.common_test_login_correct_password_change()

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.EMAIL)
    def test_login_email_auth_method_correct_password_change(self):
        """ Tests login is succesful with a correct password change (login auth email). """
        self.common_test_login_correct_password_change()

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.USERNAME_EMAIL)
    def test_login_username_email_auth_method_correct_password_change(self):
        """ Tests login is succesful with a correct password change (login auth username_email). """
        self.common_test_login_correct_password_change()

    def test_login_fail_no_input(self):
        """ Tests login fails when you provide no username and no email (login auth username_email). """
        get_user_model().objects.create_user('admin', 'email.login@gmail.com', 'password12')
        data = {"username": '', "email": '', "password": ''}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.USERNAME)
    def test_login_username_auth_method_fail_no_input(self):
        """ Tests login fails when you provide no username (login auth username). """
        get_user_model().objects.create_user('admin', 'email.login@gmail.com', 'password12')
        data = {"username": '', "email": "email.login@gmail.com", "password": 'password12'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.EMAIL)
    def test_login_email_auth_method_fail_no_input(self):
        """ Tests login fails when you provide no username (login auth email). """
        get_user_model().objects.create_user('admin', 'email.login@gmail.com', 'password12')
        data = {"username": "admin", "email": '', "password": 'password12'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(ACCOUNT_AUTHENTICATION_METHOD=app_settings.AuthenticationMethod.USERNAME_EMAIL)
    def test_login_username_email_auth_method_fail_no_input(self):
        """ Tests login fails when you provide no username and no email (login auth username_email). """
        get_user_model().objects.create_user('admin', 'email.login@gmail.com', 'password12')
        data = {"username": '', "email": '', "password": 'password12'}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)





        # need to check for token
        # test login with password change
        # test login with wrong password chaneg if fails

    def test_logout(self):
        """ Tests basic logout functionality. """
        self.create_user_and_login()
        response = self.client.post(self.logout_url, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.content, '{"success":"Successfully logged out."}')

    def test_logout_but_already_logged_out(self):
        """ Tests logout when already logged out. """
        self.create_user_and_login()
        response = self.client.post(self.logout_url, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.content, '{"success":"Successfully logged out."}')
        self.client.credentials()  # remember to remove manual token credential
        response = self.client.post(self.logout_url, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEquals(response.content, '{"success":"Successfully logged out."}')

    def test_change_password_basic(self):
        """ Tests basic functionality of 'change of password'. """
        self.create_user_and_login()
        response = self.client.post(self.password_change_url, data=self.change_password_data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.content, '{"success":"New password has been saved."}')

    def test_change_password_basic_fails_not_authorised(self):
        """ Tests basic functionality of 'change of password' fails if not authorised. """
        get_user_model().objects.create_user('admin', 'admin@email.com', 'password12')
        response = self.client.post(self.password_change_url, data=self.change_password_data, format='json')
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.content, '{"detail":"Authentication credentials were not provided."}')

    def common_change_password_login_fail_with_old_password(self, password_change_data):
        self.create_user_and_login()
        response = self.client.post(self.password_change_url, data=password_change_data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.client.credentials()  # Remove credentials
        response = self.client.post(self.login_url, self.reusable_user_data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def common_change_password_login_pass_with_new_password(self, password_change_data):
        self.create_user_and_login()
        response = self.client.post(self.password_change_url, password_change_data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.client.credentials()  # Remove credentials
        response = self.client.post(self.login_url, self.reusable_user_data_change_password, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def common_change_password_login_fail_with_old_password_pass_with_new_password(self, password_change_data):
        """ Tests change of password with old password fails but new password successes. """
        self.create_user_and_login()
        response = self.client.post(self.password_change_url, password_change_data, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK, response.content)
        self.client.credentials()  # Remove credentials
        response = self.client.post(self.login_url, self.reusable_user_data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(self.login_url, self.reusable_user_data_change_password, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK, response.content)

    def test_change_password_login_fail_with_old_password(self):
        """ Tests change of password with old password. """
        self.common_change_password_login_fail_with_old_password(self.change_password_data)

    def test_change_password_login_pass_with_new_password(self):
        """ Tests change of password with new password. """
        self.common_change_password_login_pass_with_new_password(self.change_password_data)

    def test_change_password_login_fail_with_old_password_pass_with_new_password(self):
        """ Tests change of password with old password fails but new password successes. """
        self.common_change_password_login_fail_with_old_password_pass_with_new_password(self.change_password_data)

    @override_settings(OLD_PASSWORD_FIELD_ENABLED=True)
    def test_change_password_old_password_field_required_old_password_field_enabled(self):
        """ Tests basic functionality of 'change of password' fails if old password not given as part of input (old password field enabled). """
        self.create_user_and_login()
        response = self.client.post(self.password_change_url, data=self.change_password_data, format='json')
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(response.content, '{"old_password":["This field is required."]}')

    @override_settings(OLD_PASSWORD_FIELD_ENABLED=True)
    def test_change_password_basic_old_password_field_enabled(self):
        """ Tests basic functionality of 'change of password' (old password enabled). """
        self.create_user_and_login()
        response = self.client.post(self.password_change_url, data=self.change_password_data_old_password_field_enabled, format='json')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.content, '{"success":"New password has been saved."}')

    @override_settings(OLD_PASSWORD_FIELD_ENABLED=True)
    def test_change_password_basic_fails_not_authorised_old_password_field_enabled(self):
        """ Tests basic functionality of 'change of password' fails if not authorised (old password field enabled). """
        get_user_model().objects.create_user('admin', 'admin@email.com', 'password12')
        response = self.client.post(self.password_change_url, data=self.change_password_data_old_password_field_enabled, format='json')
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEquals(response.content, '{"detail":"Authentication credentials were not provided."}')

    @override_settings(OLD_PASSWORD_FIELD_ENABLED=True)
    def test_change_password_login_fail_with_old_password_old_password_field_enabled(self):
        """ Tests change of password with old password (old password field enabled). """
        self.common_change_password_login_fail_with_old_password(self.change_password_data_old_password_field_enabled)

    @override_settings(OLD_PASSWORD_FIELD_ENABLED=True)
    def test_change_password_login_pass_with_new_password_old_password_field_enabled(self):
        """ Tests change of password with new password (old password field enabled). """
        self.common_change_password_login_pass_with_new_password(self.change_password_data_old_password_field_enabled)

    @override_settings(OLD_PASSWORD_FIELD_ENABLED=True)
    def test_change_password_login_fail_with_old_password_pass_with_new_password_old_password_field_enabled(self):
        """ Tests change of password with old password fails but new password successes (old password field enabled). """
        self.common_change_password_login_fail_with_old_password_pass_with_new_password(self.change_password_data_old_password_field_enabled)





# class TestAccountsSocial(APITestCase):
#     """ Tests normal for social login. """

#     urls = 'tests.urls'

#     def setUp(self):
#         self.fb_login_url = reverse('fb_login')
#         social_app = SocialApp.objects.create(
#             provider='facebook',
#             name='Facebook',
#             client_id='123123123',
#             secret='321321321',
#         )
#         site = Site.objects.get_current()
#         social_app.sites.add(site)
#         self.graph_api_url = GRAPH_API_URL + '/me'

#     @responses.activate
#     def test_social_auth(self):
#         """ Tests Social Login. """
#         resp_body = '{"id":"123123123123","first_name":"John","gender":"male","last_name":"Smith","link":"https:\\/\\/www.facebook.com\\/john.smith","locale":"en_US","name":"John Smith","timezone":2,"updated_time":"2014-08-13T10:14:38+0000","username":"john.smith","verified":true}'  # noqa
#         responses.add(
#             responses.GET,
#             self.graph_api_url,
#             body=resp_body,
#             status=200,
#             content_type='application/json'
#         )

#         users_count = get_user_model().objects.all().count()
#         response = self.client.post(self.fb_login_url, {'access_token': 'abc123'}, format='json')
#         self.assertEquals(response.status_code, status.HTTP_200_OK)
#         self.assertIn('key', response.data)
#         self.assertEqual(get_user_model().objects.all().count(), users_count + 1)

#     @responses.activate
#     def test_social_auth_only_one_user_created(self):
#         """ Tests Social Login. """
#         resp_body = '{"id":"123123123123","first_name":"John","gender":"male","last_name":"Smith","link":"https:\\/\\/www.facebook.com\\/john.smith","locale":"en_US","name":"John Smith","timezone":2,"updated_time":"2014-08-13T10:14:38+0000","username":"john.smith","verified":true}'  # noqa
#         responses.add(
#             responses.GET,
#             self.graph_api_url,
#             body=resp_body,
#             status=200,
#             content_type='application/json'
#         )

#         users_count = get_user_model().objects.all().count()
#         response = self.client.post(self.fb_login_url, {'access_token': 'abc123'}, format='json')
#         self.assertEquals(response.status_code, status.HTTP_200_OK)
#         self.assertIn('key', response.data)
#         self.assertEqual(get_user_model().objects.all().count(), users_count + 1)

#         # make sure that second request will not create a new user
#         response = self.client.post(self.fb_login_url, {'access_token': 'abc123'}, format='json')
#         self.assertEquals(response.status_code, status.HTTP_200_OK)
#         self.assertIn('key', response.data)
#         self.assertEqual(get_user_model().objects.all().count(), users_count + 1)

#     @responses.activate
#     def test_failed_social_auth(self):
#         # fake response
#         responses.add(
#             responses.GET,
#             self.graph_api_url,
#             body='',
#             status=400,
#             content_type='application/json'
#         )
#         response = self.client.post(self.fb_login_url, {'access_token': 'abc123'}, format='json')
#         self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)










    # @override_settings(
    #     ACCOUNT_EMAIL_CONFIRMATION_HMAC=True,
    #     ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS=1,
    # )
    # def test_hmac_expiration(self):
    #     """ Test Verification Fails if Expiration has timed out. 
    #     """
    #     initial_datetime = datetime.datetime(year=2012, month=1, day=16)
    #     future_datetime = datetime.datetime(year=2012, month=2, day=18)
    #     with freeze_time(initial_datetime, tz_offset=-4) as frozen_datetime:
    #         user = self._create_user()
    #         email = self._create_email(user)
    #         confirmation = EmailConfirmationHMAC(email)
    #         confirmation.send()
    #         self.assertEqual(len(mail.outbox), 1)

    #         frozen_datetime.move_to(future_datetime)
    #         assert frozen_datetime() == future_datetime
    #         from django.utils import timezone
    #         print datetime.timedelta(days=1)
    #         print timezone.now()

    #         response = self.client.post(
    #             self.verify_url,
    #             {'key': confirmation.key},
    #             format='json'
    #         )
    #         self.assertEquals(response.status_code, status.HTTP_200_OK)
    #         email = EmailAddress.objects.get(pk=email.pk)
    #         self.assertFalse(email.verified)


