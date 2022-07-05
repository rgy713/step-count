# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import hashlib

import datetime as dt
import os
from datetime import datetime, timedelta

import MySQLdb
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.core.mail import EmailMessage
from django.db.models import Q
from django.forms import forms
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import auth
from django.core.validators import validate_email
from django.db import connection

# Create your views here.
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

from django_project import settings
from step_count.models import UserProfile, StepData, WeightData, UserVerify, MealData, MealInfo, FoodData, SleepData, \
    SleepDataInfo, SleepQuality
from urlparse import urlparse, parse_qs


def validate_date(str_date):
    try:
        datetime.strptime(str_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")


@csrf_exempt
def data_sql_import(request):
    pw = request.GET.get('pw', None)
    response_data = {}

    if pw == None or not pw == 'rgy':
        response_data['type'] = 'error'
        response_data['content'] = 'ERROR_PW'
        return JsonResponse(response_data)

    cursor = connection.cursor()

    sql = """
                Truncate table step_count_stepdata
            """
    cursor.execute(sql)

    sql = """SELECT 
                  user_id, 
                  machine_id                       
             FROM step_count_datafiles                 
             """

    cursor.execute(sql)
    data_info = cursor.fetchall()

    for data in data_info:
        user_id = data[0]
        machine_id = data[1]
        file_path = os.path.join(settings.MEDIA_ROOT, str(user_id), machine_id)

        user_profile = UserProfile.objects.get(user_id=user_id)

        step_data_dict = {}

        user_height = user_profile.height / 100.0

        if os.path.exists(file_path):
            try:
                file = open(file_path, str('rb'))
                reader = csv.reader(file)
                for row in reader:
                    if not len(row) == 8:
                        continue
                    if str(row[0]) in step_data_dict.keys():
                        one_data = step_data_dict[str(row[0])]
                    else:
                        one_data = {
                            'start_time': '',
                            'end_time': '',
                            'step_size': 0.0,
                            'distance': 0.0,
                            'latitudes': [],
                            'longitudes': [],
                            'step_count': 0,
                            'step_level0': 0,
                            'step_level1': 0,
                            'step_level2': 0,
                            'step_level3': 0,
                            'step_level4': 0,
                            'histogram_data': {}
                        }

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
                        user_id=user_id,
                        start_time=one['start_time'],
                        end_time=one['end_time'],
                        step_size=one['distance'] / one['step_count'],
                        distance=one['distance'],
                        latitudes=','.join(one['latitudes']),
                        longitudes=','.join(one['longitudes']),
                        step_histogram=json.dumps(one['histogram_data']),
                        step_count=one['step_count'],
                        step_level0=one['step_level0'],
                        step_level1=one['step_level1'],
                        step_level2=one['step_level2'],
                        step_level3=one['step_level3'],
                        step_level4=one['step_level4'],
                    )

                    try:
                        step_data_info.save()
                    except:
                        continue
            except:
                continue

    response_data['type'] = 'success'

    return JsonResponse(response_data)


def get_news():
    conn = MySQLdb.connect("localhost", "root", "", "dependa", charset="utf8")
    cursor = conn.cursor()
    SQL = """
            SELECT 
              t.date,
              t.title,
              t.content
            FROM tbl_news as t
            WHERE t.state = 0
            ORDER BY t.date
        """
    cursor.execute(SQL)
    data = cursor.fetchall()
    conn.close()
    return data


def index(request):
    # template = loader.get_template('web_pages/index.html')
    # news = []
    #
    # for one in get_news():
    #     one_news = {}
    #     one_news['date'] = one[0]
    #     one_news['title'] = one[1]
    #     one_news['content'] = one[2]
    #
    #     news.append(one_news)
    #
    # context = {
    #     'news': news,
    # }
    # return HttpResponse(template.render(context, request))
    return redirect('/dj/web/pedovisor/dashboard')

def pedovisor_home(request):
    template = loader.get_template('web_pages/pedovisor_home.html')
    context = {}
    return HttpResponse(template.render(context, request))


def pedovisor_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        try:
            user_by_email = User.objects.get(email=request.POST.get('username'))
            user_name = user_by_email.username
            user = authenticate(request, username=user_name, password=request.POST.get('password'))
        except User.DoesNotExist:
            user = None

        if (not user is None):
            auth.login(request, user)
            next_l = request.META['HTTP_REFERER'].split("?next=")
            if len(next_l) > 1 and next_l[1] != "":
                return redirect((next_l[1].split("&")[0]).split('%3F')[0])
            else:
                return redirect('/dj/web/pedovisor/dashboard')
        else:
            template = loader.get_template('web_pages/pedovisor_login.html')
            form.errors['error'] = "error"
            context = {
                'form': form,
            }
            return HttpResponse(template.render(context, request))
    else:
        email = ""
        password = ""
        id = ""
        next_l = request.GET.get("next", None)

        if next_l != None:
            try:
                query = parse_qs(urlparse(next_l).query)
                email = query['email'][0] if 'email' in query.keys() else ""
                password = query['password'][0] if 'password' in query.keys() else ""
                id = query['id'][0] if 'id' in query.keys() else ""
            except:
                pass

        form = AuthenticationForm()
        template = loader.get_template('web_pages/pedovisor_login.html')
            
        context = {
            'form': form,
            'email': email,
            'password':password,
            'id':id,
        }
            
        return HttpResponse(template.render(context, request))


def pedovisor_signup(request):
    if request.method == 'POST':
        email = request.POST['email']
        username = email
        password = request.POST['password']
        name = request.POST['name']
        birthday = request.POST['birthday']
        height = request.POST['height']
        weight = request.POST['weight']
        habbit = request.POST['habbit']
        step_size = request.POST['step_size']
        gender = request.POST['gender']

        user_data = {
            'email': email,
            'password': password,
            'name': name,
            'birthday': birthday,
            'height': height,
            'weight': weight,
            'habbit': habbit,
            'step_zise': step_size,
            'gender': gender
        }

        template = loader.get_template('web_pages/pedovisor_signup.html')

        try:
            validate_email(email)
        except forms.ValidationError:
            context = {
                'error': 'ERR_INVALID_EMAIL',
                'user': user_data
            }
            return HttpResponse(template.render(context, request))

        valid_count = User.objects.filter(email=email).count()
        if valid_count > 0:
            context = {
                'error': 'ERR_EMAIL_ALREADY_EXISTS',
                'user': user_data
            }
            return HttpResponse(template.render(context, request))

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
        except:
            context = {
                'error': 'ERR_USER_CREATE',
                'user': user_data
            }
            return HttpResponse(template.render(context, request))

        try:
            profile = UserProfile(
                user_id=user.id,
                name=name,
                birthday=birthday,
                height=height,
                weight=weight,
                habbit=habbit,
                step_size=step_size,
                gender=gender
            )
            profile.save()
        except:

            User.objects.get(id=user.id).delete()

            context = {
                'error': 'ERR_PROFILE_SAVE',
                'user': user_data
            }
            return HttpResponse(template.render(context, request))

        return redirect('/dj/web/pedovisor/signup-success')
    else:
        template = loader.get_template('web_pages/pedovisor_signup.html')
        context = {}
        return HttpResponse(template.render(context, request))


def pedovisor_signup_success(request):
    template = loader.get_template('web_pages/pedovisor_signup_success.html')
    context = {}
    return HttpResponse(template.render(context, request))


@login_required(login_url='/dj/web/pedovisor/login')
def pedovisor_user(request):
    template = loader.get_template('web_pages/pedovisor_user.html')

    if request.method == "POST":
        user = request.user
        name = request.POST.get('name', None)
        birthday = request.POST.get('birthday', None)
        height = request.POST.get('height', None)
        weight = request.POST.get('weight', None)
        habbit = request.POST.get('habbit', None)
        step_size = request.POST.get('step_size', None)
        gender = request.POST.get('gender', None)

        context = {
            "user": {
                'email': user.email,
                'name': name,
                'birthday': birthday,
                'height': height,
                'weight': weight,
                'habbit': habbit,
                'step_size': step_size,
                'gender': gender
            }
        }

        try:
            profile = UserProfile.objects.get(user_id=user.id)
        except UserProfile.DoesNotExist:
            context['error'] = 'ERR_NO_PROFILE'
            return HttpResponse(template.render(context, request))

        if name is not None:
            profile.name = name

        if birthday is not None:
            try:
                validate_date(birthday)
            except ValueError:
                context['error'] = 'ERR_INVALID_BIRTHDAY'
                return HttpResponse(template.render(context, request))

            profile.birthday = birthday

        if height is not None:
            profile.height = height

        if weight is not None:
            profile.weight = weight

        if habbit is not None:
            profile.habbit = habbit

        if step_size is not None:
            profile.step_size = step_size

        if gender is not None:
            profile.gender = gender

        try:
            profile.save()
        except:
            context['error'] = 'ERR_PROFILE_SAVE'
            return HttpResponse(template.render(context, request))

        return HttpResponse(template.render(context, request))
    else:
        user = request.user
        if user.is_staff == 1:
            return redirect('/dj/web/pedovisor/login')
        profile = UserProfile.objects.get(user_id=user.id)
        context = {
            "user": {
                'email': user.email,
                'name': profile.name,
                'birthday': profile.birthday.strftime("%Y-%m-%d"),
                'height': profile.height,
                'weight': profile.weight,
                'habbit': profile.habbit,
                'step_size': profile.step_size,
                'gender': profile.gender
            }
        }

        return HttpResponse(template.render(context, request))


def pedovisor_forgetpw(request):
    if request.method == 'POST':

        template = loader.get_template('web_pages/pedovisor_forgetpw.html')

        email = request.POST['email']

        response_data = {}

        try:
            validate_email(email)
        except forms.ValidationError:
            context = {'error': 'ERR_INVALID_EMAIL'}
            return HttpResponse(template.render(context, request))

        try:
            user_valid = User.objects.get(email=email)
        except User.DoesNotExist:
            context = {'error': 'ERR_NO_USER'}
            return HttpResponse(template.render(context, request))

        email_hash = hashlib.sha224(email).hexdigest()

        try:
            html_content = '<p>パスワードリセットが要求されました。<br>' + \
                           '本人に間違えなければ、以下のリンクを開いて新しいパスワードを再設定して下さい。</p>' + \
                           '<a href="http://tk2-402-42013.vs.sakura.ne.jp/dj/web/pedovisor/email-verify?token=' + email_hash + '"><span style="padding:10px;background:#138144;color:#ffffff;font-size:18px;">メール住所確認</span></a>'
            # '<a href="http://192.168.0.137:8000/dj/web/pedovisor/email-verify?token=' + email_hash + '"><span style="padding:10px;background:#138144;color:#ffffff;font-size:18px;">メール住所確認</span></a>'

            msg = EmailMessage("Pedovisorアカウントのメールアドレス確認", html_content, settings.DEFAULT_FROM_EMAIL, [email])
            msg.content_subtype = "html"
            msg.send()
        except:
            context = {'error': 'ERR_SEND_MAIL'}
            return HttpResponse(template.render(context, request))

        try:
            verify = UserVerify.objects.get(user_email=email)
            verify.verify_token = email_hash
            verify.is_verified = 0
            verify.save()
        except UserVerify.DoesNotExist:
            try:
                verify = UserVerify(
                    user_email=email,
                    verify_token=email_hash,
                    is_verified=0
                )
                verify.save()
            except:
                context = {'error': 'ERR_EMAIL_VERIFY'}
                return HttpResponse(template.render(context, request))

        template = loader.get_template('web_pages/pedovisor_send_success.html')
        context = {}
        return HttpResponse(template.render(context, request))

    else:
        template = loader.get_template('web_pages/pedovisor_forgetpw.html')
        context = {}
        return HttpResponse(template.render(context, request))


@csrf_exempt
def pedovisor_email_verify(request):
    token = request.GET['token']

    template = loader.get_template('web_pages/pedovisor_resetpw.html')

    try:
        verify = UserVerify.objects.get(verify_token=token)
    except UserVerify.DoesNotExist:
        template = loader.get_template('web_pages/pedovisor_forgetpw.html')
        context = {'error': 'ERR_EMAIL_VERIFY'}
        return HttpResponse(template.render(context, request))

    verify.is_verified = 1
    verify.save()
    context = {
        'email': verify.user_email
    }
    return HttpResponse(template.render(context, request))


def pedovisor_resetpw(request):
    email = request.POST['email']
    password = request.POST['password']

    template = loader.get_template('web_pages/pedovisor_resetpw.html')
    context = {}

    try:
        validate_email(email)
    except forms.ValidationError:
        context = {
            'error': 'ERR_EMAIL_VERIFY',
            'email': email
        }
        return HttpResponse(template.render(context, request))

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        context = {
            'error': 'ERR_NO_USER',
            'email': email
        }
        return HttpResponse(template.render(context, request))

    try:
        verify = UserVerify.objects.get(user_email=email)
        if verify.is_verified != 1:
            context = {
                'error': 'ERR_EMAIL_VERIFICATION',
                'email': email
            }
            return HttpResponse(template.render(context, request))
    except UserVerify.DoesNotExist:
        context = {
            'error': 'ERR_EMAIL_VERIFICATION',
            'email': email
        }
        return HttpResponse(template.render(context, request))

    try:
        user.set_password(password)
        user.save()
    except:
        context = {
            'error': 'ERR_PASSWORD_SAVE',
            'email': email
        }
        return HttpResponse(template.render(context, request))

    template = loader.get_template('web_pages/pedovisor_reset_success.html')
    context = {}
    return HttpResponse(template.render(context, request))


@login_required(login_url='/dj/web/pedovisor/login')
def pedovisor_changepw(request):
    if request.method == 'POST':
        user = request.user

        cur_password = request.POST['cur_password']
        new_password = request.POST['new_password']

        response_data = {}

        if user.is_staff == 1:
            return redirect('/dj/web/pedovisor/login')

        template = loader.get_template('web_pages/pedovisor_changepw.html')

        try:
            if not user.check_password(cur_password):
                context = {'error': 'ERR_INVALID_PASSWORD'}
                return HttpResponse(template.render(context, request))
        except User.DoesNotExist:
            context = {'error': 'ERR_NO_USER'}
            return HttpResponse(template.render(context, request))

        try:
            user.set_password(new_password)
            user.save()
        except:
            context = {'error': 'ERR_PASSWORD_SAVE'}
            return HttpResponse(template.render(context, request))

        template = loader.get_template('web_pages/pedovisor_reset_success.html')
        context = {}
        return HttpResponse(template.render(context, request))
    else:
        user = request.user

        if user.is_staff == 1:
            return redirect('/dj/web/pedovisor/login')

        template = loader.get_template('web_pages/pedovisor_changepw.html')
        context = {}
        return HttpResponse(template.render(context, request))


@login_required(login_url='/dj/web/pedovisor/login')
def pedovisor_dashboard(request):
    template = loader.get_template('web_pages/pedovisor_dashboard.html')

    data_id = request.GET.get('data_id', None)

    user = request.user

    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

    cursor = connection.cursor()

    sql = """SELECT
                  id                 
                FROM step_count_stepdata 
                WHERE user_id=%s                 
                ORDER BY start_time DESC 
             """ % (user.id,)

    cursor.execute(sql)
    ret = cursor.fetchall()

    if data_id is None and len(ret) > 0:
        data_id = int(list(ret[0])[0])

    id = request.GET.get('id', "")

    context = {
        'data': [int(one[0]) for one in ret],
        'data_id': data_id,
        'id': id
    }
    return HttpResponse(template.render(context, request))


def pedovisor_get_measure_data(request):
    measure_id = request.GET['measure_id']
    response_data = {}

    try:
        step_data = StepData.objects.get(id=measure_id)
    except StepData.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_DATA'
        return JsonResponse(response_data)

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
              """ % (step_data.user_id, step_data.start_time, step_data.start_time)

    cursor.execute(sql)
    ret = list(cursor.fetchone())

    for i in range(len(ret)):
        ret[i] = ret[i] if ret[i] else 0

    result = {
        'id': step_data.id,
        'start_time': step_data.start_time,
        'end_time': step_data.end_time,
        'step_size': step_data.step_size,
        'distance': step_data.distance,
        'latitudes': step_data.latitudes.split(','),
        'longitudes': step_data.longitudes.split(','),
        'step_histogram': json.loads(step_data.step_histogram),
        'step_count': step_data.step_count,
        'activity_name': step_data.activity_name,
        'step_distribution': [
            "{0:.3f}".format((float(step_data.step_level0) / step_data.step_count) if step_data.step_count else 0),
            "{0:.3f}".format((float(step_data.step_level1) / step_data.step_count) if step_data.step_count else 0),
            "{0:.3f}".format((float(step_data.step_level2) / step_data.step_count) if step_data.step_count else 0),
            "{0:.3f}".format((float(step_data.step_level3) / step_data.step_count) if step_data.step_count else 0),
            "{0:.3f}".format((float(step_data.step_level4) / step_data.step_count) if step_data.step_count else 0),
        ],
        'step_month_distribution': [
            "{0:.3f}".format(float(ret[0] / ret[5]) if ret[5] else 0),
            "{0:.3f}".format(float(ret[1] / ret[5]) if ret[5] else 0),
            "{0:.3f}".format(float(ret[2] / ret[5]) if ret[5] else 0),
            "{0:.3f}".format(float(ret[3] / ret[5]) if ret[5] else 0),
            "{0:.3f}".format(float(ret[4] / ret[5]) if ret[5] else 0),
        ]
    }
    response_data['type'] = 'success'
    response_data['content'] = result

    return JsonResponse(response_data)


@login_required(login_url='/dj/web/pedovisor/login')
def pedovisor_set_activity_name(request):
    measure_id = request.POST['measure_id']
    activity_name = request.POST['activity_name']

    response_data = {}
    try:
        step_data = StepData.objects.get(id=measure_id)
    except StepData.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_DATA'
        return JsonResponse(response_data)

    if activity_name == None:
        activity_name = ""

    step_data.activity_name = activity_name

    try:
        step_data.save()
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_DATA_SAVE'

        return JsonResponse(response_data)

    response_data['type'] = 'success'

    return JsonResponse(response_data)


@login_required(login_url='/dj/web/pedovisor/login')
def pedovisor_get_week_data(request):
    try:
        timezone = int(request.GET['timezone'])
    except:
        timezone = 540
    try:
        view_type = int(request.GET['view_type'])
    except:
        view_type = 0
        
    user = request.user

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
                 """ % (timezone, now_utc_time, now_utc_time, timezone, user.id, now_utc_time, now_utc_time)
        sql_1 = """
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 6 DAY)
                      AND DATE(start_time) <= DATE('%s')
                """ % (user.id, now_utc_time, now_utc_time)
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
                 """ % (timezone, now_utc_time, now_utc_time, timezone, user.id, now_utc_time, now_utc_time)
        sql_1 = """
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 1 MONTH)
                      AND DATE(start_time) <= DATE('%s')
                """ % (user.id, now_utc_time, now_utc_time)
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
                 """ % (timezone, now_utc_time, now_utc_time, timezone, user.id, now_utc_time, now_utc_time)
        sql_1 = """
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 3 MONTH)
                      AND DATE(start_time) <= DATE('%s')
                """ % (user.id, now_utc_time, now_utc_time)
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
                 """ % (timezone, now_utc_time, now_utc_time, timezone, user.id, now_utc_time, now_utc_time)
        sql_1 = """
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 6 MONTH)
                      AND DATE(start_time) <= DATE('%s')
                """ % (user.id, now_utc_time, now_utc_time)
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
                 """ % (timezone, now_utc_time, now_utc_time, timezone, user.id, now_utc_time, now_utc_time)

        sql_1 = """
                    SELECT 
                        SUM(distance) AS distance, 
                        SUM(step_count) AS step_count
                    FROM step_count_stepdata 
                    WHERE user_id=%s 
                      AND DATE(start_time) >= DATE_SUB(DATE('%s'), INTERVAL 12 MONTH)
                      AND DATE(start_time) <= DATE('%s')
                """ % (user.id, now_utc_time, now_utc_time)

    cursor.execute(sql)
    ret = cursor.fetchall()

    day = len(ret)

    cursor.execute(sql_1)
    ret_1 = cursor.fetchone()

    data = []
    for one in ret:
        one = {
            "date":one[0],
            "distance":"{0:.2f}".format(one[1]),
            "step_count":one[2],
            "step_size":"{0:.3f}".format(one[1] / float(one[2]) * 100) if one[1] > 0 else 0,
        }
        data.append(one)
    content = {
        "data" : data,
        "all_distance" : "{0:.2f}".format(ret_1[0] if ret_1[0] > 0 else 0),
        "day_distance": "{0:.2f}".format(float(ret_1[0] / day) if ret_1[0] > 0 else 0),
        "all_step_count" : ret_1[1] if ret_1[1] > 0 else 0,
        "day_step_count" : int(ret_1[1] /day) if ret_1[1] > 0 else 0,
    }
    response_data = {}
    response_data['type'] = 'success'
    response_data["content"] = content

    return JsonResponse(response_data)


@login_required(login_url='/dj/web/pedovisor/login')
def pedovisor_get_weight_data(request):
    end_date = request.GET['end_date']
    user = request.user

    response_data = {}

    try:
        profile = UserProfile.objects.get(user_id=user.id)
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
                 """ % (user.id, date_str)

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


@login_required(login_url='/dj/web/pedovisor/login')
def pedovisor_set_weight_data(request):
    user = request.user

    weight = request.POST['weight']
    target_weight = request.POST['target_weight']

    response_data = {}

    if not weight:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_WEIGHT'
        return JsonResponse(response_data)

    if not target_weight:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_TARGET_WEIGHT'
        return JsonResponse(response_data)

    reg_date = datetime.utcnow().strftime('%Y-%m-%d')

    try:
        weight_data = WeightData.objects.get(user_id=user.id, reg_date=reg_date)
        weight_data.weight = weight
        weight_data.target_weight = target_weight
    except WeightData.DoesNotExist:
        weight_data = WeightData(
            user_id=user.id,
            reg_date=reg_date,
            weight=weight,
            target_weight=target_weight
        )

    try:
        weight_data.save()
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_WEIGHTDATA_SAVE'

        return JsonResponse(response_data)

    response_data['type'] = 'success'

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
@login_required(login_url='/dj/web/pedovisor/login')
def pedovisor_get_activity_list(request):
    if request.method == 'POST':
        user = request.user
        draw = int(request.POST.get('draw', 1))
        s_key = request.POST.get('search[value]', '')
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        orders = parseOrder(request)
        activity_list = StepData.objects.filter(user_id=user.id, activity_name__contains=s_key).order_by(orders)[
                        start:start + length]
        json_activity = []
        all_activity_count_filter = StepData.objects.filter(user_id=user.id, activity_name__contains=s_key).count()
        all_activity_count = StepData.objects.filter(user_id=user.id).count()
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


@login_required(login_url='/dj/web/pedovisor/login')
def pedovisor_activity(request):
    user = request.user
    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')
    template = loader.get_template('web_pages/pedovisor_activity.html')
    context = {}
    return HttpResponse(template.render(context, request))


@login_required(login_url='/dj/web/pedovisor/login')
def pedovisor_calendar(request):
    user = request.user
    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')
    template = loader.get_template('web_pages/pedovisor_calendar.html')
    context = {}
    return HttpResponse(template.render(context, request))


@login_required(login_url='/dj/web/pedovisor/login')
def pedovisor_get_event_list(request):
    user = request.user
    start = request.GET['start']
    end = request.GET['end']

    response_data = {}

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
             """ % (user.id, start, end)

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


@login_required(login_url='/dj/web/pedovisor/login')
def pedovisor_detail(request):
    data_id = request.GET.get('data_id', None)
    user = request.user

    template = loader.get_template('web_pages/pedovisor_detail.html')

    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

    if data_id != None:
        try:
            data = StepData.objects.get(id=data_id, user_id=user.id)
        except StepData.DoesNotExist:
            raise Http404('No data!')
    else:
        raise Http404('No data!')

    context = {'data_id': data_id}
    return HttpResponse(template.render(context, request))

@login_required(login_url='/dj/web/pedovisor/login')
def pedovisor_group(request):
    user = request.user
    user_groups = user.groups.all()

    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

    if request.method == 'POST':
        group_ids = request.POST.getlist("group_ids")
        print(group_ids)
        for group in user_groups:
            group.user_set.remove(user)

        if len(group_ids)>0:
            for group_id in group_ids:
                group = Group.objects.get(id=group_id)
                group.user_set.add(user)

    template = loader.get_template('web_pages/pedovisor_group.html')

    group_list = Group.objects.filter()
    user_groups = user.groups.all()
    json_groups = []
    for group in group_list:
        if group in user_groups:
            active = 1
        else:
            active = 0
        json_groups.append({
            "id":group.id,
            "name":group.name,
            "active":active
        })

    context = {'groups': json_groups}
    return HttpResponse(template.render(context, request))

@login_required(login_url='/dj/web/pedovisor/login')
def health(request):
    user = request.user
    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

    food_list = FoodData.objects.filter()
    sq_list = SleepQuality.objects.filter()
    template = loader.get_template('web_pages/pedovisor_health.html')
    id = request.GET.get('id', "")
    context = {
        "food_list" : food_list,
        "sq_list": sq_list,
        "id" : id
    }
    return HttpResponse(template.render(context, request))

@csrf_exempt
@login_required(login_url='/dj/web/pedovisor/login')
def meal_get_list(request):
    user = request.user
    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

    if request.method == 'POST':
        draw = int(request.POST.get('draw', 1))
        s_key = request.POST.get('search[value]', '')
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        orders = parseOrder(request)
        meal_list = MealData.objects.filter(Q(user__id=user.id) & Q(reg_date__contains=s_key)).order_by(orders)[start:start + length]
        all_meal_count = MealData.objects.filter(Q(user__id=user.id) & Q(reg_date__contains=s_key)).count()
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
@login_required(login_url='/dj/web/pedovisor/login')
def meal_get_info(request):
    user = request.user
    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

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
@login_required(login_url='/dj/web/pedovisor/login')
def meal_create(request):
    user = request.user
    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

    if request.method == 'POST':
        response_data = {}
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
        raise Http404('URL解析エラー')

@csrf_exempt
@login_required(login_url='/dj/web/pedovisor/login')
def meal_update(request):
    user = request.user
    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

    if request.method == 'POST':
        response_data = {}
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
        raise Http404('URL解析エラー')

@csrf_exempt
@login_required(login_url='/dj/web/pedovisor/login')
def meal_delete(request):
    user = request.user
    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

    if request.method == 'POST':
        response_data = {}
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

@csrf_exempt
@login_required(login_url='/dj/web/pedovisor/login')
def sleep_get_list(request):
    user = request.user
    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

    if request.method == 'POST':
        draw = int(request.POST.get('draw', 1))
        s_key = request.POST.get('search[value]', '')
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        orders = parseOrder(request)
        sleep_list = SleepData.objects.filter(Q(bed_time__contains=s_key) & Q(user__id=user.id)).order_by(orders)[start:start + length]
        all_sleep_count = SleepData.objects.filter(Q(bed_time__contains=s_key) & Q(user__id=user.id)).count()
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
@login_required(login_url='/dj/web/pedovisor/login')
def sleep_get_info(request):
    user = request.user
    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

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

@csrf_exempt
@login_required(login_url='/dj/web/pedovisor/login')
def sleep_create(request):
    user = request.user
    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

    if request.method == 'POST':
        response_data = {}
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
        raise Http404('URL解析エラー')

@csrf_exempt
@login_required(login_url='/dj/web/pedovisor/login')
def sleep_update(request):
    user = request.user
    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

    if request.method == 'POST':
        response_data = {}
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
        raise Http404('URL解析エラー')

@csrf_exempt
@login_required(login_url='/dj/web/pedovisor/login')
def sleep_delete(request):
    user = request.user
    if user.is_staff == 1:
        return redirect('/dj/web/pedovisor/login')

    if request.method == 'POST':
        response_data = {}
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

