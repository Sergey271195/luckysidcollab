import os, requests, sys, io
import subprocess
import speech_recognition as sr


class TelegramSpeechRecognizer():

    def __init__(self, file_id, token):
        self.file_id = file_id
        self.token = token
        self.file_path = f'https://api.telegram.org/{self.token}/getFile?file_id={self.file_id}'
        self.download_link = self.get_data()

    def get_data(self):

        r = requests.get(self.file_path)
        result = r.json()
        url = result['result'].get('file_path')
        download_link = f'https://api.telegram.org/file/{self.token}/{url}'
        return download_link

    def convert_data(self):

        process = subprocess.Popen(['ffmpeg', '-i', self.download_link, '-f', 'wav', '-'], stdout = subprocess.PIPE)
        bytes_data = process.stdout.read()

        audio_data = sr.AudioData(bytes_data, 48000, 2)
        recognizer = sr.Recognizer()
        try:
            transcribed_data = recognizer.recognize_google(audio_data, language = 'ru-RU')
            print("Google Speech Recognition thinks you said " + transcribed_data)
            return(transcribed_data)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            return("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))
            return('Could not request results from Google Speech Recognition service')