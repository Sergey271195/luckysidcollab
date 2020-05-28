from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework import serializers
from rest_framework.authtoken.models import Token


import json
import os
import requests

class TelegramBot():

    def __init__(self):

        self.token = os.environ.get('LAVANDA_TOKEN')
        self.url = f'https://api.telegram.org/{self.token}'

    
    def getMe(self):
        
        get_me_url = os.path.join(self.url, 'getMe')
        telegram_response = requests.get(get_me_url)
        tracker_bot = telegram_response.json()
        return tracker_bot

    def sendPhoto(self, user_id, file_location, caption = ''):

        try:
            send_message_url = os.path.join(self.url, 'sendPhoto')
            files = {'photo':(open(file_location, 'rb'))}
            telegram_request = requests.post(send_message_url, data = {'chat_id': user_id, 'caption': caption}, files = files )
            tracker_message= telegram_request.json()
            print(tracker_message)
            return tracker_message
        except Exception as e:
            print(e)

    def sendMessage(self, user_id, text, parse_mode = '', reply_markup = ''):

        send_message_url = os.path.join(self.url, 'sendMessage')
        telegram_request = requests.post(send_message_url, data = {'chat_id': user_id, 'text': text, 'parse_mode': parse_mode, 'reply_markup': reply_markup})
        tracker_message= telegram_request.json()
        print(tracker_message)
        return tracker_message

    def getFile(self, file_id):
        
        get_file_url = os.path.join(self.url, 'getFile')
        telegram_response = requests.post(get_file_url, data = {'file_id': file_id})
        file_instance = telegram_response.json()
        print(file_instance)
        return file_instance


class BotUser(models.Model):
    telegram_id = models.IntegerField(unique=True)
    first_name = models.CharField(max_length = 20, default = '')
    date_joined = models.DateField(auto_now_add=True)

class Expense(models.Model):

    FOOD ='FD'
    SERVICES = 'SV'
    APPLIANCES = 'AP'
    PETROL = 'PT'
    RESTAURANTS = 'RT'

    CATEGORY_CHOICES = [
        (FOOD, 'Продукты'),
        (SERVICES, "Услуги"), 
        (APPLIANCES, 'Техника'),
        (PETROL, 'АЗС'),
        (RESTAURANTS,  'Рестораны'),
    ]

    amount = models.FloatField(null = True, blank = True)

    category = models.CharField(
        max_length = 2,
        choices = CATEGORY_CHOICES,
        default = FOOD
    )

    date = models.DateField(auto_now_add= True)

    user = models.ForeignKey(BotUser, on_delete = models.CASCADE)

    added = models.BooleanField(default  = False)

class BotUserProfile(models.Model):

    user = models.OneToOneField(BotUser, on_delete = models.CASCADE)
    expenses = models.ManyToManyField(Expense)

@receiver(post_save, sender = BotUser)
def create_profile_on_user_creation(sender, instance, *args, **kwargs):
    profile = BotUserProfile(user = instance)
    profile.save()


class BotUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotUser
        fields = ['telegram_id', 'date_joined']

class BotUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotUserProfile
        fields = ['user', 'expenses']

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = [ 'category', 'date', 'amount']



    