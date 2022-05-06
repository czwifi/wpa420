from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('export', views.export, name='export'),
    path('export/<format>', views.wifi_list_downloadable, name='export_download'),
    path('export/<format>/<additional>', views.wifi_list_downloadable, name='export_download'),
    path('map', views.map, name='map'),
    path('data/wifi_list_json', views.data_wifi_list_json, name='data_wifi_list_json'),
    path('upload', views.upload_form, name='upload'),
    path('upload_json', views.upload_form_json, name='upload_json'),
    path('api/mobapp/getCollection', views.wifi_list_json, name='api_getCollection'),
    path('api/mobapp/getApiKey', views.api_get_api_key, name='api_getApiKey'),
    path('api/mobapp/dbHash', views.api_dbhash, name='api_dbHash'),
    path('api/mobapp/upload', views.api_upload, name='api_upload'),
    path('account/login', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('account/logout', auth_views.LogoutView.as_view(template_name='account/logout.html'), name='logout'),
    path('account/change_password', auth_views.PasswordChangeView.as_view(template_name='account/change_password.html', success_url='login'), name='change_password'),
    path('account/generate_invite', views.generate_invite, name='generate_invite'),
    path('account/register', views.register, name='register'),
    path('account/settings', views.settings, name='settings'),
    path('account/settings/api_keys', views.manage_api_keys, name='api_keys'),
    path('account/settings/api_keys/new', views.create_api_key, name='create_api_key'),
    path('account/settings/api_keys/delete/<key_id>',views.delete_api_key,name='delete_api_key'),
    path('refresh', views.refresh_location, name='refresh'),
    path('imports', views.import_history, name='imports'),
]
