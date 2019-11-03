# drf-redsys


This package can be used to add payment support using RedSys.

It uses Redsys *Redirección* mode to make client-host payments with optional preauthorization
(user performs the payment using the bank screen and introducing the card information,
business owner captures the payment if preauthorization is enabled).

**Notes**: 
* Your client web application will be the responsible of executing the payments using the server generated RedSys form (see [Manual de integración con el TPV Virtual para
comercios con conexión por Redirección](https://canales.redsys.es/canales/ayuda/documentacion/Manual%20integracion%20para%20conexion%20por%20Redireccion.pdf))
* You need to configure a bank *TPV* first. RedSys will guide you through the different steps in order to get the configuration values and access to the `https://sis-t.redsys.es:25443/canales/` admin panel.

## Installation
1.  Create a [Django](https://www.djangoproject.com) project with [django-rest-framework](https://www.django-rest-framework.org) installed.
2.  Install drf-redsys using `pip`:
```
pip install drf-redsys
```
3.  Add `drf_redsys` to your *INSTALLED_APPS* setting like this:
````
INSTALLED_APPS = [
        ...
        'drf_redsys', (with underscore)
]
````
4. Run `./manage.py migrate drf_redsys` in order to create the needed model tables.

5.  Include the `drf-redsys` urls in your project urls.py like this:
````
path('drf-redsys/', include('drf-redsys.urls')),
````
6.  Add your *TPV* values in the django settings. Please note you should use different values for the `development` and `production` settings:

```
SERMEPA_BASE_URL = 'https://sis-t.redsys.es:25443' (DEVELOPMENT ENVIRONMENT) or 'https://sis.redsys.es' (PRODUCTION ENVIRONMENT)
SERMEPA_MERCHANT_CODE = '999008881'
SERMEPA_TERMINAL = '001'
SERMEPA_SECRET_KEY = 'sq7HjrUOBfKmC576ILgskD5srU870gJ7'
SERMEPA_CURRENCY = '978'
REDSYS_PREAUTHORIZATION = True (Preauthorization allows you to confirm or cancel payments)
```
If you set `REDSYS_PREAUTHORIZATION` to False the payments will automatically be captured when the user introduces the card information and performs the payment. If you set this configuration to True, you will need to use the `Order.confirm_preauthorization` or `Order.cancel_preauthorization` methods to complete the transaction.

## Usage example

In order to add payments support to a model called `Rental`. You need to extend the `Order` model:

`````
class Rental(Order):
    start = models.DateField()
    end = models.DateField()
    offer = models.ForeignKey(Offer, related_name='rentals',
                              on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='rentals',
                             on_delete=models.CASCADE)
    
    def 
`````

Let's say your web app makes a post request to an endpoint `/rentals`. You can create a view and a serializer to handle this request. The `RentalSerializer` needs to have a method field to return the RedSys form values used to perform the payment (or a message if the order has already been executed) and include the `status` property (possible values are `PENDING`, `PREAUTHORIZED`, `AUTHORIZED`, `CONFIRMED`, `CANCELLED` and `REJECTED`)

`````
class RentalSerializer(serializers.ModelSerializer):
    rental_state = serializers.SerializerMethodField()
    
    class Meta:
        model = Rental
        fields = ('user', 'offer', 'start', 'end', 'rental_state', 'uuid',
                  'status', 'created')
    
    def get_rental_state(self, rental):
        return rental.get_order_state()
`````

The post response will contain the serialized instance including the form values (used to generate the html form) and the order status.

`````
"rentalState": {
        "Ds_SignatureVersion": "HMAC_SHA256_V1",
        "Ds_MerchantParameters": "eyM...wOwO0=",
        "Ds_Signature": "Y807dGAEi4W...PtVG3SsgB7GkJvrtJA=",
        "redsysUrl": "https://sis-t.redsys.es:25443/sis/realizarPago"
    },
"status": "Pending",
`````

