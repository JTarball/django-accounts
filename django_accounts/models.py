"""
    django_accounts.models
    ===========

    Models file for a basic Blog App

"""
import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractUser


# Get instance of logger
logger = logging.getLogger('project_logger')


class AccountsUser(AbstractUser):
    USERNAME_FIELD = 'username'  # name of field on the User that is used as the unique identfier.
    activation_key = models.CharField(_('activation key'), max_length=40)
    # Extra Profile Fields
    is_subscribed = models.BooleanField(
        _('subscribed'),
        default=False,
        help_text=_('Designates whether the user can is subscribed to the newsletter.')
    )
    # Previous Email
    _previous_email = None
    from_rest_api = False
    ###########################################################################
    # Note Django User has the following fields so dont Duplicate!
    ###########################################################################
    # id
    # username
    # first_name
    # last_name
    # email
    # password
    # is_staff
    # is_active
    # is_superuser
    # last_login
    # date_joined
    ###########################################################################
    # future
    # bio = models.TextField()
    # failed_login_attempts = models.PositiveIntegerField(default=0, editable=False)
    # last_login_attempt_ip = models.CharField(default='', max_length=45, editable=False)

    def __init__(self, *args, **kwargs):
        super(AccountsUser, self).__init__(*args, **kwargs)
        self._previous_email = self.email
        self.from_rest_api = False

    # def save(self, *args, **kwargs):
    #     self._previous_email = self.email
    #     super(AccountsUser, self).save(*args, **kwargs)



from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from allauth.account.models import EmailAddress


# allauth create a new record in EmailAddress when you signup
# therefore we have to ensure that we create an email address
# when we create a user via e.g. create_user create
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_update_allauth_email(sender, instance=None, created=False, update_fields=None, **kwargs):
    logger.error("se der: %s", sender)
    logger.warn("%s %s",instance.email, instance._previous_email)
    # We basically have to perform the actions of send_email_confirmation
    # We created a bastardized version that does the following:
    # creates an EmailAddress
    # send a confirmation email if new and not verified
    email_changed = instance._previous_email is not None and instance._previous_email != instance.email
    logger.error("email_changed, %s", email_changed)
    if (created or email_changed) and not instance.from_rest_api:
        try:
            EmailAddress.objects.get_for_user(
                instance,
                instance.email
            )
            logger.error("found")
        except EmailAddress.DoesNotExist:
            # To keep with allauth we need to update rather than create a new
            # record if the email has changed
            try:
                previous_emailaddress = EmailAddress.objects.get_for_user(
                    instance,
                    instance._previous_email
                )
                email = previous_emailaddress
                email.email = instance.email
                email.save()
            except EmailAddress.DoesNotExist:
                email = EmailAddress.objects.create(
                            user=instance,
                            email=instance.email,
                            primary=True,
                            verified=False
                        )
                email.send_confirmation(request=None, signup=True)


from rest_framework.authtoken.models import Token


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
