from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views import View

import requests
import os


my_id = 540863534
anton_id = 21509678

class TelegramBot():

    def __init__(self):

        self.token = 'bot1037758299:AAHXpwE97wXDYzaU3Jqsd1SjNK_zqekQD5c'
        self.url = f'https://api.telegram.org/{self.token}'

    
    def getMe(self):
        
        get_me_url = os.path.join(self.url, 'getMe')
        telegram_response = requests.get(get_me_url)
        tracker_bot = telegram_response.json()
        return tracker_bot

    def getUpdates(self):

        get_updates_url = os.path.join(self.url, 'getUpdates')
        telegram_response = requests.get(get_updates_url)
        tracker_update = telegram_response.json()
        return tracker_update

    def sendMessage(self, user_id, text):

        send_message_url = os.path.join(self.url, 'sendMessage')
        telegram_request = requests.post(send_message_url, data = {'chat_id': user_id, 'text': text})
        tracker_message= telegram_request.json()
        return tracker_message

class MainApiView(View):

    def get(request, *args, **kwargs):
        return(HttpResponse('Tracker Api!'))


class TelegramConnectionView(View):

    tgBot = TelegramBot()

    def get(self, request, *args, **kwargs):

        return(JsonResponse(self.tgBot.getUpdates()))
        


    def post(self, request, *args, **kwargs):
        
        # To send reponse use valid user_id

        message = self.tgBot.sendMessage(my_id, 'Test123')

        return(JsonResponse(self.tgBot.getUpdates()))

    