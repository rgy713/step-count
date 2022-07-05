# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import urllib
from datetime import datetime

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import DataFiles
from .models import UserProfile


# Create your views here.

def validate_date(str_date):
    try:
        datetime.strptime(str_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")


@csrf_exempt
def user_create(request):
    username = request.POST['username']
    password = request.POST['password']
    email = request.POST['email']
    # name = request.POST['name']
    # birthday = request.POST['birthday']
    height = request.POST['height']
    # weight = request.POST['weight']
    # habbit = request.POST['habbit']
    # step_size = request.POST['step_size']
    # gender = request.POST['gender']

    response_data = {}

    try:
        validate_email(email)
    except forms.ValidationError:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID_EMAIL'

        return JsonResponse(response_data)

    # try:
    #     validate_date(birthday)
    # except ValueError:
    #     response_data['type'] = 'error'
    #     response_data['content'] = 'ERR_INVALID_BIRTHDAY'
    #
    #     return JsonResponse(response_data)

    valid_count = User.objects.filter(username=username).count()
    if valid_count > 0:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_USERNAME_ALREADY_EXISTS'

        return JsonResponse(response_data)

    valid_count = User.objects.filter(email=email).count()
    if valid_count > 0:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_EMAIL_ALREADY_EXISTS'

        return JsonResponse(response_data)

    try:
        first_name = ""
        user = User.objects.create_user(username=username, email=email, password=password, first_name=first_name)
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_USER_CREATE'

        return JsonResponse(response_data)

    try:
        profile = UserProfile(
            user_id=user.id,
            # name=name,
            # birthday=birthday,
            height=height,
            # weight=weight,
            # habbit=habbit,
            # step_size=step_size,
            # gender=gender
        )
        profile.save()
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_PROFILE_SAVE'

        return JsonResponse(response_data)

    response_data['type'] = 'success'

    return JsonResponse(response_data)


@csrf_exempt
def user_login(request):
    username = request.POST['username']
    password = request.POST['password']
    response_data = {}

    user = authenticate(request, username=username, password=password)
    if user is None:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID_LOGIN'

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
def user_logout(request):
    logout(request)

    return JsonResponse({'type': 'success'})


@csrf_exempt
def user_modify(request):
    username = request.POST['username']
    email = request.POST.get('email', None)
    name = request.POST.get('name', None)
    birthday = request.POST.get('birthday', None)
    height = request.POST.get('height', None)
    weight = request.POST.get('weight', None)
    habbit = request.POST.get('habbit', None)
    step_size = request.POST.get('step_size', None)
    gender = request.POST.get('gender', None)

    response_data = {}

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID_USERNAME'

        return JsonResponse(response_data)

    if email is not None:

        try:
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

            user.email = email
            user.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_EMAIL_SAVE'

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
def user_change_pw(request):
    username = request.POST['username']
    cur_password = request.POST['cur_password']
    new_password = request.POST['new_password']

    response_data = {}

    user = authenticate(request, username=username, password=cur_password)
    if user is None:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID_AUTHENTICATE'

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
def user_mail_for_code(request):
    email = request.POST['email']
    # birthday = request.POST['birthday']

    response_data = {}

    try:
        validate_email(email)
    except forms.ValidationError:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_INVALID_EMAIL'

        return JsonResponse(response_data)

    # try:
    #     validate_date(birthday)
    # except ValueError:
    #     response_data['type'] = 'error'
    #     response_data['content'] = 'ERR_INVALID_BIRTHDAY'
    #
    #     return JsonResponse(response_data)

    # valid_count = User.objects.filter(email=email).filter(userprofile__birthday=birthday).count()
    valid_count = User.objects.filter(email=email).count()
    if valid_count > 0:
        user = User.objects.get(email=email)

        # 일단은 검증코드를 4자리로 하고 림시 해당 유저의 패스워드로 규정한다.
        verification_code = User.objects.make_random_password(length=4)

        try:
            send_mail("パスワードのリセット", "パスワードをリセットするには、次のの検証コードをご利用下さい。\r\n" + verification_code,
                      settings.DEFAULT_FROM_EMAIL, [email])
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_SEND_MAIL'

            return JsonResponse(response_data)

        try:
            user.first_name = verification_code
            user.save()
        except:
            response_data['type'] = 'error'
            response_data['content'] = 'ERR_CODE_SAVE'

            return JsonResponse(response_data)

    else:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_NO_USER'

        return JsonResponse(response_data)

    response_data['type'] = 'success'

    return JsonResponse(response_data)


@csrf_exempt
def user_reset_pw(request):
    email = request.POST['email']
    verification_code = request.POST['code']
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
    
    if user.first_name != verification_code or verification_code == "":
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_VERIFICATION_CODE'

        return JsonResponse(response_data)

    try:
        user.set_password(password)
        user.first_name = ""
        user.save()
    except:
        response_data['type'] = 'error'
        response_data['content'] = 'ERR_PASSWORD_SAVE'

        return JsonResponse(response_data)

    response_data['type'] = 'success'

    return JsonResponse(response_data)


@csrf_exempt
def data_upload(request):
    response_data = {}

    if request.method == 'POST' and request.FILES['data']:
        username = request.POST['username']
        machine_id = request.POST['machine_id']
        data_file = request.FILES['data']

        try:
            user = User.objects.get(username=username)
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
def data_download(request, username, machine_id):
    response_data = {}

    try:
        user = User.objects.get(username=username)
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