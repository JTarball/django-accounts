
.. image:: https://www.djangoproject.com/m/img/badges/djangoproject120x25.gif
   :target: http://www.djangoproject.com/

.. image:: https://circleci.com/gh/JTarball/django-accounts/tree/master.svg?style=svg
   :target: https://circleci.com/gh/JTarball/django-accounts/tree/master


django-accounts
===============================
Powered by django-allauth (http://www.intenct.nl/projects/django-allauth/) & includes a modified version of django-rest-auth (https://github.com/Tivix/django-rest-auth)

A basic app that deals with everything to do with front-end users include registration / activation / admin / user preferences.

- registration 
  - - deals with user registration & activation
- user details
  - - user preferences / accounts profiles / definition of accounts Model (User -- settings.AUTH_USER_MODEL)

Built-in Django Admin?
----------------------
The 'normal' django admin is for maintenance (super admin) only and will not be visible for users


The documentation can be found at (once deployed): https://JTarball.github.io/django-accounts/ 


Getting Started
===============

If you're new to django-accounts, you may want to here to get
you up and running:


Installation
------------
Install via setuptools:

.. code-block:: console
    
    python setup.py install

Django 's Configuration
-----------------------
Add ``django_accounts`` to your configuration file (normally settings.py): 

.. code-block:: python

   INSTALLED_APPS =  [
    ...
    'django_accounts',
    ...
   ]


urls.py

.. code-block:: python

    from accounts import urls as urls_accounts
    urlpatterns = [
        ...
        url(r'^{{ cookiecutter.app_name }}/', include(urls_accounts, namespace="accounts")),
        ...
    ]


Post-Installation
-----------------

In your Django root execute the command below to create your database tables::

    ./manage.py migrate

How to Use
==========

Register with POST message
--------------------------
POST - /accounts/registration/    
{
"username": "james.tarball",
"email": "danvir.guram@googlemail.com",
"password1": "mirage27",
"password2": "mirage27"
}

Receive key
-----------
HTTP 201 Created
Allow: POST, OPTIONS, HEAD
Content-Type: application/json
Vary: Accept

{
    "key": "d66914f69aee700c42e50317c2079dad1b073a31"
}
