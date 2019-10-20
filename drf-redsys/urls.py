from django.urls import path

from .views import CreateSermepaResponse


urlpatterns = [
    path('sermepa_responses/', CreateSermepaResponse.as_view(),
    	name='sermepa-responses-url'),
]
