import requests
import os

class Webhook():

    def __init__(self):
        self.token = 'bot1037758299:AAHXpwE97wXDYzaU3Jqsd1SjNK_zqekQD5c'
        self.url = f'https://api.telegram.org/{self.token}'


    def setWebhook(self, url):

        set_url = os.path.join(self.url, 'setWebhook')
        webhook = requests.post(set_url, data = {'url': url})
        r = webhook.json()
        print(r)

    def deleteWebhook(self):

        delete_url = os.path.join(self.url, 'deleteWebhook')
        webhook = requests.post(delete_url)
        r = webhook.json()
        print(r)


if __name__ == '__main__':
    Webhook().setWebhook('https://372cf369.ngrok.io/')