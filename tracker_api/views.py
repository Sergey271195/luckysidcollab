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

from .models import BotUser, BotUserProfile, Expense
from .customTg import createRowKeyboard, TelegramBot
from telegram_tracker.settings import BASE_DIR
from .constants import CATEGORY_CHOICES, STARTING_CHOICES, CALLBACK_MESSAGES, GREETING_OPTIONS, HELP_MESSAGE, TIMEPERIOD_CHOICES


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

def callback_query_decorator(callback_message, callback_data):
    def decorator(method_to_execute):
        def wrapper(self, notification, user, *args, **kwargs):
            if 'callback_query' in notification:
                if 'message' in notification['callback_query']:
                    if notification['callback_query']['message'].get('text') == callback_message:
                        if notification['callback_query'].get('data') == callback_data:
                            return method_to_execute(self, notification, user)
        return wrapper
    return decorator


def reply_message_decorator(reply_message):
    def decorator(method_to_execute):
        def wrapper(self, notification, user):
            if notification.get('message'):
                if notification['message'].get('reply_to_message'):
                    if notification['message']['reply_to_message'].get('text') == reply_message:
                        return method_to_execute(self, notification, user)
        return wrapper
    return decorator


class MainApiView(APIView):

    tgBot = TelegramBot()

    @bot_message_decorator('/add')
    def returnCategoryKeyboard(self, notification, user):
        self.tgBot.sendMessage(user.telegram_id, 'Выберите категорию затрат', reply_markup=createRowKeyboard(CATEGORY_CHOICES))

    @bot_message_decorator('/start')
    def returnGreetingMessage(self, notification, user):
        self.tgBot.sendMessage(user.telegram_id, GREETING_OPTIONS[0])

    @bot_message_decorator('/help')
    def returnStartingKeyboard(self, notification, user):
        self.tgBot.sendMessage(user.telegram_id, HELP_MESSAGE[0])

    @bot_message_decorator('/datavisualisation')
    def returnPlotKeyboard(self, notification, user):
        self.tgBot.sendMessage(user.telegram_id, 'Формат предоставления данных', reply_markup=createRowKeyboard(STARTING_CHOICES[1:3]))

    @bot_message_decorator('/stat')
    def returnWeekStatistics(self, notification, user):
        PlotCreator(user = user).createWeeklyStatisticsMessage()

    @reply_message_decorator(reply_message = 'Сумма затрат')
    def pushDataToPostgres(self, notification, user):
        try:
            amount = float(notification['message'].get('text'))
            if amount > 0:
                if Expense.objects.filter(user = user, added = False).exists():
                    latest_expense = Expense.objects.get(user = user, added = False)
                    latest_expense.amount = amount
                    latest_expense.added = True
                    latest_expense.save()
                    BotUserProfile.objects.get(user = user).expenses.add(latest_expense)
                    self.tgBot.sendMessage(user.telegram_id, "Запись успешно добавлена в базу данных!")
                else:
                    print('No unadded expenses')
            else:
                self.tgBot.sendMessage(user.telegram_id, "Вами предоставлены некорректные данные.\nСумма должна быть неотрицательным числом")
        except Exception as e:
            print(e)
            self.tgBot.sendMessage(user.telegram_id, "Вами предоставлены некорректные данные.\nСумма должна быть неотрицательным числом")
            if Expense.objects.filter(user = user, added = False).exists():
                Expense.objects.filter(user = user, added = False).delete()
   
    

    def callbackQueriesHandler(self, notification, user):

        if 'callback_query' in notification:

            ###Delete unadded expense entries

            if Expense.objects.filter(user = user, added = False).exists():
                Expense.objects.filter(user = user, added = False).delete()

            request = notification['callback_query']
            escort_message = request['message'].get('text')
            reply_data = request.get('data')
            

            if escort_message == CALLBACK_MESSAGES[0]:
                temporary_expense = Expense(user = user, category = reply_data)
                temporary_expense.save()
                self.tgBot.sendMessage(user.telegram_id, 'Сумма затрат', reply_markup=json.dumps({'force_reply': True}))
            
            
            elif escort_message == CALLBACK_MESSAGES[1]:
                if reply_data == STARTING_CHOICES[1][0]:
                    self.tgBot.sendMessage(user.telegram_id, 'Выберите временной интервал для построения столбчатой диаграммы', reply_markup=createRowKeyboard(TIMEPERIOD_CHOICES))
                elif reply_data == STARTING_CHOICES[2][0]:
                    self.tgBot.sendMessage(user.telegram_id, 'Выберите временной интервал для построения круговой диаграммы', reply_markup=createRowKeyboard(TIMEPERIOD_CHOICES))
            
            elif escort_message == CALLBACK_MESSAGES[2]:
                PlotCreator(user = user).createBarPlot(timeperiod = reply_data)

            elif escort_message == CALLBACK_MESSAGES[3]:
                PlotCreator(user = user).createPiePlot(timeperiod = reply_data)

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

        user = BotUser.objects.get(telegram_id = int(user_id))
        return user
        
    def get(self, request, *args, **kwargs):
        return(HttpResponse('Tracker Api!'))

    @csrf_exempt
    def post(self, request, *args, **kwargs):

        notification = json.loads(request.body)
        user = self.checkUser(notification)

        self.returnGreetingMessage(notification = notification, user = user)
        self.returnCategoryKeyboard(notification = notification, user = user)
        self.returnStartingKeyboard(notification = notification, user = user)
        self.returnPlotKeyboard(notification = notification, user = user)
        self.returnWeekStatistics(notification = notification, user = user)
        self.pushDataToPostgres(notification = notification, user = user)
        self.callbackQueriesHandler(notification = notification, user = user)

        return(JsonResponse({'status_code': 200}))



class PlotCreator():

    def __init__(self, user):
        self.user = user
        self.data = BotUserProfile.objects.get(user = user).expenses.all()
        self.labels = []
        self.plot_data = []
        self.tgBot = TelegramBot()
        self.today = datetime.datetime.now()


    def choose_data(self, timeperiod):

        if timeperiod == TIMEPERIOD_CHOICES[0][0]:
            timed_data = self.get_current_week()
            message_data = TIMEPERIOD_CHOICES[0][1].lower()
        elif timeperiod == TIMEPERIOD_CHOICES[1][0]:
            timed_data = self.get_last_week()
            message_data = TIMEPERIOD_CHOICES[1][1].lower()
        elif timeperiod == TIMEPERIOD_CHOICES[2][0]:
            timed_data = self.get_current_month()
            message_data = TIMEPERIOD_CHOICES[2][1].lower()
        elif timeperiod == TIMEPERIOD_CHOICES[3][0]:
            timed_data = self.get_last_month()
            message_data = TIMEPERIOD_CHOICES[3][1].lower()
        elif timeperiod == TIMEPERIOD_CHOICES[4][0]:
            timed_data = self.get_current_year()
            message_data = TIMEPERIOD_CHOICES[4][1].lower()
        return (timed_data, message_data)

    def get_current_week(self):

        self.today = datetime.datetime.now()
        current_weekday = datetime.datetime.now().weekday()
        current_week = (datetime.datetime.now() - datetime.timedelta(days = current_weekday)).date()
        data_for_current_week = self.data.filter(date__gte = current_week)

        return data_for_current_week

    def get_last_week(self):

        current_weekday = self.today.weekday()
        current_week = (self.today - datetime.timedelta(days = current_weekday)).date()
        last_week = current_week - datetime.timedelta(days = 7)
        data_for_last_week = self.data.filter(date__gte = last_week).filter(date__lt = current_week)
        
        return data_for_last_week

    def get_current_month(self):

        current_month = datetime.datetime(self.today.year, self.today.month, 1).date()
        data_for_current_month = self.data.filter(date__gte = current_month)
        
        return data_for_current_month

    def get_last_month(self):

        current_month = datetime.datetime(self.today.year, self.today.month, 1).date()
        last_month = datetime.datetime(self.today.year, self.today.month - 1, 1).date()
        data_for_last_month = self.data.filter(date__gte = last_month).filter(date__lt = current_month)
        
        return data_for_last_month

    def get_current_year(self):

        current_year = datetime.datetime(self.today.year, 1, 1).date()
        data_for_current_year = self.data.filter(date__gte = current_year)
        
        return data_for_current_year
            

    def createBarPlot(self, timeperiod):
        data, message = self.choose_data(timeperiod)
        if data:
            plt.clf()
            for category in CATEGORY_CHOICES:
                if data.filter(category = category[0]).exists():
                    self.labels.append(category[1])
                    self.plot_data.append(data.filter(category = category[0]).aggregate(total_amount = Sum('amount')).get('total_amount'))

            plt.bar(self.labels, self.plot_data)
            plt.savefig(os.path.join(BASE_DIR, f'static/images/bar_{self.user.telegram_id}.png'))

            self.file_location = f'static/images/bar_{self.user.telegram_id}.png'
            self.tgBot.sendPhoto(self.user.telegram_id, self.file_location, 'Столбчатая диаграмма '+ message)
        else:
            self.tgBot.sendMessage(self.user.telegram_id, 'Нет информации '+ message)
        
    
    def createPiePlot(self, timeperiod):
        data, message = self.choose_data(timeperiod)
        if data:
            plt.clf()
            for category in CATEGORY_CHOICES:
                if data.filter(category = category[0]).exists():
                    self.labels.append(category[1])
                    self.plot_data.append(data.filter(category = category[0]).aggregate(total_amount = Sum('amount')).get('total_amount'))

            
            fig, axs = plt.subplots(1, 2)
            pie = axs[0].pie(self.plot_data, autopct='%.1f%%', pctdistance = 1.4)
            axs[1].axis('off')
            axs[1].legend(pie[0], self.labels,
                title="Категории",
                loc="center")
            plt.savefig(os.path.join(BASE_DIR, f'static/images/pie_{self.user.telegram_id}.png'))

            self.file_location = f'static/images/pie_{self.user.telegram_id}.png'
            self.tgBot.sendPhoto(self.user.telegram_id, self.file_location, 'Круговая диаграмма '+ message)
        else:
            self.tgBot.sendMessage(self.user.telegram_id, 'Нет информации '+ message)



    def createWeeklyStatisticsMessage(self):

        ### Current week
        
        data_for_current_week = self.get_current_week()
        total_current_week = data_for_current_week.aggregate(total_amount = Sum('amount')).get('total_amount')

        ### Last week
        
        data_for_last_week = self.get_last_week()
        total_last_week = data_for_last_week.aggregate(total_amount = Sum('amount')).get('total_amount')

        ### Current month

        current_month = self.get_current_month()
        total_current_month = current_month.aggregate(total_amount = Sum('amount')).get('total_amount')

        ### Last month

        last_month = self.get_last_month()
        total_last_month = last_month.aggregate(total_amount = Sum('amount')).get('total_amount')

        ### Current year

        current_year = self.get_current_year()
        total_current_year = current_year.aggregate(total_amount = Sum('amount')).get('total_amount')
        
        result_week_data = {}
        if total_last_week and total_last_week != 0:
            response_data = data_for_last_week
        else:
            response_data = data_for_current_week

        
        for category in CATEGORY_CHOICES:
            if response_data.filter(category = category[0]).exists():
                result_week_data[category[1]] = response_data.filter(category = category[0]).aggregate(total_amount = Sum('amount')).get('total_amount')
            else:
                result_week_data[category[1]] = 0
        
        sorted_results = {k: v for k, v in sorted(result_week_data.items(), key =  lambda item: -item[1])}
        top_expenses = list(sorted_results.items())[:3]        

        if total_last_week and total_last_week != 0:
            starting_message = f'За прошедшую неделю вами было потрачено: {total_last_week} рублей.\nСамые крупные категории затрат:\n'
            ending_message = f'За текущую неделю вами было потрачено: {total_current_week} рублей.\n'
        else:
            starting_message = f'За текущую неделю вами было потрачено: {total_current_week} рублей.\nСамые крупные категории затрат:\n'
            ending_message = f''

        expenses_message = ''
        for index, entry in enumerate(top_expenses):
            if entry[1] != 0:
                expenses_message += f'\t\t\t\t\t\t\t\t{index+1}. {entry[0]} {entry[1]} рублей\n'

        if total_last_month and total_last_month != 0:
            last_month_message = f'За прошлый месяц : {total_last_month} рублей\n'
        else:
            last_month_message = ''
        
        current_month_message = f'За текущий месяц : {total_current_month} рублей\n'
        current_year_message = f'За текущий год : {total_current_year} рублей\n'

        result_message = starting_message + expenses_message + ending_message + current_month_message + last_month_message + current_year_message

        self.tgBot.sendMessage(self.user.telegram_id, result_message, parse_mode = 'HTML')
        


  