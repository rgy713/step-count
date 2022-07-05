# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import hashlib
import json
import os
import urllib
from datetime import datetime

from django import forms
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.mail.message import EmailMessage
from django.core.validators import validate_email
from django.http import HttpResponse
from django.http import JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

from .models import DataFiles
from .models import UserProfile, UserVerify, StepData


# Create your views here.


def validate_date(str_date):
    try:
        datetime.strptime(str_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")

################################################## VERSION  1 ##########################################################

@csrf_exempt
def v1_send_email_verify(request):
    email = request.POST['email']

    response_data = {}

    try:
        validate_email(email)
    except forms.ValidationError:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID_EMAIL'

        return JsonResponse(response_data)

    try:
        user_valid = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'

        return JsonResponse(response_data)

    email_hash = hashlib.sha224(email).hexdigest()

    try:
        html_content = '<p>パスワードリセットが要求されました。<br>' + \
                       '本人に間違えなければ、以下のリンクを開いて新しいパスワードを再設定して下さい。</p>' + \
                       '<a href="http://tk2-402-42013.vs.sakura.ne.jp/dj/step/v1/user/email-verify?token=' + email_hash + '"><span style="padding:10px;background:#138144;color:#ffffff;font-size:18px;">メール住所確認</span></a>'

        msg = EmailMessage("Pedovisorアカウントのメールアドレス確認", html_content, settings.DEFAULT_FROM_EMAIL, [email])
        msg.content_subtype = "html"
        msg.send()
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_SEND_MAIL'

        return JsonResponse(response_data)

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
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_EMAIL_VERIFY'

            return JsonResponse(response_data)

    response_data['type'] = 'success'
    response_data['content'] = 'OK'

    return JsonResponse(response_data)


@csrf_exempt
def v1_email_verify(request):
    token = request.GET['token']

    template = loader.get_template('client/index.html')

    try:
        verify = UserVerify.objects.get(verify_token=token)
    except UserVerify.DoesNotExist:
        context = {
            'title': "Pedovisorアカウントのメールアドレス確認",
            'content': "メールアカウントに問題があります。 登録しなおしてください。"
        }
        return HttpResponse(template.render(context, request))

    verify.is_verified = 1
    verify.save()
    context = {
        'title': "Pedovisorアカウントのメールアドレス確認",
        'content': "あなたのメールを確認しました。 Pedovisorアプリを起動し、パスワードを入力してください。"
    }
    return HttpResponse(template.render(context, request))


@csrf_exempt
def v1_check_verify(request):
    email = request.POST['email']

    response_data = {}

    try:
        validate_email(email)
    except forms.ValidationError:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID_EMAIL'

        return JsonResponse(response_data)

    try:
        verify = UserVerify.objects.get(user_email=email)
    except UserVerify.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'

        return JsonResponse(response_data)

    if verify.is_verified == 1:

        response_data['type'] = 'success'
        response_data['content'] = 'OK'

        return JsonResponse(response_data)
    else:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_UNVERIFIED_EMAIL'

        return JsonResponse(response_data)


@csrf_exempt
def v1_user_create(request):
    email = request.POST['email']
    password = request.POST['password']
    height = 170  # Default value
    weight = 65  # Default value
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
        user = User.objects.create_user(username=email, email=email, password=password)
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_USER_CREATE'

        return JsonResponse(response_data)

    try:
        profile = UserProfile(
            user_id=user.id,
            height=height,
            weight=weight,
        )
        profile.save()
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_PROFILE_SAVE'

        return JsonResponse(response_data)

    response_data['type'] = 'success'

    return JsonResponse(response_data)


@csrf_exempt
def v1_user_login(request):
    email = request.POST['email']
    password = request.POST['password']
    response_data = {}

    try:
        user = User.objects.get(email=email)
        if not user.check_password(password):
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_INVALID_PASSWORD'

            return JsonResponse(response_data)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'

        return JsonResponse(response_data)

    login(request, user)

    try:
        profile = UserProfile.objects.get(user_id=user.id)
    except UserProfile.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_PROFILE'

        return JsonResponse(response_data)

    response_data['type'] = 'success'
    response_data['content'] = {
        'height': profile.height,
        'habbit': profile.habbit,
        'step_size': profile.step_size,
        'email': user.email,
        'gender': profile.gender,
    }

    if profile.name != None:
        response_data['content']['name'] = profile.name
    else:
        response_data['content']['name'] = ""

    if profile.birthday != None:
        response_data['content']['birthday'] = profile.birthday
    else:
        response_data['content']['birthday'] = ""

    if profile.weight != None:
        response_data['content']['weight'] = profile.weight
    else:
        response_data['content']['weight'] = 0

    return JsonResponse(response_data)


@csrf_exempt
def v1_user_modify(request):
    email = request.POST.get('email')
    name = request.POST.get('name', None)
    birthday = request.POST.get('birthday', None)
    height = request.POST.get('height', None)
    weight = request.POST.get('weight', None)
    habbit = request.POST.get('habbit', None)
    step_size = request.POST.get('step_size', None)
    gender = request.POST.get('gender', None)

    response_data = {}

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID_USER'

        return JsonResponse(response_data)

    try:
        profile = UserProfile.objects.get(user_id=user.id)
    except UserProfile.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_PROFILE'

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


@csrf_exempt
def v1_user_change_pw(request):
    email = request.POST['email']
    cur_password = request.POST['cur_password']
    new_password = request.POST['new_password']

    response_data = {}

    try:
        user = User.objects.get(email=email)
        if not user.check_password(cur_password):
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_INVALID_PASSWORD'

            return JsonResponse(response_data)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'

        return JsonResponse(response_data)

    try:
        user.set_password(new_password)
        user.save()
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_PASSWORD_SAVE'

        return JsonResponse(response_data)

    response_data['type'] = 'success'

    return JsonResponse(response_data)


@csrf_exempt
def v1_user_reset_pw(request):
    email = request.POST['email']
    password = request.POST['password']

    response_data = {}

    try:
        validate_email(email)
    except forms.ValidationError:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID_EMAIL'

        return JsonResponse(response_data)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'

        return JsonResponse(response_data)

    try:
        verify = UserVerify.objects.get(user_email=email)
        if verify.is_verified != 1:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_EMAIL_VERIFICATION'

            return JsonResponse(response_data)
    except UserVerify.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'

        return JsonResponse(response_data)

    try:
        user.set_password(password)
        user.save()
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_PASSWORD_SAVE'

        return JsonResponse(response_data)

    response_data['type'] = 'success'

    return JsonResponse(response_data)


@csrf_exempt
def v1_data_upload(request):
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

        if fs.exists(name=machine_id):
            fs.delete(name=machine_id)

        try:
            filename = fs.save(machine_id, data_file)
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_FILE_SAVE'

            return JsonResponse(response_data)

        uploaded_file_url = fs.url(filename)

        response_data['type'] = 'success'

        return JsonResponse(response_data)

    response_data['type'] = 'error'
    response_data['content'] = 'ERR_NO_FILE'

    return JsonResponse(response_data)


@csrf_exempt
def v1_data_download(request, email, machine_id):
    response_data = {}

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'

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