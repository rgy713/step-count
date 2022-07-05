"""django_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url

from admin_site import views_health
from . import views
from . import views_user
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.contrib import admin

urlpatterns = [
    url(r'^$', views.index, name='dashboard'),
    url(r'^login/$', views.login, name='adminLogin'),
    url(r'^logout/$', auth_views.logout, name='adminLogout', kwargs={'next_page': settings.LOGIN_URL, }),
    url(r'^forget-password/$', views.forgetpw, name='admin.forgetpw'),
    url(r'^email-verify$', views.email_verify, name='admin.email_verify'),
    url(r'^reset-password/$', views.resetpw, name='admin.resetpw'),

    url(r'^profile/$', views.profile, name='admin.profile'),
    url(r'^profile/change-password$', views.change_password, name='admin.change_password'),
    url(r'^profile/change-group-name$', views.change_group_name, name='admin.change_group_name'),

    url(r'^user/$', views.user_index, name='user.index'),
    url(r'^user/getuserlist/$', views.get_user_list, name='getUserList'),
    url(r'^user/getuserinfo/$', views.get_user_info, name='getUserInfo'),
    url(r'^user/getusermachinelist/$', views.get_user_machine_list, name='getUserMachineList'),
    url(r'^user/delete_user/$', views.delete_user, name='delUser'),
    url(r'^user/register/$', views.user_create, name='register'),
    url(r'^user/update/$', views.user_modify, name='update'),
    url(r'^user/download/(?P<email>[\w.@+-]+)/(?P<machine_id>[\w.@+-]+)/$', views.data_download, name='data_download'),

    url(r'^group/$', views.group_index, name='group.index'),
    url(r'^group/get-list$', views.group_get_list, name='group.get_list'),
    url(r'^group/get-info$', views.group_get_info, name='group.get_info'),
    url(r'^group/create$', views.group_create, name='group.create'),
    url(r'^group/delete$', views.group_delete, name='group.delete'),
    url(r'^group/update$', views.group_update, name='group.update'),

    url(r'^view-user/dashboard$', views_user.user_dashboard, name='user.dashboard'),
    url(r'^view-user/get-week-data$', views_user.user_get_week_data, name='user.get_week_data'),
    url(r'^view-user/get-weight-data$', views_user.user_get_weight_data, name='user.get_weight_data'),
    url(r'^view-user/activity$', views_user.user_activity, name='user.activity'),
    url(r'^view-user/get-activity-list$', views_user.user_get_activity_list, name='user.get_activity_list'),
    url(r'^view-user/calendar$', views_user.user_calendar, name='user.calendar'),
    url(r'^view-user/get-event-list$', views_user.user_get_event_list, name='user.get_event_list'),
    url(r'^view-user/detail$', views_user.user_detail, name='user.detail'),

    url(r'^health/food$', views_health.food_index, name='health.food'),
    url(r'^health/food-get-list$', views_health.food_get_list, name='health.food.get_list'),
    url(r'^health/food-get-info$', views_health.food_get_info, name='health.food.get_info'),
    url(r'^health/food-create$', views_health.food_create, name='health.food.create'),
    url(r'^health/food-update$', views_health.food_update, name='health.food.update'),
    url(r'^health/food-delete$', views_health.food_delete, name='health.food.delete'),
    url(r'^health/sq$', views_health.sq_index, name='health.sq'),
    url(r'^health/sq-get-list$', views_health.sq_get_list, name='health.sq.get_list'),
    url(r'^health/sq-get-info$', views_health.sq_get_info, name='health.sq.get_info'),
    url(r'^health/sq-create$', views_health.sq_create, name='health.sq.create'),
    url(r'^health/sq-update$', views_health.sq_update, name='health.sq.update'),
    url(r'^health/sq-delete$', views_health.sq_delete, name='health.sq.delete'),
    url(r'^health/score-view$', views_health.score_view, name='health.score_view'),
    url(r'^health/get-score-list$', views_health.get_score_list, name='health.get_score_list'),
    url(r'^health/user-view$', views_health.health_view, name='health.user_view'),
    url(r'^health/user-view/meal_get_list$', views_health.meal_get_list, name='health.meal_get_list'),
    url(r'^health/user-view/meal_get_info$', views_health.meal_get_info, name='health.meal_get_info'),
    url(r'^health/user-view/sleep_get_list$', views_health.sleep_get_list, name='health.sleep_get_list'),
    url(r'^health/user-view/sleep_get_info$', views_health.sleep_get_info, name='health.sleep_get_info'),
]
