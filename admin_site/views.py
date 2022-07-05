# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db.models import Q
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.core.mail import EmailMessage
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.http import HttpResponse, JsonResponse, Http404
from django.core.validators import validate_email
from django import forms
from step_count.models import UserProfile, DataFiles, UserVerify
from datetime import datetime

import hashlib
import urllib
import os
from django.conf import settings


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


# Create your views here.
@csrf_exempt
def login(request):
    if request.method == "POST":
        form = AdminAuthenticationForm(request, data=request.POST)
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if (not user is None) and user.is_staff == 1:
            auth.login(request, user)
            next_l = request.META['HTTP_REFERER'].split("?next=")
            if len(next_l) > 1 and next_l[1] != "":
                return redirect(next_l[1].split("&")[0])
            else:
                return redirect('/dj/admin/')
        else:
            template = loader.get_template('admin_site/login.html')
            form.errors['error'] = "error"
            context = {
                'form': form,
            }
            return HttpResponse(template.render(context, request))

    if request.method == "GET":
        form = AdminAuthenticationForm
        template = loader.get_template('admin_site/login.html')
        context = {'form': form}
        return HttpResponse(template.render(context, request))


@login_required(login_url='/dj/admin/login')
def index(request):
    if request.user.is_staff == 0:
        return redirect('/dj/admin/login')
    else:
        return redirect('/dj/admin/user')
        template = loader.get_template('admin_site/index.html')
        context = {
            'current': "dashboard",
        }
        return HttpResponse(template.render(context, request))


def forgetpw(request):
    if request.method == 'POST':
        template = loader.get_template('admin_site/forgetpw.html')

        email = request.POST.get('email',None)

        response_data = {}

        if not email:
            context = {'error': 'ERR_INVALID_EMAIL'}
            return HttpResponse(template.render(context, request))

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
                           '<a href="http://dependa.co.jp/dj/admin/email-verify?token=' + email_hash + '"><span style="padding:10px;background:#138144;color:#ffffff;font-size:18px;">メール住所確認</span></a>'
            # '<a href="http://192.168.0.137:8000/dj/admin/email-verify?token=' + email_hash + '"><span style="padding:10px;background:#138144;color:#ffffff;font-size:18px;">メール住所確認</span></a>'

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

        template = loader.get_template('admin_site/send_success.html')
        context = {}
        return HttpResponse(template.render(context, request))

    else:
        template = loader.get_template('admin_site/forgetpw.html')
        context = {}
        return HttpResponse(template.render(context, request))


@csrf_exempt
def email_verify(request):
    token = request.GET['token']

    template = loader.get_template('admin_site/resetpw.html')

    try:
        verify = UserVerify.objects.get(verify_token=token)
    except UserVerify.DoesNotExist:
        template = loader.get_template('admin_site/forgetpw.html')
        context = {'error': 'ERR_EMAIL_VERIFY'}
        return HttpResponse(template.render(context, request))

    verify.is_verified = 1
    verify.save()
    context = {
        'email': verify.user_email
    }
    return HttpResponse(template.render(context, request))


def resetpw(request):
    if request.method == 'POST':
        email = request.POST.get('email', None)
        password = request.POST.get('password', None)

        template = loader.get_template('admin_site/resetpw.html')
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

        template = loader.get_template('admin_site/reset_success.html')
        context = {}
        return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('admin_site/resetpw.html')
        context = {}
        return HttpResponse(template.render(context, request))


@login_required(login_url='/dj/admin/login')
def profile(request):
    if request.user.is_staff == 0:
        return redirect('/dj/admin/login')
    template = loader.get_template('admin_site/profile.html')
    context = {
    }
    return HttpResponse(template.render(context, request))


@login_required(login_url='/dj/admin/login')
def change_password(request):
    if request.method == 'POST':
        user = request.user

        old_password = request.POST['old_password']
        new_password = request.POST['new_password']

        response_data = {}

        try:
            if not user.check_password(old_password):
                response_data = {
                    "type": "error",
                    "content": 'ERR_INVALID_PASSWORD'
                }
                return JsonResponse(response_data)

        except User.DoesNotExist:
            response_data = {
                "type": "error",
                "content": 'ERR_NO_USRER'
            }
            return JsonResponse(response_data)

        try:
            user.set_password(new_password)
            user.save()
        except:
            response_data = {
                "type": "error",
                "content": 'ERR_PASSWORD_SAVE'
            }
            return JsonResponse(response_data)

        response_data = {
            "type": "success"
        }
        return JsonResponse(response_data)
    else:
        raise Http404('URL解析エラー')


@login_required(login_url='/dj/admin/login')
def user_index(request):
    if request.user.is_staff == 0:
        return redirect('/dj/admin/login')
    group_list = Group.objects.filter()
    template = loader.get_template('admin_site/user.html')
    context = {
        'current': "user",
        'group_list': group_list
    }
    return HttpResponse(template.render(context, request))


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def get_user_list(request):
    if request.method == 'POST':
        group_id = int(request.POST.get('group_id', 0))
        draw = int(request.POST.get('draw', 1))
        s_key = request.POST.get('search[value]', '')
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        orders = parseOrder(request)
        if group_id > 0:
            user_list = UserProfile.objects.filter(Q(name__contains=s_key) & Q(user__is_staff=0) & Q(user__groups__id=group_id)).order_by(orders)[start:start + length]
            all_user_count = UserProfile.objects.filter( Q(name__contains=s_key) & Q(user__is_staff=0) & Q(user__groups__id=group_id)).count()
        else:
            user_list = UserProfile.objects.filter((Q(name__contains=s_key) | Q(user__email__contains=s_key)) & Q(user__is_staff=0)).order_by(orders)[start:start + length]
            all_user_count = UserProfile.objects.filter((Q(name__contains=s_key) | Q(user__email__contains=s_key)) & Q(user__is_staff=0)).count()
        json_users = []
        idx = 0
        for user in user_list:
            idx += 1
            number = start + idx
            user_info = User.objects.get(id=user.user_id)
            json_user = {
                'number': number,
                'email': user.user.email,
                'id': user.id,
                'user_id': user.user_id,
                'name': user.name,
                'gender': user.gender,
                'birthday': user.birthday,
                'height': user.height,
                'weight': user.weight,
                # 'last_login':user_info.last_login,
            }
            json_users.append(json_user)

        return JsonResponse(
            {'draw': draw + 1, 'recordsFiltered': all_user_count, 'recordsTotal': all_user_count, 'data': json_users})
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def get_user_info(request):
    if request.method == 'POST':
        user_id = int(request.POST.get('user_id', 0))
        user_info = User.objects.filter(userprofile__user_id=user_id).values_list('id', 'email',
                                                                                  'userprofile__name',
                                                                                  'userprofile__gender',
                                                                                  'userprofile__birthday',
                                                                                  'userprofile__height',
                                                                                  'userprofile__weight',
                                                                                  'userprofile__habbit',
                                                                                  'userprofile__step_size')
        if (len(user_info) > 0):
            json_user = {
                'id': user_info[0][0],
                'email': user_info[0][1],
                'name': user_info[0][2],
                'gender': user_info[0][3],
                'birthday': user_info[0][4],
                'height': user_info[0][5],
                'weight': user_info[0][6],
                'habbit': user_info[0][7],
                'step_size': user_info[0][8]
            }
            response = {
                "type": "success",
                "content": json_user
            }
        else:
            response = {
                "type": "error",
            }
        return JsonResponse(response)
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def delete_user(request):
    if request.method == 'POST':
        uid = int(request.POST.get('user_id', 0))
        admin = request.user
        try:
            if admin.is_superuser:
                User.objects.filter(id=uid).delete()
                UserProfile.objects.filter(user_id=uid).delete()
            else:
                group = admin.groups.all()[0]
                user = User.objects.get(id=uid)
                group.user_set.remove(user)
            response = {
                "type": "success"
            }
        except:
            response = {
                "type": "error"
            }
        return JsonResponse(response)
    else:
        raise Http404('URL解析エラー')


@login_required(login_url='/dj/admin/login')
def user_create(request):
    email = request.POST['email']
    username = email
    name = request.POST['name']
    birthday = request.POST['birthday']
    height = request.POST['height']
    weight = request.POST['weight']
    habbit = request.POST['habbit']
    step_size = request.POST['step_size']
    gender = request.POST['gender']

    group_id = request.POST.get('group_id', 0)

    response_data = {}

    try:
        validate_email(email)
    except forms.ValidationError:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID_EMAIL'

        return JsonResponse(response_data)

    valid_count = User.objects.filter(email=email).count()
    if valid_count > 0:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_EMAIL_ALREADY_EXISTS'

        return JsonResponse(response_data)

    try:
        user = User.objects.create_user(username=username, email=email, password="123456")
        if group_id > 0:
            group = Group.objects.get(id=group_id)
            group.user_set.add(user)
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_USER_CREATE'

        return JsonResponse(response_data)

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
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_PROFILE_SAVE'

        return JsonResponse(response_data)

    response_data['type'] = 'success'

    return JsonResponse(response_data)


@login_required(login_url='/dj/admin/login')
def user_modify(request):
    userid = request.POST['user_id']
    email = request.POST.get('email', None)
    name = request.POST.get('name', None)
    birthday = request.POST.get('birthday', None)
    height = request.POST.get('height', None)
    weight = request.POST.get('weight', None)
    habbit = request.POST.get('habbit', None)
    step_size = request.POST.get('step_size', None)
    gender = request.POST.get('gender', None)

    response_data = {}

    user = User.objects.get(id=userid)
    if email is not None:
        try:
            try:
                validate_email(email)
            except forms.ValidationError:
                response_data['type'] = 'error'
                response_data['content'] = 'ERR_INVALID_EMAIL'

                return JsonResponse(response_data)

            valid_count = User.objects.exclude(id=userid).filter(email=email).count()
            if valid_count > 0:
                response_data['type'] = 'error'
                response_data['content'] = 'ERR_EMAIL_ALREADY_EXISTS'

                return JsonResponse(response_data)

            user.email = email
            user.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_EMAIL_SAVE'

            return JsonResponse(response_data)

    try:
        profile = UserProfile.objects.get(user_id=userid)
    except UserProfile.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOPROFILE'

        return JsonResponse(response_data)

    if name is not None:
        profile.name = name
    if birthday is not None:
        try:
            validate_date(birthday)
        except ValueError:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_INVALID_BIRTHDAY'

            return JsonResponse(response_data)

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
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_PROFILE_SAVE'

        return JsonResponse(response_data)

    response_data['type'] = 'success'

    return JsonResponse(response_data)


def validate_date(str_date):
    try:
        datetime.strptime(str_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")


@login_required(login_url='/dj/admin/login')
def get_user_machine_list(request):
    if request.method == 'POST':
        userid = request.POST['user_id']
        draw = int(request.POST.get('draw', 1))
        s_key = request.POST.get('search[value]', '')
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        orders = parseOrder(request)
        # machine_list = DataFiles.objects.filter(user_id=userid).order_by(orders)[start:start + length]
        machine_list = DataFiles.objects.filter(user_id=userid)
        email = ''
        if userid != '0':
            email = User.objects.values_list('email', flat=True).get(id=userid)
        json_datas = []
        all_count = DataFiles.objects.filter(user=userid).count()
        idx = 0
        if len(machine_list) > 0:
            for one in machine_list:
                idx += 1
                number = start + idx
                json_data = {
                    'number': number,
                    'machine_id': one.machine_id,
                    'email': email
                }
                json_datas.append(json_data)
        return JsonResponse(
            {'draw': draw + 1, 'recordsFiltered': all_count, 'recordsTotal': all_count, 'data': json_datas})
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
def data_download(request, email, machine_id):
    response_data = {}

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOUSER'

        return JsonResponse(response_data)

    try:
        data_info = DataFiles.objects.get(user_id=user.id, machine_id=machine_id)
    except DataFiles.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOMACHINE'

        return JsonResponse(response_data)

    file_path = os.path.join(settings.MEDIA_ROOT, str(user.id), machine_id)
    if os.path.exists(file_path):
        try:
            fp = open(file_path, str('rb'))
            response = HttpResponse(fp.read())
            fp.close()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_FILE_READ'

            return JsonResponse(response_data)

        response['Content-Type'] = 'application/octet-stream'
        response['Content-Length'] = str(os.stat(file_path).st_size)
        response['Content-Encoding'] = 'utf-8'
        if not ".csv" in data_info.filename:
            data_info.filename = data_info.filename + ".csv"
        # To inspect details for the below code, see http://greenbytes.de/tech/tc2231/
        if u'WebKit' in request.META['HTTP_USER_AGENT']:
            # Safari 3.0 and Chrome 2.0 accepts UTF-8 encoded string directly.
            filename_header = 'filename=%s' % data_info.filename.encode('utf-8')
        elif u'MSIE' in request.META['HTTP_USER_AGENT']:
            # IE does not support internationalized filename at all.
            # It can only recognize internationalized URL, so we do the trick via routing rules.
            filename_header = ''
        else:
            # For others like Firefox, we follow RFC2231 (encoding extension in HTTP headers).
            filename_header = 'filename*=UTF-8\'\'%s' % urllib.quote(data_info.filename.encode('utf-8'))

        response['Content-Disposition'] = 'attachment; ' + filename_header

        return response

    response_data['type'] = 'error'
    response_data['content'] = 'ERR_NOT_EXISTS'

    return JsonResponse(response_data)


@login_required(login_url='/dj/admin/login')
def group_index(request):
    if request.user.is_staff == 0:
        return redirect('/dj/admin/login')
    template = loader.get_template('admin_site/group.html')
    context = {
        'current': "group",
    }
    return HttpResponse(template.render(context, request))


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def group_get_list(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 1))
        s_key = request.POST.get('search[value]', '')
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        orders = parseOrder(request)
        group_list = Group.objects.filter(Q(name__contains=s_key) & Q(user__is_staff=1)).values_list('id', 'name',
                                                                                                     'user__email').order_by(
            orders)[start:start + length]
        json_groups = []
        all_group_count = Group.objects.filter(name__contains=s_key).count()
        idx = 0
        for group in group_list:
            idx += 1
            number = start + idx

            json_group = {
                'number': number,
                'id': group[0],
                'name': group[1],
                'email': group[2],
            }
            json_groups.append(json_group)

        return JsonResponse({'draw': draw + 1, 'recordsFiltered': all_group_count, 'recordsTotal': all_group_count,
                             'data': json_groups})
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def group_get_info(request):
    if request.method == 'POST':
        id = int(request.POST.get('id', 0))
        group_info = Group.objects.filter(Q(id=id) & Q(user__is_staff=1)).values_list('id', 'name', 'user__email')
        if (len(group_info) > 0):
            json_group = {
                'id': group_info[0][0],
                'name': group_info[0][1],
                'email': group_info[0][2],
            }
            response = {
                "type": "success",
                "content": json_group
            }
        else:
            response = {
                "type": "error",
            }
        return JsonResponse(response)
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def group_delete(request):
    if request.method == 'POST':
        id = int(request.POST.get('id', 0))
        try:
            group_info = Group.objects.filter(Q(id=id) & Q(user__is_staff=1)).values_list('id', 'name', 'user__id')
            user_id = group_info[0][2]
            Group.objects.get(id=id).delete()
            User.objects.get(id=user_id).delete()
            response = {
                "type": "success"
            }
        except:
            response = {
                "type": "error"
            }
        return JsonResponse(response)
    else:
        raise Http404('URL解析エラー')


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def group_update(request):
    id = request.POST['id']
    name = request.POST.get('name', None)
    email = request.POST.get('email', None)

    response_data = {}

    if id is None or name is None or email is None:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID'
        return JsonResponse(response_data)

    try:
        group = Group.objects.get(id=id)
    except Group.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NOGROUP'
        return JsonResponse(response_data)

    valid_count = Group.objects.filter(Q(name=name) & ~Q(id=id)).count()
    if valid_count > 0:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NAME_ALREADY_EXISTS'
        return JsonResponse(response_data)


    group_info = Group.objects.filter(Q(id=id) & Q(user__is_staff=1)).values_list('id', 'name', 'user__id')
    user_id = group_info[0][2]
    user = User.objects.get(id=user_id)
    try:
        validate_email(email)
    except forms.ValidationError:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID_EMAIL'
        return JsonResponse(response_data)

    valid_count = User.objects.filter(~Q(id=user_id) & Q(email=email)).count()
    if valid_count > 0:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_EMAIL_ALREADY_EXISTS'
        return JsonResponse(response_data)
    else:
        try:
            user.email = email
            user.username = email
            user.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_USER_SAVE'

    group.name = name

    try:
        group.save()
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_GROUP_SAVE'

        return JsonResponse(response_data)

    response_data['type'] = 'success'

    return JsonResponse(response_data)


@csrf_exempt
@login_required(login_url='/dj/admin/login')
def group_create(request):
    name = request.POST.get('name', None)
    email = request.POST.get('email', None)

    response_data = {}

    if name is None or email is None:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID'
        return JsonResponse(response_data)

    valid_count = Group.objects.filter(name=name).count()
    if valid_count > 0:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NAME_ALREADY_EXISTS'
        return JsonResponse(response_data)

    try:
        validate_email(email)
    except forms.ValidationError:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID_EMAIL'
        return JsonResponse(response_data)

    valid_count = User.objects.filter(email=email).count()
    if valid_count > 0:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_EMAIL_ALREADY_EXISTS'
        return JsonResponse(response_data)

    try:
        user = User.objects.create_user(username=email, email=email, password="123456", is_staff=1)
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_USER_CREATE'

        return JsonResponse(response_data)

    try:
        group = Group.objects.create(name=name)
        group.user_set.add(user)
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_GROUP_CREATE'

        return JsonResponse(response_data)

    response_data['type'] = 'success'

    return JsonResponse(response_data)

@login_required(login_url='/dj/admin/login')
def change_group_name(request):
    admin = request.user
    name = request.POST.get('name', None)

    response_data = {}

    if name is None:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID'
        return JsonResponse(response_data)


    group = admin.groups.all()[0]

    valid_count = Group.objects.filter(Q(name=name) & ~Q(id=group.id)).count()
    if valid_count > 0:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NAME_ALREADY_EXISTS'
        return JsonResponse(response_data)

    group.name = name

    try:
        group.save()
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_GROUP_SAVE'

        return JsonResponse(response_data)

    response_data['type'] = 'success'

    return JsonResponse(response_data)