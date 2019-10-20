from .choices import ERROR
from .RedsysUtils import post_trata_peticion, process_transaction_response


def post_merchant_data(merchant_data, merchant_order):
    """
    Function to send the merchant request data about a merchant order to RedSys
    It is executed asynchronously using django-rq.
    """
    try:
        # Call the trataPeticion web service and parse the response.
        response = post_trata_peticion(merchant_data)

        # Process the call response and check possible errors
        process_transaction_response(response)

        return None

    except Exception as post_error:
        from .models import SermepaTransaction
        error = str(post_error)
        transaction = SermepaTransaction.objects.get(
            merchant_order=merchant_order)
        transaction.status = ERROR
        transaction.status_details = error
        transaction.save()

        return error
