"""
    django_accounts.serializers
    ================

    Serializers file for a basic Blog App

"""
from rest_framework import serializers


from models import Example


class ExampleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Example
