from django.conf.urls import url

from . import views
from . import views_v1
from . import views_v2
from django.conf import settings
from django.conf.urls.static import static


# if settings.DEBUG:
urlpatterns = [
    url(r'^user/create', views.user_create, name='create'),
    url(r'^user/login', views.user_login, name='login'),
    url(r'^user/logout', views.user_logout, name='logout'),
    url(r'^user/modify', views.user_modify, name='modify'),
    url(r'^user/change_pw', views.user_change_pw, name='change_pw'),
    url(r'^user/verification', views.user_mail_for_code, name='verification'),
    url(r'^user/reset_pw', views.user_reset_pw, name='reset_pw'),
    url(r'^data/upload', views.data_upload, name='data_upload'),
    url(r'^data/download/(?P<username>[\w.@+-]+)/(?P<machine_id>[\w.@+-]+)/$', views.data_download, name='data_download'),
    #   version 1
    url(r'^v1/user/send-email-verify', views_v1.v1_send_email_verify, name='v1_send_email_verify'),
    url(r'^v1/user/email-verify', views_v1.v1_email_verify, name='v1_email_verify'),
    url(r'^v1/user/check-verify', views_v1.v1_check_verify, name='v1_check_verify'),
    url(r'^v1/user/create', views_v1.v1_user_create, name='v1_user_create'),
    url(r'^v1/user/login', views_v1.v1_user_login, name='v1_login'),
    url(r'^v1/user/logout', views.user_logout, name='logout'),
    url(r'^v1/user/modify', views_v1.v1_user_modify, name='v1_modify'),
    url(r'^v1/user/change_pw', views_v1.v1_user_change_pw, name='v1_change_pw'),
    url(r'^v1/user/reset_pw', views_v1.v1_user_reset_pw, name='v1_reset_pw'),
    url(r'^v1/data/upload', views_v1.v1_data_upload, name='v1_data_upload'),
    url(r'^v1/data/download/(?P<email>[\w.@+-]+)/(?P<machine_id>[\w.@+-]+)/$', views_v1.v1_data_download, name='v1_data_download'),
    #   version 2
    url(r'^v2/data/upload', views_v2.v2_data_upload, name='v2_data_upload'),
    url(r'^v2/data/get-main-data', views_v2.v2_get_main_data, name='v2_get_main_data'),
    url(r'^v2/data/get-calendar-data', views_v2.v2_get_calendar_data, name='v2_get_calendar_data'),
    url(r'^v2/data/get-measurement-data', views_v2.v2_get_measurement_data, name='v2_get_measurement_data'),
    url(r'^v2/user/send-email-verify', views_v1.v1_send_email_verify, name='v2_send_email_verify'),
    url(r'^v2/user/email-verify', views_v1.v1_email_verify, name='v2_email_verify'),
    url(r'^v2/user/check-verify', views_v1.v1_check_verify, name='v2_check_verify'),
    url(r'^v2/user/create', views_v1.v1_user_create, name='v2_user_create'),
    url(r'^v2/user/login', views_v1.v1_user_login, name='v2_login'),
    url(r'^v2/user/logout', views.user_logout, name='logout'),
    url(r'^v2/user/modify', views_v1.v1_user_modify, name='v2_modify'),
    url(r'^v2/user/change_pw', views_v1.v1_user_change_pw, name='v2_change_pw'),
    url(r'^v2/user/reset_pw', views_v1.v1_user_reset_pw, name='v2_reset_pw'),
    # addition
    url(r'^v2/user/get-groups', views_v2.get_user_groups, name='v2.get_groups'),
    url(r'^v2/user/set-groups', views_v2.set_user_groups, name='v2.set_groups'),
    url(r'^v2/health/get-food-list', views_v2.get_food_list, name='v2.health.get_food_list'),
    url(r'^v2/health/get-sq-list', views_v2.get_sq_list, name='v2.health.get_sq_list'),
    url(r'^v2/health/meal-get-list', views_v2.meal_get_list, name='v2.health.meal_get_list'),
    url(r'^v2/health/meal-get-info', views_v2.meal_get_info, name='v2.health.meal_get_info'),
    url(r'^v2/health/meal-create', views_v2.meal_create, name='v2.health.meal_create'),
    url(r'^v2/health/meal-update', views_v2.meal_update, name='v2.health.meal_update'),
    url(r'^v2/health/meal-delete', views_v2.meal_delete, name='v2.health.meal_delete'),
    url(r'^v2/health/sleep-get-list', views_v2.sleep_get_list, name='v2.health.sleep_get_list'),
    url(r'^v2/health/sleep-get-info', views_v2.sleep_get_info, name='v2.health.sleep_get_info'),
    url(r'^v2/health/sleep-create', views_v2.sleep_create, name='v2.health.sleep_create'),
    url(r'^v2/health/sleep-update', views_v2.sleep_update, name='v2.health.sleep_update'),
    url(r'^v2/health/sleep-delete', views_v2.sleep_delete, name='v2.health.sleep_delete'),
    url(r'^v2/health/get-score-data$', views_v2.get_score_data, name='v2.health.get_score_data'),
    url(r'^v2/health/weight-get-month-list$', views_v2.weight_get_month_list, name='v2.health.weight_get_month_list'),
    url(r'^v2/health/weight-get-list$', views_v2.weight_get_list, name='v2.health.weight_get_list'),
    url(r'^v2/health/weight-add$', views_v2.weight_add, name='v2.health.weight_add'),
    url(r'^v2/health/weight-update$', views_v2.weight_update, name='v2.health.weight_update'),
    url(r'^v2/health/weight-delete$', views_v2.weight_delete, name='v2.health.weight_delete'),
]
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
