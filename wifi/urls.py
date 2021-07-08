from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('map', views.map, name='map'),
    path('upload', views.upload_form, name='upload'),
    path('uploadJson', views.upload_form_json, name='uploadJson'),
    path('api/mobapp/getCollection', views.wifi_list_json, name='api'),
    path('login', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('refresh_location', views.refresh_location, name='refresh_location'),
]