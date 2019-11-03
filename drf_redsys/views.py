import dateutil.parser

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from .models import SermepaTransaction
from .serializers import SermepaResponseSerializer
from .RedsysUtils import decode_parameters
from .choices import ERROR


class CreateSermepaResponse(APIView):
    """
    This view is used to handle RedSys form callbacks containing a
    Sermepa Response
    """
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        # Transform response data to the correct sermepa response fields
        enc_merchant_parameters = request.data.get('_ds__merchant_parameters')
        merchant_parameters = decode_parameters(enc_merchant_parameters)
        merchant_parameters['Ds_Date'] = dateutil.parser.parse(
            merchant_parameters['Ds_Date'].replace(
                '\\', ''), dayfirst=True).strftime('%d/%m/%Y')
        merchant_parameters['Ds_Hour'] = dateutil.parser.parse(
            merchant_parameters['Ds_Hour'].replace(
                '%3A', ':')).strftime('%H:%M')
        merchant_parameters['Ds_Signature'] = \
            request.data.get('_ds__signature')

        # Validate and create sermepa response
        deserializer = SermepaResponseSerializer(
            data=merchant_parameters,
            context={'merchant_parameters': enc_merchant_parameters})
        if deserializer.is_valid():
            deserializer.save()
            # Return expected status code by redsys
            return Response(status=HTTP_200_OK)

        # Update order status and store response validation errors.
        if 'Ds_Order' in merchant_parameters:
            transaction = SermepaTransaction.objects.get(
                merchant_order=merchant_parameters.get('Ds_Order'))
            transaction.status = ERROR
            transaction.status_details = deserializer.errors
            transaction.save()
        else:
            raise Exception("Sermepa response contained errors and didn't"
                            "contain the order indetifier. Find Order with"
                            "pending status.")

        return Response(data=deserializer.errors, status=HTTP_400_BAD_REQUEST)
