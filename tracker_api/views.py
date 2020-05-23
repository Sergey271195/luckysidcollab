from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import requests
import os

from .models import BotUserSerializer, BotUserProfileSerializer, ExpenseSerializer, BotUser, BotUserProfile, Expense


class TelegramBot():

    def __init__(self):

        self.token = 'bot1037758299:AAHXpwE97wXDYzaU3Jqsd1SjNK_zqekQD5c'
        self.url = f'https://api.telegram.org/{self.token}'

    
    def getMe(self):
        
        get_me_url = os.path.join(self.url, 'getMe')
        telegram_response = requests.get(get_me_url)
        tracker_bot = telegram_response.json()
        return tracker_bot

    def getUpdates(self, limit = 100):

        get_updates_url = os.path.join(self.url, 'getUpdates')
        telegram_response = requests.get(get_updates_url, params = {'limit': limit})
        tracker_update = telegram_response.json()
        return tracker_update

    def sendMessage(self, user_id, text):

        send_message_url = os.path.join(self.url, 'sendMessage')
        telegram_request = requests.post(send_message_url, data = {'chat_id': user_id, 'text': text})
        tracker_message= telegram_request.json()
        return tracker_message

    def getUniqueIds(self):
        
        results = self.getUpdates()['result']
        unique_ids = set()
        for result in results:
            unique_ids.add(result['message']['chat']['id'])

        return unique_ids

class MainApiView(View):

    def get(request, *args, **kwargs):
        return(HttpResponse('Tracker Api!'))


class TelegramConnectionView(TemplateView):

    template_name = 'sendMessage.html'
    tgBot = TelegramBot()

    @csrf_exempt
    def get(self, request, *args, **kwargs):

        updates = self.tgBot.getUpdates()

        if request.is_ajax():
            user_id = request.GET.get('user_id')
            user_updates = sorted(list(filter(lambda x: str(x['message']['chat']['id']) == user_id, updates['result'])), key = lambda x : x['message']['date'], reverse = True)
            user_first_name = user_updates[0]['message']['chat']['first_name']
            message = request.GET.get('message')
            if message and message != '':
                message = self.tgBot.sendMessage(user_id, message)
            return(JsonResponse({'update': user_updates, 'username': user_first_name}))
        
        else:

            return(render(request, self.template_name, context = {'user_id': self.tgBot.getUniqueIds()}))


class BotUserApiView(APIView):
    
    def get(self, request, *args, **kwargs):
        telegram_id = request.GET.get('telegram_id')
        try:
            bot_user = BotUser.objects.get(telegram_id = telegram_id)
            serializer = BotUserSerializer(bot_user)
            return(JsonResponse(serializer.data, safe = False))
        except BotUser.DoesNotExist:
            serializer = BotUserSerializer(data = request.GET)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BotUserProfileApiView(APIView):

    def get(self, request, *args, **kwargs):
        telegram_id = request.GET.get('telegram_id')
        bot_user = BotUser.objects.get(telegram_id = telegram_id)
        expenses = BotUserProfile.objects.get(user = bot_user).expenses.all()
        serializer = ExpenseSerializer(expenses, many = True)
        return(JsonResponse(serializer.data, safe = False))

    def post(self, request, *args, **kwargs):
        telegram_id = request.POST.get('telegram_id')
        amount = request.POST.get('amount')
        category = request.POST.get('category')
        bot_user = BotUser.objects.get(telegram_id = telegram_id)
        profile = BotUserProfile.objects.get(user = bot_user)
        serializer = ExpenseSerializer(data = request.data)
        if serializer.is_valid():
            expense = Expense(amount = amount, category = category)
            expense.save()
            profile.expenses.add(expense)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        



    