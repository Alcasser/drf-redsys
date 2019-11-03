import ast
import json
import base64
import hashlib
import hmac
import pyDes
import zeep
import xmltodict

from django.conf import settings
from django.urls import reverse
from django.apps import apps
from .choices import AUTHORIZED, PREAUTHORIZED, CANCELLED, REJECTED,\
    CONFIRMED, REFUNDED, ERROR


# See "TPV-Virtual Manual Integracion - Web Service
AUTHORIZATION_ORDER = '0'
PREAUTHORIZATION_ORDER = '1'
CONFIRMATION_ORDER = '2'
REFUND_ORDER = '3'
CANCELLATION_ORDER = '9'

# Sermepa transaction status details
SUCCESSFUL_TRANSACTION = "The transaction has completed successfully"
REJECTED_TRANSACTION = 'The transaction has been rejected. Please check ' \
                       'error code {}'
UNRECOGNIZED_RESPONSE_CODE = 'The transaction response code is not recognized'
TRANSACTION_TYPE_CODE_MISMATCH = "The transaction type and response code " \
                                 "combination doesn't make sense"

CANCELLED_TRANSACTION = "The transaction has already been cancelled"

# Response codes
SIS_CALL_OK = '0'

SERMEPA_SIGNATURE_VERSION = 'HMAC_SHA256_V1'
SERMEPA_FORM_URL = "{}/sis/realizarPago".format(settings.SERMEPA_BASE_URL)
SERMEPA_WSDL_URL = "{}/sis/services/SerClsWSEntrada/wsdl/SerClsWSEntrada.wsdl".format(settings.SERMEPA_BASE_URL)

# Set authorization type depending if using preauthorization or not
AUTHORIZATION_TYPE = PREAUTHORIZATION_ORDER if \
    settings.REDSYS_PREAUTHORIZATION else AUTHORIZATION_ORDER


def get_formatted_amount(order_amount):
    """
    Returns the decimal order_amount in the format expected by RedSys.
    Example: 20,00 -> 2000
    """
    return int(round(float(order_amount) * 100))


def get_authorization_merchant_data_using_reference(
        order_amount, merchant_order, card_reference):
    """
    Return the ws request data to perform an authorized transaction sending
    the user card reference (Ds_Merchant_Identifier, 1 Click)
    """
    amount = get_formatted_amount(order_amount)
    merchant_data = {
        'DS_MERCHANT_AMOUNT': amount,
        'DS_MERCHANT_ORDER': merchant_order,
        'DS_MERCHANT_MERCHANTCODE': settings.SERMEPA_MERCHANT_CODE,
        'DS_MERCHANT_CURRENCY': settings.SERMEPA_CURRENCY,
        'DS_MERCHANT_TRANSACTIONTYPE': AUTHORIZATION_TYPE,
        'DS_MERCHANT_TERMINAL': settings.SERMEPA_TERMINAL,
        'DS_MERCHANT_IDENTIFIER': card_reference
    }
    return generate_ws_call_data(merchant_data, merchant_order)


def get_confirmation_merchant_data(order_amount, merchant_order):
    """
    Returns the ws request data to confirm a preauthorization
    """
    amount = get_formatted_amount(order_amount)
    merchant_data = {
        'DS_MERCHANT_AMOUNT': amount,
        'DS_MERCHANT_ORDER': merchant_order,
        'DS_MERCHANT_MERCHANTCODE': settings.SERMEPA_MERCHANT_CODE,
        'DS_MERCHANT_CURRENCY': settings.SERMEPA_CURRENCY,
        'DS_MERCHANT_TRANSACTIONTYPE': CONFIRMATION_ORDER,
        'DS_MERCHANT_TERMINAL': settings.SERMEPA_TERMINAL
    }
    return generate_ws_call_data(merchant_data, merchant_order)


def get_cancellation_merchant_data(order_amount, merchant_order):
    """
    Returns the ws request data to cancel a preauthorization
    """
    amount = get_formatted_amount(order_amount)
    merchant_data = {
        'DS_MERCHANT_AMOUNT': amount,
        'DS_MERCHANT_ORDER': merchant_order,
        'DS_MERCHANT_MERCHANTCODE': settings.SERMEPA_MERCHANT_CODE,
        'DS_MERCHANT_CURRENCY': settings.SERMEPA_CURRENCY,
        'DS_MERCHANT_TRANSACTIONTYPE': CANCELLATION_ORDER,
        'DS_MERCHANT_TERMINAL': settings.SERMEPA_TERMINAL
    }
    return generate_ws_call_data(merchant_data, merchant_order)


def generate_ws_call_data(merchant_data, merchant_order):
    # Build the request xml and computhe the signature using the merchant
    # private key
    signature_data = xmltodict.unparse(
        {"DATOSENTRADA": merchant_data},
        full_document=False
    )
    signature = compute_signature(
        merchant_order, signature_data.encode('utf-8'),
        settings.SERMEPA_SECRET_KEY)

    # Return the data used in the trataPeticion request
    return {
        "REQUEST": {
            "DATOSENTRADA": merchant_data,
            'DS_SIGNATUREVERSION': SERMEPA_SIGNATURE_VERSION,
            'DS_SIGNATURE': signature.decode(),
        },
    }


def get_authorization_form(order_amount, merchant_order, ok_url, ko_url,
    merchant_data='', request_card_reference=False, card_reference=None):

    amount = get_formatted_amount(order_amount)
    data = {
        'DS_MERCHANT_ORDER': merchant_order,
        'DS_MERCHANT_TRANSACTIONTYPE': AUTHORIZATION_TYPE,
        'DS_MERCHANT_CURRENCY': settings.SERMEPA_CURRENCY,
        'DS_MERCHANT_URLOK': ok_url,
        'DS_MERCHANT_URLKO': ko_url,
        'DS_MERCHANT_MERCHANTCODE': settings.SERMEPA_MERCHANT_CODE,
        'DS_MERCHANT_MERCHANTURL': reverse('sermepa-responses-url'),
        'DS_MERCHANT_MERCHANTDATA': str(merchant_data),
        'DS_MERCHANT_TERMINAL': settings.SERMEPA_TERMINAL,
        'DS_MERCHANT_AMOUNT': amount,
    }

    if request_card_reference:
        data['DS_MERCHANT_IDENTIFIER'] = 'REQUIRED'

    if card_reference:
        data['DS_MERCHANT_IDENTIFIER'] = card_reference

    parameters = json.dumps(data)
    Ds_MerchantParameters = base64.b64encode(parameters.encode())
    Ds_Signature = compute_signature(merchant_order, Ds_MerchantParameters,
                                     settings.SERMEPA_SECRET_KEY)

    return {
        'Ds_SignatureVersion': SERMEPA_SIGNATURE_VERSION,
        'Ds_MerchantParameters': Ds_MerchantParameters.decode(),
        'Ds_Signature': Ds_Signature.decode(),
        'redsys_url': SERMEPA_FORM_URL
    }


def compute_signature(salt, payload, key, urlsafe=False):
    '''
    For Redsys:
        salt = order number (Ds_Order or Ds_Merchant_Order)
        payload = Ds_MerchantParameters
        key = shared secret (aka key) from the Redsys Administration Module
              (Merchant Data Query option in the "See Key" section)
    '''

    bkey = base64.b64decode(key)
    des3 = pyDes.triple_des(bkey, mode=pyDes.CBC,
                            IV='\0' * 8, pad='\0',
                            padmode=pyDes.PAD_NORMAL)
    pepper = des3.encrypt(salt.encode('utf-8'))
    payload_hash = hmac.new(pepper, payload, hashlib.sha256).digest()
    if urlsafe:
        return base64.urlsafe_b64encode(payload_hash)
    return base64.b64encode(payload_hash)


def post_trata_peticion(merchant_data):
    """
    This function can be used to post a given transaction merchant data. The
    trataPeticion web service is used.
    """
    data_xml = xmltodict.unparse(merchant_data)
    client = zeep.Client(SERMEPA_WSDL_URL)
    response = client.service.trataPeticion(data_xml)
    response_dict = xmltodict.parse(response)
    return response_dict.get('RETORNOXML', {})


def process_transaction_response(response_data):
    from .serializers import SermepaResponseSerializer

    # Check if the response contains an integration error
    integration_code = response_data.get('CODIGO')
    if integration_code != SIS_CALL_OK:
        raise Exception(
            f'Redsys integration error with code {integration_code}')

    # Deserialize the sermepa response and assign the related order
    response_serializer = SermepaResponseSerializer(
        data=response_data.get('OPERACION', {}))
    if response_serializer.is_valid():
        response_serializer.save()
    else:
        raise Exception(f'Validation error in sermepa response '
                        f'{response_serializer.errors}')


def decode_parameters(Ds_MerchantParameters):
    Ds_MerchantParameters_decoded = base64.b64decode(
        Ds_MerchantParameters)
    return ast.literal_eval(
        Ds_MerchantParameters_decoded.decode(encoding='utf-8'))


def get_transaction_status_and_details(transaction_type, response_code):
    """
    This function returns the corresponding RedSys transaction status based on
    its type and the received response code.
    """

    # Transaction ok for authorizations and preauthorizations
    if response_code < 100:
        if transaction_type == AUTHORIZATION_ORDER:
            return AUTHORIZED, SUCCESSFUL_TRANSACTION
        elif transaction_type == PREAUTHORIZATION_ORDER:
            return PREAUTHORIZED, SUCCESSFUL_TRANSACTION
        else:
            return ERROR, TRANSACTION_TYPE_CODE_MISMATCH

    # Transaction ok for refunds and confirmations
    if response_code == 900:
        if transaction_type == CONFIRMATION_ORDER:
            return CONFIRMED, SUCCESSFUL_TRANSACTION
        elif transaction_type == REFUND_ORDER:
            return REFUNDED, SUCCESSFUL_TRANSACTION
        else:
            return ERROR, TRANSACTION_TYPE_CODE_MISMATCH

    # Transaction ok for cancellations
    if response_code == 400:
        if transaction_type == CANCELLATION_ORDER:
            return CANCELLED, SUCCESSFUL_TRANSACTION
        else:
            return ERROR, TRANSACTION_TYPE_CODE_MISMATCH

    # Different errors which cause the transaction rejection.
    if 100 < response_code < 10000:
        return REJECTED, REJECTED_TRANSACTION.format(response_code)

    return ERROR, UNRECOGNIZED_RESPONSE_CODE
