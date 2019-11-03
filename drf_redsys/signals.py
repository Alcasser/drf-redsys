import django.dispatch


order_transaction_changed = django.dispatch.Signal(providing_args=["order"])
