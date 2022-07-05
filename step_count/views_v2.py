# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import json
import os
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt

from .models import DataFiles, FoodData, SleepQuality, MealData, MealInfo, SleepData, SleepDataInfo, WeightData
from .models import UserProfile, StepData
from django.db import connection

# Create your views here.

def validate_date(str_date):
    try:
        datetime.strptime(str_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")

#################################################### VERSION 2 #########################################################

@csrf_exempt
def v2_data_upload(request):
    response_data = {}

    if request.method == 'POST' and request.FILES['data']:
        email = request.POST['email']
        machine_id = request.POST['machine_id']
        data_file = request.FILES['data']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_USER'

            return JsonResponse(response_data)

        user_profile = UserProfile.objects.get(user_id=user.id)

        dir_path = os.path.join(settings.MEDIA_ROOT, str(user.id))

        now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            data_info = DataFiles.objects.get(user_id=user.id, machine_id=machine_id)
            data_info.machine_id = machine_id
            data_info.uploaded_at = now_time
            data_info.filename = data_file.name
        except DataFiles.DoesNotExist:
            data_info = DataFiles(
                user_id=user.id,
                machine_id=machine_id,
                uploaded_at=now_time,
                filename=data_file.name
            )
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

        try:
            data_info.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_DATA_SAVE'

            return JsonResponse(response_data)

        fs = FileSystemStorage(dir_path)

        step_data = csv.reader(data_file)

        step_data_dict = {}

        write_rows = []

        user_height = user_profile.height / 100.0

        for row in step_data:
            if not len(row) == 8:
                continue
            if str(row[0]) in step_data_dict.keys():
                one_data = step_data_dict[str(row[0])]
            else:
                one_data = {
                    'start_time' : '',
                    'end_time' : '',
                    'step_size' : 0.0,
                    'distance' : 0.0,
                    'latitudes' : [],
                    'longitudes' : [],
                    'step_count' : 0,
                    'step_level0' : 0,
                    'step_level1' : 0,
                    'step_level2' : 0,
                    'step_level3' : 0,
                    'step_level4' : 0,
                    'histogram_data' : {}
                }

            write_rows.append(','.join(row) + '\n')
            one_data['start_time'] = str(row[0])
            step_count_one = int(row[1])
            one_data['step_count'] += step_count_one
            one_data['distance'] += float(row[2])
            step_size = float(row[3])
            one_data['end_time'] = str(row[5])
            one_data['latitudes'].append("{0:.7f}".format(float(row[6])))
            one_data['longitudes'].append("{0:.7f}".format(float(row[7])))

            if step_size < user_height * 0.315:
                one_data['step_level0'] += step_count_one
            elif step_size < user_height * 0.405:
                one_data['step_level1'] += step_count_one
            elif step_size < user_height * 0.495:
                one_data['step_level2'] += step_count_one
            elif step_size < user_height * 0.585:
                one_data['step_level3'] += step_count_one
            else:
                one_data['step_level4'] += step_count_one

            key = str(int(step_size * 100 / 5) * 5)
            if key in one_data['histogram_data'].keys():
                one_data['histogram_data'][key] += step_count_one
            else:
                one_data['histogram_data'][key] = step_count_one

            step_data_dict[str(row[0])] = one_data

        for key in step_data_dict.keys():
            one = step_data_dict[key]
            step_data_info = StepData(
                user_id = user.id,
                start_time = one['start_time'],
                end_time = one['end_time'],
                step_size = one['distance']/one['step_count'],
                distance = one['distance'],
                latitudes = ','.join(one['latitudes']),
                longitudes = ','.join(one['longitudes']),
                step_histogram = json.dumps(one['histogram_data']),
                step_count = one['step_count'],
                step_level0 = one['step_level0'],
                step_level1 = one['step_level1'],
                step_level2 = one['step_level2'],
                step_level3 = one['step_level3'],
                step_level4 = one['step_level4'],
            )

            try:
                step_data_info.save()
            except:
                response_data['type'] = 'error'
                response_data['content'] = 'ERR_STEP_DATA_SAVE'

                return JsonResponse(response_data)

        if fs.exists(name=machine_id):
            with open(os.path.join(dir_path, machine_id), "a") as myfile:
                myfile.writelines(write_rows)
        else:
            try:
                filename = fs.save(machine_id, data_file)
            except:
                response_data['type'] = 'error'
                response_data['content'] = 'ERR_FILE_SAVE'

                return JsonResponse(response_data)

        # uploaded_file_url = fs.url(filename)
        response_data['type'] = 'success'

        return JsonResponse(response_data)

    response_data['type'] = 'error'
    response_data['content'] = 'ERR_NO_FILE'

    return JsonResponse(response_data)


@csrf_exempt
def v2_get_main_data(request):
    email = request.GET.get('email', None)
    try:
        timezone = int(request.GET['timezone'])
    except:
        timezone = 540

    sign = "-" if timezone < 0 else "+"
    h = str(timezone / 60)
    m = str(timezone % 60)
    h = h if len(h) == 2 else "0" + h
    m = m if len(m) == 2 else "0" + m

    timezone = "{}{}:{}".format(sign, h, m)

    response_data = {}

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'

        return JsonResponse(response_data)

    user_profile = UserProfile.objects.get(user_id=user.id)

    now_utc_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    cursor = connection.cursor()

    sql = """SELECT 
              SUM(distance) AS distance, 
              SUM(step_count) AS step_count,
              DATE_FORMAT(CONVERT_TZ(start_time,'+00:00','%s'),'%%Y-%%m-%%d') AS date 
            FROM step_count_stepdata 
            WHERE user_id=%s 
              AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 6 DAY)
            GROUP BY date
            ORDER BY date 
         """ % (timezone, user.id, now_utc_time)

    cursor.execute(sql)
    ret = cursor.fetchall()

    distance_7 = 0.
    step_count_7 = 0
    step_count_week = {}
    for one in ret:
        distance_7 += one[0]
        step_count_7 += one[1]
        step_count_week[one[2]] = one[1]

    if step_count_7 == 0:
        mean_step_size = 0
    else:
        mean_step_size = "{0:.3f}".format(distance_7 / float(step_count_7))

    score = 0

    if step_count_7 < 2500:
        score += 0
    elif step_count_7 < 5000:
        score += 1
    elif step_count_7 < 10000:
        score += 2
    elif step_count_7 < 15000:
        score += 3
    else:
        score += 4

    height = user_profile.height / 100.0

    if mean_step_size < height * 0.42:
        score += 0
    elif mean_step_size < height * 0.45:
        score += 1
    elif mean_step_size < height * 0.48:
        score += 2
    elif mean_step_size < height * 0.51:
        score += 3
    else:
        score += 4

    sql = """
            SELECT YEAR(start_time) AS Year, WEEK(start_time) AS Week, COUNT(*) AS count
            FROM step_count_stepdata
            WHERE user_id=%s
            GROUP BY Year, Week;
            """ % (user.id,)

    cursor.execute(sql)
    ret = cursor.fetchall()

    count_week_2times = 0

    for one in ret:
        if one[2] > 1:
            count_week_2times += 1

    if count_week_2times < 4:
        score += 0
    elif count_week_2times < 8:
        score += 1
    elif count_week_2times < 12:
        score += 2
    elif count_week_2times < 24:
        score += 3
    else:
        score += 4

    if score < 2:
        rating_value = 1
    elif score < 5:
        rating_value = 2
    elif score < 8:
        rating_value = 3
    elif score < 11:
        rating_value = 4
    else:
        rating_value = 5

    content = {}

    content['mean_step_size']  = mean_step_size
    content['rating_value'] = rating_value
    content['step_count_week'] = step_count_week

    response_data['type'] = 'success'
    response_data['content'] = content

    return JsonResponse(response_data)

@csrf_exempt
def v2_get_calendar_data(request):
    email = request.GET.get('email', None)
    year_month = request.GET.get('year_month', None)

    response_data = {}

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'

        return JsonResponse(response_data)

    cursor = connection.cursor()

    sql = """
            SELECT 
              start_time
            FROM step_count_stepdata
            WHERE user_id = %s AND DATE_FORMAT(start_time,'%%Y-%%m') = '%s'
            ORDER BY start_time
        """ % (user.id, year_month)

    cursor.execute(sql)
    ret = cursor.fetchall()

    result = []

    for one in ret:
        result.append(one[0])

    response_data['type'] = 'success'
    response_data['content'] = result

    return JsonResponse(response_data)

@csrf_exempt
def v2_get_measurement_data(request):
    email = request.GET.get('email', None)
    start_time = request.GET['start_time']

    response_data = {}

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'

        return JsonResponse(response_data)

    try:
        step_data = StepData.objects.get(user_id=user.id, start_time=start_time)
    except StepData.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_DATA'

        return JsonResponse(response_data)

    now_utc_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    cursor = connection.cursor()

    sql = """
            SELECT                
                SUM(step_level0) AS level0,
                SUM(step_level1) AS level1,
                SUM(step_level2) AS level2,
                SUM(step_level3) AS level3,
                SUM(step_level4) AS level4,
                SUM(step_count) AS all_count
            FROM step_count_stepdata
            WHERE user_id=%s
                AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 30 DAY)
                AND DATE(start_time) <= DATE('%s')
          """ % (user.id, now_utc_time, now_utc_time)

    cursor.execute(sql)
    ret = list(cursor.fetchone())

    for i in range(len(ret)):
        ret[i] = ret[i] if ret[i] else 0

    response_data['type'] = 'success'
    content={}
    content['start_time'] = start_time
    content['end_time'] = step_data.end_time.strftime('%Y-%m-%dT%H:%M:%S')
    content['distance'] = step_data.distance
    content['step_size'] = "{0:.3f}".format(step_data.step_size)
    content['step_count'] = step_data.step_count
    content['latitudes'] = step_data.latitudes.split(',')
    content['longitudes'] = step_data.longitudes.split(',')
    content['step_distribution'] = [
        "{0:.3f}".format((float(step_data.step_level0) / step_data.step_count) if step_data.step_count else 0),
        "{0:.3f}".format((float(step_data.step_level1) / step_data.step_count) if step_data.step_count else 0),
        "{0:.3f}".format((float(step_data.step_level2) / step_data.step_count) if step_data.step_count else 0),
        "{0:.3f}".format((float(step_data.step_level3) / step_data.step_count) if step_data.step_count else 0),
        "{0:.3f}".format((float(step_data.step_level4) / step_data.step_count) if step_data.step_count else 0),
    ]
    content['step_month_distribution'] = [
        "{0:.3f}".format(float(ret[0] / ret[5]) if ret[5] else 0),
        "{0:.3f}".format(float(ret[1] / ret[5]) if ret[5] else 0),
        "{0:.3f}".format(float(ret[2] / ret[5]) if ret[5] else 0),
        "{0:.3f}".format(float(ret[3] / ret[5]) if ret[5] else 0),
        "{0:.3f}".format(float(ret[4] / ret[5]) if ret[5] else 0),
    ]

    content['step_histogram'] = json.loads(step_data.step_histogram)

    response_data['content'] = content

    return JsonResponse(response_data)

@csrf_exempt
def get_user_groups(request):
    email = request.GET.get('email', None)
    response_data = {}
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'
        return JsonResponse(response_data)

    user_groups = user.groups.all()
    group_list = Group.objects.filter()
    json_groups = []
    for group in group_list:
        if group in user_groups:
            active = 1
        else:
            active = 0
        json_groups.append({
            "id": group.id,
            "name": group.name,
            "active": active
        })
    response_data['type'] = 'success'
    response_data['content'] = json_groups
    return JsonResponse(response_data)

@csrf_exempt
def set_user_groups(request):
    response_data = {}

    if request.method == 'POST':
        email = request.POST['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_USER'
            return JsonResponse(response_data)


        group_list = Group.objects.filter()
        user_groups = user.groups.all()
        for group in group_list:
            group_id = str(group.id)
            active = int(request.POST.get("group[" + group_id + "]", 0))

            try:
                selected_group = Group.objects.get(id=group_id)
            except Group.DoesNotExist:
                continue

            if active == 0 and selected_group in user_groups:
                group.user_set.remove(user)
            if active == 1 and selected_group not in user_groups:
                group.user_set.add(user)

        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOT_GET'
        return JsonResponse(response_data)

@csrf_exempt
def get_food_list(request):
    food_list = FoodData.objects.filter()
    content = []
    for food in food_list:
        content.append({
            "id":food.id,
            "name":food.name
        })
    response_data = {
        "type" : 'success',
        "content": content
    }
    return JsonResponse(response_data)

@csrf_exempt
def get_sq_list(request):
    sq_list = SleepQuality.objects.filter()
    content = []
    for sq in sq_list:
        content.append({
            "id":sq.id,
            "name":sq.name,
            "level0":sq.level0,
            "level1":sq.level1,
            "level2":sq.level2,
            "level3":sq.level3
        })
    response_data = {
        "type" : 'success',
        "content": content
    }
    return JsonResponse(response_data)

@csrf_exempt
def meal_get_list(request):
    email = request.GET.get('email', None)
    year_month = request.GET.get('year_month', None)

    response_data = {}

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'
        return JsonResponse(response_data)

    if not year_month:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_YEARMONTH'
        return JsonResponse(response_data)
    try:
        year = year_month.split("-")[0]
        month = year_month.split("-")[1]
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_YEARMONTH'
        return JsonResponse(response_data)

    meal_list = MealData.objects.filter(Q(user__id=user.id) & Q(reg_date__year=year) & Q(reg_date__month=month))
    json_meals = []

    for meal in meal_list:
        json_meal = {
            'id': meal.id,
            'reg_date':meal.reg_date,
        }
        json_meals.append(json_meal)

    response_data = {
        "type": 'success',
        "content": json_meals
    }
    return JsonResponse(response_data)

@csrf_exempt
def meal_get_info(request):    
    response_data = {}
    id = request.GET.get('id', None)
    if not id:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_ID'
        return JsonResponse(response_data)

    meal_info_list = MealInfo.objects.filter(Q(meal_data_id=id))
    content = []
    for meal_info in meal_info_list:
        food = FoodData.objects.get(id=meal_info.food_data_id)
        content.append({
            "id":meal_info.id,
            "meal_data_id":meal_info.meal_data_id,
            "food_data_id":meal_info.food_data_id,
            "food_name":food.name,
            "breakfast":meal_info.breakfast,
            "lunch":meal_info.lunch,
            "dinner":meal_info.dinner
        })

    response_data['type'] = 'success'
    response_data['content'] = content
    return JsonResponse(response_data)

@csrf_exempt
def meal_create(request):
    response_data = {}
    if request.method == 'POST':
        email = request.POST.get('email',None)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_USER'
            return JsonResponse(response_data)

        reg_date = request.POST.get('reg_date', None)
        if not reg_date:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_DATE'
            return JsonResponse(response_data)

        meal_data = MealData.objects.filter(Q(user_id = user.id) & Q(reg_date = reg_date))
        if len(meal_data)>0:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_EXIST_DATA'
            return JsonResponse(response_data)

        meal = MealData(
            user_id = user.id,
            reg_date = reg_date
        )
        try:
            meal.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_SAVE'
            return JsonResponse(response_data)

        food_ids = FoodData.objects.filter()

        for food in food_ids:
            food_id = str(food.id)
            breakfast = request.POST.get('breakfast[' + food_id + ']', 0)
            lunch = request.POST.get('lunch[' + food_id + ']', 0)
            dinner = request.POST.get('dinner[' + food_id + ']', 0)

            meal_info = MealInfo(
                meal_data_id = meal.id,
                food_data_id = food_id,
                breakfast = breakfast,
                lunch = lunch,
                dinner = dinner
            )
            meal_info.save()

        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOT_GET'
        return JsonResponse(response_data)

@csrf_exempt
def meal_update(request):
    response_data = {}
    if request.method == 'POST':
        email = request.POST.get('email', None)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_USER'
            return JsonResponse(response_data)

        id = request.POST.get('id', None)
        reg_date = request.POST.get('reg_date', None)
        if not id:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_ID'
            return JsonResponse(response_data)
        if not reg_date:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_DATE'
            return JsonResponse(response_data)

        try:
            meal = MealData.objects.get(id=id)
        except MealData.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NOT_EXIST'
            return JsonResponse(response_data)

        meal_data = MealData.objects.filter(Q(user_id=user.id) & Q(reg_date=reg_date) & ~Q(id=id))
        if len(meal_data) > 0:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_EXIST_DATA'
            return JsonResponse(response_data)

        meal.reg_date = reg_date

        try:
            meal.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_SAVE'
            return JsonResponse(response_data)

        food_list = FoodData.objects.filter()

        for food in food_list:
            food_id = str(food.id)
            meal_info_id = request.POST.get('meal_info_id[' + food_id + ']', 0)
            breakfast = request.POST.get('breakfast[' + food_id + ']', 0)
            lunch = request.POST.get('lunch[' + food_id + ']', 0)
            dinner = request.POST.get('dinner[' + food_id + ']', 0)

            meal_info = MealInfo.objects.get(id=meal_info_id)
            meal_info.breakfast = breakfast
            meal_info.lunch = lunch
            meal_info.dinner = dinner

            meal_info.save()

        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOT_GET'
        return JsonResponse(response_data)

@csrf_exempt
def meal_delete(request):
    response_data = {}
    if request.method == 'POST':
        email = request.POST.get('email', None)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_USER'
            return JsonResponse(response_data)

        id = request.POST.get('id', None)
        if not id:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_ID'
            return JsonResponse(response_data)

        try:
            meal = MealData.objects.get(id=id)
        except MealData.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NOT_EXIST'
            return JsonResponse(response_data)

        meal.delete()

        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOT_GET'
        return JsonResponse(response_data)

@csrf_exempt
def sleep_get_list(request):
    email = request.GET.get('email', None)
    year_month = request.GET.get('year_month', None)
    response_data = {}

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'
        return JsonResponse(response_data)

    try:
        year = year_month.split("-")[0]
        month = year_month.split("-")[1]
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_YEARMONTH'
        return JsonResponse(response_data)

    sleep_list = SleepData.objects.filter(Q(user__id=user.id) & Q(bed_time__contains=year_month))
    content = []
    for sleep in sleep_list:
        content.append({
            'id': sleep.id,
            'bed_time':sleep.bed_time,
            'wakeup_time':sleep.wakeup_time,
            'created_at': sleep.created_at
        })

    response_data['type'] = 'success'
    response_data['content'] = content
    return JsonResponse(response_data)

@csrf_exempt
def sleep_get_info(request):
    response_data = {}
    id = request.GET.get('id', None)
    if not id:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_ID'
        return JsonResponse(response_data)

    sleep_info_list = SleepDataInfo.objects.filter(Q(sleep_data_id=id))
    content = []
    for sleep_info in sleep_info_list:
        sq = SleepQuality.objects.get(id=sleep_info.sleep_quality_id)
        content.append({
            "id":sleep_info.id,
            "sleep_data_id":sleep_info.sleep_data_id,
            "sq_id":sleep_info.sleep_quality_id,
            "level": sleep_info.level,
            "sq_name":sq.name,
            "level0":sq.level0,
            "level1":sq.level1,
            "level2":sq.level2,
            "level3":sq.level3
        })

    response_data['type'] = 'success'
    response_data['content'] = content
    return JsonResponse(response_data)

@csrf_exempt
def sleep_create(request):
    response_data = {}
    if request.method == 'POST':
        email = request.POST.get('email', None)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_USER'
            return JsonResponse(response_data)

        bed_time = request.POST.get('bed_time', None)
        wakeup_time = request.POST.get('wakeup_time', None)
        if not bed_time:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_BED_TIME'
            return JsonResponse(response_data)
        if not wakeup_time:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_WAKEUP_TIME'
            return JsonResponse(response_data)
        try:
            bed_time_obj = datetime.strptime(bed_time, '%Y-%m-%d %H:%M')
            wakeup_time_obj = datetime.strptime(wakeup_time, '%Y-%m-%d %H:%M')
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_TIME_FORMAT'
            return JsonResponse(response_data)
        if bed_time_obj >= wakeup_time_obj:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_INVALID_TIME'
            return JsonResponse(response_data)

        sleep = SleepData(
            user_id = user.id,
            bed_time = bed_time,
            wakeup_time = wakeup_time,
        )
        try:
            sleep.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_SAVE'
            return JsonResponse(response_data)

        sqs = SleepQuality.objects.filter()

        for sq in sqs:
            sq_id = str(sq.id)
            level = request.POST.get("level[" + sq_id + "]", 3)

            sleep_info = SleepDataInfo(
                sleep_data_id = sleep.id,
                sleep_quality_id = sq_id,
                level = level
            )
            sleep_info.save()

        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOT_GET'
        return JsonResponse(response_data)

@csrf_exempt
def sleep_update(request):
    response_data = {}
    if request.method == 'POST':
        email = request.POST.get('email', None)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_USER'
            return JsonResponse(response_data)

        id = request.POST.get('id', None)
        bed_time = request.POST.get('bed_time', None)
        wakeup_time = request.POST.get('wakeup_time', None)
        if not id:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_ID'
            return JsonResponse(response_data)
        if not bed_time:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_BED_TIME'
            return JsonResponse(response_data)
        if not wakeup_time:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_WAKEUP_TIME'
            return JsonResponse(response_data)

        try:
            bed_time_obj = datetime.strptime(bed_time, '%Y-%m-%d %H:%M')
            wakeup_time_obj = datetime.strptime(wakeup_time, '%Y-%m-%d %H:%M')
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_TIME_FORMAT'
            return JsonResponse(response_data)
        if bed_time_obj >= wakeup_time_obj:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_INVALID_TIME'
            return JsonResponse(response_data)

        try:
            sleep = SleepData.objects.get(id=id)
        except SleepData.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NOT_EXIST'
            return JsonResponse(response_data)

        sleep.bed_time = bed_time
        sleep.wakeup_time = wakeup_time

        try:
            sleep.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_SAVE'
            return JsonResponse(response_data)

        sqs = SleepQuality.objects.filter()

        for sq in sqs:
            sq_id = str(sq.id)
            sleep_info_id = request.POST.get("sleep_info_id[" + sq_id + "]", 0)
            level = request.POST.get("level[" + sq_id + "]", 3)
            sleep_info = SleepDataInfo.objects.get(id=sleep_info_id)
            sleep_info.level = level
            sleep_info.save()

        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOT_GET'
        return JsonResponse(response_data)

@csrf_exempt
def sleep_delete(request):
    response_data = {}
    if request.method == 'POST':
        email = request.POST.get('email', None)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_USER'
            return JsonResponse(response_data)

        id = request.POST.get('id', None)
        if not id:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_ID'
            return JsonResponse(response_data)
        try:
            sleep = SleepData.objects.get(id=id)
        except SleepData.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NOT_EXIST'
            return JsonResponse(response_data)

        sleep.delete()

        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOT_GET'
        return JsonResponse(response_data)

def make_health_sql(user_id):

    sql = """            
            SELECT
                t0.user_id,
                t0.name,
                t0.email,
                t0.step_size_score,
                t0.step_habit_score,
                t0.step_continuity_score,
                t0.meal_balance_score,
                t0.meal_habit_score,
                t0.meal_continuity_score,
                t0.sleep_quality_score,
                t0.sleep_std_score,
                t0.sleep_continuity_score,
                t0.step_size_score + t0.step_habit_score + t0.step_continuity_score AS step_score,
                t0.meal_balance_score + t0.meal_habit_score + t0.meal_continuity_score AS meal_score,
                t0.sleep_quality_score + t0.sleep_std_score + t0.sleep_continuity_score AS sleep_score,
                t0.step_size_score + t0.step_habit_score + t0.step_continuity_score + t0.sleep_quality_score + t0.meal_balance_score + t0.meal_habit_score + t0.meal_continuity_score + t0.sleep_std_score + t0.sleep_continuity_score AS all_score
            FROM(
                SELECT
                    t0.user_id AS user_id,
                    t0.name AS name,
                    t0.email AS email,
                    IF(t0.step_size<t0.height/100*0.42,0,IF(t0.step_size<t0.height/100*0.45,5,IF(t0.step_size<t0.height/100*0.48,10,15))) AS step_size_score,
                    IF(t0.habit<1,0,IF(t0.habit<2,5,IF(t0.habit<3,10,15))) AS step_habit_score,
                    IF(t0.continuity<1,0,IF(t0.continuity<2,5,IF(t0.continuity<4,10,15))) AS step_continuity_score,
                    IF(t0.meal_balance<5,0,IF(t0.meal_balance<10,5,IF(t0.meal_balance<12,10,15))) AS meal_balance_score,
                    IF(t0.meal_habit<1,0,IF(t0.meal_habit<3,5,IF(t0.meal_habit<4,10,15))) AS meal_habit_score,
                    IF(t0.meal_continuity<1,0,IF(t0.meal_continuity<2,5,IF(t0.meal_continuity<4,10,15))) AS meal_continuity_score,
                    IF(t0.sleep_quality<3,0,IF(t0.sleep_quality<5,5,IF(t0.sleep_quality<7,10,15))) AS sleep_quality_score,
                    IF(t0.sleep_std>120,0,IF(t0.sleep_std>90,5,IF(t0.sleep_std>60,10,IF(t0.sleep_std>0,15,0)))) AS sleep_std_score,
                    IF(t0.sleep_continuity<1,0,IF(t0.sleep_continuity<2,5,IF(t0.sleep_continuity<4,10,15))) AS sleep_continuity_score
                FROM
                (
                    SELECT
                        t0.user_id AS user_id,
                        t0.name AS name,
                        t0.email AS email,
                        t0.height AS height,
                        t0.step_size AS step_size,
                        IF(t0.habit,t0.habit,0) AS habit,                
                        t0.continuity AS continuity,
                        IF(t0.meal_balance,t0.meal_balance,0) AS meal_balance,
                        IF(t0.meal_habit,t0.meal_habit,0) AS meal_habit,		
                        t0.meal_continuity AS meal_continuity,
                        IF(t0.quality,t0.quality,0) AS sleep_quality,
                        IF(t0.sleep_std,t0.sleep_std,0) AS sleep_std,
                        t0.sleep_continuity
                    FROM 
                    (
                        SELECT
                            tt.user_id AS user_id,
                            tt.name AS name,
                            t12.email AS email,
                            tt.height AS height,
                            IF(t2.step_size,t2.step_size,0) AS step_size,
                            t0.count / IF(DATEDIFF(NOW(),t1.start_time)>60,60,DATEDIFF(NOW(),t1.start_time)) * 7 AS habit,                
                            IF(t3.count,t3.count,0) / 7 AS continuity,
                            t4.count / IF(DATEDIFF(NOW(),t5.start_time)>60,60,DATEDIFF(NOW(),t5.start_time)) AS meal_balance,
                            t6.habit AS meal_habit,
                            IF(t7.count,t7.count,0) / 7 AS meal_continuity,
                            t8.count / IF(DATEDIFF(NOW(),t9.start_time)>60,60,DATEDIFF(NOW(),t9.start_time)) AS quality,
                            t10.std AS sleep_std,
                            IF(t11.count,t11.count,0) / 7 AS sleep_continuity
                        FROM 
                        (
                            SELECT
                                *
                            FROM step_count_userprofile
                            WHERE user_id = {0}
                        ) AS tt                        
                        LEFT JOIN auth_user AS t12 ON tt.user_id = t12.id
                        LEFT JOIN
                        (
                            SELECT
                                user_id,
                                COUNT(*) AS count
                            FROM
                            (
                                SELECT 
                                    user_id,
                                    YEAR(start_time) AS Year, 
                                    WEEK(start_time) AS Week, 
                                    Day(start_time) AS Day
                                FROM step_count_stepdata	
                                WHERE DATE(start_time) >= DATE_SUB(NOW(), INTERVAL 60 DAY)
                                GROUP BY user_id, Year, Week, Day
                            ) AS t0
                            GROUP BY t0.user_id
                        ) AS t0 ON t0.user_id=tt.user_id
                        LEFT JOIN 
                        (
                            SELECT
                                user_id,
                                MIN(start_time) AS start_time
                            FROM step_count_stepdata
                            GROUP BY user_id
                        ) AS t1 ON tt.user_id=t1.user_id
                        LEFT JOIN 
                        (
                            SELECT
                                user_id,
                                IF(step_count>0,SUM(distance) / SUM(step_count),0) AS step_size
                            FROM step_count_stepdata 
                            WHERE DATE(start_time) >= DATE_SUB(NOW(), INTERVAL 6 DAY)
                            GROUP BY user_id
                        ) AS t2 ON tt.user_id=t2.user_id
                        LEFT JOIN
                        (
                            SELECT
                                t0.user_id,
                                IF(MAX(count)<0,0,MAX(count)) AS count
                            FROM(
                                SELECT  		
                                    DATEDIFF(@rank,t0.date) AS diff,
                                    @count:=IF(DATEDIFF(IF(t0.user_id = @b_id, @rank, NOW()),t0.date)<8, IF(t0.user_id = @b_id, IF(@count>-1, @count+1, -1), 1), -1) AS count,
                                    @rank:=t0.date AS b_date,
                                    @b_id:=t0.user_id AS user_id
                                FROM(	
                                    SELECT 
                                        user_id,
                                        DATE(start_time) AS date	
                                    FROM step_count_stepdata
                                    WHERE DATE(start_time) >= DATE_SUB(NOW(), INTERVAL 245 DAY)
                                    GROUP BY user_id, date
                                    ORDER BY user_id, date DESC
                                ) AS t0
                            ) AS t0
                            GROUP BY t0.user_id
                        ) AS t3 ON tt.user_id=t3.user_id
                        LEFT JOIN(		
                            SELECT 
                                t0.user_id,
                                SUM(t1.breakfast + t1.lunch + t1.dinner) AS count
                            FROM step_count_mealdata AS t0
                            LEFT JOIN step_count_mealinfo AS t1 ON t0.id=t1.meal_data_id
                            WHERE DATE(t0.reg_date) >= DATE_SUB(NOW(), INTERVAL 60 DAY)
                            GROUP BY t0.user_id		
                        ) AS t4 ON t4.user_id=tt.user_id
                        LEFT JOIN(
                            SELECT
                                t0.user_id,
                                COUNT(IF(t0.count>12,1,NULL)) AS habit
                            FROM(
                                SELECT 
                                    t0.user_id,
                                    SUM(t1.breakfast + t1.lunch + t1.dinner) AS count,
                                    t0.reg_date
                                FROM step_count_mealdata AS t0
                                LEFT JOIN step_count_mealinfo AS t1 ON t0.id=t1.meal_data_id
                                WHERE DATE(t0.reg_date) >= DATE_SUB(NOW(), INTERVAL 60 DAY)
                                GROUP BY t0.user_id, t0.reg_date
                            ) AS t0
                            GROUP BY t0.user_id
                        ) AS t6 ON t6.user_id=tt.user_id
                        LEFT JOIN 
                        (
                            SELECT
                                user_id,
                                MIN(reg_date) AS start_time
                            FROM step_count_mealdata
                            GROUP BY user_id
                        ) AS t5 ON tt.user_id=t5.user_id
                        LEFT JOIN
                        (
                            SELECT
                                t0.user_id,
                                IF(MAX(count)<0,0,MAX(count)) AS count
                            FROM(
                                SELECT  		
                                    DATEDIFF(@meal_rank,t0.date) AS diff,
                                    @meal_count:=IF(DATEDIFF(IF(t0.user_id = @meal_b_id, @meal_rank, NOW()),t0.date)<8, IF(t0.user_id = @b_id, IF(@meal_count>-1, @meal_count+1, -1), 1), -1) AS count,
                                    @meal_rank:=t0.date AS b_date,
                                    @meal_b_id:=t0.user_id AS user_id
                                FROM
                                (	
                                    SELECT 
                                        user_id,
                                        DATE(reg_date) AS date	
                                    FROM step_count_mealdata
                                    WHERE DATE(reg_date) >= DATE_SUB(NOW(), INTERVAL 245 DAY)
                                    GROUP BY user_id, date
                                    ORDER BY user_id, date DESC
                                ) AS t0
                            ) AS t0
                            GROUP BY t0.user_id
                        ) AS t7 ON tt.user_id=t7.user_id
                        LEFT JOIN(		
                            SELECT 
                                t0.user_id,
                                COUNT(t1.id) AS count
                            FROM step_count_sleepdata AS t0
                            LEFT JOIN step_count_sleepdatainfo AS t1 ON t0.id=t1.sleep_data_id
                            WHERE DATE(t0.bed_time) >= DATE_SUB(NOW(), INTERVAL 60 DAY)
                            GROUP BY t0.user_id		
                        ) AS t8 ON t8.user_id=tt.user_id
                        LEFT JOIN 
                        (
                            SELECT
                                user_id,
                                MIN(bed_time) AS start_time
                            FROM step_count_sleepdata
                            GROUP BY user_id
                        ) AS t9 ON tt.user_id=t9.user_id
                        LEFT JOIN
                        (
                            SELECT
                                t0.user_id,
                                STD(t0.sleep_time) AS std
                            FROM(
                                SELECT
                                    user_id,
                                    TIMESTAMPDIFF(MINUTE,bed_time,wakeup_time) AS sleep_time
                                FROM step_count_sleepdata		
                            ) AS t0
                            GROUP BY t0.user_id	
                        ) AS t10 ON tt.user_id=t10.user_id
                        LEFT JOIN
                        (
                            SELECT
                                t0.user_id,
                                IF(MAX(count)<0,0,MAX(count)) AS count
                            FROM
                            (
                                SELECT  		
                                    DATEDIFF(@sleep_rank,t0.date) AS diff,
                                    @sleep_count:=IF(DATEDIFF(IF(t0.user_id = @sleep_b_id, @sleep_rank, NOW()),t0.date)<8, IF(t0.user_id = @b_id, IF(@sleep_count>-1, @sleep_count+1, -1), 1), -1) AS count,
                                    @sleep_rank:=t0.date AS b_date,
                                    @sleep_b_id:=t0.user_id AS user_id
                                FROM
                                (	
                                    SELECT 
                                        user_id,
                                        DATE(bed_time) AS date	
                                    FROM step_count_sleepdata
                                    WHERE DATE(bed_time) >= DATE_SUB(NOW(), INTERVAL 245 DAY)
                                    GROUP BY user_id, date
                                    ORDER BY user_id, date DESC
                                ) AS t0
                            ) AS t0
                            GROUP BY t0.user_id
                        ) AS t11 ON tt.user_id=t11.user_id		
                    ) AS t0
                ) AS t0
            ) AS t0              
            """.format(user_id,)
    return sql

@csrf_exempt
def get_score_data(request):
    email = request.GET.get('email', None)
    response_data = {}

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'
        return JsonResponse(response_data)

    cursor = connection.cursor()
    setting = ["SET @rank=NOW();",
               "SET @count=0;",
               "SET @b_id=0;",
               "SET @meal_rank=NOW();",
               "SET @meal_count=0;",
               "SET @meal_b_id=0;",
               "SET @sleep_rank=NOW();",
               "SET @sleep_count=0;",
               "SET @sleep_b_id=0;"]
    for one in setting:
        cursor.execute(one)

    sql = make_health_sql(user.id)
    cursor.execute(sql)
    ret = cursor.fetchone()
    result = {
            "user_id": ret[0],
            "name": ret[1],
            "email": ret[2],
            "step_size_score": float(ret[3]) * 2 / 3,
            "step_habit_score": float(ret[4]) * 2 / 3,
            "step_continuity_score": float(ret[5]) * 2 / 3,
            "meal_balance_score": float(ret[6]) * 2 / 3,
            "meal_habit_score": float(ret[7]) * 2 / 3,
            "meal_continuity_score": float(ret[8]) * 2 / 3,
            "sleep_quality_score": float(ret[9]) * 2 / 3,
            "sleep_std_score": float(ret[10]) * 2 / 3,
            "sleep_continuity_score": float(ret[11]) * 2 / 3,
            "step_score": ret[12],
            "meal_score": ret[13],
            "sleep_score": ret[14],
            "all_score": ret[15]
        }

    sql = """SELECT 
                 weight                       
               FROM step_count_weightdata 
               WHERE user_id=%s                       
               ORDER BY reg_date DESC
               LIMIT 1
            """ % (user.id,)

    cursor.execute(sql)
    ret = cursor.fetchone()

    profile = UserProfile.objects.get(user_id=user.id)
    height = float(profile.height)

    if ret == None:
        weight = float(profile.weight)
    else:
        weight = float(ret[0])

    BMI = 0

    if height and weight:
        BMI = weight / (height/100 * height/100)

    if BMI > 0 and BMI < 21:
        P = 0.0193 * BMI * BMI + 0.0946 * BMI - 0.4979
    elif BMI >= 21:
        P = 0.0193 * BMI * BMI - 1.7118 * BMI + 37.4365
    else:
        P = 0

    P = P * 10 / 25

    result['BMI'] = P

    response_data['type'] = 'success'
    response_data['content'] = result
    return JsonResponse(response_data)

@csrf_exempt
def weight_get_month_list(request):
    email = request.GET.get('email', None)
    year_month = request.GET.get('year_month', None)
    response_data = {}

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'
        return JsonResponse(response_data)

    try:
        year_month_obj = datetime.strptime(year_month, '%Y-%m')
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_YEARMONTH'
        return JsonResponse(response_data)

    weight_list = WeightData.objects.filter(Q(user__id=user.id) & Q(reg_date__contains=year_month))
    content = []
    for one in weight_list:
        content.append({
            'id': one.id,
            'reg_date':one.reg_date,
            'weight':one.weight,
            'target_weight': one.target_weight
        })

    response_data['type'] = 'success'
    response_data['content'] = content
    return JsonResponse(response_data)

@csrf_exempt
def weight_get_list(request):
    email = request.GET.get('email', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)
    response_data = {}

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'
        return JsonResponse(response_data)

    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_STARTTIME_FORMAT'
        return JsonResponse(response_data)

    try:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_ENDTIME_FORMAT'
        return JsonResponse(response_data)

    weight_list = WeightData.objects.filter(Q(user__id=user.id) & Q(reg_date__range=(start_date, end_date)))

    content = []
    for one in weight_list:
        content.append({
            'id': one.id,
            'reg_date':one.reg_date,
            'weight':one.weight,
            'target_weight': one.target_weight
        })

    response_data['type'] = 'success'
    response_data['content'] = content
    return JsonResponse(response_data)

@csrf_exempt
def weight_add(request):
    response_data = {}
    if request.method == 'POST':
        email = request.POST.get('email', None)
        reg_date = request.POST.get('reg_date', None)
        weight = request.POST.get('weight', None)
        target_weight = request.POST.get('target_weight', None)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_USER'
            return JsonResponse(response_data)

        if not reg_date:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_REG_DATE'
            return JsonResponse(response_data)
        if not weight:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_WEIGHT'
            return JsonResponse(response_data)

        if not target_weight:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_TARGET_WEIGHT'
            return JsonResponse(response_data)

        try:
            reg_date_obj = datetime.strptime(reg_date, '%Y-%m-%d')
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_TIME_FORMAT'
            return JsonResponse(response_data)

        weight_list = WeightData.objects.filter(Q(user__id=user.id) & Q(reg_date=reg_date))

        if len(weight_list) > 0:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_ALREADY_REGIST'
            return JsonResponse(response_data)

        weight_data = WeightData(
            user_id=user.id,
            reg_date=reg_date,
            weight=weight,
            target_weight=target_weight,
        )
        try:
            weight_data.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_SAVE'
            return JsonResponse(response_data)

        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOT_GET'
        return JsonResponse(response_data)

@csrf_exempt
def weight_update(request):
    response_data = {}
    if request.method == 'POST':
        email = request.POST.get('email', None)
        id = request.POST.get('id', None)
        weight = request.POST.get('weight', None)
        target_weight = request.POST.get('target_weight', None)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_USER'
            return JsonResponse(response_data)

        if not id:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_ID'
            return JsonResponse(response_data)
        if not weight:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_WEIGHT'
            return JsonResponse(response_data)

        if not target_weight:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_TARGET_WEIGHT'
            return JsonResponse(response_data)

        try:
            weight_data = WeightData.objects.get(id=id)
        except WeightData.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_DATA'
            return JsonResponse(response_data)

        weight_data.weight = weight
        weight_data.target_weight = target_weight

        try:
            weight_data.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_SAVE'
            return JsonResponse(response_data)

        response_data['type'] = 'success'
        return JsonResponse(response_data)

    else:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOT_GET'
        return JsonResponse(response_data)

@csrf_exempt
def weight_delete(request):
    response_data = {}
    if request.method == 'POST':
        email = request.POST.get('email', None)
        id = request.POST.get('id', None)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_USER'
            return JsonResponse(response_data)

        if not id:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_ID'
            return JsonResponse(response_data)

        try:
            weight_data = WeightData.objects.get(id=id)
        except WeightData.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_DATA'
            return JsonResponse(response_data)

        try:
            weight_data.delete()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_DELETE'
            return JsonResponse(response_data)

        response_data['type'] = 'success'
        return JsonResponse(response_data)

    else:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOT_GET'
        return JsonResponse(response_data)