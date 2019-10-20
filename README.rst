# drf-redsys


This package can be used to add payment support using RedSys.

You can use this package in two modes:
* Redsys forms to make client-host payments with optional preauthorization
(user performs the payment using the bank screen and introducing the card information,
business owner captures the payment if preauthorization is enabled).
* (Future release) One-click mode to allow host-host payments and refunds
using user card references (user adds a new card reference using the bank screen,
so he/she can use it to make automatic payments).


## Installation

1. Create a [Django](https://www.djangoproject.com) project and install [django-rest-framework](https://www.django-rest-framework.org)

2. Install drf-redsys using `pip`:

```
pip install drf-redsys
```




This package calls RedSys to perform payments. You need to configure a bank `TPV` first and you will receive some 