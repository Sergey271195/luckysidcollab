from django.urls import path
from .views import MainApiView, TelegramConnectionView, BotUserApiView, BotUserProfileApiView

urlpatterns = [
    path('', MainApiView.as_view(), name = 'tracker_api'),
    path('telegram/', TelegramConnectionView.as_view(), name = 'telegram_connection'),
    path('user/', BotUserApiView.as_view(), name = 'bot_user'),
    path('expense/', BotUserProfileApiView.as_view(), name = 'expense_view')
]