from uuid import uuid4
from django.db import models

from .choices import STATUS, PREAUTHORIZED, PENDING
from .managers import SermepaTransactionManager, ActiveOrdersManagers
from .RedsysUtils import get_transaction_status_and_details,\
    get_authorization_form, get_confirmation_merchant_data,\
    get_cancellation_merchant_data
from .tasks import post_merchant_data
from .signals import order_transaction_changed


class SermepaTransaction(models.Model):
    """
    This model stores the status and id of a sermepa transaction.
    Redsys expects merchant_order to be an incremental value which can't be
    repeated.
    """
    merchant_order = models.CharField(primary_key=True, max_length=12)
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20,
                              choices=STATUS,
                              default=PENDING)
    status_details = models.TextField(blank=True)

    objects = SermepaTransactionManager()


class SermepaResponse(models.Model):
    """
    This model stores a transaction response and is used to update the related
    transaction status.
    """
    creation_date = models.DateTimeField(auto_now_add=True)
    sermepa_transaction = models.ForeignKey(
        SermepaTransaction, related_name='sermepa_responses',
        on_delete=models.CASCADE, null=True)

    Ds_Date = models.DateField(blank=True, null=True)
    Ds_Hour = models.TimeField(blank=True, null=True)
    Ds_SecurePayment = models.IntegerField()
    Ds_MerchantData = models.CharField(max_length=1024, blank=True, null=True)
    Ds_Card_Country = models.IntegerField(null=True, blank=True)
    Ds_Card_Type = models.CharField(max_length=1, null=True, blank=True)
    Ds_Terminal = models.IntegerField()
    Ds_MerchantCode = models.CharField(max_length=9)
    Ds_ConsumerLanguage = models.IntegerField(null=True, blank=True)
    Ds_Response = models.CharField(max_length=4)
    Ds_Order = models.CharField(max_length=12)
    Ds_Currency = models.IntegerField()
    Ds_Amount = models.IntegerField()
    Ds_Signature = models.CharField(max_length=256)
    Ds_AuthorisationCode = models.CharField(max_length=256, null=True,
                                            blank=True)
    Ds_TransactionType = models.CharField(max_length=1)
    Ds_Merchant_Identifier = models.CharField(max_length=40,
                                              null=True, blank=True)
    Ds_ExpiryDate = models.CharField(max_length=4, null=True, blank=True)
    Ds_Merchant_Group = models.CharField(max_length=9, null=True, blank=True)
    Ds_Card_Number = models.CharField(max_length=40, null=True, blank=True)

    def update_transaction_status(self):
        transaction_type = self.Ds_TransactionType
        response_code = int(self.Ds_Response)
        status, details = get_transaction_status_and_details(
            transaction_type, response_code)
        self.sermepa_transaction.status = status
        self.sermepa_transaction.status_details = details
        self.sermepa_transaction.save()
        order_transaction_changed.send(
            sender=Order, order=self.sermepa_transaction.order)

    def __str__(self):
        return f'Response from order: ' \
               f'{self.sermepa_transaction.merchant_order} - ' \
               f'response code: {self.Ds_Response}'


class Order(models.Model):
    """
    This class is used by other apps to add payments support.
    Has a related SermepaTransaction used to call RedSys and perform the
    payment.
    """
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(primary_key=True, default=uuid4,
                            editable=False)
    sermepa_transaction = models.OneToOneField(SermepaTransaction,
                                               on_delete=models.CASCADE,
                                               null=True)
    objects = models.Manager()
    active = ActiveOrdersManagers()

    @property
    def status(self):
        return None if self.sermepa_transaction is None else \
            self.sermepa_transaction.status

    def get_order_amount(self):
        raise NotImplementedError('You need to provide the order amount used '
                                  'in the payment')

    def get_ok_url(self):
        raise NotImplementedError('You need to provide a OK url used '
                                  'by RedSys to redirect the user after a '
                                  'successful payment')

    def get_ko_url(self):
        raise NotImplementedError('You need to provide a KO url used '
                                  'by RedSys to redirect the user after a '
                                  'failed payment')

    def is_preauthorized(self):
        return self.sermepa_transaction.status == PREAUTHORIZED

    def get_status_error(self):
        return {"userError": f"This order is in "
                             f"{self.sermepa_transaction.status} status"}

    def confirm_preauthorization(self):
        """
        This method is used to confirm the Order. It can be called when the
        related sermepa_transaction is in preauthorized status, otherwise a
        error message is returned.
        """
        if not self.is_preauthorized():
            return self.get_status_error()

        data = get_confirmation_merchant_data(
            self.get_order_amount(), self.sermepa_transaction.merchant_order)

        # Call as blocking request and return transaction result
        # (error message or None)
        return post_merchant_data(
            data, self.sermepa_transaction.merchant_order)

    def cancel_preauthorization(self):
        """
        It can be called when the related sermepa_transaction is in
        preauthorized status, otherwise a error message is returned.
        """
        if not self.is_preauthorized():
            return self.get_status_error()

        data = get_cancellation_merchant_data(
            self.get_order_amount(), self.sermepa_transaction.merchant_order)

        # Call as blocking request and return transaction result
        # (error message or None)
        return post_merchant_data(
            data, self.sermepa_transaction.merchant_order)

    def get_order_state(self):
        """
        This function is called from a Order serializer to perform the Order
        transaction
        """

        # Create the corresponding SermepaTransaction if not exists
        if not self.sermepa_transaction:
            self.sermepa_transaction = SermepaTransaction.objects.create()
            self.save()

        if self.status != PENDING:
            return {'message': 'Order already executed'}

        # Return a form to perform the transaction using the bank screen
        return get_authorization_form(
            self.get_order_amount(),
            self.sermepa_transaction.merchant_order, self.get_ko_url(),
            self.get_ko_url())
