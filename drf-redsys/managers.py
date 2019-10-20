from django.db import models

from .choices import PREAUTHORIZED, CONFIRMED


class SermepaTransactionManager(models.Manager):
    """
    Manager for SermepaTransaction model. The primary key merchant_order is
    assigned an incremental value starting from a given order number.
    """

    def create(self, **kwargs):
        transaction = self.model(**kwargs)

        starting_from_order = '2235900000'
        transaction.merchant_order = '%d' % (int(self.all().aggregate(
            models.Max('merchant_order')).get(
            'merchant_order__max') or starting_from_order[:10]) + 1)
        transaction.save()

        return transaction


class ActiveOrdersManagers(models.Manager):
    """
    Manager to return Orders which have a sermepa transaction in preauthorized
    or confirmed status. Used to exclude pending or cancelled orders.
    """
    def get_queryset(self):
        return super(ActiveOrdersManagers, self).get_queryset().filter(
            sermepa_transaction__status__in=[PREAUTHORIZED, CONFIRMED])
