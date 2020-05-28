from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count, Min, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import requests
import os
import json
import re
import datetime
import matplotlib.pyplot as plt



from .models import BotUser, BotUserProfile, Expense, TelegramBot
from .customTg import createRowKeyboard
from telegram_tracker.settings import BASE_DIR
from .constants import CATEGORY_CHOICES, STARTING_CHOICES, CALLBACK_MESSAGES, VOICE_COMMANDS
from .speech import TelegramSpeechRecognizer

def admin_decorator(message):
    def decorator(method):
        def wrapper(self, notification, user, *args, **kwargs):
            if user.telegram_id == int(os.environ.get('ADMIN_TELEGRAM_ID')):
                if 'message' in notification:
                    if notification['message'].get('text') == message:
                        return method(self, notification, user)
        return wrapper
    return decorator

def bot_message_decorator(message):
    def decorator(method_to_execute):
        def wrapper(self, notification, user, *args, **kwargs):
            if 'message' in notification:
                if 'entities' in notification['message']:
                    if notification['message']['entities'][0].get('type') == 'bot_command':
                        if notification['message'].get('text') == message:
                            return method_to_execute(self, notification, user)
        return wrapper
    return decorator


class MainApiView(APIView):

    tgBot = TelegramBot()

    @bot_message_decorator('/add')
    def returnCategoryKeyboard(self, notification, user):
        self.tgBot.sendMessage(user.telegram_id, 'Choose the category of your expense', reply_markup=createRowKeyboard(CATEGORY_CHOICES))
    
    def simpleReturnCategoryKeyboard(self, notification, user):
        self.tgBot.sendMessage(user.telegram_id, 'Choose the category of your expense', reply_markup=createRowKeyboard(CATEGORY_CHOICES))

    @bot_message_decorator('/help')
    def returnStartingKeyboard(self, notification, user):
        self.tgBot.sendMessage(user.telegram_id, 'Choose your next action', reply_markup=createRowKeyboard(STARTING_CHOICES))

    @bot_message_decorator('/datavisualisation')
    def returnPlotKeyboard(self, notification, user):
        self.tgBot.sendMessage(user.telegram_id, 'Choose visualization style', reply_markup=createRowKeyboard(STARTING_CHOICES[1:]))

    @bot_message_decorator('/stat')
    def returnWeekStatistics(self, notification, user):
        self.tgBot.sendMessage(user.telegram_id, 'Choose visualization style')

    @admin_decorator('/users')
    def returnSubscribersList(self, notification, user):
        reply = 'List of current users \n'
        bot_users = BotUser.objects.all()
        for user in bot_users:
            reply += f'{user.first_name} id {user.telegram_id} \n'
        self.tgBot.sendMessage(os.environ.get('ADMIN_TELEGRAM_ID'), reply)

    @admin_decorator('/group_message')
    def sendGroupMessage(self, notification, user):
        current_hour = datetime.datetime.now().hour
        current_time = datetime.datetime.now().time()
        if current_hour < 5 or current_hour > 22:
            greeting_message = 'Good night'
        elif current_hour > 5 and current_hour < 10:
            greeting_message = 'Good morning'
        elif current_hour > 10 and current_hour < 16:
            greeting_message = 'Good day'
        elif current_hour > 16 and current_hour < 22:
            greeting_message = 'Good evening'
        bot_users = BotUser.objects.all()
        for user in bot_users:
            try:
                profile_today = BotUserProfile.objects.get(user=user).expenses.all().filter(date = datetime.datetime.today().date() + datetime.timedelta(days = -0))
                today_amount = profile_today.aggregate(total_amount = Sum('amount')).get('total_amount')
            except Exception as e:
                today_amount = 0
            try:
                profile_yesterday = BotUserProfile.objects.get(user=user).expenses.all().filter(date = datetime.datetime.today().date() + datetime.timedelta(days = -1))
                yesterday_amount = profile_yesterday.aggregate(total_amount = Sum('amount')).get('total_amount')
            except Exception as e:
                yesterday_amount = 0
            if today_amount is None:
                today_amount = 0
            if yesterday_amount is None:
                yesterday_amount = 0
            delta = yesterday_amount - today_amount
            if delta > 0:
                pre_message = f'less by {abs(delta)} \n'
            elif delta < 0:
                pre_message = f'more by {abs(delta)} \n'
            elif delta == 0:
                pre_message = f'exectly the same as yesterday! \n'
            group_message = f"Hello {user.first_name}! This message is halfautomatic! \nIt's used for testing group messages \nCurrent time is : {current_time}\n"
            greet = f"That's why we are saying: {greeting_message}!\n"
            summary = f"Today you've spend {today_amount}. Which is "
            yest = f'That is by the way {yesterday_amount}'
            self.tgBot.sendMessage(user.telegram_id, group_message+greet+summary+pre_message+yest)
    

    def callbackQueriesHandler(self, notification, user):

        ###Delete unadded expense entries

        if Expense.objects.filter(user = user, added = False).exists():
            Expense.objects.filter(user = user, added = False).delete()

        request = notification['callback_query']
        escort_message = request['message'].get('text')
        reply_data = request.get('data')
        if escort_message == CALLBACK_MESSAGES[0]:
            if reply_data == STARTING_CHOICES[0][0]:
                self.simpleReturnCategoryKeyboard(notification, user)
            else:
                PlotCreator(user, reply_data)

        elif escort_message == CALLBACK_MESSAGES[1]:
            temporary_expense = Expense(user = user, category = reply_data)
            temporary_expense.save()
            self.tgBot.sendMessage(user.telegram_id, 'Specify the amount spent', reply_markup=json.dumps({'force_reply': True}))

        elif escort_message == CALLBACK_MESSAGES[2]:
            PlotCreator(user, reply_data)

    def checkUser(self, notification):

        if 'callback_query' in notification:
            request = notification['callback_query']
            user_id = request['message']['chat'].get('id')
            user_first_name = request['message']['chat'].get('first_name')

        else:
            user_id = notification['message']['from'].get('id')
            user_first_name = notification['message']['from'].get('first_name')

        if (not BotUser.objects.filter(telegram_id = int(user_id)).exists()):
            new_user = BotUser(telegram_id = int(user_id), first_name = user_first_name)
            new_user.save()
            print('New user has been created')
            self.tgBot.sendMessage(user_id, "Greetings and welcome. You've been added to our small db. Wish you a nice stay. If you have any complaints, contact LuckySid! ;)")
        
        user = BotUser.objects.get(telegram_id = int(user_id))
        return user
        

    def messageHandler(self, notification, user):
        
        if 'callback_query' in notification:
            self.callbackQueriesHandler(notification, user)

        mess = notification.get('message')
        if mess:
            voice = mess.get('voice')
            if voice:
                file_id = voice.get('file_id')

                tsr = TelegramSpeechRecognizer(file_id, os.environ.get('LAVANDA_TOKEN'))
                response = tsr.convert_data()
                if response:
                    if any([voice_command in response.lower() for voice_command in VOICE_COMMANDS]):
                        if VOICE_COMMANDS[0] in response.lower():
                            self.tgBot.sendMessage(user.telegram_id, f"Привет, {user.first_name}")
                        if VOICE_COMMANDS[1] in response.lower():
                            self.tgBot.sendMessage(user.telegram_id, f"Сейчас {datetime.datetime.now().strftime('%H:%M:%S')}")
                        if VOICE_COMMANDS[2] in response.lower():
                            self.tgBot.sendMessage(user.telegram_id, f"Мои создатели еще не придумали мне имя")
                        if VOICE_COMMANDS[3] in response.lower():
                            self.tgBot.sendMessage(user.telegram_id, f"Пока, {user.first_name}")
                    else:
                        self.tgBot.sendMessage(user.telegram_id, f"Google Speech Recognition считает, что ты сказал: {response}")
                else:
                    self.tgBot.sendMessage(user.telegram_id, f"Google Speech Recognition could not understand audio")


            elif notification['message'].get('reply_to_message') and notification['message']['reply_to_message'].get('text') == 'Specify the amount spent':
                try:
                    amount = float(notification['message'].get('text'))
                    if Expense.objects.filter(user = user, added = False).exists():
                        latest_expense = Expense.objects.get(user = user, added = False)
                        latest_expense.amount = amount
                        latest_expense.added = True
                        latest_expense.save()
                        BotUserProfile.objects.get(user = user).expenses.add(latest_expense)
                        self.tgBot.sendMessage(user.telegram_id, "Your data has been added to the database!")
                    else:
                        print('No unadded expenses')
                except Exception as e:
                    print(e)
                    self.tgBot.sendMessage(user.telegram_id, "You've been providing wrong data!")
            else:
                if Expense.objects.filter(user = user, added = False).exists():
                    Expense.objects.filter(user = user, added = False).delete()


    def get(self, request, *args, **kwargs):
        return(HttpResponse('Tracker Api!'))

    @csrf_exempt
    def post(self, request, *args, **kwargs):

        notification = json.loads(request.body)
        
        user = self.checkUser(notification)

        

        self.returnCategoryKeyboard(notification = notification, user = user)
        self.returnStartingKeyboard(notification = notification, user = user)
        self.returnPlotKeyboard(notification = notification, user = user)

        self.messageHandler(notification, user)

        ### For admin

        self.returnSubscribersList(notification = notification, user = user)
        self.sendGroupMessage(notification = notification, user = user)
        
        print(user.first_name)
        print(json.dumps(notification, indent=4))

        return(JsonResponse({'status_code': 200}))



class PlotCreator():

    def __init__(self, user, plot_type):
        self.user = user
        self.type = plot_type
        self.data = BotUserProfile.objects.get(user = user).expenses.all()
        self.labels = []
        self.plot_data = []
        self.file_location = f'static/images/{self.type}_{self.user.telegram_id}.png'
        self.tgBot = TelegramBot()
        if self.type == STARTING_CHOICES[1][0]:
            self.createWeekTable()
            self.message = 'Weekly table...'
        elif self.type == STARTING_CHOICES[2][0]:
            self.createBarPlot()
            self.message = 'Bar plot...'
        elif self.type == STARTING_CHOICES[3][0]:
            self.createPiePlot()
            self.message = 'Pie plot...'
        self.tgBot.sendPhoto(user.telegram_id, self.file_location, self.message)

    def createBarPlot(self):
        plt.clf()
        for category in CATEGORY_CHOICES:
            if self.data.filter(category = category[0]).exists():
                self.labels.append(category[1])
                self.plot_data.append(self.data.filter(category = category[0]).aggregate(total_amount = Sum('amount')).get('total_amount'))

        plt.bar(self.labels, self.plot_data)
        plt.savefig(os.path.join(BASE_DIR, f'static/images/bar_{self.user.telegram_id}.png'))
        

    
    def createPiePlot(self):
        plt.clf()
        for category in CATEGORY_CHOICES:
            if self.data.filter(category = category[0]).exists():
                self.labels.append(category[1])
                self.plot_data.append(self.data.filter(category = category[0]).aggregate(total_amount = Sum('amount')).get('total_amount'))

        
        fig, axs = plt.subplots(1, 2)
        pie = axs[0].pie(self.plot_data, autopct='%.1f%%', pctdistance = 1.4)
        axs[1].axis('off')
        axs[1].legend(pie[0], self.labels,
            title="Категории",
            loc="center")
        plt.savefig(os.path.join(BASE_DIR, f'static/images/pie_{self.user.telegram_id}.png'))
        return('Pie plot...')

    def createWeekTable(self):
        plt.clf()
        self.labels = ['Дата'] + [category[1] for category in CATEGORY_CHOICES] + ['Итог']

        for i in range(0, 6):
            day = datetime.datetime.today().date() + datetime.timedelta(days = -i)
            day_query = self.data.filter(date = day)
            day_data = [day]
            total_for_day = day_query.aggregate(total_amount = Sum('amount')).get('total_amount')
            for category in CATEGORY_CHOICES:
                if day_query.filter(category = category[0]).exists():
                    day_data.append(day_query.filter(category = category[0]).aggregate(total_amount = Sum('amount')).get('total_amount'))
                else:
                    day_data.append(0)
            day_data.append(total_for_day)
            self.plot_data.append(day_data)

        plt.figure()
        ax = plt.gca()
        ax.axis('off')
        table = plt.table(	
            cellText = self.plot_data, colLabels = self.labels, cellLoc= 'center', loc = 'center'
        )
        table.scale(1, 3)
        plt.savefig(os.path.join(BASE_DIR, f'static/images/table_{self.user.telegram_id}.png'))
        return('Weekly table...')

    def createWeeklyStatisticsMessage(self):
        pass


  