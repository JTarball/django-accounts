"""
    tests.test_api_user_details.py
    ==============================

    Tests the REST API calls for user details

"""
from django_dynamic_fixture import G

from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from django_accounts.models import AccountsUser

from utils import parameterise


class TestUserDetails(APITestCase):
    """
        User Detail Tests
        =================
    """
    GET_TESTS = [
        {
            'test_name': 'test_get_user_details_forbidden_if_not_logged_in',
            'test_description': 'Tests getting of user details fail if not logged in',
            'authentication': None,
            'status_code': status.HTTP_403_FORBIDDEN,
            'response_content': '{"detail":"Authentication credentials were not provided."}'
        },
        {
            'test_name': 'test_get_user_details_for_basic_user',
            'test_description': 'Tests getting of user details if logged in as a basic user',
            'authentication': 'user',
            'status_code': status.HTTP_200_OK,
            'response_content': '{"username":"jtarball","email":"jtarball@example.com","first_name":"James","last_name":"Tarball"}'
        },
        {
            'test_name': 'test_get_user_details_for_staff_user',
            'test_description': 'Tests getting of user details if logged in as a staff user',
            'authentication': 'staff',
            'status_code': status.HTTP_200_OK,
            'response_content': '{"username":"admin","email":"admin@example.com","first_name":"James","last_name":"Tarball"}'
        },
        {
            'test_name': 'test_get_user_details_for_superuser',
            'test_description': 'Tests getting of user details if logged in as a superuser user',
            'authentication': 'superuser',
            'status_code': status.HTTP_200_OK,
            'response_content': '{"username":"superuser","email":"superuser@email.com","first_name":"James","last_name":"Tarball"}'
        },
        {
            'test_name': 'test_get_user_details_for_superuser_not_staff',
            'test_description': 'Tests getting of user details if logged in as a superuser but not staff user',
            'authentication': 'superuser_not_staff',
            'status_code': status.HTTP_200_OK,
            'response_content': '{"username":"superuser_not_staff","email":"superuser_not_staff@email.com","first_name":"James","last_name":"Tarball"}'
        },
    ]
    POST_TESTS = [
        {
            'test_name': 'test_post_user_details_forbidden_if_not_logged_in',
            'test_description': 'Tests post of user details fail if not logged in',
            'authentication': None,
            'status_code': status.HTTP_403_FORBIDDEN,
            'response_content': '{"detail":"Authentication credentials were not provided."}'
        },
        {
            'test_name': 'test_post_user_details_for_basic_user',
            'test_description': 'Tests post of user details if logged in as a basic user',
            'authentication': 'user',
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"POST\\" not allowed."}'
        },
        {
            'test_name': 'test_post_user_details_for_staff_user',
            'test_description': 'Tests post of user details if logged in as a staff user',
            'authentication': 'staff',
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"POST\\" not allowed."}'
        },
        {
            'test_name': 'test_post_user_details_for_superuser',
            'test_description': 'Tests post of user details if logged in as a superuser user',
            'authentication': 'superuser',
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"POST\\" not allowed."}'
        },
        {
            'test_name': 'test_post_user_details_for_superuser_not_staff',
            'test_description': 'Tests post of user details if logged in as a superuser but not staff user',
            'authentication': 'superuser_not_staff',
            'status_code': status.HTTP_405_METHOD_NOT_ALLOWED,
            'response_content': '{"detail":"Method \\"POST\\" not allowed."}'
        },
    ]
    PUT_TESTS = [
        {
            'test_name': 'test_put_user_details_forbidden_if_not_logged_in',
            'test_description': 'Tests put of user details fail if not logged in',
            'authentication': None,
            'status_code': status.HTTP_403_FORBIDDEN,
            'response_content': '{"detail":"Authentication credentials were not provided."}'
        },
        {
            'test_name': 'test_put_user_details_for_basic_user',
            'test_description': 'Tests put of user details if logged in as a basic user',
            'authentication': 'user',
            'status_code': status.HTTP_200_OK,
            'response_content': '{"username":"changed","email":"changed@email.com","first_name":"changed","last_name":"name"}'
        },
        {
            'test_name': 'test_put_user_details_for_staff_user',
            'test_description': 'Tests put of user details if logged in as a staff user',
            'authentication': 'staff',
            'status_code': status.HTTP_200_OK,
            'response_content': '{"username":"changed","email":"changed@email.com","first_name":"changed","last_name":"name"}'
        },
        {
            'test_name': 'test_put_user_details_for_superuser',
            'test_description': 'Tests put of user details if logged in as a superuser user',
            'authentication': 'superuser',
            'status_code': status.HTTP_200_OK,
            'response_content': '{"username":"changed","email":"changed@email.com","first_name":"changed","last_name":"name"}'
        },
        {
            'test_name': 'test_put_user_details_for_superuser_not_staff',
            'test_description': 'Tests put of user details if logged in as a superuser but not staff user',
            'authentication': 'superuser_not_staff',
            'status_code': status.HTTP_200_OK,
            'response_content': '{"username":"changed","email":"changed@email.com","first_name":"changed","last_name":"name"}'
        },
    ]
    PATCH_TESTS = [
        {
            'test_name': 'test_patch_user_details_forbidden_if_not_logged_in',
            'test_description': 'Tests patch of user details fail if not logged in',
            'authentication': None,
            'status_code': status.HTTP_403_FORBIDDEN,
            'response_content': '{"detail":"Authentication credentials were not provided."}'
        },
        {
            'test_name': 'test_patch_user_details_for_basic_user',
            'test_description': 'Tests patch of user details if logged in as a basic user',
            'authentication': 'user',
            'status_code': status.HTTP_200_OK,
            'response_content':  '{"username":"changed_username","email":"changed@email.com","first_name":"James","last_name":"Tarball"}'
        },
        {
            'test_name': 'test_patch_user_details_for_staff_user',
            'test_description': 'Tests patch of user details if logged in as a staff user',
            'authentication': 'staff',
            'status_code': status.HTTP_200_OK,
            'response_content':  '{"username":"changed_username","email":"changed@email.com","first_name":"James","last_name":"Tarball"}'
        },
        {
            'test_name': 'test_patch_user_details_for_superuser',
            'test_description': 'Tests patch of user details if logged in as a superuser user',
            'authentication': 'superuser',
            'status_code': status.HTTP_200_OK,
            'response_content':  '{"username":"changed_username","email":"changed@email.com","first_name":"James","last_name":"Tarball"}'
        },
        {
            'test_name': 'test_patch_user_details_for_superuser_not_staff',
            'test_description': 'Tests patch of user details if logged in as a superuser but not staff user',
            'authentication': 'superuser_not_staff',
            'status_code': status.HTTP_200_OK,
            'response_content':  '{"username":"changed_username","email":"changed@email.com","first_name":"James","last_name":"Tarball"}'
        },
    ]

    def setUp(self):
        self.client = APIClient()
        self.user_url = reverse('accounts:rest_user_details')
        self.login_url = reverse('accounts:rest_login')
        self.logout_url = reverse('accounts:rest_logout')

        self.email = 'jtarball@example.com'
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

        self.user = G(AccountsUser, is_superuser=False, is_staff=False, **self.user_data)
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

        self.MAP_USER = {
            None: None,
            'user': self.user,
            'staff': self.staff,
            'superuser': self.superuser,
            'superuser_not_staff': self.superuser_not_staff
        }

    def cleanUp(self):
        self.client.logout()

    @parameterise.testcase_method(GET_TESTS)
    def test_get_user_details(self, authentication, status_code, response_content):
        """ Basic test - authenticate a user and try to a http method on user_url """
        self.client.force_authenticate(user=self.MAP_USER[authentication])
        response = self.client.get(self.user_url, format='json')
        self.assertEquals(response.status_code, status_code)
        self.assertEquals(response.content, response_content)

    @parameterise.testcase_method(POST_TESTS)
    def test_post_user_details(self, authentication, status_code, response_content):
        """ Test to post update user details. """
        self.client.force_authenticate(user=self.MAP_USER[authentication])
        response = self.client.post(self.user_url, self.update_data, format='json')
        self.assertEquals(response.status_code, status_code)
        self.assertEquals(response.content, response_content)

    @parameterise.testcase_method(PUT_TESTS)
    def test_put_user_details(self, authentication, status_code, response_content):
        """ Test to put update user details. """
        self.client.force_authenticate(user=self.MAP_USER[authentication])
        response = self.client.put(self.user_url, self.update_data, format='json')
        self.assertEquals(response.status_code, status_code)
        self.assertEquals(response.content, response_content)

    @parameterise.testcase_method(PATCH_TESTS)
    def test_patch_user_details(self, authentication, status_code, response_content):
        """ Test to patch update user details. """
        self.client.force_authenticate(user=self.MAP_USER[authentication])
        response = self.client.patch(self.user_url, self.partial_update_data, format='json')
        self.assertEquals(response.status_code, status_code)
        self.assertEquals(response.content, response_content)
