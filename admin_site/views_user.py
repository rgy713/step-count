# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime as dt
from datetime import datetime, timedelta

import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import redirect
from django.db import connection

# Create your views here.
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

from step_count.models import UserProfile, StepData, WeightData


@login_required(login_url='/dj/admin/login')
def user_dashboard(request):
    if request.user.is_staff == 0:
        return redirect('/dj/admin/login')
    user_id = request.GET.get('user_id', None)
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

    template = loader.get_template('admin_site/user_dashboard.html')

    data_id = request.GET.get('data_id', None)

    cursor = connection.cursor()

    sql = """SELECT
                  id                 
                FROM step_count_stepdata 
                WHERE user_id=%s                 
                ORDER BY start_time DESC 
             """ % (user_id,)

    cursor.execute(sql)
    ret = cursor.fetchall()
    if len(ret) > 0:
        if data_id is None:
            data_id = int(list(ret[0])[0])

        context = {
            'data': [int(one[0]) for one in ret],
            'data_id': data_id,
            'user_id': user_id,
            'username': profile.name
        }
    else:
        context = {
        }

    return HttpResponse(template.render(context, request))


@login_required(login_url='/dj/admin/login')
def user_get_week_data(request):
    response_data = {}

    try:
        timezone = int(request.GET['timezone'])
    except:
        timezone = 540
    try:
        view_type = int(request.GET['view_type'])
    except:
        view_type = 0

    user_id = request.GET.get('user_id', None)
    if not user_id:
        response_data['type'] = "error"
        response_data['content'] = "ERR_NO_USER"
        return JsonResponse(response_data)

    user_id = int(user_id)

    sign = "-" if timezone < 0 else "+"
    h = str(timezone / 60)
    m = str(timezone % 60)
    h = h if len(h) == 2 else "0" + h
    m = m if len(m) == 2 else "0" + m

    timezone = "{}{}:{}".format(sign, h, m)

    now_utc_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    cursor = connection.cursor()
    sql = ""
    sql_1 = ""
    day = 0
    # a week
    if view_type == 0:
        sql = """
                  SELECT
                      t0.date,
                      IF(ISNULL(t1.distance), 0 ,t1.distance) AS distance,
                      IF(ISNULL(t1.step_count), 0 ,t1.step_count) AS step_count
                  FROM (
                      select DATE_FORMAT(CONVERT_TZ(selected_date,'+00:00','%s'),'%%Y-%%m-%%d') AS date from 
                         (select adddate('1970-01-01',t4.i*10000 + t3.i*1000 + t2.i*100 + t1.i*10 + t0.i) selected_date from
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t0,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t1,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t2,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t3,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t4) v
                      where selected_date >= DATE_SUB(DATE('%s'), INTERVAL 6 DAY)
                        and selected_date <= DATE('%s')
                  ) AS t0
                  LEFT JOIN(
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count,
                        DATE_FORMAT(CONVERT_TZ(start_time,'+00:00','%s'),'%%Y-%%m-%%d') AS date                     
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 6 DAY)
                      AND DATE(start_time) <= DATE('%s')
                    GROUP BY date
                  ) AS t1 ON t0.date=t1.date
                  ORDER BY date 
                 """ % (timezone, now_utc_time, now_utc_time, timezone, user_id, now_utc_time, now_utc_time)
        sql_1 = """
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 6 DAY)
                      AND DATE(start_time) <= DATE('%s')
                """ % (user_id, now_utc_time, now_utc_time)
    # a month
    elif view_type == 1:
        sql = """
                  SELECT
                      t0.date,
                      IF(ISNULL(t1.distance), 0 ,t1.distance) AS distance,
                      IF(ISNULL(t1.step_count), 0 ,t1.step_count) AS step_count
                  FROM (
                      select DATE_FORMAT(CONVERT_TZ(selected_date,'+00:00','%s'),'%%Y-%%m-%%d') AS date from 
                         (select adddate('1970-01-01',t4.i*10000 + t3.i*1000 + t2.i*100 + t1.i*10 + t0.i) selected_date from
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t0,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t1,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t2,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t3,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t4) v
                      where DATE(selected_date) <= DATE('%s')
                        AND DATE(selected_date) >= DATE_SUB(DATE('%s'), INTERVAL 1 MONTH)                        
                  ) AS t0
                  LEFT JOIN(
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count,
                        DATE_FORMAT(CONVERT_TZ(start_time,'+00:00','%s'),'%%Y-%%m-%%d') AS date                     
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND (
                        DATE(start_time) <= DATE('%s')
                        AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 1 MONTH)                        
                      )
                    GROUP BY date
                  ) AS t1 ON t0.date=t1.date
                  ORDER BY date 
                 """ % (timezone, now_utc_time, now_utc_time, timezone, user_id, now_utc_time, now_utc_time)
        sql_1 = """
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 1 MONTH)
                      AND DATE(start_time) <= DATE('%s')
                """ % (user_id, now_utc_time, now_utc_time)
    # 3 months
    elif view_type == 2:
        sql = """
                  SELECT
                      t0.date,
                      IF(ISNULL(t1.distance), 0 ,t1.distance) AS distance,
                      IF(ISNULL(t1.step_count), 0 ,t1.step_count) AS step_count
                  FROM (
                      select DATE_FORMAT(CONVERT_TZ(selected_date,'+00:00','%s'),'%%Y-%%m-%%d') AS date from 
                         (select adddate('1970-01-01',t4.i*10000 + t3.i*1000 + t2.i*100 + t1.i*10 + t0.i) selected_date from
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t0,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t1,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t2,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t3,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t4) v
                      where DATE(selected_date) <= DATE('%s')
                        AND DATE(selected_date) >= DATE_SUB(DATE('%s'), INTERVAL 3 MONTH)                        
                  ) AS t0
                  LEFT JOIN(
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count,
                        DATE_FORMAT(CONVERT_TZ(start_time,'+00:00','%s'),'%%Y-%%m-%%d') AS date                     
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND (
                        DATE(start_time) <= DATE('%s')
                        AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 3 MONTH)                        
                      )
                    GROUP BY date
                  ) AS t1 ON t0.date=t1.date
                  ORDER BY date 
                 """ % (timezone, now_utc_time, now_utc_time, timezone, user_id, now_utc_time, now_utc_time)
        sql_1 = """
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 3 MONTH)
                      AND DATE(start_time) <= DATE('%s')
                """ % (user_id, now_utc_time, now_utc_time)
    # 6 months
    elif view_type == 3:
        sql = """
                  SELECT
                      t0.date,
                      IF(ISNULL(t1.distance), 0 ,t1.distance) AS distance,
                      IF(ISNULL(t1.step_count), 0 ,t1.step_count) AS step_count
                  FROM (
                      select DATE_FORMAT(CONVERT_TZ(selected_date,'+00:00','%s'),'%%Y-%%m-%%d') AS date from 
                         (select adddate('1970-01-01',t4.i*10000 + t3.i*1000 + t2.i*100 + t1.i*10 + t0.i) selected_date from
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t0,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t1,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t2,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t3,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t4) v
                      where DATE(selected_date) <= DATE('%s')
                        AND DATE(selected_date) >= DATE_SUB(DATE('%s'), INTERVAL 6 MONTH)
                  ) AS t0
                  LEFT JOIN(
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count,
                        DATE_FORMAT(CONVERT_TZ(start_time,'+00:00','%s'),'%%Y-%%m-%%d') AS date                     
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND (
                        DATE(start_time) <= DATE('%s')
                        AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 6 MONTH)
                      )
                    GROUP BY date
                  ) AS t1 ON t0.date=t1.date
                  ORDER BY date 
                 """ % (timezone, now_utc_time, now_utc_time, timezone, user_id, now_utc_time, now_utc_time)
        sql_1 = """
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 6 MONTH)
                      AND DATE(start_time) <= DATE('%s')
                """ % (user_id, now_utc_time, now_utc_time)
    # 12 months
    elif view_type == 4:
        sql = """
                  SELECT
                      t0.date,
                      IF(ISNULL(t1.distance), 0 ,t1.distance) AS distance,
                      IF(ISNULL(t1.step_count), 0 ,t1.step_count) AS step_count
                  FROM (
                      select DATE_FORMAT(CONVERT_TZ(selected_date,'+00:00','%s'),'%%Y-%%m-%%d') AS date from 
                         (select adddate('1970-01-01',t4.i*10000 + t3.i*1000 + t2.i*100 + t1.i*10 + t0.i) selected_date from
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t0,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t1,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t2,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t3,
                         (select 0 i union select 1 union select 2 union select 3 union select 4 union select 5 union select 6 union select 7 union select 8 union select 9) t4) v
                      where DATE(selected_date) <= DATE('%s')
                        AND DATE(selected_date) >= DATE_SUB(DATE('%s'), INTERVAL 12 MONTH)                        
                  ) AS t0
                  LEFT JOIN(
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count,
                        DATE_FORMAT(CONVERT_TZ(start_time,'+00:00','%s'),'%%Y-%%m-%%d') AS date                     
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND (
                        DATE(start_time) <= DATE('%s')
                        AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 12 MONTH)                        
                      )
                    GROUP BY date
                  ) AS t1 ON t0.date=t1.date
                  ORDER BY date 
                 """ % (timezone, now_utc_time, now_utc_time, timezone, user_id, now_utc_time, now_utc_time)

        sql_1 = """
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 12 MONTH)
                      AND DATE(start_time) <= DATE('%s')
                """ % (user_id, now_utc_time, now_utc_time)

    cursor.execute(sql)
    ret = cursor.fetchall()

    day = len(ret)

    cursor.execute(sql_1)
    ret_1 = cursor.fetchone()

    data = []
    for one in ret:
        one = {
            "date": one[0],
            "distance": "{0:.2f}".format(one[1]),
            "step_count": one[2],
            "step_size": "{0:.3f}".format(one[1] / float(one[2]) * 100) if one[1] > 0 else 0,
        }
        data.append(one)
    content = {
        "data": data,
        "all_distance": "{0:.2f}".format(ret_1[0] if ret_1[0] > 0 else 0),
        "day_distance": "{0:.2f}".format(float(ret_1[0] / day) if ret_1[0] > 0 else 0),
        "all_step_count": ret_1[1] if ret_1[1] > 0 else 0,
        "day_step_count": int(ret_1[1] / day) if ret_1[1] > 0 else 0,
    }

    response_data['type'] = 'success'
    response_data["content"] = content

    return JsonResponse(response_data)


@login_required(login_url='/dj/admin/login')
def user_get_weight_data(request):
    response_data = {}
    end_date = request.GET['end_date']
    user_id = request.GET.get('user_id', None)
    if not user_id:
        response_data['type'] = "error"
        response_data['content'] = "ERR_NO_USER"
        return JsonResponse(response_data)
    user_id = int(user_id)

    try:
        profile = UserProfile.objects.get(user_id=user_id)
    except UserProfile.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_PROFILE'

        return JsonResponse(response_data)

    result = {}

    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    for d in range(7):
        date = end_date - timedelta(days=(6 - d))
        date_str = date.strftime('%Y-%m-%d')

        cursor = connection.cursor()

        sql = """SELECT 
                      weight, 
                      target_weight                       
                    FROM step_count_weightdata 
                    WHERE user_id=%s                       
                      AND reg_date <= DATE('%s')
                    ORDER BY reg_date DESC
                    LIMIT 1
                 """ % (user_id, date_str)

        cursor.execute(sql)
        ret = cursor.fetchone()

        if ret == None:
            weight = profile.weight
            target_weight = weight
        else:
            weight = ret[0]
            target_weight = ret[1]

        one = {
            "weight": weight,
            "target_weight": target_weight
        }

        result[date_str] = one

    response_data['type'] = 'success'
    response_data['content'] = result

    return JsonResponse(response_data)


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

        if col_name == 'email':
            i += 1
            continue
        orders.append(one_order)
        i += 1

    return ', '.join(orders)


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def user_get_activity_list(request):
    if request.method == 'POST':
        user_id = request.GET.get('user_id', None)
        if not user_id:
            response_data = {}
            response_data['type'] = "error"
            response_data['content'] = "ERR_NO_USER"
            return JsonResponse(response_data)

        user_id = int(user_id)

        draw = int(request.POST.get('draw', 1))
        s_key = request.POST.get('search[value]', '')
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        orders = parseOrder(request)
        activity_list = StepData.objects.filter(user_id=user_id, activity_name__contains=s_key).order_by(orders)[
                        start:start + length]
        json_activity = []
        all_activity_count_filter = StepData.objects.filter(user_id=user_id, activity_name__contains=s_key).count()
        all_activity_count = StepData.objects.filter(user_id=user_id).count()
        idx = 0
        for activity in activity_list:
            idx += 1
            number = start + idx

            diff = (activity.end_time - activity.start_time).total_seconds()
            duration = str(dt.timedelta(seconds=diff))
            json_user = {
                'number': number,
                'id': activity.id,
                'start_time': activity.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                'step_count': activity.step_count,
                'distance': "{0:.3f}".format(float(activity.distance) / 1000),
                'step_size': "{0:.2f}".format(float(activity.step_size) * 100),
                'activity_name': activity.activity_name,
                'duration': duration
            }
            json_activity.append(json_user)

        return JsonResponse(
            {'draw': draw + 1, 'recordsFiltered': all_activity_count_filter, 'recordsTotal': all_activity_count,
             'data': json_activity})
    else:
        raise Http404('URL解析エラー')


@login_required(login_url='/dj/admin/login')
def user_activity(request):
    if request.user.is_staff == 0:
        return redirect('/dj/admin/login')
    user_id = request.GET.get('user_id', None)
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

    template = loader.get_template('admin_site/user_activity.html')
    context = {
        "user_id":user_id,
        "username":profile.name
    }
    return HttpResponse(template.render(context, request))


@login_required(login_url='/dj/admin/login')
def user_calendar(request):
    if request.user.is_staff == 0:
        return redirect('/dj/admin/login')
    user_id = request.GET.get('user_id', None)
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

    template = loader.get_template('admin_site/user_calendar.html')
    context = {
        "user_id": user_id,
        "username": profile.name
    }
    return HttpResponse(template.render(context, request))


@login_required(login_url='/dj/admin/login')
def user_get_event_list(request):
    response_data = {}

    user_id = request.GET.get('user_id', None)
    if not user_id:
        response_data['type'] = "error"
        response_data['content'] = "ERR_NO_USER"
        return JsonResponse(response_data)
    user_id = int(user_id)

    start = request.GET['start']
    end = request.GET['end']

    cursor = connection.cursor()

    sql = """SELECT 
                  id,
                  activity_name, 
                  DATE_FORMAT(start_time,'%%Y-%%m-%%dT%%H:%%i:%%s'),                                    
                  DATE_FORMAT(end_time,'%%Y-%%m-%%dT%%H:%%i:%%s')                       
                FROM step_count_stepdata 
                WHERE user_id=%s                                         
                  AND DATE(start_time) >= DATE('%s')
                  AND DATE(start_time) <= DATE('%s')
                ORDER BY start_time
             """ % (user_id, start, end)

    cursor.execute(sql)
    ret = cursor.fetchall()

    result = []
    for one in ret:
        result.append({
            'id': one[0],
            'title': one[1],
            'start': one[2],
            'end': one[3]
        })

    response_data['type'] = "success"
    response_data['content'] = result

    return JsonResponse(response_data)


@login_required(login_url='/dj/admin/login')
def user_detail(request):
    if request.user.is_staff == 0:
        return redirect('/dj/admin/login')
    data_id = request.GET.get('data_id', None)
    user_id = request.GET.get('user_id', None)
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

    template = loader.get_template('admin_site/user_detail.html')

    if data_id != None:
        try:
            data = StepData.objects.get(id=data_id, user_id=user_id)
        except StepData.DoesNotExist:
            raise Http404('No data!')
    else:
        raise Http404('No data!')

    context = {
        'data_id': data_id,
        'user_id': user_id,
        "username": profile.name
    }

    return HttpResponse(template.render(context, request))
