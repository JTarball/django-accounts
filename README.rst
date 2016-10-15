
.. image:: https://www.djangoproject.com/m/img/badges/djangoproject120x25.gif
   :target: http://www.djangoproject.com/

.. image:: https://circleci.com/gh/JTarball/django-accounts/tree/master.svg?style=svg
   :target: https://circleci.com/gh/JTarball/django-accounts/tree/master


django-accounts
===============================
A basic app perfect for something.

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

    urlpatterns = [
        ...
        url(r'^accounts/', include('allauth.urls')),
        ...
    ]


Post-Installation
-----------------

In your Django root execute the command below to create your database tables::

    ./manage.py migrate