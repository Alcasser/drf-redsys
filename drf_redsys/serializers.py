from django.conf import settings

from rest_framework import serializers

from .models import SermepaResponse, SermepaTransaction
from .RedsysUtils import compute_signature


class SermepaResponseSerializer(serializers.ModelSerializer):
    """
    This serializer is used to deserialize a Sermepa Response.
    The source of this response can be a form callback from RedSys or a
    web service (Host to Host) response.
    """
    Ds_Date = serializers.DateField(input_formats=['%d/%m/%Y'], required=False)
    Ds_Hour = serializers.TimeField(input_formats=['%H:%M'], required=False)

    class Meta:
        model = SermepaResponse
        fields = '__all__'

    def validate(self, attrs):
        transaction = SermepaTransaction.objects.get(
            merchant_order=attrs.get('Ds_Order'))

        # Set payload to verify signature depending if the response is from
        # a form callback or a web service response
        merchant_parameters = self.context.get('merchant_parameters')
        if merchant_parameters:
            payload = merchant_parameters
            urlsafe = True
        else:
            payload = f'{attrs.get("Ds_Amount")}{attrs.get("Ds_Order")}' \
                f'{attrs.get("Ds_MerchantCode")}' \
                f'{attrs.get("Ds_Currency")}{attrs.get("Ds_Response")}' \
                f'{attrs.get("Ds_TransactionType")}' \
                f'{attrs.get("Ds_SecurePayment")}'
            urlsafe = False

        key = settings.SERMEPA_SECRET_KEY
        signature = compute_signature(
            transaction.merchant_order, payload.encode(), key.encode(),
            urlsafe)

        # Raise error if signatures mismatch
        if signature.decode() != attrs.get("Ds_Signature"):
            raise serializers.ValidationError(
                'Response signature mismatch. Possible attack')

        return attrs

    def create(self, validated_data):
        # Create the response and assign the related transaction
        transaction = SermepaTransaction.objects.get(
            merchant_order=validated_data.get('Ds_Order'))
        sermepa_response = SermepaResponse.objects.create(
            sermepa_transaction=transaction, **validated_data)

        # Update the transaction status based on the sermepa response
        sermepa_response.update_transaction_status()

        return sermepa_response
