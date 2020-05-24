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
import json
import re


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

    def sendMessage(self, user_id, text, parse_mode = ''):

        send_message_url = os.path.join(self.url, 'sendMessage')
        telegram_request = requests.post(send_message_url, data = {'chat_id': user_id, 'text': text, 'parse_mode': parse_mode})
        tracker_message= telegram_request.json()
        return tracker_message

    def getUniqueIds(self):
        
        results = self.getUpdates()['result']
        unique_ids = set()
        for result in results:
            unique_ids.add(result['message']['chat']['id'])

        return unique_ids

class MainApiView(APIView):

    tgBot = TelegramBot()

    def checkUser(self, notification):

        user_id = notification['message']['from'].get('id')

        if (not BotUser.objects.filter(telegram_id = int(user_id)).exists()):
            new_user = BotUser(telegram_id = int(user_id))
            new_user.save()
            print('New user has been created')
            self.tgBot.sendMessage(user_id, "Greetings and welcome. You've been added to our small db. Wish you a nice stay. If you have any complaints, contact LuckySid! ;)")

        user = BotUser.objects.get(telegram_id = int(user_id))
        return user

    def messageHandler(self, notification, user):

        message = notification['message'].get('text')

        if message == 'data':
            print('Data request')
            expenses = BotUserProfile.objects.get(user = user).expenses.all()
            for expense in expenses:
                response = ''
                response += f'Date: {expense.date} \n'
                response += f'Amount: {expense.amount} \n'
                response += f'Category: {expense.get_category_display()} \n'
                self.tgBot.sendMessage(user.telegram_id, response, 'HTML')

        elif message.find('send') != -1:

            amount = re.search(r'amount:(\s)?(?P<amount>(\d+)(.(\d+))?)', message)
            category = re.search(r'category:(\s)?(?P<category>(\w{2}\b))', message)           

            if amount and category:
                post_dict = {'amount': amount.group('amount'), 'category': category.group('category').upper()}
                serializer = ExpenseSerializer(data = post_dict)
                if serializer.is_valid():
                    expense = Expense(amount = post_dict.get('amount'), category = post_dict.get('category'))
                    expense.save()
                    BotUserProfile.objects.get(user = user).expenses.add(expense)
                    self.tgBot.sendMessage(user.telegram_id, "Your data has been added to db!")
                else:
                    print(serializer.errors)
                    self.tgBot.sendMessage(user.telegram_id, "You've been providing wrong data!")

            else:
                self.tgBot.sendMessage(user.telegram_id, "You've been providing wrong data!")

        elif message == 'help':

            categories = 'Available categories: \n FD (FOOD) \n SV (SERVICES) \n AP (APPLIANCES) \n PT (PETROL) \n RT (RESTAURANTS)\n'
            methods = "Available methods: \n data - get list of your expenses \n send amount: (money you've spent) category: (one of the available categories) - to add data to database \n"
            check = "check users - just for informational purposes"
            self.tgBot.sendMessage(user.telegram_id, categories+methods+check, 'HTML')

        elif message == 'check users':
            users = BotUser.objects.all()
            response = ''
            for u in users:
                response += f'{u.telegram_id} \n'

            self.tgBot.sendMessage(user.telegram_id, response, 'HTML')



    def get(self, request, *args, **kwargs):
        return(HttpResponse('Tracker Api!'))

    @csrf_exempt
    def post(self, request, *args, **kwargs):

        notification = json.loads(request.body)
        
        user = self.checkUser(notification)

        self.messageHandler(notification, user)
        
        print(user)
        print(notification)

        return(JsonResponse({'status_code': 200}))


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
        



    