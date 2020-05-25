from django.urls import path
from .views import MainApiView

urlpatterns = [
    path('', MainApiView.as_view(), name = 'tracker_api'),   
]