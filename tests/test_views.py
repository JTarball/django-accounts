"""
    blog.test_views.py
    ==================

    Test Views for Blog App

"""
import logging

from django.core.urlresolvers import reverse

from django_dynamic_fixture import G
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from tests.models import AccountsUser

logger = logging.getLogger('test_logger')


class ExampleViewTest(APITestCase):

    def setUp(self):
        self.user = G(AccountsUser, is_superuser=False, is_staff=False)
        self.staff = G(AccountsUser, is_superuser=False, is_staff=True)
        self.superadmin = G(AccountsUser, is_superuser=True, is_staff=True)
        self.superadmin_not_staff = G(AccountsUser, is_superuser=True, is_staff=False)
        self.client = APIClient()
        #self.url = reverse('blog:list')

    def test_example_view(self):
        """ Test example. """
        # post = G(Post, author=self.user)
        # count = Post.objects.count()
        # serializer = PostSerializer(post)
        # # Force Authentication and Post
        # self.client.force_authenticate(user=self.superadmin)
        # response = self.client.post(self.url, serializer.data, format='json')
        # # Basic check: slug is the same, created & object count increased
        # self.assertEquals(response.status_code, status.HTTP_201_CREATED, "%s" % response.data)
        # self.assertEquals(Post.objects.count(), count + 1)
        # self.assertEquals(response.data['slug'], post.slug, response.data)
        pass
