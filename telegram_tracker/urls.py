from django.contrib import admin
from django.urls import path, include
from .webhook import Webhook

###Setting webhook connection

Webhook().setWebhook()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tracker_api.urls')),
]

