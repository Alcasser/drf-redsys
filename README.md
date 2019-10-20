# drf-redsys


This package can be used to add payment support using RedSys.

It is intended to use in one of the following two modes:
* Redsys forms to make client-host payments with optional preauthorization
(user performs the payment using the bank screen and introducing the card information,
business owner captures the payment if preauthorization is enabled).
* **(Future release)** 1-Click mode to allow host-host payments and refunds
using user card references (user adds a new card reference using the bank screen,
so he/she can use it to make automatic payments).


## Installation
1.  Create a [Django](https://www.djangoproject.com) project with [django-rest-framework](https://www.django-rest-framework.org) installed.
2.  Install drf-redsys using `pip`:
```
pip install drf-redsys
```
3.  Add `drf-redsys` to your *INSTALLED_APPS* setting like this:
````
INSTALLED_APPS = [
        ...
        'drf-redsys',
]
````
4.  Include the `drf-redsys` urls in your project urls.py like this:
````
path('drf-redsys/', include('drf-redsys.urls')),
````
2.  Add the following settings:
*This package calls RedSys to perform payments. You need to configure a bank `TPV` first. RedSys will guide you through the different steps in order to get the configuration values and access to the `https://sis-t.redsys.es:25443/canales/` admin panel.*

```
SERMEPA_BASE_URL = 'https://sis-t.redsys.es:25443' (DEVELOPMENT ENVIRONMENT) or 'https://sis.redsys.es' (PRODUCTION ENVIRONMENT)
SERMEPA_MERCHANT_CODE = '999008881'
SERMEPA_TERMINAL = '001'
SERMEPA_SECRET_KEY = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
SERMEPA_CURRENCY = '978'
REDSYS_PREAUTHORIZATION = True (Preauthorization allows you to confirm or cancel payments)
```

## Usage

...