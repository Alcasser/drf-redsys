from django.contrib import admin

from .models import SermepaResponse, SermepaTransaction


admin.site.register(SermepaResponse)
admin.site.register(SermepaTransaction)
