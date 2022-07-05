from django.conf.urls import include, url
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.contrib import admin

urlpatterns = [
    url(r'^$', views.index, name='web_index'),
    # url(r'^pedovisor/home/$', views.pedovisor_home, name='pedovisor_home'),
    url(r'^pedovisor/login$', views.pedovisor_login, name='pedovisor_login'),
    url(r'^pedovisor/logout$', auth_views.logout, name='pedovisor_logout', kwargs={'next_page': '/dj/web/pedovisor/login', }),
    url(r'^pedovisor/dashboard$', views.pedovisor_dashboard, name='pedovisor_dashboard'),
    url(r'^pedovisor/signup$', views.pedovisor_signup, name='pedovisor_signup'),
    url(r'^pedovisor/signup-success$', views.pedovisor_signup_success, name='pedovisor_signup_success'),
    url(r'^pedovisor/user$', views.pedovisor_user, name='pedovisor_user'),
    url(r'^pedovisor/forget-password$', views.pedovisor_forgetpw, name='pedovisor_forgetpw'),
    url(r'^pedovisor/email-verify$', views.pedovisor_email_verify, name='pedovisor_email_verify'),
    url(r'^pedovisor/reset-password$', views.pedovisor_resetpw, name='pedovisor_resetpw'),
    url(r'^pedovisor/change-password$', views.pedovisor_changepw, name='pedovisor_changepw'),
    url(r'^pedovisor/get-measure-data$', views.pedovisor_get_measure_data, name='pedovisor_get_measure_data'),
    url(r'^pedovisor/set-activity-name$', views.pedovisor_set_activity_name, name='pedovisor_set_activity_name'),
    url(r'^pedovisor/get-week-data$', views.pedovisor_get_week_data, name='pedovisor_get_week_data'),
    url(r'^pedovisor/get-weight-data$', views.pedovisor_get_weight_data, name='pedovisor_get_weight_data'),
    url(r'^pedovisor/set-weight-data$', views.pedovisor_set_weight_data, name='pedovisor_set_weight_data'),
    url(r'^pedovisor/activity$', views.pedovisor_activity, name='pedovisor_activity'),
    url(r'^pedovisor/get-activity-list$', views.pedovisor_get_activity_list, name='pedovisor_get_activity_list'),
    url(r'^pedovisor/calendar$', views.pedovisor_calendar, name='pedovisor_calendar'),
    url(r'^pedovisor/get-event-list$', views.pedovisor_get_event_list, name='pedovisor_get_event_list'),
    url(r'^pedovisor/detail$', views.pedovisor_detail, name='pedovisor_detail'),
    url(r'^pedovisor/data/sql-import', views.data_sql_import, name='data_sql_import'),
    url(r'^pedovisor/group', views.pedovisor_group, name='pedovisor_group'),
    url(r'^pedovisor/health', views.health, name='pedovisor.health'),
    url(r'^pedovisor/meal-get-list', views.meal_get_list, name='pedovisor.health.meal_get_list'),
    url(r'^pedovisor/meal-get-info', views.meal_get_info, name='pedovisor.health.meal_get_info'),
    url(r'^pedovisor/meal-create', views.meal_create, name='pedovisor.health.meal_create'),
    url(r'^pedovisor/meal-update', views.meal_update, name='pedovisor.health.meal_update'),
    url(r'^pedovisor/meal-delete', views.meal_delete, name='pedovisor.health.meal_delete'),
    url(r'^pedovisor/sleep-get-list', views.sleep_get_list, name='pedovisor.health.sleep_get_list'),
    url(r'^pedovisor/sleep-get-info', views.sleep_get_info, name='pedovisor.health.sleep_get_info'),
    url(r'^pedovisor/sleep-create', views.sleep_create, name='pedovisor.health.sleep_create'),
    url(r'^pedovisor/sleep-update', views.sleep_update, name='pedovisor.health.sleep_update'),
    url(r'^pedovisor/sleep-delete', views.sleep_delete, name='pedovisor.health.sleep_delete'),
]
