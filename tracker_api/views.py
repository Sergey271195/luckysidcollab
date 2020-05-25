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
from .constants import CATEGORY_CHOICES, STARTING_CHOICES, CALLBACK_MESSAGES

class MainApiView(APIView):

    tgBot = TelegramBot()

    def returnCategoryKeyboard(self, user):
        self.tgBot.sendMessage(user.telegram_id, 'Choose the category of your expense', reply_markup=createRowKeyboard(CATEGORY_CHOICES))

    def returnStartingKeyboard(self, user):
        self.tgBot.sendMessage(user.telegram_id, 'Choose your next action', reply_markup=createRowKeyboard(STARTING_CHOICES))

    def callbackQueriesHandler(self, notification, user):

        ###Delete unadded expense entries

        if Expense.objects.filter(user = user, added = False).exists():
            Expense.objects.filter(user = user, added = False).delete()
        
        request = notification['callback_query']
        escort_message = request['message'].get('text')
        reply_data = request.get('data')

        if escort_message == CALLBACK_MESSAGES[0]:
            if reply_data == STARTING_CHOICES[0][0]:
                self.returnCategoryKeyboard(user)
            else:
                PlotCreator(user, reply_data)

        elif escort_message == CALLBACK_MESSAGES[1]:
            temporary_expense = Expense(user = user, category = reply_data)
            temporary_expense.save()
            self.tgBot.sendMessage(user.telegram_id, 'Specify the amount spent', reply_markup=json.dumps({'force_reply': True}))


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
                    self.tgBot.sendMessage(user.telegram_id, 'Choose your next action', reply_markup=createRowKeyboard(STARTING_CHOICES))
                else:
                    print('No unadded expenses')
            except Exception as e:
                print(e)
                self.tgBot.sendMessage(user.telegram_id, "You've been providing wrong data!")
                self.tgBot.sendMessage(user.telegram_id, 'Choose your next action', reply_markup=createRowKeyboard(STARTING_CHOICES))

        else:
            if Expense.objects.filter(user = user, added = False).exists():
                Expense.objects.filter(user = user, added = False).delete()
            self.tgBot.sendMessage(user.telegram_id, 'Choose your next action', reply_markup=createRowKeyboard(STARTING_CHOICES))


    def get(self, request, *args, **kwargs):
        return(HttpResponse('Tracker Api!'))

    @csrf_exempt
    def post(self, request, *args, **kwargs):

        notification = json.loads(request.body)
        
        user = self.checkUser(notification)

        self.messageHandler(notification, user)
        
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
        for category in CATEGORY_CHOICES:
            if self.data.filter(category = category[0]).exists():
                self.labels.append(category[1])
                self.plot_data.append(self.data.filter(category = category[0]).aggregate(total_amount = Sum('amount')).get('total_amount'))

        plt.bar(self.labels, self.plot_data)
        plt.savefig(os.path.join(BASE_DIR, f'static/images/bar_{self.user.telegram_id}.png'))
        

    
    def createPiePlot(self):

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


  