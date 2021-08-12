from django.contrib import admin
from .models import AccessPoint, WifiUser, WifiUserInvite, WifiUserApiKey

# Register your models here.
admin.site.register(AccessPoint)
admin.site.register(WifiUser)
admin.site.register(WifiUserApiKey)
admin.site.register(WifiUserInvite)