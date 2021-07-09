from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('map', views.map, name='map'),
    path('upload', views.upload_form, name='upload'),
    path('upload_json', views.upload_form_json, name='upload_json'),
    path('api/mobapp/getCollection', views.wifi_list_json, name='api_getCollection'),
    path('api/mobapp/dbHash', views.api_dbhash, name='api_dbHash'),
    path('account/login', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('account/logout', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('account/change_password', auth_views.PasswordChangeView.as_view(template_name='change_password.html', success_url='login'), name='change_password'),
    path('account/generate_invite', views.generate_invite, name='generate_invite'),
    path('account/register', views.register, name='register'),
    path('my_imports/refresh_location', views.refresh_location, name='refresh_location'),
]