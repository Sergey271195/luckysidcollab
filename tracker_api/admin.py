from django.contrib import admin
from .models import BotUser, BotUserProfile, Expense

admin.site.register(BotUser)
admin.site.register(BotUserProfile)
admin.site.register(Expense)


