from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework import serializers
from rest_framework.authtoken.models import Token

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



    