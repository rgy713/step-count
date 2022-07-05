# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=15, null=True)
    birthday = models.DateField('Birthday', null=True)
    height = models.FloatField('Height')
    weight = models.FloatField('Weight', null=True)
    habbit = models.IntegerField('Habbit', default=0)
    step_size = models.IntegerField('Step Width', default=0)
    gender = models.IntegerField('Gender', default=0)

class DataFiles(models.Model):
    user = models.ForeignKey(User, unique=False, on_delete=models.CASCADE)
    machine_id = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField('File Uploaded Time')
    filename = models.CharField('File Name', max_length=50)

class UserVerify(models.Model):
    user_email = models.EmailField('Email Address of User', max_length=254, blank=True)
    verify_token = models.CharField('Verify Token', max_length=255)
    is_verified = models.IntegerField('Verify Result', default=0)

class StepData(models.Model):
    user = models.ForeignKey(User, unique=False, on_delete=models.CASCADE)
    start_time = models.DateTimeField('Measurement Start Time')
    end_time = models.DateTimeField('Measurement End Time')
    step_size = models.FloatField('Step Size')
    distance = models.FloatField('Distance')
    latitudes = models.TextField('Latitudes')
    longitudes = models.TextField('Longitudes')
    step_histogram = models.TextField('Step histogram')
    step_count = models.IntegerField('Step Count')
    step_level0 = models.IntegerField('Step Narrow', default=0)
    step_level1 = models.IntegerField('Step Slightly Narrow', default=0)
    step_level2 = models.IntegerField('Step Standard', default=0)
    step_level3 = models.IntegerField('Step Slightly Wide', default=0)
    step_level4 = models.IntegerField('Step Wide', default=0)
    activity_name = models.CharField('Activity Name', max_length=255, default='')

class WeightData(models.Model):
    user = models.ForeignKey(User, unique=False, on_delete=models.CASCADE)
    reg_date = models.DateField('Registration Time')
    weight = models.FloatField('Weight')
    target_weight = models.FloatField('Target Weight')
#--------------------------------------------------- version 3----------------------------------------------------------
class FoodData(models.Model):
    name = models.CharField('Food name', max_length=255)

class MealData(models.Model):
    user = models.ForeignKey(User, unique=False, on_delete=models.CASCADE)
    reg_date = models.DateField('Registration Date')
    created_at = models.DateTimeField('Create Time', auto_now_add=True)

class MealInfo(models.Model):
    meal_data = models.ForeignKey(MealData, unique=False, on_delete=models.CASCADE)
    food_data = models.ForeignKey(FoodData, unique=False, on_delete=models.CASCADE)
    breakfast = models.BooleanField('Breakfast')
    lunch = models.BooleanField('Lunch')
    dinner = models.BooleanField('Dinner')

class SleepQuality(models.Model):
    name = models.CharField('SleepQuality name', max_length=255)
    level0 = models.CharField('level0 name', max_length=255)
    level1 = models.CharField('level1 name', max_length=255)
    level2 = models.CharField('level2 name', max_length=255)
    level3 = models.CharField('level3 name', max_length=255)

class SleepData(models.Model):
    user = models.ForeignKey(User, unique=False, on_delete=models.CASCADE)
    bed_time = models.DateTimeField('Bed Time')
    wakeup_time = models.DateTimeField('Wake up Time')
    created_at = models.DateTimeField('Create Time', auto_now_add=True)

class SleepDataInfo(models.Model):
    sleep_data = models.ForeignKey(SleepData, unique=False, on_delete=models.CASCADE)
    sleep_quality = models.ForeignKey(SleepQuality, unique=False, on_delete=models.CASCADE)
    level = models.SmallIntegerField('Sleep level', default=0)