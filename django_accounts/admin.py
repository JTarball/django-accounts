#!/usr/bin/env python
"""
    django_accounts.admin
    =====================

    Admin Functionality for django_accounts App

"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from django_accounts.models import AccountsUser


class AccountsUserAdmin(UserAdmin):
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('username', 'email', 'is_staff', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'username')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

    # fieldsets = (
    #  (None, {'fields': ('email', 'password')}),
    #  ('Personal info', {'fields': ('first_name', 'last_name')}),
    #  ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups.', 'user_permissions')}),
    #  ('Important dates', {'fields': ('last_login',)}),
    # )
    # Fields for adding a new user form in admin
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'email', 'password1', 'password2')
            }
        ),
    )

# Register the user forms to django admin for super-duper editing
admin.site.register(AccountsUser, AccountsUserAdmin)

