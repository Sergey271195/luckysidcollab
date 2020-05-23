from django.urls import path
from .views import MainApiView, TelegramConnectionView

urlpatterns = [
    path('', MainApiView.as_view(), name = 'tracker_api'),
    path('telegram/', TelegramConnectionView.as_view(), name = 'telegram_connection'),
]