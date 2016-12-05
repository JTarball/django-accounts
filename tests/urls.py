"""
    tests.urls
    ===========

    URLs for testing purposes ONLY

    you can add to TestCase / APITestCase:

    def ExampleTestClass(TestCase):
        urls = 'tests.urls'

"""
from django.conf.urls import patterns, url, include
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter

from django_accounts.registration.views import SocialLoginView
from django_accounts import urls as urls_accounts


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter

urlpatterns = patterns(
    '',
    url(r'^social-login/facebook/$', FacebookLogin.as_view(), name='fb_login'),
    url(r'^accounts/', include(urls_accounts, namespace="accounts")),
    url(r'^account/', include('allauth.urls')),
)
