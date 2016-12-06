"""
    tests.test_api_integration.py
    =============================

    Tests the REST API calls for normal use case

"""
from django_dynamic_fixture import G

from django.utils.encoding import force_bytes
from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode


from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from allauth.account.models import EmailAddress, EmailConfirmationHMAC

from django_accounts.models import AccountsUser

from utils import parameterise


# # http://django-allauth.readthedocs.org/en/latest/configuration.html
# # Note if you change e.g. ACCOUNT_UNIQUE_EMAIL you may need to delete db before changes work

# # Changing these could cause tests to fail
# ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_USERNAME_REQUIRED = True
# ACCOUNT_EMAIL_VERIFICATION = "mandatory"
# ACCOUNT_AUTHENTICATION_METHOD = "username_email"
# ACCOUNT_EMAIL_CONFIRMATION_HMAC = True
# # Note if set to true - tests will fail as we need to recreate db every test
# ACCOUNT_UNIQUE_EMAIL = True
# ACCOUNT_ADAPTER = "django_accounts.adapter.DefaultAccountAdapter"

# AUTH_USER_MODEL = 'django_accounts.AccountsUser'
# REGISTRATION_OPEN = True

# AUTHENTICATION_BACKENDS = (

#     # Needed to login by username in Django admin, regardless of `allauth`
#     'django.contrib.auth.backends.ModelBackend',

#     # `allauth` specific authentication methods, such as login by e-mail
#     'allauth.account.auth_backends.AuthenticationBackend',
# )
class TestException(Exception):
    pass


class TestNormalUseCases(APITestCase):
    """
        Tests normal use - non social logins
        ====================================

        Acts as a basic regression testing suite
    """
    EMAIL = 'jtarball@example.com'
    USERNAME = 'jtarball'
    PASSWORD = 'password12'

    RESUABLE_SIGNUP = {
        'username': 'new_user',
        'email': 'new_user@example.com',
        'password1': PASSWORD,
        'password2': PASSWORD
    }

    LOGIN_TESTS = [
        {
            'test_name': 'test_login_with_username',
            'test_description': 'Tests you can log in with username.',
            'http_method': 'POST',
            'data': {'username': USERNAME, 'password': PASSWORD},
            'status_code': status.HTTP_200_OK,
        },
        {
            'test_name': 'test_login_fails_with_bad_password',
            'test_description': 'Tests you can log fails with the wrong password.',
            'http_method': 'POST',
            'data': {'username': USERNAME, 'password': 'wrong_password'},
            'status_code': status.HTTP_400_BAD_REQUEST,
        },
        {
            'test_name': 'test_login_with_email',
            'test_description': 'Tests you can log in with email.'
                                'We only want to be able to login with the username.',
            'http_method': 'POST',
            'data': {'email': EMAIL, 'password': PASSWORD},
            'status_code': status.HTTP_200_OK
        },
        {
            'test_name': 'test_login_http_method_GET_not_allowed',
            'test_description': 'Tests a GET method fails for the login url.',
            'http_method': 'GET',
            'data': {'username': USERNAME, 'password': PASSWORD},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"GET\\" not allowed."}'
        },
        {
            'test_name': 'test_login_http_method_PATCH_not_allowed',
            'test_description': 'Tests a PATCH method fails for the login url.',
            'http_method': 'PATCH',
            'data': {'username': USERNAME, 'password': PASSWORD},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PATCH\\" not allowed."}'
        },
        {
            'test_name': 'test_login_http_method_PUT_not_allowed',
            'test_description': 'Tests a PUT method fails for the login url.',
            'http_method': 'PUT',
            'data': {'username': USERNAME, 'password': PASSWORD},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PUT\\" not allowed."}'
        },
        {
            'test_name': 'test_login_http_method_DELETE_not_allowed',
            'test_description': 'Tests a DELETE method fails for the login url.',
            'http_method': 'DELETE',
            'data': {'username': USERNAME, 'password': PASSWORD},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"DELETE\\" not allowed."}'
        },
    ]
    SIGNUP_TESTS = [
        {
            'test_name': 'test_signup_user',
            'test_description': 'Tests signup of a user',
            'http_method': 'POST',
            'data': RESUABLE_SIGNUP,
            'status_code': status.HTTP_201_CREATED,
            'mail_count_change': 1,
        },
        {
            'test_name': 'test_signup_user_fails_email_already_exists',
            'test_description': 'Tests signup fails if email is already registerd',
            'http_method': 'POST',
            'data': {'username': 'new_user', 'email': EMAIL, 'password1': PASSWORD, 'password2': PASSWORD},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"email":["A user is already registered with this e-mail address."]}',
            'mail_count_change': 0,
        },
        {
            'test_name': 'test_signup_user_fails_username_already_exists',
            'test_description': 'Tests signup fails if username is already registered',
            'http_method': 'POST',
            'data': {'username': USERNAME, 'email': 'new_user@example.com', 'password1': PASSWORD, 'password2': PASSWORD},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"username":["A user with that username already exists."]}',
            'mail_count_change': 0,
        },
        {
            'test_name': 'test_signup_user_fails_if_passwords_not_same',
            'test_description': 'Tests signup fails if the passwords are not the same',
            'http_method': 'POST',
            'data': {'username': 'new_user', 'email': 'new_user@example.com', 'password1': 'different', 'password2': PASSWORD},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"password2":["You must type the same password each time."]}',
            'mail_count_change': 0,
        },
        {
            'test_name': 'test_signup_user_fails_blank_email',
            'test_description': 'Tests signup fails if email is blank',
            'http_method': 'POST',
            'data': {'username': 'new_user', 'email': '', 'password1': PASSWORD, 'password2': PASSWORD},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'mail_count_change': 0,
        },
        {
            'test_name': 'test_signup_user_fails_missing_email',
            'test_description': 'Tests signup fails if email is missing from POST.',
            'http_method': 'POST',
            'data': {'username': 'new_user', 'password1': PASSWORD, 'password2': PASSWORD},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'mail_count_change': 0,
        },
        {
            'test_name': 'test_signup_user_fails_blank_username',
            'test_description': 'Tests signup fails if username is blank.',
            'http_method': 'POST',
            'data': {'username': '', 'email': 'new_user@example.com', 'password1': PASSWORD, 'password2': PASSWORD},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'mail_count_change': 0,
        },
        {
            'test_name': 'test_signup_user_fails_missing_username',
            'test_description': 'Tests signup fails if username is missing from POST.',
            'http_method': 'POST',
            'data': {'email': 'new_user@example.com', 'password1': PASSWORD, 'password2': PASSWORD},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'mail_count_change': 0,
        },
        {
            'test_name': 'test_signup_user_fails_blank_password1',
            'test_description': 'Tests signup fails if password1 is blank.',
            'http_method': 'POST',
            'data': {'username': 'new_user', 'email': 'new_user@example.com', 'password1': '', 'password2': PASSWORD},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'mail_count_change': 0,
        },
        {
            'test_name': 'test_signup_user_fails_missing_password1',
            'test_description': 'Tests signup fails if password1 is missing from POST.',
            'http_method': 'POST',
            'data': {'username': 'new_user', 'email': 'new_user@example.com', 'password2': PASSWORD},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'mail_count_change': 0,
        },
        {
            'test_name': 'test_signup_user_fails_blank_password2',
            'test_description': 'Tests signup fails if password2 is blank.',
            'http_method': 'POST',
            'data': {'username': 'new_user', 'email': 'new_user@example.com', 'password2': '', 'password1': PASSWORD},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'mail_count_change': 0,
        },
        {
            'test_name': 'test_signup_user_fails_missing_password2',
            'test_description': 'Tests signup fails if password2 is missing from POST.',
            'http_method': 'POST',
            'data': {'username': 'new_user', 'email': 'new_user@example.com', 'password1': PASSWORD},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'mail_count_change': 0,
        },
        {
            'test_name': 'test_signup_http_method_GET_not_allowed',
            'test_description': 'Tests a GET method fails for the signup url.',
            'http_method': 'GET',
            'data': {'username': USERNAME, 'password': PASSWORD},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"GET\\" not allowed."}'
        },
        {
            'test_name': 'test_signup_http_method_PATCH_not_allowed',
            'test_description': 'Tests a PATCH method fails for the signup url.',
            'http_method': 'PATCH',
            'data': {'username': USERNAME, 'password': PASSWORD},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PATCH\\" not allowed."}'
        },
        {
            'test_name': 'test_signup_http_method_PUT_not_allowed',
            'test_description': 'Tests a PUT method fails for the signup url.',
            'http_method': 'PUT',
            'data': {'username': USERNAME, 'password': PASSWORD},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PUT\\" not allowed."}'
        },
        {
            'test_name': 'test_signup_http_method_DELETE_not_allowed',
            'test_description': 'Tests a DELETE method fails for the signup url.',
            'http_method': 'DELETE',
            'data': {'username': USERNAME, 'password': PASSWORD},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"DELETE\\" not allowed."}'
        },
    ]
    PASSWORD_CHANGE_TESTS = [
        {
            'test_name': 'test_password_change_password',
            'test_description': 'Tests password change is successful.',
            'authentication': 'user',
            'http_method': 'POST',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_200_OK,
            'response_content': '{"success":"New password has been saved."}'
        },
        {
            'test_name': 'test_password_change_fails_if_passwords_different',
            'test_description': 'Tests password change fails if passwords are different.',
            'authentication': 'user',
            'http_method': 'POST',
            'data': {"password1": "password_different", "password2": "password_same"},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"password2":["You must type the same password each time."]}'
        },
        {
            'test_name': 'test_password_change_password_fails_if_password1_missing',
            'test_description': 'Tests password change fails if password1 is missing.',
            'authentication': 'user',
            'http_method': 'POST',
            'data': {"password2": "password_same"},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"password1":["This field is required."]}'
        },
        {
            'test_name': 'test_password_change_password_fails_if_password1_blank',
            'test_description': 'Tests password change fails if password1 is missing.',
            'authentication': 'user',
            'http_method': 'POST',
            'data': {"password1": "", "password2": "password_same"},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"password1":["This field may not be blank."]}'
        },
        {
            'test_name': 'test_password_change_password_fails_if_password2_missing',
            'test_description': 'Tests password change fails if password2 is missing.',
            'authentication': 'user',
            'http_method': 'POST',
            'data': {"password1": "password_same"},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"password2":["This field is required."]}'
        },
        {
            'test_name': 'test_password_change_password_fails_if_password2_blank',
            'test_description': 'Tests password change fails if password2 is missing.',
            'authentication': 'user',
            'http_method': 'POST',
            'data': {"password2": "", "password1": "password_same"},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"password2":["This field may not be blank."]}'
        },
        {
            'test_name': 'test_password_change_password_fails_if_not_logged_In',
            'test_description': 'Tests password change fails if not logged in.',
            'http_method': 'POST',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_403_FORBIDDEN,
            'response_content': '{"detail":"Authentication credentials were not provided."}'
        },
        {
            'test_name': 'test_password_change_http_method_GET_forbidden_if_not_logged_in',
            'test_description': 'Tests a GET method fails for the signup url.',
            'http_method': 'GET',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_403_FORBIDDEN,
            'response_content': '{"detail":"Authentication credentials were not provided."}'
        },
        {
            'test_name': 'test_password_change_http_method_PATCH_forbidden_if_not_logged_in',
            'test_description': 'Tests a PATCH method fails for the signup url.',
            'http_method': 'PATCH',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_403_FORBIDDEN,
            'response_content': '{"detail":"Authentication credentials were not provided."}'
        },
        {
            'test_name': 'test_password_change_http_method_PUT_forbidden_if_not_logged_in',
            'test_description': 'Tests a PUT method fails for the signup url.',
            'http_method': 'PUT',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_403_FORBIDDEN,
            'response_content': '{"detail":"Authentication credentials were not provided."}'
        },
        {
            'test_name': 'test_password_change_http_method_DELETE_forbidden_if_not_logged_in',
            'test_description': 'Tests a DELETE method fails for the signup url.',
            'http_method': 'DELETE',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_403_FORBIDDEN,
            'response_content': '{"detail":"Authentication credentials were not provided."}'
        },
        {
            'test_name': 'test_password_change_http_method_GET_not_allowed_if_logged_in',
            'test_description': 'Tests a GET method fails for the signup url.',
            'authentication': 'user',
            'http_method': 'GET',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"GET\\" not allowed."}'
        },
        {
            'test_name': 'test_password_change_http_method_PATCH_not_allowed_if_logged_in',
            'test_description': 'Tests a PATCH method fails for the signup url.',
            'authentication': 'user',
            'http_method': 'PATCH',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PATCH\\" not allowed."}'
        },
        {
            'test_name': 'test_password_change_http_method_PUT_not_allowed_if_logged_in',
            'test_description': 'Tests a PUT method fails for the signup url.',
            'authentication': 'user',
            'http_method': 'PUT',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PUT\\" not allowed."}'
        },
        {
            'test_name': 'test_password_change_http_method_DELETE_not_allowed_if_logged_in',
            'test_description': 'Tests a DELETE method fails for the signup url.',
            'authentication': 'user',
            'http_method': 'DELETE',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"DELETE\\" not allowed."}'
        },
    ]
    EMAIL_VERIFICATION_TESTS = [
        {
            'test_name': 'test_email_verification_POST',
            'test_description': 'Tests basic email verification',
            'http_method': 'POST',
            'status_code': status.HTTP_200_OK,
            'response_content': '{"message":"ok"}',
            'check_login_status_code': status.HTTP_200_OK,
        },
        {
            'test_name': 'test_email_verification_GET',
            'test_description': 'Tests basic email verification',
            'http_method': 'GET',
            'status_code': status.HTTP_200_OK,
            'response_content': '{"message":"ok"}',
            'check_login_status_code': status.HTTP_200_OK,
        },
        {
            'test_name': 'test_email_verification_fails_POST',
            'test_description': 'Tests basic email verification fails for POST if key is incorrect',
            'http_method': 'POST',
            'key': 'a801d43811d76b766a7d0e6a9be702e97e71a56b',  # wrong key
            'status_code': status.HTTP_404_NOT_FOUND,
            'response_content': '{"detail":"Not found."}',
            'check_login_status_code': status.HTTP_400_BAD_REQUEST,
            'check_login_response': '{"non_field_errors":["E-mail is not verified."]}'
        },
        {
            'test_name': 'test_email_verification_fails_GET',
            'test_description': 'Tests basic email verification fails if GET if key is incorrect',
            'http_method': 'GET',
            'key': 'a801d43811d76b766a7d0e6a9be702e97e71a56b',  # wrong key
            'status_code': status.HTTP_404_NOT_FOUND,
            'response_content': '{"detail":"Not found."}',
            'check_login_status_code': status.HTTP_400_BAD_REQUEST,
            'check_login_response': '{"non_field_errors":["E-mail is not verified."]}'
        },
        {
            'test_name': 'test_email_verification_http_method_PATCH_not_allowed',
            'test_description': 'Tests a PATCH method fails for the verify url.',
            'http_method': 'PATCH',
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PATCH\\" not allowed."}',
        },
        {
            'test_name': 'test_email_verification_http_method_PUT_not_allowed',
            'test_description': 'Tests a PUT method fails for the verify url.',
            'http_method': 'PUT',
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PUT\\" not allowed."}',
        },
        {
            'test_name': 'test_email_verification_http_method_DELETE_not_allowed',
            'test_description': 'Tests a DELETE method fails for the verify url.',
            'http_method': 'DELETE',
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"DELETE\\" not allowed."}'
        },
    ]
    LOGOUT_TESTS = [
        {
            'test_name': 'test_logout_if_not_logged_in',
            'test_description': 'Tests you can logout successfully.',
            'http_method': 'POST',
            'status_code': status.HTTP_200_OK,
            'response_content': '{"success":"Successfully logged out."}'
        },
        {
            'test_name': 'test_logout_if_logged_in',
            'test_description': 'Tests you can logout successfully.',
            'http_method': 'POST',
            'status_code': status.HTTP_200_OK,
            'response_content': '{"success":"Successfully logged out."}'
        },
        {
            'test_name': 'test_logout_http_method_GET_not_allowed',
            'test_description': 'Tests a GET method fails for the login url.',
            'http_method': 'GET',
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"GET\\" not allowed."}'
        },
        {
            'test_name': 'test_logout_http_method_PATCH_not_allowed',
            'test_description': 'Tests a PATCH method fails for the login url.',
            'http_method': 'PATCH',
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PATCH\\" not allowed."}'
        },
        {
            'test_name': 'test_logout_http_method_PUT_not_allowed',
            'test_description': 'Tests a PUT method fails for the login url.',
            'http_method': 'PUT',
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PUT\\" not allowed."}'
        },
        {
            'test_name': 'test_logout_http_method_DELETE_not_allowed',
            'test_description': 'Tests a DELETE method fails for the login url.',
            'http_method': 'DELETE',
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"DELETE\\" not allowed."}'
        },
    ]
    PASSWORD_RESET_TESTS = [
        {
            'test_name': 'test_password_reset',
            'test_description': 'Tests password change is successful.',
            'authentication': 'user',
            'http_method': 'POST',
            'data': {'email': EMAIL},
            'status_code': status.HTTP_200_OK,
            'response_content': '{"success":"Password reset e-mail has been sent."}',
            'mail_count_change': 1
        },
        {
            'test_name': 'test_password_reset_no_authentication_needed',
            'test_description': 'Tests password change is successful.',
            'http_method': 'POST',
            'data': {'email': EMAIL},
            'status_code': status.HTTP_200_OK,
            'response_content': '{"success":"Password reset e-mail has been sent."}',
            'mail_count_change': 1
        },
        {
            'test_name': 'test_password_reset_fails_if_user_for_email_not_in_system',
            'test_description': 'Tests password change is successful.',
            'http_method': 'POST',
            'data': {'email': 'not_in_system@example.com'},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content':  '{"email":["Validation Error {\'email\': [u\'The e-mail address is not assigned to any user account\']}"]}',
            'mail_count_change': 0
        },
        {
            'test_name': 'test_password_reset_fails_if_missing_email',
            'test_description': 'Tests password change is successful.',
            'http_method': 'POST',
            'data': {},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content':  '{"email":["This field is required."]}',
            'mail_count_change': 0
        },
        {
            'test_name': 'test_password_reset_fails_if_blank_email',
            'test_description': 'Tests password change is successful.',
            'http_method': 'POST',
            'data': {'email': ''},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content':  '{"email":["This field may not be blank."]}',
            'mail_count_change': 0
        },
        {
            'test_name': 'test_password_reset_http_method_GET_not_allowed_if_logged_in',
            'test_description': 'Tests a GET method fails for the signup url.',
            'authentication': 'user',
            'http_method': 'GET',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"GET\\" not allowed."}'
        },
        {
            'test_name': 'test_password_reset_http_method_PATCH_not_allowed_if_logged_in',
            'test_description': 'Tests a PATCH method fails for the signup url.',
            'authentication': 'user',
            'http_method': 'PATCH',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PATCH\\" not allowed."}'
        },
        {
            'test_name': 'test_password_reset_http_method_PUT_not_allowed_if_logged_in',
            'test_description': 'Tests a PUT method fails for the signup url.',
            'authentication': 'user',
            'http_method': 'PUT',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PUT\\" not allowed."}'
        },
        {
            'test_name': 'test_password_reset_http_method_DELETE_not_allowed_if_logged_in',
            'test_description': 'Tests a DELETE method fails for the signup url.',
            'authentication': 'user',
            'http_method': 'DELETE',
            'data': {"password1": "password_same", "password2": "password_same"},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"DELETE\\" not allowed."}'
        },
    ]
    PASSWORD_RESET_CONFIRMATION_TESTS = [
        {
            'test_name': 'test_password_reset_confirm_POST',
            'test_description': 'Tests basic password reset confirmation',
            'http_method': 'POST',
            'password_data': {'password1': 'new_password', 'password2': 'new_password'},
            'status_code': status.HTTP_200_OK,
            'response_content': '{"success":"Password has been reset with the new password."}',
            'check_login_status_code': status.HTTP_200_OK,
        },
        {
            'test_name': 'test_password_reset_confirm_fails_uid_invalid',
            'test_description': 'Tests basic password reset confirmation',
            'http_method': 'POST',
            'uid': 10010100,
            'password_data': {'password1': 'new_password', 'password2': 'new_password'},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"uid":["Invalid value"]}'
        },
        {
            'test_name': 'test_password_reset_confirm_fails_uid_wrong_user',
            'test_description': 'Tests basic password reset confirmation',
            'http_method': 'POST',
            'uid': urlsafe_base64_encode(force_bytes(10)),
            'password_data': {'password1': 'new_password', 'password2': 'new_password'},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"uid":["Invalid value"]}'
        },
        {
            'test_name': 'test_password_reset_confirm_fails_token_wrong_user',
            'test_description': 'Tests basic password reset confirmation',
            'http_method': 'POST',
            'token_user': 'superuser',
            'password_data': {'password1': 'new_password', 'password2': 'new_password'},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"token":["Invalid value"]}'
        },
        {
            'test_name': 'test_password_reset_confirm_fails_if_passwords_different',
            'test_description': 'Tests password change fails if passwords are different.',
            'http_method': 'POST',
            'password_data': {"password1": "password_different", "password2": "password_same"},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"password2":["You must type the same password each time."]}',
            'check_login_status_code': status.HTTP_400_BAD_REQUEST,
            'check_login_response': '{"non_field_errors":["Unable to log in with provided credentials."]}'
        },
        {
            'test_name': 'test_password_reset_confirm_password_fails_if_password1_missing',
            'test_description': 'Tests password change fails if password1 is missing.',
            'http_method': 'POST',
            'password_data': {"password2": "password_same"},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"password1":["This field is required."]}',
            'check_login_status_code': status.HTTP_400_BAD_REQUEST,
            'check_login_response': '{"non_field_errors":["Unable to log in with provided credentials."]}'
        },
        {
            'test_name': 'test_password_reset_confirm_password_fails_if_password1_blank',
            'test_description': 'Tests password change fails if password1 is missing.',
            'http_method': 'POST',
            'password_data': {"password1": "", "password2": "password_same"},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"password1":["This field may not be blank."]}',
            'check_login_status_code': status.HTTP_400_BAD_REQUEST,
            'check_login_response': '{"non_field_errors":["Unable to log in with provided credentials."]}'
        },
        {
            'test_name': 'test_password_reset_confirm_password_fails_if_password2_missing',
            'test_description': 'Tests password change fails if password2 is missing.',
            'http_method': 'POST',
            'password_data': {"password1": "password_same"},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"password2":["This field is required."]}',
            'check_login_status_code': status.HTTP_400_BAD_REQUEST,
            'check_login_response': '{"non_field_errors":["Unable to log in with provided credentials."]}'
        },
        {
            'test_name': 'test_password_reset_confirm_password_fails_if_password2_blank',
            'test_description': 'Tests password change fails if password2 is missing.',
            'http_method': 'POST',
            'password_data': {"password2": "", "password1": "password_same"},
            'status_code': status.HTTP_400_BAD_REQUEST,
            'response_content': '{"password2":["This field may not be blank."]}',
            'check_login_status_code': status.HTTP_400_BAD_REQUEST,
            'check_login_response': '{"non_field_errors":["Unable to log in with provided credentials."]}'
        },
        {
            'test_name': 'test_password_reset_confirm_GET_not_allowed',
            'test_description': 'Tests basic email verification fails if GET if key is incorrect',
            'http_method': 'GET',
            'password_data': {'password1': 'new_password', 'password2': 'new_password'},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"GET\\" not allowed."}'
        },
        {
            'test_name': 'test_password_reset_confirm_http_method_PATCH_not_allowed',
            'test_description': 'Tests a PATCH method fails for the verify url.',
            'http_method': 'PATCH',
            'password_data': {'password1': 'new_password', 'password2': 'new_password'},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PATCH\\" not allowed."}',
        },
        {
            'test_name': 'test_password_reset_confirm_http_method_PUT_not_allowed',
            'test_description': 'Tests a PUT method fails for the verify url.',
            'http_method': 'PUT',
            'password_data': {'password1': 'new_password', 'password2': 'new_password'},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"PUT\\" not allowed."}',
        },
        {
            'test_name': 'test_password_reset_confirm_http_method_DELETE_not_allowed',
            'test_description': 'Tests a DELETE method fails for the verify url.',
            'http_method': 'DELETE',
            'password_data': {'password1': 'new_password', 'password2': 'new_password'},
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"DELETE\\" not allowed."}'
        },
    ]
    INTEGRATION_TESTS = []

    def setUp(self):
        # More information on asserts
        self.longMessage = True

        self.client = APIClient()
        self.user_url = reverse('accounts:rest_user_details')
        self.login_url = reverse('accounts:rest_login')
        self.logout_url = reverse('accounts:rest_logout')
        self.register_url = reverse('accounts:rest_register')
        self.password_change_url = reverse('accounts:rest_password_change')
        self.password_reset_url = reverse('accounts:rest_password_reset')
        self.password_reset_confirm_url = reverse('accounts:rest_password_reset_confirm')
        self.verify_url = reverse('accounts:rest_verify_email')

        self.email = self.EMAIL
        self.username = 'jtarball'
        self.password = 'password12'
        self.first_name = 'James'
        self.last_name = 'Tarball'
        self.staff_email = 'admin@example.com'
        self.staff_username = 'admin'
        self.superuser_username = 'superuser'
        self.superuser_email = 'superuser@email.com'
        self.superuser_not_staff_username = 'superuser_not_staff'
        self.superuser_not_staff_email = 'superuser_not_staff@email.com'

        self.user_data = {
            'username': self.username,
            'password': self.password,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name
        }
        self.staff_data = {
            'username': self.staff_username,
            'password': self.password,
            'email': self.staff_email,
            'first_name': self.first_name,
            'last_name': self.last_name
        }

        self.superuser_data = {
            'username': self.superuser_username,
            'password': self.password,
            'email': self.superuser_email,
            'first_name': self.first_name,
            'last_name': self.last_name
        }

        self.superuser_not_staff_data = {
            'username': self.superuser_not_staff_username,
            'password': self.password,
            'email': self.superuser_not_staff_email,
            'first_name': self.first_name,
            'last_name': self.last_name
        }

        #self.user = None #G(AccountsUser, is_superuser=False, is_staff=False, **self.user_data)
        self.staff = G(AccountsUser, is_superuser=False, is_staff=True, **self.staff_data)
        self.superuser = G(AccountsUser, is_superuser=True, is_staff=True, **self.superuser_data)
        self.superuser_not_staff = G(AccountsUser, is_superuser=True, is_staff=False, **self.superuser_not_staff_data)

        self.update_data = {
            "username": "changed",
            "email": "changed@email.com",
            "first_name": "changed",
            "last_name": "name"
        }

        self.partial_update_data = {
            "username": "changed_username",
            "email": "changed@email.com"
        }

        self._create_verified_user()
        self._create_unverified_user()

        self.MAP_USER = {
            '': None,
            None: None,
            'user': self.user,
            'staff': self.staff,
            'superuser': self.superuser,
            'superuser_not_staff': self.superuser_not_staff
        }

    def cleanUp(self):
        self.client.logout()

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
        user = get_user_model().objects.create_user(**self.user_data)
        self.user = user
        self.email_object = EmailAddress.objects.create(
            user=user,
            email=self.email,
            verified=True,
            primary=True
        )
        return user

    def _create_unverified_user(self):
        self.user_data_unverified = {
            'username': 'unverified',
            'password': self.password,
            'email': 'unverified@example.com',
            'first_name': self.first_name,
            'last_name': self.last_name
        }
        self.user_unverified = get_user_model().objects.create_user(**self.user_data_unverified)
        self.email_object_unverified = EmailAddress.objects.create(
            user=self.user_unverified,
            email='unverified@example.com',
            verified=False,
            primary=True
        )

    def _client_method(self, url, http_method, data=None):
        if http_method == 'GET':
            response = self.client.get(url, format='json')
        elif http_method == 'POST':
            response = self.client.post(url, data, format='json')
        elif http_method == 'PUT':
            response = self.client.put(url, data, format='json')
        elif http_method == 'PATCH':
            response = self.client.patch(url, data, format='json')
        elif http_method == 'DELETE':
            response = self.client.delete(url, format='json')
        else:
            raise TestException('invalid http_method: %s' % http_method)
        return response

    @parameterise.testcase_method(LOGIN_TESTS)
    def test_basic_login(self, data, http_method, status_code, response_content=None):
        """ Basic test - authenticate a user and try to a http method on user_url """
        response = self._client_method(self.login_url, http_method, data)
        self.assertEquals(response.status_code, status_code, response.data)
        if response_content is not None:
            self.assertEquals(response.content, response_content)

    @parameterise.testcase_method(LOGOUT_TESTS)
    def test_basic_logout(self, http_method, status_code, authentication=None, response_content=None):
        """ Basic test - authenticate a user and try to a http method on logout_url """
        if authentication is not None:
            self.client.force_authenticate(user=self.MAP_USER[authentication])
        response = self._client_method(self.logout_url, http_method)
        self.assertEquals(response.status_code, status_code, response.data)
        if response_content is not None:
            self.assertEquals(response.content, response_content)

    @parameterise.testcase_method(SIGNUP_TESTS)
    def test_basic_signup(self, data, http_method, status_code, mail_count_change=None, response_content=None):
        """ Basic test - authenticate a user and try to a http method on user_url """
        mail_count = len(mail.outbox)
        response = self._client_method(self.register_url, http_method, data)
        self.assertEquals(response.status_code, status_code, response.data)
        if response_content is not None:
            self.assertEquals(response.content, response_content)
        if mail_count_change is not None:
            self.assertEqual(len(mail.outbox), mail_count + mail_count_change)

    @parameterise.testcase_method(PASSWORD_RESET_TESTS)
    def test_basic_password_reset(self, data, http_method, status_code, mail_count_change=None, authentication=None, response_content=None):
        """ Basic test - authenticate a user and try to a http method on user_url """
        mail_count = len(mail.outbox)
        if authentication is not None:
            self.client.force_authenticate(user=self.MAP_USER[authentication])
        response = self._client_method(self.password_reset_url, http_method, data)
        self.assertEquals(response.status_code, status_code, response.data)
        if response_content is not None:
            self.assertEquals(response.content, response_content)
        if mail_count_change is not None:
            self.assertEqual(len(mail.outbox), mail_count + mail_count_change)

    @parameterise.testcase_method(PASSWORD_CHANGE_TESTS)
    def test_basic_password_change(self, data, http_method, status_code, authentication=None, response_content=None):
        """ Basic test - authenticate a user and try to a http method on user_url """
        if authentication is not None:
            self.client.force_authenticate(user=self.MAP_USER[authentication])
        response = self._client_method(self.password_change_url, http_method, data)
        self.assertEquals(response.status_code, status_code, response.data)
        if response_content is not None:
            self.assertEquals(response.content, response_content)

    @parameterise.testcase_method(EMAIL_VERIFICATION_TESTS)
    def test_basic_email_verification(
        self, http_method, status_code, key=None, response_content=None,
        check_login_status_code=None, check_login_response=None
    ):
        """ Basic test - email verification must click verify email link before logging in. """
        if key is None:
            confirmation = EmailConfirmationHMAC(self.email_object_unverified)
            key = confirmation.key
        if http_method == 'GET':
            verify_url = self.verify_url + "?key=" + key
        else:
            verify_url = self.verify_url
        response = self._client_method(verify_url, http_method, {'key': key})
        self.assertEquals(response.status_code, status_code, response.data)
        if response_content is not None:
            self.assertEquals(response.content, response_content)

        # Double check login ?
        if check_login_response is not None and check_login_status_code is not None:
            response = self._client_method(
                self.login_url,
                'POST',
                {'username': 'unverified', 'password': self.PASSWORD}
            )
            self.assertEquals(response.status_code, check_login_status_code, response.data)
            self.assertEquals(response.content, check_login_response)

    @parameterise.testcase_method(PASSWORD_RESET_CONFIRMATION_TESTS)
    def test_basic_password_reset_confirmation(
        self, password_data, http_method, status_code,
        uid=None, token_user=None,
        response_content=None,
        check_login_status_code=None, check_login_response=None,
    ):
        token_data = self._generate_uid_and_token(self.user)

        if uid is None:
            uid = token_data['uid']
            print uid

        if token_user is None:
            token = token_data['token']
        else:
            token = default_token_generator.make_token(self.MAP_USER[token_user])
            print token

        data = password_data
        data['uid'] = uid
        data['token'] = token

        response = self._client_method(
            self.password_reset_confirm_url,
            http_method,
            data
        )
        self.assertEquals(response.status_code, status_code, response.data)
        if response_content is not None:
            self.assertEquals(response.content, response_content)

        # Double check login ?
        if check_login_status_code is not None:
            response = self._client_method(
                self.login_url,
                'POST',
                {'username': self.USERNAME, 'password': 'new_password'}
            )
            self.assertEquals(response.status_code, check_login_status_code, response.data)
        if check_login_response is not None:
            self.assertEquals(response.content, check_login_response)

    # TODO: Change test_api_user_details.py or remove and add tests here
    # @parameterise.testcase_method(USER_DETAILS_TESTS)
    # def test_basic_user_details(self, data, http_method, status_code, authentication=None, response_content=None):
    #     """ Basic test - authenticate a user and try to a http method on user_url """
    #     if authentication is not None:
    #         self.client.force_authenticate(user=self.MAP_USER[authentication])
    #     response = self._client_method(self.password_change_url, http_method, data)
    #     self.assertEquals(response.status_code, status_code, response.data)
    #     if response_content is not None:
    #         self.assertEquals(response.content, response_content)

    def test_integration_signup(
        self, password_data, http_method, status_code,
        uid=None, token_user=None,
        response_content=None,
        check_login_status_code=None, check_login_response=None,
    ):
    pass


    def test_integration_password_reset():
        pass

    def test_integration_password_change():
        pass

    def test_login_logout_get_set_user_details():
        pass



