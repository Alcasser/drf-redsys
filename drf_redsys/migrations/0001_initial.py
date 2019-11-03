# Generated by Django 2.2.6 on 2019-10-20 17:38

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SermepaTransaction',
            fields=[
                ('merchant_order', models.CharField(max_length=12, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Authorized', 'Authorized'), ('Preauthorized', 'Preauthorized'), ('Confirmed', 'Confirmed'), ('Cancelled', 'Cancelled'), ('Refunded', 'Refunded'), ('Rejected', 'Rejected'), ('Error', 'Error')], default='Pending', max_length=20)),
                ('status_details', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='SermepaResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('Ds_Date', models.DateField(blank=True, null=True)),
                ('Ds_Hour', models.TimeField(blank=True, null=True)),
                ('Ds_SecurePayment', models.IntegerField()),
                ('Ds_MerchantData', models.CharField(blank=True, max_length=1024, null=True)),
                ('Ds_Card_Country', models.IntegerField(blank=True, null=True)),
                ('Ds_Card_Type', models.CharField(blank=True, max_length=1, null=True)),
                ('Ds_Terminal', models.IntegerField()),
                ('Ds_MerchantCode', models.CharField(max_length=9)),
                ('Ds_ConsumerLanguage', models.IntegerField(blank=True, null=True)),
                ('Ds_Response', models.CharField(max_length=4)),
                ('Ds_Order', models.CharField(max_length=12)),
                ('Ds_Currency', models.IntegerField()),
                ('Ds_Amount', models.IntegerField()),
                ('Ds_Signature', models.CharField(max_length=256)),
                ('Ds_AuthorisationCode', models.CharField(blank=True, max_length=256, null=True)),
                ('Ds_TransactionType', models.CharField(max_length=1)),
                ('Ds_Merchant_Identifier', models.CharField(blank=True, max_length=40, null=True)),
                ('Ds_ExpiryDate', models.CharField(blank=True, max_length=4, null=True)),
                ('Ds_Merchant_Group', models.CharField(blank=True, max_length=9, null=True)),
                ('Ds_Card_Number', models.CharField(blank=True, max_length=40, null=True)),
                ('sermepa_transaction', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sermepa_responses', to='drf_redsys.SermepaTransaction')),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('sermepa_transaction', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='drf_redsys.SermepaTransaction')),
            ],
        ),
    ]