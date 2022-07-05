# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.db import connection

from step_count.models import UserProfile, FoodData, SleepQuality, MealData, MealInfo, SleepData, SleepDataInfo


def parseOrder(request):
    i = 0
    orders = []
    order_str = ''
    while (1):
        col_idx = request.POST.get('order[' + str(i) + '][column]')
        if (col_idx == None):
            break
        col_name = request.POST.get('columns[' + col_idx + '][name]')
        dir = request.POST.get('order[' + str(i) + '][dir]')
        one_order = col_name
        if (dir == 'desc'):
            one_order = '-' + col_name

        orders.append(one_order)
        i += 1

    return ', '.join(orders)

@login_required(login_url='/dj/admin/login')
def food_index(request):
    if request.user.is_staff == 0:
        return redirect('/dj/admin/login')
    else:
        template = loader.get_template('admin_site/food.html')
        context = {
            'current': "food",
        }
        return HttpResponse(template.render(context, request))

@csrf_exempt
@login_required(login_url='/dj/admin/login')
def food_get_list(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 1))
        s_key = request.POST.get('search[value]', '')
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        orders = parseOrder(request)
        food_list = FoodData.objects.filter(Q(name__contains=s_key)).order_by(orders)[start:start + length]
        all_food_count = FoodData.objects.filter(Q(name__contains=s_key)).count()
        json_foods = []
        idx = 0
        for food in food_list:
            idx += 1
            number = start + idx
            json_food = {
                'number': number,
                'id': food.id,
                'name': food.name,
            }
            json_foods.append(json_food)

        return JsonResponse(
            {'draw': draw + 1, 'recordsFiltered': all_food_count, 'recordsTotal': all_food_count, 'data': json_foods})
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def food_get_info(request):
    if request.method == 'POST':
        response_data = {}
        id = request.POST.get('id', None)
        if not id:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_ID'
            return JsonResponse(response_data)

        try:
            food = FoodData.objects.get(id=id)
        except FoodData.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_DATA'
            return JsonResponse(response_data)

        content = {
            "id": food.id,
            "name":food.name
        }

        response_data['type'] = 'success'
        response_data['content'] = content
        return JsonResponse(response_data)
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def food_create(request):
    if request.method == 'POST':
        response_data = {}
        name = request.POST.get('name', None)

        if not name:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_NAME'
            return JsonResponse(response_data)

        food = FoodData.objects.filter(name=name)

        if len(food) > 0:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_EXIST_FOOD'
            return JsonResponse(response_data)

        food = FoodData(name=name)
        try:
            food.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NOT_SAVE'
            return JsonResponse(response_data)
        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def food_update(request):
    if request.method == 'POST':
        response_data = {}
        id = request.POST.get('id', None)
        name = request.POST.get('name', None)
        if not id:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_ID'
            return JsonResponse(response_data)
        if not name:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_NAME'
            return JsonResponse(response_data)

        try:
            food = FoodData.objects.get(id=id)
        except FoodData.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_DATA'
            return JsonResponse(response_data)

        food.name=name
        try:
            food.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NOT_SAVE'
            return JsonResponse(response_data)
        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def food_delete(request):
    if request.method == 'POST':
        response_data = {}
        id = request.POST.get('id', None)
        if not id:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_ID'
            return JsonResponse(response_data)

        try:
            food = FoodData.objects.get(id=id)
        except FoodData.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_DATA'
            return JsonResponse(response_data)

        try:
            food.delete()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NOT_DELETE'
            return JsonResponse(response_data)

        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        raise Http404('URL解析エラー')

@login_required(login_url='/dj/admin/login')
def sq_index(request):
    if request.user.is_staff == 0:
        return redirect('/dj/admin/login')
    else:
        template = loader.get_template('admin_site/sleep_quality.html')
        context = {
            'current': "sq",
        }
        return HttpResponse(template.render(context, request))


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def sq_get_list(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 1))
        s_key = request.POST.get('search[value]', '')
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        orders = parseOrder(request)
        sq_list = SleepQuality.objects.filter(Q(name__contains=s_key)).order_by(orders)[start:start + length]
        all_sq_count = SleepQuality.objects.filter(Q(name__contains=s_key)).count()
        json_sqs = []
        idx = 0
        for sq in sq_list:
            idx += 1
            number = start + idx
            json_sq = {
                'number': number,
                'id': sq.id,
                'name': sq.name,
                'level0':sq.level0,
                'level1':sq.level1,
                'level2':sq.level2,
                'level3':sq.level3,
            }
            json_sqs.append(json_sq)

        return JsonResponse(
            {'draw': draw + 1, 'recordsFiltered': all_sq_count, 'recordsTotal': all_sq_count, 'data': json_sqs})
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def sq_get_info(request):
    if request.method == 'POST':
        response_data = {}
        id = request.POST.get('id', None)
        if not id:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_ID'
            return JsonResponse(response_data)

        try:
            sq = SleepQuality.objects.get(id=id)
        except SleepQuality.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_DATA'
            return JsonResponse(response_data)

        content = {
            "id": sq.id,
            "name": sq.name,
            "level0":sq.level0,
            "level1":sq.level1,
            "level2":sq.level2,
            "level3":sq.level3,
        }

        response_data['type'] = 'success'
        response_data['content'] = content
        return JsonResponse(response_data)
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def sq_create(request):
    if request.method == 'POST':
        response_data = {}
        name = request.POST.get('name', None)
        level0 = request.POST.get('level0', None)
        level1 = request.POST.get('level1', None)
        level2 = request.POST.get('level2', None)
        level3 = request.POST.get('level3', None)

        if not name:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_NAME'
            return JsonResponse(response_data)

        if not level0 or not level1 or not level2  or not level3:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_LEVELS'
            return JsonResponse(response_data)

        sq = SleepQuality.objects.filter(name=name)

        if len(sq) > 0:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_EXIST_SLEEEP'
            return JsonResponse(response_data)

        sq = SleepQuality(
            name=name,
            level0=level0,
            level1=level1,
            level2=level2,
            level3=level3
        )
        try:
            sq.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NOT_SAVE'
            return JsonResponse(response_data)
        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def sq_update(request):
    if request.method == 'POST':
        response_data = {}
        id = request.POST.get('id', None)
        name = request.POST.get('name', None)
        level0 = request.POST.get('level0', None)
        level1 = request.POST.get('level1', None)
        level2 = request.POST.get('level2', None)
        level3 = request.POST.get('level3', None)
        if not id:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_ID'
            return JsonResponse(response_data)

        if not name:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_NAME'
            return JsonResponse(response_data)

        if not level0 or not level1 or not level2  or not level3:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_LEVELS'
            return JsonResponse(response_data)

        try:
            sq = SleepQuality.objects.get(id=id)
        except SleepQuality.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_DATA'
            return JsonResponse(response_data)

        sq.name=name
        sq.level0=level0
        sq.level1=level1
        sq.level2=level2
        sq.level3=level3
        try:
            sq.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NOT_SAVE'
            return JsonResponse(response_data)
        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def sq_delete(request):
    if request.method == 'POST':
        response_data = {}
        id = request.POST.get('id', None)
        if not id:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_ID'
            return JsonResponse(response_data)

        try:
            sq = SleepQuality.objects.get(id=id)
        except SleepQuality.DoesNotExist:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NO_DATA'
            return JsonResponse(response_data)

        try:
            sq.delete()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_NOT_DELETE'
            return JsonResponse(response_data)

        response_data['type'] = 'success'
        return JsonResponse(response_data)
    else:
        raise Http404('URL解析エラー')

def make_health_sql(group_id):
    if group_id>0:
        group_sql = " INNER JOIN auth_user_groups AS ta ON ta.group_id={0} AND ta.user_id=tt.user_id ".format(group_id,)
    else:
        group_sql = ""
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
                        FROM step_count_userprofile AS tt
                        {0}                        
                        LEFT JOIN auth_user AS t12 ON tt.user_id = t12.id
                        LEFT JOIN
                        (
                                SELECT
                                        user_id,
                                        COUNT(*) AS count
                                FROM(
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
                                        FROM(	
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
                                FROM(
                                        SELECT  		
                                                DATEDIFF(@sleep_rank,t0.date) AS diff,
                                                @sleep_count:=IF(DATEDIFF(IF(t0.user_id = @sleep_b_id, @sleep_rank, NOW()),t0.date)<8, IF(t0.user_id = @b_id, IF(@sleep_count>-1, @sleep_count+1, -1), 1), -1) AS count,
                                                @sleep_rank:=t0.date AS b_date,
                                                @sleep_b_id:=t0.user_id AS user_id
                                        FROM(	
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
            """.format(group_sql,)
    return sql
@login_required(login_url='/dj/admin/login')
def score_view(request):
    if request.user.is_staff == 0:
        return redirect('/dj/admin/login')
    else:
        group_list = Group.objects.filter()
        template = loader.get_template('admin_site/score_view.html')
        context = {
            'current': "score",
            'group_list': group_list
        }
        return HttpResponse(template.render(context, request))

@csrf_exempt
@login_required(login_url='/dj/admin/login')
def get_score_list(request):
    if request.method == 'POST':
        group_id = int(request.POST.get('group_id', 0))
        draw = int(request.POST.get('draw', 1))
        s_key = request.POST.get('search[value]', '')
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))

        orders = parseOrder(request)
        where = ""
        if s_key:
            where = " WHERE t0.name LIKE '%{0}%' OR t0.email LIKE '%{1}%' ".format(s_key, s_key)
        limit = " LIMIT {0}, {1} ".format(start, length)

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

        sql = make_health_sql(group_id)
        sql += where
        cursor.execute(sql)
        ret = cursor.fetchall()
        all_count = len(ret)

        if orders:
            sql += " ORDER BY {0} ".format(orders,)
        sql += limit
        cursor = connection.cursor()
        for one in setting:
            cursor.execute(one)
        cursor.execute(sql)
        ret = cursor.fetchall()
        result = []
        idx = 0
        for one in ret:
            idx += 1
            number = start + idx
            result.append({
                "number":number,
                "user_id":one[0],
                "name":one[1],
                "email":one[2],
                "step_size_score":one[3],
                "step_habit_score":one[4],
                "step_continuity_score":one[5],
                "meal_balance_score":one[6],
                "meal_habit_score":one[7],
                "meal_continuity_score":one[8],
                "sleep_quality_score":one[9],
                "sleep_std_score":one[10],
                "sleep_continuity_score":one[11],
                "step_score":one[12],
                "meal_score":one[13],
                "sleep_score":one[14],
                "all_score":one[15]
            })

        return JsonResponse(
            {'draw': draw + 1, 'recordsFiltered': all_count, 'recordsTotal': all_count, 'data': result})
    else:
        raise Http404('URL解析エラー')

@login_required(login_url='/dj/admin/login')
def health_view(request):
    user = request.user
    if user.is_staff == 0:
        return redirect('/dj/admin/login')

    user_id = request.GET.get("user_id",None)
    if not user_id:
        template = loader.get_template('admin_site/no_user.html')
        context = {}
        return HttpResponse(template.render(context, request))
    user_id = int(user_id)

    try:
        profile = UserProfile.objects.get(user_id=user_id)
    except UserProfile.DoesNotExist:
        template = loader.get_template('admin_site/no_user.html')
        context = {}
        return HttpResponse(template.render(context, request))

    food_list = FoodData.objects.filter()
    sq_list = SleepQuality.objects.filter()
    template = loader.get_template('admin_site/user_health.html')
    context = {
        "food_list" : food_list,
        "sq_list": sq_list,
        "user_id":user_id,
        "username":profile.name
    }
    return HttpResponse(template.render(context, request))

@csrf_exempt
@login_required(login_url='/dj/admin/login')
def meal_get_list(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id', None)
        draw = int(request.POST.get('draw', 1))
        s_key = request.POST.get('search[value]', '')
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        orders = parseOrder(request)
        meal_list = MealData.objects.filter(Q(user__id=user_id) & Q(reg_date__contains=s_key)).order_by(orders)[start:start + length]
        all_meal_count = MealData.objects.filter(Q(user__id=user_id) & Q(reg_date__contains=s_key)).count()
        json_meals = []
        idx = 0
        for meal in meal_list:
            idx += 1
            number = start + idx
            json_meal = {
                'number': number,
                'id': meal.id,
                'reg_date':meal.reg_date,
                'created_at': meal.created_at
            }
            json_meals.append(json_meal)

        return JsonResponse(
            {'draw': draw + 1, 'recordsFiltered': all_meal_count, 'recordsTotal': all_meal_count, 'data': json_meals})
    else:
        raise Http404('URL解析エラー')

@csrf_exempt
@login_required(login_url='/dj/admin/login')
def meal_get_info(request):

    if request.method == 'POST':
        response_data = {}
        id = request.POST.get('id', None)
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
    else:
        raise Http404('URL解析エラー')

@csrf_exempt
@login_required(login_url='/dj/admin/login')
def sleep_get_list(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id', None)
        draw = int(request.POST.get('draw', 1))
        s_key = request.POST.get('search[value]', '')
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        orders = parseOrder(request)
        sleep_list = SleepData.objects.filter(Q(bed_time__contains=s_key) & Q(user__id=user_id)).order_by(orders)[start:start + length]
        all_sleep_count = SleepData.objects.filter(Q(bed_time__contains=s_key) & Q(user__id=user_id)).count()
        json_sleeps = []
        idx = 0
        for sleep in sleep_list:
            idx += 1
            number = start + idx
            diff = sleep.wakeup_time - sleep.bed_time
            days, seconds = diff.days, diff.seconds
            hours = days * 24 + seconds // 3600
            minutes = (seconds % 3600) // 60
            json_sleep = {
                'number': number,
                'id': sleep.id,
                'bed_time':sleep.bed_time,
                'wakeup_time':sleep.wakeup_time,
                'sleep_time': str(hours) + "時間" + str(minutes) + "分",
                'created_at': sleep.created_at
            }
            json_sleeps.append(json_sleep)

        return JsonResponse(
            {'draw': draw + 1, 'recordsFiltered': all_sleep_count, 'recordsTotal': all_sleep_count, 'data': json_sleeps})
    else:
        raise Http404('URL解析エラー')

@csrf_exempt
@login_required(login_url='/dj/admin/login')
def sleep_get_info(request):
    if request.method == 'POST':
        response_data = {}
        id = request.POST.get('id', None)
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
    else:
        raise Http404('URL解析エラー')
